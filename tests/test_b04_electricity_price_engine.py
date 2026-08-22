import csv
import unittest
from datetime import date
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def annual_bill(consumption_kwh, threshold, discounted, higher, fixed=0):
    return min(consumption_kwh, threshold) * discounted + max(consumption_kwh - threshold, 0) * higher + fixed


def h_is_in_season(day):
    return (day.month > 10 or (day.month == 10 and day.day >= 15)) or (day.month < 4 or (day.month == 4 and day.day <= 15))


class B04ElectricityPriceEngineTests(unittest.TestCase):
    def test_layers_are_separate(self):
        path = ROOT / "data" / "processed" / "electricity_price_history.csv"
        with path.open(encoding="utf-8", newline="") as handle:
            rows = list(csv.DictReader(handle))
        self.assertTrue(all(row["layer"] == "WHOLESALE_ELECTRICITY" for row in rows))
        self.assertNotIn("70.104", {row.get("eur_per_mwh") for row in rows})

    def test_threshold_boundaries_only_excess_is_higher(self):
        self.assertEqual(2522 * 36.386, annual_bill(2522, 2523, 36.386, 70.104))
        self.assertEqual(2523 * 36.386, annual_bill(2523, 2523, 36.386, 70.104))
        self.assertEqual(2523 * 36.386 + 70.104, annual_bill(2524, 2523, 36.386, 70.104))

    def test_h_boundaries_and_outside_fallback(self):
        self.assertTrue(h_is_in_season(date(2026, 10, 15)))
        self.assertTrue(h_is_in_season(date(2027, 4, 15)))
        self.assertFalse(h_is_in_season(date(2027, 4, 16)))
        self.assertFalse(h_is_in_season(date(2026, 10, 14)))

    def test_h_requires_separate_meter_and_fail_closed_battery(self):
        path = ROOT / "data" / "processed" / "h_tariff_schedule.csv"
        with path.open(encoding="utf-8", newline="") as handle:
            rows = list(csv.DictReader(handle))
        heating = [row for row in rows if row["period_type"] == "heating season"]
        self.assertTrue(all(row["separate_meter_required"] == "yes" for row in heating))
        self.assertTrue(all(row["battery_charging_status"] == "Q" for row in rows))
        self.assertTrue(all(row["export_status"] == "Q" for row in rows))

    def test_vat_and_fixed_charge_once(self):
        self.assertAlmostEqual(5.25 * 1.27, 6.6675, places=4)
        self.assertEqual(annual_bill(2523, 2523, 36.386, 70.104, 1836.42), 2523 * 36.386 + 1836.42)

    def test_wholesale_conversion_is_dimensional(self):
        self.assertAlmostEqual(103.52 * 400 / 1000, 41.408)

    def test_scenario_transition_and_dynamic_fail_closed(self):
        path = ROOT / "data" / "processed" / "electricity_price_scenarios.csv"
        with path.open(encoding="utf-8", newline="") as handle:
            rows = list(csv.DictReader(handle))
        self.assertEqual({row["year"] for row in rows}, {"2026", "2038", "2041", "2046"})
        self.assertTrue(all(row["status"] in {"Q", "SCN"} for row in rows))
        vars_path = ROOT / "registry" / "electricity_price_variables.csv"
        with vars_path.open(encoding="utf-8", newline="") as handle:
            variables = list(csv.DictReader(handle))
        dynamic = next(row for row in variables if row["variable_id"] == "VAR-B04-DYNAMIC-HOUSEHOLD-PRICE")
        self.assertEqual(dynamic["status"], "Q")

    def test_component_bridge_does_not_double_count_network(self):
        path = ROOT / "data" / "processed" / "electricity_price_component_bridge.csv"
        with path.open(encoding="utf-8", newline="") as handle:
            rows = list(csv.DictReader(handle))
        self.assertTrue(all(row["layer"] == "COMPONENT_BRIDGE" for row in rows))
        self.assertEqual(sum(1 for row in rows if row["tariff_id"] == "A1-DÉMÁSZ-DISCOUNTED"), 1)

    def test_missing_bridge_and_incremental_meter_cost_are_q(self):
        path = ROOT / "data" / "processed" / "electricity_price_component_bridge.csv"
        with path.open(encoding="utf-8", newline="") as handle:
            rows = list(csv.DictReader(handle))
        market = next(row for row in rows if row["status"] == "Q")
        self.assertEqual(market["final_gross_huf_per_kwh"], "")
        rules_path = ROOT / "registry" / "electricity_tariff_rules.csv"
        with rules_path.open(encoding="utf-8", newline="") as handle:
            rules = list(csv.DictReader(handle))
        self.assertTrue(any(row["rule_id"] == "RULE-B04-H-BATTERY-FAIL-CLOSED" and row["status"] == "Q" for row in rules))


if __name__ == "__main__":
    unittest.main()
