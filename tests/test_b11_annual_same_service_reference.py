import copy
import json
import math
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from modules.B11 import annual_same_service_reference as gas


class AnnualSameServiceReferenceTests(unittest.TestCase):
    def setUp(self):
        self.manifest = gas._manifest()
        self.hp = dict(
            reference_id=self.manifest['device_reference_id'],
            evidence_status='DER', evidence_tier='E2',
            thermal_reference=gas.device._thermal(gas.device._manifest()),
            summary=dict(complete_generator_service=True, unknown_hours=0,
                         source_capacity_shortfall_kwh=0.0, hours=8760,
                         annual_device_reference_electricity_kwh=2472.633793065277),
            rows=[],
        )

    def compose(self, hp=None, manifest=None):
        return gas._compose(hp or self.hp, manifest or self.manifest,
                            gas.FULL_REFERENCE_REPLACEMENT)

    def test_original_annual_fuel_and_separate_auxiliary(self):
        result = self.compose()
        self.assertAlmostEqual(result['baseline']['space_heating_gas_kwh_gcv'], 6353.082153236605)
        self.assertAlmostEqual(result['baseline']['heating_auxiliary_electricity_kwh'], 156.8)
        self.assertAlmostEqual(result['source_annual_service']['generator_heat_kwh'], 6050.554431653909)
        self.assertAlmostEqual(result['source_allocated_gas_reduction_kwh_gcv'],
                               result['source_annual_service']['generator_heat_kwh'] * 1.05)

    def test_useful_heat_is_not_generator_heat(self):
        result = self.compose()
        self.assertAlmostEqual(result['source_annual_service']['generator_heat_kwh']
                               - result['source_annual_service']['useful_heat_kwh'], 302.4)
        self.assertNotAlmostEqual(result['source_allocated_gas_reduction_kwh_gcv'],
                                  result['source_annual_service']['useful_heat_kwh'] * 1.05)

    def test_condition_and_evidence_are_distinct(self):
        result = self.compose()
        self.assertEqual(result['condition']['evidence_status'], 'SCN')
        self.assertEqual((result['evidence_status'], result['evidence_tier']), ('DER', 'E2'))
        self.assertFalse(result['national_admission'])
        self.assertIsNone(result['measured_whole_boiler_fuel_savings_kwh_gcv'])

    def test_dhw_is_excluded_from_fuel_and_auxiliary_reduction(self):
        result = self.compose()
        self.assertAlmostEqual(result['excluded_dhw']['source_gas_kwh_gcv'], 542.976)
        self.assertAlmostEqual(result['excluded_dhw']['source_auxiliary_electricity_kwh'], 72.8)
        self.assertFalse(result['excluded_dhw']['displaced_by_this_reference'])
        self.assertNotAlmostEqual(result['source_allocated_gas_reduction_kwh_gcv'], 6896.058153236605)

    def test_mislabeled_combined_source_fuel_cannot_replace_heating_cell(self):
        self.manifest['gas_reference']['space_heating_fuel_kwh_gcv_m2'] = 123.1438955935108
        with self.assertRaisesRegex(ValueError, 'does not reconcile'):
            self.compose()

    def test_generator_efficiency_cannot_replace_expenditure_factor(self):
        self.manifest['gas_reference']['seasonal_generator_expenditure_gcv'] = 1 / 1.05
        with self.assertRaisesRegex(ValueError, 'does not reconcile'):
            self.compose()

    def test_affine_components_do_not_become_complete_totals(self):
        result = self.compose()
        delta = result['electricity_change']
        saved = result['purchased_energy_reduction']
        self.assertAlmostEqual(delta['known_intercept_kwh'], 2315.833793065277)
        self.assertAlmostEqual(saved['known_intercept_kwh'], 4037.2483601713284)
        self.assertEqual((delta['residual_coefficient'], saved['residual_coefficient']), (1, -1))
        self.assertEqual(delta['residual_name'], saved['residual_name'])
        self.assertIsNone(delta['total_kwh'])
        self.assertIsNone(saved['total_kwh'])

    def test_post_replacement_residual_preserves_retained_combi_uncertainty(self):
        result = self.compose()
        residual = result['replacement']['nondevice_and_retained_auxiliary']
        self.assertIn('combi-control', residual['definition'])
        self.assertFalse(residual['baseline_auxiliary_is_avoidable_measurement'])
        self.assertFalse(residual['unchanged_dhw_auxiliary_proves_residual_covered'])
        self.assertEqual(residual['evidence_status'], 'Q')
        for field in ('value_kwh_year', 'upper_bound_kwh_year', 'timing'):
            self.assertIsNone(residual[field])

    def test_unsupported_outputs_remain_unknown(self):
        result = self.compose()
        for key in ('gas_hourly_profile', 'auxiliary_hourly_profile', 'net_grid_increment_profile',
                    'gas_volume_m3', 'import_value', 'household_savings', 'physical_spf', 'national_increment'):
            with self.subTest(key=key):
                self.assertIsNone(result[key])
        self.assertIsNone(result['replacement']['complete_heating_system_electricity_kwh'])

    def test_b05_profile_is_preserved_without_fabricated_auxiliary_timing(self):
        marker = {'scope': 'test-only marker'}
        self.hp['rows'] = [marker]
        before = copy.deepcopy(self.hp)
        result = self.compose()
        self.assertEqual(self.hp, before)
        self.assertIs(result['device_reference'], self.hp)
        self.assertEqual(result['device_reference']['rows'], [marker])

    def test_conditional_replacement_requires_complete_service(self):
        for key, value in [('complete_generator_service', False), ('complete_generator_service', 1),
                           ('unknown_hours', 1), ('source_capacity_shortfall_kwh', 0.1), ('hours', 8784)]:
            with self.subTest(key=key, value=value):
                hp = copy.deepcopy(self.hp)
                hp['summary'][key] = value
                with self.assertRaisesRegex(ValueError, 'complete annual'):
                    self.compose(hp=hp)

    def test_unknown_or_nonphysical_device_input_is_not_zero(self):
        for value in (None, True, 0, -1, math.nan, math.inf):
            with self.subTest(value=value):
                hp = copy.deepcopy(self.hp)
                hp['summary']['annual_device_reference_electricity_kwh'] = value
                with self.assertRaisesRegex(ValueError, 'complete device electricity'):
                    self.compose(hp=hp)

    def test_validation_debt_keeps_unknown_status_separate_from_evidence_tier(self):
        debts = self.compose()['validation_debt']
        self.assertEqual([d['evidence_tier'] for d in debts if 'evidence_tier' in d], ['E2'])
        unknown = {d['scope'] for d in debts if d.get('evidence_status') == 'Q'}
        self.assertEqual(unknown, {'POST_REPLACEMENT_AUXILIARY_BOUNDARY', 'GAS_VOLUME_AND_VALUE'})
        for debt in debts:
            if 'evidence_tier' in debt:
                self.assertIn(debt['evidence_tier'], ('E1', 'E2', 'E3'))

    def test_different_service_or_evidence_is_not_retagged(self):
        for key, value in [('reference_id', 'OTHER'), ('evidence_status', 'OBS'), ('evidence_tier', 'E1')]:
            with self.subTest(key=key):
                hp = copy.deepcopy(self.hp)
                hp[key] = value
                with self.assertRaisesRegex(ValueError, 'matching source-service'):
                    self.compose(hp=hp)
        self.hp['thermal_reference']['variant_id'] = 'OTHER'
        with self.assertRaisesRegex(ValueError, 'matching source-service'):
            self.compose()

    def test_different_calorific_basis_cannot_be_relabelled(self):
        self.manifest['gas_reference']['energy_basis'] = 'LHV'
        with self.assertRaisesRegex(ValueError, 'GCV basis'):
            self.compose()

    def test_source_heat_boundary_drift_rejects(self):
        for key in ('useful_heat_kwh', 'generator_heat_kwh'):
            with self.subTest(key=key):
                hp = copy.deepcopy(self.hp)
                hp['thermal_reference'][key] += 10
                with self.assertRaisesRegex(ValueError, 'does not reconcile'):
                    self.compose(hp=hp)

    def test_public_condition_is_required_and_checked_before_source_read(self):
        with self.assertRaises(TypeError):
            gas.calculate_reference(weather_path=Path('absent'))
        with patch.object(gas.device, 'calculate_reference') as producer:
            for condition in (None, '', True, 'NATIONAL_FULL_REPLACEMENT', 'DHW_REPLACEMENT'):
                with self.subTest(condition=condition), self.assertRaisesRegex(ValueError, 'explicit full'):
                    gas.calculate_reference(weather_path=Path('absent'), condition=condition)
            producer.assert_not_called()

    def test_public_api_calls_bound_producer_and_preserves_missing_weather(self):
        with patch.object(gas.device, 'calculate_reference', return_value=self.hp) as producer:
            result = gas.calculate_reference(weather_path=Path('test-only'), condition=gas.FULL_REFERENCE_REPLACEMENT)
            producer.assert_called_once_with(weather_path=Path('test-only'))
            self.assertEqual(result['device_reference'], self.hp)
        with self.assertRaises(FileNotFoundError):
            gas.calculate_reference(weather_path=Path('absent'), condition=gas.FULL_REFERENCE_REPLACEMENT)

    def test_unreviewed_manifest_bytes_fail_before_quantity_use(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'manifest.json'
            path.write_text(json.dumps(self.manifest) + '\n')
            with patch.object(gas, 'MANIFEST', path), self.assertRaisesRegex(ValueError, 'manifest mismatch'):
                gas._manifest()

    def test_changed_producer_dependency_fails(self):
        original = Path.read_bytes
        def read(path):
            raw = original(path)
            return raw + b'\n' if str(path).endswith('modules/B05/annual_device_reference.py') else raw
        with patch.object(Path, 'read_bytes', read), self.assertRaisesRegex(ValueError, 'repository input changed'):
            gas._manifest()


if __name__ == '__main__':
    unittest.main()
