import csv
import json
import unittest
from pathlib import Path

from modules.B02.current_baseline_u_inference import (
    EXPECTED_OCCUPIED,
    NEXT_RESIDUAL,
    P101_STATUS,
    STRATUM_STATUS,
    all_stratum_current_states,
    load_table38_type_state,
    national_population_bounds,
    p101_state,
    semantic_boundaries,
    stratum_current_state,
    type_current_state,
)
from modules.B02.programme_envelope_action_selection_crosswalk import (
    REFERENCE_COMPONENT_U_MAX,
)


ROOT = Path(__file__).resolve().parents[1]
TYPE_DATA = (
    ROOT / "data" / "processed" / "b02"
    / "p101_rekk_table38_type_state_2022.csv"
)
STRATUM_DATA = (
    ROOT / "data" / "processed" / "b02"
    / "p101_current_baseline_u_stratum_surface.csv"
)
NATIONAL_DATA = (
    ROOT / "data" / "processed" / "b02"
    / "p101_national_action_bounds.csv"
)
REG = (
    ROOT / "registry"
    / "b02_p101_current_baseline_u_inference.csv"
)
SOURCES = ROOT / "registry" / "sources.csv"
QUESTIONS = ROOT / "registry" / "open_questions.csv"
MODULES = ROOT / "registry" / "module_status.csv"
READINESS = ROOT / "registry" / "retrofit_readiness.csv"
DOC = (
    ROOT / "docs" / "source_packs"
    / "B02_P101_CURRENT_BASELINE_U_INFERENCE.md"
)


def rows(path, key=None):
    with path.open(encoding="utf-8", newline="") as handle:
        data = list(csv.DictReader(handle))
    if key is None:
        return data
    return {row[key]: row for row in data}


class B02P101CurrentBaselineUInferenceTests(unittest.TestCase):
    def test_table38_type_surface_is_exact_and_complete(self):
        data = load_table38_type_state()
        self.assertEqual(len(data), 23)
        self.assertEqual(set(data), set(range(1, 24)))
        self.assertEqual(data[1], (0.069, 0.177, 0.273))
        self.assertEqual(data[10], (0.897, 0.814, 1.000))
        self.assertEqual(data[17], (0.234, 0.031, 0.188))
        self.assertEqual(data[23], (0.894, 0.195, 1.000))

        materialized = rows(TYPE_DATA, "type_id")
        self.assertEqual(len(materialized), 23)
        self.assertEqual(
            materialized["1"]["source_id"],
            "SRC-B02-HU-REKK-TARKI-ENVELOPE-2022",
        )

    def test_uninsulated_wall_and_not_replaced_window_calibrations_exceed_targets(self):
        wall_target = REFERENCE_COMPONENT_U_MAX["EXTERNAL_WALL"]
        window_target = REFERENCE_COMPONENT_U_MAX["WINDOW"]
        states = [type_current_state(i) for i in range(1, 24)]
        self.assertTrue(
            all(state.wall_uninsulated_u_w_m2k > wall_target for state in states)
        )
        self.assertTrue(
            all(
                state.window_not_replaced_u_w_m2k > window_target
                for state in states
            )
        )

    def test_type_level_union_floor_is_overlap_safe(self):
        t1 = type_current_state(1)
        self.assertAlmostEqual(t1.wall_baseline_deficit_share, 0.931)
        self.assertAlmostEqual(t1.window_baseline_deficit_share, 0.727)
        self.assertAlmostEqual(t1.calibrated_deficit_union_lower_share, 0.931)
        self.assertAlmostEqual(t1.calibrated_deficit_union_upper_share, 1.0)

        t10 = type_current_state(10)
        self.assertAlmostEqual(t10.wall_baseline_deficit_share, 0.103)
        self.assertAlmostEqual(t10.window_baseline_deficit_share, 0.0)
        self.assertAlmostEqual(t10.calibrated_deficit_union_lower_share, 0.103)
        self.assertAlmostEqual(t10.calibrated_deficit_union_upper_share, 0.103)

        t17 = type_current_state(17)
        self.assertAlmostEqual(t17.calibrated_deficit_union_lower_share, 0.812)

    def test_fourteen_stratum_set_surface_matches_materialized_csv(self):
        runtime = {
            (row.wbl_period_code, row.building_group): row
            for row in all_stratum_current_states()
        }
        materialized = {
            (row["wbl_period_code"], row["building_group"]): row
            for row in rows(STRATUM_DATA)
        }
        self.assertEqual(len(runtime), 14)
        self.assertEqual(set(runtime), set(materialized))

        for key, state in runtime.items():
            row = materialized[key]
            self.assertEqual(state.status, STRATUM_STATUS)
            self.assertEqual(
                ";".join(str(x) for x in state.candidate_type_ids),
                row["candidate_type_ids"],
            )
            self.assertAlmostEqual(
                state.calibrated_deficit_floor_lower_share,
                float(row["calibrated_deficit_floor_lower_share"]),
            )
            self.assertAlmostEqual(
                state.calibrated_deficit_floor_upper_share,
                float(row["calibrated_deficit_floor_upper_share"]),
            )
            self.assertEqual(state.residual, NEXT_RESIDUAL)

        old_family = stratum_current_state("Y_LT1919", "FAMILY_HOUSE")
        self.assertAlmostEqual(old_family.calibrated_deficit_floor_lower_share, 0.777)
        self.assertAlmostEqual(old_family.calibrated_deficit_floor_upper_share, 0.931)

        new_family = stratum_current_state("Y_GE2011", "FAMILY_HOUSE")
        self.assertAlmostEqual(new_family.calibrated_deficit_floor_lower_share, 0.103)
        self.assertAlmostEqual(new_family.calibrated_deficit_floor_upper_share, 0.298)

    def test_p21_weighted_national_bounds_are_executable_and_fail_closed(self):
        scenarios = national_population_bounds()
        self.assertEqual({row.scenario for row in scenarios}, {"CENTRAL", "FLAT"})
        for row in scenarios:
            self.assertAlmostEqual(row.occupied_dwellings, EXPECTED_OCCUPIED)
            self.assertGreater(row.calibrated_retrofit_floor_lower_share, 0.0)
            self.assertLess(row.calibrated_retrofit_floor_lower_share, 1.0)
            self.assertGreaterEqual(
                row.calibrated_retrofit_floor_upper_share,
                row.calibrated_retrofit_floor_lower_share,
            )
            self.assertLessEqual(row.calibrated_retrofit_floor_upper_share, 1.0)
            self.assertEqual(row.hp_only_share_lower, 0.0)
            self.assertAlmostEqual(
                row.hp_only_share_upper,
                1.0 - row.calibrated_retrofit_floor_lower_share,
            )
            self.assertEqual(row.residual, NEXT_RESIDUAL)

        by_scenario = {row.scenario: row for row in scenarios}
        self.assertAlmostEqual(
            by_scenario["CENTRAL"].calibrated_retrofit_floor_lower_share,
            0.37828554686480326,
        )
        self.assertAlmostEqual(
            by_scenario["CENTRAL"].calibrated_retrofit_floor_upper_share,
            0.6337975082239213,
        )
        self.assertAlmostEqual(
            by_scenario["FLAT"].calibrated_retrofit_floor_lower_share,
            0.37781217722501986,
        )
        self.assertAlmostEqual(
            by_scenario["FLAT"].calibrated_retrofit_floor_upper_share,
            0.6314763486127777,
        )

        materialized = rows(NATIONAL_DATA, "scenario")
        self.assertEqual(set(materialized), {"CENTRAL", "FLAT", "STRUCTURAL_ENVELOPE"})
        for scenario in ("CENTRAL", "FLAT"):
            runtime = by_scenario[scenario]
            data = materialized[scenario]
            self.assertAlmostEqual(
                runtime.calibrated_retrofit_floor_lower_share,
                float(data["calibrated_retrofit_floor_lower_share"]),
            )
            self.assertAlmostEqual(
                runtime.calibrated_retrofit_floor_upper_share,
                float(data["calibrated_retrofit_floor_upper_share"]),
            )
            self.assertAlmostEqual(
                runtime.hp_only_share_upper,
                float(data["hp_only_share_upper"]),
            )

        state = p101_state()
        self.assertEqual(state["status"], P101_STATUS)
        self.assertIsNone(state["current_baseline_u_inference_blocker"])
        self.assertFalse(state["national_point_action_share_identified"])
        self.assertEqual(state["hp_only_share_lower"], 0.0)
        self.assertAlmostEqual(
            state["structural_calibrated_retrofit_floor_lower_share"],
            0.37781217722501986,
        )
        self.assertAlmostEqual(
            state["structural_calibrated_retrofit_floor_upper_share"],
            0.6337975082239213,
        )
        self.assertAlmostEqual(
            state["hp_only_share_upper"],
            0.6221878227749802,
        )
        self.assertEqual(state["residual"], NEXT_RESIDUAL)

        print(
            "B02_P101_STATE="
            + json.dumps(state, sort_keys=True, separators=(",", ":"))
        )

    def test_registry_source_and_project_state_are_narrowed(self):
        reg = rows(REG, "item_id")
        self.assertEqual(
            reg["B02-P101-U04"]["status"],
            "RESOLVED_BOUNDED_CALIBRATED_INFERENCE",
        )
        self.assertAlmostEqual(
            float(reg["B02-P101-U05"]["lower_bound"]),
            0.37781217722501986,
        )
        self.assertAlmostEqual(
            float(reg["B02-P101-U05"]["upper_bound"]),
            0.6337975082239213,
        )
        self.assertEqual(
            reg["B02-P101-U06"]["status"],
            "BOUNDED_UPPER_ONLY",
        )
        self.assertAlmostEqual(
            float(reg["B02-P101-U06"]["upper_bound"]),
            0.6221878227749802,
        )
        self.assertEqual(
            reg["B02-P101-U06"]["residual_gap"],
            NEXT_RESIDUAL,
        )

        sources = rows(SOURCES, "source_id")
        note = sources["SRC-B02-HU-REKK-TARKI-ENVELOPE-2022"]["notes"]
        self.assertIn("Table 38", note)
        self.assertIn("23 type", note)
        self.assertIn("type-level weighted averages", note)

        q = rows(QUESTIONS, "question_id")["Q-B02-004"]
        self.assertEqual(q["status"], "OPEN")
        self.assertIn("B02-P101", q["notes"])
        self.assertIn("RESOLVED_BOUNDED_CALIBRATED_INFERENCE", q["notes"])
        self.assertIn(NEXT_RESIDUAL, q["notes"])

        module = rows(MODULES, "module_id")["B02"]
        self.assertEqual(module["readiness_percent"], "55")
        self.assertIn("B02-P101", module["gate_note"])

        peak = rows(READINESS, "component_id")["PEAK_LOAD_EFFECT"]
        self.assertEqual(peak["readiness_percent"], "50")
        self.assertIn("B02-P101", peak["notes"])

    def test_semantic_boundaries_and_document_are_frozen(self):
        boundary = semantic_boundaries()
        for item in (
            "TARKI_TYPE_WEIGHTED_SHARE_IS_NOT_HOUSEHOLD_STATE",
            "P80_SYNTHETIC_TYPE_MEAN_U_IS_NOT_HOUSEHOLD_U",
            "CALIBRATED_DEFICIT_FLOOR_IS_NOT_OBSERVED_HOUSEHOLD_FAIL_SHARE",
            "INSULATED_OR_REPLACED_IS_NOT_REFERENCE_U_COMPLIANCE",
            "2022_CURRENT_STATE_CALIBRATION_IS_NOT_2026_POINT_STATE",
            "HP_ONLY_LOWER_BOUND_REMAINS_ZERO_WITHOUT_RENOVATED_U_QUALITY",
        ):
            self.assertIn(item, boundary)

        text = DOC.read_text(encoding="utf-8")
        for phrase in (
            "23-type",
            "type-level weighted averages",
            "CALIBRATED DEFICIT FLOOR != OBSERVED HOUSEHOLD FAIL SHARE",
            "HP_ONLY lower bound remains 0",
            "37.7812177225%",
            "62.2187822775%",
            NEXT_RESIDUAL,
            "**B02 remains 55%**",
        ):
            self.assertIn(phrase, text)


if __name__ == "__main__":
    unittest.main()
