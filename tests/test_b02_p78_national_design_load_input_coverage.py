import csv
import unittest
from pathlib import Path

from modules.B02.national_design_load_input_coverage import (
    EXPECTED_FULL_JOINT_ROWS,
    EXPECTED_OCCUPIED_DWELLINGS,
    MATERIALIZED_ASS_CALIBRATED,
    MATERIALIZED_OBS,
    MATERIALIZED_OBS_SET_BOUNDED,
    PARTIAL_ARCHETYPE_CALIBRATION,
    PARTIAL_CURRENT_STANDARD_ZONE_DOMAIN,
    QUALIFIED_REFERENCE_PROGRAMME_ENVELOPE_GEOMETRY_PROXY,
    QUALIFIED_REFERENCE_PROGRAMME_TARGET_SURFACE,
    QUALIFIED_SIMPLIFIED_THERMAL_BRIDGE_CORRECTION_SURFACE,
    CURRENT_METHOD_SERVICE_REFERENCE,
    Q,
    archetype_calibration_boundary,
    assess_national_post_retrofit_design_load_surface,
    current_design_load_blockers,
    national_design_load_input_coverage,
    population_surface,
)

ROOT = Path(__file__).resolve().parents[1]
REG = ROOT / "registry" / "b02_p78_national_design_load_input_coverage.csv"
P77 = ROOT / "registry" / "b02_p77_transition_response_coverage.csv"
OPEN_Q = ROOT / "registry" / "open_questions.csv"
MODULE_STATUS = ROOT / "registry" / "module_status.csv"
DOC = ROOT / "docs" / "source_packs" / "B02_P78_NATIONAL_DESIGN_LOAD_INPUT_COVERAGE.md"


def rows(path, key):
    with path.open(encoding="utf-8", newline="") as handle:
        return {row[key]: row for row in csv.DictReader(handle)}


class B02P78NationalDesignLoadInputCoverageTests(unittest.TestCase):
    def test_exact_wbl_population_surface(self):
        x = population_surface()
        self.assertEqual(x.row_count, EXPECTED_FULL_JOINT_ROWS)
        self.assertEqual(x.row_count, 116_452)
        self.assertEqual(x.occupied_dwellings, EXPECTED_OCCUPIED_DWELLINGS)
        self.assertEqual(x.occupied_dwellings, 4_008_541)
        self.assertEqual(x.materialization_status, "MATERIALIZED")
        self.assertIn("wall_material", x.grain)
        self.assertIn("floor_area", x.grain)

    def test_population_keys_are_not_promoted_to_physics(self):
        by = {item.input_id: item for item in national_design_load_input_coverage()}
        self.assertEqual(by["GEOGRAPHY_SETTLEMENT"].status, MATERIALIZED_OBS)
        self.assertEqual(by["CONSTRUCTION_PERIOD"].status, MATERIALIZED_OBS)
        self.assertEqual(by["WALL_MATERIAL_CATEGORY"].status, MATERIALIZED_OBS)
        self.assertEqual(
            by["DWELLING_FLOOR_AREA_BAND"].status,
            MATERIALIZED_OBS_SET_BOUNDED,
        )
        self.assertEqual(by["BUILDING_TYPE"].status, MATERIALIZED_ASS_CALIBRATED)
        self.assertEqual(
            by["POST_RETROFIT_ENVELOPE_GEOMETRY"].status,
            QUALIFIED_REFERENCE_PROGRAMME_ENVELOPE_GEOMETRY_PROXY,
        )
        self.assertEqual(by["POST_RETROFIT_COMPONENT_U_VALUES"].status, Q)
        self.assertEqual(
            by["DESIGN_OUTDOOR_TEMPERATURE"].status,
            PARTIAL_CURRENT_STANDARD_ZONE_DOMAIN,
        )
        self.assertEqual(
            by["DESIGN_OUTDOOR_TEMPERATURE"].blocker,
            "COMPLETE_LOCATION_TO_CURRENT_STANDARD_ZONE_MAPPING_REQUIRED",
        )

    def test_hungarian_archetype_layer_is_calibration_not_post_state(self):
        b = archetype_calibration_boundary()
        self.assertEqual(b["keop_survey_buildings"], 2029)
        self.assertEqual(b["synthetic_average_building_types"], 23)
        self.assertEqual(b["single_family_types"], 12)
        self.assertEqual(b["multi_family_types"], 11)
        self.assertEqual(b["type5_heated_floor_area_m2"], 103.4)
        self.assertIn(
            "2015_SYNTHETIC_AVERAGE_TO_2026_POST_RETROFIT_OBSERVATION",
            b["forbidden_promotions"],
        )

    def test_ventilation_and_thermal_bridge_reference_inputs_are_qualified(self):
        by = {item.input_id: item for item in national_design_load_input_coverage()}
        self.assertEqual(
            by["POST_RETROFIT_VENTILATION"].status,
            QUALIFIED_REFERENCE_PROGRAMME_TARGET_SURFACE,
        )
        self.assertEqual(
            by["DESIGN_INDOOR_TEMPERATURE"].status,
            CURRENT_METHOD_SERVICE_REFERENCE,
        )
        self.assertEqual(
            by["POST_RETROFIT_THERMAL_BRIDGE_H"].status,
            QUALIFIED_SIMPLIFIED_THERMAL_BRIDGE_CORRECTION_SURFACE,
        )
        self.assertIsNone(by["POST_RETROFIT_THERMAL_BRIDGE_H"].blocker)

    def test_current_blockers_are_field_level_and_fail_closed(self):
        blockers = current_design_load_blockers()
        expected = {
            "HEATED_AREA_OR_DIRECT_GEOMETRY_SURFACE_REQUIRED",
            "POST_RETROFIT_COMPONENT_U_VALUE_SURFACE_REQUIRED",
            "COMPLETE_LOCATION_TO_CURRENT_STANDARD_ZONE_MAPPING_REQUIRED",
            "ACTION_TO_POST_STATE_PHYSICAL_MAPPING_REQUIRED",
        }
        self.assertEqual(set(blockers), expected)
        d = assess_national_post_retrofit_design_load_surface()
        self.assertEqual(d.status, "PARTIAL_RESOLVED_INPUT_COVERAGE_DECOMPOSED")
        self.assertEqual(set(d.blockers), expected)

    def test_complete_supply_only_qualifies_materialization(self):
        supplied = set(current_design_load_blockers())
        d = assess_national_post_retrofit_design_load_surface(supplied)
        self.assertEqual(d.status, "QUALIFIED_FOR_B06_DESIGN_LOAD_MATERIALIZATION")
        self.assertEqual(d.blockers, ())

    def test_registry_records_decomposition(self):
        reg = rows(REG, "item_id")
        self.assertEqual(
            reg["B02-P78-D14"]["status"],
            "PARTIAL_RESOLVED_INPUT_COVERAGE_DECOMPOSED",
        )
        self.assertIn(
            "POST_RETROFIT_ENVELOPE_GEOMETRY_SURFACE_REQUIRED",
            reg["B02-P78-D14"]["residual_gap"],
        )
        self.assertEqual(
            reg["B02-P78-D05"]["lower_bound"],
            "23",
        )

    def test_p77_current_state_is_superseded(self):
        p77 = rows(P77, "item_id")
        self.assertEqual(
            p77["B02-P77-R10"]["status"],
            "SUPERSEDED_BY_P78_CURRENT_STATE",
        )

    def test_q_and_module_readiness(self):
        q = rows(OPEN_Q, "question_id")["Q-B02-004"]
        self.assertEqual(q["status"], "OPEN")
        self.assertIn("B02-P78", q["notes"])
        self.assertIn(
            "POST_RETROFIT_THERMAL_BRIDGE_SURFACE_REQUIRED",
            q["notes"],
        )
        b02 = rows(MODULE_STATUS, "module_id")["B02"]
        self.assertEqual(b02["readiness_percent"], "55")
        self.assertIn("B02-P78", b02["gate_note"])

    def test_document_preserves_nonpromotion_boundaries(self):
        text = DOC.read_text(encoding="utf-8")
        for phrase in (
            "NATIONAL POPULATION KEY COVERAGE != PHYSICAL STATE PARAMETERIZATION",
            "WBL FLOOR-AREA BAND != HEATED FLOOR-AREA POINT",
            "WALL-MATERIAL CATEGORY != COMPONENT U-VALUE",
            "ANNUAL ENERGY -> DESIGN PEAK",
        ):
            self.assertIn(phrase, text)


if __name__ == "__main__":
    unittest.main()
