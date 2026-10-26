"""Qualified C01 model cash event, not an invoice or complete cash flow."""
import copy
from dataclasses import replace
from datetime import date
from decimal import Decimal, localcontext, ROUND_DOWN
import hashlib
import json
from pathlib import Path
import unittest
from unittest.mock import patch

from modules.B12 import input_accounting_contract as native
from modules.B12 import source_cost_inputs as source
from modules.B12 import annual_reference_adapter as annual
from modules.B12 import a1_reference_response as a1

ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/'data/processed/b12'

def read(p):return json.loads(p.read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

class QualifiedC01CashTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.case=annual._decode(read(ROOT/'inputs/annual_reference/C01_NATIVE_CASE.json'),native)
        cls.bindings=tuple(read(DATA/'unresolved_target_bindings.json')['bindings'])
        cls.catalogue=source.load_source_catalogue(ROOT,'data/processed/b12/source_catalogue.json',expected_sha256=sha(DATA/'source_catalogue.json'))

    def audit(self,case=None,bindings=None):
        return native.audit_accounting(case or self.case,source_catalogue=self.catalogue,
            cost_bindings=self.bindings if bindings is None else bindings)

    def test_actual_C01_one_signed_event_at_approved_model_date(self):
        audit=self.audit();self.assertEqual(len(audit.source_cost_cash_rows),1)
        row=audit.source_cost_cash_rows[0];cost=audit.source_costs[0]
        self.assertIs(type(row),native.AuditRow)
        self.assertEqual(row.unfinanced,Decimal('-1220781'))
        self.assertEqual((row.leg,row.event_id,row.category,row.period),
            (cost.leg,cost.event_id,'INITIAL_CAPEX',cost.period))
        self.assertEqual((row.period.start,row.period.end),(date(2028,1,1),date(2028,1,1)))
        self.assertEqual(cost.quantity.value,Decimal(1))
        self.assertEqual(cost.scope_ref,'SCN-HH1-OUTDOOR-C01')

    def test_provenance_links_actual_native_cost_and_retains_source_review(self):
        audit=self.audit();row=audit.source_cost_cash_rows[0];cost=self.case.costs.rows[0]
        self.assertEqual(row.input_paths,('case.costs.rows[0]',))
        self.assertEqual(audit.source_costs,(cost,))
        self.assertEqual(dict(audit.provenance)['case.costs.rows[0].gross'],cost.gross)
        self.assertTrue(cost.gross.source_ids)
        self.assertTrue(cost.attribution.ref)
        self.assertEqual(self.bindings[0]['review_id'],'USE-C01-WM50-SCN-T0-20261023')
        self.assertEqual(cost.payer,'SCN-MODEL-HH1')
        self.assertIn('NOT-A-SELECTED-VENDOR',cost.payee)

    def test_partial_cash_does_not_unlock_complete_boundary_or_financing(self):
        audit=self.audit();row=audit.source_cost_cash_rows[0]
        self.assertEqual((row.financed,row.bank,row.recurring),(None,None,None))
        self.assertEqual((audit.truth,audit.rows,audit.liquidity),('Q',(),()))
        for key in ['total_initial_cost','unfinanced_cash','financed_cash','bank_liquidity','valuation']:
            self.assertTrue(audit.unavailable[key])
        for key in ['total_initial_cost.programme','unfinanced_cash.programme','financed_cash.programme','ROI']:
            self.assertNotIn(key,audit.amounts)
        self.assertEqual(audit.amounts['qualified_initial_cost_subset.programme'],Decimal('1220781'))

    def test_replay_idempotent_and_no_second_quantity_or_recurrence(self):
        first=self.audit();second=self.audit()
        self.assertEqual(first.source_cost_cash_rows,second.source_cost_cash_rows)
        self.assertEqual(len({r.event_id for r in first.source_cost_cash_rows}),1)
        self.assertEqual(len(first.source_cost_cash_rows),1)
        self.assertEqual(first.source_cost_cash_rows[0].unfinanced,-first.source_costs[0].gross.value)

    def test_missing_catalogue_or_missing_use_review_has_no_cash_rows(self):
        self.assertEqual(native.audit_accounting(self.case).source_cost_cash_rows,())
        bindings=copy.deepcopy(self.bindings);bindings[0]['review_id']='UNRESOLVED-REVIEW'
        self.assertEqual(self.audit(bindings=bindings).source_cost_cash_rows,())

    def test_unknown_quantity_or_cash_period_not_zero_or_default_date(self):
        for field in ['quantity','cash_period']:
            bindings=copy.deepcopy(self.bindings)
            # A missing-input request is not the previously reviewed binding.
            # Reusing that old review is separately required to fail closed.
            bindings[0]['review_id']='UNRESOLVED-MISSING-DATA'
            if field=='quantity':
                bindings[0]['quantity'].update(value=None,truth='Q',source_ids=[],scenario_ref=None,
                    evidence_tier=None,admission_ref=None,reason='not supplied',acquisition_ref='B12-D01')
            else:bindings[0]['cash_period']=None
            audit=self.audit(bindings=bindings)
            self.assertEqual(audit.source_cost_cash_rows,())
            self.assertTrue(audit.source_cost_missing)

    def test_old_review_cannot_authorize_erasure_of_quantity_or_date(self):
        for field in ['quantity','cash_period']:
            bindings=copy.deepcopy(self.bindings)
            if field=='quantity':
                bindings[0]['quantity'].update(value=None,truth='Q',source_ids=[],scenario_ref=None,
                    evidence_tier=None,admission_ref=None,reason='missing',acquisition_ref='B12-D01')
            else:bindings[0]['cash_period']=None
            with self.assertRaises(native.B12ContractError):self.audit(bindings=bindings)

    def test_reusing_review_for_new_event_date_role_or_quantity_rejected(self):
        for key,value in [('cash_period',['2028-01-02','2028-01-02']),('event_id','OTHER-EVENT'),
                          ('payer','OTHER-HOUSEHOLD')]:
            bindings=copy.deepcopy(self.bindings);bindings[0][key]=value
            with self.subTest(field=key),self.assertRaises(native.B12ContractError):self.audit(bindings=bindings)
        bindings=copy.deepcopy(self.bindings);bindings[0]['quantity']['value']='2'
        with self.assertRaises(native.B12ContractError):self.audit(bindings=bindings)

    def test_tampered_native_cost_or_period_does_not_use_resolved_cash(self):
        cost=self.case.costs.rows[0]
        for bad in [replace(cost,gross=replace(cost.gross,value=Decimal('1220782'))),
                    replace(cost,period=native.Period(date(2028,1,2),date(2028,1,2)))]:
            case=replace(self.case,costs=replace(self.case.costs,rows=(bad,)))
            with self.assertRaises(native.B12ContractError):self.audit(case=case)

    def test_duplicate_costs_or_resolution_bindings_rejected(self):
        case=replace(self.case,costs=replace(self.case.costs,rows=self.case.costs.rows*2))
        with self.assertRaises(native.B12ContractError):self.audit(case=case)
        with self.assertRaises(native.B12ContractError):self.audit(bindings=(self.bindings[0],)+self.bindings)

    def test_fact_hash_drift_rejected_before_cash_output(self):
        manifest=read(DATA/'source_catalogue.json')
        offer=next(x for x in manifest['offers'] if x['offer_id']=='OUTDOOR_GROSS')
        fact=(ROOT/offer['fact_pin']['path']).resolve();original=Path.read_bytes
        def changed(p):
            raw=original(p)
            return raw+b'\n' if p.resolve()==fact else raw
        with patch.object(Path,'read_bytes',changed),self.assertRaises(native.B12ContractError):self.audit()

    def test_precision_and_rounding_do_not_change_the_signed_cost(self):
        with localcontext() as ctx:
            ctx.prec=2;ctx.rounding=ROUND_DOWN
            self.assertEqual(self.audit().source_cost_cash_rows[0].unfinanced,Decimal('-1220781'))
            self.assertEqual(ctx.prec,2)

    def test_historical_and_current_implementation_pins_are_distinct(self):
        self.assertEqual(sha(ROOT/'modules/B12/input_accounting_contract.py'),a1.NATIVE_IMPLEMENTATION_SHA)
        self.assertNotEqual(a1.NATIVE_C01_BASELINE_SHA,a1.NATIVE_IMPLEMENTATION_SHA)
        ref=a1.load_reference(ROOT);proof=dict(ref.provenance)
        self.assertEqual(proof['accepted_C01_B12_baseline'],a1.NATIVE_C01_BASELINE_SHA)
        self.assertEqual(proof['repo/modules/B12/input_accounting_contract.py'],a1.NATIVE_IMPLEMENTATION_SHA)
        self.assertEqual(sha(ROOT/'inputs/annual_reference/history/C01_ARTIFACT_MANIFEST.json'),
            '27653e8dea750ef82813ccf3e93a0a4e8c7784bcf19f62da7de55a380b164e61')

    def test_rehashed_native_revision_or_relabelled_baseline_rejected(self):
        original=Path.read_bytes
        for field in ['active_implementation','accepted_C01_B12_baseline_sha256']:
            def altered(p):
                raw=original(p)
                if p.name=='A1_INPUT_BINDING.json':
                    d=json.loads(raw)
                    if field=='active_implementation':d[field]['repo/modules/B12/input_accounting_contract.py']='0'*64
                    else:d[field]=a1.NATIVE_IMPLEMENTATION_SHA
                    return json.dumps(d).encode()
                return raw
            with patch.object(Path,'read_bytes',altered),self.assertRaises(a1.A1ReferenceError):a1.load_reference(ROOT)
        binding=DATA/'annual_reference_input_binding.json';original_text=Path.read_text
        def altered_binding(p,*args,**kwargs):
            text=original_text(p,*args,**kwargs)
            if p==binding:
                d=json.loads(text);d['sources']['native']['baseline_sha256']=a1.NATIVE_IMPLEMENTATION_SHA
                return json.dumps(d)
            return text
        with patch.object(Path,'read_text',altered_binding),self.assertRaises(annual.ReferenceError):annual.prepare(binding)

if __name__=='__main__':unittest.main()
