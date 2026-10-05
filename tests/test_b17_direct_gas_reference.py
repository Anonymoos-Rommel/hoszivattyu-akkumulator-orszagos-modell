import copy
from decimal import Decimal, localcontext, ROUND_DOWN
from fractions import Fraction
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from modules.B17 import direct_gas_reference as d


class DirectGasReferenceTests(unittest.TestCase):
    ACTIVITIES = {
        'original': '69835.4020929897739008',
        'standard': '29448.91917800972092800',
        'ambitious': '21041.40809151963695232',
    }

    def test_all_named_source_activities_and_mass_against_rational_oracle(self):
        for package, raw in self.ACTIVITIES.items():
            with self.subTest(package=package):
                result = d.calculate_reference(package=package)
                activity = Fraction(raw)
                self.assertEqual(Fraction(result['activity_mj_ncv']), activity)
                self.assertEqual(Fraction(result['activity_tj_ncv']), activity / 1000000)
                for field, factor in [('central_kg_co2', 56100),
                                      ('factor_interval_lower_kg_co2', 54300),
                                      ('factor_interval_upper_kg_co2', 58300)]:
                    self.assertEqual(Fraction(result[field]), activity * factor / 1000000)

    def test_source_method_scope_and_oxidation_are_explicit(self):
        r = d.calculate_reference(package='original')
        self.assertEqual(r['factor']['fuel'], 'Natural Gas')
        self.assertEqual(r['factor']['pollutant'], 'CO2')
        self.assertEqual(r['factor']['oxidation_factor_already_included'], '1')
        self.assertEqual(r['factor']['unit'], 'kg_CO2_per_TJ_NCV_fuel_input')
        self.assertEqual(r['factor']['evidence_status'], 'ASS')
        self.assertEqual((r['evidence_status'], r['evidence_tier']), ('DER', 'E2'))
        self.assertEqual(r['activity_ncv_over_gcv'], Decimal('0.92'))

    def test_native_factor_interval_not_full_model_confidence_or_hard_bound(self):
        r = d.calculate_reference(package='standard')
        self.assertEqual(r['factor']['interval_kind'], 'SOURCE_DEFAULT_95_PERCENT_CONFIDENCE_INTERVAL')
        self.assertEqual(r['uncertainty_scope'], 'FACTOR_ONLY_AT_FIXED_SOURCE_CONVENTION_ACTIVITY')
        self.assertFalse(r['interval_is_hard_bound'])
        self.assertFalse(r['interval_covers_total_model_uncertainty'])
        self.assertTrue(r['factor_validation_debt'])
        self.assertTrue(r['activity_validation_debt'])

    def test_no_unsupported_total_programme_emissions_or_economic_claim(self):
        r = d.calculate_reference(package='ambitious')
        for field in ('observed_hungarian_emissions_kg_co2', 'net_heat_pump_climate_effect',
                      'electricity_emissions', 'upstream_fuel_emissions',
                      'refrigerant_emissions', 'ch4_n2o_or_co2e', 'health_effect', 'monetary_value'):
            self.assertIsNone(r[field], field)
        self.assertFalse(r['national_admission'])
        self.assertFalse(r['whole_slice_complete'])

    def test_package_identity_and_existing_energy_are_preserved(self):
        for package in d.PACKAGES:
            old = d.activity_source.calculate_reference(package=package)
            r = d.calculate_reference(package=package)
            self.assertEqual(r['variant_id'], old['variant_id'])
            self.assertEqual(r['source_system_row'], old['source_system_row'])
            self.assertEqual(r['activity_source_id'], old['source_id'])
            self.assertEqual(r['activity_source_sha256'], old['source_sha256'])
            self.assertEqual(r['activity_mj_ncv'], old['source_convention_gas_mj_ncv'])

    def test_shared_factor_difference_is_not_independent_interval_subtraction(self):
        for after in ('standard', 'ambitious'):
            r = d.compare_reference(from_package='original', to_package=after)
            delta = Fraction(self.ACTIVITIES['original']) - Fraction(self.ACTIVITIES[after])
            self.assertTrue(r['shared_factor'])
            self.assertEqual(r['factor_dependence'], 'ONE_COMMON_FACTOR_PARAMETER')
            self.assertEqual(Fraction(r['central_kg_co2']), delta * 56100 / 1000000)
            self.assertEqual(Fraction(r['factor_interval_lower_kg_co2']), delta * 54300 / 1000000)
            self.assertEqual(Fraction(r['factor_interval_upper_kg_co2']), delta * 58300 / 1000000)
            before = d.calculate_reference(package='original')
            after_result = d.calculate_reference(package=after)
            self.assertNotEqual(r['factor_interval_lower_kg_co2'],
                                before['factor_interval_lower_kg_co2'] - after_result['factor_interval_upper_kg_co2'])

    def test_reverse_difference_reverses_interval_endpoints(self):
        positive = d.compare_reference(from_package='original', to_package='standard')
        negative = d.compare_reference(from_package='standard', to_package='original')
        self.assertEqual(negative['central_kg_co2'], -positive['central_kg_co2'])
        self.assertEqual(negative['factor_interval_lower_kg_co2'], -positive['factor_interval_upper_kg_co2'])
        self.assertEqual(negative['factor_interval_upper_kg_co2'], -positive['factor_interval_lower_kg_co2'])

    def test_identical_case_has_exact_zero_difference(self):
        r = d.compare_reference(from_package='original', to_package='original')
        for field in ('activity_difference_mj_ncv', 'activity_tj_ncv', 'central_kg_co2',
                      'factor_interval_lower_kg_co2', 'factor_interval_upper_kg_co2'):
            self.assertEqual(r[field], 0)

    def test_nondefault_explicit_package_is_required(self):
        with self.assertRaises(TypeError): d.calculate_reference()
        with self.assertRaises(TypeError): d.compare_reference(from_package='original')
        for value in ('', 'mean', 'Original', None, True, 0, [], {}):
            with self.subTest(value=value), self.assertRaises(ValueError):
                d.calculate_reference(package=value)

    def test_both_comparison_sides_are_qualified(self):
        for before, after in [('Oil', 'standard'), ('original', 'Oil')]:
            with self.subTest(before=before, after=after), self.assertRaises(ValueError):
                d.compare_reference(from_package=before, to_package=after)

    def test_ambient_context_cannot_change_factor_or_activity_arithmetic(self):
        expected = d.calculate_reference(package='original')
        comparison = d.compare_reference(from_package='original', to_package='ambitious')
        with localcontext() as ctx:
            ctx.prec = 3
            ctx.rounding = ROUND_DOWN
            ctx.Emax = 3
            ctx.Emin = -3
            for signal in ctx.traps: ctx.traps[signal] = True
            self.assertEqual(d.calculate_reference(package='original'), expected)
            self.assertEqual(d.compare_reference(from_package='original', to_package='ambitious'), comparison)

    def test_changed_manifest_rejects(self):
        with tempfile.TemporaryDirectory() as folder:
            p = Path(folder) / 'manifest.json'; p.write_bytes(d.MANIFEST.read_bytes() + b' ')
            with patch.object(d, 'MANIFEST', p), self.assertRaisesRegex(ValueError, 'applicability changed'):
                d.calculate_reference(package='original')

    def test_each_activity_authority_is_pinned(self):
        manifest = json.loads(d.MANIFEST.read_bytes())
        for name, damaged in manifest['repository_pins'].items():
            with self.subTest(name=name), tempfile.TemporaryDirectory() as folder:
                root = Path(folder)
                for pin in manifest['repository_pins'].values():
                    p = root / pin['path']; p.parent.mkdir(parents=True, exist_ok=True)
                    p.write_bytes((d.ROOT / pin['path']).read_bytes())
                p = root / damaged['path']; p.write_bytes(p.read_bytes() + b' ')
                with patch.object(d, 'ROOT', root), self.assertRaisesRegex(ValueError, 'activity authority changed'):
                    d.calculate_reference(package='original')

    def test_semantic_boundary_survives_a_reviewed_manifest_pin_update(self):
        manifest = json.loads(d.MANIFEST.read_bytes())
        mutations = [('fuel', 'Biogas'), ('pollutant', 'CO2e'),
                     ('unit', 'kg_CO2_per_TJ_GCV'), ('oxidation_factor_already_included', '0.98'),
                     ('interval_kind', 'HARD_BOUND'), ('value', 'NaN'),
                     ('lower', '0'), ('upper', '55000')]
        for key, value in mutations:
            with self.subTest(key=key), tempfile.TemporaryDirectory() as folder:
                changed = copy.deepcopy(manifest); changed['factor'][key] = value
                p = Path(folder) / 'manifest.json'; p.write_text(json.dumps(changed))
                with patch.object(d, 'MANIFEST', p), patch.object(d, 'MANIFEST_SHA256', hashlib.sha256(p.read_bytes()).hexdigest()):
                    with self.assertRaises(ValueError): d.calculate_reference(package='original')

    def test_upstream_scope_cannot_silently_expand(self):
        original = d.activity_source.calculate_reference(package='original')
        for key, value in [('quantity_scope', 'MEASURED_GAS'), ('evidence_tier', 'E3'),
                           ('dhw_or_cooking_added', True), ('gas_auxiliary_electricity_converted', True),
                           ('national_admission', True), ('annual_only', False),
                           ('source_convention_ncv_over_gcv', Decimal('0.90')),
                           ('source_convention_gas_mj_ncv', 69835.4),
                           ('source_convention_gas_mj_ncv', Decimal('NaN')),
                           ('source_convention_gas_mj_ncv', Decimal('-1'))]:
            changed = copy.deepcopy(original); changed[key] = value
            with self.subTest(key=key, value=value), patch.object(d.activity_source, 'calculate_reference', return_value=changed):
                with self.assertRaises(ValueError): d.calculate_reference(package='original')

    def test_cli_requires_and_returns_one_explicit_package(self):
        cmd = [sys.executable, '-m', 'modules.B17.direct_gas_reference']
        absent = subprocess.run(cmd, cwd=d.ROOT, capture_output=True, text=True)
        self.assertNotEqual(absent.returncode, 0)
        present = subprocess.run(cmd + ['--package', 'ambitious'], cwd=d.ROOT,
                                 capture_output=True, text=True, check=True)
        result = json.loads(present.stdout)
        self.assertEqual(result['package'], 'ambitious')
        self.assertEqual(Decimal(result['activity_mj_ncv']), Decimal(self.ACTIVITIES['ambitious']))


if __name__ == '__main__':
    unittest.main()
