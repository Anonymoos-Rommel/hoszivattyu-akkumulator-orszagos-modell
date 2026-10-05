from datetime import datetime,timedelta,timezone
import unittest
from modules.B05.weather import load_materialized_profile,materialized_intervals


class WeatherIntervalBoundaryTests(unittest.TestCase):
    def fixture(self):
        return dict(weather_profile_id='SOURCE_WINDOW',station_id='15310',timestamp_utc='2025-01-01T00:00:00Z',outdoor_temperature_C='-3.5',relative_humidity_pct='90',temperature_source_variable='ta',evidence_status='OBS',source_id='SRC-B05-HUNGARY-HOURLY-HIST-2026')

    def test_source_endpoint_is_not_energy_interval_start(self):
        x=materialized_intervals([self.fixture()])[0]
        self.assertEqual(x.interval_start_utc,datetime(2024,12,31,23,tzinfo=timezone.utc))
        self.assertEqual(x.interval_end_utc,datetime(2025,1,1,tzinfo=timezone.utc))
        self.assertEqual(x.humidity_temporal_boundary,'INSTANTANEOUS_AT_INTERVAL_END')

    def test_reuses_all_five_real_source_timestamp_windows(self):
        for station in ('15310','44527','58102','46304','52744'):
            rows=load_materialized_profile('B05-REF-OBS-2025-'+station)
            self.assertEqual(len(rows),8760)
            self.assertEqual(rows[0].interval_start_utc,datetime(2024,12,31,23,tzinfo=timezone.utc))
            self.assertEqual(rows[-1].interval_end_utc,datetime(2025,12,31,23,tzinfo=timezone.utc))
            self.assertTrue(all(b.interval_start_utc==a.interval_end_utc for a,b in zip(rows,rows[1:])))

    def test_extreme_window_preserved_and_no_national_weight_inferred(self):
        rows=load_materialized_profile('B05-EXTREME-OBSERVED-72H-15310')
        self.assertEqual(len(rows),72)
        self.assertEqual(rows[-1].interval_end_utc-rows[0].interval_start_utc,timedelta(hours=72))
        self.assertEqual(min(r.mean_temperature_c for r in rows),-21.9)
        with self.assertRaises(ValueError):load_materialized_profile('NATIONAL_AVERAGE')

    def test_bad_clock_values_and_mixed_profiles_fail_closed(self):
        row=self.fixture()
        for key,bad in [('timestamp_utc','2025-01-01T00:01:00Z'),('timestamp_utc','2025-01-01T00:00:00'),('outdoor_temperature_C','NaN'),('outdoor_temperature_C','-999'),('relative_humidity_pct','101'),('temperature_source_variable','t'),('weather_profile_id','')]:
            with self.assertRaises(ValueError):materialized_intervals([{**row,key:bad}])
        with self.assertRaises(ValueError):materialized_intervals([row,row])
        with self.assertRaises(ValueError):materialized_intervals([row,{**row,'station_id':'44527','timestamp_utc':'2025-01-01T01:00:00Z'}])
        self.assertIsNone(materialized_intervals([{**row,'relative_humidity_pct':''}])[0].end_relative_humidity_pct)


if __name__=='__main__':unittest.main()
