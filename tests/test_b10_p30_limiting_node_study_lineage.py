import csv
import unittest
from pathlib import Path

from modules.B10.incremental_reinforcement_contract import CURRENT
from modules.B10.limiting_node_contract import (
    LIMITING_NODE,
    NON_LIMITING_NODE,
    REAL,
    THERMAL_LIMIT,
    LimitingNodeEvidence,
    LimitingNodeRecord,
)
from modules.B10.limiting_node_study_lineage_contract import (
    B10LimitingNodeStudyLineageError,
    Q_REAL_LIMITING_NODE_LINEAGE_UNRESOLVED,
    REAL_LIMITING_NODE_LINEAGE_PROVEN,
    REAL_NON_LIMITING_NODE_LINEAGE_PROVEN,
    evaluate_real_limiting_node_study_lineage,
    require_real_limiting_node_lineage,
)
from modules.B10.managed_flex_survivability_contract import (
    NetworkSurvivabilityDecision,
    SURVIVABILITY_PROVEN,
)
from modules.B10.survivability_study_result_contract import (
    Q_REAL_SURVIVABILITY_STUDY_RESULT_UNRESOLVED,
    REAL_SURVIVABILITY_STUDY_RESULT_PROVEN,
    SurvivabilityStudyNodeResult,
    SurvivabilityStudyResultDecision,
)
from modules.B10.topology_endpoint_contract import (
    CANONICAL_DSO_NODE_LINK_PROVEN,
    DSO_SUBSTATION,
    TOPOLOGY_ENDPOINT_PROVEN,
    TopologyEndpointDecision,
)


ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "registry" / "limiting_node_study_lineage.csv"
DOC = ROOT / "docs" / "source_packs" / "P30_B10_LIMITING_NODE_STUDY_LINEAGE.md"

NODE = "MVM_DEMASZ:CSON:132KV"
OPERATOR = "MVM_DEMASZ"
STUDY = "STUDY-1"
CASE = "CASE-1"
PEAK = 12.5
RESULT_ID = "SURV-RESULT-1"
STUDY_INPUT_ID = "STUDY-INPUT-1"


def endpoint():
    return TopologyEndpointDecision(
        endpoint_id=NODE,
        endpoint_kind=DSO_SUBSTATION,
        operator_context_id=OPERATOR,
        scope_id=f"{OPERATOR}:SERVICE_AREA",
        edge_refs=("EDGE-1",),
        status=TOPOLOGY_ENDPOINT_PROVEN,
        evidence_status="OBS",
        node_link_status=CANONICAL_DSO_NODE_LINK_PROVEN,
        canonical_dso_node_ref=NODE,
        source_refs=("SRC-ENDPOINT",),
        reason="fixture",
    )


def legacy_survivability(node=NODE, peak=PEAK):
    return NetworkSurvivabilityDecision(
        node_region_id=node,
        status=SURVIVABILITY_PROVEN,
        assessed_managed_peak_mw=peak,
        evidence_status="OBS",
        source_refs=("SRC-SURV",),
        reason="fixture",
    )


def p29(status=REAL_SURVIVABILITY_STUDY_RESULT_PROVEN, *, study=STUDY, case=CASE, horizon=CURRENT, node=NODE, peak=PEAK):
    node_results = ()
    evidence_status = "Q"
    if status == REAL_SURVIVABILITY_STUDY_RESULT_PROVEN:
        node_results = (
            SurvivabilityStudyNodeResult(
                RESULT_ID,
                node,
                peak,
                "OBS",
                legacy_survivability(node=node, peak=peak),
            ),
        )
        evidence_status = "OBS"
    return SurvivabilityStudyResultDecision(
        STUDY_INPUT_ID,
        OPERATOR,
        study,
        case,
        horizon,
        REAL,
        status,
        evidence_status,
        node_results,
        1,
        1 if node_results else 0,
        () if node_results else (NODE,),
        (),
        ("SRC-SURV",),
        "fixture",
    )


def limiting_evidence(claim=LIMITING_NODE):
    return LimitingNodeEvidence(
        source_id="SRC-LIMIT",
        authority_level=2,
        truth_status="OBS",
        supports=(
            claim,
            f"NETWORK_OPERATOR:{OPERATOR}",
            f"NETWORK_STUDY_ID:{STUDY}",
            f"STUDY_CASE_ID:{CASE}",
            f"NODE_REGION_ID:{NODE}",
            "NODE_REGION_GRAIN:DSO_SUBSTATION",
            f"HORIZON:{CURRENT}",
            f"TRUTH_CONTEXT:{REAL}",
            f"ASSESSED_MANAGED_PEAK_MW:{PEAK}",
            f"CONSTRAINT_KIND:{THERMAL_LIMIT}",
        ),
    )


def record(claim=LIMITING_NODE, *, study=STUDY, case=CASE, horizon=CURRENT, peak=PEAK):
    item = limiting_evidence(claim)
    return LimitingNodeRecord(
        network_operator=OPERATOR,
        network_study_id=study,
        study_case_id=case,
        node_region_id=NODE,
        horizon=horizon,
        truth_context=REAL,
        assessed_managed_peak_mw=peak,
        constraint_kind=THERMAL_LIMIT,
        source_refs=(item.source_id,),
        evidence=(item,),
    )


class TestB10P30LimitingNodeStudyLineage(unittest.TestCase):
    def test_exact_p29_lineage_allows_canonical_p26_limiting_node(self):
        decision = evaluate_real_limiting_node_study_lineage(
            record(),
            topology_endpoint=endpoint(),
            survivability_study_result=p29(),
        )
        self.assertEqual(REAL_LIMITING_NODE_LINEAGE_PROVEN, decision.status)
        self.assertEqual(RESULT_ID, decision.survivability_result_id)
        self.assertEqual(NODE, require_real_limiting_node_lineage(decision))

    def test_exact_p29_lineage_can_preserve_non_limiting_p26_conclusion(self):
        decision = evaluate_real_limiting_node_study_lineage(
            record(NON_LIMITING_NODE),
            topology_endpoint=endpoint(),
            survivability_study_result=p29(),
        )
        self.assertEqual(REAL_NON_LIMITING_NODE_LINEAGE_PROVEN, decision.status)
        with self.assertRaises(B10LimitingNodeStudyLineageError):
            require_real_limiting_node_lineage(decision)

    def test_raw_p10_survivability_is_not_an_input_to_p30(self):
        with self.assertRaisesRegex(B10LimitingNodeStudyLineageError, "SurvivabilityStudyResultDecision"):
            evaluate_real_limiting_node_study_lineage(
                record(),
                topology_endpoint=endpoint(),
                survivability_study_result=legacy_survivability(),
            )

    def test_unproven_p29_result_stays_q(self):
        decision = evaluate_real_limiting_node_study_lineage(
            record(),
            topology_endpoint=endpoint(),
            survivability_study_result=p29(Q_REAL_SURVIVABILITY_STUDY_RESULT_UNRESOLVED),
        )
        self.assertEqual(Q_REAL_LIMITING_NODE_LINEAGE_UNRESOLVED, decision.status)
        self.assertIsNone(decision.limiting_node_decision)

    def test_study_case_horizon_mismatch_stays_q(self):
        for candidate in (
            p29(study="OTHER-STUDY"),
            p29(case="OTHER-CASE"),
            p29(horizon="FIVE_YEAR"),
        ):
            decision = evaluate_real_limiting_node_study_lineage(
                record(),
                topology_endpoint=endpoint(),
                survivability_study_result=candidate,
            )
            self.assertEqual(Q_REAL_LIMITING_NODE_LINEAGE_UNRESOLVED, decision.status)

    def test_peak_mismatch_stays_q(self):
        decision = evaluate_real_limiting_node_study_lineage(
            record(peak=PEAK + 1),
            topology_endpoint=endpoint(),
            survivability_study_result=p29(),
        )
        self.assertEqual(Q_REAL_LIMITING_NODE_LINEAGE_UNRESOLVED, decision.status)

    def test_missing_node_in_p29_is_not_non_limiting(self):
        decision = evaluate_real_limiting_node_study_lineage(
            record(),
            topology_endpoint=endpoint(),
            survivability_study_result=p29(node="OTHER:NODE"),
        )
        self.assertEqual(Q_REAL_LIMITING_NODE_LINEAGE_UNRESOLVED, decision.status)

    def test_registry_is_header_only(self):
        with REGISTRY.open(newline="", encoding="utf-8") as handle:
            rows = list(csv.reader(handle))
        self.assertEqual(1, len(rows))
        self.assertIn("survivability_result_id", rows[0])

    def test_source_pack_preserves_boundary_and_readiness(self):
        text = DOC.read_text(encoding="utf-8")
        self.assertIn("P26 LIMITING_NODE_PROVEN != P29-LINKED REAL LIMITING NODE", text)
        self.assertIn("MISSING P29 NODE RESULT != NON_LIMITING NODE", text)
        self.assertIn("readiness remains 15%", text)


if __name__ == "__main__":
    unittest.main()
