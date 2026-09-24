import csv
import unittest
from pathlib import Path

from modules.B05.engine import PerformanceMap


ROOT = Path(__file__).resolve().parents[1]
POINTS = ROOT / "data" / "processed" / "heat_pump_performance_points.csv"
SOURCE_OBS = ROOT / "data" / "processed" / "b05_p13_wamak_source_observations.csv"
COVERAGE = ROOT / "data" / "processed" / "b05_p13_observed_extreme_performance_coverage.csv"
REG = ROOT / "registry" / "b05_p13_wamak_extreme_cold_closure.csv"
QUESTIONS = ROOT / "registry" / "open_questions.csv"
READINESS = ROOT / "registry" / "heat_pump_readiness.csv"
SOURCES = ROOT / "registry" / "heat_pump_sources.csv"
PACK = ROOT / "docs" / "source_packs" / "B05_P13_WAMAK_EXTREME_COLD_CLOSURE.md"


def rows(path):
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


class B05P13WamakExtremeColdClosureTests(unittest.TestCase):
    def test_source_inconsistency_is_preserved_not_silently_corrected(self):
        source = {row["observation_id"]: row for row in rows(SOURCE_OBS)}
        conflict = source["WAMAK-AWK35-SRC-A-22-W55"]
        self.assertEqual(conflict["published_electrical_input_kW"], "13.0")
        self.assertEqual(conflict["COP"], "1.51")
        self.assertEqual(conflict["admission_status"], "REJECTED_INPUT_CONFLICT")
        self.assertGreater(
            abs(
                float(conflict["thermal_capacity_kW"])
                / float(conflict["published_electrical_input_kW"])
                - float(conflict["COP"])
            ),
            0.05,
        )

    def test_canonical_rectangle_has_three_obs_and_one_der_corner(self):
        relevant = [
            row for row in rows(POINTS)
            if row["equipment_id"] == "WAMAK-AWK35-EVI"
        ]
        self.assertEqual(len(relevant), 4)
        by_coord = {
            (float(row["outdoor_temperature_C"]), float(row["supply_temperature_C"])): row
            for row in relevant
        }
        self.assertEqual(by_coord[(-22.0, 35.0)]["evidence_status"], "OBS")
        self.assertEqual(by_coord[(-10.0, 35.0)]["evidence_status"], "OBS")
        self.assertEqual(by_coord[(-10.0, 55.0)]["evidence_status"], "OBS")
        self.assertEqual(by_coord[(-22.0, 55.0)]["evidence_status"], "DER")
        self.assertAlmostEqual(
            float(by_coord[(-22.0, 55.0)]["electrical_input_kW"]),
            21.2 / 1.51,
            places=8,
        )

    def test_observed_minus21_9_is_covered_at_w35_w45_w55(self):
        performance_map = PerformanceMap.from_csv(POINTS, "WAMAK-AWK35-EVI")
        for supply in (35.0, 45.0, 55.0):
            result = performance_map.evaluate(-21.9, supply)
            self.assertEqual(result.status, "DER")
            self.assertEqual(result.point.interpolation, "bilinear_bounded")
            self.assertGreater(result.point.thermal_capacity_kw, 0)
            self.assertGreater(result.point.electrical_input_kw, 0)
            self.assertGreater(result.point.cop, 0)

    def test_below_minus22_still_fails_closed(self):
        performance_map = PerformanceMap.from_csv(POINTS, "WAMAK-AWK35-EVI")
        self.assertEqual(
            performance_map.evaluate(-22.1, 45.0).status,
            "Q / OUT_OF_PERFORMANCE_DOMAIN",
        )

    def test_materialized_extreme_coverage_is_supply_specific(self):
        coverage = rows(COVERAGE)
        self.assertEqual(len(coverage), 3)
        self.assertEqual(
            {float(row["supply_temperature_C"]) for row in coverage},
            {35.0, 45.0, 55.0},
        )
        self.assertTrue(
            all(row["status"] == "COVERED_WITHOUT_EXTRAPOLATION" for row in coverage)
        )

    def test_p13_registry_resolves_q_b05_001_physical_scope(self):
        registry = {row["claim"]: row for row in rows(REG)}
        self.assertEqual(
            registry["OBSERVED_MINUS21_9_W35_W45_W55_COVERAGE"]["status"],
            "RESOLVED_FOR_BOUNDED_PRODUCT_FAMILY",
        )
        self.assertEqual(
            registry["BELOW_MINUS15_CONDITIONAL_RESIDUAL"]["status"],
            "RESOLVED_FOR_CANONICAL_OBSERVED_EVENT",
        )
        self.assertEqual(
            registry["Q-B05-001"]["status"],
            "RESOLVED_FOR_PHYSICAL_MODEL",
        )
        self.assertEqual(registry["Q-B05-003"]["status"], "UNCHANGED_OPEN")

    def test_live_question_is_resolved_without_market_promotion(self):
        questions = {row["question_id"]: row for row in rows(QUESTIONS)}
        q = questions["Q-B05-001"]
        self.assertEqual(q["status"], "RESOLVED")
        self.assertIn("B05-P13", q["notes"])
        self.assertIn("RESOLVED_FOR_PHYSICAL_MODEL", q["notes"])
        self.assertIn("procurement", q["notes"].lower())
        self.assertIn("market", q["notes"].lower())

    def test_readiness_percentages_are_not_minted(self):
        readiness = {row["component_id"]: row for row in rows(READINESS)}
        self.assertEqual(readiness["PERFORMANCE_MAP"]["readiness_percent"], "80")
        self.assertEqual(
            readiness["WEATHER_PERFORMANCE_DOMAIN_COVERAGE"]["readiness_percent"],
            "60",
        )
        self.assertIn(
            "SRC-B05-WAMAK-AWK35-EVI-2026",
            readiness["PERFORMANCE_MAP"]["source_ids"],
        )

    def test_source_and_document_boundaries(self):
        sources = {row["source_id"]: row for row in rows(SOURCES)}
        self.assertIn("SRC-B05-WAMAK-AWK35-EVI-2026", sources)
        text = PACK.read_text(encoding="utf-8")
        for phrase in (
            "SOURCE-INCONSISTENT TRIPLE != OBS COMPLETE POINT",
            "OBSERVED EVENT MINIMUM != FUTURE DESIGN MINIMUM",
            "Q-B05-001 therefore becomes:",
            "B05 module readiness remains **64%**",
        ):
            self.assertIn(phrase, text)


if __name__ == "__main__":
    unittest.main()
