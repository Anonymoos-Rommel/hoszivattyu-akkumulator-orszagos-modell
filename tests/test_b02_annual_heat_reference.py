from decimal import Decimal
import unittest
import json
import hashlib
from pathlib import Path
from modules.B02.annual_heat_reference import annual_heat_reference,cohort_accounting,district_split_sensitivity,load_native_cells,district_other_dhw_allocation_sensitivity
from tools.extract_b02_jrc_cohorts import relevant_code


class AnnualHeatReferenceTests(unittest.TestCase):
    def test_scoped_admission_has_exact_input_and_named_debt(self):
        root=Path(__file__).resolve().parents[1]
        a=json.loads((root/'registry/b02_v1_annual_heat_admission.json').read_text())
        self.assertEqual(a['admission_status'],'E2_PROVISIONAL_BASE')
        self.assertEqual(a['reference_year'],2022)
        self.assertEqual(len(a['admission_criteria']),8)
        self.assertEqual(hashlib.sha256((root/a['input_artifact']).read_bytes()).hexdigest(),a['input_artifact_sha256'])
        self.assertTrue((root/a['consumer']).is_file())
        self.assertTrue(all((root/t).is_file() for t in a['tests']))
        for debt in a['validation_debt']:
            self.assertTrue(all(debt[k] for k in ('id','missing_exact_evidence','possible_supplier','claim_upgraded','material_to_finalization')))

    def test_native_inventory_and_paired_counts_conserve(self):
        self.assertEqual(len(load_native_cells()),558)
        for year,total in [(2022,4174806),(2023,4161137)]:
            rows=cohort_accounting(year)
            self.assertEqual(sum(r['households'] for r in rows),total)
            self.assertEqual(len(rows),9)

    def test_reference_is_not_rescaled_by_household_dwelling_ratio(self):
        r=annual_heat_reference()
        self.assertEqual(r.native_non_district_households,3738170)
        self.assertEqual(r.ksh_normalization_dwellings,3389817)
        self.assertAlmostEqual(float(r.space_heating_excluding_circulation_gwh),29266.755434224965,places=7)
        self.assertAlmostEqual(float(r.water_heating_including_solar_gwh),4966.646779497815,places=7)
        self.assertEqual(r.normalized_sh_kwh_per_dwelling_equivalent*r.ksh_normalization_dwellings/Decimal(1000000),r.space_heating_excluding_circulation_gwh)
        self.assertFalse(r.programme_scaling_allowed)
        self.assertEqual(r.normalization_scope,'KSH_DWELLING_EQUIVALENT_NOT_OBSERVED_MEAN')

    def test_circulation_solar_and_existing_heat_pumps_are_visible(self):
        r=annual_heat_reference()
        self.assertAlmostEqual(float(r.circulation_gwh),440.3781017004817,places=7)
        self.assertAlmostEqual(float(r.solar_dhw_included_gwh),176.9622584513864,places=7)
        self.assertAlmostEqual(float(r.existing_advanced_electric_sh_included_gwh),485.7850830547123,places=7)
        self.assertGreater(r.existing_advanced_electric_sh_included_gwh,0)

    def test_district_split_stress_conserves_fec_and_not_an_interval(self):
        r=district_split_sensitivity()
        self.assertLess(abs(sum(r['original_final_energy_tj'])-sum(r['alternative_final_energy_tj'])),Decimal('1e-20'))
        self.assertLess(r['delta_useful_gwh'][0],0);self.assertGreater(r['delta_useful_gwh'][1],0)
        self.assertAlmostEqual(float(sum(r['delta_useful_gwh'])),48.70197436628213,places=7)
        self.assertFalse(r['canonical_reference_replaced'])
        self.assertEqual(r['affected_scope'],'EXCLUDED_H8000_DISTRICT_BRANCH')
        self.assertTrue(all(abs(x)<Decimal('1e-19') for x in r['non_district_delta_useful_gwh']))

    def test_other_district_dhw_transfer_conserves_national_energy(self):
        r=district_other_dhw_allocation_sensitivity()
        self.assertAlmostEqual(float(r['non_district_delta_gwh']),-25.678,places=3)
        self.assertLess(abs(r['original_district_other_dhw_gwh']+r['original_non_district_dhw_gwh']-r['alternative_district_other_dhw_gwh']-r['alternative_non_district_dhw_gwh']),Decimal('1e-20'))
        self.assertEqual(r['national_energy_delta_gwh'],0)
        self.assertFalse(r['canonical_reference_replaced'])

    def test_selection_preserves_paired_wh_but_excludes_unrelated_enduses(self):
        self.assertTrue(relevant_code('NUM.number.HU.Res.HH.Thermal.SH.DistrHeat'))
        self.assertTrue(relevant_code('TES.ktoe.HU.Res.HH.Thermal.SH.DistrHeat.WH.Elc.Solar.Solar'))
        self.assertFalse(relevant_code('TES.ktoe.HU.Res.HH.Thermal.SH.DistrHeat.CO'))
        self.assertFalse(relevant_code('TES.ktoe.DE.Res.HH.Thermal.SH.DistrHeat.WH'))
        with self.assertRaises(ValueError):cohort_accounting(2024)


if __name__=='__main__':unittest.main()
