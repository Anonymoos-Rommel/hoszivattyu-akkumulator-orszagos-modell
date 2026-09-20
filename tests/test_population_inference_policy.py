import csv
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
POLICY = ROOT / "docs" / "methodology" / "population_inference_policy.md"
CHARTER = ROOT / "PROJECT_CHARTER.md"
AGENTS = ROOT / "AGENTS.md"
README = ROOT / "README.md"
OPEN_QUESTIONS = ROOT / "registry" / "open_questions.csv"


class PopulationInferencePolicyTests(unittest.TestCase):
    def test_project_wide_policy_freezes_core_non_equivalence(self):
        text = POLICY.read_text(encoding="utf-8")
        self.assertIn("NO FULL-POPULATION DATA != BLOCKER", text)
        self.assertIn("NO DEFENSIBLE POPULATION INFERENCE == BLOCKER", text)
        self.assertIn("POPULATION ESTIMATE != RECORD PASS/FAIL", text)
        self.assertIn("REPRESENTATIVE_OBSERVED_SAMPLE", text)
        self.assertIn("CALIBRATED_MULTI_SOURCE_INFERENCE", text)
        self.assertIn("BOUNDED_ENGINEERING_VALIDATION", text)
        self.assertIn("MARGINALS != JOINT", text)

    def test_core_repository_docs_bind_to_policy(self):
        charter = CHARTER.read_text(encoding="utf-8")
        agents = AGENTS.read_text(encoding="utf-8")
        readme = README.read_text(encoding="utf-8")
        self.assertIn("NO FULL-POPULATION DATA != BLOCKER", charter)
        self.assertIn("population_inference_policy.md", agents)
        self.assertIn("population_inference_policy.md", readme)
        self.assertIn("Record-level decisions still require record-level evidence", agents)

    def test_b02_questions_accept_defensible_inference_but_remain_open(self):
        with OPEN_QUESTIONS.open(encoding="utf-8", newline="") as handle:
            rows = {row["question_id"]: row for row in csv.DictReader(handle)}

        q1 = rows["Q-B02-001"]
        q4 = rows["Q-B02-004"]
        self.assertEqual("OPEN", q1["status"])
        self.assertEqual("OPEN", q4["status"])
        self.assertIn("reprezentatív", q1["evidence_needed"])
        self.assertIn("kalibrált", q1["evidence_needed"])
        self.assertIn("önmagában nem blocker", q1["notes"])
        self.assertIn("reprezentatív", q4["evidence_needed"])
        self.assertIn("uncertainty", q4["evidence_needed"])
        self.assertIn("2026-08-22", q4["notes"])
        self.assertIn("record-level evidence", q4["notes"])

    def test_policy_does_not_promote_sample_estimates_to_observed_population_truth(self):
        text = POLICY.read_text(encoding="utf-8")
        self.assertIn("national estimate calculated from them is normally `DER`", text)
        self.assertIn("does not inherit `OBS`", text)
        self.assertIn("individual network-node facts remain node-specific", text)


if __name__ == "__main__":
    unittest.main()
