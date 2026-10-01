import csv
from decimal import Decimal
import hashlib
import io
import json
from pathlib import Path
import unittest
from modules.B02.household_energy_controls import control,end_use_balance_residual_tj,load_controls
from tools.extract_b02_eurostat_household import extract

ROOT=Path(__file__).resolve().parents[1]


class HouseholdEnergyControlTests(unittest.TestCase):
    def source(self):
        m=json.loads((ROOT/'registry/b02_eurostat_household_manifest.json').read_text())
        raw=(ROOT/m['repo_snapshot_path']).read_bytes()
        self.assertEqual(hashlib.sha256(raw).hexdigest(),m['sha256'])
        return raw

    def test_exact_reproduction_and_missing_cells(self):
        rows=extract(self.source());self.assertEqual(len(rows),315)
        self.assertEqual(sum(r['availability']=='PRESENT' for r in rows),222)
        with (ROOT/'data/processed/b02/eurostat_household_enduse_hu_2022_2024.csv').open(newline='') as f:self.assertEqual(list(csv.DictReader(f)),rows)
        self.assertEqual(sum(v is None for v in load_controls().values()),93)

    def test_actual_gas_and_unit_boundaries(self):
        v=control(2024,'FC_OTH_HH_E_SH','G3000')
        self.assertEqual(v.value_tj,Decimal('82546.835'))
        self.assertEqual(v.value_gwh,Decimal('82546.835')/Decimal('3.6'))
        self.assertEqual(v.energy_boundary,'REPORTED_HOUSEHOLD_FINAL_ENERGY_BY_PRODUCT_AND_END_USE')
        self.assertEqual(control(2024,'FC_OTH_HH_E_WH','G3000').value_tj,Decimal('12926.63'))

    def test_missing_is_not_published_zero(self):
        self.assertEqual(control(2024,'FC_OTH_HH_E_WH','RA600').value_tj,0)
        for args in [(2024,'FC_OTH_HH_E_SC','G3000'),(2025,'FC_OTH_HH_E','TOTAL'),(2024,'FC_OTH_HH_E','HYD')]:
            with self.assertRaises(ValueError):control(*args)
        with self.assertRaises(ValueError):end_use_balance_residual_tj(2024,'G3000')

    def test_end_use_rounding_residual_retained(self):
        self.assertEqual(end_use_balance_residual_tj(2023,'TOTAL'),Decimal('-.001'))
        self.assertEqual(end_use_balance_residual_tj(2024,'TOTAL'),Decimal('.001'))
        self.assertEqual(end_use_balance_residual_tj(2024,'E7000'),0)

    def test_bad_scope_index_and_value_rejected(self):
        original=json.loads(self.source())
        for kind in ['scope','index','negative','nonfinite','bool','alias','flag_alias']:
            j=json.loads(json.dumps(original))
            if kind=='scope':j['dimension']['geo']['category']['index']={'DE':0}
            if kind=='index':j['value']['99999']=1
            if kind=='negative':j['value']['0']=-1
            if kind=='nonfinite':j['value']['0']='NaN'
            if kind=='bool':j['value']['0']=True
            if kind=='alias':j['value']['00']=123
            if kind=='flag_alias':j['status']={'00':'e'}
            with self.assertRaises(ValueError):extract(json.dumps(j).encode())


if __name__=='__main__':unittest.main()
