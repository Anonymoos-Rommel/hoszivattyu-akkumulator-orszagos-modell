import csv
import unittest
from pathlib import Path

from modules.B07.engine import BatteryEngine, BatterySpec, make_b08_handoff, compute_household_balance


ROOT = Path(__file__).resolve().parents[1]


def read_rows(path):
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


class B07P2EfficiencyEvidenceTests(unittest.TestCase):
    def setUp(self):
        self.products = {
            row["product_id"]: row
            for row in read_rows(ROOT / "registry" / "battery_products.csv")
        }
        self.evidence = {
            row["product_id"]: row
            for row in read_rows(ROOT / "data" / "processed" / "battery_product_evidence.csv")
        }

    def test_varta_battery_only_efficiency_is_not_ac_grid_one_way(self):
        row = self.products["VARTA-PULSE-NEO-6"]
        self.assertEqual("0.978", row["efficiency_value"])
        self.assertEqual("battery_efficiency", row["efficiency_type"])
        self.assertEqual("BATTERY_ONLY", row["efficiency_boundary"])
        self.assertEqual("Q", row["charge_efficiency_status"])
        self.assertEqual("Q", row["discharge_efficiency_status"])
        self.assertEqual("Q", row["round_trip_efficiency_status"])

    def test_sonnen_unspecified_boundary_is_q(self):
        row = self.products["SONNEN-BATTERY-10-PERFORMANCE"]
        self.assertEqual("Q", row["efficiency_status"])
        self.assertEqual("UNSPECIFIED", row["efficiency_boundary"])
        self.assertEqual("Q", row["charge_efficiency_status"])
        self.assertEqual("Q", row["discharge_efficiency_status"])
        self.assertEqual("Q", row["round_trip_efficiency_status"])

    def test_direction_specific_fields_are_present_for_each_product(self):
        for row in self.products.values():
            for field in (
                "charge_efficiency_value",
                "charge_efficiency_status",
                "discharge_efficiency_value",
                "discharge_efficiency_status",
                "round_trip_efficiency_value",
                "round_trip_efficiency_status",
                "efficiency_boundary",
            ):
                self.assertIn(field, row)
            self.assertTrue(row["efficiency_boundary"])
            self.assertIn(row["charge_efficiency_status"], {"Q", "OBS", "DER", "ASS", "SCN", "POL"})
            self.assertIn(row["discharge_efficiency_status"], {"Q", "OBS", "DER", "ASS", "SCN", "POL"})

    def test_source_model_mismatch_cannot_promote_efficiency(self):
        sources = {row["source_id"]: row for row in read_rows(ROOT / "registry" / "battery_sources.csv")}
        for row in self.products.values():
            refs = [item for item in row["source_ids"].split(";") if item]
            self.assertTrue(refs)
            self.assertTrue(all(item in sources for item in refs))
            if row["charge_efficiency_status"] == "OBS":
                self.assertTrue(row["charge_efficiency_value"])
            if row["discharge_efficiency_status"] == "OBS":
                self.assertTrue(row["discharge_efficiency_value"])

    def test_processed_evidence_matches_registry_boundary_status(self):
        for product_id, row in self.products.items():
            evidence = self.evidence[product_id]
            for field in (
                "charge_efficiency_value",
                "charge_efficiency_status",
                "discharge_efficiency_value",
                "discharge_efficiency_status",
                "round_trip_efficiency_value",
                "round_trip_efficiency_status",
                "efficiency_boundary",
            ):
                self.assertEqual(row[field], evidence[field], field)

    def test_scn_one_way_fixture_remains_single_application(self):
        spec = BatterySpec(
            10, 10, 0, 1, 5, 5, 0.95, 0.90, 1,
            efficiency_boundary="SCN_ONE_WAY", status="SCN",
        )
        engine = BatteryEngine(spec, 0)
        charged = engine.step(requested_charge_kw=5)
        self.assertAlmostEqual(charged.energy_added_to_storage_kwh, 4.75)
        discharged = BatteryEngine(spec, charged.soc_after_kwh).step(requested_discharge_kw=1)
        self.assertAlmostEqual(discharged.discharge_energy_to_load_grid_kwh, 1)
        self.assertAlmostEqual(discharged.energy_removed_from_storage_kwh, 1 / 0.90)

    def test_b08_handoff_keeps_grid_import_export_physical_semantics(self):
        spec = BatterySpec(10, 10, 0, 1, 5, 5, 0.95, 0.95, 1, status="SCN")
        engine = BatteryEngine(spec, 5)
        result = engine.step(requested_discharge_kw=1)
        balance = compute_household_balance(2, 0, 0, 0, 0, result.actual_discharge_kw)
        handoff = make_b08_handoff(balance, result, spec)
        self.assertEqual(handoff.net_grid_import_kw, 1)
        self.assertEqual(handoff.net_grid_export_kw, 0)
        self.assertEqual(handoff.status, "SCN")
        self.assertEqual(handoff.timestep_hours, spec.timestep_hours)


if __name__ == "__main__":
    unittest.main()
