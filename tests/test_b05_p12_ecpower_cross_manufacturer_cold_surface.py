import csv
import unittest
from pathlib import Path

from modules.B05.cold_high_supply_cohort import (
    boundary,
    cross_manufacturer_status,
    qualified_manufacturers,
    qualify_equipment_surface,
)
from modules.B05.engine import PerformanceMap


ROOT = Path(__file__).resolve().parents[1]
POINTS = ROOT / "data" / "processed" / "heat_pump_performance_points.csv"
SURFACE = ROOT / "data" / "processed" / "b05_p12_cross_manufacturer_cold_high_supply_surface.csv"
REG = ROOT / "registry" / "b05_p12_ecpower_cross_manufacturer_cold_surface.csv"
QUESTIONS = ROOT / "registry" / "open_questions.csv"
READINESS = ROOT / "registry" / "heat_pump_readiness.csv"
SOURCES = ROOT / "registry" / "heat_pump_sources.csv"
PACK = ROOT / "docs" / "source_packs" / "B05_P12_ECPOWER_CROSS_MANUFACTURER_COLD_SURFACE.md"


def rows(path):
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


class B05P12EcPowerCrossManufacturerColdSurfaceTests(unittest.TestCase):
    def test_ecpower_source_points_keep_input_unpromoted(self):
        relevant = [
            row for row in rows(POINTS)
            if row["equipment_id"] in {"ECPOWER-PMH-6", "ECPOWER-PMH-19"}
        ]
        self.assertEqual(len(relevant), 8)
        for row in relevant:
            self.assertEqual(row["evidence_status"], "OBS")
            self.assertNotEqual(row["thermal_capacity_kW"], "")
            self.assertEqual(row["electrical_input_kW"], "")
            self.assertNotEqual(row["COP"], "")
            self.assertEqual(row["source_id"], "SRC-B05-ECPOWER-PMH-2023")

    def test_ecpower_exact_points_are_der_completed_not_obs_input(self):
        performance_map = PerformanceMap.from_csv(POINTS, "ECPOWER-PMH-6")
        exact = performance_map.evaluate(-15.0, 55.0)
        self.assertEqual(exact.status, "DER")
        self.assertAlmostEqual(exact.point.thermal_capacity_kw, 2.82)
        self.assertAlmostEqual(exact.point.cop, 1.37)
        self.assertAlmostEqual(exact.point.electrical_input_kw, 2.82 / 1.37)
        self.assertEqual(exact.point.interpolation, "exact")

    def test_both_manufacturers_cover_p9_stress_w35_w45_w55(self):
        self.assertEqual(qualified_manufacturers(), ("EC_POWER", "TEKNO_POINT"))
        self.assertEqual(
            cross_manufacturer_status(),
            "RESOLVED_FOR_PROGRAMME_PHYSICAL_COHORT",
        )
        for equipment in (
            "TEKNOPOINT-ATHENA-R32-A0732",
            "TEKNOPOINT-ATHENA-R32-A0932",
            "ECPOWER-PMH-6",
            "ECPOWER-PMH-19",
        ):
            qualification = qualify_equipment_surface(equipment)
            self.assertTrue(qualification.qualified)
            self.assertEqual(qualification.evaluated_coordinate_count, 6)

    def test_w45_is_bounded_der_and_below_minus15_fails_closed(self):
        performance_map = PerformanceMap.from_csv(POINTS, "ECPOWER-PMH-6")
        for outdoor in (-13.331944, -9.644444):
            result = performance_map.evaluate(outdoor, 45.0)
            self.assertEqual(result.status, "DER")
            self.assertEqual(result.point.interpolation, "bilinear_bounded")
        self.assertEqual(
            performance_map.evaluate(-16.0, 45.0).status,
            "Q / OUT_OF_PERFORMANCE_DOMAIN",
        )

    def test_materialized_surface_does_not_average_product_sizes(self):
        materialized = rows(SURFACE)
        self.assertEqual(len(materialized), 4)
        self.assertEqual(
            {row["manufacturer"] for row in materialized},
            {"TEKNO_POINT", "EC_POWER"},
        )
        self.assertNotIn("capacity_min_kW", materialized[0])
        self.assertNotIn("capacity_max_kW", materialized[0])
        self.assertTrue(all(row["p9_stress_covered"] == "YES" for row in materialized))

    def test_registry_resolves_cross_manufacturer_residual_only(self):
        registry = {row["claim"]: row for row in rows(REG)}
        self.assertEqual(
            registry["CROSS_MANUFACTURER_COLD_HIGH_SUPPLY_SURFACE"]["status"],
            "RESOLVED_FOR_PROGRAMME_PHYSICAL_COHORT",
        )
        self.assertEqual(
            registry["P11_CROSS_MANUFACTURER_RESIDUAL"]["status"],
            "RESOLVED",
        )
        self.assertEqual(registry["Q-B05-001"]["status"], "OPEN_CONDITIONAL")
        self.assertIn(
            "BELOW_MINUS15_W35_REQUIRED_IF_HOURLY_EXTREME_EVENT_SIMULATION_IS_IN_SCOPE",
            registry["Q-B05-001"]["residual_gap"],
        )

    def test_live_question_and_readiness_do_not_mint_uplift(self):
        questions = {row["question_id"]: row for row in rows(QUESTIONS)}
        self.assertEqual(questions["Q-B05-001"]["status"], "OPEN")
        self.assertIn("B05-P12", questions["Q-B05-001"]["notes"])
        self.assertIn("OPEN_CONDITIONAL", questions["Q-B05-001"]["notes"])

        readiness = {row["component_id"]: row for row in rows(READINESS)}
        self.assertEqual(readiness["PERFORMANCE_MAP"]["readiness_percent"], "80")
        self.assertEqual(readiness["WEATHER_PERFORMANCE_DOMAIN_COVERAGE"]["readiness_percent"], "60")
        self.assertIn("SRC-B05-ECPOWER-PMH-2023", readiness["PERFORMANCE_MAP"]["source_ids"])

    def test_sources_and_nonpromotion_boundaries_are_explicit(self):
        sources = {row["source_id"]: row for row in rows(SOURCES)}
        self.assertIn("SRC-B05-ECPOWER-PMH-2023", sources)
        self.assertIn("SRC-B05-ECPOWER-PMH-CURRENT-2026", sources)
        b = boundary()
        self.assertIn("NO_PRODUCT_SIZE_AVERAGING", b)
        self.assertIn("NO_HUNGARY_PROCUREMENT_CLAIM", b)
        self.assertIn("ECPOWER_ELECTRICAL_INPUT_IS_DER_NOT_OBS", b)

        text = PACK.read_text(encoding="utf-8")
        for phrase in (
            "DER COMPLETION != SOURCE-NATIVE ELECTRICAL INPUT OBS",
            "TWO-MANUFACTURER PHYSICAL SURFACE != HUNGARIAN MARKET REPRESENTATIVENESS",
            "B05 module readiness remains **64%**",
        ):
            self.assertIn(phrase, text)


if __name__ == "__main__":
    unittest.main()
