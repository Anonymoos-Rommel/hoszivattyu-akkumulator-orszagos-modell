import csv
import unittest
from pathlib import Path

from modules.B05.engine import PerformanceMap


ROOT = Path(__file__).parents[1]


class B05P5ColdHighSupplyTests(unittest.TestCase):
    POINTS = ROOT / "data" / "processed" / "heat_pump_performance_points.csv"
    SUPPLY_COVERAGE = ROOT / "data" / "processed" / "heat_pump_weather_supply_coverage.csv"

    def test_extreme_weather_coverage_is_supply_specific(self):
        with self.SUPPLY_COVERAGE.open(encoding="utf-8", newline="") as handle:
            rows = [
                row
                for row in csv.DictReader(handle)
                if row["weather_profile_id"] == "B05-EXTREME-OBSERVED-72H-15310"
                and row["equipment_id"] == "STIEBEL-HPA-O-4-CS-PLUS-INT"
            ]
        by_supply = {float(row["supply_temperature_C"]): row for row in rows}
        self.assertEqual(set(by_supply), {35.0, 45.0, 55.0})
        self.assertEqual(by_supply[35.0]["performance_domain_min_Tout_C"], "-15")
        self.assertEqual(by_supply[35.0]["weather_hours_inside_domain"], "35")
        self.assertEqual(by_supply[35.0]["weather_hours_below_domain"], "37")
        self.assertAlmostEqual(float(by_supply[35.0]["coverage_share"]), 35 / 72, places=5)
        self.assertEqual(by_supply[35.0]["coldest_uncovered_Tout_C"], "-21.9")
        self.assertEqual(by_supply[45.0]["performance_domain_min_Tout_C"], "-7")
        self.assertEqual(by_supply[45.0]["weather_hours_inside_domain"], "9")
        self.assertEqual(by_supply[45.0]["weather_hours_below_domain"], "63")
        self.assertAlmostEqual(float(by_supply[45.0]["coverage_share"]), 9 / 72, places=5)
        self.assertEqual(by_supply[45.0]["coldest_uncovered_Tout_C"], "-21.9")
        self.assertEqual(by_supply[55.0]["status"], "Q")
        self.assertEqual(by_supply[55.0]["weather_hours_inside_domain"], "")
        self.assertEqual(by_supply[55.0]["coverage_share"], "")

    def test_supply_surface_isolation_and_fail_closed_boundaries(self):
        performance_map = PerformanceMap.from_csv(self.POINTS, "STIEBEL-HPA-O-4-CS-PLUS-INT")
        self.assertEqual(performance_map.evaluate(-7.0, 45.0).status, "OBS")
        self.assertTrue(performance_map.evaluate(-11.0, 45.0).status.startswith("Q / "))
        self.assertTrue(performance_map.evaluate(-11.0, 55.0).status.startswith("Q / "))
        self.assertEqual(performance_map.evaluate(7.0, 55.0).status, "OBS")
        self.assertTrue(performance_map.evaluate(2.0, 55.0).status.startswith("Q / MISSING_GRID_POINT"))
        self.assertTrue(performance_map.evaluate(-20.0, 35.0).status.startswith("Q / OUT_OF_PERFORMANCE_DOMAIN"))

    def test_no_new_high_supply_obs_or_synthetic_promotion(self):
        with self.POINTS.open(encoding="utf-8", newline="") as handle:
            rows = list(csv.DictReader(handle))
        high_supply_obs = [
            row
            for row in rows
            if row["evidence_status"] == "OBS"
            and row["supply_temperature_C"] in {"45", "55"}
            and float(row["outdoor_temperature_C"]) < -7
        ]
        self.assertEqual(high_supply_obs, [])
        self.assertNotIn(
            "SRC-B05-SYNTHETIC-TEST-GRID",
            {row["source_id"] for row in rows if row["evidence_status"] == "OBS"},
        )


if __name__ == "__main__":
    unittest.main()
