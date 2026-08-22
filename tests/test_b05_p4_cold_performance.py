import csv
import unittest
from pathlib import Path

from modules.B05.engine import PerformanceMap


ROOT = Path(__file__).parents[1]
POINTS = ROOT / "data" / "processed" / "heat_pump_performance_points.csv"


class B05P4ColdPerformanceTests(unittest.TestCase):
    def test_cold_obs_points_and_bounded_w35_interpolation(self):
        performance_map = PerformanceMap.from_csv(POINTS, "STIEBEL-HPA-O-4-CS-PLUS-INT")
        exact = performance_map.evaluate(-15.0, 35.0)
        self.assertEqual(exact.status, "OBS")
        self.assertAlmostEqual(exact.point.thermal_capacity_kw, 3.43)
        self.assertAlmostEqual(exact.point.electrical_input_kw, 1.42)
        self.assertAlmostEqual(exact.point.cop, 2.41)
        interpolated = performance_map.evaluate(-11.0, 35.0)
        self.assertEqual(interpolated.status, "DER")
        self.assertEqual(interpolated.point.interpolation, "bounded_axis_linear")
        self.assertEqual(performance_map.evaluate(-18.0, 35.0).status, "Q / OUT_OF_PERFORMANCE_DOMAIN")

    def test_missing_cold_w45_and_w55_corners_fail_closed(self):
        performance_map = PerformanceMap.from_csv(POINTS, "STIEBEL-HPA-O-4-CS-PLUS-INT")
        self.assertEqual(performance_map.evaluate(-11.0, 45.0).status, "Q / MISSING_GRID_POINT")
        self.assertEqual(performance_map.evaluate(-11.0, 55.0).status, "Q / MISSING_GRID_POINT")

    def test_operating_envelope_is_not_performance_evidence_and_eu_gate_remains(self):
        with POINTS.open(encoding="utf-8", newline="") as handle:
            cold_rows = [row for row in csv.DictReader(handle) if row["point_id"].endswith("A-15-W35")]
        self.assertEqual({row["evidence_status"] for row in cold_rows}, {"OBS"})
        self.assertEqual({row["source_id"] for row in cold_rows}, {"SRC-B05-STIEBEL-HPA-O-P4-COLD-2025"})
        for row in cold_rows:
            self.assertAlmostEqual(float(row["thermal_capacity_kW"]) / float(row["electrical_input_kW"]), float(row["COP"]), delta=0.05)
            self.assertEqual(row["operating_limit_min_outdoor_C"], "-20")
        with (ROOT / "registry" / "heat_pump_sources.csv").open(encoding="utf-8", newline="") as handle:
            sources = {row["source_id"]: row for row in csv.DictReader(handle)}
        self.assertIn("SRC-B05-STIEBEL-EU-ORIGIN-2026", sources)
        self.assertIn("SRC-B05-STIEBEL-HPA-O-P4-COLD-2025", sources)
        self.assertNotEqual(sources["SRC-B05-STIEBEL-EU-ORIGIN-2026"]["evidence_status"], "SCN")

    def test_weather_domain_reports_before_and_after_without_demand_claim(self):
        with (ROOT / "data" / "processed" / "heat_pump_weather_coverage.csv").open(encoding="utf-8", newline="") as handle:
            rows = {row["weather_profile_id"]: row for row in csv.DictReader(handle)}
        extreme = rows["B05-EXTREME-OBSERVED-72H-15310"]
        self.assertEqual(extreme["hours_inside_performance_domain"], "9")
        self.assertEqual(extreme["new_hours_inside_performance_domain"], "35")
        self.assertEqual(extreme["remaining_hours_below_new_minimum_performance_C"], "37")
        self.assertIn("not heating-runtime coverage", extreme["notes"])
        self.assertEqual(extreme["minimum_observed_temperature_C"], "-21.9")


if __name__ == "__main__":
    unittest.main()
