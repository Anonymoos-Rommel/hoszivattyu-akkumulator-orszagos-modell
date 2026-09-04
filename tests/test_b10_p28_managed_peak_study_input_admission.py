from datetime import datetime, timezone
from pathlib import Path
import unittest

from modules.B10.managed_flex_survivability_contract import (
    FLEX_ACTIVATION,
    FLEX_COMMITMENT,
    FLEX_DELIVERY,
    PHYSICAL_FLEX_CAPABILITY,
    FlexAuthorityEvidence,
    FlexDispatchSnapshot,
)
from modules.B10.managed_peak_study_input_contract import (
    B10ManagedPeakStudyInputError,
    MANAGED_PEAK_STUDY_INPUT,
    ManagedPeakStudyInputEvidence,
    ManagedPeakStudyInputRecord,
    Q_REAL_MANAGED_PEAK_STUDY_INPUT_UNRESOLVED,
    REAL_MANAGED_PEAK_STUDY_INPUT_PROVEN,
    certify_real_managed_peak_study_input,
    require_real_managed_peak_study_input,
    require_study_node_peak,
)
from modules.B10.programme_node_demand_contract import ProgrammeDemandSnapshot
from modules.B10.real_programme_node_panel_contract import (
    PROGRAMME_COHORT_MANIFEST,
    PROGRAMME_ENTITY_MEMBERSHIP,
    PROGRAMME_PANEL_TIMESTAMP,
    ProgrammeCohortEvidence,
    RealProgrammeCohortManifest,
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
NODE = "MVM_DEMASZ:CSON:132KV"
OPERATOR = "MVM_DEMASZ"
SERVICE = "MVM_DEMASZ:SERVICE_AREA"
SCOPE = "PROGRAMME:REAL:2026:PILOT-A"
PROGRAMME = "HP-BATTERY-PROGRAMME"
COHORT = "PILOT-A-COHORT"
PANEL = "PANEL-2026-01-15"
STUDY = "DSO-STUDY-2026-01"
CASE = "CASE-MANAGED-PEAK-A"
INPUT_ID = "STUDY-INPUT-A"


def exact(entity: str):
    sid = f"spatial:{entity}"
    evidence = SpatialAuthorityEvidence(
        sid,
        2,
        "OBS",
        (
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
            source_refs=(sid,),
            evidence=(evidence,),
        )
    )


def demand_rows():
    rows = []
    for entity, hp0, hp1 in (("H1", 3.0, 5.0), ("H2", 2.0, 4.0)):
        for timestamp, hp in ((T0, hp0), (T1, hp1)):
            rows.append(
                ProgrammeDemandSnapshot(
                    timestamp=timestamp,
                    timestep_hours=1.0,
                    scope_id=SCOPE,
                    source_entity_id=entity,
                    truth_context="REAL",
                    evidence_status="OBS",
                    source_refs=(f"demand:{entity}:{timestamp.hour}",),
                    spatial_authority=exact(entity),
                    heat_pump_import_kw=hp,
                    battery_charge_import_kw=0.0,
                    other_programme_import_excluding_hp_and_battery_kw=0.0,
                )
            )
    return tuple(rows)


def cohort_manifest():
    source_id = "programme-register"
    supports = [
        PROGRAMME_COHORT_MANIFEST,
        f"PANEL_ID:{PANEL}",
        f"PROGRAMME_ID:{PROGRAMME}",
        f"COHORT_ID:{COHORT}",
        f"SCOPE_ID:{SCOPE}",
        "EXPECTED_ENTITY_COUNT:2",
        "EXPECTED_TIMESTAMP_COUNT:2",
    ]
    supports.extend(f"{PROGRAMME_ENTITY_MEMBERSHIP}:{entity}" for entity in ("H1", "H2"))
    supports.extend(f"{PROGRAMME_PANEL_TIMESTAMP}:{timestamp.isoformat()}" for timestamp in (T0, T1))
    evidence = ProgrammeCohortEvidence(source_id, 2, "OBS", tuple(supports))
    return RealProgrammeCohortManifest(
        panel_id=PANEL,
        programme_id=PROGRAMME,
        cohort_id=COHORT,
        scope_id=SCOPE,
        expected_entity_ids=("H1", "H2"),
        expected_timestamps=(T0, T1),
        source_refs=(source_id,),
        evidence=(evidence,),
    )


def flex_support(entity: str, timestamp: datetime):
    return (
        PHYSICAL_FLEX_CAPABILITY,
        FLEX_COMMITMENT,
        FLEX_ACTIVATION,
        FLEX_DELIVERY,
        f"ENTITY_ID:{entity}",
        f"NODE_REGION_ID:{NODE}",
        "NODE_REGION_GRAIN:DSO_SUBSTATION",
        f"TIMESTAMP:{timestamp.isoformat()}",
    )


def flex_rows():
    rows = []
    for entity in ("H1", "H2"):
        for timestamp in (T0, T1):
            delivered = 1.5 if timestamp == T1 and entity == "H1" else (0.5 if timestamp == T1 else 0.0)
            sid = f"flex:{entity}:{timestamp.hour}"
            rows.append(
                FlexDispatchSnapshot(
                    timestamp=timestamp,
                    timestep_hours=1.0,
                    scope_id=SCOPE,
                    source_entity_id=entity,
                    node_region_id=NODE,
                    truth_context="REAL",
                    physical_up_flex_kw=2.0,
                    committed_up_flex_kw=delivered,
                    dispatched_up_flex_kw=delivered,
                    delivered_up_flex_kw=delivered,
                    source_refs=(sid,),
                    evidence=(FlexAuthorityEvidence(sid, 2, "OBS", flex_support(entity, timestamp)),),
                )
            )
    return tuple(rows)


def study_record(*, authoritative=True, bound_peak=0.007, panel_id=PANEL):
    source_id = "network-study-input"
    supports = [
        MANAGED_PEAK_STUDY_INPUT,
        f"STUDY_INPUT_ID:{INPUT_ID}",
        f"NETWORK_OPERATOR:{OPERATOR}",
        f"NETWORK_STUDY_ID:{STUDY}",
        f"STUDY_CASE_ID:{CASE}",
        f"PANEL_ID:{panel_id}",
        f"PROGRAMME_ID:{PROGRAMME}",
        f"COHORT_ID:{COHORT}",
        f"SCOPE_ID:{SCOPE}",
        "HORIZON:CURRENT",
        "TRUTH_CONTEXT:REAL",
        "NODE_REGION_GRAIN:DSO_SUBSTATION",
        "EXPECTED_NODE_COUNT:1",
        f"STUDY_NODE:{NODE}",
        f"MANAGED_PEAK_MW:{NODE}:{bound_peak}",
    ]
    if not authoritative:
        supports.remove(MANAGED_PEAK_STUDY_INPUT)
    evidence = ManagedPeakStudyInputEvidence(source_id, 1, "OBS", tuple(supports))
    return ManagedPeakStudyInputRecord(
        study_input_id=INPUT_ID,
        network_operator=OPERATOR,
        network_study_id=STUDY,
        study_case_id=CASE,
        panel_id=panel_id,
        programme_id=PROGRAMME,
        cohort_id=COHORT,
        scope_id=SCOPE,
        horizon="CURRENT",
        source_refs=(source_id,),
        evidence=(evidence,),
    )


class B10P28ManagedPeakStudyInputAdmissionTests(unittest.TestCase):
    def test_exact_p27_p10_lineage_plus_study_binding_is_proven(self):
        decision = certify_real_managed_peak_study_input(
            study_record(),
            cohort_manifest=cohort_manifest(),
            programme_snapshots=demand_rows(),
            flex_snapshots=flex_rows(),
        )
        self.assertEqual(REAL_MANAGED_PEAK_STUDY_INPUT_PROVEN, decision.status)
        self.assertEqual("OBS", decision.evidence_status)
        self.assertEqual(1, len(decision.nodes))
        self.assertEqual(NODE, decision.nodes[0].node_region_id)
        self.assertAlmostEqual(0.007, decision.nodes[0].assessed_managed_peak_mw)
        self.assertTrue(decision.managed_load_result.rows)

    def test_numeric_peak_without_claim_specific_binding_stays_q(self):
        decision = certify_real_managed_peak_study_input(
            study_record(authoritative=False),
            cohort_manifest=cohort_manifest(),
            programme_snapshots=demand_rows(),
            flex_snapshots=flex_rows(),
        )
        self.assertEqual(Q_REAL_MANAGED_PEAK_STUDY_INPUT_UNRESOLVED, decision.status)
        self.assertFalse(decision.nodes)
        self.assertIsNone(decision.managed_load_result)

    def test_wrong_bound_peak_stays_q_even_if_close(self):
        decision = certify_real_managed_peak_study_input(
            study_record(bound_peak=0.006999),
            cohort_manifest=cohort_manifest(),
            programme_snapshots=demand_rows(),
            flex_snapshots=flex_rows(),
        )
        self.assertEqual(Q_REAL_MANAGED_PEAK_STUDY_INPUT_UNRESOLVED, decision.status)
        self.assertIn("managed node peaks", decision.reason)

    def test_panel_identity_substitution_is_rejected(self):
        decision = certify_real_managed_peak_study_input(
            study_record(panel_id="OTHER-PANEL"),
            cohort_manifest=cohort_manifest(),
            programme_snapshots=demand_rows(),
            flex_snapshots=flex_rows(),
        )
        self.assertEqual(Q_REAL_MANAGED_PEAK_STUDY_INPUT_UNRESOLVED, decision.status)
        self.assertIn("panel_id", decision.reason)

    def test_incomplete_real_cohort_cannot_enter_study(self):
        rows = tuple(row for row in demand_rows() if row.source_entity_id == "H1")
        decision = certify_real_managed_peak_study_input(
            study_record(),
            cohort_manifest=cohort_manifest(),
            programme_snapshots=rows,
            flex_snapshots=tuple(row for row in flex_rows() if row.source_entity_id == "H1"),
        )
        self.assertEqual(Q_REAL_MANAGED_PEAK_STUDY_INPUT_UNRESOLVED, decision.status)
        self.assertIn("P27 REAL programme node panel is not proven", decision.reason)

    def test_unresolved_real_flex_cannot_enter_study(self):
        rows = list(flex_rows())
        row = rows[-1]
        sid = "weak-flex"
        rows[-1] = FlexDispatchSnapshot(
            timestamp=row.timestamp,
            timestep_hours=row.timestep_hours,
            scope_id=row.scope_id,
            source_entity_id=row.source_entity_id,
            node_region_id=row.node_region_id,
            truth_context=row.truth_context,
            physical_up_flex_kw=2.0,
            committed_up_flex_kw=1.0,
            dispatched_up_flex_kw=1.0,
            delivered_up_flex_kw=1.0,
            source_refs=(sid,),
            evidence=(FlexAuthorityEvidence(sid, 2, "OBS", (PHYSICAL_FLEX_CAPABILITY,)),),
        )
        decision = certify_real_managed_peak_study_input(
            study_record(),
            cohort_manifest=cohort_manifest(),
            programme_snapshots=demand_rows(),
            flex_snapshots=tuple(rows),
        )
        self.assertEqual(Q_REAL_MANAGED_PEAK_STUDY_INPUT_UNRESOLVED, decision.status)
        self.assertIn("P10 REAL managed node load is unresolved", decision.reason)

    def test_require_functions_fail_closed(self):
        decision = certify_real_managed_peak_study_input(
            study_record(authoritative=False),
            cohort_manifest=cohort_manifest(),
            programme_snapshots=demand_rows(),
            flex_snapshots=flex_rows(),
        )
        with self.assertRaisesRegex(B10ManagedPeakStudyInputError, "proven REAL managed-peak study input"):
            require_real_managed_peak_study_input(decision)
        with self.assertRaisesRegex(B10ManagedPeakStudyInputError, "proven REAL managed-peak study input"):
            require_study_node_peak(decision, NODE)

    def test_wrong_node_lookup_fails_closed_on_proven_study_input(self):
        decision = certify_real_managed_peak_study_input(
            study_record(),
            cohort_manifest=cohort_manifest(),
            programme_snapshots=demand_rows(),
            flex_snapshots=flex_rows(),
        )
        with self.assertRaisesRegex(B10ManagedPeakStudyInputError, "not uniquely proven"):
            require_study_node_peak(decision, "OTHER:NODE")

    def test_registry_is_header_only(self):
        lines = (ROOT / "registry/managed_peak_study_inputs.csv").read_text(encoding="utf-8").splitlines()
        self.assertEqual(1, len(lines))
        self.assertTrue(lines[0].startswith("study_input_id,network_operator,network_study_id,"))

    def test_source_pack_keeps_downstream_claims_separate_and_readiness_15(self):
        text = (ROOT / "docs/source_packs/P28_B10_MANAGED_PEAK_STUDY_INPUT_ADMISSION.md").read_text(encoding="utf-8")
        self.assertIn("P10 MANAGED NODE LOAD != NETWORK STUDY INPUT", text)
        self.assertIn("STUDY INPUT != NETWORK SURVIVABILITY RESULT", text)
        self.assertIn("MISSING STUDY NODE != NON_LIMITING NODE", text)
        self.assertIn("NO_REAL_MANAGED_PEAK_SURVIVABILITY_STUDY", text)
        self.assertIn("readiness remains 15%", text)


if __name__ == "__main__":
    unittest.main()
