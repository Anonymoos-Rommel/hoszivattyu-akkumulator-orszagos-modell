from __future__ import annotations

import unittest
from dataclasses import fields
from datetime import datetime, timezone

from modules.B10.managed_flex_survivability_contract import (
    B10ManagedFlexSurvivabilityError,
    COMMITTED_NOT_DELIVERED,
    DELIVERED_FLEX_PROVEN,
    FLEX_ACTIVATION,
    FLEX_COMMITMENT,
    FLEX_DELIVERY,
    FlexAuthorityEvidence,
    FlexDispatchSnapshot,
    MANAGED_NODE_LOAD_PROVEN,
    NETWORK_SURVIVABILITY,
    NetworkSurvivabilityEvidence,
    NetworkSurvivabilityRecord,
    PHYSICAL_FLEX_CAPABILITY,
    PHYSICAL_ONLY,
    Q_FLEX_AUTHORITY_UNRESOLVED,
    Q_MANAGED_NODE_LOAD_UNRESOLVED,
    Q_NETWORK_SURVIVABILITY_UNRESOLVED,
    SCN_DISPATCH_PROVEN,
    SCN_MANAGED_NODE_LOAD,
    SURVIVABILITY_PROVEN,
    build_managed_node_load,
    classify_flex_authority,
    evaluate_network_survivability,
)
from modules.B10.programme_node_demand_contract import ProgrammeDemandSnapshot
from modules.B10.spatial_authority_contract import (
    DSO_SUBSTATION,
    EXACT_NODE_PROVEN,
    Q_SERVICE_AREA_UNRESOLVED,
    SpatialAuthorityDecision,
)


T0 = datetime(2026, 1, 15, 17, 0, tzinfo=timezone.utc)
T1 = datetime(2026, 1, 15, 18, 0, tzinfo=timezone.utc)
NODE = "MVM_DEMASZ:ABCD:132KV"


def spatial(entity: str) -> SpatialAuthorityDecision:
    return SpatialAuthorityDecision(
        entity_id=entity,
        network_operator="DEMASZ",
        service_area_id=None,
        service_area_status=Q_SERVICE_AREA_UNRESOLVED,
        target_node_region_id=NODE,
        target_node_region_scheme=DSO_SUBSTATION,
        exact_node_status=EXACT_NODE_PROVEN,
        evidence_status="DER",
        source_refs=(f"spatial:{entity}",),
        reason="fixture exact node",
    )


def demand_panel(truth: str = "SCN") -> tuple[ProgrammeDemandSnapshot, ...]:
    status = "SCN" if truth == "SCN" else "DER"
    rows = []
    for entity, hp0, hp1 in (("H1", 3.0, 5.0), ("H2", 2.0, 4.0)):
        for timestamp, hp in ((T0, hp0), (T1, hp1)):
            rows.append(ProgrammeDemandSnapshot(
                timestamp=timestamp,
                timestep_hours=1.0,
                scope_id="P10-FIXTURE",
                source_entity_id=entity,
                truth_context=truth,
                evidence_status=status,
                source_refs=(f"demand:{entity}:{timestamp.hour}",),
                spatial_authority=spatial(entity),
                heat_pump_import_kw=hp,
                battery_charge_import_kw=0.0,
                other_programme_import_excluding_hp_and_battery_kw=0.0,
            ))
    return tuple(rows)


def support(entity: str, timestamp: datetime, *claims: str) -> tuple[str, ...]:
    return (
        *claims,
        f"ENTITY_ID:{entity}",
        f"NODE_REGION_ID:{NODE}",
        "NODE_REGION_GRAIN:DSO_SUBSTATION",
        f"TIMESTAMP:{timestamp.isoformat()}",
    )


def flex_row(
    entity: str,
    timestamp: datetime,
    *,
    truth: str = "SCN",
    physical: float = 2.0,
    committed: float = 0.0,
    dispatched: float = 0.0,
    delivered: float = 0.0,
    claims: tuple[str, ...] = (PHYSICAL_FLEX_CAPABILITY,),
    node: str = NODE,
) -> FlexDispatchSnapshot:
    evidence_status = "SCN" if truth == "SCN" else "DER"
    source_id = f"flex:{entity}:{timestamp.hour}"
    return FlexDispatchSnapshot(
        timestamp=timestamp,
        timestep_hours=1.0,
        scope_id="P10-FIXTURE",
        source_entity_id=entity,
        node_region_id=node,
        truth_context=truth,
        physical_up_flex_kw=physical,
        committed_up_flex_kw=committed,
        dispatched_up_flex_kw=dispatched,
        delivered_up_flex_kw=delivered,
        source_refs=(source_id,),
        evidence=(FlexAuthorityEvidence(source_id, 2, evidence_status, support(entity, timestamp, *claims)),),
    )


def flex_panel(**overrides) -> tuple[FlexDispatchSnapshot, ...]:
    rows = []
    for entity in ("H1", "H2"):
        for timestamp in (T0, T1):
            values = overrides.get((entity, timestamp), {})
            rows.append(flex_row(entity, timestamp, **values))
    return tuple(rows)


class B10P10ManagedFlexTests(unittest.TestCase):
    def test_physical_capability_is_not_managed_reduction(self) -> None:
        decision = classify_flex_authority(flex_row("H1", T0))
        self.assertEqual(decision.authority_status, PHYSICAL_ONLY)
        self.assertEqual(decision.usable_managed_reduction_kw, 0.0)

    def test_commitment_is_not_delivery(self) -> None:
        row = flex_row(
            "H1", T0,
            committed=1.5,
            claims=(PHYSICAL_FLEX_CAPABILITY, FLEX_COMMITMENT),
        )
        decision = classify_flex_authority(row)
        self.assertEqual(decision.authority_status, COMMITTED_NOT_DELIVERED)
        self.assertEqual(decision.usable_managed_reduction_kw, 0.0)

    def test_scn_dispatch_can_reduce_only_with_bound_activation(self) -> None:
        row = flex_row(
            "H1", T0,
            committed=1.5,
            dispatched=1.0,
            claims=(PHYSICAL_FLEX_CAPABILITY, FLEX_ACTIVATION),
        )
        decision = classify_flex_authority(row)
        self.assertEqual(decision.authority_status, SCN_DISPATCH_PROVEN)
        self.assertEqual(decision.usable_managed_reduction_kw, 1.0)

    def test_numeric_dispatch_without_activation_is_q(self) -> None:
        row = flex_row("H1", T0, committed=1.5, dispatched=1.0)
        decision = classify_flex_authority(row)
        self.assertEqual(decision.authority_status, Q_FLEX_AUTHORITY_UNRESOLVED)
        self.assertIsNone(decision.usable_managed_reduction_kw)

    def test_real_dispatch_without_delivery_cannot_reduce_load(self) -> None:
        row = flex_row(
            "H1", T0,
            truth="REAL",
            committed=1.5,
            dispatched=1.0,
            claims=(PHYSICAL_FLEX_CAPABILITY, FLEX_COMMITMENT, FLEX_ACTIVATION),
        )
        self.assertEqual(classify_flex_authority(row).authority_status, Q_FLEX_AUTHORITY_UNRESOLVED)

    def test_real_delivered_flex_requires_commit_activation_and_delivery(self) -> None:
        row = flex_row(
            "H1", T0,
            truth="REAL",
            committed=1.5,
            dispatched=1.0,
            delivered=0.8,
            claims=(PHYSICAL_FLEX_CAPABILITY, FLEX_COMMITMENT, FLEX_ACTIVATION, FLEX_DELIVERY),
        )
        decision = classify_flex_authority(row)
        self.assertEqual(decision.authority_status, DELIVERED_FLEX_PROVEN)
        self.assertEqual(decision.usable_managed_reduction_kw, 0.8)

    def test_managed_load_uses_exact_entity_lineage_and_dispatch(self) -> None:
        overrides = {
            ("H1", T1): {
                "committed": 2.0,
                "dispatched": 2.0,
                "claims": (PHYSICAL_FLEX_CAPABILITY, FLEX_ACTIVATION),
            },
            ("H2", T1): {
                "committed": 1.0,
                "dispatched": 1.0,
                "claims": (PHYSICAL_FLEX_CAPABILITY, FLEX_ACTIVATION),
            },
        }
        result = build_managed_node_load(demand_panel(), flex_panel(**overrides))
        self.assertEqual(result.status, SCN_MANAGED_NODE_LOAD)
        t1 = next(row for row in result.rows if row.timestamp == T1)
        self.assertAlmostEqual(t1.unmanaged_programme_import_mw, 0.009)
        self.assertAlmostEqual(t1.proven_managed_reduction_mw, 0.003)
        self.assertAlmostEqual(t1.managed_programme_import_mw, 0.006)
        self.assertEqual(result.peak_managed_import_mw_by_node, ((NODE, 0.006),))

    def test_missing_flex_entity_fails_closed_not_zero(self) -> None:
        rows = tuple(row for row in flex_panel() if row.source_entity_id == "H1")
        with self.assertRaisesRegex(B10ManagedFlexSurvivabilityError, "exactly the P9 entities"):
            build_managed_node_load(demand_panel(), rows)

    def test_wrong_flex_node_is_rejected(self) -> None:
        rows = list(flex_panel())
        rows[0] = flex_row("H1", T0, node="OTHER:NODE")
        with self.assertRaisesRegex(B10ManagedFlexSurvivabilityError, "exact P9/P8"):
            build_managed_node_load(demand_panel(), rows)

    def test_one_unresolved_flex_row_removes_all_numeric_managed_results(self) -> None:
        overrides = {
            ("H1", T1): {"committed": 1.0, "dispatched": 1.0},
        }
        result = build_managed_node_load(demand_panel(), flex_panel(**overrides))
        self.assertEqual(result.status, Q_MANAGED_NODE_LOAD_UNRESOLVED)
        self.assertEqual(result.rows, ())
        self.assertEqual(result.peak_managed_import_mw_by_node, ())

    def test_managed_load_does_not_mint_survivability_or_reinforcement_fields(self) -> None:
        names = {field.name for field in fields(type(build_managed_node_load(demand_panel(), flex_panel())))}
        self.assertNotIn("network_survivability", names)
        self.assertNotIn("hosting_capacity_mw", names)
        self.assertNotIn("reinforcement_required", names)
        self.assertNotIn("programme_incremental_capex_huf", names)

    def test_survivability_requires_claim_specific_network_study(self) -> None:
        evidence = NetworkSurvivabilityEvidence(
            "study", 2, "OBS",
            ("NODE_REGION_ID:" + NODE, "NODE_REGION_GRAIN:DSO_SUBSTATION"),
        )
        record = NetworkSurvivabilityRecord("DEMASZ", "NS-1", NODE, 0.006, ("study",), (evidence,))
        decision = evaluate_network_survivability(record)
        self.assertEqual(decision.status, Q_NETWORK_SURVIVABILITY_UNRESOLVED)
        self.assertIsNone(decision.assessed_managed_peak_mw)

    def test_exact_network_study_can_prove_survivability_without_minting_capex(self) -> None:
        supports = (
            NETWORK_SURVIVABILITY,
            "NETWORK_OPERATOR:DEMASZ",
            "NETWORK_STUDY_ID:NS-1",
            "NODE_REGION_ID:" + NODE,
            "NODE_REGION_GRAIN:DSO_SUBSTATION",
            "ASSESSED_MANAGED_PEAK_MW:0.006",
        )
        evidence = NetworkSurvivabilityEvidence("study", 1, "OBS", supports)
        record = NetworkSurvivabilityRecord("DEMASZ", "NS-1", NODE, 0.006, ("study",), (evidence,))
        decision = evaluate_network_survivability(record)
        self.assertEqual(decision.status, SURVIVABILITY_PROVEN)
        self.assertEqual(decision.assessed_managed_peak_mw, 0.006)
        self.assertNotIn("programme_incremental_capex_huf", {field.name for field in fields(type(decision))})

    def test_real_managed_panel_with_delivered_flex_is_der_or_obs_not_scn(self) -> None:
        overrides = {}
        for entity in ("H1", "H2"):
            for timestamp in (T0, T1):
                overrides[(entity, timestamp)] = {
                    "truth": "REAL",
                    "committed": 1.0,
                    "dispatched": 1.0,
                    "delivered": 0.5,
                    "claims": (PHYSICAL_FLEX_CAPABILITY, FLEX_COMMITMENT, FLEX_ACTIVATION, FLEX_DELIVERY),
                }
        result = build_managed_node_load(demand_panel("REAL"), flex_panel(**overrides))
        self.assertEqual(result.status, MANAGED_NODE_LOAD_PROVEN)
        self.assertTrue(all(row.evidence_status in {"OBS", "DER"} for row in result.rows))


if __name__ == "__main__":
    unittest.main()
