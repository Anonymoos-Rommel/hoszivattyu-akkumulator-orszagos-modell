import copy
import hashlib
import json
import tempfile
import unittest
from decimal import Decimal, localcontext
from pathlib import Path
from unittest.mock import patch

from modules.B11 import calorific_reference as c


class CalorificReferenceTests(unittest.TestCase):
    def test_registry_serialized_source_cases_preserve_units(self):
        expected = {'original': '69835.4020929897739008',
                    'standard': '29448.91917800972092800',
                    'ambitious': '21041.40809151963695232'}
        for package, ncv in expected.items():
            with self.subTest(package=package):
                r = c.calculate_reference(package=package)
                self.assertEqual(r['source_convention_gas_mj_ncv'], Decimal(ncv))
                self.assertEqual(r['source_gas_mj_gcv'], r['source_gas_kwh_gcv'] * Decimal('3.6'))
                self.assertEqual(r['source_convention_ncv_over_gcv'], Decimal('0.92'))
                self.assertEqual((r['evidence_status'], r['evidence_tier']), ('DER', 'E2'))

    def test_arithmetic_does_not_depend_on_ambient_precision(self):
        expected = c.calculate_reference(package='ambitious')
        with localcontext() as ctx:
            ctx.prec = 6
            self.assertEqual(c.calculate_reference(package='ambitious'), expected)

    def test_general_convention_is_not_averaged_or_promoted(self):
        r = c.calculate_reference(package='ambitious')
        self.assertEqual(r['general_convention_difference_mj'], Decimal('457.42191503303558592'))
        self.assertFalse(r['general_convention_difference_is_uncertainty_bound'])
        self.assertFalse(r['general_convention_is_second_canonical_case'])

    def test_unsupported_billing_volume_and_downstream_claims_stay_unknown(self):
        r = c.calculate_reference(package='original')
        for field in ('gas_hourly_profile', 'billing_year_allocation',
                      'physical_hungarian_gas_mj_ncv', 'actual_billing_energy_mj',
                      'gas_volume_m3', 'import_value', 'household_savings'):
            self.assertIsNone(r[field], field)
        for field in ('dhw_or_cooking_added', 'gas_auxiliary_electricity_converted',
                      'national_admission', 'whole_slice_complete'):
            self.assertFalse(r[field], field)
        self.assertTrue(r['annual_only'])
        self.assertTrue(r['validation_debt'])

    def test_unknown_package_rejects_without_default(self):
        for value in ('', 'average', 'Original', None, True, 0):
            with self.subTest(value=value), self.assertRaises(ValueError):
                c.calculate_reference(package=value)

    def test_manifest_mutation_rejects(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / 'manifest.json'
            p.write_bytes(c.MANIFEST.read_bytes() + b' ')
            with patch.object(c, 'MANIFEST', p), self.assertRaisesRegex(ValueError, 'mismatch'):
                c.calculate_reference(package='ambitious')

    def test_changed_source_family_rejects(self):
        manifest = c._manifest()
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            pin = manifest['repository_pins']['source_family']
            p = root / pin['path']; p.parent.mkdir(parents=True)
            p.write_bytes((c.ROOT / pin['path']).read_bytes() + b' ')
            with patch.object(c, 'ROOT', root), self.assertRaisesRegex(ValueError, 'changed'):
                c.calculate_reference(package='ambitious')

    def test_fuel_identity_guard_survives_reviewed_hash_update(self):
        manifest = c._manifest()
        pin = manifest['repository_pins']['source_family']
        original = json.loads((c.ROOT / pin['path']).read_text())
        for bad in ('Oil', '', None):
            family = copy.deepcopy(original)
            for cell in family['cases']['ambitious']['source_system_cells']:
                if cell['field'] == 'Code_SysH_EC_1': cell['value'] = bad
            with self.subTest(bad=bad), tempfile.TemporaryDirectory() as d:
                root = Path(d); p = root / pin['path']; p.parent.mkdir(parents=True)
                p.write_text(json.dumps(family))
                m = copy.deepcopy(manifest)
                m['repository_pins']['source_family']['sha256'] = hashlib.sha256(p.read_bytes()).hexdigest()
                with patch.object(c, 'ROOT', root), patch.object(c, '_manifest', return_value=m):
                    with self.assertRaisesRegex(ValueError, 'natural-gas'):
                        c.calculate_reference(package='ambitious')
