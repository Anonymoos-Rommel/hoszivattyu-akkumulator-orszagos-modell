"""Two historical B11 pins do not grant current EOH replay permission."""
import hashlib,json,subprocess,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from tools import validate_registry as v
from tools import analyze_b05_eoh_annual_transfer as annual
from modules.B07 import shared_use_schedule_contract as shared

class HistoricalBoundaryTests(unittest.TestCase):
    def specs(self):
        for name in v._EOH_HISTORICAL_B11:
            m=json.loads((v.REGISTRY/name).read_text());yield name,m,m['protected_sha256'][v._EOH_B11_PATH]
    def test_exact_historical_blobs_match_while_live_differs(self):
        for name,m,h in self.specs():
            with self.subTest(name=name):
                self.assertTrue(v._eoh_protected_matches(name,m,v._EOH_B11_PATH,h))
                self.assertNotEqual(hashlib.sha256((v.ROOT/v._EOH_B11_PATH).read_bytes()).hexdigest(),h)
    def test_missing_wrong_base_and_hash_fail_closed(self):
        for name,m,h in self.specs():
            for base in (None,'','f'*40):
                with self.subTest(name=name,base=base):self.assertFalse(v._eoh_protected_matches(name,{**m,'base_commit':base},v._EOH_B11_PATH,h))
            for wrong in ('0'*64,'xyz',None):self.assertFalse(v._eoh_protected_matches(name,m,v._EOH_B11_PATH,wrong))
    def test_missing_local_history_fails_closed(self):
        with tempfile.TemporaryDirectory() as d,patch.object(v,'ROOT',Path(d)):
            for name,m,h in self.specs():self.assertFalse(v._eoh_protected_matches(name,m,v._EOH_B11_PATH,h))
    def test_missing_blob_wrong_bytes_timeout_and_no_replace(self):
        for name,m,h in self.specs():
            for result in (subprocess.CompletedProcess([],128,b'',b'missing blob'),subprocess.CompletedProcess([],0,b'wrong blob',b'')):
                with patch.object(v.subprocess,'run',return_value=result) as run:
                    self.assertFalse(v._eoh_protected_matches(name,m,v._EOH_B11_PATH,h))
                    self.assertIn('--no-replace-objects',run.call_args.args[0])
                    self.assertEqual(run.call_args.kwargs['env']['GIT_NO_LAZY_FETCH'],'1')
            with patch.object(v.subprocess,'run',side_effect=subprocess.TimeoutExpired('git',10)):
                self.assertFalse(v._eoh_protected_matches(name,m,v._EOH_B11_PATH,h))
    def test_unlisted_manifest_or_other_file_stays_live(self):
        for name,m,h in self.specs():
            self.assertFalse(v._eoh_protected_matches('other.json',m,v._EOH_B11_PATH,h))
            other='modules/B05/engine.py';good=m['protected_sha256'][other]
            self.assertTrue(v._eoh_protected_matches(name,m,other,good))
            with tempfile.TemporaryDirectory() as d:
                f=Path(d)/other;f.parent.mkdir(parents=True);f.write_text('changed')
                with patch.object(v,'ROOT',Path(d)):self.assertFalse(v._eoh_protected_matches(name,m,other,good))
            self.assertFalse(v._eoh_protected_matches(name,m,'../outside','0'*64))
    def test_historical_manifests_and_current_analyzer_unchanged(self):
        expected={'registry/b05_eoh_comparison_support_manifest.json':'73405d6c66224baca3c430b9a3132e5924d7148465276446b1608b2fe2998c50','registry/b05_eoh_annual_transfer_manifest.json':'f98b4de28b726f6b755e00bdeb6a7a82b9e0e0e5f0c24d97bee550a56c2ed8be','tools/analyze_b05_eoh_annual_transfer.py':'22d2e6e9586b68b0d67aee1dd871f40411a3bcc1e82df73a531e18721af783fd'}
        for name,h in expected.items():self.assertEqual(hashlib.sha256((v.ROOT/name).read_bytes()).hexdigest(),h)
    def test_actual_current_rerun_guard_still_rejects_before_output(self):
        # Mock only unavailable private-input/prior-output verification, not the
        # protected-file guard. No EOH data loaded or numerical analysis reached.
        spec=json.loads(annual.MANIFEST.read_text());cfg=spec['aggregate_assessment'];real_digest=annual.digest
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);prior=root/'prior';prior.mkdir();target=prior/'INPUT_CODE_OUTPUT_MANIFEST.json'
            target.write_text(json.dumps({'research_code_sha256':cfg['prior_merged_code_sha256'],'outputs':[]}));output=root/'output'
            def digest(path):return cfg['prior_output_manifest_sha256'] if Path(path)==target else real_digest(path)
            with patch.object(annual,'verify_additive'),patch.object(annual.comparison,'verify_handoff'),patch.object(annual,'digest',side_effect=digest):
                with self.assertRaisesRegex(ValueError,'protected runtime/evidence changed'):
                    annual.assess_aggregate_e2(root/'additive',root/'handoff',prior,output)
            self.assertFalse(output.exists())
    def test_b07_live_pin_valid_and_other_dependency_tamper_rejected(self):
        shared.load_shared_use_contract()
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);data=json.loads((shared.ROOT/'registry/b07_shared_use_schedule_contract.json').read_text())
            for binding in data['source_bindings']:
                p=root/binding['path'];p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes((shared.ROOT/binding['path']).read_bytes())
            reg=root/'registry/b07_shared_use_schedule_contract.json';reg.parent.mkdir(exist_ok=True);reg.write_text(json.dumps(data))
            (root/data['source_bindings'][1]['path']).write_text('tampered')
            with patch.object(shared,'ROOT',root),self.assertRaisesRegex(shared.SharedUseError,'dependency bytes changed'):shared.load_shared_use_contract()
if __name__=='__main__':unittest.main()
