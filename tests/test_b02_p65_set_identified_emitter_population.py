import csv
import unittest
from pathlib import Path

from modules.B02.set_identified_emitter_population import (
    KSH_CENTRAL_OR_DISTRICT_CONTROL,
    MembershipScenario,
    frechet_overlap_bounds,
    identified_set,
    ksh_topology_controls,
    validate_scenario,
)


ROOT = Path(__file__).resolve().parents[1]
MODEL_REGISTRY = ROOT / "registry" / "b02_p65_set_identified_emitter_model.csv"
QUESTIONS = ROOT / "registry" / "open_questions.csv"
MODULE_STATUS = ROOT / "registry" / "module_status.csv"
SOURCE_PACK = ROOT / "docs" / "source_packs" / "B02_P65_SET_IDENTIFIED_EMITTER_POPULATION.md"


class B02P65SetIdentifiedEmitterPopulationTests(unittest.TestCase):
    def test_identified_set_preserves_known_and_unknown_dimensions(self):
        model = identified_set()
        self.assertEqual((model.surface_presence.lower, model.surface_presence.upper), (0.33, 0.66))
        self.assertEqual(
            (model.primary_gas_convector_share.lower, model.primary_gas_convector_share.upper),
            (0.233, 0.233),
        )
        self.assertEqual((model.radiator_presence.lower, model.radiator_presence.upper), (0.0, 1.0))
        self.assertEqual((model.other_emitter_presence.lower, model.other_emitter_presence.upper), (0.0, 1.0))
        self.assertEqual(model.model_status, "CANDIDATE")

    def test_frechet_overlap_bounds_are_sharp(self):
        bounds = frechet_overlap_bounds(0.50, 0.60)
        self.assertAlmostEqual(bounds.lower, 0.10)
        self.assertAlmostEqual(bounds.upper, 0.50)

        bounds = frechet_overlap_bounds(0.33, 0.20)
        self.assertAlmostEqual(bounds.lower, 0.0)
        self.assertAlmostEqual(bounds.upper, 0.20)

    def test_valid_scenario_keeps_memberships_nonexclusive(self):
        result = validate_scenario(
            MembershipScenario(
                surface_presence=0.50,
                radiator_presence=0.60,
                surface_radiator_overlap=0.20,
                other_emitter_presence=0.15,
            )
        )
        self.assertAlmostEqual(result.surface_only, 0.30)
        self.assertAlmostEqual(result.radiator_only, 0.40)
        self.assertAlmostEqual(result.surface_or_radiator_union, 0.90)
        self.assertAlmostEqual(result.minimum_overlap_by_frechet, 0.10)
        self.assertAlmostEqual(result.maximum_overlap_by_frechet, 0.50)
        self.assertAlmostEqual(result.ksh_fixed_minus_primary_convector_pp, 5.6)

    def test_invalid_overlap_or_evidence_bound_fails_closed(self):
        with self.assertRaises(ValueError):
            validate_scenario(
                MembershipScenario(
                    surface_presence=0.50,
                    radiator_presence=0.60,
                    surface_radiator_overlap=0.05,
                    other_emitter_presence=0.10,
                )
            )
        with self.assertRaises(ValueError):
            validate_scenario(
                MembershipScenario(
                    surface_presence=0.20,
                    radiator_presence=0.60,
                    surface_radiator_overlap=0.10,
                    other_emitter_presence=0.10,
                )
            )
        with self.assertRaises(ValueError):
            validate_scenario(
                MembershipScenario(
                    surface_presence=0.50,
                    radiator_presence=0.60,
                    surface_radiator_overlap=0.20,
                    other_emitter_presence=0.10,
                    primary_gas_convector_share=0.25,
                )
            )

    def test_ksh_topology_remains_validation_control(self):
        controls = ksh_topology_controls()
        self.assertAlmostEqual(KSH_CENTRAL_OR_DISTRICT_CONTROL, 0.707)
        self.assertAlmostEqual(controls["individual_fixed"], 0.289)
        self.assertAlmostEqual(controls["central_or_district_control"], 0.707)

    def test_registry_marks_model_candidate_and_unknowns_q(self):
        with MODEL_REGISTRY.open(encoding="utf-8", newline="") as handle:
            rows = {row["constraint_id"]: row for row in csv.DictReader(handle)}
        self.assertEqual(rows["B02-P65-C01"]["current_status"], "QUALIFIED_BOUND")
        self.assertEqual(rows["B02-P65-C02"]["current_status"], "QUALIFIED_BOUND")
        self.assertEqual(rows["B02-P65-C03"]["current_status"], "Q")
        self.assertEqual(rows["B02-P65-C05"]["current_status"], "Q")
        self.assertEqual(rows["B02-P65-C09"]["current_status"], "CANDIDATE")
        self.assertIn("MIXED_SYSTEM_EMPIRICAL_BOUND", rows["B02-P65-C09"]["residual_gap"])

    def test_cross_source_difference_is_diagnostic_only(self):
        with MODEL_REGISTRY.open(encoding="utf-8", newline="") as handle:
            rows = {row["constraint_id"]: row for row in csv.DictReader(handle)}
        diagnostic = rows["B02-P65-C08"]
        self.assertEqual(diagnostic["lower_bound"], "0.056")
        self.assertEqual(diagnostic["upper_bound"], "0.056")
        self.assertEqual(diagnostic["use"], "DIAGNOSTIC_ONLY")
        self.assertIn("OTHER_FIXED_SHARE", diagnostic["forbidden_inference"])

    def test_q_b02_004_remains_open_with_refined_residual(self):
        with QUESTIONS.open(encoding="utf-8", newline="") as handle:
            rows = {row["question_id"]: row for row in csv.DictReader(handle)}
        q4 = rows["Q-B02-004"]
        self.assertEqual(q4["status"], "OPEN")
        self.assertIn("set-identified", q4["evidence_needed"])
        self.assertIn("KSH/P21", q4["evidence_needed"])
        self.assertIn("RADIATOR_PRESENCE_NUMERIC_BOUND", q4["notes"])
        self.assertIn("MIXED_SYSTEM_EMPIRICAL_BOUND", q4["notes"])
        self.assertIn("OTHER_EMITTER_NUMERIC_BOUND", q4["notes"])
        self.assertIn("TRANSITION_MODEL_POPULATION_WEIGHTING", q4["notes"])

    def test_module_readiness_is_unchanged(self):
        with MODULE_STATUS.open(encoding="utf-8", newline="") as handle:
            rows = {row["module_id"]: row for row in csv.DictReader(handle)}
        b02 = rows["B02"]
        self.assertEqual(b02["readiness_percent"], "55")
        self.assertIn("B02-P65 set-identified emitter model candidate", b02["gate_note"])

    def test_source_pack_forbids_false_precision(self):
        text = SOURCE_PACK.read_text(encoding="utf-8")
        for boundary in (
            "EMITTER MEMBERSHIP != MUTUALLY EXCLUSIVE STOCK BIN",
            "PRIMARY HEATING TYPE != COMPLETE EMITTER INVENTORY",
            "UNKNOWN OVERLAP != ZERO OVERLAP",
            "FRECHET BOUND != EMPIRICAL MIXED-SYSTEM SHARE",
            "CROSS-SOURCE DIFFERENCE != RESIDUAL CATEGORY SHARE",
        ):
            self.assertIn(boundary, text)


if __name__ == "__main__":
    unittest.main()
