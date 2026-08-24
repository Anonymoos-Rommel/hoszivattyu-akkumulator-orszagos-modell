import csv
import unittest
from pathlib import Path

from modules.B07.engine import (
    BatteryEngine,
    BatteryModelError,
    BatterySpec,
    compute_household_balance,
    make_b08_handoff,
)


ROOT = Path(__file__).resolve().parents[1]


def read_rows(path: Path):
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def fixture_spec(*, timestep_hours=1.0):
    return BatterySpec(
        nominal_capacity_kwh=10.0,
        usable_capacity_kwh=10.0,
        soc_min_fraction=0.0,
        soc_max_fraction=1.0,
        max_charge_power_kw=5.0,
        max_discharge_power_kw=5.0,
        charge_efficiency=0.95,
        discharge_efficiency=0.95,
        timestep_hours=timestep_hours,
        capacity_boundary="USABLE",
        power_boundary="AC",
        efficiency_boundary="SCN_ONE_WAY",
        status="SCN",
    )


class B07BatteryPhysicsTests(unittest.TestCase):
    def test_charge_increases_soc_and_efficiency_is_applied_once(self):
        engine = BatteryEngine(fixture_spec(), 0.0)
        result = engine.step(requested_charge_kw=5.0)
        self.assertAlmostEqual(result.actual_charge_kw, 5.0)
        self.assertAlmostEqual(result.charge_energy_from_grid_kwh, 5.0)
        self.assertAlmostEqual(result.energy_added_to_storage_kwh, 4.75)
        self.assertAlmostEqual(result.soc_after_kwh, 4.75)

    def test_discharge_decreases_soc_and_efficiency_is_applied_once(self):
        engine = BatteryEngine(fixture_spec(), 10.0)
        result = engine.step(requested_discharge_kw=5.0)
        self.assertAlmostEqual(result.actual_discharge_kw, 5.0)
        self.assertAlmostEqual(result.discharge_energy_to_load_grid_kwh, 5.0)
        self.assertAlmostEqual(result.energy_removed_from_storage_kwh, 5.0 / 0.95)
        self.assertAlmostEqual(result.soc_after_kwh, 10.0 - 5.0 / 0.95)

    def test_power_cap_reports_curtailed_charge(self):
        engine = BatteryEngine(fixture_spec(), 0.0)
        result = engine.step(requested_charge_kw=8.0)
        self.assertAlmostEqual(result.actual_charge_kw, 5.0)
        self.assertAlmostEqual(result.charge_curtailed_kw, 3.0)
        self.assertEqual(result.reason, "PHYSICAL_LIMIT_CLIPPED")

    def test_soc_upper_and_lower_bounds_report_clipping(self):
        upper = BatteryEngine(fixture_spec(), 9.5).step(requested_charge_kw=5.0)
        self.assertAlmostEqual(upper.soc_after_kwh, 10.0)
        self.assertGreater(upper.charge_curtailed_kwh, 0.0)
        lower_engine = BatteryEngine(fixture_spec(), 1.0)
        lower = lower_engine.step(requested_discharge_kw=5.0)
        self.assertAlmostEqual(lower.soc_after_kwh, 0.0)
        self.assertGreater(lower.discharge_unserved_kwh, 0.0)

    def test_simultaneous_commands_fail_closed(self):
        with self.assertRaises(BatteryModelError):
            BatteryEngine(fixture_spec(), 5.0).step(1.0, 1.0)

    def test_timestep_is_explicit_and_subhourly_energy_consistent(self):
        hourly = BatteryEngine(fixture_spec(timestep_hours=1.0), 0.0).step(5.0)
        half_hour = BatteryEngine(fixture_spec(timestep_hours=0.5), 0.0).step(5.0)
        self.assertAlmostEqual(hourly.charge_energy_from_grid_kwh, 5.0)
        self.assertAlmostEqual(half_hour.charge_energy_from_grid_kwh, 2.5)
        self.assertAlmostEqual(hourly.energy_added_to_storage_kwh, 2 * half_hour.energy_added_to_storage_kwh)

    def test_invalid_efficiency_and_capacity_are_rejected(self):
        with self.assertRaises(BatteryModelError):
            BatterySpec(10, 10, 0, 1, 5, 5, 0, 0.95, 1)
        with self.assertRaises(BatteryModelError):
            BatterySpec(None, 10, 0, 1, 5, 5, 0.95, 0.95, 1)
        with self.assertRaises(BatteryModelError):
            BatterySpec(10, 11, 0, 1, 5, 5, 0.95, 0.95, 1)

    def test_nominal_and_usable_capacity_are_distinct(self):
        spec = BatterySpec(12, 10, 0.1, 0.9, 5, 5, 0.95, 0.95, 1)
        self.assertEqual(spec.nominal_capacity_kwh, 12)
        self.assertEqual(spec.usable_capacity_kwh, 10)
        self.assertEqual(spec.soc_min_kwh, 1)
        self.assertEqual(spec.soc_max_kwh, 9)

    def test_temperature_outside_source_envelope_fails_closed(self):
        spec = BatterySpec(10, 10, 0, 1, 5, 5, 0.95, 0.95, 1, operating_temp_min_c=5, operating_temp_max_c=30)
        with self.assertRaises(BatteryModelError):
            BatteryEngine(spec, 5).step(requested_charge_kw=1, temperature_c=0)

    def test_standing_loss_is_not_silently_invented(self):
        with self.assertRaises(BatteryModelError):
            BatterySpec(10, 10, 0, 1, 5, 5, 0.95, 0.95, 1, standing_loss_fraction_per_timestep=0.01)

    def test_flexibility_uses_soc_and_power_headroom(self):
        engine = BatteryEngine(fixture_spec(), 5.0)
        flex = engine.flexibility()
        self.assertAlmostEqual(flex.max_additional_charge_kw, 5.0)
        self.assertAlmostEqual(flex.max_additional_discharge_kw, 4.75)
        self.assertAlmostEqual(flex.charge_energy_headroom_kwh, 5.0)
        self.assertAlmostEqual(flex.discharge_energy_available_kwh, 5.0)
        self.assertAlmostEqual(flex.physical_up_flex_kw, flex.max_additional_discharge_kw)
        self.assertAlmostEqual(flex.physical_down_flex_kw, flex.max_additional_charge_kw)

    def test_household_balance_accepts_b05_electric_load_without_calling_b05(self):
        balance = compute_household_balance(1.0, 2.0, 0.5, 4.0, 0.0, 0.0)
        self.assertAlmostEqual(balance.total_load_kw, 3.5)
        self.assertAlmostEqual(balance.grid_export_kw, 0.5)
        self.assertEqual(balance.export_status, "Q")

    def test_export_limit_is_explicit_scenario_not_legal_permission(self):
        balance = compute_household_balance(1, 0, 0, 5, 0, 0, export_limit_kw=2, export_permission_status="SCN")
        self.assertAlmostEqual(balance.grid_export_kw, 2)
        self.assertAlmostEqual(balance.export_curtailed_kw, 2)
        self.assertEqual(balance.export_status, "SCN")

    def test_b08_handoff_has_only_physical_fields(self):
        spec = fixture_spec()
        engine = BatteryEngine(spec, 5)
        result = engine.step(requested_discharge_kw=1)
        balance = compute_household_balance(2, 1, 0, 0, 0, result.actual_discharge_kw)
        handoff = make_b08_handoff(balance, result, spec)
        self.assertEqual(handoff.net_grid_import_kw, 2)
        self.assertEqual(handoff.battery_discharge_kw, 1)
        self.assertGreaterEqual(handoff.physical_up_flex_kw, 0)
        self.assertGreaterEqual(handoff.physical_down_flex_kw, 0)
        self.assertTrue(0 <= handoff.soc_fraction <= 1)

    def test_h_tariff_and_vpp_policy_gates_remain_q(self):
        rows = read_rows(ROOT / "registry" / "battery_variables.csv")
        gates = {row["variable_id"]: row["status"] for row in rows if row["variable_id"].startswith("VAR-B07-H-") or row["variable_id"] == "VAR-B07-VPP-ELIGIBILITY"}
        self.assertEqual(set(gates.values()), {"Q"})

    def test_product_evidence_is_eu_first_and_not_full_supply_chain_claim(self):
        rows = read_rows(ROOT / "data" / "processed" / "battery_product_evidence.csv")
        self.assertEqual({row["origin_status"] for row in rows}, {"OBS"})
        self.assertTrue(all("Germany" in row["origin_claim"] for row in rows))
        self.assertTrue(all("cell origin" in row["limitations"] for row in rows))

    def test_round_trip_efficiency_is_not_used_as_one_way_runtime_input(self):
        rows = read_rows(ROOT / "data" / "processed" / "battery_product_evidence.csv")
        varta = next(row for row in rows if row["product_id"].startswith("VARTA"))
        self.assertEqual(varta["efficiency_type"], "battery_efficiency")
        self.assertEqual(varta["efficiency_status"], "OBS")
        self.assertIn("not converted into one-way", varta["limitations"])

    def test_scn_fixture_never_becomes_obs(self):
        rows = read_rows(ROOT / "data" / "processed" / "battery_physical_fixture_results.csv")
        self.assertTrue(rows)
        self.assertEqual({row["status"] for row in rows}, {"SCN"})
        self.assertTrue(all(row["source_ids"] == "SRC-B07-SYNTHETIC-PHYSICAL-FIXTURE" for row in rows))

    def test_product_fixture_uses_source_power_but_explicit_scn_efficiency(self):
        product = read_rows(ROOT / "data" / "processed" / "battery_product_evidence.csv")[0]
        spec = BatterySpec(float(product["nominal_capacity_kwh"]), float(product["usable_capacity_kwh"]), 0, 1, float(product["max_charge_power_kw"]), float(product["max_discharge_power_kw"]), 0.95, 0.95, 1, capacity_boundary="USABLE", power_boundary=product["power_boundary"], efficiency_boundary="SCN_ONE_WAY", status="SCN", source_ids=(product["product_id"],))
        result = BatteryEngine(spec, 0).step(requested_charge_kw=2.5)
        self.assertEqual(result.status, "SCN")
        self.assertAlmostEqual(result.energy_added_to_storage_kwh, 2.375)


if __name__ == "__main__":
    unittest.main()
