from __future__ import annotations

import hashlib
import unittest
from datetime import datetime, timezone

from modules.B10.dso_headroom_contract import (
    DsoHeadroomProvenance,
    EXTERNAL_ONLY_REUSE_UNRESOLVED,
    MVM_DEMASZ_DATASET_NAME,
    MVM_DEMASZ_DATA_URL,
    MVM_DEMASZ_METHOD_SOURCE_ID,
    MVM_DEMASZ_METHOD_URL,
    MVM_DEMASZ_PUBLISHER,
    MVM_DEMASZ_SOURCE_ID,
    REUSE_CLEARED,
    VERIFIED_AGAINST_SOURCE,
    parse_mvm_demasz_consumption_headroom_text,
)
from modules.B10.programme_node_demand_contract import (
    B10ProgrammeNodeDemandError,
    NODE_DEMAND_PROVEN,
    NO_DIVERSITY_OR_FLEX_AUTHORITY,
    ProgrammeDemandSnapshot,
    Q_NODE_DEMAND_UNRESOLVED,
    UNMANAGED_POSITIVE_PROGRAMME_IMPORT,
    aggregate_programme_node_demand,
    screen_programme_node_peak_against_mvm_headroom,
)
from modules.B10.spatial_authority_contract import (
    DSO_SUBSTATION,
    EXACT_NODE_PROVEN,
    Q_EXACT_NODE_UNRESOLVED,
    Q_SERVICE_AREA_UNRESOLVED,
    SERVICE_AREA_PROVEN,
    SpatialAuthorityDecision,
)


UTC = timezone.utc
T0 = datetime(2026, 1, 15, 17, 0, tzinfo=UTC)
T1 = datetime(2026, 1, 15, 18, 0, tzinfo=UTC)
NODE_A = "MVM_DEMASZ:ABCD:132KV"
NODE_B = "MVM_DEMASZ:EFGH:132KV"


def exact(entity: str, node: str = NODE_A, *, decision_status: str = "DER") -> SpatialAuthorityDecision:
    return SpatialAuthorityDecision(
        entity_id=entity,
        network_operator="DEMASZ",
        service_area_id=None,
        service_area_status=Q_SERVICE_AREA_UNRESOLVED,
        target_node_region_id=node,
        target_node_region_scheme=DSO_SUBSTATION,
        exact_node_status=EXACT_NODE_PROVEN,
        evidence_status=decision_status,
        source_refs=(f"MAP-{entity}",),
        reason="exact electrical node authority",
    )


def unresolved(entity: str) -> SpatialAuthorityDecision:
    return SpatialAuthorityDecision(
        entity_id=entity,
        network_operator="DEMASZ",
        service_area_id="DEMASZ-SA",
        service_area_status=SERVICE_AREA_PROVEN,
        target_node_region_id=None,
        target_node_region_scheme=DSO_SUBSTATION,
        exact_node_status=Q_EXACT_NODE_UNRESOLVED,
        evidence_status="Q",
        source_refs=(f"MAP-{entity}",),
        reason="service area only",
    )


def snapshot(
    entity: str,
    timestamp: datetime,
    mapping: SpatialAuthorityDecision,
    *,
    hp: float = 2.0,
    charge: float = 1.0,
    other: float = 0.0,
    status: str = "SCN",
    truth: str = "SCN",
) -> ProgrammeDemandSnapshot:
    return ProgrammeDemandSnapshot(
        timestamp=timestamp,
        timestep_hours=1.0,
        scope_id="P9-BOUNDED-SCN",
        source_entity_id=entity,
        truth_context=truth,
        evidence_status=status,
        source_refs=(f"LOAD-{entity}-{timestamp.hour}",),
        spatial_authority=mapping,
        heat_pump_import_kw=hp,
        battery_charge_import_kw=charge,
        other_programme_import_excluding_hp_and_battery_kw=other,
    )


def verified_mvm_headroom():
    text = (
        "network_operator\tstation_name\tstation_code\tn1_capacity_current_mw\tn1_capacity_5y_mw\tvoltage_kv\t"
        "winter_evening_load_current_mw\tfree_capacity_current_mw\twinter_evening_load_5y_mw\tfree_capacity_5y_mw\n"
        "DEMASZ\tAlpha\tABCD\t100\t100\t132\t70\t30\t75\t25\n"
    )
    provenance = DsoHeadroomProvenance(
        source_id=MVM_DEMASZ_SOURCE_ID,
        publisher=MVM_DEMASZ_PUBLISHER,
        dataset_name=MVM_DEMASZ_DATASET_NAME,
        source_url=MVM_DEMASZ_DATA_URL,
        methodology_source_id=MVM_DEMASZ_METHOD_SOURCE_ID,
        methodology_url=MVM_DEMASZ_METHOD_URL,
        retrieved_at=datetime(2026, 9, 2, 12, 0, tzinfo=UTC),
        license_decision=REUSE_CLEARED,
        raw_storage_policy="EXTERNAL_ONLY",
        extraction_verification=VERIFIED_AGAINST_SOURCE,
        source_pdf_sha256="a" * 64,
        normalized_text_sha256=hashlib.sha256(text.encode("utf-8")).hexdigest(),
    )
    return parse_mvm_demasz_consumption_headroom_text(text, provenance=provenance).records[0]


class TestB10P9ProgrammeNodeDemand(unittest.TestCase):
    def test_complete_explicit_panel_aggregates_same_timestamp_only(self):
        rows = (
            snapshot("H1", T0, exact("H1"), hp=2.0, charge=1.0),
            snapshot("H2", T0, exact("H2"), hp=3.0, charge=0.5),
            snapshot("H1", T1, exact("H1"), hp=4.0, charge=0.0),
            snapshot("H2", T1, exact("H2"), hp=1.0, charge=0.0),
        )
        result = aggregate_programme_node_demand(rows)
        self.assertEqual(result.status, NODE_DEMAND_PROVEN)
        self.assertEqual(len(result.rows), 2)
        self.assertEqual(result.rows[0].positive_programme_import_kw, 6.5)
        self.assertEqual(result.rows[1].positive_programme_import_kw, 5.0)
        self.assertEqual(result.peaks[0].peak_positive_programme_import_mw, 0.0065)
        self.assertEqual(result.peaks[0].peak_timestamps, (T0,))

    def test_components_remain_separate_and_sum_exactly(self):
        result = aggregate_programme_node_demand((snapshot("H1", T0, exact("H1"), hp=2.5, charge=1.25, other=0.75),))
        row = result.rows[0]
        self.assertEqual(row.heat_pump_import_kw, 2.5)
        self.assertEqual(row.battery_charge_import_kw, 1.25)
        self.assertEqual(row.other_programme_import_kw, 0.75)
        self.assertEqual(row.positive_programme_import_kw, 4.5)
        self.assertEqual(row.incremental_demand_mw, 0.0045)

    def test_no_nameplate_or_diversity_factor_api_is_minted(self):
        result = aggregate_programme_node_demand((snapshot("H1", T0, exact("H1")),))
        row = result.rows[0]
        self.assertEqual(row.demand_semantics, UNMANAGED_POSITIVE_PROGRAMME_IMPORT)
        self.assertEqual(row.management_authority, NO_DIVERSITY_OR_FLEX_AUTHORITY)
        self.assertFalse(hasattr(row, "diversity_factor"))
        self.assertFalse(hasattr(row, "managed_peak_mw"))
        self.assertFalse(hasattr(row, "battery_discharge_kw"))

    def test_exact_node_can_be_used_even_when_service_area_dimension_is_q(self):
        mapping = exact("H1", decision_status="Q")
        result = aggregate_programme_node_demand((snapshot("H1", T0, mapping),))
        self.assertEqual(result.status, NODE_DEMAND_PROVEN)
        self.assertEqual(result.rows[0].node_region_id, NODE_A)

    def test_service_area_without_exact_node_returns_q_and_no_numeric_rows(self):
        result = aggregate_programme_node_demand((snapshot("H1", T0, unresolved("H1")),))
        self.assertEqual(result.status, Q_NODE_DEMAND_UNRESOLVED)
        self.assertEqual(result.rows, ())
        self.assertEqual(result.peaks, ())
        self.assertEqual(result.unresolved_entity_ids, ("H1",))

    def test_q_demand_evidence_returns_q_and_no_numeric_rows(self):
        result = aggregate_programme_node_demand((snapshot("H1", T0, exact("H1"), status="Q"),))
        self.assertEqual(result.status, Q_NODE_DEMAND_UNRESOLVED)
        self.assertEqual(result.rows, ())

    def test_incomplete_entity_timestamp_panel_is_rejected(self):
        rows = (
            snapshot("H1", T0, exact("H1")),
            snapshot("H2", T0, exact("H2")),
            snapshot("H1", T1, exact("H1")),
        )
        with self.assertRaisesRegex(B10ProgrammeNodeDemandError, "incomplete programme entity/timestamp panel"):
            aggregate_programme_node_demand(rows)

    def test_duplicate_entity_timestamp_is_rejected(self):
        row = snapshot("H1", T0, exact("H1"))
        with self.assertRaisesRegex(B10ProgrammeNodeDemandError, "duplicate entity/timestamp"):
            aggregate_programme_node_demand((row, row))

    def test_entity_node_change_inside_panel_returns_q(self):
        rows = (
            snapshot("H1", T0, exact("H1", NODE_A)),
            snapshot("H1", T1, exact("H1", NODE_B)),
        )
        result = aggregate_programme_node_demand(rows)
        self.assertEqual(result.status, Q_NODE_DEMAND_UNRESOLVED)
        self.assertEqual(result.rows, ())
        self.assertEqual(result.unresolved_entity_ids, ("H1",))

    def test_mixed_truth_context_is_rejected(self):
        rows = (
            snapshot("H1", T0, exact("H1"), status="SCN", truth="SCN"),
            snapshot("H2", T0, exact("H2"), status="DER", truth="REAL"),
        )
        with self.assertRaisesRegex(B10ProgrammeNodeDemandError, "mixed REAL and SCN"):
            aggregate_programme_node_demand(rows)

    def test_negative_component_is_rejected(self):
        with self.assertRaisesRegex(B10ProgrammeNodeDemandError, "heat_pump_import_kw"):
            snapshot("H1", T0, exact("H1"), hp=-0.1)

    def test_headroom_handoff_uses_exact_node_and_is_screening_only(self):
        peak = aggregate_programme_node_demand((snapshot("H1", T0, exact("H1"), hp=2000.0, charge=0.0),)).peaks[0]
        assessment = screen_programme_node_peak_against_mvm_headroom(peak, verified_mvm_headroom())
        self.assertEqual(assessment.region_id, NODE_A)
        self.assertEqual(assessment.incremental_demand_mw, 2.0)
        self.assertEqual(assessment.published_headroom_mw, 30.0)
        self.assertEqual(assessment.evidence_status, "SCN")
        self.assertEqual(assessment.connection_authority, "MGT_REQUIRED")
        self.assertFalse(hasattr(assessment, "reinforcement_required"))
        self.assertFalse(hasattr(assessment, "hosting_capacity_mw"))

    def test_wrong_node_cannot_enter_headroom_screening(self):
        peak = aggregate_programme_node_demand((snapshot("H1", T0, exact("H1", NODE_B)),)).peaks[0]
        with self.assertRaisesRegex(ValueError, "exactly match"):
            screen_programme_node_peak_against_mvm_headroom(peak, verified_mvm_headroom())


if __name__ == "__main__":
    unittest.main()
