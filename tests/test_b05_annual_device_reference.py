import copy
import csv
import hashlib
import io
import json
import math
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from modules.B05 import annual_device_reference as m


class AnnualReferenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest = m._manifest()
        cls.hp = cls.manifest['heat_pump']
        cls.models = {mode: m.wm50.load_wm50_reference(mode, fixed_supply_c=55) for mode in m.paired.MODES}
        cls.grid = m.wm50.source_grid()

    def points(self, temperature=-7):
        return m.paired._points(self.models, self.grid, temperature)

    def test_source_annual_heat_and_effective_distribution_are_added_once(self):
        r = m._thermal(self.manifest)
        self.assertAlmostEqual(r['useful_heat_kwh'], 5748.154431653909, places=8)
        self.assertAlmostEqual(r['effective_distribution_heat_kwh'], 302.4)
        self.assertAlmostEqual(r['generator_heat_kwh'], 6050.554431653909, places=8)
        self.assertAlmostEqual(r['balance_temperature_c'], 17.873392190756576, places=10)
        self.assertEqual(self.manifest['thermal']['source_mixed_gas_aux_kwh_m2'], 2.8)
        self.assertNotIn('gas_auxiliary_addition', r)

    def test_thermal_identity_and_generator_closure_cannot_be_changed(self):
        for key, value in (('area_m2', 57), ('storage_kwh_m2', 1),
                           ('source_generator_kwh_m2', 99), ('variant_id', 'OTHER')):
            contract = copy.deepcopy(self.manifest)
            contract['thermal'][key] = value
            with self.subTest(key=key), self.assertRaises(ValueError):
                m._thermal(contract)

    def test_zero_load_uses_declared_equal_nonactive_power_without_a_heating_map(self):
        r = m._hour(0, None, self.hp)
        self.assertEqual(r['device_reference_electricity_kwh'], .015)
        self.assertEqual((r['active_rating_kwh'], r['inertia_kwh'], r['stage_on_fraction']), (0, 0, 0))
        self.assertEqual(r['source_cells'], [])

    def test_minimum_stage_formula_uses_single_duty_and_total_rating_boundary(self):
        r = m._hour(1, self.points(), self.hp)
        self.assertAlmostEqual(r['stage_on_fraction'], .5)
        self.assertAlmostEqual(r['active_rating_kwh'], 1 / 1.76)
        self.assertAlmostEqual(r['inertia_kwh'], (2 / 1.76) * (140 / 1370) * .5 * .5)
        self.assertAlmostEqual(r['idle_kwh'], .0075)
        self.assertAlmostEqual(r['device_reference_electricity_kwh'], .6047130059721301)
        self.assertEqual(r['source_modes'], ['MIN'])

    def test_zero_and_minimum_limits_are_continuous_for_every_native_temperature(self):
        for ta in (-10, -7, 2, 7, 12, 20):
            pts = self.points(ta)
            minimum = pts[0]
            near_zero = m._hour(minimum['q_kw'] * 1e-12, pts, self.hp)
            below = m._hour(minimum['q_kw'] * (1 - 1e-12), pts, self.hp)
            exact = m._hour(minimum['q_kw'], pts, self.hp)
            with self.subTest(ta=ta):
                self.assertAlmostEqual(near_zero['device_reference_electricity_kwh'], .015, places=10)
                self.assertAlmostEqual(below['device_reference_electricity_kwh'], exact['device_reference_electricity_kwh'], places=10)
                self.assertEqual(exact['active_rating_kwh'], minimum['p_kw'])
                self.assertEqual(exact['inertia_kwh'], 0)
                self.assertEqual(exact['idle_kwh'], 0)

    def test_all_supported_duties_have_nonoverlapping_positive_energy(self):
        for ta in (-10, -7, 2, 7, 12, 20):
            pts = self.points(ta)
            for duty in (.001, .05, .25, .5, .75, .99):
                r = m._hour(pts[0]['q_kw'] * duty, pts, self.hp)
                with self.subTest(ta=ta, duty=duty):
                    self.assertAlmostEqual(r['stage_on_fraction'], duty)
                    self.assertAlmostEqual(r['idle_kwh'] / .015 + r['stage_on_fraction'], 1)
                    self.assertGreaterEqual(r['inertia_kwh'], 0)
                    self.assertLessEqual(r['inertia_kwh'], pts[0]['p_kw'] * (140 / 1370) / 4 + 1e-14)
                    self.assertAlmostEqual(sum(r[k] for k in ('active_rating_kwh', 'inertia_kwh', 'idle_kwh')), r['device_reference_electricity_kwh'])

    def test_continuous_pair_preserves_power_interpolation_and_defrost_cells(self):
        pts = self.points(1)
        q = (pts[0]['q_kw'] + pts[1]['q_kw']) / 2
        r = m._hour(q, pts, self.hp)
        self.assertAlmostEqual(r['device_reference_electricity_kwh'], (pts[0]['p_kw'] + pts[1]['p_kw']) / 2)
        self.assertEqual(r['branch'], 'PAIRED_POWER_CONTINUOUS')
        self.assertTrue(r['mixed_defrost_annotations'])
        self.assertEqual(r['source_modes'], ['MIN', 'MID'])
        self.assertEqual(r['inertia_kwh'] + r['idle_kwh'], 0)

    def test_overload_preserves_unserved_heat_without_a_backup(self):
        pts = self.points()
        q = pts[-1]['q_kw'] + 1
        r = m._hour(q, pts, self.hp)
        self.assertEqual(r['branch'], 'ABOVE_MAX_COMPONENT_ONLY')
        self.assertEqual(r['unserved_heat_kwh'], 1)
        self.assertEqual(r['device_reference_electricity_kwh'], pts[-1]['p_kw'])
        self.assertEqual(r['generator_heat_served_kwh'], pts[-1]['q_kw'])
        self.assertIsNone(r['whole_installed_system_electricity_kwh'])

    def test_missing_reversed_and_conflicting_source_modes_stay_unknown(self):
        cases = []
        missing = self.points(); missing[1] = dict(missing[1], status='Q'); cases.append(missing)
        reversed_modes = copy.deepcopy(self.points()); reversed_modes[1]['q_kw'] = .1; cases.append(reversed_modes)
        conflict = copy.deepcopy(self.points()); conflict[1]['q_kw'] = conflict[0]['q_kw']; conflict[1]['p_kw'] = conflict[0]['p_kw'] + 1; cases.append(conflict)
        cases.append(self.points(-15))
        for points in cases:
            with self.subTest(points=points):
                r = m._hour(1, points, self.hp)
                self.assertEqual(r['status'], 'Q')
                self.assertIsNone(r['device_reference_electricity_kwh'])
                self.assertIsNone(r['generator_heat_served_kwh'])

    def test_invalid_load_and_changed_default_method_fail_closed(self):
        for q in (-1, None, True, float('nan'), float('inf')):
            with self.subTest(q=q), self.assertRaises(ValueError):
                m._hour(q, self.points(), self.hp)
        hp = dict(self.hp, tau_eq_s=30)
        with self.assertRaisesRegex(ValueError, 'default method changed'):
            m._hour(1, self.points(), hp)

    def weather(self, temperatures):
        start = datetime(2025, 1, 1, tzinfo=timezone.utc)
        return [dict(start=start+i*m.HOUR, end=start+(i+1)*m.HOUR, ta_c=ta, source_id='SYNTHETIC')
                for i, ta in enumerate(temperatures)]

    def thermal(self, amount=4):
        return dict(useful_heat_kwh=amount, effective_distribution_heat_kwh=amount/10,
                    generator_heat_kwh=amount*1.1, effective_loss_kw_k=.1, balance_temperature_c=18)

    def test_annual_allocation_preserves_heat_and_electrical_components(self):
        rows, summary = m._calculate(self.weather([-7, 0, 15, 22]), self.thermal(), self.hp, self.models, self.grid)
        self.assertAlmostEqual(sum(r['useful_heat_kwh'] for r in rows), 4)
        self.assertAlmostEqual(sum(r['effective_distribution_heat_kwh'] for r in rows), .4)
        self.assertTrue(summary['complete_generator_service'])
        self.assertAlmostEqual(sum(summary['known_device_components'][k] for k in ('active_rating_kwh', 'inertia_kwh', 'idle_kwh')),
                               summary['annual_device_reference_electricity_kwh'])
        for key in ('whole_installed_system_electricity_kwh', 'physical_spf', 'national_increment_kwh', 'subhourly_peak_kw'):
            self.assertIsNone(summary[key], key)

    def test_no_heating_exposure_cannot_allocate_a_positive_native_total(self):
        with self.assertRaisesRegex(ValueError, 'nonzero heating exposure'):
            m._calculate(self.weather([25, 30]), self.thermal(), self.hp, self.models, self.grid)

    def test_source_gap_does_not_produce_a_false_complete_annual_sum(self):
        rows, summary = m._calculate(self.weather([-15, 0]), self.thermal(), self.hp, self.models, self.grid)
        self.assertEqual(summary['unknown_hours'], 1)
        self.assertFalse(summary['complete_generator_service'])
        self.assertIsNone(summary['annual_device_reference_electricity_kwh'])
        self.assertGreater(summary['known_device_components']['device_reference_electricity_kwh'], 0)

    def test_capacity_shortfall_does_not_become_equal_service_efficiency(self):
        rows, summary = m._calculate(self.weather([-7, 0]), self.thermal(100), self.hp, self.models, self.grid)
        self.assertGreater(summary['source_capacity_shortfall_kwh'], 0)
        self.assertIsNone(summary['annual_device_reference_electricity_kwh'])
        self.assertIsNone(summary['generator_heat_to_device_reference_input_ratio'])

    def test_warm_zero_load_does_not_require_heating_map_extrapolation(self):
        rows, summary = m._calculate(self.weather([-7, 37.5]), self.thermal(), self.hp, self.models, self.grid)
        self.assertEqual(rows[1]['branch'], 'ZERO_HEAT')
        self.assertEqual(rows[1]['device_reference_electricity_kwh'], .015)
        self.assertEqual(rows[1]['source_cells'], [])

    def test_hourly_hold_preserves_energy_and_exact_quarter_boundaries(self):
        rows, _ = m._calculate(self.weather([-7, 0, 15, 22]), self.thermal(), self.hp, self.models, self.grid)
        q = list(m._quarters(rows))
        self.assertEqual(len(q), 16)
        self.assertTrue(all(b-a == m.QUARTER for a,b,_ in q))
        self.assertTrue(all(a[1] == b[0] for a,b in zip(q,q[1:])))
        expected = sum((Decimal(str(r['device_reference_electricity_kwh'])) for r in rows), Decimal(0))
        self.assertEqual(sum((power/4 for _,_,power in q), Decimal(0)), expected)

    def test_quarter_comparison_rejects_unknown_or_reduced_service(self):
        for ta, heat in (([-15, 0], 4), ([-7, 0], 100)):
            rows, _ = m._calculate(self.weather(ta), self.thermal(heat), self.hp, self.models, self.grid)
            with self.assertRaises(ValueError): list(m._quarters(rows))

    def test_every_pinned_repository_dependency_is_checked(self):
        original = Path.read_bytes
        for name in self.manifest['repository_pins']:
            target = m.ROOT/name
            def altered(path): return original(path)+b'\n' if path == target else original(path)
            with self.subTest(name=name), patch.object(Path, 'read_bytes', altered), self.assertRaisesRegex(ValueError, 'repository input changed'):
                m._manifest()

    def test_manifest_and_external_bytes_cannot_be_replaced(self):
        original = Path.read_bytes
        def altered(path): return original(path)+b'\n' if path == m.MANIFEST else original(path)
        with patch.object(Path, 'read_bytes', altered), self.assertRaisesRegex(ValueError, 'manifest mismatch'):
            m._manifest()
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp)/'fake.csv'; p.write_text('ta_C\n0\n')
            with self.assertRaisesRegex(ValueError, 'weather bytes mismatch'):
                m.calculate_reference(weather_path=p)


class WeatherBoundaryTests(unittest.TestCase):
    def sample(self):
        start = datetime(2025, 1, 1, tzinfo=timezone.utc)
        contract = dict(rows=4, start_utc=start.isoformat(), end_utc=(start+4*m.HOUR).isoformat(),
                        recent_endpoint_utc=(start+4*m.HOUR).isoformat(), station_id='44527',
                        history_source_id='HISTORY', recent_source_id='RECENT')
        rows = [dict(interval_start_utc=(start+i*m.HOUR).isoformat(), source_endpoint_utc=(start+(i+1)*m.HOUR).isoformat(),
                     station_id='44527', source_id='RECENT' if i == 3 else 'HISTORY', ta_C=str(-2+i)) for i in range(4)]
        return rows, contract

    def test_exact_source_transition_and_utc_hour_semantics(self):
        rows, contract = self.sample()
        result = m._weather_rows(rows, contract)
        self.assertEqual([r['ta_c'] for r in result], [-2,-1,0,1])
        self.assertEqual(result[-1]['source_id'], 'RECENT')

    def test_shift_gap_duplicate_missing_and_extra_rows_are_rejected(self):
        rows, contract = self.sample()
        for broken in (rows[:-1], rows+[rows[-1]], rows[1:]+rows[:1], rows[:2]+rows[1:2]+rows[3:]):
            with self.subTest(broken=broken), self.assertRaises(ValueError): m._weather_rows(broken, contract)

    def test_identity_and_missing_temperature_cannot_be_substituted(self):
        for field,value in (('station_id','OTHER'),('source_id','OTHER'),('ta_C',''),('ta_C','-999'),
                            ('ta_C','-999.0'),('ta_C','nan'),('ta_C','inf'),('ta_C',True),('ta_C',None)):
            rows,contract=self.sample();rows[0][field]=value
            with self.subTest(field=field,value=value),self.assertRaises(ValueError):m._weather_rows(rows,contract)

    def test_non_utc_and_partial_hours_are_rejected(self):
        for text in ('2025-01-01T00:00:00','2025-01-01T01:00:00+01:00',
                     '2025-01-01T00:15:00Z','2025-01-01T00:00:00.1Z'):
            with self.subTest(text=text),self.assertRaises(ValueError):m._endpoint(text)


class HistoricalCompositionTests(unittest.TestCase):
    def annual(self):
        start = datetime(2025, 1, 1, tzinfo=timezone.utc)
        rows = [dict(interval_start_utc=(start+i*m.HOUR).isoformat(),
                     interval_end_utc=(start+(i+1)*m.HOUR).isoformat(), duration_h=1.0,
                     status='DER', unserved_heat_kwh=0.0, device_reference_electricity_kwh=.015)
                for i in range(8760)]
        return dict(reference_id='SYNTHETIC_COMPOSITION_TEST', rows=rows,
                    summary=dict(complete_generator_service=True,
                                 annual_device_reference_electricity_kwh=131.4))

    def original_rows(self, count=35040, shift_first=False):
        start = datetime(2025, 1, 1, tzinfo=timezone.utc)
        for i in range(count):
            a = start+i*m.QUARTER
            if i == 0 and shift_first: a += timedelta(minutes=1)
            yield SimpleNamespace(start_utc=a, end_utc=a+m.QUARTER,
                                  actual_load_mw=Decimal(2 if i == 0 else 1),
                                  source_reference_residual_mw=Decimal('-.5'))

    @staticmethod
    def consume_original(rows):
        values = list(rows)
        return dict(count=len(values), unchanged_negative_residual=str(values[0].source_reference_residual_mw))

    def test_complete_composition_preserves_source_rows_and_selects_no_programme(self):
        annual = self.annual()
        with patch.object(m, 'calculate_reference', return_value=annual), \
             patch.object(m.historical, 'iter_historical_source_balance', return_value=self.original_rows()) as source, \
             patch.object(m.historical, '_summarize', side_effect=self.consume_original):
            result = m.compare_historical_reference(weather_path=Path('synthetic'), source_paths={'source':'path'}, handoff_paths={'handoff':'path'})
        source.assert_called_once_with({'source':'path'}, {'handoff':'path'})
        self.assertEqual(result['intervals'], 35040)
        self.assertEqual(Decimal(result['reference_device_energy_kwh']), Decimal('131.4'))
        self.assertEqual(result['historical_summary']['unchanged_negative_residual'], '-0.5')
        self.assertEqual(result['coincident_source_load_peak'][0]['reference_device_hour_mean_kw'], '0.015')
        self.assertIsNone(result['programme_adjusted_load'])
        self.assertIsNone(result['national_increment'])
        self.assertFalse(result['existing_heatpump_stock_removed'])

    def test_missing_extra_or_shifted_historical_intervals_fail_closed(self):
        for count, shift in ((35039, False), (35041, False), (35040, True)):
            with self.subTest(count=count, shift=shift), \
                 patch.object(m, 'calculate_reference', return_value=self.annual()), \
                 patch.object(m.historical, 'iter_historical_source_balance', return_value=self.original_rows(count, shift)), \
                 patch.object(m.historical, '_summarize', side_effect=self.consume_original), \
                 self.assertRaises(ValueError):
                m.compare_historical_reference(weather_path=Path('synthetic'), source_paths={}, handoff_paths={})

    def test_quarter_allocation_cannot_accept_a_false_duration_or_energy(self):
        row = self.annual()['rows'][0]
        for change in (dict(duration_h=.25), dict(device_reference_electricity_kwh=True),
                       dict(device_reference_electricity_kwh=float('nan')), dict(status='UNKNOWN')):
            with self.subTest(change=change), self.assertRaises(ValueError):
                list(m._quarters([dict(row, **change)]))


if __name__ == '__main__': unittest.main()
