import csv
import copy
import tempfile
import unittest
from decimal import Decimal, localcontext
from pathlib import Path
from unittest.mock import patch

from modules.B03 import regulated_reference as r
from tools.validate_registry import validate_b03_fixed_fee


class RegulatedReferenceTests(unittest.TestCase):
    def args(self, **updates):
        values = dict(package='ambitious', energy_condition=r.ENERGY_CONDITION,
                      period_condition=r.PERIOD_CONDITION, discounted_allocation_mj='63645',
                      connection_fee_fraction='1', connection_reference_id='explicit-test-connection')
        values.update(updates)
        return values

    def test_discounted_source_reference_and_one_gross_connection_fee(self):
        value = r.price_reference(**self.args())
        self.assertEqual(value['reference_consumption_charge_huf'], Decimal('60286.1591511747422248310784'))
        self.assertEqual(value['declared_connection_charge_net_huf'], Decimal('9192'))
        self.assertEqual(value['declared_connection_charge_gross_huf'], Decimal('11673.84'))
        self.assertEqual(value['reference_energy_plus_declared_connection_huf'],
                         value['reference_consumption_charge_huf'] + Decimal('11673.84'))

    def test_original_case_crosses_band_once(self):
        value = r.price_reference(**self.args(package='original'))
        self.assertEqual(value['reference_discounted_mj'], Decimal('63645'))
        self.assertEqual(value['reference_excess_mj'], Decimal('6190.4020929897739008'))
        self.assertEqual(value['reference_consumption_charge_huf'], Decimal('318551.7892499610053654016'))

    def test_allocation_is_explicit_not_inferred_from_heating(self):
        for allocation in ('0', '1000', '21041.40809151963695232', '63645'):
            with self.subTest(allocation=allocation):
                value = r.price_reference(**self.args(discounted_allocation_mj=allocation))
                q = value['energy_reference']['source_convention_gas_mj_ncv']
                low = min(q, Decimal(allocation))
                self.assertEqual(value['reference_discounted_mj'], low)
                self.assertEqual(value['reference_discounted_mj'] + value['reference_excess_mj'], q)
                self.assertEqual(value['reference_consumption_charge_huf'], low*Decimal('2.86512')+(q-low)*Decimal('22.002'))

    def test_connection_fraction_is_separate_from_consumption(self):
        full = r.price_reference(**self.args())
        for fraction in ('0', '0.5', '1'):
            value = r.price_reference(**self.args(connection_fee_fraction=fraction))
            self.assertEqual(value['reference_consumption_charge_huf'], full['reference_consumption_charge_huf'])
            self.assertEqual(value['declared_connection_charge_gross_huf'], Decimal(fraction)*Decimal('11673.84'))
            self.assertIsNone(value['connection_charge_attributed_to_heating_huf'])
            self.assertIsNone(value['avoided_connection_charge_huf'])

    def test_scenario_does_not_admit_household_or_import_outputs(self):
        value = r.price_reference(**self.args())
        self.assertEqual(value['evidence_status'], 'SCN')
        self.assertEqual(value['price_status'], 'SCN_CONSTANT_2026_TARIFF_SNAPSHOT')
        self.assertEqual(value['permitted_context'], 'B13_BASELINE_REFERENCE_ONLY')
        for field in ('actual_billing_energy_mj', 'actual_household_bill_huf', 'actual_tariff_eligibility',
                      'household_savings_huf', 'import_value_huf', 'fiscal_compensation_huf', 'retained_other_gas_mj'):
            self.assertIsNone(value[field], field)
        for field in ('b12_cashflow_admitted', 'national_admission', 'invoice_rounding_applied',
                      'alternatives_are_additive', 'calendar_year_split_invented', 'whole_slice_complete'):
            self.assertFalse(value[field], field)

    def test_invalid_numbers_reject_in_both_accounting_arguments(self):
        for field in ('discounted_allocation_mj', 'connection_fee_fraction'):
            for bad in (None, True, False, '', 'NaN', 'Infinity', '-Infinity', '-0.01', [], {}):
                with self.subTest(field=field, bad=bad), self.assertRaises(ValueError):
                    r.price_reference(**self.args(**{field: bad}))

    def test_excessive_allocation_or_connection_charge_rejects(self):
        for updates in ({'discounted_allocation_mj':'63645.00001'}, {'connection_fee_fraction':'1.00001'}):
            with self.subTest(updates=updates), self.assertRaises(ValueError):
                r.price_reference(**self.args(**updates))

    def test_conditions_and_connection_identity_are_mandatory(self):
        for field in ('energy_condition', 'period_condition', 'connection_reference_id'):
            for bad in ('', None, True, ' '):
                with self.subTest(field=field, bad=bad), self.assertRaises(ValueError):
                    r.price_reference(**self.args(**{field:bad}))
        for field in self.args():
            args = self.args(); del args[field]
            with self.subTest(missing=field), self.assertRaises(TypeError):
                r.price_reference(**args)

    def test_ambient_decimal_context_does_not_change_money(self):
        expected = r.price_reference(**self.args())
        with localcontext() as ctx:
            ctx.prec = 6
            self.assertEqual(r.price_reference(**self.args()), expected)

    def test_manifest_pin_and_schedule_mutation_reject(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d)/'manifest.json'; p.write_bytes(r.MANIFEST.read_bytes()+b' ')
            with patch.object(r, 'MANIFEST', p), self.assertRaisesRegex(ValueError, 'mismatch'):
                r.price_reference(**self.args())
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            for key,pin in r._manifest()['repository_pins'].items():
                p=root/pin['path']; p.parent.mkdir(parents=True, exist_ok=True)
                p.write_bytes((r.ROOT/pin['path']).read_bytes()+(b' ' if key=='schedule' else b''))
            with patch.object(r, 'ROOT', root), self.assertRaisesRegex(ValueError, 'dependency changed'):
                r.price_reference(**self.args())

    def rows(self):
        with (r.ROOT/'data/processed/residential_gas_tariff_schedule.csv').open(newline='') as f:
            return list(csv.DictReader(f))

    def test_registry_validates_observed_net_and_derived_gross(self):
        for row in self.rows():
            errors=[]; validate_b03_fixed_fee(row, errors); self.assertEqual(errors, [])

    def test_registry_rejects_lost_tax_basis_and_double_vat(self):
        for key, bad in [('annual_fixed_charge_vat_basis','GROSS'),
                         ('gross_fixed_charge_status','OBS'),
                         ('gross_annual_fixed_charge_huf','9192'),
                         ('gross_annual_fixed_charge_huf','14825.7768'),
                         ('annual_fixed_charge_huf','NaN'), ('vat_rate','-1')]:
            row=self.rows()[0]; row[key]=bad; errors=[]
            validate_b03_fixed_fee(row, errors)
            with self.subTest(key=key,bad=bad): self.assertTrue(errors)

    def test_registry_absent_band_fee_cannot_hide_gross_charge(self):
        for key,bad in [('gross_annual_fixed_charge_huf','11673.84'),
                        ('annual_fixed_charge_vat_basis','NET'), ('gross_fixed_charge_status','DER')]:
            row=self.rows()[1]; row[key]=bad; errors=[]
            validate_b03_fixed_fee(row, errors)
            with self.subTest(key=key): self.assertTrue(errors)

    def test_registry_rejects_fully_populated_second_fee(self):
        row=self.rows()[1]
        row.update(annual_fixed_charge_huf='9192', gross_annual_fixed_charge_huf='11673.84',
                   annual_fixed_charge_vat_basis='NET', gross_fixed_charge_status='DER')
        errors=[]; validate_b03_fixed_fee(row, errors)
        self.assertTrue(errors)
