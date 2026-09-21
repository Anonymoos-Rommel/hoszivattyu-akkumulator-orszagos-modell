import csv
import unittest
from pathlib import Path

from modules.B02.keop23_uvalue_poststate import (
    AIR_TO_WATER_HP_ONLY,
    REFERENCE_ENVELOPE_RETROFIT_PLUS_AWHP,
    assess_national_post_state_u_surface,
    assess_post_state_uvalue,
    candidate_baseline_uvalue_envelope,
    load_uvalue_rows,
    reference_retrofit_constraint,
)

ROOT = Path(__file__).resolve().parents[1]
REG = ROOT / "registry" / "b02_p80_keop23_uvalue_poststate.csv"
P79 = ROOT / "registry" / "b02_p79_keop23_state.csv"
OPEN_Q = ROOT / "registry" / "open_questions.csv"
MODULE_STATUS = ROOT / "registry" / "module_status.csv"
DOC = ROOT / "docs" / "source_packs" / "B02_P80_KEOP23_UVALUE_POSTSTATE.md"


def rows(path, key):
    with path.open(encoding="utf-8", newline="") as handle:
        return {row[key]: row for row in csv.DictReader(handle)}


class B02P80Keop23UValuePostStateTests(unittest.TestCase):
    def test_table_8_3_matrix_has_exact_type_domain(self):
        data = load_uvalue_rows()
        self.assertEqual(set(data), set(range(1, 24)))
        self.assertAlmostEqual(
            data[1].values["external_wall_u_uninsulated"],
            1.12,
        )
        self.assertAlmostEqual(
            data[23].values["window_u_not_replaced"],
            1.40,
        )

    def test_source_zero_is_preserved_raw_but_not_promoted(self):
        data = load_uvalue_rows()
        self.assertEqual(
            data[2].values["pitched_roof_u_uninsulated"],
            0.0,
        )
        env = candidate_baseline_uvalue_envelope(
            "Y_LT1919",
            "FAMILY_HOUSE",
            "PITCHED_ROOF",
        )
        self.assertNotEqual(env.lower_u_w_m2k, 0.0)
        self.assertIn(2, env.invalid_or_missing_type_ids)

    def test_recent_family_external_wall_baseline_set_is_exact(self):
        env = candidate_baseline_uvalue_envelope(
            "Y_GE2011",
            "FAMILY_HOUSE",
            "EXTERNAL_WALL",
        )
        self.assertEqual(env.candidate_type_count, 2)
        self.assertEqual(env.valid_type_count, 2)
        self.assertAlmostEqual(env.lower_u_w_m2k, 0.29)
        self.assertAlmostEqual(env.upper_u_w_m2k, 0.36)
        self.assertEqual(
            env.status,
            "QUALIFIED_SET_VALUED_BASELINE_CALIBRATION",
        )

    def test_table_9_1_reference_retrofit_targets(self):
        expected = {
            "EXTERNAL_WALL": 0.24,
            "FLAT_ROOF": 0.17,
            "ATTIC_FLOOR": 0.17,
            "BASEMENT_CEILING": 0.26,
            "WINDOW": 1.15,
        }
        for component, upper in expected.items():
            out = reference_retrofit_constraint(
                component,
                action=REFERENCE_ENVELOPE_RETROFIT_PLUS_AWHP,
            )
            self.assertEqual(
                out.status,
                "QUALIFIED_SOURCE_NATIVE_REFERENCE_RETROFIT_UPPER_BOUND",
            )
            self.assertIsNone(out.lower_u_w_m2k)
            self.assertEqual(out.upper_u_w_m2k, upper)

    def test_pitched_roof_does_not_inherit_unstated_table_row(self):
        out = reference_retrofit_constraint(
            "PITCHED_ROOF",
            action=REFERENCE_ENVELOPE_RETROFIT_PLUS_AWHP,
        )
        self.assertEqual(out.status, "Q")
        self.assertIn(
            "TABLE_9_1_HAS_NO_EXPLICIT_PITCHED_ROOF_ROW",
            out.blockers,
        )

    def test_heat_pump_only_does_not_mint_current_baseline(self):
        out = assess_post_state_uvalue(
            action=AIR_TO_WATER_HP_ONLY,
            component="EXTERNAL_WALL",
        )
        self.assertEqual(out.status, "Q")
        self.assertIn(
            "HEAT_PUMP_ONLY_PRESERVES_ENVELOPE_BUT_CURRENT_2026_BASELINE_U_SURFACE_IS_NOT_MATERIALIZED",
            out.blockers,
        )

    def test_national_surface_still_requires_action_baseline_and_area(self):
        status, blockers = assess_national_post_state_u_surface(
            national_action_assignment_materialized=False,
            current_no_action_baseline_materialized=False,
            component_area_surface_materialized=False,
        )
        self.assertEqual(status, "Q")
        self.assertEqual(
            blockers,
            (
                "NATIONAL_ENVELOPE_ACTION_ASSIGNMENT_REQUIRED",
                "CURRENT_NO_ACTION_BASELINE_U_SURFACE_REQUIRED",
                "COMPONENT_AREA_GEOMETRY_SURFACE_REQUIRED",
            ),
        )

    def test_registry_narrows_uvalue_blocker(self):
        reg = rows(REG, "item_id")
        self.assertEqual(
            reg["B02-P80-U11"]["status"],
            "PARTIAL_RESOLVED_ACTION_CONDITIONED",
        )
        self.assertEqual(
            reg["B02-P80-U03"]["upper_bound"],
            "0.24",
        )
        self.assertIn(
            "NATIONAL_ENVELOPE_ACTION_ASSIGNMENT_REQUIRED",
            reg["B02-P80-U12"]["residual_gap"],
        )

    def test_p79_current_state_is_superseded_not_erased(self):
        p79 = rows(P79, "item_id")
        self.assertEqual(
            p79["B02-P79-S10"]["status"],
            "SUPERSEDED_BY_P80_CURRENT_STATE",
        )

    def test_q_and_readiness_remain_fail_closed(self):
        q = rows(OPEN_Q, "question_id")["Q-B02-004"]
        self.assertEqual(q["status"], "OPEN")
        self.assertIn("B02-P80", q["notes"])
        self.assertIn("CURRENT_NO_ACTION_BASELINE_U_SURFACE_REQUIRED", q["notes"])
        self.assertIn("NATIONAL_ENVELOPE_ACTION_ASSIGNMENT_REQUIRED", q["notes"])

        b02 = rows(MODULE_STATUS, "module_id")["B02"]
        self.assertEqual(b02["readiness_percent"], "55")
        self.assertIn("B02-P80", b02["gate_note"])

    def test_source_pack_preserves_core_boundaries(self):
        text = DOC.read_text(encoding="utf-8")
        for phrase in (
            "TABLE 8.3 HISTORICAL BASELINE != 2026 CURRENT STOCK OBSERVATION",
            "SOURCE ZERO / N-A != PHYSICAL ZERO",
            "REFERENCE RETROFIT U-MAX != REALIZED U-VALUE POINT",
            "ACTION-CONDITIONED MODEL STATE != NATIONAL ACTION ASSIGNMENT",
        ):
            self.assertIn(phrase, text)


if __name__ == "__main__":
    unittest.main()
