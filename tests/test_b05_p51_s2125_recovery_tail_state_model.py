import csv
import unittest
from pathlib import Path

from modules.B05.s2125_defrost_recovery_tail import (
    can_admit_full_cycle_constant,
    compressor_state_bin,
    p51_boundaries,
)

ROOT = Path(__file__).resolve().parents[1]
REG = ROOT / "registry" / "b05_p51_s2125_recovery_tail_state_model.csv"
QUESTIONS = ROOT / "registry" / "open_questions.csv"
AUDIT = ROOT / "registry" / "project_blocker_evidence_audit.csv"
VARIABLES = ROOT / "registry" / "heat_pump_variables.csv"
READINESS = ROOT / "registry" / "heat_pump_readiness.csv"
MODULES = ROOT / "registry" / "module_status.csv"
PACK = ROOT / "docs" / "source_packs" / "B05_P51_S2125_RECOVERY_TAIL_STATE_MODEL.md"

def rows(path):
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))

class B05P51S2125RecoveryTailStateModelTests(unittest.TestCase):
    def test_state_bins_are_explicit(self):
        self.assertEqual("LE_30", compressor_state_bin(30.0))
        self.assertEqual("GT30_LE40", compressor_state_bin(30.1))
        self.assertEqual("GT40_LE50", compressor_state_bin(45.0))
        self.assertEqual("GT50", compressor_state_bin(50.1))

    def test_full_cycle_constant_is_not_admitted(self):
        self.assertFalse(can_admit_full_cycle_constant())
        self.assertIn("ACTIVE_STATE_UPLIFT != FULL_CYCLE_PENALTY", p51_boundaries())
        self.assertIn("STATE_BIN_SURFACE != CONTINUOUS_PREDICTIVE_FORMULA", p51_boundaries())

    def test_complete_case_recovery_trajectory_is_pinned(self):
        r = {row["claim"]: row for row in rows(REG)}
        self.assertEqual("48", r["RECOVERY_TAIL_CLEAN_COMPLETE_CASE"]["value"])
        self.assertEqual("0.343058080", r["RECOVERY_H45_ELECTRIC"]["value"])
        self.assertEqual("-0.128300271", r["RECOVERY_H45_THERMAL_SHORTFALL"]["value"])
        self.assertEqual("0.212086623", r["PAIRED_45MIN_TAIL_ELECTRIC_INCREMENT"]["value"])

    def test_censoring_is_explicit(self):
        r = {row["claim"]: row for row in rows(REG)}
        self.assertEqual("30", r["SUSTAINED_RECOVERY_SUBSET"]["value"])
        self.assertEqual("236", r["CENSORING_SEVERITY"]["value"])
        self.assertEqual("33.5", r["SUSTAINED_RECOVERY_TIME_MEDIAN"]["value"])
        self.assertIn("RIGHT_CENSORING_REQUIRED", r["SUSTAINED_RECOVERY_SUBSET"]["residual_gap"])

    def test_state_surface_is_descriptive_not_predictive(self):
        r = {row["claim"]: row for row in rows(REG)}
        self.assertEqual("0.138917334", r["STATE_SURFACE_LE30"]["value"])
        self.assertEqual("0.001314091", r["STATE_SURFACE_GT50"]["value"])
        self.assertEqual("NOT_ADMITTED", r["CONTINUOUS_PREDICTIVE_FORMULA"]["status"])
        self.assertEqual("9", r["CONTINUOUS_PREDICTIVE_FORMULA"]["value"])

    def test_q_b05_003_remains_e2_model_continue(self):
        a = {row["blocker_id"]: row for row in rows(AUDIT)}["Q-B05-003"]
        self.assertEqual("E2", a["evidence_tier"])
        self.assertEqual("VALIDATION_BLOCKER", a["blocker_class"])
        self.assertEqual("no", a["model_blocker"])
        self.assertEqual("MODEL_CONTINUE", a["canonical_use"])
        self.assertIn("RECOVERY_TAIL_CENSORING_AND_FULL_CYCLE_PARAMETER_ADMISSION_REQUIRED", a["validation_debt"])

    def test_new_variables_are_bounded_der(self):
        v = {row["variable_id"]: row for row in rows(VARIABLES)}
        self.assertEqual("DER", v["VAR-B05-S2125-P51-RECOVERY-45MIN-TRAJECTORY"]["status"])
        self.assertEqual("DER", v["VAR-B05-S2125-P51-PREFREQ-STATE-SURFACE"]["status"])
        self.assertEqual("Q", v["VAR-B05-NIBE-DEFROST-EVENT-ENERGY"]["status"])

    def test_no_readiness_uplift(self):
        ready = {row["component_id"]: row for row in rows(READINESS)}
        self.assertGreaterEqual(int(ready["DEFROST"]["readiness_percent"]), 20)
        self.assertIn("P54 performs the deferred successor-aware recalibration", ready["DEFROST"]["notes"])
        self.assertEqual("64", {row["module_id"]: row for row in rows(MODULES)}["B05"]["readiness_percent"])

    def test_pack_preserves_censoring_and_no_formula_boundaries(self):
        text = PACK.read_text(encoding="utf-8")
        self.assertIn("CLEAN_45MIN_COMPLETE_CASE != ALL_DEFROST_EVENTS", text)
        self.assertIn("STATE_BIN_SURFACE != CONTINUOUS_PREDICTIVE_FORMULA", text)
        self.assertIn("NO_MECHANICAL_READINESS_UPLIFT", text)

if __name__ == "__main__":
    unittest.main()
