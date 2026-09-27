import csv
import unittest
from pathlib import Path

from modules.B05.s2125_matched_defrost_penalty import (
    MatchAdmission,
    classify_pre_mode,
    direct_electric_uplift_kwh,
    p50_boundaries,
    signed_thermal_power_kw,
    thermal_service_shortfall_kwh,
)

ROOT = Path(__file__).resolve().parents[1]
REG = ROOT / "registry" / "b05_p50_s2125_matched_defrost_penalty.csv"
QUESTIONS = ROOT / "registry" / "open_questions.csv"
AUDIT = ROOT / "registry" / "project_blocker_evidence_audit.csv"
VARIABLES = ROOT / "registry" / "heat_pump_variables.csv"
READINESS = ROOT / "registry" / "heat_pump_readiness.csv"
MODULES = ROOT / "registry" / "module_status.csv"
PACK = ROOT / "docs" / "source_packs" / "B05_P50_S2125_MATCHED_DEFROST_PENALTY.md"

def rows(path):
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))

class B05P50S2125MatchedDefrostPenaltyTests(unittest.TestCase):
    def test_mode_separation_is_fail_closed(self):
        self.assertEqual("HEAT", classify_pre_mode(0.0))
        self.assertEqual("DHW", classify_pre_mode(1.0))
        self.assertEqual("TRANSITION", classify_pre_mode(0.4))

    def test_signed_thermal_der_preserves_reverse_sign(self):
        self.assertLess(signed_thermal_power_kw(10.0, 30.0, 35.0), 0.0)
        self.assertGreater(signed_thermal_power_kw(10.0, 35.0, 30.0), 0.0)

    def test_match_admission_requires_three_controls_and_coverage(self):
        self.assertTrue(MatchAdmission("HEAT", 3, 0.98, False, True).admitted())
        self.assertFalse(MatchAdmission("HEAT", 2, 1.0, False, True).admitted())
        self.assertFalse(MatchAdmission("HEAT", 5, 0.97, False, True).admitted())
        self.assertFalse(MatchAdmission("TRANSITION", 5, 1.0, False, True).admitted())

    def test_penalty_identities_remain_signed(self):
        self.assertAlmostEqual(0.1, direct_electric_uplift_kwh(0.3, 0.2))
        self.assertAlmostEqual(-0.1, direct_electric_uplift_kwh(0.2, 0.3))
        self.assertAlmostEqual(0.8, thermal_service_shortfall_kwh(0.5, -0.3))

    def test_registry_primary_values(self):
        r = {row["claim"]: row for row in rows(REG)}
        self.assertEqual("266", r["ACTIVE_DEFROST_MATCHING_PRIMARY"]["value"])
        self.assertEqual("0.118280543", r["ACTIVE_HEAT_DIRECT_ELECTRIC_UPLIFT_MEDIAN"]["value"])
        self.assertEqual("-0.260139396", r["ACTIVE_HEAT_SIGNED_THERMAL_EVENT_MEDIAN"]["value"])
        self.assertEqual("0.826803152", r["ACTIVE_HEAT_THERMAL_SERVICE_SHORTFALL_MEDIAN"]["value"])
        self.assertIn("CALL_FULL_DEFROST_PENALTY", r["ACTIVE_HEAT_DIRECT_ELECTRIC_UPLIFT_MEDIAN"]["forbidden_use"])

    def test_q_b05_003_remains_e2_model_continue(self):
        a = {row["blocker_id"]: row for row in rows(AUDIT)}["Q-B05-003"]
        self.assertEqual("E2", a["evidence_tier"])
        self.assertEqual("VALIDATION_BLOCKER", a["blocker_class"])
        self.assertEqual("no", a["model_blocker"])
        self.assertEqual("MODEL_CONTINUE", a["canonical_use"])
        self.assertTrue(
            "POST_DEFROST_RECOVERY_TAIL_REQUIRED" in a["validation_debt"]
            or "RECOVERY_TAIL_CENSORING_AND_FULL_CYCLE_PARAMETER_ADMISSION_REQUIRED" in a["validation_debt"]
        )

    def test_generic_event_energy_stays_q_while_p50_der_is_bounded(self):
        v = {row["variable_id"]: row for row in rows(VARIABLES)}
        self.assertEqual("Q", v["VAR-B05-NIBE-DEFROST-EVENT-ENERGY"]["status"])
        self.assertEqual("DER", v["VAR-B05-S2125-P50-ACTIVE-HEAT-ELECTRIC-UPLIFT"]["status"])
        self.assertEqual("DER", v["VAR-B05-S2125-P50-ACTIVE-HEAT-THERMAL-SHORTFALL"]["status"])

    def test_no_mechanical_readiness_uplift(self):
        ready = {row["component_id"]: row for row in rows(READINESS)}
        self.assertEqual("20", ready["DEFROST"]["readiness_percent"])
        self.assertEqual("64", {row["module_id"]: row for row in rows(MODULES)}["B05"]["readiness_percent"])
        self.assertIn("NO_MECHANICAL_READINESS_UPLIFT", p50_boundaries())

    def test_pack_preserves_full_cycle_boundary(self):
        text = PACK.read_text(encoding="utf-8")
        self.assertIn("ACTIVE_STATE_DIRECT_ELECTRIC_UPLIFT != FULL_DEFROST_CYCLE_PENALTY", text)
        self.assertIn("POST_DEFROST_RECOVERY_TAIL_REQUIRED", text)
        self.assertIn("HEAT_DEFROST != DHW_DEFROST", text)

if __name__ == "__main__":
    unittest.main()
