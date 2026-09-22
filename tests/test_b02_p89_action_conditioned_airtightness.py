import csv
import unittest
from pathlib import Path

from modules.B02.action_conditioned_airtightness_response import (
    HUNGARIAN_PTE_EXAMPLE_N4_MAX_H,
    HUNGARIAN_PTE_EXAMPLE_N4_MIN_H,
    HUNGARIAN_PTE_EXAMPLE_N50_MAX_H,
    HUNGARIAN_PTE_EXAMPLE_N50_MIN_H,
    HUNGARIAN_PTE_FLOW_EXPONENT_MAX,
    HUNGARIAN_PTE_FLOW_EXPONENT_MIN,
    RFTF_PAIRED_PROPERTIES,
    WINDOW_REPLACEMENT_MAX_N50_REDUCTION_FRACTION,
    WINDOW_REPLACEMENT_MEAN_N50_REDUCTION_FRACTION,
    WINDOW_REPLACEMENT_PAIRED_HOMES,
    apply_relative_airtightness_reduction,
    hungarian_n4_bound_from_n50_upper,
    p89_state,
    pressure_transfer_factor,
    semantic_boundaries,
)
from modules.B02.national_design_load_input_coverage import (
    QUALIFIED_REFERENCE_PROGRAMME_TARGET_SURFACE,
    current_design_load_blockers,
    national_design_load_input_coverage,
)


ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "data" / "processed" / "b02" / "p89_action_conditioned_airtightness_evidence.csv"
REG = ROOT / "registry" / "b02_p89_action_conditioned_airtightness.csv"
QUESTIONS = ROOT / "registry" / "open_questions.csv"
MODULES = ROOT / "registry" / "module_status.csv"
READINESS = ROOT / "registry" / "retrofit_readiness.csv"
SOURCES = ROOT / "registry" / "sources.csv"
DOC = ROOT / "docs" / "source_packs" / "B02_P89_ACTION_CONDITIONED_AIRTIGHTNESS_RESPONSE.md"


def rows(path, key=None):
    with path.open(encoding="utf-8", newline="") as handle:
        data = list(csv.DictReader(handle))
    if key is None:
        return data
    return {row[key]: row for row in data}


class B02P89ActionConditionedAirtightnessTests(unittest.TestCase):
    def test_hungarian_pressure_transfer_constants_are_exact(self):
        self.assertEqual(HUNGARIAN_PTE_FLOW_EXPONENT_MIN, 0.566)
        self.assertEqual(HUNGARIAN_PTE_FLOW_EXPONENT_MAX, 0.689)
        self.assertEqual(HUNGARIAN_PTE_EXAMPLE_N50_MIN_H, 1.86)
        self.assertEqual(HUNGARIAN_PTE_EXAMPLE_N50_MAX_H, 8.28)
        self.assertEqual(HUNGARIAN_PTE_EXAMPLE_N4_MIN_H, 0.36)
        self.assertEqual(HUNGARIAN_PTE_EXAMPLE_N4_MAX_H, 1.52)

    def test_pressure_transfer_factor_and_n50_upper_bound(self):
        lower = pressure_transfer_factor(
            pressure_pa=4.0,
            reference_pressure_pa=50.0,
            flow_exponent=0.689,
        )
        upper = pressure_transfer_factor(
            pressure_pa=4.0,
            reference_pressure_pa=50.0,
            flow_exponent=0.566,
        )
        self.assertAlmostEqual(lower, 0.17548055570317644)
        self.assertAlmostEqual(upper, 0.23941366370915412)

        bound = hungarian_n4_bound_from_n50_upper(n50_upper_h=3.0)
        self.assertAlmostEqual(bound.n4_upper_lower_h, 0.5264416671095293)
        self.assertAlmostEqual(bound.n4_upper_upper_h, 0.7182409911274623)
        self.assertEqual(
            bound.status,
            "HUNGARIAN_4PA_PRESSURE_TRANSFER_CALIBRATION",
        )

    def test_same_metric_relative_response_only(self):
        mean = apply_relative_airtightness_reduction(
            baseline_value=8.0,
            reduction_fraction=WINDOW_REPLACEMENT_MEAN_N50_REDUCTION_FRACTION,
            metric="n50_1_per_h",
        )
        maximum = apply_relative_airtightness_reduction(
            baseline_value=8.0,
            reduction_fraction=WINDOW_REPLACEMENT_MAX_N50_REDUCTION_FRACTION,
            metric="n50_1_per_h",
        )
        self.assertAlmostEqual(mean.post_value, 7.512)
        self.assertAlmostEqual(maximum.post_value, 6.456)

        with self.assertRaises(ValueError):
            apply_relative_airtightness_reduction(
                baseline_value=8.0,
                reduction_fraction=0.1,
                metric="n4_1_per_h",
            )
        with self.assertRaises(ValueError):
            apply_relative_airtightness_reduction(
                baseline_value=8.0,
                reduction_fraction=1.1,
                metric="n50_1_per_h",
            )

    def test_measured_response_cohorts_are_not_minted_as_hungarian_weights(self):
        self.assertEqual(WINDOW_REPLACEMENT_PAIRED_HOMES, 20)
        self.assertEqual(RFTF_PAIRED_PROPERTIES, 87)
        self.assertEqual(
            WINDOW_REPLACEMENT_MEAN_N50_REDUCTION_FRACTION,
            0.061,
        )
        self.assertEqual(
            WINDOW_REPLACEMENT_MAX_N50_REDUCTION_FRACTION,
            0.193,
        )

        evidence = rows(EVIDENCE, "evidence_id")
        self.assertEqual(len(evidence), 4)
        self.assertIn(
            "HUNGARIAN_POPULATION_WEIGHT",
            evidence["B02-P89-E03"]["forbidden_use"],
        )
        self.assertIn(
            "N50_CONVERSION_WITHOUT_GEOMETRY",
            evidence["B02-P89-E02"]["forbidden_use"],
        )
        self.assertIn(
            "MINIMUM_EFFECT_FLOOR",
            evidence["B02-P89-E03"]["forbidden_use"],
        )

    def test_current_ventilation_coverage_is_narrowed_not_resolved(self):
        by = {item.input_id: item for item in national_design_load_input_coverage()}
        vent = by["POST_RETROFIT_VENTILATION"]
        self.assertEqual(
            vent.status,
            QUALIFIED_REFERENCE_PROGRAMME_TARGET_SURFACE,
        )
        self.assertIsNone(vent.blocker)
        self.assertIn("B02-P89", vent.source_refs)
        self.assertIn("B02-P90", vent.source_refs)
        blockers = set(current_design_load_blockers())
        self.assertNotIn(
            "POST_RETROFIT_ABSOLUTE_AIRTIGHTNESS_STATE_OR_PROGRAMME_TARGET_REQUIRED",
            blockers,
        )
        self.assertNotIn(
            "ACTION_CONDITIONED_POST_RETROFIT_INFILTRATION_REQUIRED",
            blockers,
        )

    def test_p89_state_reports_exact_residual(self):
        state = p89_state()
        self.assertEqual(state["hungarian_field_locations"], 33)
        self.assertEqual(state["hungarian_example_count"], 7)
        self.assertEqual(
            state["response_engine_status"],
            "PARTIAL_RESOLVED_MEASURED_AIRTIGHTNESS_RESPONSE",
        )
        self.assertEqual(
            state["current_residual"],
            "POST_RETROFIT_ABSOLUTE_AIRTIGHTNESS_STATE_OR_PROGRAMME_TARGET_REQUIRED",
        )

    def test_registry_and_readiness_are_conservative(self):
        reg = rows(REG, "item_id")
        self.assertEqual(
            reg["B02-P89-A08"]["status"],
            "PARTIAL_RESOLVED_MEASURED_AIRTIGHTNESS_RESPONSE",
        )
        self.assertEqual(
            reg["B02-P89-A09"]["status"],
            "OPEN_NARROWED",
        )

        q = rows(QUESTIONS, "question_id")["Q-B02-004"]
        self.assertEqual(q["status"], "OPEN")
        self.assertIn("B02-P89", q["notes"])
        self.assertIn(
            "POST_RETROFIT_ABSOLUTE_AIRTIGHTNESS_STATE_OR_PROGRAMME_TARGET_REQUIRED",
            q["notes"],
        )

        module = rows(MODULES, "module_id")["B02"]
        self.assertEqual(module["readiness_percent"], "55")
        self.assertIn("B02-P89", module["gate_note"])

        peak = rows(READINESS, "component_id")["PEAK_LOAD_EFFECT"]
        self.assertEqual(peak["readiness_percent"], "50")
        self.assertIn("B02-P89", peak["notes"])

    def test_source_registry_contains_all_p89_authorities(self):
        sources = rows(SOURCES, "source_id")
        for source_id in (
            "SRC-B02-HU-PTE-AIRTIGHTNESS-2014",
            "SRC-B02-UK-RFTF-AIRTIGHTNESS-2013",
            "SRC-B02-US-WINDOW-AIRTIGHTNESS-2026",
            "SRC-B02-UK-AIRTIGHTNESS-DURABILITY-2025",
        ):
            self.assertIn(source_id, sources)

        self.assertIn(
            "33 locations",
            sources["SRC-B02-HU-PTE-AIRTIGHTNESS-2014"]["notes"],
        )
        self.assertIn(
            "87 properties",
            sources["SRC-B02-UK-RFTF-AIRTIGHTNESS-2013"]["notes"],
        )
        self.assertIn(
            "6.1%",
            sources["SRC-B02-US-WINDOW-AIRTIGHTNESS-2026"]["notes"],
        )
        self.assertIn(
            "seven became less airtight",
            sources["SRC-B02-UK-AIRTIGHTNESS-DURABILITY-2025"]["notes"],
        )

    def test_nonpromotion_boundaries_are_frozen(self):
        boundary = semantic_boundaries()
        for item in (
            "Q50_IS_NOT_N50",
            "PRESSURE_TEST_AIRTIGHTNESS_IS_NOT_NATURAL_INFILTRATION",
            "TYPE_A_N50_INCLUDES_INTENTIONAL_OPENINGS",
            "FOREIGN_RETROFIT_RESPONSE_IS_NOT_HUNGARIAN_POPULATION_WEIGHT",
            "IMMEDIATE_POST_RETROFIT_AIRTIGHTNESS_IS_NOT_LONG_TERM_DURABILITY",
            "N4_PRESSURE_TRANSFER_IS_NOT_CURRENT_METHOD_NFILT_CLASSIFICATION",
        ):
            self.assertIn(item, boundary)

        text = DOC.read_text(encoding="utf-8")
        for phrase in (
            "Q50 != N50",
            "PRESSURE-TEST AIRTIGHTNESS != NATURAL INFILTRATION",
            "B02 remains **55%**",
            "POST_RETROFIT_ABSOLUTE_AIRTIGHTNESS_STATE_OR_PROGRAMME_TARGET_REQUIRED",
        ):
            self.assertIn(phrase, text)


if __name__ == "__main__":
    unittest.main()
