import csv
import unittest
from pathlib import Path

from modules.B05.s2125_passive_defrost_branch import (
    EXPECTED_PASSIVE_MEDIAN_DURATION_S,
    EXPECTED_PASSIVE_STATE_RUNS,
    EXPECTED_PASSIVE_STATE_SAMPLES,
    PASSIVE_DHW_EVENTS_WITH_STRICT_MATCH_SUPPORT,
    PASSIVE_DHW_RUNS,
    PASSIVE_HEAT_EVENTS_WITH_STRICT_MATCH_SUPPORT,
    PASSIVE_HEAT_RUNS,
    PASSIVE_MEDIAN_ELECTRICAL_COVERAGE_PERCENT,
    PASSIVE_MEDIAN_MEASURED_COVERED_ENERGY_KWH,
    PASSIVE_MEDIAN_MEASURED_INTERVAL_POWER_W,
    PASSIVE_MIN_NEXT_COMPRESSOR_GAP_MIN,
    PASSIVE_TRANSITION_RUNS,
    PINNED_ARCHIVE_SHA256,
    PINNED_NIBE_MEMBER_SHA256,
    PINNED_VICTRON_MEMBER_SHA256,
    PassiveElectricMatchAdmission,
    can_admit_passive_penalty_constant,
    passive_branch_matched_parameter_admitted,
    passive_signed_thermal_der_admitted,
    p52_boundaries,
    raw_identity_admitted,
)

ROOT = Path(__file__).resolve().parents[1]
REG = ROOT / "registry" / "b05_p52_s2125_passive_defrost_branch.csv"
QUESTIONS = ROOT / "registry" / "open_questions.csv"
AUDIT = ROOT / "registry" / "project_blocker_evidence_audit.csv"
READINESS = ROOT / "registry" / "heat_pump_readiness.csv"
MODULES = ROOT / "registry" / "module_status.csv"
PACK = ROOT / "docs" / "source_packs" / "B05_P52_S2125_PASSIVE_DEFROST_BRANCH.md"


def rows(path):
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


class B05P52S2125PassiveDefrostBranchTests(unittest.TestCase):
    def test_exact_p49_raw_identity_is_required(self):
        self.assertTrue(
            raw_identity_admitted(
                PINNED_ARCHIVE_SHA256,
                PINNED_NIBE_MEMBER_SHA256,
                PINNED_VICTRON_MEMBER_SHA256,
            )
        )
        self.assertFalse(
            raw_identity_admitted(
                "0" * 64,
                PINNED_NIBE_MEMBER_SHA256,
                PINNED_VICTRON_MEMBER_SHA256,
            )
        )

    def test_direct_passive_population_is_frozen(self):
        self.assertEqual(102, EXPECTED_PASSIVE_STATE_SAMPLES)
        self.assertEqual(22, EXPECTED_PASSIVE_STATE_RUNS)
        self.assertEqual(180.5, EXPECTED_PASSIVE_MEDIAN_DURATION_S)
        self.assertEqual(9, PASSIVE_HEAT_RUNS)
        self.assertEqual(11, PASSIVE_DHW_RUNS)
        self.assertEqual(2, PASSIVE_TRANSITION_RUNS)
        self.assertAlmostEqual(0.004854669, PASSIVE_MEDIAN_MEASURED_COVERED_ENERGY_KWH)
        self.assertAlmostEqual(94.9480, PASSIVE_MEDIAN_ELECTRICAL_COVERAGE_PERCENT)
        self.assertAlmostEqual(80.640888, PASSIVE_MEDIAN_MEASURED_INTERVAL_POWER_W)
        self.assertEqual(14.0, PASSIVE_MIN_NEXT_COMPRESSOR_GAP_MIN)

    def test_single_match_can_pass_but_branch_parameter_stays_fail_closed(self):
        good = PassiveElectricMatchAdmission(
            mode="HEAT",
            n_controls=3,
            electrical_coverage_fraction=0.98,
            control_has_nonzero_defrost=False,
            control_compressor_off=True,
            stable_control_mode=True,
            event_is_direct_passive_state=True,
        )
        self.assertTrue(good.admitted())
        self.assertEqual(5, PASSIVE_HEAT_EVENTS_WITH_STRICT_MATCH_SUPPORT)
        self.assertEqual(0, PASSIVE_DHW_EVENTS_WITH_STRICT_MATCH_SUPPORT)
        self.assertFalse(
            passive_branch_matched_parameter_admitted(
                heat_events_supported=PASSIVE_HEAT_EVENTS_WITH_STRICT_MATCH_SUPPORT,
                heat_events_total=PASSIVE_HEAT_RUNS,
                dhw_events_supported=PASSIVE_DHW_EVENTS_WITH_STRICT_MATCH_SUPPORT,
                dhw_events_total=PASSIVE_DHW_RUNS,
            )
        )

    def test_p50_thermal_factor_is_not_auto_transferred(self):
        self.assertFalse(
            passive_signed_thermal_der_admitted(
                p50_factor_domain_validated_for_passive=False,
                flow_and_temperatures_qualified=True,
            )
        )

    def test_registry_keeps_state_window_separate_from_incremental_penalty(self):
        r = {row["claim"]: row for row in rows(REG)}
        self.assertEqual("22", r["PASSIVE_DIRECT_STATE_POPULATION"]["value"])
        self.assertEqual(
            "0.004854669",
            r["PASSIVE_MEASURED_COVERED_ELECTRIC_ENERGY"]["value"],
        )
        self.assertEqual("NOT_ADMITTED", r["PASSIVE_STRICT_MATCHED_ELECTRIC_EFFECT"]["status"])
        self.assertEqual("NOT_ADMITTED", r["PASSIVE_SIGNED_THERMAL_DER"]["status"])
        self.assertIn(
            "PASSIVE_INCREMENTAL_ELECTRIC_AND_THERMAL_DOMAIN_VALIDATION_REQUIRED",
            r["Q_B05_003_STATE"]["residual_gap"],
        )

    def test_q_b05_003_is_narrowed_not_closed(self):
        q = {row["question_id"]: row for row in rows(QUESTIONS)}["Q-B05-003"]
        self.assertEqual("OPEN", q["status"])
        self.assertIn(
            "PASSIVE_INCREMENTAL_ELECTRIC_AND_THERMAL_DOMAIN_VALIDATION_REQUIRED",
            q["notes"],
        )
        audit = {row["blocker_id"]: row for row in rows(AUDIT)}["Q-B05-003"]
        self.assertEqual("E2", audit["evidence_tier"])
        self.assertIn(
            "PASSIVE_INCREMENTAL_ELECTRIC_AND_THERMAL_DOMAIN_VALIDATION_REQUIRED",
            audit["validation_debt"],
        )

    def test_no_mechanical_readiness_uplift(self):
        ready = {row["component_id"]: row for row in rows(READINESS)}
        self.assertGreaterEqual(int(ready["DEFROST"]["readiness_percent"]), 20)
        self.assertIn("P54 performs the deferred successor-aware recalibration", ready["DEFROST"]["notes"])
        modules = {row["module_id"]: row for row in rows(MODULES)}
        self.assertEqual("64", modules["B05"]["readiness_percent"])

    def test_no_raw_or_transfer_secret_is_committed(self):
        forbidden = {
            "nibe_daten_jan_maerz_2026.tar.xz",
            "nibe_alle_daten_jan_maerz_2026.csv",
            "nibe_energie_jan_maerz_2026.csv",
        }
        committed = {p.name for p in ROOT.rglob("*") if p.is_file()}
        self.assertTrue(forbidden.isdisjoint(committed))
        text = PACK.read_text(encoding="utf-8").lower()
        self.assertNotIn("swisstransfer.com", text)
        self.assertIn("external_only", text)

    def test_boundaries_remain_fail_closed(self):
        self.assertFalse(can_admit_passive_penalty_constant())
        boundaries = p52_boundaries()
        self.assertIn("PASSIVE_DEFROST != ACTIVE_REVERSE_CYCLE_DEFROST", boundaries)
        self.assertIn(
            "ZERO_COMPRESSOR_REQUEST_DURING_PASSIVE != ZERO_BUILDING_THERMAL_COST",
            boundaries,
        )


if __name__ == "__main__":
    unittest.main()
