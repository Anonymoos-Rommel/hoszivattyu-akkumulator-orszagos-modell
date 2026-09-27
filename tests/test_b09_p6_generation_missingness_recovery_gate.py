import csv
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "registry" / "b09_p6_generation_missingness_recovery_gate.csv"
QUESTIONS = ROOT / "registry" / "open_questions.csv"
AUDIT = ROOT / "registry" / "project_blocker_evidence_audit.csv"
PACK = ROOT / "docs" / "source_packs" / "B09_P6_GENERATION_MISSINGNESS_RECOVERY_GATE.md"


def rows(path):
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


class B09P6GenerationMissingnessRecoveryGateTests(unittest.TestCase):
    def test_area_view_switching_is_exhausted(self):
        r = {row["record_id"]: row for row in rows(REGISTRY)}
        x = r["B09-P6-R01"]
        self.assertEqual("EXHAUSTED_NO_RECOVERY", x["current_state"])
        self.assertIn("09ede94527e3539", x["notes"])
        self.assertEqual("CONTENT_IDENTICAL_NO_NEW_VALUES", x["disqualifier"])

    def test_mavir_settlement_basis_is_acquired_and_operational_basis_is_next(self):
        r = {row["record_id"]: row for row in rows(REGISTRY)}
        settlement = r["B09-P6-R02"]
        operational = r["B09-P6-R03"]
        self.assertEqual("PRIMARY_AGGREGATE_RECOVERY", settlement["recovery_route"])
        self.assertEqual("ACQUIRED_COMPLETE_CANDIDATE", settlement["current_state"])
        self.assertIn("elszámolási", settlement["source_product"])
        self.assertIn("b0c1a200cad87773", settlement["notes"])
        self.assertIn("82.44199095", settlement["notes"])
        self.assertEqual("PRIMARY_AGGREGATE_RECOVERY", operational["recovery_route"])
        self.assertEqual("ACQUISITION_REQUIRED", operational["current_state"])
        self.assertIn("üzemirányítási", operational["source_product"])
        self.assertIn("NET_OPERATIONAL_2025_EXPORT_REQUIRED", operational["residual_gap"])

    def test_a73_is_secondary_threshold_bound_not_complete_aggregate(self):
        r = {row["record_id"]: row for row in rows(REGISTRY)}
        x = r["B09-P6-R04"]
        self.assertEqual("SECONDARY_ONLY", x["current_state"])
        self.assertIn("GE_100MW", x["disqualifier"])
        text = PACK.read_text(encoding="utf-8")
        self.assertIn("100 MW or more", text)
        self.assertIn("SUM(A73 PUBLISHED UNITS) != PROVEN COMPLETE A75 PRODUCTION_TYPE TOTAL", text)

    def test_blank_to_zero_remains_forbidden(self):
        r = {row["record_id"]: row for row in rows(REGISTRY)}
        x = r["B09-P6-R05"]
        self.assertEqual("ACTIVE", x["current_state"])
        self.assertIn("BLANK_TO_ZERO", x["disqualifier"])
        self.assertIn("Fossil Oil=4817", x["notes"])

    def test_blocker_remains_e3_until_recovery(self):
        audit = {row["blocker_id"]: row for row in rows(AUDIT)}
        x = audit["Q-B09-001"]
        self.assertEqual("E3", x["evidence_tier"])
        self.assertEqual("MODEL_BLOCKER", x["blocker_class"])
        self.assertEqual("yes", x["model_blocker"])
        self.assertIn("MAVIR_NET_SETTLEMENT_2025_COMPLETE_EXTERNAL_ONLY", x["canonical_base_rule"])
        self.assertIn("NO_SPLICE_BEFORE_DUAL_BASIS_SELECTION", x["canonical_base_rule"])

    def test_open_question_has_exact_new_residual(self):
        q = {row["question_id"]: row for row in rows(QUESTIONS)}
        notes = q["Q-B09-001"]["notes"]
        self.assertIn("NET_OPERATIONAL_2025_EXPORT_REQUIRED_FOR_DUAL_BASIS_SELECTION", notes)
        self.assertIn("DUAL_BASIS_OVERLAP_SELECTION_REQUIRED", notes)


if __name__ == "__main__":
    unittest.main()
