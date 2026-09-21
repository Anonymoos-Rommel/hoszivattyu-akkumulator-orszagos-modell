import csv
import json
import unittest
from pathlib import Path

from modules.B02.keop23_wbl_crosswalk import (
    EXPECTED_OCCUPIED,
    EXPECTED_TYPE_COUNT,
    EXPECTED_WBL_ROWS,
    as_log_dict,
    assess_geometry_use,
    build_crosswalk_summary,
    candidates_for,
    load_rules,
    load_types,
)

ROOT = Path(__file__).resolve().parents[1]
STATE = ROOT / "registry" / "b02_p79_keop23_state.csv"
P78 = ROOT / "registry" / "b02_p78_national_design_load_input_coverage.csv"
OPEN_Q = ROOT / "registry" / "open_questions.csv"
MODULE_STATUS = ROOT / "registry" / "module_status.csv"
DOC = ROOT / "docs" / "source_packs" / "B02_P79_KEOP23_WBL_SET_CROSSWALK.md"


def rows(path, key):
    with path.open(encoding="utf-8", newline="") as handle:
        return {row[key]: row for row in csv.DictReader(handle)}


class B02P79Keop23CrosswalkTests(unittest.TestCase):
    def test_all_23_source_types_and_exact_geometry_examples(self):
        types = load_types()
        self.assertEqual(len(types), EXPECTED_TYPE_COUNT)
        self.assertEqual(set(types), set(range(1, 24)))
        self.assertEqual(types[1].heated_floor_area_m2, 69.9)
        self.assertEqual(types[6].heated_floor_area_m2, 150.1)
        self.assertEqual(types[12].heated_floor_area_m2, 233.8)
        self.assertEqual(types[20].dwelling_count_model, 76)
        self.assertEqual(types[20].heated_floor_area_m2, 5513.5)
        self.assertAlmostEqual(
            types[23].heated_floor_area_per_dwelling_m2,
            2963.1 / 49,
            places=9,
        )

    def test_crosswalk_covers_every_period_group_state(self):
        rules = load_rules()
        self.assertEqual(len(rules), 14)
        self.assertEqual(candidates_for("Y1946-1960", "FAMILY_HOUSE").candidate_type_ids, (4, 5, 6))
        self.assertEqual(candidates_for("Y1961-1980", "MULTI_DWELLING").candidate_type_ids, (14, 18, 19, 20, 21))
        self.assertEqual(candidates_for("Y_GE2011", "FAMILY_HOUSE").candidate_type_ids, (11, 12))
        self.assertEqual(candidates_for("Y_GE2011", "MULTI_DWELLING").candidate_type_ids, (16, 23))
        self.assertTrue(all(len(rule.candidate_type_ids) >= 2 for rule in rules.values()))
        self.assertTrue(all(len(rule.candidate_type_ids) <= 5 for rule in rules.values()))

    def test_geometry_envelopes_are_source_type_mean_sets(self):
        family = candidates_for("Y1961-1980", "FAMILY_HOUSE")
        self.assertEqual(family.heated_floor_area_per_dwelling_min_m2, 84.5)
        self.assertEqual(family.heated_floor_area_per_dwelling_max_m2, 180.5)

        multi = candidates_for("Y1946-1960", "MULTI_DWELLING")
        self.assertAlmostEqual(
            multi.heated_floor_area_per_dwelling_min_m2,
            1974.2 / 36,
            places=9,
        )
        self.assertAlmostEqual(
            multi.heated_floor_area_per_dwelling_max_m2,
            466.4 / 6,
            places=9,
        )

    def test_full_p21_wbl_population_has_candidate_set_coverage(self):
        x = build_crosswalk_summary()
        self.assertEqual(x.wbl_row_count, EXPECTED_WBL_ROWS)
        self.assertEqual(x.occupied_dwellings, EXPECTED_OCCUPIED)
        self.assertTrue(x.all_period_group_states_covered)
        self.assertEqual(x.minimum_candidate_count, 2)
        self.assertEqual(x.maximum_candidate_count, 5)
        self.assertEqual(x.point_identified_period_group_states, 0)
        self.assertAlmostEqual(
            x.central_candidate_set_covered_expected,
            EXPECTED_OCCUPIED,
            places=5,
        )
        self.assertAlmostEqual(
            x.flat_candidate_set_covered_expected,
            EXPECTED_OCCUPIED,
            places=5,
        )
        self.assertAlmostEqual(
            x.central_family_expected + x.central_multi_expected,
            EXPECTED_OCCUPIED,
            places=5,
        )

    def test_geometry_use_fails_closed_beyond_calibration_set(self):
        ok = assess_geometry_use("ARCHETYPE_CALIBRATION_SET")
        self.assertEqual(ok, ("QUALIFIED_SET_VALUED_CALIBRATION", ()))

        point = assess_geometry_use("NATIONAL_POINT_TYPE_ASSIGNMENT")
        self.assertEqual(point[0], "Q")
        self.assertIn("WITHIN_SET_KEOP23_TYPE_ASSIGNMENT_NOT_IDENTIFIED", point[1])

        household = assess_geometry_use("HOUSEHOLD_HEATED_AREA_BOUND")
        self.assertEqual(household[0], "Q")
        self.assertIn("SYNTHETIC_TYPE_MEAN_IS_NOT_HOUSEHOLD_BOUND", household[1])

        component = assess_geometry_use("B06_COMPONENT_AREA_INPUT")
        self.assertEqual(component[0], "Q")
        self.assertIn("COMPONENT_AREA_GEOMETRY_SURFACE_REQUIRED", component[1])

    def test_p78_current_state_is_superseded(self):
        p78 = rows(P78, "item_id")
        self.assertEqual(
            p78["B02-P78-D15"]["status"],
            "SUPERSEDED_BY_P79_CURRENT_STATE",
        )

    def test_state_and_q_remain_fail_closed(self):
        state = rows(STATE, "item_id")
        self.assertEqual(state["B02-P79-S03"]["status"], "FULL_SET_COVERAGE")
        self.assertEqual(
            state["B02-P79-S07"]["status"],
            "PARTIAL_RESOLVED_SET_VALUED_CALIBRATION",
        )
        q = rows(OPEN_Q, "question_id")["Q-B02-004"]
        self.assertEqual(q["status"], "OPEN")
        self.assertIn("B02-P79", q["notes"])
        self.assertIn("COMPONENT_AREA_GEOMETRY_SURFACE_REQUIRED", q["notes"])
        b02 = rows(MODULE_STATUS, "module_id")["B02"]
        self.assertEqual(b02["readiness_percent"], "55")
        self.assertIn("B02-P79", b02["gate_note"])

    def test_document_preserves_semantic_boundaries(self):
        text = DOC.read_text(encoding="utf-8")
        for phrase in (
            "FULL TYPE-SOURCE COVERAGE != POINT TYPE IDENTIFICATION",
            "WBL WALL CODE != KEOP WALL TECHNOLOGY WITHOUT AN ADMITTED CODE CROSSWALK",
            "WBL DWELLING FLOOR AREA != KEOP BUILDING USEFUL FLOOR AREA",
            "CANDIDATE-TYPE MIN/MAX != WITHIN-TYPE POPULATION CONFIDENCE INTERVAL",
        ):
            self.assertIn(phrase, text)

    def test_emit_exact_summary_for_ci_audit(self):
        print("B02_P79_CROSSWALK=" + json.dumps(as_log_dict(), sort_keys=True))


if __name__ == "__main__":
    unittest.main()
