import csv
import unittest
from pathlib import Path

from modules.B05.part_load_readiness_recalibration import (
    GATES,
    READINESS_SCORE,
    TOTAL_WEIGHT,
    open_gate_ids,
    unresolved_gate_ids,
    validate_scorecard,
)

ROOT = Path(__file__).resolve().parents[1]
READINESS = ROOT / "registry" / "heat_pump_readiness.csv"
MODULES = ROOT / "registry" / "module_status.csv"
QUESTIONS = ROOT / "registry" / "open_questions.csv"
AUDIT = ROOT / "registry" / "project_blocker_evidence_audit.csv"
SCORECARD = ROOT / "registry" / "b05_p59_part_load_readiness_scorecard.csv"


def rows(path):
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


class B05P59PartLoadReadinessRecalibrationTests(unittest.TestCase):
    def test_scorecard_is_canonical_and_bounded(self):
        validate_scorecard()
        self.assertEqual(100, TOTAL_WEIGHT)
        self.assertEqual(75, READINESS_SCORE)
        self.assertEqual(12, len(GATES))

    def test_open_gates_are_exact_current_zero_credit_residuals(self):
        self.assertEqual(
            (
                "PRODUCT_SPECIFIC_HEAT_PUMP_TRANSIENT_AUTHORITY",
                "EXACT_FCC06_OBS_TRANSIENT_MASS_BINDING",
            ),
            open_gate_ids(),
        )
        self.assertIn("COLD_HIGH_SUPPLY_COORDINATE_COVERAGE", unresolved_gate_ids())
        self.assertIn("DIRECT_FIELD_CYCLING_MODULATION_VALIDATION", unresolved_gate_ids())

    def test_registry_scorecard_matches_module(self):
        scorecard = {r["gate_id"]: r for r in rows(SCORECARD)}
        self.assertEqual("100", scorecard["TOTAL"]["weight"])
        self.assertEqual("75", scorecard["TOTAL"]["earned"])
        self.assertEqual("PARTIAL", scorecard["TOTAL"]["status"])

    def test_part_load_component_is_recalibrated(self):
        ready = {r["component_id"]: r for r in rows(READINESS)}
        row = ready["PART_LOAD_MODULATION"]
        self.assertEqual("PARTIAL", row["status"])
        self.assertEqual("75", row["readiness_percent"])
        self.assertIn("P59", row["notes"])
        self.assertIn(
            "EXACT_VDE_328782_TL2_1_REPORT_CONTENT_OR_SOURCE_NATIVE_TRANSIENT_EXCERPT_REQUIRED",
            row["notes"],
        )

    def test_b05_module_readiness_is_not_mechanically_changed(self):
        modules = {r["module_id"]: r for r in rows(MODULES)}
        self.assertEqual("64", modules["B05"]["readiness_percent"])
        self.assertIn("P59", modules["B05"]["gate_note"])

    def test_q_b05_004_remains_open_e2_validation_debt(self):
        q = {r["question_id"]: r for r in rows(QUESTIONS)}["Q-B05-004"]
        self.assertEqual("OPEN", q["status"])
        self.assertIn("B05-P59", q["notes"])
        audit = {r["blocker_id"]: r for r in rows(AUDIT)}["Q-B05-004"]
        self.assertEqual("E2", audit["evidence_tier"])
        self.assertEqual("VALIDATION_BLOCKER", audit["blocker_class"])
        self.assertEqual("MODEL_CONTINUE", audit["canonical_use"])
        self.assertIn(
            "EXACT_PUZ_WM50_TESTED_SPECIMEN_BINDING",
            audit["validation_debt"],
        )


if __name__ == "__main__":
    unittest.main()
