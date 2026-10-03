from dataclasses import replace
from datetime import datetime, timedelta, timezone
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from modules.B05 import cold_domain_reference as cold
from modules.B05 import manufacturer_wm50_reference as wm50
from modules.B05.weather import WeatherRecord


def records(temperatures):
    start = datetime(2017, 1, 6, 11, tzinfo=timezone.utc)
    return tuple(WeatherRecord('44527', start+timedelta(hours=i), 99.0, t,
                               None, None, None, cold.SOURCE_ID)
                 for i, t in enumerate(temperatures))


class ColdDomainReferenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.model = wm50.load_wm50_reference('MAX', fixed_supply_c=55)

    def test_reviewed_dependencies_are_pinned(self):
        m = cold._manifest()
        self.assertEqual(m['archive']['rows'], 210384)
        self.assertEqual(len(m['complete_winter_labels']), 23)
        self.assertIn('approximately', m['operating_envelope_context']['precision'])

    def test_exact_map_edge_and_neighbors_preserve_unknown(self):
        r = cold._exposure(records([-10.000001, -10, -9.999999]*24), self.model)
        self.assertEqual(r['numeric_map_unavailable_hours'], 24)
        self.assertEqual(r['numeric_map_supported_hours'], 48)
        self.assertFalse(r['complete_numeric_map_coverage'])
        for field in ('physical_equipment_failure_hours', 'full_capacity_deficit_kwh',
                      'backup_capacity_kw', 'electricity_kwh', 'actual_spf'):
            self.assertIsNone(r[field])

    def test_all_supported_is_only_numeric_coverage(self):
        r = cold._exposure(records([-5]*72), self.model)
        self.assertEqual(r['numeric_map_supported_hours'], 72)
        self.assertTrue(r['complete_numeric_map_coverage'])
        self.assertIsNone(r['physical_equipment_failure_hours'])
        self.assertIsNone(r['full_capacity_deficit_kwh'])

    def test_all_unavailable_is_not_zero_capacity(self):
        r = cold._exposure(records([-16]*72), self.model)
        self.assertEqual(r['numeric_map_unavailable_hours'], 72)
        self.assertIsNone(r['full_capacity_deficit_kwh'])
        self.assertIsNone(r['electricity_kwh'])

    def test_warm_outside_domain_does_not_become_cold_failure(self):
        r = cold._exposure(records([30]*72), self.model)
        self.assertEqual(r['numeric_map_unavailable_hours'], 72)
        self.assertIsNone(r['physical_equipment_failure_hours'])

    def test_endpoint_translation_has_full_72_hour_support(self):
        r = cold._exposure(records([-5]*72), self.model)
        self.assertEqual(r['physical_start_utc'], '2017-01-06T10:00:00+00:00')
        self.assertEqual(r['physical_end_exclusive_utc'], '2017-01-09T10:00:00+00:00')
        self.assertEqual(datetime.fromisoformat(r['physical_end_exclusive_utc']) -
                         datetime.fromisoformat(r['physical_start_utc']), timedelta(hours=72))

    def test_hourly_mean_not_instantaneous_temperature(self):
        r = cold._exposure(records([-5]*72), self.model)
        self.assertEqual(r['mean_ta_c'], -5)
        self.assertEqual(r['numeric_map_supported_hours'], 72)

    def test_missing_nonfinite_and_boolean_mean_reject(self):
        for bad in (None, float('nan'), float('inf'), -float('inf'), True, '-10'):
            with self.subTest(value=bad), self.assertRaises(ValueError):
                cold._exposure(records([-5]*71+[bad]), self.model)

    def test_missing_duplicate_reversed_and_shifted_intervals_reject(self):
        r = records([-5]*72)
        for candidate in (r[:-1], r+(r[-1],), r[:30]+(r[29],)+r[31:], tuple(reversed(r)),
                          r[:30]+(replace(r[30], timestamp_utc=r[30].timestamp_utc+timedelta(minutes=1)),)+r[31:]):
            with self.subTest(candidate=candidate[0].timestamp_utc), self.assertRaises(ValueError):
                cold._exposure(candidate, self.model)

    def test_invalid_source_station_and_endpoint_reject(self):
        r = records([-5]*72)
        for changes in ({'station_id':'OTHER'}, {'source_id':'OTHER'}, {'timestamp_utc':None},
                        {'timestamp_utc':r[0].timestamp_utc.replace(tzinfo=None)},
                        {'timestamp_utc':r[0].timestamp_utc.astimezone(timezone(timedelta(hours=1)))}):
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                cold._exposure((replace(r[0], **changes),)+r[1:], self.model)

    def test_other_supply_and_mode_cannot_silently_replace_product_case(self):
        for mode, supply in (('MAX',35), ('MIN',55), ('NOMINAL',55)):
            with self.subTest(mode=mode,supply=supply), self.assertRaises(ValueError):
                cold._exposure(records([-5]*72), wm50.load_wm50_reference(mode,fixed_supply_c=supply))

    def test_unqualified_archive_rejects_before_parser(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'fake.zip';p.write_bytes(b'synthetic-not-source')
            with patch.object(cold,'parse_hungaromet_csv') as parser:
                with self.assertRaisesRegex(ValueError,'exact registered'):
                    cold.calculate_reference(archive_path=p)
                parser.assert_not_called()

    def test_manifest_mutation_is_not_an_override(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'manifest.json';p.write_bytes(cold.MANIFEST.read_bytes()+b' ')
            with patch.object(cold,'MANIFEST',p), self.assertRaises(ValueError):cold._manifest()


if __name__ == '__main__':
    unittest.main()
