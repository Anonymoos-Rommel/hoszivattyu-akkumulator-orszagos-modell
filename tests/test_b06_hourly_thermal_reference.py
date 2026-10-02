"""Portable contract and physics checks; all weather/radiation fixtures are synthetic.

These tests do not contain, seek or certify the external observed radiation
extract. Parser/helper fixtures exercise failures without relaxing admission
through the pinned public calculate_reference entry point.
"""
import copy
import hashlib
import inspect
import math
import tempfile
import unittest
from dataclasses import replace
from datetime import datetime, timedelta, timezone
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from modules.B06 import hourly_thermal_reference as model


UTC = timezone.utc


def synthetic_weather(manifest, temperatures=(2.0, -4.0, -4.0, 2.0)):
    """A tiny invented panel, with its own explicit parser-only contract."""
    manifest = copy.deepcopy(manifest)
    contract = manifest['weather']
    first = datetime(2024, 1, 3, 1, tzinfo=UTC)
    rows = [dict(
        timestamp_utc=(first + timedelta(hours=i)).isoformat(),
        outdoor_temperature_C=str(temperature),
        relative_humidity_pct='70', temperature_source_variable='ta',
        station_id=contract['station_id'], source_id=contract['source_id'],
        weather_profile_id=contract['profile_id'], evidence_status='OBS',
    ) for i, temperature in enumerate(temperatures)]
    contract.update(panel_rows=len(rows), first_endpoint_utc=rows[0]['timestamp_utc'],
                    last_endpoint_utc=rows[-1]['timestamp_utc'])
    return rows, manifest


def synthetic_radiation(panel, manifest, observations=None):
    observations = observations or [0.0, 36.0, None, 72.0]
    rows = []
    for weather, sr in zip(panel, observations):
        rows.append(dict(
            station_id=weather['station_id'], source_id=manifest['external_radiation']['source_id'],
            source_endpoint_utc=weather['end'].isoformat(),
            interval_start_utc=weather['start'].isoformat(),
            ta_C=str(weather['ta']), u_pct_at_endpoint=str(weather['rh']),
            sr_J_cm2_native='' if sr is None else str(sr),
            global_energy_kWh_m2_DER='' if sr is None else str(sr / 360),
            global_hour_mean_W_m2_DER='' if sr is None else str(sr * 10000 / 3600),
        ))
    return rows


def synthetic_parameters():
    return dict(outdoor_h_w_k=90.0, lower_boundary_h_w_k=30.0,
                total_h_w_k=120.0, capacity_wh_k=1800.0,
                lower_boundary_temperature_c=8.0, internal_gain_w=100.0,
                initial_node_temperature_c=20.0, latitude_deg=45.0,
                longitude_deg=0.0, ground_shortwave_albedo=0.2,
                ideal_day_target_c=20.0, ideal_night_target_c=18.0,
                day_start_hour_local=6, day_end_hour_local=22,
                supply_coordinate_c=55.0)


def synthetic_windows():
    return dict(A_Calc_Window_North=3.0, A_Calc_Window_East=0.0,
                A_Calc_Window_South=0.0, A_Calc_Window_West=0.0,
                A_Calc_Window_Horizontal=0.0, F_sh_vert=0.7,
                F_f=0.2, F_w=0.9, g_gl_n_Measure_Window_1=0.5)


class PinnedAdmissionTests(unittest.TestCase):
    def setUp(self):
        self.manifest = model._load_manifest(model.MANIFEST_PATH)

    def test_manifest_copy_preserves_admission_but_changed_bytes_do_not(self):
        original = model.MANIFEST_PATH.read_bytes()
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'manifest.json'
            path.write_bytes(original)
            self.assertEqual(model._load_manifest(path), self.manifest)
            path.write_bytes(original + b'\n')
            with self.assertRaisesRegex(ValueError, 'manifest bytes'):
                model._load_manifest(path)

    def test_metadata_and_scenario_edits_cannot_repin_themselves(self):
        import json
        mutations = (
            lambda m: m['sources'][0].update(source_id='SUBSTITUTE'),
            lambda m: m['sources'][0].update(reuse_status='PUBLIC'),
            lambda m: m['scenario']['lower_boundary_temperature_c'].update(value=12),
            lambda m: m['scenario']['supply_coordinate_c'].update(value=35),
            lambda m: m['weather'].update(solar_unit='kWh/m2'),
            lambda m: m['weather'].update(temperature_support='INSTANTANEOUS'),
            lambda m: m['building']['parameter_lineage']['c_m'].update(native_unit='J/K'),
            lambda m: m['external_radiation'].update(sha256=hashlib.sha256(b'new source').hexdigest()),
        )
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'manifest.json'
            for mutate in mutations:
                changed = copy.deepcopy(self.manifest)
                mutate(changed)
                path.write_text(json.dumps(changed))
                with self.subTest(mutation=mutate), self.assertRaisesRegex(ValueError, 'manifest bytes'):
                    model._load_manifest(path)

    def test_every_pinned_source_and_metadata_file_is_verified(self):
        read_bytes = Path.read_bytes
        for name, pin in self.manifest['repository_pins'].items():
            target = model.ROOT / pin['path']

            def changed_bytes(path):
                value = read_bytes(path)
                return value + b'\n' if path == target else value

            with self.subTest(source=name), patch.object(Path, 'read_bytes', changed_bytes):
                with self.assertRaisesRegex(ValueError, 'source/code hash mismatch'):
                    model._load_manifest(model.MANIFEST_PATH)

    def test_substitute_radiation_is_rejected_before_parsing(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'synthetic.csv'
            path.write_text('station_id,sr_J_cm2_native\nSYNTHETIC,0\n')
            with patch.object(model, '_parse_radiation_rows') as parser:
                with self.assertRaisesRegex(ValueError, 'bytes/hash mismatch'):
                    model._load_radiation(path, [], self.manifest)
                parser.assert_not_called()

    def test_public_entry_point_has_no_scenario_or_mapping_override(self):
        signature = inspect.signature(model.calculate_reference)
        self.assertEqual(set(signature.parameters), {'radiation_path', 'manifest_path'})
        for parameter in signature.parameters.values():
            self.assertEqual(parameter.kind, inspect.Parameter.KEYWORD_ONLY)
            self.assertIsNone(parameter.default)
        for kwargs in ({'scenario': {}}, {'radiation_by_endpoint': {}},
                       {'supply_coordinate_c': 35}, {'initial_node_temperature_c': 0}):
            with self.subTest(kwargs=kwargs), self.assertRaises(TypeError):
                model.calculate_reference(**kwargs)

    def test_hourly_parameters_exclude_seasonal_factors_and_annual_heat(self):
        item = model._source_building(self.manifest)
        original = model._build_parameters(item, self.manifest)
        changed = copy.deepcopy(item)
        for key in self.manifest['excluded_source_fields']:
            changed['values'][key] = 987654321.0
        self.assertEqual(model._build_parameters(changed, self.manifest), original)
        values = item['values']
        self.assertAlmostEqual(original['capacity_wh_k'], values['c_m'] * values['A_C_Ref'])
        self.assertAlmostEqual(original['lower_boundary_h_w_k'],
                               sum(original['component_h_w_k'][key] for key in ('Floor_1', 'Floor_2')))
        self.assertAlmostEqual(original['total_h_w_k'],
                               original['outdoor_h_w_k'] + original['lower_boundary_h_w_k'])
        glazing = self.manifest['building']['parameter_lineage']['g_gl_n_Measure_Window_1']
        self.assertEqual(glazing['used_unit'], 'ratio')
        self.assertTrue(glazing['unit_qualification'])

    def test_absent_external_input_returns_q_without_invented_totals(self):
        result = model.calculate_reference()
        self.assertEqual(result['radiation_input_status'], 'Q_MISSING_EXTERNAL_RADIATION')
        self.assertEqual(result['hours'], self.manifest['weather']['hours'])
        self.assertEqual(result['missing_solar_hours'], result['hours'])
        self.assertIsNone(result['verified_radiation_sha256'])
        for mode in ('ideal', 'capacity_limited'):
            summary = result['summary'][mode]
            self.assertEqual(summary['status'], 'Q_INCOMPLETE_PERIOD')
            self.assertEqual(summary['supported_hours'], 0)
            for key in ('heat_kwh', 'min_node_temperature_c', 'max_heat_kw',
                        'target_deficit_degree_hours', 'total_storage_change_kwh'):
                self.assertIsNone(summary[key])
            for row in result['rows']:
                self.assertEqual(row[mode]['status'], 'Q')
                self.assertIsNone(row[mode]['t_end_c'])
        self.assertEqual(result['fixed_path']['status'], 'Q_INCOMPLETE_CAPACITY_COMPARISON')
        self.assertIsNone(result['fixed_path']['required_thermal_energy_kwh'])
        for key in ('actual_electricity_kwh', 'actual_spf', 'emitter_required_supply_c',
                    'dhw_kwh', 'population_weight', 'auxiliary_electricity_kwh',
                    'cycling_electricity_kwh', 'defrost_electricity_kwh',
                    'equal_service_heat_savings_kwh'):
            self.assertIsNone(result[key])
        for key in ('whole_slice_complete', 'empirical_model_validation',
                    'national_comfort_policy_selected', 'seasonal_annual_heat_consumed',
                    'seasonal_ground_factor_consumed'):
            self.assertFalse(result[key])
        self.assertEqual(result['evidence_status'], 'SCN')
        self.assertEqual(result['evidence_tier'], 'E3_SCENARIO_ONLY_NO_CANONICAL_BASE_ADMISSION')

    def test_explicit_missing_external_path_does_not_silently_use_no_input(self):
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(FileNotFoundError):
                model.calculate_reference(radiation_path=Path(directory) / 'missing.csv')


class SyntheticForcingContractTests(unittest.TestCase):
    def setUp(self):
        manifest = model._load_manifest(model.MANIFEST_PATH)
        self.weather_rows, self.manifest = synthetic_weather(manifest)
        self.panel = model._parse_weather_rows(self.weather_rows, self.manifest)
        self.radiation_rows = synthetic_radiation(self.panel, self.manifest)

    def test_weather_uses_preceding_hour_and_preserves_endpoint_humidity(self):
        first = self.panel[0]
        self.assertEqual(first['start'], datetime(2024, 1, 3, 0, tzinfo=UTC))
        self.assertEqual(first['end'] - first['start'], timedelta(hours=1))
        self.assertEqual(first['ta'], 2)
        self.assertEqual(first['rh'], 70)

    def test_weather_missing_duplicate_wrong_source_or_boundary_fails_closed(self):
        changes = (
            lambda rows: rows.pop(),
            lambda rows: rows.__setitem__(1, copy.deepcopy(rows[0])),
            lambda rows: rows[1].update(source_id='OTHER'),
            lambda rows: rows[1].update(station_id='OTHER'),
            lambda rows: rows[1].update(weather_profile_id='OTHER'),
            lambda rows: rows[1].update(temperature_source_variable='t'),
            lambda rows: rows[1].update(evidence_status='SCN'),
            lambda rows: rows[1].update(timestamp_utc='2024-01-03T02:30:00+00:00'),
            lambda rows: rows[1].update(timestamp_utc='2024-01-03T02:00:00'),
            lambda rows: rows[1].update(outdoor_temperature_C='-999'),
            lambda rows: rows[1].update(outdoor_temperature_C='nan'),
            lambda rows: rows[1].update(relative_humidity_pct='101'),
        )
        for change in changes:
            rows = copy.deepcopy(self.weather_rows)
            change(rows)
            with self.subTest(change=change), self.assertRaises(ValueError):
                model._parse_weather_rows(rows, self.manifest)

    def test_cold_window_selection_uses_temperature_and_earliest_tie(self):
        rows, manifest = synthetic_weather(self.manifest, (-2, -2, -2, 5))
        panel = model._parse_weather_rows(rows, manifest)
        manifest['weather'].update(hours=2, selection_index=0,
                                   physical_start_utc=panel[0]['start'].isoformat(),
                                   physical_end_utc=panel[1]['end'].isoformat())
        self.assertEqual(model._select_weather(panel, manifest), panel[:2])
        manifest['weather']['selection_index'] = 1
        with self.assertRaisesRegex(ValueError, 'selection drift'):
            model._select_weather(panel, manifest)

    def test_radiation_units_observed_zero_and_missing_remain_distinct(self):
        parsed = model._parse_radiation_rows(self.radiation_rows, self.panel, self.manifest)
        self.assertEqual(list(parsed), [w['start'] for w in self.panel])
        self.assertEqual(list(parsed.values()), [0, 36, None, 72])
        self.radiation_rows[2]['sr_J_cm2_native'] = '-999'
        self.assertIsNone(model._parse_radiation_rows(
            self.radiation_rows, self.panel, self.manifest)[self.panel[2]['start']])
        self.assertEqual(float(self.radiation_rows[1]['global_energy_kWh_m2_DER']), 0.1)
        self.assertEqual(float(self.radiation_rows[1]['global_hour_mean_W_m2_DER']), 100)

    def test_radiation_schema_units_joint_identity_and_time_join_fail_closed(self):
        changes = (
            lambda rows: rows.pop(),
            lambda rows: rows.__setitem__(1, copy.deepcopy(rows[0])),
            lambda rows: rows.reverse(),
            lambda rows: rows[1].update(source_id='OTHER'),
            lambda rows: rows[1].update(station_id='OTHER'),
            lambda rows: rows[1].update(ta_C='-3'),
            lambda rows: rows[1].update(u_pct_at_endpoint='71'),
            lambda rows: rows[1].update(interval_start_utc=rows[1]['source_endpoint_utc']),
            lambda rows: rows[1].update(source_endpoint_utc='2024-01-03T02:30:00+00:00'),
            lambda rows: rows[1].update(global_energy_kWh_m2_DER='100'),
            lambda rows: rows[1].update(global_hour_mean_W_m2_DER='0.1'),
            lambda rows: rows[1].update(sr_J_cm2_native='nan'),
            lambda rows: rows[1].update(sr_J_cm2_native='inf'),
            lambda rows: rows[1].update(sr_J_cm2_native='-1'),
            lambda rows: rows[1].update(sr_J_cm2_native=''),
            lambda rows: rows[2].update(global_hour_mean_W_m2_DER='0'),
            lambda rows: rows[1].__setitem__('sr_kWh_m2', rows[1].pop('sr_J_cm2_native')),
        )
        for change in changes:
            rows = copy.deepcopy(self.radiation_rows)
            change(rows)
            with self.subTest(change=change), self.assertRaises(ValueError):
                model._parse_radiation_rows(rows, self.panel, self.manifest)


class IndependentPhysicsTests(unittest.TestCase):
    def setUp(self):
        self.p = synthetic_parameters()
        self.windows = synthetic_windows()

    def test_exact_transition_matches_independent_seconds_joules_integration(self):
        # RK4 integrates dT/dseconds, independently of the Wh/hour analytic form.
        for initial, outdoor, gains, heat, hours in ((15, -8, 150, 2700, 1),
                (23, 4, 250, 0, 0.5), (18, -3, 100, 3600, 2)):
            temperature = float(initial)
            steps = 720
            dt = hours * 3600 / steps
            def derivative(value):
                return (90 * (outdoor - value) + 30 * (8 - value) + gains + heat) / (1800 * 3600)
            for _ in range(steps):
                k1 = derivative(temperature)
                k2 = derivative(temperature + dt * k1 / 2)
                k3 = derivative(temperature + dt * k2 / 2)
                k4 = derivative(temperature + dt * k3)
                temperature += dt * (k1 + 2 * k2 + 2 * k3 + k4) / 6
            output = model.transition(initial, outdoor, gains, heat, self.p, hours)
            self.assertAlmostEqual(output['t_end_c'], temperature, places=10)
            self.assertAlmostEqual(output['storage_change_wh'],
                (gains + heat) * hours - output['outdoor_loss_wh'] - output['lower_boundary_loss_wh'], places=8)

    def test_semigroup_energy_partition_and_equilibrium(self):
        whole = model.transition(19, -2, 180, 2200, self.p, 2)
        first = model.transition(19, -2, 180, 2200, self.p, 0.75)
        second = model.transition(first['t_end_c'], -2, 180, 2200, self.p, 1.25)
        self.assertAlmostEqual(whole['t_end_c'], second['t_end_c'], places=12)
        for key in ('storage_change_wh', 'outdoor_loss_wh', 'lower_boundary_loss_wh'):
            self.assertAlmostEqual(whole[key], first[key] + second[key], places=8)
        equilibrium = model.transition(8, 8, 0, 0, self.p)
        self.assertEqual(equilibrium['t_end_c'], 8)
        for key in ('storage_change_wh', 'outdoor_loss_wh', 'lower_boundary_loss_wh'):
            self.assertEqual(equilibrium[key], 0)

    def test_endpoint_controller_does_not_claim_instantaneous_recovery(self):
        request = model.required_heat(17, -3, 100, 20, self.p)
        step = model.transition(17, -3, 100, request, self.p)
        self.assertAlmostEqual(step['t_end_c'], 20, places=12)
        deficit = model.deficit_degree_hours(17, step, 20, self.p)
        self.assertGreater(deficit, 0)
        self.assertLess(deficit, 3)
        self.assertEqual(model.required_heat(25, 25, 100, 18, self.p), 0)

    def test_deficit_integral_handles_crossing_in_both_directions(self):
        for initial, outdoor, heat, target in ((17, -3, 9000, 20), (23, -8, 0, 22)):
            step = model.transition(initial, outdoor, 100, heat, self.p)
            samples = 20000
            numeric = sum(max(0, target - model.transition(initial, outdoor, 100, heat,
                self.p, (i + 0.5) / samples)['t_end_c']) for i in range(samples)) / samples
            self.assertAlmostEqual(model.deficit_degree_hours(initial, step, target, self.p), numeric, places=7)

    def test_solar_energy_conversion_closure_and_low_sun_rule(self):
        for hour in (0, 6, 12, 18):
            at = datetime(2024, 1, 3, hour, 30, tzinfo=UTC)
            solar = model.solar_gain(36, at, self.windows, self.p)
            self.assertAlmostEqual(solar['ghi_w_m2'], 100)
            self.assertAlmostEqual(solar['horizontal_radiation_closure_w_m2'], 0, places=10)
            self.assertGreaterEqual(solar['solar_gain_scn_w'], 0)
            if solar['solar_low_sun_rule_applied']:
                self.assertEqual(solar['dni_scn_w_m2'], 0)
                self.assertEqual(solar['dhi_scn_w_m2'], 100)
            self.assertEqual(model.solar_gain(0, at, self.windows, self.p)['solar_gain_scn_w'], 0)
        changed = dict(self.windows, A_Calc_Window_South=1)
        with self.assertRaisesRegex(ValueError, 'north-only'):
            model.solar_gain(36, at, changed, self.p)

    def test_numeric_missing_nonfinite_and_invalid_capacity_are_rejected(self):
        at = datetime(2024, 1, 3, 12, tzinfo=UTC)
        for value in (None, True, float('nan'), float('inf'), -999):
            with self.subTest(value=value), self.assertRaises(ValueError):
                model.solar_gain(value, at, self.windows, self.p)
        for value in (None, True, float('nan'), float('inf')):
            with self.subTest(value=value), self.assertRaises(ValueError):
                model.transition(value, 0, 100, 1000, self.p)
        for value in (0, -1, float('nan')):
            with self.subTest(capacity=value), self.assertRaises(ValueError):
                model.transition(20, 0, 100, 1000, dict(self.p, capacity_wh_k=value))
        for hours in (0, -1):
            with self.subTest(hours=hours), self.assertRaises(ValueError):
                model.transition(20, 0, 100, 1000, self.p, hours)


class SyntheticCoupledStateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        manifest = model._load_manifest(model.MANIFEST_PATH)
        weather_rows, manifest = synthetic_weather(manifest, (-8.0,) * 24)
        cls.weather = model._parse_weather_rows(weather_rows, manifest)
        cls.radiation = {row['start']: 0.0 for row in cls.weather}
        cls.p = synthetic_parameters()
        cls.windows = synthetic_windows()
        cls.source_map = model.wm50.load_wm50_reference('MAX', fixed_supply_c=55)
        cls.grid = model.wm50.source_grid()
        cls.result = cls.run_case(cls.weather, cls.radiation)

    @classmethod
    def run_case(cls, weather, radiation):
        return model._simulate(weather, radiation, cls.windows, cls.p,
                               cls.source_map, cls.grid, 'Europe/Budapest')

    def test_hourly_and_period_energy_balance_with_continuous_states(self):
        rows = self.result['rows']
        for mode in ('ideal', 'capacity_limited'):
            self.assertEqual(rows[0][mode]['t_start_c'], self.p['initial_node_temperature_c'])
            for previous, current in zip(rows, rows[1:]):
                self.assertEqual(previous[mode]['t_end_c'], current[mode]['t_start_c'])
            for row in rows:
                state = row[mode]
                storage = self.p['capacity_wh_k'] * (state['t_end_c'] - state['t_start_c'])
                net_heat = (state['delivered_heat_kwh'] + state['internal_gain_kwh']
                            + state['solar_gain_kwh']) * 1000
                self.assertAlmostEqual(storage,
                    net_heat - state['outdoor_loss_wh'] - state['lower_boundary_loss_wh'], places=8)
            summary = self.result['summary'][mode]
            storage = self.p['capacity_wh_k'] * (rows[-1][mode]['t_end_c']
                                                - rows[0][mode]['t_start_c']) / 1000
            net_heat = summary['heat_kwh'] + summary['internal_gain_kwh'] + summary['solar_gain_kwh']
            self.assertAlmostEqual(storage, summary['total_storage_change_kwh'], places=10)
            self.assertAlmostEqual(storage,
                net_heat - summary['outdoor_exchange_kwh'] - summary['lower_boundary_exchange_kwh'], places=10)

    def test_zero_is_supported_but_missing_solar_invalidates_all_following_states(self):
        self.assertEqual(self.result['summary']['ideal']['supported_hours'], 24)
        for missing_form in ('absent', 'explicit_none'):
            radiation = dict(self.radiation)
            start = self.weather[5]['start']
            if missing_form == 'absent':
                del radiation[start]
            else:
                radiation[start] = None
            result = self.run_case(self.weather, radiation)
            for mode in ('ideal', 'capacity_limited'):
                self.assertEqual(result['summary'][mode]['supported_hours'], 5)
                self.assertIsNone(result['summary'][mode]['heat_kwh'])
                self.assertIsNone(result['summary'][mode]['target_deficit_degree_hours'])
                for row in result['rows'][5:]:
                    self.assertEqual(row[mode]['status'], 'Q')
                    self.assertIsNone(row[mode]['t_end_c'])
                for row in result['rows'][6:]:
                    self.assertIsNone(row[mode]['t_start_c'])
            self.assertEqual(result['fixed_path']['unknown_thermal_path_hours'], 19)
            self.assertIsNone(result['fixed_path']['required_thermal_energy_kwh'])
            self.assertIsNone(result['fixed_path']['additional_thermal_requirement_kwh'])

    def test_unknown_capacity_preserves_ideal_path_and_blocks_dependent_period(self):
        weather = copy.deepcopy(self.weather)
        weather[5]['ta'] = -35.0
        result = self.run_case(weather, self.radiation)
        self.assertIsNone(result['rows'][5]['manufacturer_capacity_kw'])
        self.assertEqual(result['summary']['ideal']['supported_hours'], 24)
        self.assertEqual(result['summary']['capacity_limited']['supported_hours'], 5)
        self.assertIsNone(result['summary']['capacity_limited']['heat_kwh'])
        self.assertIsNone(result['summary']['ideal']['below_minimum_modulation_hours'])
        for row in result['rows'][5:]:
            self.assertEqual(row['ideal']['status'], 'SCN')
            self.assertEqual(row['capacity_limited']['status'], 'Q')
        fixed = result['fixed_path']
        self.assertEqual(fixed['unknown_capacity_hours'], 1)
        self.assertEqual(fixed['unknown_thermal_path_hours'], 0)
        self.assertAlmostEqual(fixed['required_thermal_energy_kwh'], result['summary']['ideal']['heat_kwh'])
        for key in ('additional_thermal_requirement_kwh', 'peak_additional_thermal_requirement_kw',
                    'capacity_covered_thermal_requirement_kwh', 'same_service_capacity_feasible',
                    'capacity_deficit_hours'):
            self.assertIsNone(fixed[key])
        # Capacity support resumes for fixed-path comparison; the clipped state cannot restart.
        self.assertTrue(fixed['rows'][6]['source_supported'])
        self.assertIsNone(result['rows'][6]['capacity_limited']['t_start_c'])

    def test_continuous_same_service_path_satisfies_first_law_between_endpoints(self):
        fixed = self.result['fixed_path']
        self.assertTrue(fixed['full_prescribed_thermal_service_preserved'])
        self.assertFalse(fixed['alternative_temperature_state_evolved'])
        for row, comparison in zip(self.result['rows'], fixed['rows']):
            self.assertEqual(comparison['start_temperature_c'], row['ideal']['t_start_c'])
            self.assertEqual(comparison['end_temperature_c'], row['ideal']['t_end_c'])
            for fraction in (0, 0.07, 0.19, 0.43, 0.71, 0.93, 1):
                temperature, derivative = model.prescribed_state(row, self.p, fraction)
                first_law_heat = (1800 * derivative + 90 * (temperature - row['ta_observed_c'])
                                  + 30 * (temperature - 8) - 100 - row['solar_gain_scn_w'])
                self.assertAlmostEqual(first_law_heat, row['ideal']['command_heat_w'], places=8)
                self.assertAlmostEqual(model.heat_to_follow_path(row, self.p, fraction),
                                       first_law_heat, places=10)
            for fraction, endpoint in ((0, 't_start_c'), (1, 't_end_c')):
                self.assertAlmostEqual(model.prescribed_state(row, self.p, fraction)[0],
                                       row['ideal'][endpoint], places=12)
        self.assertAlmostEqual(fixed['required_thermal_energy_kwh'], self.result['summary']['ideal']['heat_kwh'])
        self.assertAlmostEqual(fixed['capacity_covered_thermal_requirement_kwh']
            + fixed['additional_thermal_requirement_kwh'], fixed['required_thermal_energy_kwh'])
        self.assertGreater(fixed['additional_thermal_requirement_kwh'], 0)
        self.assertFalse(fixed['same_service_capacity_feasible'])
        self.assertEqual(fixed['peak_additional_thermal_requirement_kw'],
                         max(row['additional_thermal_requirement_kw'] for row in fixed['rows']))

    def test_same_service_identity_detects_changed_path_or_heat(self):
        for field in ('equilibrium_c', 't_start_c', 't_end_c', 'command_heat_w'):
            rows = copy.deepcopy(self.result['rows'])
            rows[5]['ideal'][field] += 0.25
            with self.subTest(field=field), self.assertRaises(ValueError):
                model._fixed_path(rows, self.p)
        for fraction in (-0.1, 1.1, True, float('nan')):
            with self.subTest(fraction=fraction), self.assertRaises(ValueError):
                model.prescribed_state(self.result['rows'][0], self.p, fraction)

    def test_fixed_path_rejects_interval_gaps_and_state_resumption_after_q(self):
        rows = copy.deepcopy(self.result['rows'])
        for key in ('interval_start_utc', 'interval_end_utc'):
            rows[5][key] = (datetime.fromisoformat(rows[5][key]) + timedelta(hours=1)).isoformat()
        with self.assertRaisesRegex(ValueError, 'interval boundary/continuity'):
            model._fixed_path(rows, self.p)
        rows = copy.deepcopy(self.result['rows'])
        rows[5]['ideal'].update(status='Q', t_end_c=None)
        with self.assertRaisesRegex(ValueError, 'state continuity'):
            model._fixed_path(rows, self.p)

    def test_capacity_clipping_cannot_be_presented_as_equal_service_savings(self):
        ideal, clipped = (self.result['summary'][key] for key in ('ideal', 'capacity_limited'))
        self.assertLess(clipped['heat_kwh'], ideal['heat_kwh'])
        self.assertGreater(clipped['target_deficit_degree_hours'], ideal['target_deficit_degree_hours'])
        self.assertGreater(clipped['capacity_clipped_hours'], 0)
        self.assertEqual(self.result['service_comparison_status'],
                         'CLIPPED_BRANCH_REDUCES_SERVICE_NOT_AN_EFFICIENCY_COMPARISON')
        self.assertIsNone(self.result['equal_service_heat_savings_kwh'])
        for row in self.result['rows']:
            self.assertLessEqual(row['capacity_limited']['delivered_heat_kwh'], row['manufacturer_capacity_kw'])
            self.assertLessEqual(row['capacity_limited']['t_end_c'], row['ideal']['t_end_c'] + 1e-10)
            self.assertAlmostEqual(row['manufacturer_capacity_kw'],
                                   row['source_condition_input_kw'] * row['source_condition_cop'])

    def test_source_ratings_and_below_minimum_flags_never_invent_actual_electricity(self):
        self.assertGreater(self.result['summary']['capacity_limited']['below_minimum_modulation_hours'], 0)
        for key in ('actual_electricity_kwh', 'actual_spf'):
            self.assertIsNone(self.result[key])
            self.assertIsNone(self.result['fixed_path'][key])
        for key in ('backup_equipment', 'backup_electricity_kwh',
                    'selected_dispatch_policy', 'selected_additional_capacity_kw'):
            self.assertIsNone(self.result['fixed_path'][key])
        annotations = {cell['defrost_source_annotation']
                       for row in self.result['rows'] for cell in row['map_support_cells']}
        self.assertTrue(annotations)
        self.assertTrue(all(row['map_support_cells'] for row in self.result['rows']))

    def test_radiation_gain_reaches_the_thermal_balance_once(self):
        radiation = dict(self.radiation)
        radiation[self.weather[11]['start']] = 36.0
        result = self.run_case(self.weather, radiation)
        for mode in ('ideal', 'capacity_limited'):
            before, after = self.result['rows'][11][mode], result['rows'][11][mode]
            self.assertGreater(after['solar_gain_kwh'], 0)
            self.assertAlmostEqual(before['t_start_c'], after['t_start_c'])
            self.assertAlmostEqual(before['t_end_c'], after['t_end_c'])
            self.assertAlmostEqual(before['delivered_heat_kwh'] - after['delivered_heat_kwh'],
                                   after['solar_gain_kwh'], places=10)
            self.assertAlmostEqual(result['summary'][mode]['solar_gain_kwh'],
                                   result['rows'][11]['solar_gain_scn_w'] / 1000)

    def test_manufacturer_identity_coordinates_and_energy_pair_cannot_be_substituted(self):
        original = self.source_map.evaluate(-8, 55)
        changes = (
            {'source_ids': ('SUBSTITUTE',)}, {'evidence_status': 'OBS'},
            {'supply_temperature_c': 35}, {'outdoor_temperature_c': -7},
            {'cop': original.point.cop + 1}, {'thermal_capacity_kw': -1},
            {'min_modulation_kw': original.point.thermal_capacity_kw + 1},
        )
        for changeset in changes:
            substituted = replace(original, point=replace(original.point, **changeset))
            fake_map = SimpleNamespace(evaluate=lambda *_: substituted)
            with self.subTest(changes=changeset), self.assertRaises(ValueError):
                model._capacity(fake_map, self.grid, -8, 55)
        unsupported = replace(original, status='DER', point=None)
        with self.assertRaisesRegex(ValueError, 'requires Q'):
            model._capacity(SimpleNamespace(evaluate=lambda *_: unsupported), self.grid, -8, 55)


if __name__ == '__main__':
    unittest.main()
