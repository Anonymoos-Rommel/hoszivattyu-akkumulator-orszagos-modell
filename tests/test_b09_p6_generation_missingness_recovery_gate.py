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

    def test_mavir_two_measurement_bases_are_primary_candidates(self):
        r = {row["record_id"]: row for row in rows(REGISTRY)}
        self.assertEqual("PRIMARY_AGGREGATE_RECOVERY", r["B09-P6-R02"]["recovery_route"])
        self.assertEqual("PRIMARY_AGGREGATE_RECOVERY", r["B09-P6-R03"]["recovery_route"])
        self.assertIn("elszámolási", r["B09-P6-R02"]["source_product"])
        self.assertIn("üzemirányítási", r["B09-P6-R03"]["source_product"])
        self.assertIn("OVERLAP_VALIDATION", r["B09-P6-R02"]["residual_gap"])

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
        self.assertIn("NO_UNIT_LEVEL_COMPLETENESS_INFERENCE", x["canonical_base_rule"])

    def test_open_question_has_exact_new_residual(self):
        q = {row["question_id"]: row for row in rows(QUESTIONS)}
        notes = q["Q-B09-001"]["notes"]
        self.assertIn("MAVIR_2025_FUEL_TYPE_EXPORTS_REQUIRED", notes)
        self.assertIn("SEMANTIC_ALIGNMENT_AND_OVERLAP_VALIDATION_REQUIRED", notes)


if __name__ == "__main__":
    unittest.main()
