import csv
import unittest
from pathlib import Path

from modules.B02.reference_programme_thermal_bridge_correction import (
    ATTIC_FLOOR,
    BASEMENT_CEILING,
    DETAILED_THERMAL_BRIDGE_MODEL_REQUIRED,
    EXTERNAL_WALL,
    FLAT_ROOF,
    INTERNAL_INSULATION,
    NON_INTERNAL_INSULATION,
    PITCHED_ROOF,
    QUALIFIED_SIMPLIFIED_ZETA_CORRECTION_SURFACE,
    REALIZED_THERMAL_BRIDGE_VERIFICATION_REQUIRED,
    WINDOW,
    corrected_u_w_m2k,
    equivalent_thermal_bridge_h_w_per_k,
    p91_state,
    reference_component_correction,
    reference_programme_thermal_bridge_surface,
    semantic_boundaries,
    zeta_bound,
)
from modules.B02.national_design_load_input_coverage import (
    QUALIFIED_SIMPLIFIED_THERMAL_BRIDGE_CORRECTION_SURFACE as COVERAGE_STATUS,
    current_design_load_blockers,
    national_design_load_input_coverage,
)


ROOT = Path(__file__).resolve().parents[1]
SURFACE = ROOT / "data" / "processed" / "b02" / "p91_reference_programme_thermal_bridge_correction.csv"
REG = ROOT / "registry" / "b02_p91_reference_programme_thermal_bridge_correction.csv"
QUESTIONS = ROOT / "registry" / "open_questions.csv"
MODULES = ROOT / "registry" / "module_status.csv"
READINESS = ROOT / "registry" / "retrofit_readiness.csv"
SOURCES = ROOT / "registry" / "sources.csv"
DOC = ROOT / "docs" / "source_packs" / "B02_P91_REFERENCE_PROGRAMME_THERMAL_BRIDGE_CORRECTION.md"


def rows(path, key=None):
    with path.open(encoding="utf-8", newline="") as handle:
        data = list(csv.DictReader(handle))
    if key is None:
        return data
    return {row[key]: row for row in data}


class B02P91ReferenceProgrammeThermalBridgeTests(unittest.TestCase):
    def test_current_method_zeta_envelopes_are_exact(self):
        wall = zeta_bound(EXTERNAL_WALL)
        self.assertEqual((wall.lower, wall.upper), (0.15, 0.40))
        self.assertEqual(wall.status, QUALIFIED_SIMPLIFIED_ZETA_CORRECTION_SURFACE)

        flat = zeta_bound(FLAT_ROOF)
        self.assertEqual((flat.lower, flat.upper), (0.10, 0.20))

        attic = zeta_bound(ATTIC_FLOOR)
        self.assertEqual((attic.lower, attic.upper), (0.10, 0.10))

        basement = zeta_bound(BASEMENT_CEILING)
        self.assertEqual((basement.lower, basement.upper), (0.10, 0.20))

        pitched = zeta_bound(PITCHED_ROOF)
        self.assertEqual((pitched.lower, pitched.upper), (0.10, 0.20))

    def test_internal_insulation_fails_closed_to_detailed_method(self):
        bound = zeta_bound(
            EXTERNAL_WALL,
            insulation_position=INTERNAL_INSULATION,
        )
        self.assertEqual(bound.status, "Q_DETAILED_METHOD_REQUIRED")
        self.assertEqual(bound.blocker, DETAILED_THERMAL_BRIDGE_MODEL_REQUIRED)
        self.assertIsNone(bound.lower)
        self.assertIsNone(bound.upper)

        with self.assertRaises(ValueError):
            zeta_bound(EXTERNAL_WALL, insulation_position="UNKNOWN_POSITION")

    def test_window_gets_no_additional_generic_zeta(self):
        window = zeta_bound(WINDOW, insulation_position=NON_INTERNAL_INSULATION)
        self.assertEqual(window.status, "NO_SEPARATE_GENERIC_ZETA")
        self.assertIsNone(window.lower)
        self.assertIsNone(window.upper)
        self.assertIsNone(window.blocker)

        correction = reference_component_correction(WINDOW)
        self.assertEqual(correction.delta_u_upper_w_m2k, 0.0)
        self.assertAlmostEqual(correction.corrected_u_upper_w_m2k, 1.15)

    def test_equivalent_separate_h_matches_corrected_u_form(self):
        area = 100.0
        u = 0.24
        zeta = 0.40

        direct = area * corrected_u_w_m2k(base_u_w_m2k=u, zeta=zeta)
        base = area * u
        bridge = equivalent_thermal_bridge_h_w_per_k(
            area_m2=area,
            base_u_w_m2k=u,
            zeta=zeta,
        )
        self.assertAlmostEqual(direct, 33.6)
        self.assertAlmostEqual(base, 24.0)
        self.assertAlmostEqual(bridge, 9.6)
        self.assertAlmostEqual(base + bridge, direct)

    def test_reference_component_corrected_u_upper_sensitivities(self):
        wall = reference_component_correction(EXTERNAL_WALL)
        flat = reference_component_correction(FLAT_ROOF)
        attic = reference_component_correction(ATTIC_FLOOR)
        basement = reference_component_correction(BASEMENT_CEILING)
        pitched = reference_component_correction(PITCHED_ROOF)

        self.assertAlmostEqual(wall.corrected_u_upper_w_m2k, 0.336)
        self.assertAlmostEqual(wall.delta_u_upper_w_m2k, 0.096)
        self.assertAlmostEqual(flat.corrected_u_upper_w_m2k, 0.204)
        self.assertAlmostEqual(attic.corrected_u_upper_w_m2k, 0.187)
        self.assertAlmostEqual(basement.corrected_u_upper_w_m2k, 0.312)

        self.assertEqual(pitched.status, "PARTIAL_ZETA_KNOWN_U_BOUND_Q")
        self.assertEqual(
            pitched.blocker,
            "PITCHED_ROOF_POSTSTATE_U_BOUND_REQUIRED",
        )
        self.assertIsNone(pitched.corrected_u_upper_w_m2k)

    def test_fourteen_stratum_surface_is_materialized(self):
        surface = reference_programme_thermal_bridge_surface()
        self.assertEqual(len(surface), 14)
        self.assertEqual(
            {(row.wbl_period_code, row.building_group) for row in surface},
            {
                (period, group)
                for period in (
                    "Y_LT1919",
                    "Y1919-1945",
                    "Y1946-1960",
                    "Y1961-1980",
                    "Y1981-2000",
                    "Y2001-2010",
                    "Y_GE2011",
                )
                for group in ("FAMILY_HOUSE", "MULTI_DWELLING")
            },
        )
        self.assertEqual(
            {row.status for row in surface},
            {QUALIFIED_SIMPLIFIED_ZETA_CORRECTION_SURFACE},
        )

    def test_materialized_csv_matches_runtime_surface(self):
        data = rows(SURFACE)
        self.assertEqual(len(data), 14)
        self.assertEqual(
            {float(row["external_wall_zeta_lower"]) for row in data},
            {0.15},
        )
        self.assertEqual(
            {float(row["external_wall_zeta_upper"]) for row in data},
            {0.40},
        )
        self.assertEqual(
            {float(row["external_wall_corrected_u_upper_w_m2k"]) for row in data},
            {0.336},
        )
        self.assertEqual(
            {float(row["flat_roof_corrected_u_upper_w_m2k"]) for row in data},
            {0.204},
        )
        self.assertEqual(
            {row["pitched_roof_u_status"] for row in data},
            {"Q"},
        )

    def test_current_design_load_coverage_removes_independent_bridge_blocker(self):
        by = {item.input_id: item for item in national_design_load_input_coverage()}
        bridge = by["POST_RETROFIT_THERMAL_BRIDGE_H"]
        self.assertEqual(bridge.status, COVERAGE_STATUS)
        self.assertIsNone(bridge.blocker)
        self.assertIn("B02-P91", bridge.source_refs)

        blockers = set(current_design_load_blockers())
        self.assertNotIn("POST_RETROFIT_THERMAL_BRIDGE_SURFACE_REQUIRED", blockers)
        self.assertNotIn("POST_RETROFIT_ENVELOPE_GEOMETRY_SURFACE_REQUIRED", blockers)
        self.assertIn("POST_RETROFIT_COMPONENT_U_VALUE_SURFACE_REQUIRED", blockers)

    def test_p91_state_preserves_independent_dependencies(self):
        state = p91_state()
        self.assertEqual(state["stratum_count"], 14)
        self.assertEqual(
            state["reference_programme_thermal_bridge_status"],
            QUALIFIED_SIMPLIFIED_ZETA_CORRECTION_SURFACE,
        )
        self.assertIsNone(state["reference_programme_thermal_bridge_blocker"])
        self.assertEqual(
            state["independent_geometry_dependency"],
            "COMPONENT_AREA_GEOMETRY_SURFACE_REQUIRED",
        )
        self.assertEqual(
            state["pitched_roof_dependency"],
            "PITCHED_ROOF_POSTSTATE_U_BOUND_REQUIRED",
        )
        self.assertEqual(
            state["realized_claim_residual"],
            REALIZED_THERMAL_BRIDGE_VERIFICATION_REQUIRED,
        )

    def test_registry_and_readiness_remain_conservative(self):
        reg = rows(REG, "item_id")
        self.assertEqual(
            reg["B02-P91-T11"]["status"],
            "RESOLVED_FOR_REFERENCE_PROGRAMME_SIMPLIFIED_ROUTE",
        )
        self.assertEqual(
            reg["B02-P91-T12"]["status"],
            "RECORD_LEVEL_RESIDUAL",
        )

        q = rows(QUESTIONS, "question_id")["Q-B02-004"]
        self.assertEqual(q["status"], "OPEN")
        self.assertIn("B02-P91", q["notes"])
        self.assertIn(
            "RESOLVED_FOR_REFERENCE_PROGRAMME_SIMPLIFIED_ROUTE",
            q["notes"],
        )

        module = rows(MODULES, "module_id")["B02"]
        self.assertEqual(module["readiness_percent"], "55")
        self.assertIn("B02-P91", module["gate_note"])

        peak = rows(READINESS, "component_id")["PEAK_LOAD_EFFECT"]
        self.assertEqual(peak["readiness_percent"], "50")
        self.assertIn("B02-P91", peak["notes"])

    def test_current_method_source_and_boundaries_are_frozen(self):
        sources = rows(SOURCES, "source_id")
        self.assertIn(
            "P91 thermal-bridge authority",
            sources["SRC-B06-HU-ENERGY-METHOD-2023"]["notes"],
        )

        boundary = semantic_boundaries()
        for item in (
            "SIMPLIFIED_ZETA_ROUTE_IS_NOT_DETAILED_PSI_CHI_ROUTE",
            "REFERENCE_PROGRAMME_ZETA_IS_NOT_OBSERVED_THERMAL_BRIDGE_DISTRIBUTION",
            "INTERNAL_INSULATION_REQUIRES_DETAILED_THERMAL_BRIDGE_METHOD",
            "NO_DOUBLE_COUNT_IF_COMPONENT_U_ALREADY_INCLUDES_BRIDGE_EFFECT",
            "THERMAL_BRIDGE_CORRECTION_FACTOR_IS_NOT_COMPONENT_AREA_GEOMETRY",
            "PITCHED_ROOF_ZETA_KNOWN_DOES_NOT_RESOLVE_PITCHED_ROOF_U",
        ):
            self.assertIn(item, boundary)

        text = DOC.read_text(encoding="utf-8")
        for phrase in (
            "SIMPLIFIED ZETA ROUTE != DETAILED PSI/CHI ROUTE",
            "INTERNAL INSULATION != ZETA-ELIGIBLE",
            "B02 remains **55%**",
            "Q-B02-004",
        ):
            self.assertIn(phrase, text)


if __name__ == "__main__":
    unittest.main()
