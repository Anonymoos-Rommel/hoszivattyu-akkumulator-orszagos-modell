import csv
import unittest
from pathlib import Path

from modules.B05.engine import PerformanceMap


ROOT = Path(__file__).parents[1]
POINTS = ROOT / "data" / "processed" / "heat_pump_performance_points.csv"
PACK = ROOT / "docs" / "source_packs" / "B05_P11_TEKNOPOINT_COLD_HIGH_SUPPLY_RECTANGLE.md"
REG = ROOT / "registry" / "b05_p11_teknopoint_cold_high_supply_rectangle.csv"
SOURCES = ROOT / "registry" / "heat_pump_sources.csv"
READINESS = ROOT / "registry" / "heat_pump_readiness.csv"
QUESTIONS = ROOT / "registry" / "open_questions.csv"


def rows(path):
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


class B05P11TeknoPointColdRectangleTests(unittest.TestCase):
    def test_exact_source_native_corners(self):
        performance_map = PerformanceMap.from_csv(POINTS, "TEKNOPOINT-ATHENA-R32-A0732")
        p = performance_map.evaluate(-15.0, 55.0)
        self.assertEqual(p.status, "OBS")
        self.assertAlmostEqual(p.point.thermal_capacity_kw, 3.90)
        self.assertAlmostEqual(p.point.electrical_input_kw, 2.00)
        self.assertAlmostEqual(p.point.cop, 1.95)
        self.assertEqual(p.point.interpolation, "exact")

        p2 = performance_map.evaluate(-7.0, 35.0)
        self.assertEqual(p2.status, "OBS")
        self.assertAlmostEqual(p2.point.thermal_capacity_kw, 5.03)
        self.assertAlmostEqual(p2.point.electrical_input_kw, 1.57)
        self.assertAlmostEqual(p2.point.cop, 3.20)

    def test_p9_stress_endpoints_and_w45_are_bounded_der(self):
        for equipment in ("TEKNOPOINT-ATHENA-R32-A0732", "TEKNOPOINT-ATHENA-R32-A0932"):
            performance_map = PerformanceMap.from_csv(POINTS, equipment)
            for outdoor in (-13.331944, -9.644444):
                for supply in (35.0, 45.0, 55.0):
                    result = performance_map.evaluate(outdoor, supply)
                    self.assertEqual(result.status, "DER")
                    self.assertIsNotNone(result.point)
                    self.assertEqual(result.point.interpolation, "bilinear_bounded")
                    self.assertGreater(result.point.thermal_capacity_kw, 0)
                    self.assertGreater(result.point.electrical_input_kw, 0)
                    self.assertGreater(result.point.cop, 0)

    def test_no_performance_extrapolation_below_minus15(self):
        performance_map = PerformanceMap.from_csv(POINTS, "TEKNOPOINT-ATHENA-R32-A0732")
        self.assertEqual(
            performance_map.evaluate(-16.0, 45.0).status,
            "Q / OUT_OF_PERFORMANCE_DOMAIN",
        )

    def test_source_triples_are_consistent_with_existing_tolerance(self):
        relevant = [
            row for row in rows(POINTS)
            if row["equipment_id"].startswith("TEKNOPOINT-ATHENA-R32-")
        ]
        self.assertEqual(len(relevant), 8)
        for row in relevant:
            capacity = float(row["thermal_capacity_kW"])
            electrical = float(row["electrical_input_kW"])
            cop = float(row["COP"])
            self.assertAlmostEqual(capacity / electrical, cop, delta=0.05)
            self.assertEqual(row["evidence_status"], "OBS")
            self.assertEqual(row["unit_boundary"], "total_unit_input")
            self.assertEqual(row["source_id"], "SRC-B05-TEKNOPOINT-ATHENA-R32-2025")

    def test_registry_narrows_q_b05_001_without_closing_defrost(self):
        registry = {row["claim"]: row for row in rows(REG)}
        self.assertEqual(
            registry["P9_STRESS_W35_W45_W55_PERFORMANCE_COVERAGE"]["status"],
            "RESOLVED_FOR_BOUNDED_PRODUCT_FAMILY",
        )
        self.assertEqual(registry["Q-B05-001"]["status"], "OPEN_NARROWED")
        self.assertIn(
            "SECOND_MANUFACTURER_COLD_W45_W55_COMPLETE_SURFACE_REQUIRED_FOR_CROSS_MANUFACTURER_COHORT",
            registry["Q-B05-001"]["residual_gap"],
        )
        self.assertEqual(registry["Q-B05-003"]["status"], "UNCHANGED_OPEN")

    def test_live_registries_and_readiness_preserve_boundaries(self):
        sources = {row["source_id"]: row for row in rows(SOURCES)}
        self.assertIn("SRC-B05-TEKNOPOINT-ATHENA-R32-2025", sources)
        self.assertIn("SRC-B05-TEKNOPOINT-ATHENA-R32-CURRENT-2026", sources)

        questions = {row["question_id"]: row for row in rows(QUESTIONS)}
        self.assertEqual(questions["Q-B05-001"]["status"], "OPEN")
        self.assertIn("B05-P11", questions["Q-B05-001"]["notes"])
        self.assertIn(
            "SECOND_MANUFACTURER_COLD_W45_W55_COMPLETE_SURFACE_REQUIRED_FOR_CROSS_MANUFACTURER_COHORT",
            questions["Q-B05-001"]["notes"],
        )

        readiness = {row["component_id"]: row for row in rows(READINESS)}
        self.assertEqual(readiness["PERFORMANCE_MAP"]["readiness_percent"], "80")
        self.assertEqual(readiness["WEATHER_PERFORMANCE_DOMAIN_COVERAGE"]["readiness_percent"], "60")
        self.assertIn("SRC-B05-TEKNOPOINT-ATHENA-R32-2025", readiness["PERFORMANCE_MAP"]["source_ids"])

        text = PACK.read_text(encoding="utf-8")
        self.assertIn("W45 DERIVATION INSIDE W35..W55 != SOURCE-NATIVE W45 OBSERVATION", text)
        self.assertIn("B05 module readiness remains **64%**", text)
        self.assertIn("Q-B05-003 defrost accounting", text)


if __name__ == "__main__":
    unittest.main()
