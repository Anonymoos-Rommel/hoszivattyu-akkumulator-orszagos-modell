from decimal import Decimal
import unittest
from modules.B02.jrc_household_controls import load_controls,value,efficiency_residual,eurostat_comparisons,TJ_PER_KTOE,gas_end_use_rebase_sensitivity
from tools.extract_b02_jrc_household import source_record


class JrcHouseholdControlTests(unittest.TestCase):
    def test_inventory_and_admission_boundary(self):
        rows=load_controls();self.assertEqual(len(rows),256);self.assertEqual(sum(v.value is None for v in rows.values()),12)
        self.assertTrue(all(v.admission_scope=='RESEARCH_CALIBRATION_CONTROLS_ONLY' for v in rows.values()))
        self.assertEqual(value('RES_summary',6,2022,'number'),4174806)
        self.assertEqual(value('RES_summary',7,2023,'ksqm'),Decimal('341154.7311656439'))

    def test_native_efficiency_identity_and_missing_zero_denominator(self):
        for year in (2022,2023):
            for row in range(3,33):
                if value('RES_hh_fec',row,year,'ktoe')>0:self.assertLess(abs(efficiency_residual(year,row)),Decimal('1e-12'))
        with self.assertRaises(ValueError):efficiency_residual(2023,7)
        with self.assertRaises(ValueError):value('RES_hh_eff',7,2023,'ratio')

    def test_native_sums_and_ambient_boundary(self):
        for year in (2022,2023):
            for sheet in ('RES_hh_fec','RES_hh_tes'):
                for parent,children in [(4,range(5,15)),(17,range(18,27)),(27,range(28,33)),(3,[4,15,17,27])]:
                    residual=value(sheet,parent,year,'ktoe')-sum(value(sheet,c,year,'ktoe') for c in children)
                    self.assertLess(abs(residual),Decimal('1e-9'))
            self.assertLess(abs(value('RES_summary',28,year,'ktoe')-value('RES_summary',44,year,'ktoe')-value('RES_summary',40,year,'ktoe')),Decimal('1e-9'))

    def test_matched_product_year_and_end_use_comparison(self):
        rows={r['quantity']:r for r in eurostat_comparisons(2023)}
        self.assertLess(abs(rows['GAS_AND_BIOGAS_TOTAL']['residual']),Decimal('.301'))
        self.assertAlmostEqual(float(rows['WATER_HEATING_TOTAL']['relative_to_eurostat']),-.1047648571937316,places=12)
        self.assertAlmostEqual(float(rows['SPACE_HEATING_EXCLUDING_AMBIENT']['relative_to_eurostat']),.02035383544468854,places=12)
        self.assertTrue(all(r['status']=='UNRESOLVED_REVISION_OR_DECOMPOSITION_DIFFERENCE' for r in rows.values()))
        with self.assertRaises(ValueError):eurostat_comparisons(2024)
        with self.assertRaises(ValueError):value('RES_hh_fec',8,2023,'GWh')

    def test_coherent_gas_rebase_is_explicit_diagnostic_only(self):
        rows=gas_end_use_rebase_sensitivity(2023)
        self.assertEqual([r['end_use'] for r in rows],['SH','WH'])
        self.assertTrue(all(not r['canonical_base_admitted'] and r['delta']<0 for r in rows))
        for r in rows:
            self.assertEqual(r['matched_eurostat_fec_with_same_jrc_efficiency']-r['native_jrc_tes'],r['delta'])
        with self.assertRaises(ValueError):gas_end_use_rebase_sensitivity(2024)

    def test_extractor_rejects_bad_numbers_and_retains_missing(self):
        args=['RES_hh_eff',7,2023,'Eff.ratio.HU.Res.HH.Thermal.SH.Oil.Oil_LiqBio','Diesel oil']
        for bad in [True,-1,float('nan'),float('inf'),'NaN']:
            with self.assertRaises(ValueError):source_record(*args,bad,None)
        self.assertEqual(source_record(*args,None,None)['availability'],'MISSING')
        self.assertEqual(source_record(*args,0,None)['availability'],'PRESENT')


if __name__=='__main__':unittest.main()
