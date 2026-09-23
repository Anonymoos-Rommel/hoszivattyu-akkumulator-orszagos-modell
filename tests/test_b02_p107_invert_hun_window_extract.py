import csv
import unittest
from pathlib import Path

from modules.B02.invert_hun_window_extract import (
    BASE_GENERATION_ROWS,
    BASE_GENERATION_SHARE,
    GEN2_ROWS,
    GEN2_SHARE,
    GEN2_REFERENCE_1_10_ROWS,
    HUN_2025_ARCHETYPE_ROWS,
    HUN_2025_MODEL_DWELLING_WEIGHT,
    INVERT_TO_CANONICAL_DWELLING_WEIGHT_RATIO,
    PRIMARY_NEXT_RESIDUAL,
    REFERENCE_1_10_ROWS,
    RESOLVED_EXTRACT_BLOCKER,
    SOURCE_MD5,
    can_promote_invert_generation_to_replaced_window_population,
    classify_source_generation,
    p107_state,
    semantic_boundaries,
)

ROOT = Path(__file__).resolve().parents[1]
DETAIL = ROOT / "data" / "processed" / "b02" / "p107_invert_hun_2025_window_archetypes.csv"
SUMMARY = ROOT / "data" / "processed" / "b02" / "p107_invert_hun_2025_window_generation_summary.csv"
DIAG = ROOT / "data" / "processed" / "b02" / "p107_invert_hun_2025_extract_diagnostics.csv"
REG = ROOT / "registry" / "b02_p107_invert_hun_window_extract.csv"
SOURCES = ROOT / "registry" / "sources.csv"
QUESTIONS = ROOT / "registry" / "open_questions.csv"
MODULES = ROOT / "registry" / "module_status.csv"
READINESS = ROOT / "registry" / "retrofit_readiness.csv"
DOC = ROOT / "docs" / "source_packs" / "B02_P107_INVERT_HUN_WINDOW_EXTRACT.md"


def rows(path, key=None):
    with path.open(encoding="utf-8", newline="") as handle:
        data = list(csv.DictReader(handle))
    if key is None:
        return data
    return {row[key]: row for row in data}


class B02P107InvertHunWindowExtractTests(unittest.TestCase):
    def test_source_generation_contract(self):
        base = classify_source_generation("SFHdh_1800_1944_Debrecen_ren1")
        self.assertEqual(base.generation, "BASE_GENERATION")
        self.assertFalse(base.explicit_renovated_generation)

        gen2 = classify_source_generation("SFHdh_1960_1979_Debrecen_ren13_gen2")
        self.assertEqual(gen2.generation, "gen2")
        self.assertTrue(gen2.explicit_renovated_generation)

        with self.assertRaises(ValueError):
            classify_source_generation("x_gen5")

    def test_detail_extract_is_exact_hun_2025_surface(self):
        detail = rows(DETAIL)
        self.assertEqual(len(detail), HUN_2025_ARCHETYPE_ROWS)
        self.assertTrue(all(r["country"] == "HUN" for r in detail))
        self.assertTrue(all(r["year"] == "2025" for r in detail))
        self.assertEqual(
            sum(1 for r in detail if r["renovation_generation"] == "BASE_GENERATION"),
            BASE_GENERATION_ROWS,
        )
        self.assertEqual(
            sum(1 for r in detail if r["renovation_generation"] == "gen2"),
            GEN2_ROWS,
        )
        self.assertFalse(any(r["renovation_generation"] == "UNKNOWN" for r in detail))
        self.assertFalse(any(r["renovation_generation"] == "gen3" for r in detail))
        self.assertFalse(any(r["renovation_generation"] == "gen4" for r in detail))

    def test_generation_summary_freezes_numeric_findings(self):
        summary = rows(SUMMARY, "renovation_generation")
        self.assertEqual(set(summary), {"BASE_GENERATION", "gen2"})

        base = summary["BASE_GENERATION"]
        self.assertEqual(int(base["archetype_rows"]), BASE_GENERATION_ROWS)
        self.assertAlmostEqual(
            float(base["dwelling_weight_share_of_hun_2025"]),
            BASE_GENERATION_SHARE,
        )
        self.assertAlmostEqual(
            float(base["dwelling_weighted_mean_effective_u_w_m2k"]),
            3.95483899117,
        )

        gen2 = summary["gen2"]
        self.assertEqual(int(gen2["archetype_rows"]), GEN2_ROWS)
        self.assertAlmostEqual(
            float(gen2["dwelling_weight_share_of_hun_2025"]),
            GEN2_SHARE,
        )
        self.assertAlmostEqual(
            float(gen2["dwelling_weighted_mean_effective_u_w_m2k"]),
            4.2734375,
        )
        self.assertEqual(
            float(gen2["dwelling_weight_share_at_or_below_1_10"]),
            0.0,
        )

    def test_reference_satisfied_rows_are_new_construction_only(self):
        detail = rows(DETAIL)
        satisfied = [
            r for r in detail if r["model_reference_satisfied_1_10"] == "True"
        ]
        self.assertEqual(len(satisfied), REFERENCE_1_10_ROWS)
        self.assertEqual({r["name"] for r in satisfied}, {"New_MFH_1_MFH"})
        self.assertEqual(
            {int(float(r["construction_period_start"])) for r in satisfied},
            {2020, 2022, 2025},
        )
        self.assertEqual(
            sum(1 for r in satisfied if r["renovation_generation"] == "gen2"),
            GEN2_REFERENCE_1_10_ROWS,
        )

    def test_diagnostics_pin_source_and_population_boundary(self):
        diag = rows(DIAG, "metric")
        self.assertEqual(diag["source_md5"]["value"], SOURCE_MD5)
        self.assertEqual(int(diag["hun_2025_rows"]["value"]), HUN_2025_ARCHETYPE_ROWS)
        self.assertAlmostEqual(
            float(diag["hun_2025_total_dwelling_weight"]["value"]),
            HUN_2025_MODEL_DWELLING_WEIGHT,
        )
        self.assertAlmostEqual(
            float(diag["invert_to_canonical_dwelling_weight_ratio"]["value"]),
            INVERT_TO_CANONICAL_DWELLING_WEIGHT_RATIO,
        )
        self.assertEqual(diag["raw_binary_committed"]["value"], "NO")

    def test_direct_population_promotion_is_rejected(self):
        admitted, blockers = can_promote_invert_generation_to_replaced_window_population()
        self.assertFalse(admitted)
        self.assertIn(
            "RENOVATION_GENERATION_IS_NOT_COMPONENT_SPECIFIC_WINDOW_REPLACEMENT",
            blockers,
        )
        self.assertIn(
            "GEN2_WINDOW_UEFF_IS_NOT_MONOTONIC_IMPROVEMENT_OVER_BASE",
            blockers,
        )
        self.assertIn(PRIMARY_NEXT_RESIDUAL, blockers)

    def test_state_and_registries_preserve_no_numeric_tightening(self):
        state = p107_state()
        self.assertEqual(state["resolved_blocker"], RESOLVED_EXTRACT_BLOCKER)
        self.assertEqual(state["primary_residual"], PRIMARY_NEXT_RESIDUAL)
        self.assertTrue(state["invert_extract_materialized"])
        self.assertFalse(
            state["invert_direct_replaced_window_population_promotion_admitted"]
        )
        self.assertFalse(state["p107_numeric_national_action_tightening"])
        self.assertAlmostEqual(
            state["p102_structural_calibrated_retrofit_floor_lower_share"],
            0.8278610299446981,
        )
        self.assertAlmostEqual(state["hp_only_share_upper"], 0.17213897005530188)

        reg = rows(REG, "item_id")
        self.assertEqual(
            reg["B02-P107-U09"]["status"],
            "RESOLVED_EXECUTABLE_NUMERIC_EXTRACT",
        )
        self.assertEqual(
            reg["B02-P107-U08"]["status"],
            "REJECTED_SEMANTIC_MISMATCH",
        )

        sources = rows(SOURCES, "source_id")
        self.assertIn(
            "P107 exact HUN 2025 extract",
            sources["SRC-B02-TUWIEN-INVERT-EU27-STOCK-2026"]["notes"],
        )

        q = rows(QUESTIONS, "question_id")["Q-B02-004"]
        self.assertIn("B02-P107", q["notes"])
        self.assertIn(PRIMARY_NEXT_RESIDUAL, q["notes"])

        module = rows(MODULES, "module_id")["B02"]
        self.assertEqual(module["readiness_percent"], "55")
        self.assertIn("B02-P107", module["gate_note"])

        peak = rows(READINESS, "component_id")["PEAK_LOAD_EFFECT"]
        self.assertEqual(peak["readiness_percent"], "50")
        self.assertIn("B02-P107", peak["notes"])

    def test_semantic_boundaries_and_document_are_frozen(self):
        for boundary in (
            "BASE_GENERATION_IS_NOT_REPLACED_WINDOW_CLASS",
            "GEN2_IS_WHOLE_BUILDING_RENOVATION_NOT_WINDOW_REPLACEMENT",
            "MODEL_UEFF_IS_NOT_OBSERVED_PRODUCT_UW",
            "NEW_CONSTRUCTION_REFERENCE_ROWS_ARE_NOT_REPLACED_WINDOW_EVIDENCE",
            "INVERT_MODEL_WEIGHT_IS_NOT_CANONICAL_B02_POPULATION_WEIGHT",
            "TARKI_WINDOW_REPLACED_SHARE_CANNOT_BE_DIRECTLY_MAPPED_TO_INVERT_GENERATION",
        ):
            self.assertIn(boundary, semantic_boundaries())

        text = DOC.read_text(encoding="utf-8")
        for phrase in (
            "1,358",
            "3,515,973",
            "78.0601441860%",
            "21.9398438931%",
            "3.95483899117",
            "4.2734375",
            "964.809265137",
            "COMPONENT_SPECIFIC_WINDOW_REPLACEMENT_PERFORMANCE_BRIDGE_REQUIRED",
            "82.7861029945%",
            "17.2138970055%",
        ):
            self.assertIn(phrase, text)


if __name__ == "__main__":
    unittest.main()
