import csv
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
QUESTIONS = ROOT / "registry" / "open_questions.csv"
LINKAGE = ROOT / "registry" / "b02_calibrated_linkage_admission.csv"
DIMENSIONS = ROOT / "registry" / "archetype_dimensions.csv"
P50 = ROOT / "docs" / "source_packs" / "B02_P50_CANONICAL_ARCHETYPE_BLOCKER_REAUDIT.md"
AUDIT = ROOT / "docs" / "source_packs" / "PROJECT_BLOCKER_REAUDIT_2026-09-20.md"


class B02P50CanonicalArchetypeBlockerReauditTests(unittest.TestCase):
    def test_q_b02_002_is_resolved_without_closing_technical_stock_questions(self):
        with QUESTIONS.open(encoding="utf-8", newline="") as handle:
            q = {row["question_id"]: row for row in csv.DictReader(handle)}
        self.assertEqual(q["Q-B02-002"]["status"], "RESOLVED")
        self.assertEqual(q["Q-B02-001"]["status"], "OPEN")
        self.assertEqual(q["Q-B02-004"]["status"], "OPEN")
        self.assertIn("P21", q["Q-B02-002"]["notes"])
        self.assertIn("ASS", q["Q-B02-002"]["notes"])
        self.assertIn("MODELLED", q["Q-B02-002"]["notes"])

    def test_p21_building_and_energy_linkages_are_admitted(self):
        with LINKAGE.open(encoding="utf-8", newline="") as handle:
            rows = {row["claim_id"]: row for row in csv.DictReader(handle)}
        for claim in ("CALIBRATED_BUILDING_TYPE_LINKAGE", "CALIBRATED_PRIMARY_ENERGY_LINKAGE"):
            self.assertEqual(rows[claim]["approval_status"], "APPROVED")
            self.assertEqual(rows[claim]["approval_authority"], "JOSEPH")
            self.assertEqual(rows[claim]["current_status"], "QUALIFIED")
            self.assertEqual(rows[claim]["representativeness_diagnostics"], "yes")
            self.assertEqual(rows[claim]["validation_metrics"], "yes")
            self.assertEqual(rows[claim]["marginal_reconciliation"], "yes")
            self.assertEqual(rows[claim]["uncertainty_method"], "yes")
            self.assertEqual(rows[claim]["uncertainty_propagation"], "yes")
            self.assertEqual(rows[claim]["independence_assumption_controlled"], "yes")

    def test_canonical_archetype_dimensions_are_contracted(self):
        with DIMENSIONS.open(encoding="utf-8", newline="") as handle:
            rows = list(csv.DictReader(handle))
        required = [row for row in rows if row["required"] == "yes"]
        self.assertTrue(required)
        self.assertTrue(all(row["status"] in {"CONTRACTED", "GAP"} for row in required))
        building = next(row for row in rows if row["dimension_id"] == "DIM-B02-BUILDING-TYPE")
        self.assertEqual(building["status"], "CONTRACTED")
        self.assertIn("B02-P21", building["aggregation_rule"])
        self.assertIn("ASS", building["unknown_policy"])

    def test_p50_preserves_population_vs_record_boundaries(self):
        text = P50.read_text(encoding="utf-8")
        self.assertIn("NO FULL-POPULATION DATA != BLOCKER", text)
        self.assertIn("Q-B02-002 -> RESOLVED", text)
        self.assertIn("building-type output is OBS or DER", text)
        self.assertIn("Q-B02-004", text)
        self.assertIn("Q-B02-001", text)

    def test_project_reaudit_covers_every_question(self):
        with QUESTIONS.open(encoding="utf-8", newline="") as handle:
            ids = [row["question_id"] for row in csv.DictReader(handle)]
        text = AUDIT.read_text(encoding="utf-8")
        for qid in ids:
            self.assertIn(f"| {qid} |", text)
        self.assertIn("TARGETED_EXTERNAL_SEARCH", text)
        self.assertIn("CONTINUE_EXISTING_FIRST", text)
        self.assertIn("OWNER_POLICY_DECISION", text)


if __name__ == "__main__":
    unittest.main()
