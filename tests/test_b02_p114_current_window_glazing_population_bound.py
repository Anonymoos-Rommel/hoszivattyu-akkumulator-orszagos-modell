import csv
import unittest
from pathlib import Path

from modules.B02.current_window_glazing_population_bound import (
    DWELLING_GRAIN_RESIDUAL,
    HU_SINGLE_GLAZING_PRESENT_SHARE,
    PRIMARY_NEXT_RESIDUAL,
    frechet_non_district_single_glazing_bound,
    p114_state,
    semantic_boundaries,
    single_glazing_is_current_glazing_deficit,
)

ROOT = Path(__file__).resolve().parents[1]
SURFACE = ROOT / "data" / "processed" / "b02" / "p114_current_window_glazing_surface.csv"
CONTRACT = ROOT / "data" / "processed" / "b02" / "p114_current_window_glazing_contract.csv"
REG = ROOT / "registry" / "b02_p114_current_window_glazing_bound.csv"
SOURCES = ROOT / "registry" / "sources.csv"
QUESTIONS = ROOT / "registry" / "open_questions.csv"
MODULES = ROOT / "registry" / "module_status.csv"
READINESS = ROOT / "registry" / "retrofit_readiness.csv"
DOC = ROOT / "docs" / "source_packs" / "B02_P114_CURRENT_WINDOW_GLAZING_BOUND.md"


def rows(path, key=None):
    with path.open(encoding="utf-8", newline="") as h:
        data = list(csv.DictReader(h))
    return {r[key]: r for r in data} if key else data


class P114Tests(unittest.TestCase):
    def test_observed_hungary_window_mix_sums_to_one(self):
        s = p114_state()
        total = (
            s["only_single_glazing_share"]
            + s["only_double_glazing_share"]
            + s["triple_or_more_glazing_share"]
            + s["mixed_single_and_multiglazing_share"]
            + s["mixed_double_and_triple_share"]
        )
        self.assertAlmostEqual(total, 1.0)
        self.assertAlmostEqual(HU_SINGLE_GLAZING_PRESENT_SHARE, 0.215)

    def test_dependence_free_non_district_bound(self):
        b = frechet_non_district_single_glazing_bound()
        self.assertAlmostEqual(b.intersection_lower, 0.061)
        self.assertAlmostEqual(b.intersection_upper, 0.215)
        self.assertAlmostEqual(b.conditional_lower, 0.061 / 0.846)
        self.assertAlmostEqual(b.conditional_upper, 0.215 / 0.846)
        self.assertGreater(b.conditional_lower, 0.072)
        self.assertLess(b.conditional_lower, 0.073)

    def test_single_glazing_deficit_is_direct(self):
        self.assertTrue(single_glazing_is_current_glazing_deficit())
        s = p114_state()
        self.assertEqual(s["current_glazing_u_requirement_w_m2k"], 1.0)
        self.assertEqual(s["official_single_glazing_reference_u_w_m2k"], 5.8)
        self.assertTrue(s["single_glazing_current_glazing_deficit_proven"])

    def test_no_multiglazed_compliance_overclaim(self):
        s = p114_state()
        self.assertFalse(s["double_glazing_current_whole_window_compliance_proven"])
        self.assertFalse(s["triple_glazing_current_whole_window_compliance_proven"])
        self.assertFalse(s["exact_hc001_x_hc004_joint_observed"])
        self.assertFalse(s["exact_b02_dwelling_count_transfer_admitted"])
        self.assertEqual(s["primary_residual"], PRIMARY_NEXT_RESIDUAL)
        self.assertEqual(s["dwelling_grain_residual"], DWELLING_GRAIN_RESIDUAL)

    def test_existing_overall_bounds_not_artificially_tightened(self):
        s = p114_state()
        self.assertAlmostEqual(
            s["p102_structural_calibrated_retrofit_floor_lower_share"],
            0.8278610299446981,
        )
        self.assertEqual(s["hp_only_share_lower"], 0.0)
        self.assertAlmostEqual(s["hp_only_share_upper"], 0.17213897005530188)
        self.assertFalse(s["p114_numeric_overall_bound_tightening"])

    def test_surface_contract_registry_and_sources(self):
        surface = rows(SURFACE, "surface_id")
        self.assertEqual(surface["B02-P114-S01"]["status"], "OBSERVED_CURRENT_HU_SURFACE")
        self.assertEqual(surface["B02-P114-S03"]["status"], "DERIVED_HARD_LOWER_BOUND")
        self.assertEqual(surface["B02-P114-S05"]["status"], "PRIMARY_NEXT_ACQUISITION")

        contract = rows(CONTRACT, "field_id")
        self.assertEqual(contract["B02-P114-C04"]["status"], "OBSERVED")
        self.assertEqual(contract["B02-P114-C08"]["status"], "REQUIRED_FOR_EXACT_B02_COUNT")

        reg = rows(REG, "item_id")
        self.assertEqual(reg["B02-P114-U01"]["status"], "OBSERVED_CURRENT_HU_SURFACE")
        self.assertEqual(reg["B02-P114-U05"]["residual_gap"], PRIMARY_NEXT_RESIDUAL)

        sources = rows(SOURCES, "source_id")
        self.assertIn("SRC-B02-EUROSTAT-SILC-2023-ENERGY-MODULE-ASSESSMENT", sources)
        self.assertIn("SRC-B02-EU-2021-2052-HC001-HC004", sources)
        self.assertIn("SRC-B02-HU-2023-EKM-CURRENT-U", sources)
        self.assertIn("SRC-B02-HU-EKM-APPENDIX2-GLAZING-U", sources)

        q = rows(QUESTIONS, "question_id")["Q-B02-004"]
        self.assertIn("B02-P114", q["notes"])
        self.assertIn(PRIMARY_NEXT_RESIDUAL, q["notes"])

        module = rows(MODULES, "module_id")["B02"]
        self.assertEqual(module["readiness_percent"], "55")
        self.assertIn("B02-P114", module["gate_note"])

        peak = rows(READINESS, "component_id")["PEAK_LOAD_EFFECT"]
        self.assertEqual(peak["readiness_percent"], "50")
        self.assertIn("B02-P114", peak["notes"])

    def test_boundaries_and_doc(self):
        for b in (
            "SINGLE_GLAZING_PRESENT_IS_NOT_WHOLE_WINDOW_UW_VALUE",
            "DOUBLE_GLAZING_IS_NOT_CURRENT_UW_COMPLIANCE",
            "TRIPLE_GLAZING_IS_NOT_CURRENT_UW_COMPLIANCE",
            "HOUSEHOLD_WEIGHTED_SURVEY_SHARE_IS_NOT_EXACT_DWELLING_COUNT",
            "MARGINALS_PLUS_FRECHET_IS_NOT_OBSERVED_JOINT_TABLE",
        ):
            self.assertIn(b, semantic_boundaries())

        text = DOC.read_text(encoding="utf-8")
        for phrase in (
            "16.2%",
            "5.3%",
            "21.5%",
            "15.4%",
            "7.2104018913%",
            "5.8 W/m2K",
            "CURRENT_MULTIGLAZED_WINDOW_REALIZED_UW_DISTRIBUTION_REQUIRED",
        ):
            self.assertIn(phrase, text)


if __name__ == "__main__":
    unittest.main()
