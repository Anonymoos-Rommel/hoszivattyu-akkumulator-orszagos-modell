import csv
import unittest
from pathlib import Path

from modules.B02.post_retrofit_ventilation_path import (
    ALLOWED_POST_RETROFIT_VENTILATION_PATHS,
    MECHANICAL_EXHAUST_WITH_AIR_INLETS,
    MECHANICAL_HEAT_RECOVERY,
    NATURAL_WINDOW,
    fourteen_stratum_response_coefficients,
    hrv_recovered_h_w_per_k,
    response_envelope_state,
    semantic_boundaries,
    ventilation_design_load_kw,
    ventilation_path_h_w_per_k,
)
from modules.B02.national_design_load_input_coverage import (
    current_design_load_blockers,
    national_design_load_input_coverage,
)


ROOT = Path(__file__).resolve().parents[1]
SURFACE = ROOT / "data" / "processed" / "b02" / "p88_ventilation_path_response_coefficients.csv"
REG = ROOT / "registry" / "b02_p88_ventilation_path_response.csv"
QUESTIONS = ROOT / "registry" / "open_questions.csv"
MODULES = ROOT / "registry" / "module_status.csv"
READINESS = ROOT / "registry" / "retrofit_readiness.csv"
SOURCES = ROOT / "registry" / "sources.csv"
DOC = ROOT / "docs" / "source_packs" / "B02_P88_VENTILATION_PATH_RESPONSE.md"


def rows(path, key=None):
    with path.open(encoding="utf-8", newline="") as handle:
        data = list(csv.DictReader(handle))
    if key is None:
        return data
    return {row[key]: row for row in data}


class B02P88VentilationPathResponseTests(unittest.TestCase):
    def test_exact_allowed_post_retrofit_paths(self):
        self.assertEqual(
            ALLOWED_POST_RETROFIT_VENTILATION_PATHS,
            (
                NATURAL_WINDOW,
                MECHANICAL_EXHAUST_WITH_AIR_INLETS,
                MECHANICAL_HEAT_RECOVERY,
            ),
        )

    def test_no_heat_recovery_paths_have_same_sensible_response(self):
        natural = ventilation_path_h_w_per_k(
            path=NATURAL_WINDOW,
            volume_m3=200.0,
            infiltration_air_change_h=0.1,
        )
        exhaust = ventilation_path_h_w_per_k(
            path=MECHANICAL_EXHAUST_WITH_AIR_INLETS,
            volume_m3=200.0,
            infiltration_air_change_h=0.1,
        )
        self.assertAlmostEqual(natural.required_air_h_w_per_k, 35.0)
        self.assertAlmostEqual(natural.infiltration_h_w_per_k, 7.0)
        self.assertAlmostEqual(natural.h_vent_w_per_k, 42.0)
        self.assertAlmostEqual(exhaust.h_vent_w_per_k, 42.0)
        self.assertEqual(natural.recovered_h_w_per_k, 0.0)
        self.assertEqual(exhaust.recovered_h_w_per_k, 0.0)

    def test_hrv_eta_reduces_only_required_air_term(self):
        result = ventilation_path_h_w_per_k(
            path=MECHANICAL_HEAT_RECOVERY,
            volume_m3=200.0,
            infiltration_air_change_h=0.1,
            heat_recovery_efficiency=0.8,
        )
        self.assertAlmostEqual(result.required_air_h_w_per_k, 35.0)
        self.assertAlmostEqual(result.infiltration_h_w_per_k, 7.0)
        self.assertAlmostEqual(result.recovered_h_w_per_k, 28.0)
        self.assertAlmostEqual(result.h_vent_w_per_k, 14.0)
        self.assertAlmostEqual(
            hrv_recovered_h_w_per_k(
                volume_m3=200.0,
                heat_recovery_efficiency=0.8,
            ),
            28.0,
        )
        self.assertAlmostEqual(
            ventilation_design_load_kw(
                h_vent_w_per_k=result.h_vent_w_per_k,
                indoor_temperature_c=20.0,
                outdoor_temperature_c=-12.0,
            ),
            0.448,
        )

    def test_hrv_fails_closed_without_valid_eta(self):
        with self.assertRaises(ValueError):
            ventilation_path_h_w_per_k(
                path=MECHANICAL_HEAT_RECOVERY,
                volume_m3=200.0,
                infiltration_air_change_h=0.1,
            )
        with self.assertRaises(ValueError):
            ventilation_path_h_w_per_k(
                path=MECHANICAL_HEAT_RECOVERY,
                volume_m3=200.0,
                infiltration_air_change_h=0.1,
                heat_recovery_efficiency=1.01,
            )
        with self.assertRaises(ValueError):
            ventilation_path_h_w_per_k(
                path=NATURAL_WINDOW,
                volume_m3=200.0,
                infiltration_air_change_h=0.1,
                heat_recovery_efficiency=0.8,
            )

    def test_fourteen_stratum_response_coefficients_are_materialized(self):
        surface = fourteen_stratum_response_coefficients()
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
        state = response_envelope_state()
        self.assertAlmostEqual(
            state["required_air_h_global_lower_w_per_k"],
            25.431534722,
        )
        self.assertAlmostEqual(
            state["required_air_h_global_upper_w_per_k"],
            110.4705,
        )
        self.assertAlmostEqual(
            state["infiltration_h_global_upper_w_per_k"],
            220.941,
        )
        self.assertFalse(state["population_prevalence_required_for_response_engine"])
        self.assertFalse(
            state["heat_recovery_efficiency_population_distribution_required"]
        )
        self.assertEqual(
            state["remaining_physical_residual"],
            "ACTION_CONDITIONED_POST_RETROFIT_INFILTRATION_REQUIRED",
        )

    def test_materialized_csv_matches_runtime_coefficients(self):
        data = rows(SURFACE)
        runtime = fourteen_stratum_response_coefficients()
        self.assertEqual(len(data), 14)
        self.assertEqual(len(runtime), 14)
        self.assertAlmostEqual(
            min(float(row["required_air_h_lower_w_per_k"]) for row in data),
            25.431534722,
        )
        self.assertAlmostEqual(
            max(float(row["required_air_h_upper_w_per_k"]) for row in data),
            110.4705,
        )
        self.assertAlmostEqual(
            max(float(row["infiltration_h_upper_w_per_k"]) for row in data),
            220.941,
        )
        self.assertEqual(
            {row["status"] for row in data},
            {"MATERIALIZED_HRV_RESPONSE_COEFFICIENT"},
        )

    def test_current_design_load_blocker_is_only_infiltration_for_ventilation(self):
        by = {item.input_id: item for item in national_design_load_input_coverage()}
        vent = by["POST_RETROFIT_VENTILATION"]
        self.assertEqual(
            vent.blocker,
            "ACTION_CONDITIONED_POST_RETROFIT_INFILTRATION_REQUIRED",
        )
        self.assertIn("B02-P88", vent.source_refs)
        blockers = set(current_design_load_blockers())
        self.assertIn(
            "ACTION_CONDITIONED_POST_RETROFIT_INFILTRATION_REQUIRED",
            blockers,
        )
        self.assertNotIn(
            "POST_RETROFIT_AIRTIGHTNESS_AND_HRV_PREVALENCE_REQUIRED",
            blockers,
        )

    def test_registry_and_readiness_state(self):
        reg = rows(REG, "item_id")
        self.assertEqual(
            reg["B02-P88-V06"]["status"],
            "RETIRED_AS_SCENARIO_OR_PROJECT_STATE",
        )
        self.assertEqual(
            reg["B02-P88-V07"]["status"],
            "RETIRED_AS_PROJECT_PROCUREMENT_INPUT",
        )
        self.assertEqual(
            reg["B02-P88-V09"]["status"],
            "PARTIAL_RESOLVED_PATH_RESPONSE",
        )

        q = rows(QUESTIONS, "question_id")["Q-B02-004"]
        self.assertEqual(q["status"], "OPEN")
        self.assertIn("B02-P88", q["notes"])
        self.assertIn(
            "ACTION_CONDITIONED_POST_RETROFIT_INFILTRATION_REQUIRED",
            q["notes"],
        )

        module = rows(MODULES, "module_id")["B02"]
        self.assertEqual(module["readiness_percent"], "55")
        self.assertIn("B02-P88", module["gate_note"])

        readiness = rows(READINESS, "component_id")["PEAK_LOAD_EFFECT"]
        self.assertEqual(readiness["readiness_percent"], "50")
        self.assertIn("B02-P88", readiness["notes"])

    def test_source_authorities_and_nonpromotion_boundaries(self):
        sources = rows(SOURCES, "source_id")
        self.assertIn(
            "SRC-B02-EU-ECODESIGN-VENTILATION-1253-2014",
            sources,
        )
        self.assertIn(
            "thermal efficiency",
            sources["SRC-B02-EU-ECODESIGN-VENTILATION-1253-2014"]["notes"],
        )
        self.assertIn(
            "P88 section 2.8 authority",
            sources["SRC-B06-HU-EKR-18-2025"]["notes"],
        )

        boundaries = semantic_boundaries()
        self.assertIn(
            "WINDOW_OR_ENVELOPE_ACTION_DOES_NOT_PROVE_POST_RETROFIT_INFILTRATION",
            boundaries,
        )
        self.assertIn(
            "HRV_ETA_IS_PROJECT_OR_PROCUREMENT_EVIDENCE_NOT_POPULATION_DISTRIBUTION",
            boundaries,
        )

        text = DOC.read_text(encoding="utf-8")
        for phrase in (
            "POST-RETROFIT VENTILATION PATH != OBSERVED NATIONAL PREVALENCE",
            "PRODUCT-DECLARED ETA != INSTALLED/COMMISSIONED PERFORMANCE",
            "B02 remains **55%**",
            "PEAK_LOAD_EFFECT",
            "remains **50%**",
        ):
            self.assertIn(phrase, text)


if __name__ == "__main__":
    unittest.main()
