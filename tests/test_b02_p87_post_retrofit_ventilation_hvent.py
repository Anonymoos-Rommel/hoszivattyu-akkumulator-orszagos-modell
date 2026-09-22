import csv
import unittest
from pathlib import Path

from modules.B02.post_retrofit_ventilation_hvent import (
    AIR_VOLUMETRIC_HEAT_CAPACITY_WH_M3K,
    RESIDENTIAL_REQUIRED_AIR_CHANGE_H,
    OFFICIAL_INFILTRATION_MIN_H,
    OFFICIAL_INFILTRATION_MAX_H,
    GOOD_AIRTIGHTNESS_INFILTRATION_MIN_H,
    GOOD_AIRTIGHTNESS_INFILTRATION_MAX_H,
    BME_TYPE5_VENTILATION_MIN_H,
    BME_TYPE5_VENTILATION_MAX_H,
    BME_TYPE5_INFILTRATION_MEAN_H,
    BME_TYPE5_INFILTRATION_STD_H,
    current_method_ventilation_surface,
    good_airtightness_sensitivity_surface,
    semantic_boundaries,
    type5_empirical_calibration,
    ventilation_h_w_per_k,
    ventilation_state,
)
from modules.B02.national_design_load_input_coverage import (
    CURRENT_METHOD_SERVICE_REFERENCE,
    PARTIAL_CURRENT_METHOD_HVENT_SURFACE,
    current_design_load_blockers,
    national_design_load_input_coverage,
)


ROOT = Path(__file__).resolve().parents[1]
SURFACE = ROOT / "data" / "processed" / "b02" / "p87_post_retrofit_ventilation_hvent_surface.csv"
REG = ROOT / "registry" / "b02_p87_post_retrofit_ventilation_hvent.csv"
QUESTIONS = ROOT / "registry" / "open_questions.csv"
MODULES = ROOT / "registry" / "module_status.csv"
SOURCES = ROOT / "registry" / "sources.csv"
DOC = ROOT / "docs" / "source_packs" / "B02_P87_POST_RETROFIT_VENTILATION_HVENT.md"


def rows(path, key=None):
    with path.open(encoding="utf-8", newline="") as handle:
        data = list(csv.DictReader(handle))
    if key is None:
        return data
    return {row[key]: row for row in data}


class B02P87PostRetrofitVentilationHventTests(unittest.TestCase):
    def test_current_method_constants_are_exact(self):
        self.assertEqual(AIR_VOLUMETRIC_HEAT_CAPACITY_WH_M3K, 0.35)
        self.assertEqual(RESIDENTIAL_REQUIRED_AIR_CHANGE_H, 0.5)
        self.assertEqual(OFFICIAL_INFILTRATION_MIN_H, 0.0)
        self.assertEqual(OFFICIAL_INFILTRATION_MAX_H, 1.0)
        self.assertEqual(GOOD_AIRTIGHTNESS_INFILTRATION_MIN_H, 0.03)
        self.assertEqual(GOOD_AIRTIGHTNESS_INFILTRATION_MAX_H, 0.06)

    def test_bme_type5_calibration_is_preserved_as_calibration_only(self):
        self.assertEqual(BME_TYPE5_VENTILATION_MIN_H, 0.110)
        self.assertEqual(BME_TYPE5_VENTILATION_MAX_H, 0.860)
        self.assertEqual(BME_TYPE5_INFILTRATION_MEAN_H, 0.280)
        self.assertEqual(BME_TYPE5_INFILTRATION_STD_H, 0.100)
        calibration = type5_empirical_calibration()
        self.assertEqual(calibration["status"], "TYPE5_EMPIRICAL_CALIBRATION_ONLY")

    def test_fourteen_stratum_current_method_surface(self):
        surface = current_method_ventilation_surface()
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
        for row in surface:
            expected_lo = ventilation_h_w_per_k(
                volume_m3=row.heated_volume_lower_m3_per_dwelling,
                required_air_change_h=0.5,
                infiltration_air_change_h=0.0,
            )
            expected_hi = ventilation_h_w_per_k(
                volume_m3=row.heated_volume_upper_m3_per_dwelling,
                required_air_change_h=0.5,
                infiltration_air_change_h=1.0,
            )
            self.assertAlmostEqual(row.h_vent_lower_w_per_k, expected_lo)
            self.assertAlmostEqual(row.h_vent_upper_w_per_k, expected_hi)
            self.assertEqual(
                row.status,
                "BOUNDED_CURRENT_METHOD_NATURAL_VENTILATION_HVENT",
            )

    def test_materialized_surface_matches_expected_global_edges(self):
        data = rows(SURFACE)
        self.assertEqual(len(data), 14)
        h_lo = min(float(row["current_method_hvent_lower_w_per_k"]) for row in data)
        h_hi = max(float(row["current_method_hvent_upper_w_per_k"]) for row in data)
        q_lo = min(float(row["current_method_qvent_lower_kw"]) for row in data)
        q_hi = max(float(row["current_method_qvent_upper_kw"]) for row in data)
        self.assertAlmostEqual(h_lo, 25.431534722)
        self.assertAlmostEqual(h_hi, 331.4115)
        self.assertAlmostEqual(q_lo, 0.762946042)
        self.assertAlmostEqual(q_hi, 10.605168)
        self.assertEqual(
            {row["status"] for row in data},
            {"BOUNDED_CURRENT_METHOD_NATURAL_VENTILATION_HVENT"},
        )
        self.assertTrue(
            all("not a population probability interval" in row["notes"] for row in data)
        )

    def test_good_airtightness_is_sensitivity_only(self):
        surface = good_airtightness_sensitivity_surface()
        self.assertEqual(len(surface), 14)
        self.assertEqual(
            {row.status for row in surface},
            {"GOOD_AIRTIGHTNESS_SENSITIVITY_ONLY"},
        )
        data = rows(SURFACE)
        h_lo = min(float(row["good_airtightness_hvent_lower_w_per_k"]) for row in data)
        h_hi = max(float(row["good_airtightness_hvent_upper_w_per_k"]) for row in data)
        q_lo = min(float(row["good_airtightness_qvent_lower_kw"]) for row in data)
        q_hi = max(float(row["good_airtightness_qvent_upper_kw"]) for row in data)
        self.assertAlmostEqual(h_lo, 26.957426806)
        self.assertAlmostEqual(h_hi, 123.72696)
        self.assertAlmostEqual(q_lo, 0.808722804)
        self.assertAlmostEqual(q_hi, 3.95926272)

    def test_design_load_coverage_uses_narrower_residuals(self):
        by = {item.input_id: item for item in national_design_load_input_coverage()}
        self.assertEqual(
            by["POST_RETROFIT_VENTILATION"].status,
            PARTIAL_CURRENT_METHOD_HVENT_SURFACE,
        )
        self.assertEqual(
            by["POST_RETROFIT_VENTILATION"].blocker,
            "ACTION_CONDITIONED_POST_RETROFIT_INFILTRATION_REQUIRED",
        )
        self.assertEqual(
            by["DESIGN_INDOOR_TEMPERATURE"].status,
            CURRENT_METHOD_SERVICE_REFERENCE,
        )
        self.assertIsNone(by["DESIGN_INDOOR_TEMPERATURE"].blocker)

        blockers = set(current_design_load_blockers())
        self.assertIn("ACTION_CONDITIONED_POST_RETROFIT_INFILTRATION_REQUIRED", blockers)
        self.assertNotIn("POST_RETROFIT_VENTILATION_SURFACE_REQUIRED", blockers)
        self.assertNotIn("DESIGN_INDOOR_SERVICE_CONDITION_REQUIRED", blockers)

    def test_registry_q_and_readiness_state(self):
        reg = rows(REG, "item_id")
        self.assertEqual(
            reg["B02-P87-V12"]["status"],
            "PARTIAL_RESOLVED_CURRENT_METHOD_HVENT_SURFACE",
        )
        self.assertEqual(reg["B02-P87-V13"]["status"], "OPEN_NARROWED")

        q = rows(QUESTIONS, "question_id")["Q-B02-004"]
        self.assertEqual(q["status"], "OPEN")
        self.assertIn("B02-P87", q["notes"])
        self.assertIn(
            "POST_RETROFIT_AIRTIGHTNESS_CLASS_PREVALENCE_REQUIRED",
            q["notes"],
        )

        module = rows(MODULES, "module_id")["B02"]
        self.assertEqual(module["readiness_percent"], "55")
        self.assertIn("B02-P87", module["gate_note"])

    def test_source_registry_contains_exact_p87_authority_notes(self):
        sources = rows(SOURCES, "source_id")
        self.assertIn("P87 exact ventilation calibration", sources["SRC-B02-BME-RBSM-2026"]["notes"])
        self.assertIn("0.110-0.860 1/h", sources["SRC-B02-BME-RBSM-2026"]["notes"])
        self.assertIn("P87 exact current-method ventilation authority", sources["SRC-B06-HU-ENERGY-METHOD-2023"]["notes"])
        self.assertIn("0.35 Wh/m3K", sources["SRC-B06-HU-ENERGY-METHOD-2023"]["notes"])

    def test_nonpromotion_boundaries_are_frozen(self):
        boundary = semantic_boundaries()
        self.assertIn(
            "TYPE5_EMPIRICAL_DISTRIBUTION_CANNOT_BE_PROMOTED_TO_ALL_ARCHETYPES",
            boundary,
        )
        self.assertIn(
            "GOOD_AIRTIGHTNESS_SCENARIO_IS_NOT_REFERENCE_RETROFIT_DEFAULT",
            boundary,
        )
        self.assertIn(
            "HRV_REQUIRES_EXPLICIT_AIRFLOW_RECOVERY_AND_PREVALENCE_AUTHORITY",
            boundary,
        )
        text = DOC.read_text(encoding="utf-8")
        for phrase in (
            "REQUIRED RESIDENTIAL AIR CHANGE != OBSERVED POPULATION AIR CHANGE",
            "TYPE-5 EMPIRICAL DISTRIBUTION != ALL-ARCHETYPE POST-RETROFIT DISTRIBUTION",
            "B02 remains **55%**",
        ):
            self.assertIn(phrase, text)


if __name__ == "__main__":
    unittest.main()
