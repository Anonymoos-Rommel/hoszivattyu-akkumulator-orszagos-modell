import csv
import unittest
from pathlib import Path

from modules.B02.official_type_weighted_envelope_calibration import (
    EXPECTED_BTR_FAMILY_TOTAL,
    EXPECTED_BTR_MULTI_TOTAL,
    EXPECTED_BTR_TOTAL,
    EXPECTED_CANONICAL_OCCUPIED,
    EXPECTED_P21_FAMILY,
    EXPECTED_P21_MULTI,
    PRIMARY_NEXT_RESIDUAL,
    PROBLEM_TYPE_IDS,
    group_calibrations,
    load_btr_type_weights,
    national_calibration,
    p115_state,
    problematic_type_surface,
    semantic_boundaries,
)

ROOT = Path(__file__).resolve().parents[1]
WEIGHTS = ROOT / "data" / "processed" / "b02" / "p115_unfccc_btr_type_weights.csv"
SUMMARY = ROOT / "data" / "processed" / "b02" / "p115_official_type_weighted_summary.csv"
REG = ROOT / "registry" / "b02_p115_official_type_weighted_envelope.csv"
SOURCES = ROOT / "registry" / "sources.csv"
QUESTIONS = ROOT / "registry" / "open_questions.csv"
MODULES = ROOT / "registry" / "module_status.csv"
READINESS = ROOT / "registry" / "retrofit_readiness.csv"
DOC = ROOT / "docs" / "source_packs" / "B02_P115_OFFICIAL_TYPE_WEIGHTED_ENVELOPE.md"


def rows(path, key=None):
    with path.open(encoding="utf-8", newline="") as h:
        data = list(csv.DictReader(h))
    return {r[key]: r for r in data} if key else data


class P115Tests(unittest.TestCase):
    def test_btr_exact_type_surface(self):
        w = load_btr_type_weights()
        self.assertEqual(set(w), set(range(1, 24)))
        family = sum(x.occupied_dwellings for x in w.values() if x.building_group == "FAMILY_HOUSE")
        multi = sum(x.occupied_dwellings for x in w.values() if x.building_group == "MULTI_DWELLING")
        self.assertEqual(family, EXPECTED_BTR_FAMILY_TOTAL)
        self.assertEqual(multi, EXPECTED_BTR_MULTI_TOTAL)
        self.assertEqual(family + multi, EXPECTED_BTR_TOTAL)
        self.assertEqual(w[11].occupied_dwellings, 44464)
        self.assertEqual(w[15].occupied_dwellings, 41607)
        self.assertEqual(w[16].occupied_dwellings, 24150)
        self.assertEqual(w[23].occupied_dwellings, 47484)

    def test_group_calibrations(self):
        g = {x.building_group: x for x in group_calibrations()}
        self.assertEqual(g["FAMILY_HOUSE"].p21_canonical_group_total, EXPECTED_P21_FAMILY)
        self.assertEqual(g["MULTI_DWELLING"].p21_canonical_group_total, EXPECTED_P21_MULTI)
        self.assertAlmostEqual(g["FAMILY_HOUSE"].calibrated_deficit_floor_share, 0.9866233682972694)
        self.assertAlmostEqual(g["FAMILY_HOUSE"].calibrated_deficit_upper_share, 0.9918444467681358)
        self.assertAlmostEqual(g["MULTI_DWELLING"].calibrated_deficit_floor_share, 0.9348630915138852)
        self.assertAlmostEqual(g["MULTI_DWELLING"].calibrated_deficit_upper_share, 0.9404304727232026)

    def test_material_national_tightening(self):
        n = national_calibration()
        self.assertEqual(n.occupied_dwellings, EXPECTED_CANONICAL_OCCUPIED)
        self.assertAlmostEqual(n.calibrated_deficit_floor_share, 0.9661518297465196)
        self.assertAlmostEqual(n.calibrated_deficit_upper_share, 0.9715098732859866)
        self.assertAlmostEqual(n.calibrated_deficit_floor_dwellings, 3872859.2217639433)
        self.assertEqual(n.hp_only_share_lower, 0.0)
        self.assertAlmostEqual(n.hp_only_share_upper, 0.033848170253480414)
        self.assertAlmostEqual(n.floor_gain, 0.1382907998018215)
        self.assertAlmostEqual(n.hp_only_upper_reduction, 0.13829079980182146)

    def test_residual_is_four_type_specific(self):
        s = p115_state()
        self.assertEqual(s["problem_type_ids"], PROBLEM_TYPE_IDS)
        self.assertEqual(s["problem_type_btr_total"], 157705)
        self.assertAlmostEqual(s["problem_type_btr_share"], 0.042312331842655704)
        self.assertEqual(s["primary_residual"], PRIMARY_NEXT_RESIDUAL)
        self.assertTrue(s["national_point_type_mix_blocker_resolved"])
        self.assertTrue(s["p115_numeric_tightening"])

        p = {x["type_id"]: x for x in problematic_type_surface()}
        self.assertAlmostEqual(p[11]["combined_floor_share"], 0.298)
        self.assertAlmostEqual(p[15]["combined_floor_share"], 0.265)
        self.assertAlmostEqual(p[16]["combined_floor_share"], 0.265)
        self.assertAlmostEqual(p[23]["combined_floor_share"], 0.106)

    def test_denominator_boundary(self):
        s = p115_state()
        self.assertFalse(s["btr_total_used_as_canonical_denominator"])
        self.assertTrue(s["within_group_source_native_type_weights_used"])
        self.assertEqual(s["canonical_occupied_total"], EXPECTED_CANONICAL_OCCUPIED)

    def test_materialized_files_and_registry(self):
        w = rows(WEIGHTS, "type_id")
        self.assertEqual(len(w), 23)
        self.assertEqual(w["23"]["btr_occupied_dwellings"], "47484")

        sm = rows(SUMMARY, "metric")
        self.assertEqual(sm["national_deficit_floor_share"]["value"], "0.9661518297465196")
        self.assertEqual(sm["hp_only_share_upper"]["value"], "0.033848170253480414")

        reg = rows(REG, "item_id")
        self.assertEqual(reg["B02-P115-U04"]["status"], "QUALIFIED_NUMERIC_TIGHTENING")
        self.assertEqual(reg["B02-P115-U06"]["residual_gap"], PRIMARY_NEXT_RESIDUAL)

        sources = rows(SOURCES, "source_id")
        self.assertIn("SRC-B02-HU-UNFCCC-BTR1-BUILDING-TYPOLOGY-2025", sources)

        q = rows(QUESTIONS, "question_id")["Q-B02-004"]
        self.assertIn("B02-P115", q["notes"])
        self.assertIn("96.6151829747%", q["notes"])

        module = rows(MODULES, "module_id")["B02"]
        self.assertEqual(module["readiness_percent"], "55")
        self.assertIn("B02-P115", module["gate_note"])

        peak = rows(READINESS, "component_id")["PEAK_LOAD_EFFECT"]
        self.assertEqual(peak["readiness_percent"], "50")
        self.assertIn("B02-P115", peak["notes"])

    def test_boundaries_and_doc(self):
        for boundary in (
            "BTR_TYPE_WEIGHT_IS_NOT_CENSUS_DWELLING_IDENTITY",
            "WITHIN_GROUP_TYPE_SHARE_IS_NOT_RAW_BTR_TOTAL_AS_CANONICAL_DENOMINATOR",
            "OFFICIAL_MODEL_WEIGHTED_CALIBRATION_IS_NOT_OBSERVED_HOUSEHOLD_FAIL_RATE",
            "NATIONAL_TYPE_MIX_IS_NOT_LOCAL_WBL_POINT_TYPE_ASSIGNMENT",
            "TYPE_11_15_16_23_RESIDUAL_IS_NOT_WHOLE_STOCK_MULTIGLAZED_UW_BLOCKER",
        ):
            self.assertIn(boundary, semantic_boundaries())

        text = DOC.read_text(encoding="utf-8")
        for phrase in (
            "96.6151829747%",
            "3.38481702535%",
            "13.8290799802 percentage points",
            "TYPES_11_15_16_23_CURRENT_ENVELOPE_POSTSTATE_REQUIRED",
        ):
            self.assertIn(phrase, text)


if __name__ == "__main__":
    unittest.main()
