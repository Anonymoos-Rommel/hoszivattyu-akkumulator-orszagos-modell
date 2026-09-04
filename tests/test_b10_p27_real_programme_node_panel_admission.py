from datetime import datetime, timezone
from pathlib import Path
import unittest

from modules.B10.programme_node_demand_contract import ProgrammeDemandSnapshot
from modules.B10.real_programme_node_panel_contract import (
    B10RealProgrammeNodePanelError,
    PROGRAMME_COHORT_MANIFEST,
    PROGRAMME_ENTITY_MEMBERSHIP,
    PROGRAMME_PANEL_TIMESTAMP,
    ProgrammeCohortEvidence,
    Q_REAL_PROGRAMME_NODE_PANEL_UNRESOLVED,
    REAL_PROGRAMME_NODE_PANEL_PROVEN,
    RealProgrammeCohortManifest,
    certify_real_programme_node_panel,
    require_real_programme_node_panel,
)
from modules.B10.spatial_authority_contract import (
    DSO_SERVICE_AREA_MEMBERSHIP,
    EXACT_DSO_SUBSTATION_MAPPING,
    NODE_REGION_GRAIN_BINDING,
    SpatialAuthorityEvidence,
    SpatialAuthorityRecord,
    classify_spatial_authority,
)


ROOT = Path(__file__).resolve().parents[1]
T0 = datetime(2026, 1, 15, 17, 0, tzinfo=timezone.utc)
T1 = datetime(2026, 1, 15, 18, 0, tzinfo=timezone.utc)
SCOPE = "PROGRAMME:REAL:2026:PILOT-A"
PROGRAMME = "HP-BATTERY-PROGRAMME"
COHORT = "PILOT-A-COHORT"
PANEL = "PANEL-2026-01-15"
NODE = "MVM_DEMASZ:CSON:132KV"
OPERATOR = "MVM_DEMASZ"
SERVICE = "MVM_DEMASZ:SERVICE_AREA"


def exact(entity: str):
    source_id = f"spatial:{entity}"
    evidence = SpatialAuthorityEvidence(
        source_id=source_id,
        authority_level=2,
        truth_status="OBS",
        supports=(
            DSO_SERVICE_AREA_MEMBERSHIP,
            EXACT_DSO_SUBSTATION_MAPPING,
            f"ENTITY_ID:{entity}",
            f"NETWORK_OPERATOR:{OPERATOR}",
            f"SERVICE_AREA_ID:{SERVICE}",
            f"NODE_REGION_ID:{NODE}",
            NODE_REGION_GRAIN_BINDING,
        ),
    )
    return classify_spatial_authority(
        SpatialAuthorityRecord(
            entity_id=entity,
            network_operator=OPERATOR,
            service_area_id=SERVICE,
            target_node_region_id=NODE,
            source_refs=(source_id,),
            evidence=(evidence,),
        )
    )


def snapshot(entity: str, timestamp: datetime, *, truth_context: str = "REAL"):
    return ProgrammeDemandSnapshot(
        timestamp=timestamp,
        timestep_hours=1.0,
        scope_id=SCOPE,
        source_entity_id=entity,
        truth_context=truth_context,
        evidence_status="OBS" if truth_context == "REAL" else "SCN",
        source_refs=(f"demand:{entity}:{timestamp.isoformat()}",),
        spatial_authority=exact(entity),
        heat_pump_import_kw=4.0,
        battery_charge_import_kw=1.0,
        other_programme_import_excluding_hp_and_battery_kw=0.0,
    )


def manifest(entities=("H1", "H2"), timestamps=(T0, T1), *, authoritative=True):
    source_id = "programme-register"
    supports = [
        PROGRAMME_COHORT_MANIFEST,
        f"PANEL_ID:{PANEL}",
        f"PROGRAMME_ID:{PROGRAMME}",
        f"COHORT_ID:{COHORT}",
        f"SCOPE_ID:{SCOPE}",
        f"EXPECTED_ENTITY_COUNT:{len(entities)}",
        f"EXPECTED_TIMESTAMP_COUNT:{len(timestamps)}",
    ]
    supports.extend(f"{PROGRAMME_ENTITY_MEMBERSHIP}:{entity}" for entity in entities)
    supports.extend(f"{PROGRAMME_PANEL_TIMESTAMP}:{timestamp.isoformat()}" for timestamp in timestamps)
    if not authoritative:
        supports.remove(PROGRAMME_COHORT_MANIFEST)
    evidence = ProgrammeCohortEvidence(
        source_id=source_id,
        authority_level=2,
        truth_status="OBS",
        supports=tuple(supports),
    )
    return RealProgrammeCohortManifest(
        panel_id=PANEL,
        programme_id=PROGRAMME,
        cohort_id=COHORT,
        scope_id=SCOPE,
        expected_entity_ids=tuple(entities),
        expected_timestamps=tuple(timestamps),
        source_refs=(source_id,),
        evidence=(evidence,),
    )


class B10P27RealProgrammeNodePanelAdmissionTests(unittest.TestCase):
    def test_exact_authoritative_real_cohort_plus_p9_panel_is_proven(self):
        rows = tuple(snapshot(entity, timestamp) for entity in ("H1", "H2") for timestamp in (T0, T1))
        decision = certify_real_programme_node_panel(manifest(), rows)
        self.assertEqual(REAL_PROGRAMME_NODE_PANEL_PROVEN, decision.status)
        self.assertEqual("OBS", decision.evidence_status)
        self.assertEqual(2, decision.expected_entity_count)
        self.assertEqual(2, decision.actual_entity_count)
        self.assertEqual(2, decision.expected_timestamp_count)
        self.assertEqual(2, decision.actual_timestamp_count)
        self.assertTrue(decision.node_demand_result.rows)
        self.assertFalse(decision.missing_entity_ids)
        self.assertFalse(decision.missing_timestamps)

    def test_internal_p9_completeness_does_not_prove_cohort_completeness(self):
        rows = tuple(snapshot("H1", timestamp) for timestamp in (T0, T1))
        decision = certify_real_programme_node_panel(manifest(), rows)
        self.assertEqual(Q_REAL_PROGRAMME_NODE_PANEL_UNRESOLVED, decision.status)
        self.assertIsNone(decision.node_demand_result)
        self.assertEqual(("H2",), decision.missing_entity_ids)

    def test_extra_entity_is_rejected(self):
        rows = tuple(snapshot(entity, timestamp) for entity in ("H1", "H2", "H3") for timestamp in (T0, T1))
        decision = certify_real_programme_node_panel(manifest(), rows)
        self.assertEqual(Q_REAL_PROGRAMME_NODE_PANEL_UNRESOLVED, decision.status)
        self.assertEqual(("H3",), decision.extra_entity_ids)

    def test_missing_timestamp_is_not_zero_imputed(self):
        rows = tuple(snapshot(entity, T0) for entity in ("H1", "H2"))
        decision = certify_real_programme_node_panel(manifest(), rows)
        self.assertEqual(Q_REAL_PROGRAMME_NODE_PANEL_UNRESOLVED, decision.status)
        self.assertEqual((T1,), decision.missing_timestamps)
        self.assertIsNone(decision.node_demand_result)

    def test_extra_timestamp_is_rejected(self):
        t2 = datetime(2026, 1, 15, 19, 0, tzinfo=timezone.utc)
        rows = tuple(snapshot(entity, timestamp) for entity in ("H1", "H2") for timestamp in (T0, T1, t2))
        decision = certify_real_programme_node_panel(manifest(), rows)
        self.assertEqual(Q_REAL_PROGRAMME_NODE_PANEL_UNRESOLVED, decision.status)
        self.assertEqual((t2,), decision.extra_timestamps)

    def test_unauthoritative_manifest_stays_q(self):
        rows = tuple(snapshot(entity, timestamp) for entity in ("H1", "H2") for timestamp in (T0, T1))
        decision = certify_real_programme_node_panel(manifest(authoritative=False), rows)
        self.assertEqual(Q_REAL_PROGRAMME_NODE_PANEL_UNRESOLVED, decision.status)
        self.assertIsNone(decision.node_demand_result)

    def test_scenario_rows_cannot_clear_real_programme_panel_blocker(self):
        rows = tuple(snapshot(entity, timestamp, truth_context="SCN") for entity in ("H1", "H2") for timestamp in (T0, T1))
        decision = certify_real_programme_node_panel(manifest(), rows)
        self.assertEqual(Q_REAL_PROGRAMME_NODE_PANEL_UNRESOLVED, decision.status)
        self.assertIn("rejects SCN", decision.reason)

    def test_scope_mismatch_stays_q(self):
        row = snapshot("H1", T0)
        bad = ProgrammeDemandSnapshot(
            timestamp=row.timestamp,
            timestep_hours=row.timestep_hours,
            scope_id="OTHER-SCOPE",
            source_entity_id=row.source_entity_id,
            truth_context=row.truth_context,
            evidence_status=row.evidence_status,
            source_refs=row.source_refs,
            spatial_authority=row.spatial_authority,
            heat_pump_import_kw=row.heat_pump_import_kw,
            battery_charge_import_kw=row.battery_charge_import_kw,
            other_programme_import_excluding_hp_and_battery_kw=row.other_programme_import_excluding_hp_and_battery_kw,
        )
        rows = (bad, snapshot("H1", T1), snapshot("H2", T0), snapshot("H2", T1))
        decision = certify_real_programme_node_panel(manifest(), rows)
        self.assertEqual(Q_REAL_PROGRAMME_NODE_PANEL_UNRESOLVED, decision.status)
        self.assertIn("scope", decision.reason)

    def test_p9_q_is_not_promoted(self):
        unresolved_spatial = classify_spatial_authority(
            SpatialAuthorityRecord(
                entity_id="H2",
                network_operator=OPERATOR,
                service_area_id=SERVICE,
                target_node_region_id=NODE,
                source_refs=("weak",),
                evidence=(
                    SpatialAuthorityEvidence(
                        source_id="weak",
                        authority_level=4,
                        truth_status="OBS",
                        supports=(
                            DSO_SERVICE_AREA_MEMBERSHIP,
                            f"ENTITY_ID:H2",
                            f"NETWORK_OPERATOR:{OPERATOR}",
                            f"SERVICE_AREA_ID:{SERVICE}",
                        ),
                    ),
                ),
            )
        )
        rows = [snapshot("H1", T0), snapshot("H1", T1), snapshot("H2", T0), snapshot("H2", T1)]
        rows[2] = ProgrammeDemandSnapshot(
            timestamp=T0,
            timestep_hours=1.0,
            scope_id=SCOPE,
            source_entity_id="H2",
            truth_context="REAL",
            evidence_status="OBS",
            source_refs=("demand:H2:T0",),
            spatial_authority=unresolved_spatial,
            heat_pump_import_kw=4.0,
            battery_charge_import_kw=1.0,
            other_programme_import_excluding_hp_and_battery_kw=0.0,
        )
        rows[3] = ProgrammeDemandSnapshot(
            timestamp=T1,
            timestep_hours=1.0,
            scope_id=SCOPE,
            source_entity_id="H2",
            truth_context="REAL",
            evidence_status="OBS",
            source_refs=("demand:H2:T1",),
            spatial_authority=unresolved_spatial,
            heat_pump_import_kw=4.0,
            battery_charge_import_kw=1.0,
            other_programme_import_excluding_hp_and_battery_kw=0.0,
        )
        decision = certify_real_programme_node_panel(manifest(), tuple(rows))
        self.assertEqual(Q_REAL_PROGRAMME_NODE_PANEL_UNRESOLVED, decision.status)
        self.assertIn("H2", decision.unresolved_entity_ids)
        self.assertIsNone(decision.node_demand_result)

    def test_require_real_panel_fails_closed(self):
        decision = certify_real_programme_node_panel(manifest(), ())
        with self.assertRaisesRegex(B10RealProgrammeNodePanelError, "proven REAL programme node panel"):
            require_real_programme_node_panel(decision)

    def test_registry_remains_header_only(self):
        lines = (ROOT / "registry/real_programme_node_panels.csv").read_text(encoding="utf-8").splitlines()
        self.assertEqual(1, len(lines))
        self.assertTrue(lines[0].startswith("panel_id,programme_id,cohort_id,scope_id,"))

    def test_source_pack_preserves_boundary_and_readiness(self):
        text = (ROOT / "docs/source_packs/P27_B10_REAL_PROGRAMME_NODE_PANEL_ADMISSION.md").read_text(encoding="utf-8")
        self.assertIn("P9 INTERNAL PANEL COMPLETENESS != PROGRAMME COHORT COMPLETENESS", text)
        self.assertIn("MISSING ENTITY/TIMESTAMP != ZERO", text)
        self.assertIn("NO_REAL_PROGRAMME_NODE_PANEL", text)
        self.assertIn("readiness remains 15%", text)


if __name__ == "__main__":
    unittest.main()
