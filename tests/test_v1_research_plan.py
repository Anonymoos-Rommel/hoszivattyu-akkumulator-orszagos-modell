"""Planning integrity only; these tests do not validate any research result."""
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class V1ResearchPlanTests(unittest.TestCase):
    def setUp(self):
        self.plan = json.loads((ROOT / 'registry/v1_research_plan.json').read_text())

    def test_module_and_slice_identity(self):
        modules = self.plan['modules']
        self.assertEqual([m['id'] for m in modules], [f'B{i:02d}' for i in range(1, 21)])
        ids = [s['slice_id'] for m in modules for s in m['slices']]
        self.assertEqual(len(ids), 58)
        self.assertEqual(len(set(ids)), 58)
        for m in modules:
            for field in ['dependencies', 'e2', 'accept', 'stop']:
                self.assertTrue(m[field].strip())
            for s in m['slices']:
                self.assertTrue(s['slice_id'].startswith(m['id'] + '-'))
                self.assertTrue(s['data'].strip())
                self.assertIn(s['phase'], ['A', 'V', 'V↔A'])

    def test_acceptance_requires_artifacts_consumers_and_review(self):
        for m in self.plan['modules']:
            for s in m['slices']:
                self.assertIn(s['status'], ['NOT_STARTED', 'RESEARCHING', 'INTEGRATING', 'REVIEW_REQUIRED', 'ACCEPTED', 'PAUSED'])
                if s['status'] == 'ACCEPTED':
                    self.assertTrue(s['accepted_artifacts'], s['slice_id'])
                    self.assertTrue(s['consumer_tests'], s['slice_id'])
                    self.assertRegex(s['reviewed_commit'] or '', r'^[0-9a-f]{40}$')
                    self.assertTrue(s['research_log'], s['slice_id'])

    def test_authority_paths_exist(self):
        for field in ['evidence_policy', 'execution_contract']:
            self.assertTrue((ROOT / self.plan[field]).is_file())


if __name__ == '__main__':
    unittest.main()
