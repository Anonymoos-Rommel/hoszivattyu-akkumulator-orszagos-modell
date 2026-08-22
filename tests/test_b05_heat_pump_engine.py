from datetime import datetime, timedelta
from collections import defaultdict
import csv
from pathlib import Path
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
    PRODUCT_POINTS = Path(__file__).parents[1] / "data" / "processed" / "heat_pump_performance_points.csv"

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

    def test_real_product_maps_are_source_native_and_regress_at_exact_nodes(self):
        with self.PRODUCT_POINTS.open(encoding="utf-8", newline="") as handle:
            rows = list(csv.DictReader(handle))
        real_rows = [row for row in rows if row["evidence_status"] == "OBS"]
        equipment_ids = {row["equipment_id"] for row in real_rows}
        self.assertGreaterEqual(len(equipment_ids), 4)
        self.assertTrue(all(row["source_id"].startswith("SRC-B05-") for row in real_rows))
        self.assertNotIn("SRC-B05-SYNTHETIC-TEST-GRID", {row["source_id"] for row in real_rows})
        with (self.PRODUCT_POINTS.parents[2] / "registry" / "heat_pump_sources.csv").open(encoding="utf-8", newline="") as handle:
            registered_sources = {row["source_id"] for row in csv.DictReader(handle)}
        self.assertIn("SRC-B05-VAILLANT-SPLIT-EU-ORIGIN-2019", registered_sources)
        self.assertIn("SRC-B05-VAILLANT-PLUS-EU-ORIGIN-2020", registered_sources)
        self.assertFalse(any(source_id.startswith("SRC-B05-DAIKIN-") for source_id in registered_sources))

        expected_nodes = {
            "VAILLANT-AROTHERM-SPLIT-35": {(-7.0, 35.0), (2.0, 35.0), (7.0, 35.0), (7.0, 55.0)},
            "VAILLANT-AROTHERM-SPLIT-70": {(-7.0, 35.0), (2.0, 35.0), (7.0, 35.0), (7.0, 55.0)},
            "VAILLANT-AROTHERM-SPLIT-120": {(-7.0, 35.0), (2.0, 35.0), (7.0, 35.0), (7.0, 55.0)},
            "VAILLANT-AROTHERM-PLUS-55": {(-7.0, 35.0), (2.0, 35.0), (7.0, 35.0), (7.0, 45.0), (7.0, 55.0)},
        }
        for equipment_id, nodes in expected_nodes.items():
            product_rows = [row for row in real_rows if row["equipment_id"] == equipment_id]
            self.assertEqual({(float(row["outdoor_temperature_C"]), float(row["supply_temperature_C"])) for row in product_rows}, nodes)
            performance_map = PerformanceMap.from_csv(self.PRODUCT_POINTS, equipment_id)
            for row in product_rows:
                result = performance_map.evaluate(float(row["outdoor_temperature_C"]), float(row["supply_temperature_C"]))
                self.assertEqual(result.status, "OBS")
                self.assertAlmostEqual(result.point.thermal_capacity_kw, float(row["thermal_capacity_kW"]))
                self.assertAlmostEqual(result.point.electrical_input_kw, float(row["electrical_input_kW"]))
                self.assertAlmostEqual(result.point.cop, float(row["COP"]))

        plus_rows = [row for row in real_rows if row["equipment_id"] == "VAILLANT-AROTHERM-PLUS-55"]
        plus_a7_w35 = next(row for row in plus_rows if row["outdoor_temperature_C"] == "7" and row["supply_temperature_C"] == "35")
        self.assertEqual(float(plus_a7_w35["min_modulation_kW"]), 2.10)

        sparse_surface = PerformanceMap.from_csv(self.PRODUCT_POINTS, "VAILLANT-AROTHERM-SPLIT-35").evaluate(-2.0, 35.0)
        self.assertEqual(sparse_surface.status, "Q / MISSING_GRID_POINT")
        self.assertIsNone(sparse_surface.point)

    def test_csv_loader_keeps_synthetic_fixture_separate(self):
        fixture = PerformanceMap.from_csv(self.PRODUCT_POINTS, "TEST-AWHP-REFERENCE")
        self.assertEqual(fixture.evaluate(0.0, 35.0).status, "SCN")
        with self.assertRaises(PerformanceMapError):
            PerformanceMap.from_csv(self.PRODUCT_POINTS, "NOT-A-REAL-EQUIPMENT")


if __name__ == "__main__":
    unittest.main()
