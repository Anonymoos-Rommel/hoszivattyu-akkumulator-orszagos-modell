import csv
import unittest
from pathlib import Path

from modules.B02.bounded_physical_state_surface import (
    GEOMETRY_RULE,
    POST_STATE_RULE,
    SUPPORTED_COMPONENTS,
    action_model_contract_status,
    bounded_reference_retrofit_state,
    explicit_design_service_scenario,
    record_level_boundary,
)
from modules.B02.keop23_wbl_crosswalk import GROUPS, WBL_PERIOD_INTERVALS


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "processed" / "b02" / "p83_bounded_reference_retrofit_surface.csv"
REG = ROOT / "registry" / "b02_p83_bounded_physical_state_surface.csv"
DOC = ROOT / "docs" / "source_packs" / "B02_P83_BOUNDED_PHYSICAL_STATE_SURFACE.md"


def rows(path, key):
    with path.open(encoding="utf-8", newline="") as handle:
        return {row[key]: row for row in csv.DictReader(handle)}


class B02P83BoundedPhysicalStateSurfaceTests(unittest.TestCase):
    def test_all_14_period_group_strata_are_executable(self):
        states = [
            bounded_reference_retrofit_state(period, group)
            for period in WBL_PERIOD_INTERVALS
            for group in GROUPS
        ]
        self.assertEqual(len(states), 14)
        self.assertTrue(all(x.status == "PARTIAL_MATERIALIZED_BOUNDED_POST_STATE" for x in states))
        self.assertTrue(all(x.geometry_rule == GEOMETRY_RULE for x in states))
        self.assertTrue(all(x.post_state_rule == POST_STATE_RULE for x in states))
        self.assertTrue(all(x.candidate_type_ids for x in states))
        self.assertTrue(
            all(
                x.heated_floor_area_lower_m2_per_dwelling
                <= x.heated_floor_area_upper_m2_per_dwelling
                for x in states
            )
        )

    def test_reference_u_constraints_are_exactly_the_p80_supported_set(self):
        state = bounded_reference_retrofit_state("Y_GE2011", "FAMILY_HOUSE")
        values = dict(state.u_upper_bounds_w_m2k)
        self.assertEqual(set(values), set(SUPPORTED_COMPONENTS))
        self.assertEqual(
            values,
            {
                "EXTERNAL_WALL": 0.24,
                "FLAT_ROOF": 0.17,
                "ATTIC_FLOOR": 0.17,
                "BASEMENT_CEILING": 0.26,
                "WINDOW": 1.15,
            },
        )
        self.assertIn("PITCHED_ROOF_POSTSTATE_U_BOUND_REQUIRED", state.residuals)

    def test_materialized_csv_matches_executable_surface(self):
        with DATA.open(encoding="utf-8", newline="") as handle:
            data = list(csv.DictReader(handle))
        self.assertEqual(len(data), 14)

        keyed = {(r["wbl_period_code"], r["building_group"]): r for r in data}
        self.assertEqual(len(keyed), 14)

        for period in WBL_PERIOD_INTERVALS:
            for group in GROUPS:
                state = bounded_reference_retrofit_state(period, group)
                row = keyed[(period, group)]
                self.assertEqual(
                    row["candidate_type_ids"],
                    ";".join(str(x) for x in state.candidate_type_ids),
                )
                self.assertAlmostEqual(
                    float(row["heated_floor_area_lower_m2_per_dwelling"]),
                    state.heated_floor_area_lower_m2_per_dwelling,
                )
                self.assertAlmostEqual(
                    float(row["heated_floor_area_upper_m2_per_dwelling"]),
                    state.heated_floor_area_upper_m2_per_dwelling,
                )
                self.assertEqual(row["geometry_rule"], GEOMETRY_RULE)
                self.assertEqual(row["pitched_roof_u_status"], "Q")

    def test_three_p82_model_contract_requirements_are_implemented(self):
        status = action_model_contract_status()
        self.assertEqual(
            status,
            {
                "EXPLICIT_ACTION_GEOMETRY_RULE_REQUIRED": "CONTRACTED",
                "EXPLICIT_ACTION_TO_POST_STATE_MODEL_REQUIRED": "CONTRACTED",
                "EXPLICIT_DESIGN_INDOOR_SERVICE_SCENARIO_REQUIRED": "CONTRACTED_EXPLICIT_INPUT",
            },
        )

    def test_design_indoor_temperature_is_explicit_not_defaulted(self):
        scenario = explicit_design_service_scenario(20.0)
        self.assertEqual(scenario.design_indoor_temperature_c, 20.0)
        with self.assertRaises(ValueError):
            explicit_design_service_scenario(80.0)

    def test_record_level_boundary_is_preserved(self):
        boundary = record_level_boundary()
        self.assertIn("P83_SURFACE_CANNOT_PASS_A_SPECIFIC_BUILDING", boundary)
        self.assertIn(
            "SPECIFIC_BUILDING_DESIGN_LOAD_STILL_REQUIRES_COMPLETE_RECORD_INPUTS",
            boundary,
        )

    def test_registry_keeps_complete_design_load_q(self):
        reg = rows(REG, "item_id")
        self.assertEqual(reg["B02-P83-S01"]["status"], "MATERIALIZED")
        self.assertEqual(reg["B02-P83-S12"]["status"], "Q")
        self.assertIn(
            "DEFENSIBLE_COMPONENT_AREA_GEOMETRY_INFERENCE_REQUIRED",
            reg["B02-P83-S12"]["residual_gap"],
        )
        self.assertEqual(reg["B02-P83-S13"]["status"], "OPEN_NARROWED")

    def test_document_freezes_nonpromotion_boundaries(self):
        text = DOC.read_text(encoding="utf-8")
        for phrase in (
            "POPULATION SURFACE != HOUSEHOLD DESIGN INPUT",
            "REFERENCE RETROFIT U-MAX != REALIZED HOUSEHOLD U",
            "SET-VALUED GEOMETRY != HOUSEHOLD GEOMETRY",
            "B02 readiness remains 55%",
        ):
            self.assertIn(phrase, text)


if __name__ == "__main__":
    unittest.main()
