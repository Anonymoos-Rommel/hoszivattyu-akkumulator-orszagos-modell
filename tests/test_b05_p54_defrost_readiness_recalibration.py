import csv
import unittest
from pathlib import Path

from modules.B05.defrost_readiness_recalibration import (
    GATES,
    MAX_WITHOUT_INDEPENDENT_REPLICATION,
    READINESS_SCORE,
    TOTAL_WEIGHT,
    can_exceed_current_ceiling,
    validate_scorecard,
)

ROOT = Path(__file__).resolve().parents[1]
READINESS = ROOT / "registry" / "heat_pump_readiness.csv"
MODULES = ROOT / "registry" / "module_status.csv"
AUDIT = ROOT / "registry" / "project_blocker_evidence_audit.csv"
SCORECARD = ROOT / "registry" / "b05_p54_defrost_readiness_scorecard.csv"


def rows(path):
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


class B05P54DefrostReadinessRecalibrationTests(unittest.TestCase):
    def test_scorecard_is_bounded_and_canonical(self):
        validate_scorecard()
        self.assertEqual(100, TOTAL_WEIGHT)
        self.assertEqual(65, READINESS_SCORE)
        self.assertEqual(65, MAX_WITHOUT_INDEPENDENT_REPLICATION)
        self.assertEqual(11, len(GATES))

    def test_independent_replication_is_required_above_ceiling(self):
        self.assertFalse(can_exceed_current_ceiling(independent_replication=False))
        self.assertTrue(can_exceed_current_ceiling(independent_replication=True))

    def test_registry_scorecard_matches_module(self):
        data = rows(SCORECARD)
        total = next(row for row in data if row["gate_id"] == "TOTAL")
        self.assertEqual("100", total["weight"])
        self.assertEqual("65", total["earned"])
        self.assertEqual("PARTIAL", total["status"])

    def test_defrost_component_is_recalibrated(self):
        ready = {row["component_id"]: row for row in rows(READINESS)}
        self.assertEqual("PARTIAL", ready["DEFROST"]["status"])
        self.assertEqual("65", ready["DEFROST"]["readiness_percent"])
        self.assertIn("P54", ready["DEFROST"]["notes"])
        self.assertIn(
            "CROSS_PRODUCT_DEFROST_RUNTIME_COVERAGE_REQUIRED",
            ready["DEFROST"]["notes"],
        )

    def test_b05_module_readiness_is_not_mechanically_changed(self):
        modules = {row["module_id"]: row for row in rows(MODULES)}
        self.assertEqual("64", modules["B05"]["readiness_percent"])
        self.assertIn("P54", modules["B05"]["gate_note"])

    def test_q_b05_003_residuals_are_not_erased_by_scoring(self):
        audit = {row["blocker_id"]: row for row in rows(AUDIT)}["Q-B05-003"]
        self.assertEqual("E2", audit["evidence_tier"])
        self.assertIn(
            "CROSS_PRODUCT_DEFROST_RUNTIME_COVERAGE_REQUIRED",
            audit["validation_debt"],
        )
        self.assertIn(
            "HUNGARIAN_WEATHER_TRANSFER_VALIDATION_REQUIRED",
            audit["validation_debt"],
        )


if __name__ == "__main__":
    unittest.main()
