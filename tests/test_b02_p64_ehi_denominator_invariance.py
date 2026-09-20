import csv
import unittest
from pathlib import Path

from modules.B02.ehi_surface_band_aggregation import (
    BoundedStratum,
    aggregate_envelope,
    ehi_hungary_residential_validation_envelope,
)


ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "registry" / "b02_p64_ehi_denominator_invariance.csv"
QUESTIONS = ROOT / "registry" / "open_questions.csv"
MODULE_STATUS = ROOT / "registry" / "module_status.csv"
SOURCE_PACK = ROOT / "docs" / "source_packs" / "B02_P64_EHI_DENOMINATOR_INVARIANCE.md"


class B02P64EhiDenominatorInvarianceTests(unittest.TestCase):
    def test_common_bounds_do_not_require_denominator_weights(self):
        result = ehi_hungary_residential_validation_envelope()
        self.assertEqual(result.lower, 0.33)
        self.assertEqual(result.upper, 0.66)
        self.assertFalse(result.denominator_weights_required)
        self.assertEqual(result.evidence_status, "DER")
        self.assertEqual(result.use, "NATIONAL_VALIDATION_BAND_ONLY")

    def test_any_valid_house_apartment_weight_preserves_same_bounds(self):
        strata = (
            BoundedStratum("HOUSES", 0.33, 0.66),
            BoundedStratum("APARTMENTS", 0.33, 0.66),
        )
        for house_weight in (0.0, 0.1, 0.25, 0.5, 0.75, 0.9, 1.0):
            result = aggregate_envelope(strata, (house_weight, 1.0 - house_weight))
            self.assertAlmostEqual(result.lower, 0.33)
            self.assertAlmostEqual(result.upper, 0.66)

    def test_non_identical_bounds_require_weights(self):
        strata = (
            BoundedStratum("A", 0.10, 0.20),
            BoundedStratum("B", 0.30, 0.40),
        )
        with self.assertRaises(ValueError):
            aggregate_envelope(strata)
        result = aggregate_envelope(strata, (0.25, 0.75))
        self.assertAlmostEqual(result.lower, 0.25)
        self.assertAlmostEqual(result.upper, 0.35)

    def test_invalid_weights_fail_closed(self):
        strata = (
            BoundedStratum("HOUSES", 0.33, 0.66),
            BoundedStratum("APARTMENTS", 0.33, 0.66),
        )
        for weights in ((0.4, 0.4), (-0.1, 1.1), (1.0,)):
            with self.assertRaises(ValueError):
                aggregate_envelope(strata, weights)

    def test_registry_retires_numeric_denominator_only(self):
        with REGISTRY.open(encoding="utf-8", newline="") as handle:
            rows = {row["proof_id"]: row for row in csv.DictReader(handle)}
        national = rows["B02-P64-P01"]
        self.assertEqual(national["weight_requirement"], "NONE_FOR_COMMON_BAND")
        self.assertEqual(national["aggregate_bound"], "[0.33,0.66]")
        self.assertIn("P21_CELL_ASSIGNMENT", national["forbidden_inference"])

        cell = rows["B02-P64-P02"]
        self.assertEqual(cell["allowed_use"], "NO")
        self.assertIn("P21_STRATUM_EMITTER_ALLOCATION", cell["residual_gap"])

    def test_q_b02_004_uses_current_residual(self):
        with QUESTIONS.open(encoding="utf-8", newline="") as handle:
            rows = {row["question_id"]: row for row in csv.DictReader(handle)}
        q4 = rows["Q-B02-004"]
        self.assertEqual(q4["status"], "OPEN")
        self.assertIn("numerikus súly", q4["evidence_needed"])
        self.assertIn("KSH_DENOMINATOR_BRIDGE", q4["notes"])
        self.assertIn("RETIRED", q4["notes"])
        self.assertIn("EHI_TO_P21_SEMANTIC_COVERAGE", q4["notes"])
        self.assertIn("P21_STRATUM_EMITTER_ALLOCATION", q4["notes"])
        self.assertIn("MIXED_SYSTEM_OVERLAP", q4["notes"])
        self.assertIn("OTHER_EMITTER_SHARE", q4["notes"])
        self.assertIn("TRANSITION_MODEL_POPULATION_WEIGHTING", q4["notes"])

    def test_module_readiness_is_unchanged(self):
        with MODULE_STATUS.open(encoding="utf-8", newline="") as handle:
            rows = {row["module_id"]: row for row in csv.DictReader(handle)}
        b02 = rows["B02"]
        self.assertEqual(b02["readiness_percent"], "55")
        self.assertIn("P64", b02["gate_note"])
        self.assertIn("RETIRED", b02["gate_note"])
        self.assertIn("P21 stratum emitter allocation", b02["gate_note"])

    def test_source_pack_freezes_non_equivalences(self):
        text = SOURCE_PACK.read_text(encoding="utf-8")
        for boundary in (
            "COMMON STRATUM BOUNDS -> AGGREGATE BOUND INVARIANT TO NUMERIC DENOMINATOR WEIGHTS",
            "NUMERIC DENOMINATOR WEIGHTS != SEMANTIC CATEGORY MAPPING",
            "EHI_HOUSES = P21_FAMILY_HOUSE",
            "EHI_APARTMENTS = P21_MULTI_DWELLING",
            "P21_STRATUM_EMITTER_ALLOCATION",
            "MIXED_SYSTEM_OVERLAP",
            "OTHER_EMITTER_SHARE",
            "TRANSITION_MODEL_POPULATION_WEIGHTING",
        ):
            self.assertIn(boundary, text)


if __name__ == "__main__":
    unittest.main()
