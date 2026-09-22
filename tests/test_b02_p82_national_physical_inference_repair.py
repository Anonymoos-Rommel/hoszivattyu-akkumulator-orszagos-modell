import csv
import unittest
from pathlib import Path

from modules.B02.national_physical_inference_layer import (
    CALIBRATED_MULTI_SOURCE_INFERENCE,
    POPULATION_INFERENCE,
    SCENARIO_MODEL_CONTRACT,
    PopulationPhysicalEvidence,
    assess_population_physical_evidence,
    blocker_repairs,
    current_requirements,
    record_level_boundary,
)

ROOT = Path(__file__).resolve().parents[1]
REG = ROOT / "registry" / "b02_p82_national_physical_inference_repair.csv"
DOC = ROOT / "docs" / "source_packs" / "B02_P82_NATIONAL_PHYSICAL_INFERENCE_REPAIR.md"


def rows(path, key):
    with path.open(encoding="utf-8", newline="") as handle:
        return {row[key]: row for row in csv.DictReader(handle)}


class B02P82NationalPhysicalInferenceRepairTests(unittest.TestCase):
    def test_all_repairs_preserve_record_exactness(self):
        repairs = blocker_repairs()
        self.assertEqual(len(repairs), 11)
        self.assertTrue(all(x.record_level_exactness_preserved for x in repairs))

    def test_population_plane_reframes_exact_surfaces(self):
        required = set(current_requirements(POPULATION_INFERENCE))
        self.assertIn("DEFENSIBLE_CURRENT_BASELINE_U_INFERENCE_REQUIRED", required)
        self.assertIn("DEFENSIBLE_COMPONENT_AREA_GEOMETRY_INFERENCE_REQUIRED", required)
        self.assertIn("DEFENSIBLE_POST_RETROFIT_VENTILATION_INFERENCE_REQUIRED", required)
        self.assertIn("DEFENSIBLE_THERMAL_BRIDGE_CORRECTION_INFERENCE_REQUIRED", required)
        self.assertIn("DEFENSIBLE_NATIONAL_SUPPLY_TEMPERATURE_INFERENCE_REQUIRED", required)

    def test_service_and_transition_choices_are_model_contracts(self):
        required = set(current_requirements(SCENARIO_MODEL_CONTRACT))
        self.assertEqual(
            required,
            {
                "EXPLICIT_ACTION_GEOMETRY_RULE_REQUIRED",
                "EXPLICIT_DESIGN_INDOOR_SERVICE_SCENARIO_REQUIRED",
                "EXPLICIT_ACTION_TO_POST_STATE_MODEL_REQUIRED",
            },
        )

    def test_good_two_source_calibrated_inference_is_admissible_but_warned(self):
        out = assess_population_physical_evidence(
            PopulationPhysicalEvidence(
                evidence_class=CALIBRATED_MULTI_SOURCE_INFERENCE,
                target_population_explicit=True,
                grain_and_period_explicit=True,
                provenance_explicit=True,
                uncertainty_explicit=True,
                reproducible=True,
                calibrated_to_population_controls=True,
                independent_source_count=2,
            )
        )
        self.assertEqual(out.status, "QUALIFIED_FOR_NATIONAL_BOUNDED_PHYSICAL_INFERENCE")
        self.assertEqual(out.blockers, ())
        self.assertIn("FEWER_THAN_PREFERRED_INDEPENDENT_SOURCES", out.warnings)

    def test_multi_source_without_population_calibration_fails(self):
        out = assess_population_physical_evidence(
            PopulationPhysicalEvidence(
                evidence_class=CALIBRATED_MULTI_SOURCE_INFERENCE,
                target_population_explicit=True,
                grain_and_period_explicit=True,
                provenance_explicit=True,
                uncertainty_explicit=True,
                reproducible=True,
                calibrated_to_population_controls=False,
                independent_source_count=3,
            )
        )
        self.assertEqual(out.status, "Q")
        self.assertIn("POPULATION_CONTROL_CALIBRATION_REQUIRED", out.blockers)

    def test_engineering_validation_alone_cannot_be_population_truth(self):
        out = assess_population_physical_evidence(
            PopulationPhysicalEvidence(
                evidence_class="BOUNDED_ENGINEERING_VALIDATION",
                target_population_explicit=True,
                grain_and_period_explicit=True,
                provenance_explicit=True,
                uncertainty_explicit=True,
                reproducible=True,
            )
        )
        self.assertEqual(out.status, "Q")
        self.assertIn("ADMISSIBLE_POPULATION_EVIDENCE_CLASS_REQUIRED", out.blockers)

    def test_record_boundary_is_explicit(self):
        boundary = record_level_boundary()
        self.assertIn("POPULATION_INFERENCE_CANNOT_PASS_A_SPECIFIC_BUILDING", boundary)
        self.assertIn(
            "SPECIFIC_BUILDING_P65_SUPPLY_TEMPERATURE_REQUIRES_RECORD_LEVEL_EVIDENCE",
            boundary,
        )

    def test_registry_and_source_pack_freeze_repair(self):
        reg = rows(REG, "item_id")
        self.assertEqual(
            reg["B02-P82-R04"]["current_requirement"],
            "DEFENSIBLE_CURRENT_BASELINE_U_INFERENCE_REQUIRED",
        )
        self.assertEqual(
            reg["B02-P82-R09"]["plane"],
            "SCENARIO_MODEL_CONTRACT",
        )
        self.assertEqual(reg["B02-P82-R13"]["status"], "OPEN_NARROWED")

        text = DOC.read_text(encoding="utf-8")
        for phrase in (
            "NO FULL-POPULATION DATA != BLOCKER",
            "NO DEFENSIBLE POPULATION INFERENCE == BLOCKER",
            "POPULATION ESTIMATE != RECORD PASS/FAIL",
            "NATIONAL PHYSICAL INPUT != HOUSEHOLD POINT PHYSICAL INPUT",
        ):
            self.assertIn(phrase, text)


if __name__ == "__main__":
    unittest.main()
