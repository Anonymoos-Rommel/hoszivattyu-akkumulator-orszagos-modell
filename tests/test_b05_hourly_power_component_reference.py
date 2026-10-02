"""Synthetic contract/adverse cases; external observed radiation is not bundled."""
import copy
import inspect
import math
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from modules.B05 import hourly_power_component_reference as model
from modules.B05.engine import OperatingPoint, OperatingPointResult


def fixture():
    points, models, grid = [], {}, []
    for mode, q, p in zip(model.MODES, (1., 2., 3., 4.), (.4, .8, 1.3, 2.)):
        cell = dict(source_id=model.wm50.SOURCE_ID, mode=mode, outdoor_temperature_c='2',
                    supply_temperature_c='55', availability='PRESENT', thermal_capacity_kw=str(q),
                    cop=str(q / p), derived_input_kw=str(p), evidence_status='OBS',
                    source_pair_status='SOURCE_Q_COP_PAIR',
                    defrost_source_annotation='UNMARKED' if mode == 'MIN' else 'INTEGRATED_DEFROST')
        point = OperatingPoint(2., 55., q, p, q / p, 1., 'DER', (model.wm50.SOURCE_ID,), 'exact')
        result = OperatingPointResult('DER', point)
        models[mode] = SimpleNamespace(
            equipment_id=f'{model.wm50.PRODUCT}:{mode}:VOL5.3:FIXED_W55',
            evaluate=lambda ta, supply, result=result: result)
        points.append(dict(mode=mode, status='DER', q_kw=q, p_kw=p, cop=q / p,
                           source_cells=[cell]))
        grid.append(cell)
    return points, models, grid


def thermal_row(q=1.5, branch='BETWEEN_MIN_MAX'):
    row = dict(interval_start_utc='2025-01-01T00:00:00+00:00',
               interval_end_utc='2025-01-01T01:00:00+00:00', ta_observed_c=2.)
    fixed = dict(row, required_heat_kw=q, source_capacity_branch=branch,
                 source_rating_capacity_kw=4., additional_thermal_requirement_kwh=None if q is None else max(0., q-4.))
    return row, fixed


class PairedPowerTests(unittest.TestCase):
    def test_every_native_mode_and_boundary_is_recovered(self):
        points, _, _ = fixture()
        for p in points:
            with self.subTest(mode=p['mode']):
                result, reason = model._interpolate(p['q_kw'], points)
                self.assertIsNone(reason)
                self.assertEqual(result['input_kw'], p['p_kw'])
                self.assertEqual(result['support_modes'], [p['mode']])
                self.assertEqual(result['weight'], 0.)

    def test_adjacent_power_interpolation_has_energy_identity_and_continuity(self):
        points, _, _ = fixture()
        for a, b in zip(points, points[1:]):
            for weight in (1e-9, .25, .5, .75, 1-1e-9):
                q = a['q_kw'] + weight * (b['q_kw']-a['q_kw'])
                result, reason = model._interpolate(q, points)
                self.assertIsNone(reason)
                self.assertAlmostEqual(result['input_kw'], a['p_kw']+weight*(b['p_kw']-a['p_kw']))
                self.assertAlmostEqual(result['input_kw'] * result['cop'], q)
                self.assertEqual(result['support_modes'], [a['mode'], b['mode']])

    def test_interpolates_power_not_cop(self):
        points, _, _ = fixture()
        result, _ = model._interpolate(3.5, points)
        self.assertAlmostEqual(result['input_kw'], 1.65)
        self.assertNotAlmostEqual(result['input_kw'], 3.5 / ((3/1.3 + 4/2)/2))

    def test_invalid_demands_reject_without_zero_fill(self):
        points, _, _ = fixture()
        for q in (None, True, False, -1, 0, float('inf'), float('nan'), '1'):
            with self.subTest(q=q), self.assertRaises(ValueError):
                model._interpolate(q, points)

    def test_below_above_and_missing_modes_do_not_extrapolate(self):
        points, _, _ = fixture()
        for q in (.5, 4.5):
            self.assertEqual(model._interpolate(q, points), (None, 'Q_OUTSIDE_CONTINUOUS_RANGE'))
        for index in range(4):
            changed = copy.deepcopy(points)
            changed[index] = dict(mode=model.MODES[index], status='Q')
            self.assertEqual(model._interpolate(1.5, changed), (None, 'Q_MISSING_MODE_SUPPORT'))

    def test_reversed_modes_cannot_be_sorted_into_admission(self):
        points, _, _ = fixture()
        points[2]['q_kw'] = 1.8
        self.assertEqual(model._interpolate(1.5, points), (None, 'Q_REVERSED_MODE_CAPACITY'))
        points[1], points[2] = points[2], points[1]
        with self.assertRaisesRegex(ValueError, 'frequency modes'):
            model._interpolate(1.5, points)

    def test_equal_capacity_requires_equal_power_and_preserves_both_sources(self):
        points, _, _ = fixture()
        points[1]['q_kw'] = points[0]['q_kw']
        self.assertEqual(model._interpolate(1., points), (None, 'Q_CONFLICTING_EQUAL_CAPACITY'))
        points[1]['p_kw'] = points[0]['p_kw']
        result, reason = model._interpolate(1., points)
        self.assertIsNone(reason)
        self.assertEqual(result['support_modes'], ['MIN', 'MID'])
        self.assertEqual(len(result['source_cells']), 2)


class BranchAndSourceTests(unittest.TestCase):
    def setUp(self):
        self.points, self.models, self.grid = fixture()

    def test_mixed_defrost_is_retained_without_physical_admission(self):
        result = model._row(*thermal_row(), self.models, self.grid)
        c = result['component']
        self.assertTrue(c['mixed_defrost_annotations'])
        self.assertEqual(c['source_defrost_labels'], ['INTEGRATED_DEFROST', 'UNMARKED'])
        self.assertEqual(c['evidence_status'], 'SCN')
        self.assertIsNone(c['physical_weather_electricity_kwh'])
        self.assertIsNone(result['whole_service_electricity_kwh'])
        self.assertAlmostEqual(c['rating_input_kwh'], .6)

    def test_cycling_zero_and_missing_thermal_remain_q(self):
        for q, branch, reason in ((.5, 'BELOW_MIN', 'Q_CYCLING_METHOD_AND_RUNTIME'),
                                  (0., 'ZERO_DEMAND', 'Q_ZERO_LOAD_AUXILIARIES'),
                                  (None, 'Q', 'Q_THERMAL_PATH_OR_MAP')):
            result = model._row(*thermal_row(q, branch), self.models, self.grid)
            self.assertIsNone(result['component'])
            self.assertEqual(result['component_status'], 'Q')
            self.assertEqual(result['reason'], reason)
            self.assertIsNone(result['actual_electricity_kwh'])

    def test_overload_is_separate_component_with_unserved_requirement(self):
        result = model._row(*thermal_row(5., 'ABOVE_MAX'), self.models, self.grid)
        self.assertEqual(result['component']['kind'], 'FULL_MAX_COMPONENT_ONLY')
        self.assertEqual(result['component']['heat_kwh'], 4.)
        self.assertEqual(result['component']['rating_input_kwh'], 2.)
        self.assertEqual(result['additional_thermal_requirement_kwh'], 1.)
        self.assertIsNone(result['whole_service_electricity_kwh'])

    def test_missing_mid_only_blocks_its_dependent_component(self):
        self.models['MID'].evaluate = lambda *args: OperatingPointResult('Q / source gap', reason='gap')
        continuous = model._row(*thermal_row(), self.models, self.grid)
        overload = model._row(*thermal_row(5., 'ABOVE_MAX'), self.models, self.grid)
        self.assertIsNone(continuous['component'])
        self.assertEqual(continuous['reason'], 'Q_MISSING_MODE_SUPPORT')
        self.assertEqual(overload['component']['rating_input_kwh'], 2.)

    def test_source_identity_and_q_p_cop_substitutions_reject(self):
        genuine = self.models['MIN'].evaluate(2., 55.).point
        for change in (dict(source_ids=('OTHER',)), dict(evidence_status='OBS'),
                       dict(supply_temperature_c=35.), dict(outdoor_temperature_c=7.),
                       dict(cop=9.), dict(electrical_input_kw=float('nan'))):
            changed = replace(genuine, **change)
            self.models['MIN'].evaluate = lambda *args, changed=changed: OperatingPointResult('DER', changed)
            with self.subTest(change=change), self.assertRaises(ValueError):
                model._points(self.models, self.grid, 2.)

    def test_blank_source_cell_cannot_be_supported_by_a_numeric_point(self):
        self.grid[0]['availability'] = 'SOURCE_BLANK'
        with self.assertRaisesRegex(ValueError, 'support mismatch'):
            model._points(self.models, self.grid, 2.)

    def test_source_product_substitution_rejects(self):
        self.models['MIN'].equipment_id = 'OTHER_PRODUCT'
        with self.assertRaisesRegex(ValueError, 'product/mode'):
            model._points(self.models, self.grid, 2.)

    def test_interval_mismatch_non_utc_and_non_hour_reject(self):
        row, fixed = thermal_row()
        fixed['interval_end_utc'] = '2025-01-01T02:00:00+00:00'
        with self.assertRaisesRegex(ValueError, 'interval mismatch'):
            model._row(row, fixed, self.models, self.grid)
        for start, end in (('2025-01-01T00:00:00', '2025-01-01T01:00:00'),
                           ('2025-01-01T00:00:00+01:00', '2025-01-01T01:00:00+01:00'),
                           ('2025-01-01T00:00:00+00:00', '2025-01-01T02:00:00+00:00')):
            row, fixed = thermal_row()
            for r in (row, fixed):
                r.update(interval_start_utc=start, interval_end_utc=end)
            with self.subTest(start=start, end=end), self.assertRaisesRegex(ValueError, 'UTC hour'):
                model._row(row, fixed, self.models, self.grid)

    def test_thermal_max_disagreement_rejects(self):
        row, fixed = thermal_row(5., 'ABOVE_MAX')
        fixed['source_rating_capacity_kw'] = 3.
        with self.assertRaisesRegex(ValueError, 'MAX references'):
            model._row(row, fixed, self.models, self.grid)

    def test_subset_accounting_keeps_unknowns_and_overload_separate(self):
        rows = [model._row(*thermal_row(q, branch), self.models, self.grid) for q, branch in
                ((1.5, 'BETWEEN_MIN_MAX'), (5., 'ABOVE_MAX'), (.5, 'BELOW_MIN'), (0., 'ZERO_DEMAND'))]
        continuous = model._summary(rows, 'CONTINUOUS_PAIRED_POWER_REFERENCE')
        overload = model._summary(rows, 'FULL_MAX_COMPONENT_ONLY')
        self.assertAlmostEqual(continuous['supported_component_rating_input_kwh'], .6)
        self.assertEqual(overload['supported_component_rating_input_kwh'], 2.)
        self.assertIsNone(continuous['complete_period_electricity_kwh'])
        self.assertEqual(model._coverage(rows)['BELOW_MIN']['required_heat_kwh'], .5)
        self.assertIsNone(model._coverage(rows)['BELOW_MIN']['whole_service_electricity_kwh'])
        missing = [model._row(*thermal_row(None, 'Q'), self.models, self.grid)]
        self.assertIsNone(model._coverage(missing)['Q']['required_heat_kwh'])
        self.assertIsNone(model._summary(missing, 'CONTINUOUS_PAIRED_POWER_REFERENCE')['supported_component_rating_input_kwh'])


class PublicAdmissionTests(unittest.TestCase):
    def test_no_external_radiation_yields_all_unknown_components(self):
        result = model.calculate_reference()
        self.assertEqual(len(result['rows']), 72)
        self.assertEqual(result['unknown_electrical_hours'], 72)
        self.assertIsNone(result['continuous_component']['supported_component_rating_input_kwh'])
        self.assertIsNone(result['thermal_branch_coverage']['Q']['required_heat_kwh'])
        for field in ('actual_electricity_kwh', 'actual_spf', 'payback', 'whole_period_rating_input_kwh',
                      'cycling_electricity_kwh', 'auxiliary_electricity_kwh', 'backup_electricity_kwh'):
            self.assertIsNone(result[field])
        for field in ('empirical_validation', 'national_claim', 'whole_slice_complete', 'complete_load_for_B08_or_B12'):
            self.assertFalse(result[field])

    def test_entry_point_cannot_accept_caller_case_or_provenance_labels(self):
        self.assertEqual(set(inspect.signature(model.calculate_reference).parameters), {'radiation_path'})
        for extra in ('thermal_result', 'case_id', 'manifest_path', 'supply_c', 'cdh', 'source_status'):
            with self.subTest(extra=extra), self.assertRaises(TypeError):
                model.calculate_reference(**{extra: 'override'})

    def test_substitute_source_and_changed_upstream_code_fail_before_arithmetic(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'radiation.csv'
            path.write_text('invented,0\n')
            with self.assertRaisesRegex(ValueError, 'bytes/hash mismatch'):
                model.calculate_reference(radiation_path=path)
        genuine = Path.read_bytes
        target = Path(model.thermal.__file__)
        def changed(path):
            data = genuine(path)
            return data + b'\n' if path == target else data
        with patch.object(Path, 'read_bytes', changed), self.assertRaisesRegex(ValueError, 'thermal API changed'):
            model.calculate_reference()

    def test_genuine_map_native_corners_and_outside_domain(self):
        models = {m: model.wm50.load_wm50_reference(m, fixed_supply_c=55) for m in model.MODES}
        grid = model.wm50.source_grid()
        for ta in (-10., -7., 2., 7., 10., 20.):
            points = model._points(models, grid, ta)
            for p in points:
                with self.subTest(ta=ta, mode=p['mode']):
                    result, reason = model._interpolate(p['q_kw'], points)
                    self.assertIsNone(reason)
                    self.assertAlmostEqual(result['input_kw'], p['p_kw'])
        for ta in (-15., 25.):
            points = model._points(models, grid, ta)
            self.assertIsNone(model._interpolate(2., points)[0])


if __name__ == '__main__':
    unittest.main()
