"""Regression: interpolation must not violate the defining Q/P COP identity."""
from datetime import datetime
from pathlib import Path
import unittest

from modules.B05.engine import HourlyDemand, OperatingConfig, PerformanceMap, PerformancePoint, simulate_hourly


class B05InterpolationEnergyConsistencyTests(unittest.TestCase):
    def test_varying_power_grid_interpolates_powers_not_cop_ratio(self):
        points = [PerformancePoint(t, w, q, p, q / p, evidence_status='SCN')
                  for t, w, q, p in [(-7, 35, 4, 1), (2, 35, 6, 3),
                                     (-7, 45, 3, 2), (2, 45, 5, 4)]]
        point = PerformanceMap('TEST', 'air_to_water', points).evaluate(-2.5, 40).point
        self.assertAlmostEqual(point.thermal_capacity_kw, 4.5)
        self.assertAlmostEqual(point.electrical_input_kw, 2.5)
        self.assertAlmostEqual(point.cop, 1.8)
        self.assertNotAlmostEqual(point.cop, (4 + 2 + 1.5 + 1.25) / 4)

    def test_product_bilinear_and_cold_axis_conserve_power(self):
        path = Path(__file__).resolve().parents[1] / 'data/processed/heat_pump_performance_points.csv'
        for equipment in ['STIEBEL-HPA-O-4-CS-PLUS-INT', 'STIEBEL-HPA-O-8-CS-PLUS-INT']:
            surface = PerformanceMap.from_csv(path, equipment)
            for outdoor, supply in [(-2, 40), (-11, 35), (-6, 36), (4, 44)]:
                with self.subTest(equipment=equipment, outdoor=outdoor, supply=supply):
                    point = surface.evaluate(outdoor, supply).point
                    self.assertAlmostEqual(point.thermal_capacity_kw, point.electrical_input_kw * point.cop, places=12)
                    for load_fraction in [0.25, 1.0, 1.5]:
                        for duration in [0.25, 1.0]:
                            demand = HourlyDemand(datetime(2025, 1, 1), outdoor, point.thermal_capacity_kw * load_fraction, supply)
                            result = simulate_hourly(surface, [demand], OperatingConfig(timestep_hours=duration))
                            self.assertAlmostEqual(result.seasonal_heat_pump_electricity_kwh, point.electrical_input_kw * min(load_fraction, 1.0) * duration, places=12)
                            self.assertAlmostEqual(result.capacity_shortfall_kwh, point.thermal_capacity_kw * max(load_fraction - 1.0, 0) * duration, places=12)

    def test_zero_interpolated_power_fails_closed_without_division(self):
        # Two-of-three zero-capacity points complete to zero electrical power.
        for coordinates, query in [([(-7, 35), (2, 35), (-7, 45), (2, 45)], (-2, 40)),
                                   ([(-15, 35), (-7, 35)], (-11, 35))]:
            points = [PerformancePoint(t, w, 0, None, 1, evidence_status="SCN")
                      for t, w in coordinates]
            result = PerformanceMap("ZERO", "air_to_water", points).evaluate(*query)
            self.assertEqual(result.status, "Q / INVALID_INTERPOLATED_POINT")
            self.assertIsNone(result.point)

    def test_exact_source_triples_and_sparse_domain_are_not_rewritten(self):
        points = [PerformancePoint(-15, 35, 3.43, 1.42, 2.41, evidence_status='OBS', source_id='TEST'),
                  PerformancePoint(-7, 35, 4, 2, 2, evidence_status='OBS', source_id='TEST')]
        surface = PerformanceMap('TEST', 'air_to_water', points)
        point = surface.evaluate(-15, 35).point
        self.assertEqual((point.thermal_capacity_kw, point.electrical_input_kw, point.cop), (3.43, 1.42, 2.41))
        self.assertEqual(point.evidence_status, 'OBS')
        self.assertIsNone(surface.evaluate(-16, 35).point)
        self.assertIsNone(surface.evaluate(-11, 40).point)


if __name__ == '__main__':
    unittest.main()
