import csv
import unittest
from pathlib import Path

from modules.B02.emitter_set_identification import (
    CandidateEmitterComposition,
    assess_candidate,
    build_emitter_population_envelope,
    global_latent_bounds,
)


ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "registry" / "b02_p65_emitter_set_identification.csv"
QUESTIONS = ROOT / "registry" / "open_questions.csv"
MODULE_STATUS = ROOT / "registry" / "module_status.csv"
SOURCE_PACK = ROOT / "docs" / "source_packs" / "B02_P65_EMITTER_SET_IDENTIFICATION.md"


class B02P65EmitterSetIdentificationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.envelope = build_emitter_population_envelope()

    def test_exact_topology_controls_and_aggregate_evidence_are_preserved(self):
        e = self.envelope
        self.assertEqual(e.occupied_dwellings, 4_008_541)
        self.assertEqual(e.district_heating_dwellings, 618_724)
        self.assertEqual(
            e.occupied_dwellings,
            e.central_heating_dwellings
            + e.district_heating_dwellings
            + e.room_by_room_or_no_heat_dwellings,
        )
        self.assertEqual(e.surface_presence_lower, 0.33)
        self.assertEqual(e.surface_presence_upper, 0.66)
        self.assertEqual(e.primary_gas_convector_share, 0.233)
        self.assertAlmostEqual(
            e.primary_gas_convector_expected_dwellings,
            4_008_541 * 0.233,
        )
        self.assertEqual(e.evidence_status, "SET_IDENTIFIED")

    def test_point_identification_is_not_fabricated(self):
        e = self.envelope
        self.assertFalse(e.radiator_presence_identified)
        self.assertFalse(e.mixed_radiator_surface_identified)
        self.assertFalse(e.other_emitter_presence_identified)
        self.assertFalse(e.p21_cell_allocation_identified)

        bounds = global_latent_bounds()
        self.assertEqual(bounds["surface_present_share"], (0.33, 0.66))
        self.assertEqual(bounds["primary_gas_convector_share"], (0.233, 0.233))
        self.assertEqual(bounds["radiator_present_share"], (0.0, 1.0))
        self.assertEqual(bounds["mixed_radiator_surface_share"], (0.0, 0.66))
        self.assertEqual(bounds["other_emitter_present_share"], (0.0, 1.0))
        self.assertEqual(
            bounds["p21_stratum_emitter_allocation"],
            "LATENT_SIMPLEX_WITH_AGGREGATE_CONSTRAINTS",
        )

    def test_admissible_nonexclusive_candidate_passes(self):
        candidate = CandidateEmitterComposition(
            surface_present_share=0.50,
            radiator_present_share=0.70,
            mixed_radiator_surface_share=0.25,
            other_emitter_present_share=0.10,
        )
        result = assess_candidate(candidate)
        self.assertTrue(result.admissible)
        self.assertEqual(result.blockers, ())
        self.assertAlmostEqual(result.radiator_surface_union_share, 0.95)

    def test_surface_band_and_convector_margin_fail_closed(self):
        low = CandidateEmitterComposition(0.32, 0.50, 0.10, 0.10)
        self.assertIn(
            "SURFACE_PRESENCE_BELOW_EHI_BAND",
            assess_candidate(low).blockers,
        )

        high = CandidateEmitterComposition(0.67, 0.50, 0.20, 0.10)
        self.assertIn(
            "SURFACE_PRESENCE_ABOVE_EHI_BAND",
            assess_candidate(high).blockers,
        )

        drift = CandidateEmitterComposition(
            0.50, 0.70, 0.25, 0.10, primary_gas_convector_share=0.24
        )
        self.assertIn(
            "PRIMARY_GAS_CONVECTOR_MARGIN_DRIFT",
            assess_candidate(drift).blockers,
        )

    def test_mixed_overlap_uses_sharp_frechet_bounds(self):
        too_low = CandidateEmitterComposition(
            surface_present_share=0.60,
            radiator_present_share=0.70,
            mixed_radiator_surface_share=0.20,
            other_emitter_present_share=0.10,
        )
        self.assertIn(
            "RADIATOR_SURFACE_OVERLAP_BELOW_FRECHET",
            assess_candidate(too_low).blockers,
        )

        too_high = CandidateEmitterComposition(
            surface_present_share=0.40,
            radiator_present_share=0.50,
            mixed_radiator_surface_share=0.45,
            other_emitter_present_share=0.10,
        )
        self.assertIn(
            "RADIATOR_SURFACE_OVERLAP_ABOVE_FRECHET",
            assess_candidate(too_high).blockers,
        )

    def test_presence_variables_are_not_forced_to_sum_to_one(self):
        candidate = CandidateEmitterComposition(
            surface_present_share=0.55,
            radiator_present_share=0.75,
            mixed_radiator_surface_share=0.35,
            other_emitter_present_share=0.40,
        )
        result = assess_candidate(candidate)
        self.assertTrue(result.admissible)
        self.assertGreater(
            candidate.surface_present_share
            + candidate.radiator_present_share
            + candidate.other_emitter_present_share,
            1.0,
        )

    def test_registry_reclassifies_missing_point_data_as_latent(self):
        with REGISTRY.open(encoding="utf-8", newline="") as handle:
            rows = {row["parameter_id"]: row for row in csv.DictReader(handle)}

        self.assertEqual(
            rows["B02-P65-I07"]["identification_status"], "LATENT"
        )
        self.assertEqual(
            rows["B02-P65-I08"]["allowed_treatment"], "FRECHET_BOUNDED_LATENT"
        )
        self.assertEqual(
            rows["B02-P65-I10"]["allowed_treatment"],
            "SET_LATENT_WITH_AGGREGATE_CONSTRAINTS",
        )
        self.assertEqual(
            rows["B02-P65-I11"]["identification_status"],
            "RETIRED_AS_STANDALONE_BLOCKER",
        )
        self.assertIn(
            "TRANSITION_MODEL_SET_PROPAGATION",
            rows["B02-P65-I12"]["residual_gap"],
        )

    def test_q_b02_004_remains_open_only_for_set_propagation_layer(self):
        with QUESTIONS.open(encoding="utf-8", newline="") as handle:
            rows = {row["question_id"]: row for row in csv.DictReader(handle)}
        q4 = rows["Q-B02-004"]
        self.assertEqual(q4["status"], "OPEN")
        self.assertIn("LATENT_SIMPLEX_WITH_AGGREGATE_CONSTRAINTS", q4["notes"])
        self.assertIn("FRECHET_BOUNDED_LATENT", q4["notes"])
        self.assertIn("TRANSITION_MODEL_SET_PROPAGATION", q4["notes"])
        self.assertIn("ACTION_OUTCOME_BOUNDS", q4["notes"])
        self.assertIn("record-level evidence", q4["notes"])

    def test_module_readiness_does_not_increase(self):
        with MODULE_STATUS.open(encoding="utf-8", newline="") as handle:
            rows = {row["module_id"]: row for row in csv.DictReader(handle)}
        b02 = rows["B02"]
        self.assertEqual(b02["readiness_percent"], "55")
        self.assertIn("B02-P65", b02["gate_note"])
        self.assertIn("TRANSITION_MODEL_SET_PROPAGATION", b02["gate_note"])

    def test_source_pack_freezes_non_equivalences(self):
        text = SOURCE_PACK.read_text(encoding="utf-8")
        for boundary in (
            "POINT ESTIMATE NOT IDENTIFIED != MODEL BLOCKED",
            "SURFACE PRESENCE != SURFACE ONLY",
            "HEATING TOPOLOGY != HEAT EMITTER",
            "CALIBRATED GAS-CONVECTOR MARGIN != NHEAT CELL ASSIGNMENT",
            "MIXED_SYSTEM_OVERLAP -> FRECHET_BOUNDED_LATENT",
            "P21_STRATUM_EMITTER_ALLOCATION = LATENT_SIMPLEX_WITH_AGGREGATE_CONSTRAINTS",
            "TRANSITION_MODEL_SET_PROPAGATION + ACTION_OUTCOME_BOUNDS",
        ):
            self.assertIn(boundary, text)


if __name__ == "__main__":
    unittest.main()
