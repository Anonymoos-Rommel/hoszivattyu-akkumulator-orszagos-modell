import copy
import json
import math
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from modules.B11 import annual_retrofit_reference as family


class AnnualRetrofitReferenceTests(unittest.TestCase):
    def setUp(self):
        self.manifest = family._manifest()
        self.raw_rows = {}
        def calculation(weather, thermal, hp, models, grid):
            # Explicit composition fixture: physical numerical methods and real
            # external chronology are independently exercised by B05/replay.
            label = next(k for k, c in self.manifest['cases'].items()
                         if c['thermal']['variant_id'] == thermal['variant_id'])
            complete = label != 'original'
            energy = {'original': 6517.5, 'standard': 3345.7, 'ambitious': 2472.6}[label]
            rows = [dict(marker=label, source_defrost_labels=['grey', 'unmarked'])]
            self.raw_rows[label] = rows
            return rows, dict(complete_generator_service=complete, unknown_hours=0,
                              source_capacity_shortfall_kwh=0.0 if complete else 170.0,
                              hours=8760, annual_device_reference_electricity_kwh=energy if complete else None,
                              known_device_components={'device_reference_electricity_kwh': energy},
                              mixed_defrost_support_hours={'original': 2825, 'standard': 1638, 'ambitious': 58}[label])
        with patch.object(family.device, '_weather', return_value=[]), patch.object(family.device, '_calculate', side_effect=calculation):
            self.result = family.calculate_family_reference(weather_path=Path('explicit-composition-fixture'))

    def compare(self, after='standard', result=None):
        return family._compare(result or self.result, after, family.SOURCE_PACKAGE_REPLACEMENT)

    def test_three_native_source_accounts_preserve_distinct_systems(self):
        expected = {'original': (21085.5682647916, 168.56, 1.3),
                    'standard': (8891.581877418394, 156.8, 1.05),
                    'ambitious': (6353.082153236605, 156.8, 1.05)}
        for label, (fuel, aux, factor) in expected.items():
            with self.subTest(label=label):
                g = self.result['cases'][label]['native_gas_reference']
                self.assertAlmostEqual(g['source_allocated_heating_gas_kwh_gcv'], fuel)
                self.assertAlmostEqual(g['source_allocated_heating_auxiliary_kwh'], aux)
                self.assertEqual(g['source_generator_expenditure_gcv'], factor)
                self.assertIsNone(g['gas_volume_m3'])
                self.assertIsNone(g['gas_hourly_profile'])

    def test_source_service_convention_retains_envelope_response(self):
        self.assertEqual(self.result['service_convention']['nominal_indoor_c'], 20)
        values = [self.result['cases'][k] for k in ('original', 'standard', 'ambitious')]
        self.assertEqual([v['source_infiltration_h_inv'] for v in values], [0.4, 0.1, 0.1])
        self.assertEqual([v['source_nonuniform_heating_factor'] for v in values],
                         [0.8, 0.86052861200195, 0.8856106005758195])
        self.assertIn('not an identical measured', self.result['service_convention']['description'])

    def test_device_rows_and_defrost_annotations_are_not_modified(self):
        for label, case in self.result['cases'].items():
            self.assertIs(case['device_reference']['rows'], self.raw_rows[label])
            self.assertEqual(case['device_reference']['rows'][0]['source_defrost_labels'], ['grey', 'unmarked'])
        self.assertEqual([self.result['cases'][k]['device_reference']['summary']['mixed_defrost_support_hours']
                          for k in ('original', 'standard', 'ambitious')], [2825, 1638, 58])

    def test_original_partial_sum_is_not_complete_annual_electricity(self):
        s = self.result['cases']['original']['device_reference']['summary']
        self.assertFalse(s['complete_generator_service'])
        self.assertEqual(s['known_device_components']['device_reference_electricity_kwh'], 6517.5)
        self.assertGreater(s['source_capacity_shortfall_kwh'], 0)
        self.assertIsNone(s['annual_device_reference_electricity_kwh'])
        self.assertIsNone(self.result['original_full_service_hp_reduction_kwh'])

    def test_original_hp_cannot_be_selected_as_complete_after_case(self):
        with self.assertRaisesRegex(ValueError, 'standard/ambitious'):
            self.compare('original')

    def test_package_path_uses_original_gas_and_auxiliary_baseline(self):
        for label, energy in [('standard', 3345.7), ('ambitious', 2472.6)]:
            with self.subTest(label=label):
                r = self.compare(label)
                self.assertAlmostEqual(r['before']['source_allocated_gas_kwh_gcv'], 21085.5682647916)
                self.assertAlmostEqual(r['before']['source_allocated_auxiliary_kwh'], 168.56)
                self.assertAlmostEqual(r['electricity_change']['known_intercept_kwh'], energy - 168.56)
                self.assertAlmostEqual(r['purchased_final_energy_reduction']['known_intercept_kwh'],
                                       21085.5682647916 + 168.56 - energy)
                self.assertNotEqual(r['before']['variant_id'], r['after']['variant_id'])

    def test_explicit_condition_and_derived_status_do_not_admit_national_policy(self):
        r = self.compare()
        self.assertEqual(r['condition']['evidence_status'], 'SCN')
        self.assertEqual((r['evidence_status'], r['evidence_tier']), ('DER', 'E2'))
        self.assertFalse(r['national_admission'])
        self.assertFalse(r['dhw_changes_included'])
        self.assertFalse(r['native_dhw_solar_or_appliance_changes_adopted'])

    def test_case_residuals_are_not_cancelled_or_bounded(self):
        a, b = self.compare('standard'), self.compare('ambitious')
        self.assertNotEqual(a['residual']['name'], b['residual']['name'])
        self.assertFalse(self.result['standard_to_ambitious']['residuals_presumed_equal'])
        self.assertAlmostEqual(self.result['standard_to_ambitious']['device_only_reduction_kwh'], 873.1)
        self.assertIsNone(self.result['standard_to_ambitious']['installed_reduction_kwh'])
        for r in (a, b):
            self.assertIn('combi controls', r['residual']['definition'])
            for key in ('value_kwh', 'timing', 'upper_bound_kwh'):
                self.assertIsNone(r['residual'][key])
            self.assertIsNone(r['electricity_change']['total_kwh'])
            self.assertIsNone(r['purchased_final_energy_reduction']['total_kwh'])

    def test_unsupported_whole_system_and_downstream_fields_remain_unknown(self):
        r = self.compare()
        for key in ('installed_system_savings_kwh', 'net_grid_increment_profile', 'gas_volume_m3',
                    'import_value', 'household_savings', 'physical_spf', 'national_increment',
                    'measured_whole_boiler_fuel_savings_kwh_gcv'):
            with self.subTest(key=key):
                self.assertIsNone(r[key])
        self.assertIsNone(r['after']['complete_system_electricity_kwh'])

    def test_incomplete_after_service_never_receives_backup_or_full_ledger(self):
        for field, value in [('complete_generator_service', False), ('complete_generator_service', 1),
                             ('unknown_hours', 1), ('source_capacity_shortfall_kwh', 0.1), ('hours', 8784)]:
            with self.subTest(field=field, value=value):
                r = copy.deepcopy(self.result)
                r['cases']['standard']['device_reference']['summary'][field] = value
                with self.assertRaisesRegex(ValueError, 'complete after-case'):
                    self.compare(result=r)

    def test_unknown_or_invalid_complete_energy_is_not_replaced_by_partial_sum(self):
        for value in (None, True, 0, -1, math.nan, math.inf):
            with self.subTest(value=value):
                r = copy.deepcopy(self.result)
                r['cases']['standard']['device_reference']['summary']['annual_device_reference_electricity_kwh'] = value
                with self.assertRaisesRegex(ValueError, 'complete after-case device electricity'):
                    self.compare(result=r)

    def test_native_gas_factor_cannot_be_replaced_by_efficiency_or_dhw_total(self):
        case = self.manifest['cases']['original']
        thermal = self.result['cases']['original']['device_reference']['thermal_reference']
        for field, value in [('energy_basis', 'LHV'), ('expenditure_factor', 1/1.3),
                             ('heating_fuel_kwh_gcv_m2', case['gas']['heating_fuel_kwh_gcv_m2'] + 10)]:
            with self.subTest(field=field):
                c = copy.deepcopy(case)
                c['gas'][field] = value
                with self.assertRaises(ValueError):
                    family._native_gas(c, thermal)

    def test_public_path_requires_case_and_condition_before_source_access(self):
        with self.assertRaises(TypeError):
            family.compare_original_to_retrofit(weather_path=Path('absent'))
        with patch.object(family, 'calculate_family_reference') as producer:
            for case, condition in [('original', family.SOURCE_PACKAGE_REPLACEMENT),
                                    ('standard', None), ('ambitious', True), ('national', family.SOURCE_PACKAGE_REPLACEMENT)]:
                with self.subTest(case=case, condition=condition), self.assertRaises(ValueError):
                    family.compare_original_to_retrofit(weather_path=Path('absent'), after_case=case, condition=condition)
            producer.assert_not_called()

    def test_public_path_reuses_family_without_mutating_it(self):
        before = copy.deepcopy(self.result)
        with patch.object(family, 'calculate_family_reference', return_value=self.result) as producer:
            r = family.compare_original_to_retrofit(weather_path=Path('fixture'), after_case='standard', condition=family.SOURCE_PACKAGE_REPLACEMENT)
            producer.assert_called_once_with(weather_path=Path('fixture'))
            self.assertEqual(self.result, before)
            self.assertIs(r['after_device_reference'], self.result['cases']['standard']['device_reference'])

    def test_unavailable_weather_never_becomes_a_synthetic_year(self):
        with self.assertRaises(FileNotFoundError):
            family.calculate_family_reference(weather_path=Path('absent'))

    def test_unreviewed_manifest_bytes_reject(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'manifest.json'
            path.write_text(json.dumps(self.manifest))
            with patch.object(family, 'MANIFEST', path), self.assertRaisesRegex(ValueError, 'manifest mismatch'):
                family._manifest()

    def test_changed_producer_dependency_rejects(self):
        original = Path.read_bytes
        def read(path):
            raw = original(path)
            return raw + b'\n' if str(path).endswith('modules/B05/annual_device_reference.py') else raw
        with patch.object(Path, 'read_bytes', read), self.assertRaisesRegex(ValueError, 'dependency changed'):
            family._manifest()

    def test_unknown_debts_are_not_invalid_evidence_tiers(self):
        for debt in self.result['validation_debt']:
            if 'evidence_tier' in debt:
                self.assertIn(debt['evidence_tier'], ('E1', 'E2', 'E3'))
        self.assertTrue(any(d.get('evidence_status') == 'Q' for d in self.result['validation_debt']))

    def test_signed_rating_correction_preserves_unknown_installed_heat_and_controls(self):
        for result in (self.compare('standard'), self.compare('ambitious')):
            residual = result['residual']
            self.assertEqual(residual['sign'], 'SIGNED_UNKNOWN')
            self.assertFalse(residual['is_physical_auxiliary_consumption_sum'])
            self.assertTrue(residual['rated_unit_control_and_safety_input_already_included'])
            self.assertFalse(residual['installed_thermal_boundary_and_duty_reconciled'])
            self.assertIn('heat-delivery/duty', residual['definition'])
            self.assertEqual(result['service_completion_basis'], 'SOURCE_RATING_REFERENCE_ONLY')
            self.assertIsNone(result['installed_heat_delivery_kwh'])
            self.assertIsNone(result['installed_service_completion'])
        self.assertIsNone(self.result['installed_heat_delivery_kwh'])
        self.assertIsNone(self.result['installed_service_completion'])


if __name__ == '__main__':
    unittest.main()
