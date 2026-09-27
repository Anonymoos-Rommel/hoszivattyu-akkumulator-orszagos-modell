import csv
import unittest
from pathlib import Path

from modules.B05.s2125_dhw_defrost_branch import (
    MATCHED_DHW_EVENTS,
    STRICT_DHW_COUNTER_CENSORED_OR_NOT_RECOVERED_EVENTS,
    STRICT_DHW_COUNTER_EVENT_DELTA_MEDIAN_KWH,
    STRICT_DHW_COUNTER_RECOVERED_EVENTS,
    STRICT_DHW_COUNTER_RECOVERY_MEDIAN_CI95_MIN,
    STRICT_DHW_COUNTER_RECOVERY_MEDIAN_MIN,
    STRICT_DHW_COUNTER_SHORTFALL_MEDIAN_CI95,
    STRICT_DHW_COUNTER_SHORTFALL_MEDIAN_KWH,
    STRICT_DHW_COUNTER_CONTROL_DELTA_MEDIAN_KWH,
    STRICT_DHW_ELECTRIC_DELTA_MEDIAN_CI95,
    STRICT_DHW_ELECTRIC_DELTA_MEDIAN_KWH,
    STRICT_DHW_EVENTS,
    STRICT_DHW_QN10_DIVERTED_EVENTS,
    STRICT_DHW_QN10_RETAINED_EVENTS,
    can_admit_universal_dhw_defrost_constant,
    can_transfer_p50_heat_signed_thermal_factor_to_dhw,
    p53_boundaries,
)

ROOT = Path(__file__).resolve().parents[1]
REG = ROOT / "registry" / "b05_p53_s2125_dhw_defrost_branch.csv"
QUESTIONS = ROOT / "registry" / "open_questions.csv"
AUDIT = ROOT / "registry" / "project_blocker_evidence_audit.csv"
READINESS = ROOT / "registry" / "heat_pump_readiness.csv"
MODULES = ROOT / "registry" / "module_status.csv"
PACK = ROOT / "docs" / "source_packs" / "B05_P53_S2125_DHW_DEFROST_BRANCH.md"


def rows(path):
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


class B05P53S2125DHWDefrostBranchTests(unittest.TestCase):
    def test_primary_and_reproduction_counts_are_frozen(self):
        self.assertEqual(46, MATCHED_DHW_EVENTS)
        self.assertEqual(35, STRICT_DHW_EVENTS)
        self.assertAlmostEqual(-0.0198199906391567, STRICT_DHW_ELECTRIC_DELTA_MEDIAN_KWH)
        self.assertEqual(
            (-0.0585694121214747, -0.0053369687204228),
            STRICT_DHW_ELECTRIC_DELTA_MEDIAN_CI95,
        )

    def test_dhw_route_switch_is_explicit(self):
        self.assertEqual(32, STRICT_DHW_QN10_DIVERTED_EVENTS)
        self.assertEqual(3, STRICT_DHW_QN10_RETAINED_EVENTS)
        self.assertIn(
            "PRE_DEFROST_DHW_STATE != DHW_THERMAL_PATH_DURING_ACTIVE_DEFROST",
            p53_boundaries(),
        )

    def test_source_native_counter_is_positive_domain_only(self):
        self.assertAlmostEqual(0.5, STRICT_DHW_COUNTER_EVENT_DELTA_MEDIAN_KWH)
        self.assertAlmostEqual(
            0.8000000000001819,
            STRICT_DHW_COUNTER_CONTROL_DELTA_MEDIAN_KWH,
        )
        self.assertAlmostEqual(
            0.20000000000027285,
            STRICT_DHW_COUNTER_SHORTFALL_MEDIAN_KWH,
        )
        self.assertEqual(
            (0.20000000000027285, 0.3999999999996362),
            STRICT_DHW_COUNTER_SHORTFALL_MEDIAN_CI95,
        )
        self.assertIn(
            "SOURCE_NATIVE_DHW_ENERGY_REGISTER_DELTA != SIGNED_THERMAL_METER",
            p53_boundaries(),
        )

    def test_counter_recovery_remains_censored(self):
        self.assertEqual(26, STRICT_DHW_COUNTER_RECOVERED_EVENTS)
        self.assertEqual(9, STRICT_DHW_COUNTER_CENSORED_OR_NOT_RECOVERED_EVENTS)
        self.assertEqual(14.5, STRICT_DHW_COUNTER_RECOVERY_MEDIAN_MIN)
        self.assertEqual((8.5, 17.5), STRICT_DHW_COUNTER_RECOVERY_MEDIAN_CI95_MIN)

    def test_universal_and_signed_thermal_constants_remain_forbidden(self):
        self.assertFalse(can_admit_universal_dhw_defrost_constant())
        self.assertFalse(can_transfer_p50_heat_signed_thermal_factor_to_dhw())
        self.assertIn(
            "DHW_ACTIVE_STATE_ELECTRIC_DELTA != FULL_CYCLE_DHW_ELECTRIC_PENALTY",
            p53_boundaries(),
        )

    def test_registry_narrows_dhw_residual_without_closing_q_b05_003(self):
        r = {row["claim"]: row for row in rows(REG)}
        self.assertEqual("35", r["STRICT_DHW_PRIMARY"]["value"])
        self.assertEqual(
            "NOT_ADMITTED",
            r["DHW_SIGNED_THERMAL_DER"]["status"],
        )
        self.assertNotIn(
            "DHW_DEFROST_BRANCH_REQUIRED",
            r["Q_B05_003_STATE"]["residual_gap"],
        )

        q = {row["question_id"]: row for row in rows(QUESTIONS)}["Q-B05-003"]
        self.assertEqual("OPEN", q["status"])
        self.assertIn("B05-P53", q["notes"])
        self.assertNotIn(
            "DHW_DEFROST_BRANCH_REQUIRED +",
            q["notes"].split("B05-P53")[-1],
        )

        audit = {row["blocker_id"]: row for row in rows(AUDIT)}["Q-B05-003"]
        self.assertEqual("E2", audit["evidence_tier"])
        self.assertNotIn("DHW_DEFROST_BRANCH_REQUIRED", audit["validation_debt"])

    def test_no_mechanical_readiness_uplift(self):
        ready = {row["component_id"]: row for row in rows(READINESS)}
        self.assertEqual("20", ready["DEFROST"]["readiness_percent"])
        modules = {row["module_id"]: row for row in rows(MODULES)}
        self.assertEqual("64", modules["B05"]["readiness_percent"])

    def test_source_pack_preserves_raw_governance(self):
        text = PACK.read_text(encoding="utf-8").lower()
        self.assertIn("external_only", text)
        self.assertNotIn("swisstransfer.com", text)


if __name__ == "__main__":
    unittest.main()
