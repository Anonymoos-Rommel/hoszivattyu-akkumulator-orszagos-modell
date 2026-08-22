import csv
import io
import unittest
from datetime import datetime, timezone
from pathlib import Path

from modules.B05.engine import HourlyDemand, PerformanceMap, simulate_hourly
from modules.B05.weather import parse_hungaromet_csv, select_extreme_cold_spell


ROOT = Path(__file__).parents[1]


class B05WeatherEvidenceTests(unittest.TestCase):
    def test_parser_preserves_utc_and_ta_t_distinction_and_missing(self):
        text = (
            "StationNumber;Time;t;ta;tn;tx;u;EOR\n"
            " 15310;202501010100;3.0;2.0;1.0;4.0;80;EOR\n"
            " 15310;202501010200;-999;-999;-999;-999;-999;EOR\n"
        )
        rows = tuple(parse_hungaromet_csv(text, source_id="TEST-HM"))
        self.assertEqual(rows[0].station_id, "15310")
        self.assertEqual(rows[0].timestamp_utc, datetime(2025, 1, 1, 1, tzinfo=timezone.utc))
        self.assertEqual(rows[0].instantaneous_temperature_c, 3.0)
        self.assertEqual(rows[0].hourly_mean_temperature_c, 2.0)
        self.assertEqual(rows[0].outdoor_temperature_c, 2.0)
        self.assertEqual(rows[0].relative_humidity_pct, 80.0)
        self.assertIsNone(rows[1].outdoor_temperature_c)
        self.assertIsNone(rows[1].instantaneous_temperature_c)

    def test_extreme_selection_requires_contiguous_non_missing_utc_hours(self):
        text = "StationNumber;Time;t;ta;tn;tx;u;EOR\n" + "\n".join(
            f"1;20250101{hour:02d}00;0;{-10 + hour};-11;-9;80;EOR" for hour in range(5)
        )
        rows = tuple(parse_hungaromet_csv(text, source_id="TEST-HM"))
        selected = select_extreme_cold_spell(rows, window_hours=3)
        self.assertEqual(len(selected), 3)
        self.assertEqual(selected[0].timestamp_utc.hour, 0)
        self.assertEqual(selected[-1].timestamp_utc.hour, 2)

    def test_materialized_weather_is_ordered_and_station_specific(self):
        path = ROOT / "data" / "processed" / "heat_pump_weather_hourly.csv"
        with path.open(encoding="utf-8", newline="") as handle:
            rows = list(csv.DictReader(handle))
        self.assertGreater(len(rows), 40000)
        self.assertEqual({row["temperature_source_variable"] for row in rows}, {"ta"})
        self.assertEqual({row["evidence_status"] for row in rows}, {"OBS"})
        self.assertEqual({row["source_id"] for row in rows}, {"SRC-B05-HUNGARY-HOURLY-HIST-2026"})
        self.assertEqual(len({row["station_id"] for row in rows}), 5)
        for profile_id in {row["weather_profile_id"] for row in rows}:
            profile_rows = [row for row in rows if row["weather_profile_id"] == profile_id]
            timestamps = [datetime.fromisoformat(row["timestamp_utc"].replace("Z", "+00:00")) for row in profile_rows]
            self.assertTrue(all(timestamp.tzinfo is not None for timestamp in timestamps))
            self.assertEqual(timestamps, sorted(timestamps))
            self.assertEqual(len(timestamps), len(set(timestamps)))
            self.assertNotIn("-999", "".join(row["outdoor_temperature_C"] for row in profile_rows))

    def test_weather_coverage_and_profiles_keep_normal_and_extreme_distinct(self):
        profiles_path = ROOT / "data" / "processed" / "heat_pump_weather_profiles.csv"
        coverage_path = ROOT / "data" / "processed" / "heat_pump_weather_coverage.csv"
        with profiles_path.open(encoding="utf-8", newline="") as handle:
            profiles = list(csv.DictReader(handle))
        with coverage_path.open(encoding="utf-8", newline="") as handle:
            coverage = {row["weather_profile_id"]: row for row in csv.DictReader(handle)}
        reference = [row for row in profiles if row["profile_type"] == "OBSERVED_REFERENCE_YEAR"]
        extreme = [row for row in profiles if row["profile_type"] == "OBSERVED_EXTREME_COLD_SPELL"]
        self.assertEqual(len(reference), 5)
        self.assertEqual(len(extreme), 1)
        self.assertTrue(all("not a 1991-2020 normal" in row["selection_method"] for row in reference))
        self.assertIn("not 1-in-10", extreme[0]["notes"])
        self.assertEqual(coverage[extreme[0]["weather_profile_id"]]["hours_total"], "72")
        self.assertLess(float(coverage[extreme[0]["weather_profile_id"]]["share_inside_current_performance_domain"]), 1.0)
        extreme_coverage = coverage[extreme[0]["weather_profile_id"]]
        self.assertEqual(extreme_coverage["equipment_id"], "STIEBEL-HPA-O-4-CS-PLUS-INT")
        self.assertEqual(extreme_coverage["supply_temperature_C"], "35")
        self.assertEqual(extreme_coverage["new_hours_inside_performance_domain"], "35")
        self.assertEqual(extreme_coverage["remaining_hours_below_new_minimum_performance_C"], "37")
        self.assertAlmostEqual(float(extreme_coverage["new_share_inside_performance_domain"]), 35 / 72, places=5)

    def test_real_weather_integrates_with_existing_product_map_and_fails_closed(self):
        points = ROOT / "data" / "processed" / "heat_pump_performance_points.csv"
        performance_map = PerformanceMap.from_csv(points, "STIEBEL-HPA-O-4-CS-PLUS-INT")
        weather_path = ROOT / "data" / "processed" / "heat_pump_weather_hourly.csv"
        with weather_path.open(encoding="utf-8", newline="") as handle:
            rows = list(csv.DictReader(handle))
        inside = next(row for row in rows if -7 <= float(row["outdoor_temperature_C"]) <= 7)
        outside = next(row for row in rows if float(row["outdoor_temperature_C"]) < -15)

        def run(row):
            timestamp = datetime.fromisoformat(row["timestamp_utc"].replace("Z", "+00:00"))
            return simulate_hourly(
                performance_map,
                [HourlyDemand(timestamp, float(row["outdoor_temperature_C"]), 1.0, 35.0)],
            )

        self.assertEqual(run(inside).hourly[0].status, "VALID")
        self.assertTrue(run(outside).hourly[0].status.startswith("Q / OUT_OF_PERFORMANCE_DOMAIN"))
        # Weather is OBS, but the deliberately supplied thermal demand remains SCN in this integration test.
        self.assertEqual(inside["evidence_status"], "OBS")


if __name__ == "__main__":
    unittest.main()
