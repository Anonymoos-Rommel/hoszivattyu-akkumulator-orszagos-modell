import unittest
from dataclasses import replace
from datetime import datetime, timezone
from pathlib import Path

from modules.B08.engine import GridLoadAggregate, run_fixture as run_b08_fixture
from modules.B09.engine import B09ContractError, SupplyRecord, aggregate_adequacy, run_fixture


ROOT = Path(__file__).resolve().parents[1]
B08_FIXTURE = ROOT / "data/fixtures/b08_grid_load_scn.json"
B09_FIXTURE = ROOT / "data/fixtures/b09_supply_adequacy_scn.json"
SOURCE = ("SRC-B09-SCN-SUPPLY-FIXTURE",)


def unique_load_rows():
    rows = run_b08_fixture(B08_FIXTURE).rows
    unique = {}
    for row in rows:
        unique[(row.timestamp, row.region_id, row.region_scheme)] = row
    return tuple(unique[key] for key in sorted(unique))


def make_supply(load_rows, value_fn=lambda row, component: 0.0, *, component_ids=("G1", "G2"), timestep=None, status="SCN", truth="SCN"):
    result = []
    for row in load_rows:
        for component in component_ids:
            result.append(SupplyRecord(
                timestamp=row.timestamp,
                timestep_hours=row.timestep_hours if timestep is None else timestep,
                source_component_id=component, region_id=row.region_id,
                region_scheme=row.region_scheme, truth_context=truth,
                evidence_status=status, source_refs=SOURCE,
                delivered_generation_kw=value_fn(row, component),
            ))
    return result


class B09SupplyAdequacyTests(unittest.TestCase):
    def test_valid_bounded_scn_fixture_and_exact_expected_totals(self):
        result = run_fixture(B09_FIXTURE)
        self.assertEqual((result.status, result.truth_context, result.scope), ("SCN", "SCN", "BOUNDED_SCN_FIXTURE"))
        self.assertEqual(len(result.rows), 4)
        self.assertEqual(len(result.scope_total_rows), 2)
        self.assertEqual(result.scope_total_rows[0].residual_demand_kw, -0.5)
        self.assertEqual(result.scope_total_rows[1].residual_demand_kw, 2.0)
        self.assertEqual(result.peak_residual_demand_kw, 2.0)
        self.assertEqual(result.peak_surplus_supply_kw, 0.5)

    def test_positive_residual(self):
        loads = unique_load_rows()
        result = aggregate_adequacy(loads, make_supply(loads, lambda _row, _component: 0.0), scope="BOUNDED_SCN_FIXTURE")
        self.assertTrue(any(row.unserved_or_residual_load_kw > 0 for row in result.rows))

    def test_exact_balance(self):
        loads = unique_load_rows()
        result = aggregate_adequacy(loads, make_supply(loads, lambda row, component: max(row.net_grid_load_kw, 0.0) if component == "G1" else 0.0), scope="BOUNDED_SCN_FIXTURE")
        self.assertTrue(all(
            row.residual_demand_kw == 0
            if row.b08_net_grid_load_kw >= 0
            else row.residual_demand_kw == row.b08_net_grid_load_kw
            for row in result.rows
        ))

    def test_surplus(self):
        loads = unique_load_rows()
        result = aggregate_adequacy(loads, make_supply(loads, lambda row, component: max(row.net_grid_load_kw, 0.0) + (1.0 if component == "G1" else 0.0)), scope="BOUNDED_SCN_FIXTURE")
        self.assertTrue(any(row.surplus_supply_kw > 0 for row in result.rows))

    def test_explicit_zero_generation_is_valid(self):
        result = run_fixture(B09_FIXTURE)
        fixture = __import__("json").loads(B09_FIXTURE.read_text(encoding="utf-8"))
        self.assertTrue(any(record["delivered_generation_kw"] == 0 for record in fixture["supply_records"]))

    def test_missing_generation_row_rejected(self):
        loads = unique_load_rows()
        supplies = make_supply(loads)
        with self.assertRaises(B09ContractError):
            aggregate_adequacy(loads, supplies[:-1], scope="BOUNDED_SCN_FIXTURE")

    def test_duplicate_generation_key_rejected(self):
        loads = unique_load_rows()
        supplies = make_supply(loads)
        with self.assertRaises(B09ContractError):
            aggregate_adequacy(loads, supplies + [supplies[0]], scope="BOUNDED_SCN_FIXTURE")

    def test_naive_timestamp_rejected(self):
        with self.assertRaises(B09ContractError):
            SupplyRecord(datetime(2026, 1, 1), 1.0, "G1", "R1", "HU_COUNTY_SCN", "SCN", "SCN", SOURCE, 0.0)

    def test_inconsistent_timestep_rejected(self):
        loads = unique_load_rows()
        supplies = make_supply(loads)
        supplies[0] = replace(supplies[0], timestep_hours=0.5)
        with self.assertRaises(B09ContractError):
            aggregate_adequacy(loads, supplies, scope="BOUNDED_SCN_FIXTURE")

    def test_mixed_region_scheme_rejected(self):
        loads = unique_load_rows()
        supplies = make_supply(loads)
        supplies[0] = replace(supplies[0], region_scheme="OTHER_SCHEME")
        with self.assertRaises(B09ContractError):
            aggregate_adequacy(loads, supplies, scope="BOUNDED_SCN_FIXTURE")

    def test_incompatible_truth_and_scope_rejected(self):
        loads = unique_load_rows()
        supplies = make_supply(loads)
        with self.assertRaises(B09ContractError):
            aggregate_adequacy(loads, supplies, scope="BOUNDED_REAL_AGGREGATE")
        real_supply = make_supply(loads, status="OBS", truth="REAL")
        with self.assertRaises(B09ContractError):
            aggregate_adequacy(loads, real_supply, scope="BOUNDED_SCN_FIXTURE")

    def test_negative_generation_rejected(self):
        with self.assertRaises(B09ContractError):
            SupplyRecord(datetime(2026, 1, 1, tzinfo=timezone.utc), 1.0, "G1", "R1", "HU_COUNTY_SCN", "SCN", "SCN", SOURCE, -1.0)

    def test_half_hour_energy_conversion(self):
        loads = tuple(replace(row, timestep_hours=0.5) for row in unique_load_rows())
        supplies = make_supply(loads, lambda _row, _component: 0.0, timestep=0.5)
        result = aggregate_adequacy(loads, supplies, scope="BOUNDED_SCN_FIXTURE")
        row = result.rows[0]
        self.assertEqual(row.net_load_kwh, row.b08_net_grid_load_kw * 0.5)
        self.assertEqual(row.generation_kwh, 0.0)

    def test_negative_b08_net_load_is_preserved_as_surplus(self):
        loads = list(unique_load_rows())
        loads[0] = replace(loads[0], net_grid_load_kw=-2.0, net_kwh=-2.0)
        result = aggregate_adequacy(loads, make_supply(loads), scope="BOUNDED_SCN_FIXTURE")
        row = next(row for row in result.rows if row.timestamp == loads[0].timestamp and row.region_id == loads[0].region_id)
        self.assertEqual(row.residual_demand_kw, -2.0)
        self.assertEqual(row.surplus_supply_kw, 2.0)

    def test_b05_b07_electricity_is_not_added_again(self):
        loads = unique_load_rows()
        result = aggregate_adequacy(loads, make_supply(loads), scope="BOUNDED_SCN_FIXTURE")
        for row in result.rows:
            original = next(item for item in loads if item.timestamp == row.timestamp and item.region_id == row.region_id)
            self.assertEqual(row.b08_net_grid_load_kw, original.net_grid_load_kw)

    def test_b08_flexibility_does_not_change_adequacy(self):
        loads = unique_load_rows()
        altered = tuple(replace(row, physical_up_flex_kw=999.0, physical_down_flex_kw=999.0) for row in loads)
        supplies = make_supply(loads)
        first = aggregate_adequacy(loads, supplies, scope="BOUNDED_SCN_FIXTURE")
        second = aggregate_adequacy(altered, supplies, scope="BOUNDED_SCN_FIXTURE")
        self.assertEqual(tuple(row.residual_demand_kw for row in first.rows), tuple(row.residual_demand_kw for row in second.rows))

    def test_scn_output_is_bounded_not_national_or_real(self):
        result = run_fixture(B09_FIXTURE)
        self.assertEqual(result.scope_total_rows[0].region_id, "BOUNDED_SCOPE_TOTAL")
        self.assertNotEqual(result.scope, "HUNGARY_NATIONAL_VALIDATED")
        self.assertEqual(result.truth_context, "SCN")
        self.assertFalse(hasattr(result, "dispatch_kw"))
        self.assertFalse(hasattr(result, "storage_soc_kwh"))

    def test_unsupported_generation_boundary_and_missing_refs_fail_closed(self):
        with self.assertRaises(B09ContractError):
            SupplyRecord(datetime(2026, 1, 1, tzinfo=timezone.utc), 1.0, "G1", "R1", "HU_COUNTY_SCN", "SCN", "SCN", SOURCE, 0.0, boundary_id="H_TARIFF")
        with self.assertRaises(B09ContractError):
            SupplyRecord(datetime(2026, 1, 1, tzinfo=timezone.utc), 1.0, "G1", "R1", "HU_COUNTY_SCN", "SCN", "SCN", (), 0.0)

    def test_q_propagates_without_becoming_der(self):
        loads = unique_load_rows()
        supplies = make_supply(loads, status="Q")
        result = aggregate_adequacy(loads, supplies, scope="BOUNDED_SCN_FIXTURE")
        self.assertEqual(result.status, "Q")

    def test_assigned_or_policy_evidence_cannot_be_promoted(self):
        loads = list(unique_load_rows())
        loads[0] = replace(loads[0], evidence_status="ASS", evidence_statuses=("ASS",))
        with self.assertRaises(B09ContractError):
            aggregate_adequacy(loads, make_supply(loads), scope="BOUNDED_SCN_FIXTURE")
        loads[0] = replace(loads[0], evidence_status="POL", evidence_statuses=("POL",))
        with self.assertRaises(B09ContractError):
            aggregate_adequacy(loads, make_supply(loads), scope="BOUNDED_SCN_FIXTURE")


if __name__ == "__main__":
    unittest.main()
