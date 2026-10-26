"""Actual candidate sources and import origin; no new model choices."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from modules.B04 import engine as b04
from modules.B12 import input_accounting_contract as native
from modules.B12 import source_cost_inputs as costs
from modules.B12 import a1_reference_response as a1
from modules.B12 import annual_reference_adapter as annual

ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/'data/processed/b12'
BINDING=DATA/'annual_reference_input_binding.json'

def read(p):return json.loads(p.read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()


class RepositoryIntegrationTests(unittest.TestCase):
    def test_actual_imports_and_shared_native_identity(self):
        for module,relative in [(b04,'modules/B04/engine.py'),
            (native,'modules/B12/input_accounting_contract.py'),
            (costs,'modules/B12/source_cost_inputs.py'),
            (a1,'modules/B12/a1_reference_response.py'),
            (annual,'modules/B12/annual_reference_adapter.py')]:
            self.assertEqual(Path(module.__file__).resolve(),ROOT/relative)
        self.assertIs(a1.native,native)
        self.assertIs(annual.native,native)
        self.assertIs(costs.Cost,native.Cost)

    def test_c01_real_source_to_actual_native_audit(self):
        catalogue=costs.load_source_catalogue(ROOT,'data/processed/b12/source_catalogue.json',
            expected_sha256=sha(DATA/'source_catalogue.json'))
        case=annual._decode(read(ROOT/'inputs/annual_reference/C01_NATIVE_CASE.json'),native)
        bindings=tuple(read(DATA/'unresolved_target_bindings.json')['bindings'])
        result=costs.resolve_cost_inputs(catalogue,bindings,case.monetary_basis,
            case_context=costs.case_cost_context(case))
        self.assertEqual((len(result.observations),sum(x.price.value is not None for x in result.observations)),(23,22))
        self.assertEqual(case.costs.rows,result.costs)
        self.assertEqual(len(result.costs),1)
        self.assertEqual(str(result.costs[0].gross.value),'1220781')
        self.assertEqual(sum(x['quantity']['value'] is None for x in bindings),17)
        self.assertIsNone(result.full_capex)
        audit=native.audit_accounting(case,source_catalogue=catalogue,cost_bindings=bindings)
        self.assertEqual(audit.source_costs,result.costs)
        self.assertEqual(str(audit.amounts['qualified_initial_cost_subset.programme']),'1220781')
        self.assertTrue(audit.unavailable['total_initial_cost'])
        self.assertEqual(audit.truth,'Q')
        self.assertEqual(len(audit.source_cost_cash_rows),1)
        cash=audit.source_cost_cash_rows[0]
        self.assertEqual(str(cash.unfinanced),'-1220781')
        self.assertEqual((cash.event_id,cash.period),(result.costs[0].event_id,result.costs[0].period))
        self.assertEqual((audit.rows,audit.liquidity,cash.bank,cash.financed),((),(),None,None))

    def test_a1_reads_hourly_source_and_active_producers(self):
        r=a1.load_reference(ROOT)
        self.assertEqual([p.hours for p in r.periods],[5086,3674])
        self.assertFalse(r.complete_local_civil_year)
        pins=dict(r.provenance)
        self.assertEqual(pins['repo/modules/B12/input_accounting_contract.py'],sha(Path(native.__file__)))
        self.assertNotEqual(pins['historical_B12_adapter'],sha(Path(native.__file__)))

    def test_annual_binding_retains_unknowns_and_original_result(self):
        policy=read(DATA/'NORMALIZED_YEAR_POLICY.json')
        result=annual.prepare(BINDING,policy)
        self.assertEqual(result,read(ROOT/'inputs/annual_reference/ACCEPTED_V3_CURRENT_RESULT.json'))
        self.assertFalse(result['complete'])
        self.assertEqual(result['annual_om']['status'],'INCOMPLETE_ANNUAL_OM')
        self.assertEqual((result['new_Costs'],result['new_BillInputs']),(0,0))
        self.assertIsNone(result['ROI'])

    def test_relative_binding_rejects_escape(self):
        for bad in ['../outside.json',str(ROOT.parent/'outside.json')]:
            with self.subTest(path=bad):
                with self.assertRaises(annual.ReferenceError):annual._bound_path(bad)

    def test_active_relocated_review_still_binds_offer_revision(self):
        offers={x['offer_id']:x for x in read(DATA/'source_catalogue.json')['offers']}
        for use in read(DATA/'qualified_use_reviews.json')['uses']:
            self.assertEqual(use['offer_evidence_revision'],costs.offer_evidence_revision(offers[use['offer_id']]))

    def test_clean_process_from_unrelated_cwd_imports_candidate_only(self):
        code='''import json,sys
from pathlib import Path
from modules.B12 import annual_reference_adapter as a
from modules.B12 import a1_reference_response as b
from modules.B12 import source_cost_inputs as c
root=Path(sys.argv[1]).resolve()
assert all(Path(m.__file__).resolve().is_relative_to(root) for m in [a,b,c,a.native,b.b04])
assert a.native is b.native
assert all('candidate-mvm-b07-b08' not in p and 'energy-annual-adapter-om-' not in p for p in sys.path)
r=a.prepare(root/'data/processed/b12/annual_reference_input_binding.json')
assert r['status']=='INCOMPLETE_TEMPORAL_BINDING'
print(json.dumps({'files':[str(Path(m.__file__).resolve()) for m in [a,b,c,a.native,b.b04]],'status':r['status']}))
'''
        env=dict(os.environ,PYTHONPATH=str(ROOT),PYTHONDONTWRITEBYTECODE='1',PYTHONIOENCODING='utf-8')
        with tempfile.TemporaryDirectory() as unrelated:
            p=subprocess.run([sys.executable,'-B','-c',code,str(ROOT)],cwd=unrelated,
                env=env,capture_output=True,text=True,encoding='utf-8')
        self.assertEqual(p.returncode,0,p.stdout+p.stderr)
        self.assertEqual(len(json.loads(p.stdout)['files']),5)


if __name__=='__main__':unittest.main()
