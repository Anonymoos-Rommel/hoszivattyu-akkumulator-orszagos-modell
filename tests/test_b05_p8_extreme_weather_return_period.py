import unittest
from datetime import timedelta

from modules.B05.extreme_weather_return_period import (
    EMPIRICAL_ORDER_STATISTIC_BRACKET,
    Q_INSUFFICIENT_BLOCKS,
    WINTER_MEAN_TA,
    WINTER_MIN_72H_MEAN_TA,
    WinterExtremeMetric,
    complete_winter_metric,
    empirical_return_period_bracket,
    multi_station_stress_envelope,
    return_period_boundaries,
    winter_bounds_utc,
)
from modules.B05.weather import WeatherRecord


def _record(station_id, timestamp, ta):
    return WeatherRecord(
        station_id=station_id,
        timestamp_utc=timestamp,
        instantaneous_temperature_c=ta,
        hourly_mean_temperature_c=ta,
        hourly_min_temperature_c=ta,
        hourly_max_temperature_c=ta,
        relative_humidity_pct=80.0,
        source_id="SRC-TEST",
    )


def _metric(station_id, year, winter_mean, cold72):
    start, end = winter_bounds_utc(year)
    return WinterExtremeMetric(
        station_id=station_id,
        winter_label_year=year,
        window_start_utc=start,
        window_end_exclusive_utc=end,
        expected_hours=int((end - start).total_seconds() // 3600),
        observed_hours=int((end - start).total_seconds() // 3600),
        winter_mean_ta_c=winter_mean,
        coldest_72h_mean_ta_c=cold72,
        coldest_72h_start_utc=start,
        coldest_72h_end_utc=start + timedelta(hours=71),
    )


class B05P8ExtremeWeatherReturnPeriodTests(unittest.TestCase):
    def test_winter_boundary_uses_budapest_local_dec_to_mar(self):
        start, end = winter_bounds_utc(2025)
        self.assertEqual(start.isoformat(), "2024-11-30T23:00:00+00:00")
        self.assertEqual(end.isoformat(), "2025-02-28T23:00:00+00:00")
        self.assertEqual(int((end - start).total_seconds() // 3600), 2160)

    def test_complete_winter_metric_requires_full_hourly_ta(self):
        start, end = winter_bounds_utc(2025)
        hours = int((end - start).total_seconds() // 3600)
        records = []
        for i in range(hours):
            ta = -12.0 if i < 72 else 2.0
            records.append(_record("15310", start + timedelta(hours=i), ta))

        metric = complete_winter_metric(records, winter_label_year=2025)
        self.assertIsNotNone(metric)
        assert metric is not None
        self.assertEqual(metric.observed_hours, 2160)
        self.assertAlmostEqual(metric.coldest_72h_mean_ta_c, -12.0)
        self.assertEqual(metric.coldest_72h_start_utc, start)

        missing = records[:-1]
        self.assertIsNone(
            complete_winter_metric(missing, winter_label_year=2025)
        )

    def test_ten_year_target_is_nonparametric_order_statistic_bracket(self):
        metrics = [
            _metric("15310", 2014 + i, winter_mean=-10.0 + i, cold72=-20.0 + i)
            for i in range(12)
        ]
        result = empirical_return_period_bracket(
            metrics,
            metric_id=WINTER_MIN_72H_MEAN_TA,
            target_return_period_years=10.0,
        )
        self.assertEqual(result.status, EMPIRICAL_ORDER_STATISTIC_BRACKET)
        self.assertEqual(result.evidence_status, "DER")
        self.assertEqual(result.complete_winter_blocks, 12)
        self.assertEqual(result.colder_rank, 1)
        self.assertEqual(result.warmer_rank, 2)
        self.assertEqual(result.colder_bound_c, -20.0)
        self.assertEqual(result.warmer_bound_c, -19.0)
        self.assertIn("NO_POINT_INTERPOLATION", result.notes)
        self.assertIn("NOT_OFFICIAL_HUNGAROMET_1_IN_10", result.notes)

    def test_record_too_short_fails_closed_without_tail_extrapolation(self):
        metrics = [
            _metric("15310", 2018 + i, winter_mean=-5.0 + i, cold72=-15.0 + i)
            for i in range(8)
        ]
        result = empirical_return_period_bracket(
            metrics,
            metric_id=WINTER_MEAN_TA,
            target_return_period_years=10.0,
        )
        self.assertEqual(result.status, Q_INSUFFICIENT_BLOCKS)
        self.assertEqual(result.evidence_status, "Q")
        self.assertIsNone(result.colder_bound_c)
        self.assertIn("NO_PARAMETRIC_TAIL_EXTRAPOLATION", result.notes)

    def test_multi_station_envelope_is_not_a_national_weighted_statistic(self):
        station_results = []
        for station_id, offset in (("15310", 0.0), ("44527", 2.0)):
            metrics = [
                _metric(
                    station_id,
                    2014 + i,
                    winter_mean=-10.0 + i + offset,
                    cold72=-20.0 + i + offset,
                )
                for i in range(12)
            ]
            station_results.append(
                empirical_return_period_bracket(
                    metrics,
                    metric_id=WINTER_MIN_72H_MEAN_TA,
                    target_return_period_years=10.0,
                )
            )

        envelope = multi_station_stress_envelope(station_results)
        self.assertEqual(envelope.station_count, 2)
        self.assertEqual(envelope.colder_envelope_c, -20.0)
        self.assertEqual(envelope.warmer_envelope_c, -17.0)
        self.assertEqual(envelope.status, "PROJECT_STATION_ENVELOPE")

    def test_boundaries_forbid_official_or_national_promotion(self):
        boundaries = return_period_boundaries()
        self.assertIn(
            "PROJECT_DERIVED_EMPIRICAL_RETURN_PERIOD != OFFICIAL_HUNGAROMET_1_IN_10",
            boundaries,
        )
        self.assertIn(
            "STATION_RETURN_PERIOD != NATIONAL_POPULATION_WEIGHTED_CLIMATE",
            boundaries,
        )
        self.assertIn(
            "NO_PARAMETRIC_TAIL_EXTRAPOLATION_BY_DEFAULT",
            boundaries,
        )


if __name__ == "__main__":
    unittest.main()
