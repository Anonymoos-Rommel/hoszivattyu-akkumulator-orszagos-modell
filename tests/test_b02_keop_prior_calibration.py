from pathlib import Path
import csv,json,tempfile,unittest
from unittest.mock import patch
from math import fsum
from modules.B02 import keop_prior_calibration as model


class KeopPriorCalibrationTests(unittest.TestCase):
    def test_historical_prior_is_dwelling_count_not_survey_or_building_count(self):
        prior=model.prior_counts()
        self.assertEqual(sum(prior.values()),4363754)
        self.assertEqual(sum(prior[i] for i in range(1,13)),2688555)
        self.assertEqual(sum(prior[i] for i in range(13,24)),1675199)

    def test_historical_area_and_author_bridge_are_separate_from_prototype(self):
        area=model.historical_area_surface();prior=model.prior_counts()
        self.assertAlmostEqual(fsum(area[i][0]*prior[i] for i in prior),336839750,places=6)
        self.assertEqual(area[1][1],1)
        self.assertEqual(area[13][1],1.05)
        self.assertEqual(area[20][1],1.1)
        self.assertEqual(area[23][1],1.05)
        self.assertNotEqual(area[20][0],model.load_types()[20].heated_floor_area_per_dwelling_m2)

    def test_finite_age_bridge_does_not_assign_full_twenty_year_prior_to_one_year(self):
        base=dict(model.conditional_type_weights('Y1946-1960','FAMILY_HOUSE',model.UNIFORM))
        early=dict(model.conditional_type_weights('Y1946-1960','FAMILY_HOUSE',model.EARLY))
        late=dict(model.conditional_type_weights('Y1946-1960','FAMILY_HOUSE',model.LATE))
        self.assertAlmostEqual(base[4],14/15)
        self.assertAlmostEqual(base[5]+base[6],1/15)
        self.assertAlmostEqual(early[4],119/120)
        self.assertAlmostEqual(late[4],7/8)
        self.assertAlmostEqual(base[5]/base[6],model.prior_counts()[5]/model.prior_counts()[6])

    def test_all42_vectors_conserve_and_open_tails_are_not_invented(self):
        count=0
        for period in model.WBL_PERIOD_INTERVALS:
            for group in model.GROUPS:
                for method in (model.UNIFORM,model.EARLY,model.LATE):
                    r=model.conditional_type_weights(period,group,method);count+=1
                    self.assertAlmostEqual(fsum(v for _,v in r),1)
                    self.assertTrue(all(v>=0 for _,v in r))
                if period in ('Y_LT1919','Y_GE2011'):
                    self.assertEqual(model.conditional_type_weights(period,group,model.EARLY),model.conditional_type_weights(period,group,model.LATE))
        self.assertEqual(count,42)
        with self.assertRaises(ValueError):model.conditional_type_weights('Y1946-1960','FAMILY_HOUSE','UNDECLARED_MIDPOINT')

    def test_sum_preserving_prior_tamper_is_rejected(self):
        original=model.ROOT
        with tempfile.TemporaryDirectory() as td:
            root=Path(td);(root/'registry').mkdir();(root/'data/processed/b02').mkdir(parents=True)
            (root/'registry/b02_keop23_prior_manifest.json').write_bytes((original/'registry/b02_keop23_prior_manifest.json').read_bytes())
            path=root/'data/processed/b02/keop23_dwelling_prior_2011.csv'
            with (original/'data/processed/b02/keop23_dwelling_prior_2011.csv').open() as source:
                rows=list(csv.DictReader(source))
            rows[0]['source_typology_dwellings'],rows[1]['source_typology_dwellings']=rows[1]['source_typology_dwellings'],rows[0]['source_typology_dwellings']
            with path.open('w',newline='') as f:w=csv.DictWriter(f,fieldnames=list(rows[0]),lineterminator='\n');w.writeheader();w.writerows(rows)
            model.prior_counts.cache_clear()
            try:
                with patch.object(model,'ROOT',root):
                    with self.assertRaisesRegex(ValueError,'hash'):model.prior_counts()
            finally:model.prior_counts.cache_clear()

    def test_real_joint_calibration_is_experiment_only_and_conserves_controls(self):
        result=model.run_calibration_experiment();self.assertEqual(len(result),8)
        for r in result:
            self.assertLess(abs(r['model_weight_sum']-r['observed_dwellings']),1e-5)
            self.assertLess(r['maximum_cell_residual'],1e-8)
            self.assertEqual(r['weight_admission'],'EXPERIMENT_ONLY_NOT_E2')
            self.assertEqual(r['area_comparison_status'],'DIAGNOSTIC_ONLY_AREA_SEMANTICS_NOT_IDENTICAL')
            self.assertIn('floor_area_band',r['omitted_type_conditioning_fields'])
        base=next(r for r in result if r['case']=='REFERENCE_EXPERIMENT' and r['population_scope']=='NON_DISTRICT')
        self.assertAlmostEqual(base['prototype_heated_area_exposure_m2'],327086765.91800624,places=3)
        self.assertGreater(base['numeric_proxy_area_above_wbl_band_upper_assignment_mass'],1000000)
        self.assertEqual(base['observed_dwellings'],3389817)
        self.assertLess(base['historical_dwelling_area_exposure_m2'],base['full_heating_reference_exposure_m2'])
        self.assertLess(base['full_heating_reference_exposure_m2'],base['prototype_heated_area_exposure_m2'])
        self.assertEqual(base['area_transfer_status'],'ASS_2011_TYPE_MEANS_ON_2022_COUNTS_NOT_CURRENT_OBSERVATION')


if __name__=='__main__':unittest.main()
