from datetime import datetime, timedelta
from collections import defaultdict
import unittest

from modules.B05.engine import (
    HourlyDemand,
    OperatingConfig,
    PerformanceMap,
    PerformanceMapError,
    PerformancePoint,
    simulate_hourly,
)


def test_map() -> PerformanceMap:
    points = []
    for outdoor, rows in {
        -10.0: ((5.0, 2.0, 2.5, 1.5), (4.0, 2.0, 2.0, 1.6)),
        0.0: ((6.0, 2.0, 3.0, 1.5), (5.0, 2.0, 2.5, 1.6)),
        10.0: ((7.0, 1.75, 4.0, 1.5), (6.0, 2.0, 3.0, 1.6)),
    }.items():
        for supply, values in zip((35.0, 45.0), rows):
            capacity, electrical, cop, minimum = values
            points.append(PerformancePoint(outdoor, supply, capacity, electrical, cop, minimum, evidence_status="SCN", source_id="TEST"))
    return PerformanceMap("TEST", "air_to_water", points)


def demand(hour: int, load: float, outdoor: float = 0.0, supply: float = 35.0, dhw: float = 0.0, dhw_supply: float | None = None) -> HourlyDemand:
    return HourlyDemand(datetime(2026, 1, 1) + timedelta(hours=hour), outdoor, load, supply if load else None, dhw, dhw_supply)


class B05HeatPumpEngineTests(unittest.TestCase):
    def test_exact_node_and_bounded_interpolation(self):
        result = test_map().evaluate(-10.0, 35.0)
        self.assertEqual(result.status, "SCN")
        self.assertEqual(result.point.thermal_capacity_kw, 5.0)
        interpolated = test_map().evaluate(-5.0, 40.0)
        self.assertEqual(interpolated.status, "DER")
        self.assertAlmostEqual(interpolated.point.thermal_capacity_kw, 5.0)
        self.assertAlmostEqual(interpolated.point.electrical_input_kw, 2.0)
        self.assertAlmostEqual(interpolated.point.cop, 2.5)

    def test_boundaries_and_outside_domain_fail_closed(self):
        self.assertEqual(test_map().evaluate(10.0, 45.0).status, "SCN")
        outside = test_map().evaluate(10.1, 45.0)
        self.assertIsNone(outside.point)
        self.assertTrue(outside.status.startswith("Q / OUT_OF_PERFORMANCE_DOMAIN"))

    def test_inconsistent_source_point_rejected(self):
        with self.assertRaises(PerformanceMapError):
            PerformanceMap("BAD", "air_to_water", [PerformancePoint(0, 35, 5, 2, 4, evidence_status="OBS")])

    def test_zero_load_has_no_heating_energy(self):
        result = simulate_hourly(test_map(), [demand(0, 0)])
        self.assertEqual(result.status, "VALID")
        self.assertEqual(result.seasonal_total_electricity_kwh, 0.0)
        self.assertEqual(result.hourly[0].operating_state, "NO_HEAT_DEMAND")

    def test_part_load_and_cycling_state_without_invented_penalty(self):
        result = simulate_hourly(test_map(), [demand(0, 1.0)])
        hour = result.hourly[0]
        self.assertIn("CYCLING_REQUIRED", hour.operating_state)
        self.assertAlmostEqual(hour.heat_pump_heat_delivered_kwh, 1.0)
        self.assertAlmostEqual(hour.heat_pump_electricity_kwh, 1.0 / 3.0)
        self.assertIsNone(hour.defrost_energy_penalty_kwh)

    def test_capacity_shortfall_and_backup_are_separate(self):
        disabled = simulate_hourly(test_map(), [demand(0, 8.0)], OperatingConfig())
        self.assertAlmostEqual(disabled.capacity_shortfall_kwh, 2.0)
        self.assertEqual(disabled.seasonal_backup_electricity_kwh, 0.0)
        enabled = simulate_hourly(test_map(), [demand(0, 8.0)], OperatingConfig(backup_enabled=True, backup_type="resistance", backup_capacity_kw=3.0, backup_efficiency=1.0))
        self.assertEqual(enabled.capacity_shortfall_kwh, 0.0)
        self.assertEqual(enabled.seasonal_backup_electricity_kwh, 2.0)

    def test_supply_temperature_changes_surface(self):
        low = simulate_hourly(test_map(), [demand(0, 3.0, supply=35.0)])
        medium = simulate_hourly(test_map(), [demand(0, 3.0, supply=45.0)])
        self.assertNotEqual(low.seasonal_cop_simulated, medium.seasonal_cop_simulated)

    def test_energy_equals_power_times_timestep_and_aggregation(self):
        config = OperatingConfig(timestep_hours=0.5)
        result = simulate_hourly(test_map(), [demand(0, 3.0), demand(1, 3.0)], config)
        self.assertAlmostEqual(result.seasonal_heat_delivered_kwh, 3.0)
        self.assertAlmostEqual(result.seasonal_total_electricity_kwh, 1.0)
        self.assertAlmostEqual(sum(row.total_electricity_kwh for row in result.hourly), 1.0)
        self.assertAlmostEqual(result.seasonal_cop_simulated, 3.0)

    def test_hourly_daily_seasonal_energy_reconciliation(self):
        demands = [demand(0, 3.0), demand(1, 3.0), demand(24, 3.0)]
        result = simulate_hourly(test_map(), demands)
        daily = defaultdict(float)
        for row in result.hourly:
            daily[row.timestamp.date()] += row.heat_pump_heat_delivered_kwh
        self.assertEqual(len(daily), 2)
        self.assertAlmostEqual(sum(daily.values()), result.seasonal_heat_delivered_kwh)

    def test_missing_weather_and_dhw_outside_map_fail_closed(self):
        with self.assertRaises(ValueError):
            simulate_hourly(test_map(), [HourlyDemand(datetime(2026, 1, 1), None, 1.0, 35.0)])
        result = simulate_hourly(test_map(), [demand(0, 0, outdoor=0.0, dhw=1.0, dhw_supply=55.0)])
        self.assertEqual(result.status, "Q")
        self.assertTrue(result.hourly[0].status.startswith("Q / OUT_OF_PERFORMANCE_DOMAIN"))

    def test_dhw_priority_is_explicit(self):
        result = simulate_hourly(test_map(), [demand(0, 1.0, supply=35.0, dhw=1.0, dhw_supply=45.0)])
        self.assertEqual(result.status, "Q")
        self.assertEqual(result.hourly[0].operating_state, "Q_DHW_PRIORITY")

    def test_no_monetary_or_tariff_input_is_used(self):
        first = simulate_hourly(test_map(), [demand(0, 3.0)])
        second = simulate_hourly(test_map(), [demand(0, 3.0)])
        self.assertEqual(first.seasonal_total_electricity_kwh, second.seasonal_total_electricity_kwh)


if __name__ == "__main__":
    unittest.main()
