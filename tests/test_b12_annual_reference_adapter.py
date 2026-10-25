import copy
import json
import tempfile
import unittest
from pathlib import Path
from modules.B12.annual_reference_adapter import prepare, component_balance, ReferenceError
from fractions import Fraction

HERE=Path(__file__).resolve().parents[1]/'data/processed/b12'
BINDING=HERE/'annual_reference_input_binding.json'


class AnnualPreparationTests(unittest.TestCase):
    def test_missing_binding_incomplete(self):
        self.assertEqual(prepare(BINDING)['status'],'INCOMPLETE_TEMPORAL_BINDING')

    def test_no_false_complete_outputs(self):
        r=prepare(BINDING)
        self.assertFalse(r['complete'])
        for k in ['annual_economic_cashflow','full_CAPEX','ROI','household_first_day_non_worsening','subsidy_exit']:
            self.assertIsNone(r[k])

    def test_c01_once(self):
        r=prepare(BINDING)['one_off_initial_component']
        self.assertEqual(r['gross_HUF'],'1220781')
        self.assertFalse(r['repeat_annually'])

    def test_unknown_components_not_zero(self):
        r=prepare(BINDING)
        for k in ['additional_CAPEX','monetary_OM','external_auxiliary_delta']:
            self.assertIsNone(r[k])

    def test_no_dates_or_recurrence_defaults(self):
        r=prepare(BINDING)
        for k in ['operating_year','settlement_dates','payment_dates','recurrence_years']:
            self.assertIsNone(r[k])

    def test_parameter_u_preserved(self):
        self.assertIsNone(prepare(BINDING)['preserved_reference_components']['gas_u']['selected_value'])

    def test_no_native_adoption(self):
        r=prepare(BINDING)
        self.assertEqual((r['new_Costs'],r['new_BillInputs']),(0,0))
        self.assertFalse(r['source_use_adoption'])
        self.assertFalse(r['original_timestamp_remap'])

    def test_calendar_mapping_rejected(self):
        with self.assertRaises(ReferenceError):prepare(BINDING,{'mode':'CALENDAR_2028','days':366})

    def test_leap_year_not_silently_normalized(self):
        with self.assertRaises(ReferenceError):prepare(BINDING,{'mode':'NORMALIZED_365_DAY_REFERENCE','days':366,'remap_original_timestamps':False})

    def test_proposal_not_adoption_even_with_approval_label(self):
        r=prepare(BINDING,{'mode':'NORMALIZED_365_DAY_REFERENCE','days':365,'remap_original_timestamps':False,'status':'APPROVED','anchor':'2028-01-01'})
        self.assertEqual(r['status'],'INCOMPLETE_TEMPORAL_ADOPTION')
        self.assertFalse(r['proposed_binding_applied'])
        self.assertIsNone(r['annual_economic_cashflow'])

    def test_timestamp_change_rejected(self):
        with self.assertRaises(ReferenceError):prepare(BINDING,{'mode':'NORMALIZED_365_DAY_REFERENCE','days':365,'remap_original_timestamps':True})

    def test_source_drift_rejected(self):
        d=json.loads(BINDING.read_text(encoding='utf-8'))
        d['sources']['a1']['sha256']='0'*64
        with tempfile.TemporaryDirectory() as t:
            p=Path(t)/'binding.json';p.write_text(json.dumps(d),encoding='utf-8')
            with self.assertRaises(ReferenceError):prepare(p)

    def test_hash_pinned_policy_binds_only_component_reference(self):
        policy=json.loads((HERE/'NORMALIZED_YEAR_POLICY.json').read_text(encoding='utf-8'))
        r=prepare(BINDING,policy)
        self.assertEqual(r['status'],'BOUND_NORMALIZED_REFERENCE_COMPONENTS')
        self.assertTrue(r['temporal_policy_applied'])
        self.assertFalse(r['complete'])
        self.assertIsNone(r['ROI'])
        self.assertIsNone(r['annual_economic_cashflow'])
        self.assertIsNone(r['annual_component_model']['u_selected'])

    def test_component_replays_preserved_piecewise_formula(self):
        policy=json.loads((HERE/'NORMALIZED_YEAR_POLICY.json').read_text(encoding='utf-8'))
        r=prepare(BINDING,policy);m=r['annual_component_model']
        q,t,l,h,d=[Fraction(m[k]) for k in ['Q_MJ','T_MJ','L_HUF_per_MJ','H_HUF_per_MJ','Delta_A1_HUF']]
        for u in [Fraction(0),t-q,(2*t-q)/2,t,t+1]:
            with self.subTest(u=u):
                expected=(l*q if u<=t-q else h*q if u>=t else l*q+(h-l)*(u-(t-q)))-d
                self.assertEqual(component_balance(r,u),expected)
        self.assertIsNone(r['annual_component_model']['u_selected'])

    def test_component_without_policy_rejected(self):
        with self.assertRaises(ReferenceError):component_balance(prepare(BINDING),0)

    def test_invalid_parameter_rejected(self):
        policy=json.loads((HERE/'NORMALIZED_YEAR_POLICY.json').read_text(encoding='utf-8'))
        r=prepare(BINDING,policy)
        for u in [-1,True,1.0,'0']:
            with self.subTest(u=u):
                with self.assertRaises(ReferenceError):component_balance(r,u)


class AnnualOMTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import importlib
        prepare(BINDING)
        cls.native=importlib.import_module('modules.B12.input_accounting_contract')

    def inputs(self,baseline='100',programme='150'):
        from datetime import date
        from decimal import Decimal
        from modules.B12.annual_reference_adapter import AnnualOMInputs, ACCEPTED_POLICY
        n=self.native
        ref=n.Reference('EXTERNAL_ADMISSION','TEST_ONLY_NOT_SOURCE_OR_ADOPTION',None,None)
        period=n.Period(date(2026,10,21),date(2026,10,21))
        def amount(v):
            if v is None:return n.Scalar(None,'HUF','Q',period,'TEST_FROZEN2026',(),None,None,None,'Unknown test amount','B12-D03')
            return n.Scalar(Decimal(v),'HUF','SCN',period,'TEST_FROZEN2026',(),
                            'TEST_ONLY_ANNUAL_OM_FIXTURE','E3',None,None,None)
        basis=n.MoneyBasis('TEST_FROZEN2026','HUF','NOMINAL',date(2026,10,21),ref)
        return AnnualOMInputs(amount(baseline),amount(programme),basis,ref,ref,ref,
                              ('maintenance',),('maintenance',),'SCN-MODEL-HH1','TEST_ONLY_OM_SCOPE',ACCEPTED_POLICY['id'])

    def run_inputs(self,inputs):
        policy=json.loads((HERE/'NORMALIZED_YEAR_POLICY.json').read_text(encoding='utf-8'))
        return prepare(BINDING,policy,inputs)

    def test_default_om_missing_not_zero(self):
        r=self.run_inputs(None)
        self.assertEqual(r['annual_om']['status'],'INCOMPLETE_ANNUAL_OM')
        self.assertIsNone(r['annual_om']['baseline_gross_HUF'])
        self.assertIsNone(r['annual_om']['programme_gross_HUF'])

    def test_one_leg_unknown_retains_known_leg(self):
        r=self.run_inputs(self.inputs(None,'150'))
        self.assertEqual(r['annual_om']['programme_gross_HUF'],'150')
        self.assertIsNone(r['annual_om']['delta_programme_minus_baseline_HUF_exact'])

    def test_annual_known_amounts_do_not_need_cash_dates(self):
        r=self.run_inputs(self.inputs())
        self.assertEqual(r['annual_om']['status'],'ANNUAL_OM_PARAMETER_INPUTS_AVAILABLE')
        self.assertEqual(r['annual_om']['delta_programme_minus_baseline_HUF_exact'],'50')
        self.assertIsNone(r['payment_dates'])
        self.assertIsNone(r['annual_economic_cashflow'])

    def test_subtotal_sign_and_no_extra_vat(self):
        from modules.B12.annual_reference_adapter import energy_minus_om_component
        r=self.run_inputs(self.inputs())
        partial=energy_minus_om_component(r,0)
        self.assertEqual(Fraction(partial['HUF_exact']),component_balance(r,0)-50)
        self.assertIsNone(partial['full_operating_balance'])
        self.assertIsNone(partial['external_auxiliary_delta'])
        self.assertIsNone(partial['ROI'])

    def test_signed_om_difference_preserved(self):
        self.assertEqual(self.run_inputs(self.inputs('150','100'))['annual_om']['delta_programme_minus_baseline_HUF_exact'],'-50')

    def test_explicit_zero_retains_fixture_provenance(self):
        r=self.run_inputs(self.inputs('0','0'))
        self.assertEqual(r['annual_om']['delta_programme_minus_baseline_HUF_exact'],'0')
        self.assertFalse(r['annual_om']['evidence_adoption'])

    def test_negative_gross_rejected(self):
        with self.assertRaises(ReferenceError):self.run_inputs(self.inputs('-1','100'))

    def test_basis_mismatch_rejected(self):
        from dataclasses import replace
        i=self.inputs();i=replace(i,programme=replace(i.programme,basis_id='OTHER'))
        with self.assertRaises(ReferenceError):self.run_inputs(i)

    def test_currency_and_future_price_rejected(self):
        from dataclasses import replace
        from datetime import date
        i=self.inputs()
        for basis in [replace(i.money_basis,currency='EUR'),replace(i.money_basis,price_date=date(2028,1,1))]:
            with self.subTest(basis=basis):
                with self.assertRaises(ReferenceError):self.run_inputs(replace(i,money_basis=basis))

    def test_money_bridge_q_stays_incomplete(self):
        from dataclasses import replace
        i=self.inputs();q=self.native.Reference('Q',None,'Unresolved source-basis reconciliation','B12-D03')
        r=self.run_inputs(replace(i,money_bridge=q))
        self.assertIn('money bridge',r['annual_om']['missing'])
        self.assertIsNone(r['annual_om']['delta_programme_minus_baseline_HUF_exact'])

    def test_coverage_q_stays_incomplete(self):
        from dataclasses import replace
        i=self.inputs();q=self.native.Reference('Q',None,'Coverage not established','B12-D03')
        self.assertEqual(self.run_inputs(replace(i,programme_coverage=q))['annual_om']['status'],'INCOMPLETE_ANNUAL_OM')

    def test_duplicate_inclusions_rejected(self):
        from dataclasses import replace
        with self.assertRaises(ReferenceError):self.run_inputs(replace(self.inputs(),programme_inclusions=('maintenance','maintenance')))

    def test_energy_and_capital_inclusions_rejected(self):
        from dataclasses import replace
        for name in ['C01','INITIAL_CAPEX','ENERGY','W55_ELECTRICITY']:
            with self.subTest(name=name):
                with self.assertRaises(ReferenceError):self.run_inputs(replace(self.inputs(),programme_inclusions=(name,)))

    def test_scope_and_normalized_period_rejected(self):
        from dataclasses import replace
        for i in [replace(self.inputs(),household_id='OTHER_HOUSEHOLD'),replace(self.inputs(),year_policy_id='CALENDAR2028')]:
            with self.assertRaises(ReferenceError):self.run_inputs(i)

    def test_missing_temporal_binding_prevents_subtotal(self):
        from modules.B12.annual_reference_adapter import energy_minus_om_component
        r=prepare(BINDING,None,self.inputs())
        self.assertEqual(r['annual_om']['status'],'INCOMPLETE_TEMPORAL_BINDING')
        with self.assertRaises(ReferenceError):energy_minus_om_component(r,0)

    def test_rulefact_or_plain_amount_not_native_money(self):
        from dataclasses import replace
        with self.assertRaises(ReferenceError):self.run_inputs(replace(self.inputs(),programme=57150))

    def test_missing_om_prevents_false_complete_subtotal(self):
        from modules.B12.annual_reference_adapter import energy_minus_om_component
        r=self.run_inputs(None)
        with self.assertRaises(ReferenceError):energy_minus_om_component(r,0)
        self.assertIsNone(r['full_operating_balance'])

    def test_initial_c01_not_part_of_annual_om(self):
        r=self.run_inputs(self.inputs())
        self.assertEqual(r['one_off_initial_component']['gross_HUF'],'1220781')
        self.assertFalse(r['one_off_initial_component']['repeat_annually'])
        self.assertEqual(r['annual_om']['new_native_Cost_events'],0)


# Only the helper methods are reused below; existing34 tests remain one run each.
class OMReviewFixTests(unittest.TestCase):
    setUpClass=classmethod(AnnualOMTests.setUpClass.__func__)
    inputs=AnnualOMTests.inputs
    run_inputs=AnnualOMTests.run_inputs

    def test_exact_reported_component_bypasses_rejected(self):
        from dataclasses import replace
        for identity in ['ENERGY ','C01 ','EXTERNAL_AUXILIARY_ELECTRICITY']:
            for field in ['baseline_inclusions','programme_inclusions']:
                with self.subTest(identity=identity,field=field):
                    with self.assertRaises(ReferenceError):self.run_inputs(replace(self.inputs(),**{field:(identity,)}))

    def test_unknown_class_not_assumed_nonenergy(self):
        from dataclasses import replace
        for name in ['mystery_service','PUMP_ELECTRICITY','W55_ELECTRICITY\t','INITIAL_CAPEX\n','energy',' ENERGY','MAINTENANCE/ENERGY']:
            with self.subTest(name=name):
                with self.assertRaises(ReferenceError):self.run_inputs(replace(self.inputs(),programme_inclusions=(name,)))

    def test_classified_normalization_and_raw_identity_both_preserved(self):
        from dataclasses import replace
        r=self.run_inputs(replace(self.inputs(),programme_inclusions=(' maintenance ',)))['annual_om']
        self.assertEqual(r['classified_components']['programme'],[{'id':'MAINTENANCE','native_category':'O_AND_M','energy_class':'NON_ENERGY'}])
        self.assertEqual(r['input_records']['programme_inclusions']['__tuple__'],[' maintenance '])

    def test_normalized_duplicates_rejected(self):
        from dataclasses import replace
        with self.assertRaises(ReferenceError):self.run_inputs(replace(self.inputs(),programme_inclusions=('maintenance',' MAINTENANCE ')))

    def test_nonstring_component_rejected(self):
        from dataclasses import replace
        for values in [(1,),(['maintenance'],)]:
            with self.assertRaises(ReferenceError):self.run_inputs(replace(self.inputs(),programme_inclusions=values))

    def test_different_scenario_ref_stays_distinct(self):
        from dataclasses import replace
        i=self.inputs();changed=replace(i,programme=replace(i.programme,scenario_ref='DIFFERENT_TEST_ONLY_SCN'))
        a=self.run_inputs(i)['annual_om'];b=self.run_inputs(changed)['annual_om']
        self.assertEqual(a['delta_programme_minus_baseline_HUF_exact'],b['delta_programme_minus_baseline_HUF_exact'])
        self.assertNotEqual(a['input_records_sha256'],b['input_records_sha256'])
        self.assertEqual(b['input_records']['programme']['scenario_ref'],'DIFFERENT_TEST_ONLY_SCN')

    def test_explicit_zero_retains_complete_native_provenance(self):
        i=self.inputs('0','0');r=self.run_inputs(i)['annual_om'];s=r['input_records']['baseline']
        self.assertEqual(s['value'],{'__decimal__':'0'})
        self.assertEqual(s['truth'],'SCN');self.assertEqual(s['evidence_tier'],'E3')
        self.assertEqual(s['scenario_ref'],i.baseline.scenario_ref)
        self.assertEqual(s['reference_period']['start'],{'__date__':'2026-10-21'})
        self.assertIsNotNone(r['input_records_sha256'])

    def test_q_reason_and_acquisition_retained(self):
        r=self.run_inputs(self.inputs(None,'150'))['annual_om']['input_records']['baseline']
        self.assertEqual(r['truth'],'Q');self.assertIsNone(r['value'])
        self.assertEqual(r['reason'],'Unknown test amount');self.assertEqual(r['acquisition_ref'],'B12-D03')

    def test_source_admission_and_reference_period_changes_stay_distinct(self):
        from dataclasses import replace
        from datetime import date
        i=self.inputs();amount=replace(i.programme,truth='DER',source_ids=('TEST_SOURCE_ONLY_A',),scenario_ref=None,evidence_tier='E2',admission_ref='TEST_REVIEW_A')
        a=self.run_inputs(replace(i,programme=amount))['annual_om']
        other=replace(amount,source_ids=('TEST_SOURCE_ONLY_B',),admission_ref='TEST_REVIEW_B',reference_period=self.native.Period(date(2026,10,20),date(2026,10,20)))
        b=self.run_inputs(replace(i,programme=other))['annual_om']
        self.assertNotEqual(a['input_records_sha256'],b['input_records_sha256'])
        self.assertEqual(b['input_records']['programme']['source_ids']['__tuple__'],['TEST_SOURCE_ONLY_B'])
        self.assertEqual(b['input_records']['programme']['admission_ref'],'TEST_REVIEW_B')

    def test_all_bridge_and_coverage_references_retained(self):
        from dataclasses import replace
        i=self.inputs();original=self.run_inputs(i)['annual_om']
        for field in ['money_bridge','baseline_coverage','programme_coverage']:
            changed=replace(i,**{field:self.native.Reference('EXTERNAL_ADMISSION','DIFFERENT_'+field,None,None)})
            r=self.run_inputs(changed)['annual_om']
            self.assertNotEqual(original['input_records_sha256'],r['input_records_sha256'])
            self.assertEqual(r['input_records'][field]['ref'],'DIFFERENT_'+field)
        changed=replace(i,money_basis=replace(i.money_basis,convention=self.native.Reference('EXTERNAL_ADMISSION','DIFFERENT_CONVENTION',None,None)))
        r=self.run_inputs(changed)['annual_om']
        self.assertNotEqual(original['input_records_sha256'],r['input_records_sha256'])
        self.assertEqual(r['input_records']['money_basis']['convention']['ref'],'DIFFERENT_CONVENTION')

    def test_returned_input_identity_verifiable(self):
        import hashlib
        r=self.run_inputs(self.inputs())['annual_om']
        expected=hashlib.sha256(json.dumps(r['input_records'],sort_keys=True,separators=(',',':'),ensure_ascii=True,allow_nan=False).encode('utf-8')).hexdigest()
        self.assertEqual(r['input_records_sha256'],expected)

    def test_subtotal_rejects_changed_provenance_or_derived_delta(self):
        from modules.B12.annual_reference_adapter import energy_minus_om_component
        r=self.run_inputs(self.inputs());r['annual_om']['input_records']['programme']['scenario_ref']='MUTATED'
        with self.assertRaises(ReferenceError):energy_minus_om_component(r,0)
        r=self.run_inputs(self.inputs());r['annual_om']['delta_programme_minus_baseline_HUF_exact']='0'
        with self.assertRaises(ReferenceError):energy_minus_om_component(r,0)

    def test_analogous_identifier_padding_refused(self):
        from dataclasses import replace
        i=self.inputs()
        for changed in [replace(i,scope_ref=i.scope_ref+' '),replace(i,household_id=i.household_id+' '),
                        replace(i,money_bridge=self.native.Reference('EXTERNAL_ADMISSION','REF ',None,None)),
                        replace(i,programme=replace(i.programme,scenario_ref='SCN '))]:
            with self.assertRaises(ReferenceError):self.run_inputs(changed)


if __name__=='__main__':unittest.main(verbosity=2)
