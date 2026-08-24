import csv
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def rows(path):
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


class B04HTariffBatteryBoundaryTests(unittest.TestCase):
    def test_three_canonical_gates_are_independent_and_fail_closed(self):
        variables = rows(ROOT / "registry" / "electricity_price_variables.csv")
        gates = {
            row["name"]: row
            for row in variables
            if row["name"].startswith("H_TARIFF_")
        }
        expected = {
            "H_TARIFF_BATTERY_CHARGE_ALLOWED",
            "H_TARIFF_BATTERY_DISCHARGE_ALLOWED",
            "H_TARIFF_EXPORT_ALLOWED",
        }
        self.assertEqual(expected, set(gates))
        for row in gates.values():
            self.assertEqual("Q", row["status"])
            self.assertIn("2026-08-24", row["notes"])
            self.assertIn("fail closed", row["notes"])
            self.assertTrue(row["source_ids"])
        self.assertNotEqual(gates["H_TARIFF_BATTERY_CHARGE_ALLOWED"]["variable_id"], gates["H_TARIFF_BATTERY_DISCHARGE_ALLOWED"]["variable_id"])
        self.assertNotEqual(gates["H_TARIFF_BATTERY_DISCHARGE_ALLOWED"]["variable_id"], gates["H_TARIFF_EXPORT_ALLOWED"]["variable_id"])

    def test_topology_rows_keep_h_side_and_hmke_questions_separate(self):
        rules = rows(ROOT / "registry" / "electricity_tariff_rules.csv")
        by_id = {row["rule_id"]: row for row in rules}
        required = {
            "RULE-B04-H-TOPOLOGY-H-ONLY-DEDICATED",
            "RULE-B04-H-TOPOLOGY-NORMAL-A1",
            "RULE-B04-H-TOPOLOGY-BATTERY-NORMAL-ONLY",
            "RULE-B04-H-TOPOLOGY-BATTERY-H-SIDE",
            "RULE-B04-H-TOPOLOGY-HYBRID-COMMON-BUS",
            "RULE-B04-H-TOPOLOGY-HMKE-EXPORT",
        }
        self.assertTrue(required <= set(by_id))
        self.assertEqual("OBS", by_id["RULE-B04-H-TOPOLOGY-H-ONLY-DEDICATED"]["status"])
        for rule_id in required - {"RULE-B04-H-TOPOLOGY-H-ONLY-DEDICATED"}:
            self.assertEqual("Q", by_id[rule_id]["status"])

    def test_gate_rules_pin_snapshot_applicability_and_sources(self):
        rules = rows(ROOT / "registry" / "electricity_tariff_rules.csv")
        gate_rules = {
            row["rule_type"]: row
            for row in rules
            if row["rule_type"] in {
                "battery_charge_authorization",
                "battery_discharge_authorization",
                "export_authorization",
            }
        }
        self.assertEqual(
            {
                "battery_charge_authorization",
                "battery_discharge_authorization",
                "export_authorization",
            },
            set(gate_rules),
        )
        for row in gate_rules.values():
            self.assertEqual("2026-08-24", row["valid_from"])
            self.assertEqual("Q", row["status"])
            self.assertIn("Snapshot applicability 2026-08-24", row["notes"])
            self.assertTrue(row["source_ids"])

    def test_processed_h_schedule_never_promotes_battery_or_export(self):
        schedule = rows(ROOT / "data" / "processed" / "h_tariff_schedule.csv")
        self.assertTrue(schedule)
        self.assertTrue(all(row["battery_charging_status"] == "Q" for row in schedule))
        self.assertTrue(all(row["export_status"] == "Q" for row in schedule))

    def test_physical_export_status_does_not_become_legal_permission(self):
        from modules.B07.engine import compute_household_balance

        balance = compute_household_balance(
            household_load_kw=0,
            heat_pump_load_kw=0,
            other_household_load_kw=0,
            onsite_generation_kw=2,
            battery_charge_kw=0,
            battery_discharge_kw=0,
            export_permission_status="Q",
        )
        self.assertEqual(2, balance.grid_export_kw)
        self.assertEqual("Q", balance.export_status)

    def test_b07_interface_remains_partial_but_gate_values_q(self):
        readiness = rows(ROOT / "registry" / "battery_readiness.csv")
        interface = next(row for row in readiness if row["component_id"] == "B04_TARIFF_INTERFACE")
        self.assertEqual("PARTIAL", interface["status"])
        self.assertEqual("20", interface["readiness_percent"])
        variables = rows(ROOT / "registry" / "battery_variables.csv")
        for gate in (
            "VAR-B07-H-TARIFF-CHARGE-ALLOWED",
            "VAR-B07-H-TARIFF-DISCHARGE-ALLOWED",
            "VAR-B07-H-TARIFF-EXPORT-ALLOWED",
        ):
            self.assertEqual("Q", next(row for row in variables if row["variable_id"] == gate)["status"])


if __name__ == "__main__":
    unittest.main()
