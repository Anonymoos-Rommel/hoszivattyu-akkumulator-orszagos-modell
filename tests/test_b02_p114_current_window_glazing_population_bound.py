import csv
import unittest
from pathlib import Path

from modules.B02.current_window_glazing_population_bound import (
    CONDITIONAL_INTERVAL_STATUS,
    P114_STATUS,
    VALIDATION_DEBTS,
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

    def test_single_glazing_comparison_is_reference_only(self):
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
        self.assertEqual(surface["B02-P114-S03"]["status"], CONDITIONAL_INTERVAL_STATUS)
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

    def test_conditional_claim_and_explicit_unknowns(self):
        s = p114_state()
        self.assertEqual(s["status"], P114_STATUS)
        self.assertEqual(s["conditional_interval_status"], CONDITIONAL_INTERVAL_STATUS)
        self.assertEqual(s["reference_period"], "2023")
        self.assertTrue(s["common_household_current_scope_corroborated"])
        self.assertTrue(s["published_survey_coverage_corroborated"])
        for key in (
            "exact_common_table_measure_proven", "incompatible_populations_proven",
            "unweighted_tables_proven", "true_population_hard_bound_proven",
            "target_period_stock_transfer_admitted", "record_level_glazing_deficit_proven",
        ):
            self.assertFalse(s[key], key)
        for key in ("exact_table_denominator", "table_weight_revision",
                    "table_release_binding", "sampling_and_rounding_uncertainty"):
            self.assertIsNone(s[key], key)
        self.assertTrue(s["reference_glazing_comparison_only"])
        self.assertEqual(s["validation_debt"], VALIDATION_DEBTS)
        self.assertIn("HC001_HC004_TABLE_DENOMINATOR_WEIGHT_RELEASE_BINDING_REQUIRED", VALIDATION_DEBTS)
        self.assertIn("HC001_HC004_SAMPLING_AND_PUBLICATION_ROUNDING_UNCERTAINTY_REQUIRED", VALIDATION_DEBTS)
        self.assertIn(DWELLING_GRAIN_RESIDUAL, VALIDATION_DEBTS)
        self.assertIn(PRIMARY_NEXT_RESIDUAL, VALIDATION_DEBTS)
        self.assertIn("HC001_HC004_2023_TO_TARGET_PERIOD_STOCK_BRIDGE_REQUIRED", VALIDATION_DEBTS)

    def test_conditional_metadata_consistent_across_tables(self):
        reg = rows(REG, "item_id")["B02-P114-U03"]
        surface = rows(SURFACE, "surface_id")["B02-P114-S03"]
        contract = rows(CONTRACT, "field_id")
        self.assertEqual(reg["status"], CONDITIONAL_INTERVAL_STATUS)
        self.assertEqual(contract["B02-P114-C06"]["status"], CONDITIONAL_INTERVAL_STATUS)
        self.assertEqual(contract["B02-P114-C07"]["status"], CONDITIONAL_INTERVAL_STATUS)
        for debt in VALIDATION_DEBTS:
            self.assertIn(debt, reg["residual_gap"])
            self.assertIn(debt, surface["residual"])
        self.assertIn("TRUE_POPULATION_HARD_BOUND", reg["forbidden_use"])
        self.assertEqual(contract["B02-P114-C10"]["status"], "Q_VALIDATION_DEBT")
        self.assertEqual(contract["B02-P114-C11"]["status"], "Q_VALIDATION_DEBT")
        self.assertEqual(contract["B02-P114-C12"]["status"], "Q_VALIDATION_DEBT")
        for row in (
            rows(REG, "item_id")["B02-P114-U04"],
            rows(SURFACE, "surface_id")["B02-P114-S04"],
            contract["B02-P114-C13"],
        ):
            self.assertEqual(row["status"], "QUALIFIED_REFERENCE_GLAZING_COMPARISON")

    def test_frechet_conditional_domain_and_edges(self):
        for a, b in ((-0.1, 0.5), (1.1, 0.5), (0.5, -0.1),
                     (0.5, 1.1), (0.5, 0.0), (float("nan"), 0.5)):
            with self.subTest(a=a, b=b), self.assertRaises(ValueError):
                frechet_non_district_single_glazing_bound(
                    single_glazing_present_share=a, non_district_share=b)
        empty = frechet_non_district_single_glazing_bound(
            single_glazing_present_share=0.0, non_district_share=1.0)
        self.assertEqual((empty.conditional_lower, empty.conditional_upper), (0.0, 0.0))
        certain = frechet_non_district_single_glazing_bound(
            single_glazing_present_share=1.0, non_district_share=0.5)
        self.assertEqual((certain.conditional_lower, certain.conditional_upper), (1.0, 1.0))

    def test_current_registry_notes_preserve_conditional_scope(self):
        source = rows(SOURCES, "source_id")[
            "SRC-B02-EUROSTAT-SILC-2023-ENERGY-MODULE-ASSESSMENT"
        ]["notes"]
        self.assertIn("exact table denominator/weight/release remain unpinned", source)
        self.assertIn("no true-population hard bound is admitted", source)
        current_notes = (
            rows(QUESTIONS, "question_id")["Q-B02-004"]["notes"],
            rows(MODULES, "module_id")["B02"]["gate_note"],
            rows(READINESS, "component_id")["PEAK_LOAD_EFFECT"]["notes"],
        )
        for notes in current_notes:
            current = notes[notes.index("B02-P114"):]
            self.assertIn("conditional", current)
            for debt in VALIDATION_DEBTS:
                self.assertIn(debt, current)
            self.assertIn("no true-population hard bound is admitted", current)

    def test_boundaries_and_doc(self):
        for b in (
            "SINGLE_GLAZING_PRESENT_IS_NOT_WHOLE_WINDOW_UW_VALUE",
            "DOUBLE_GLAZING_IS_NOT_CURRENT_UW_COMPLIANCE",
            "TRIPLE_GLAZING_IS_NOT_CURRENT_UW_COMPLIANCE",
            "HOUSEHOLD_WEIGHTED_SURVEY_SHARE_IS_NOT_EXACT_DWELLING_COUNT",
            "MARGINALS_PLUS_FRECHET_IS_NOT_OBSERVED_JOINT_TABLE",
            "CONDITIONAL_EMPIRICAL_INTERVAL_IS_NOT_TRUE_POPULATION_HARD_BOUND",
            "PUBLISHED_COVERAGE_IS_NOT_EXACT_TABLE_WEIGHT_RELEASE_BINDING",
            "MISSING_WEIGHT_METADATA_IS_NOT_PROOF_OF_INCOMPATIBILITY",
            "ROUNDED_MARGINALS_ARE_NOT_EXACT_POPULATION_PARAMETERS",
            "GLAZING_REFERENCE_COMPARISON_IS_NOT_RECORD_LEVEL_DEFICIT_OR_LEGAL_DUTY",
            "REFERENCE_2023_IS_NOT_LATER_TARGET_STOCK",
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
