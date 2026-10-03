import csv
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from modules.B05 import manufacturer_wm50_reference as reference


class Wm50ManufacturerReferenceTests(unittest.TestCase):
    def test_complete_source_inventory_and_existing_minimum_points(self):
        rows = reference.source_grid()
        self.assertEqual(len(rows), 252)
        self.assertEqual(sum(r['availability'] == 'PRESENT' for r in rows), 208)
        self.assertEqual(sum(r['availability'] == 'SOURCE_BLANK' for r in rows), 44)
        self.assertEqual(sum(r['defrost_source_annotation'] == 'GRAY_INTEGRATED_DEFROST' for r in rows), 21)
        lookup = {(r['mode'], float(r['outdoor_temperature_c']), float(r['supply_temperature_c'])): r for r in rows}
        with (reference.ROOT/'data/processed/b05_p22_mitsubishi_minimum_point_grid.csv').open() as f:
            prior = list(csv.DictReader(f))
        self.assertEqual(len(prior), 40)
        for row in prior:
            current = lookup['MIN', float(row['outdoor_temperature_C']), float(row['supply_temperature_C'])]
            self.assertEqual(float(current['thermal_capacity_kw']), float(row['min_modulation_kW']))
            self.assertEqual(float(current['cop']), float(row['min_point_COP']))

    def test_all208_native_pairs_feed_existing_engine_with_derived_input(self):
        for mode in reference.MODES:
            model = reference.load_wm50_reference(mode)
            self.assertEqual(len(model.points), 52)
            for native in model.points:
                result = model.evaluate(native.outdoor_temperature_c, native.supply_temperature_c)
                self.assertEqual(result.status, 'DER')
                point = result.point
                self.assertEqual(point.cop, native.cop)
                self.assertEqual(point.thermal_capacity_kw, native.thermal_capacity_kw)
                self.assertAlmostEqual(point.electrical_input_kw * point.cop, point.thermal_capacity_kw)
                self.assertLessEqual(point.min_modulation_kw, point.thermal_capacity_kw)

    def test_interpolation_conserves_power_and_gaps_remain_unknown(self):
        for mode in reference.MODES:
            model = reference.load_wm50_reference(mode)
            for outdoor, supply in [(-17, 37.5), (-2, 40), (10, 52.5)]:
                point = model.evaluate(outdoor, supply).point
                self.assertIsNotNone(point)
                self.assertAlmostEqual(point.thermal_capacity_kw, point.electrical_input_kw * point.cop)
            for outdoor, supply in [(-15, 50), (-17, 42.5), (-21, 35), (21, 35)]:
                result = model.evaluate(outdoor, supply)
                self.assertTrue(result.status.startswith('Q /'))
                self.assertIsNone(result.point)
            fixed = reference.load_wm50_reference(mode, fixed_supply_c=35)
            self.assertEqual(len(fixed.points), 9)
            self.assertIsNotNone(fixed.evaluate(-17, 35).point)
            self.assertIsNone(fixed.evaluate(-17, 36).point)
        with self.assertRaises(ValueError): reference.load_wm50_reference('MIN', fixed_supply_c=36)
        unavailable = tuple(dict(r, availability='SOURCE_BLANK') if r['mode'] == 'MIN'
                            and r['supply_temperature_c'] == '35' else r for r in reference.source_grid())
        with patch.object(reference, 'source_grid', return_value=unavailable):
            with self.assertRaisesRegex(ValueError, 'no source performance points'):
                reference.load_wm50_reference('MIN', fixed_supply_c=35)

    def test_defrost_label_is_not_transferred_between_modes_or_coordinates(self):
        self.assertEqual(reference.source_annotation('MAX', 2, 35), ('PRESENT', 'GRAY_INTEGRATED_DEFROST'))
        self.assertEqual(reference.source_annotation('MIN', 2, 35), ('PRESENT', 'NOT_GRAY_NO_EXPLICIT_INTEGRATED_LABEL'))
        self.assertEqual(reference.source_annotation('MAX', -15, 50)[0], 'SOURCE_BLANK')
        with self.assertRaises(ValueError): reference.source_annotation('MAX', 2.1, 35)
        with self.assertRaises(ValueError): reference.load_wm50_reference('AUTOMATIC')

    def test_changed_source_extract_is_rejected(self):
        original = reference.ROOT
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root/'registry').mkdir()
            (root/'data/processed/b05').mkdir(parents=True)
            manifest = 'registry/b05_wm50_full_grid_manifest.json'
            data = 'data/processed/b05/wm50_full_performance_v53.csv'
            (root/manifest).write_bytes((original/manifest).read_bytes())
            (root/data).write_bytes((original/data).read_bytes()+b'\n')
            with patch.object(reference, 'ROOT', root):
                with self.assertRaisesRegex(ValueError, 'hash'): reference.source_grid()


if __name__ == '__main__': unittest.main()
