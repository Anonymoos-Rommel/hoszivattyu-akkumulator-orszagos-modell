"""Actual admitted E2 reference reuse; SCN is not installed/national evidence."""
import copy
import dataclasses
import hashlib
import json
from decimal import Decimal, localcontext, ROUND_DOWN
from fractions import Fraction
from pathlib import Path
import unittest
from unittest.mock import patch

from modules.B12 import annual_reference_adapter as annual
from modules.B12 import a1_reference_response as a1

ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/'data/processed/b12'
BINDING=DATA/'annual_reference_input_binding.json'
SELECTION=DATA/'REFERENCE_CONSUMER_SCN.json'
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()


class E2ReferenceConsumerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.selection=read(SELECTION)
        cls.policy=read(DATA/'NORMALIZED_YEAR_POLICY.json')
        cls.reference=a1.load_reference(ROOT)
        cls.result=annual.prepare(BINDING,cls.policy,reference_consumer=cls.selection)

    def evaluate(self,selection=None,policy=None):
        return annual.prepare(BINDING,self.policy if policy is None else policy,
            reference_consumer=self.selection if selection is None else selection)

    def test_default_existing_result_is_unchanged(self):
        self.assertEqual(annual.prepare(BINDING,self.policy),
                         read(ROOT/'inputs/annual_reference/ACCEPTED_V3_CURRENT_RESULT.json'))

    def test_selected_reference_ready_without_E1_installed_proof(self):
        v=self.result['reference_consumer']
        self.assertEqual(v['status'],'E2_REFERENCE_SCENARIO_READY')
        self.assertEqual((v['truth_context'],v['device_reference']['truth'],
            v['device_reference']['evidence_tier'],v['device_reference']['base_status']),
            ('SCN','DER','E2','PROVISIONAL_BASE'))
        self.assertFalse(self.result['complete'])

    def test_actual_hourly_energy_and_single_base_conserve(self):
        e=self.result['reference_consumer']['annual_energy']
        base=sum(Fraction(p.base_kwh) for p in self.reference.periods)
        hp=sum(Fraction(p.hp_kwh) for p in self.reference.periods)
        self.assertEqual(Fraction(e['baseline_common_base']['exact_kWh']),base)
        self.assertEqual(Fraction(e['incremental_W55_device_reference']['exact_kWh']),hp)
        self.assertEqual(Fraction(e['programme_common_base_plus_device']['exact_kWh']),base+hp)
        self.assertEqual(e['declared_common_base_kWh'],'2419')
        self.assertEqual(e['declared_common_base_truth'],'ASS')
        self.assertEqual(e['programme_common_base_plus_device']['readable_kWh_6dp'],'4891.633793')

    def test_UTC_window_DST_partials_and_normalized_year_not_remapped(self):
        e=self.result['reference_consumer']['annual_energy'];windows=e['windows']
        self.assertEqual((e['hours'],[p['hours'] for p in windows]),(8760,[5086,3674]))
        self.assertEqual(windows[0]['start_utc'],'2025-01-01T00:00:00+00:00')
        self.assertEqual(windows[0]['end_utc_exclusive'],windows[1]['start_utc'])
        self.assertEqual(windows[1]['start_utc'],'2025-07-31T22:00:00+00:00')
        self.assertEqual(windows[-1]['end_utc_exclusive'],'2026-01-01T00:00:00+00:00')
        self.assertFalse(e['original_timestamps_remapped'])
        self.assertIsNone(self.result['operating_year'])

    def test_validation_debt_retained_losslessly(self):
        old=read(ROOT/annual.DEVICE_REFERENCE_PATH)
        self.assertEqual(self.result['reference_consumer']['validation_debt'],old['validation_debt'])
        self.assertEqual(self.result['reference_consumer']['limits'],old['limits'])

    def test_unknowns_not_zero_or_complete_cashflow(self):
        view=self.result['reference_consumer']
        self.assertTrue(all(x=={'value':None,'truth':'Q'} for x in view['unknown_components'].values()))
        for field in ['full_CAPEX','annual_economic_cashflow','ROI','payment_dates','settlement_dates',
                      'full_operating_balance','external_auxiliary_delta','subsidy_exit']:
            self.assertIsNone(self.result[field])
        self.assertIsNone(view['installed_system_total_kWh'])

    def test_no_national_or_population_adoption(self):
        v=self.result['reference_consumer'];s=v['selection']
        self.assertEqual((s['reference_households'],s['household_id']),(1,'SCN-MODEL-HH1'))
        self.assertIsNone(v['national_scaling'])
        self.assertIsNone(s['national_population']);self.assertIsNone(s['national_weights'])
        self.assertFalse(s['national_representative']);self.assertFalse(v['new_evidence_admission'])

    def test_C01_once_and_no_extra_pump_or_idle_energy(self):
        self.assertEqual(self.result['one_off_initial_component']['gross_HUF'],'1220781')
        self.assertFalse(self.result['one_off_initial_component']['repeat_annually'])
        self.assertEqual((self.result['new_Costs'],self.result['new_BillInputs']),(0,0))
        self.assertIsNone(self.result['reference_consumer']['unknown_components']['installed_pump_correction']['value'])
        hp=self.result['reference_consumer']['annual_energy']['incremental_W55_device_reference']
        self.assertEqual(hp['readable_kWh_6dp'],'2472.633793')

    def test_existing_parametric_component_is_reused_without_u_choice(self):
        old=annual.prepare(BINDING,self.policy)
        self.assertEqual(self.result['reference_consumer']['energy_economic_component'],old['annual_component_model'])
        t=Fraction(old['annual_component_model']['T_MJ']);q=Fraction(old['annual_component_model']['Q_MJ'])
        for u in [0,t-q,t,t+1]:self.assertEqual(annual.component_balance(self.result,u),annual.component_balance(old,u))
        self.assertIsNone(self.result['annual_component_model']['u_selected'])

    def test_no_selection_by_approval_label_or_id_only(self):
        for bad in [{},{'id':self.selection['id']},{**self.selection,'approved':True}]:
            with self.subTest(bad=bad),self.assertRaises(annual.ReferenceError):self.evaluate(bad)

    def test_changed_count_hardware_or_evidence_claim_rejected(self):
        for key,value in [('reference_households',2),('device','OTHER'),('supply_C','35'),
            ('service_scope','WHOLE_SYSTEM'),('installed_measurement_claim',True),
            ('national_representative',True),('national_weights',{'all':1}),('u_selected','0')]:
            bad=copy.deepcopy(self.selection);bad[key]=value
            with self.subTest(key=key),self.assertRaises(annual.ReferenceError):self.evaluate(bad)

    def test_bool_float_and_extra_parameter_types_rejected(self):
        for value in [True,1.0]:
            bad=copy.deepcopy(self.selection);bad['reference_households']=value
            with self.subTest(value=value),self.assertRaises(annual.ReferenceError):self.evaluate(bad)
        for bad in [[], 'APPROVED', {'id':float('nan')}]:
            with self.subTest(value=bad),self.assertRaises(annual.ReferenceError):self.evaluate(bad)

    def test_temporal_binding_still_explicit(self):
        r=annual.prepare(BINDING,reference_consumer=self.selection)
        self.assertEqual(r['reference_consumer']['status'],'INCOMPLETE_TEMPORAL_BINDING')
        self.assertIsNone(r['reference_consumer']['annual_energy'])

    def test_calendar_2028_not_allowed(self):
        p=copy.deepcopy(self.policy);p['mode']='CALENDAR_2028';p['days']=366
        with self.assertRaises(annual.ReferenceError):self.evaluate(policy=p)

    def test_policy_bytes_cannot_be_silently_replaced(self):
        original=Path.read_bytes
        def altered(p):return original(p)+b' ' if p==SELECTION else original(p)
        with patch.object(Path,'read_bytes',altered),self.assertRaisesRegex(annual.ReferenceError,'decision record'):
            self.evaluate()

    def test_device_manifest_and_producer_pins_enforced(self):
        original=Path.read_bytes
        for relative in [annual.DEVICE_REFERENCE_PATH,'modules/B05/engine.py']:
            target=ROOT/relative
            def altered(p):return original(p)+b' ' if p==target else original(p)
            with self.subTest(relative=relative),patch.object(Path,'read_bytes',altered),self.assertRaises(annual.ReferenceError):
                self.evaluate()

    def test_hourly_profile_drift_rejected(self):
        target=DATA/'a1_minimal5/REFERENCE_HOURLY_5.csv';original=Path.read_bytes
        def altered(p):return original(p)+b'\n' if p==target else original(p)
        with patch.object(Path,'read_bytes',altered),self.assertRaises(annual.ReferenceError):self.evaluate()

    def test_loaded_energy_must_equal_accepted_window(self):
        p=dataclasses.replace(self.reference.periods[0],hp_kwh=self.reference.periods[0].hp_kwh+1)
        ref=dataclasses.replace(self.reference,periods=(p,self.reference.periods[1]))
        with patch.object(a1,'load_reference',return_value=ref),self.assertRaisesRegex(annual.ReferenceError,'energy windows'):
            self.evaluate()

    def test_provenance_identifies_decision_code_and_profile(self):
        view=self.result['reference_consumer'];p=view['provenance']
        self.assertEqual(p['decision'],sha(SELECTION))
        self.assertEqual(p['annual_adapter'],sha(Path(annual.__file__)))
        self.assertEqual(p['annual_input_binding'],sha(BINDING))
        self.assertEqual(p['device_manifest'],sha(ROOT/annual.DEVICE_REFERENCE_PATH))
        self.assertEqual(view['selection'],self.selection)
        self.assertIn('projection_source_classification',p['hourly_reference'])

    def test_ambient_decimal_context_does_not_change_result(self):
        with localcontext() as ctx:
            ctx.prec=2;ctx.rounding=ROUND_DOWN
            r=self.evaluate()
            self.assertEqual(ctx.prec,2);self.assertEqual(ctx.rounding,ROUND_DOWN)
        self.assertEqual(r,self.result)


if __name__=='__main__':unittest.main()
