import csv
import unittest
from pathlib import Path

from modules.B10.incremental_reinforcement_contract import (
    CURRENT,
    EXCEEDS_PUBLISHED_HEADROOM_SCREENING,
    HeadroomScreeningContext,
)
from modules.B10.limiting_node_contract import (
    B10LimitingNodeError,
    LIMITING_NODE,
    LIMITING_NODE_PROVEN,
    NON_LIMITING_NODE,
    NON_LIMITING_NODE_PROVEN,
    Q_LIMITING_NODE_UNRESOLVED,
    REAL,
    SCN,
    THERMAL_LIMIT,
    LimitingNodeEvidence,
    LimitingNodeRecord,
    evaluate_limiting_node,
    require_limiting_node,
)
from modules.B10.managed_flex_survivability_contract import (
    NetworkSurvivabilityDecision,
    SURVIVABILITY_PROVEN,
)
from modules.B10.topology_endpoint_contract import (
    CANONICAL_DSO_NODE_LINK_PROVEN,
    DSO_SUBSTATION,
    NAMED_LINE,
    TOPOLOGY_ENDPOINT_PROVEN,
    TopologyEndpointDecision,
)


ROOT = Path(__file__).resolve().parents[1]
ASSESSMENTS = ROOT / "registry" / "limiting_node_assessments.csv"
DOC = ROOT / "docs" / "source_packs" / "P26_B10_LIMITING_NODE_AUTHORITY_GATE.md"


NODE = "MVM_DEMASZ:CSON:132KV"
OPERATOR = "MVM_DEMASZ"
STUDY = "STUDY-1"
CASE = "CASE-1"
PEAK = 12.5


def endpoint(kind=DSO_SUBSTATION, node_link_status=CANONICAL_DSO_NODE_LINK_PROVEN, node_ref=NODE):
    return TopologyEndpointDecision(
        endpoint_id=NODE,
        endpoint_kind=kind,
        operator_context_id=OPERATOR,
        scope_id=f"{OPERATOR}:SERVICE_AREA",
        edge_refs=("EDGE-1",),
        status=TOPOLOGY_ENDPOINT_PROVEN,
        evidence_status="OBS",
        node_link_status=node_link_status,
        canonical_dso_node_ref=node_ref,
        source_refs=("SRC-ENDPOINT",),
        reason="test",
    )


def survivability(node=NODE, peak=PEAK, status=SURVIVABILITY_PROVEN):
    return NetworkSurvivabilityDecision(
        node_region_id=node,
        status=status,
        assessed_managed_peak_mw=peak if status == SURVIVABILITY_PROVEN else None,
        evidence_status="OBS" if status == SURVIVABILITY_PROVEN else "Q",
        source_refs=("SRC-SURV",),
        reason="test",
    )


def screening(status=EXCEEDS_PUBLISHED_HEADROOM_SCREENING):
    return HeadroomScreeningContext(
        network_operator=OPERATOR,
        region_id=NODE,
        region_grain="DSO_SUBSTATION",
        horizon=CURRENT,
        screening_status=status,
        evidence_status="DER" if status != "Q" else "Q",
        source_refs=("SRC-SCREEN",),
        incremental_demand_mw=10.0 if status != "Q" else None,
        published_headroom_mw=5.0 if status != "Q" else None,
        remaining_headroom_mw=0.0 if status != "Q" else None,
        overload_mw=5.0 if status != "Q" else None,
    )


def evidence(claim=LIMITING_NODE, truth_status="OBS", authority_level=2):
    return LimitingNodeEvidence(
        source_id="SRC-LIMIT",
        authority_level=authority_level,
        truth_status=truth_status,
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


def record(items, truth_context=REAL):
    return LimitingNodeRecord(
        network_operator=OPERATOR,
        network_study_id=STUDY,
        study_case_id=CASE,
        node_region_id=NODE,
        horizon=CURRENT,
        truth_context=truth_context,
        assessed_managed_peak_mw=PEAK,
        constraint_kind=THERMAL_LIMIT,
        source_refs=tuple(item.source_id for item in items),
        evidence=tuple(items),
    )


class TestB10P26LimitingNodeAuthorityGate(unittest.TestCase):
    def test_registry_is_header_only(self):
        with ASSESSMENTS.open(newline="", encoding="utf-8") as handle:
            rows = list(csv.reader(handle))
        self.assertEqual(len(rows), 1)
        self.assertIn("status", rows[0])
        self.assertIn("constraint_kind", rows[0])

    def test_exact_authority_proves_limiting_node(self):
        decision = evaluate_limiting_node(
            record((evidence(),)),
            topology_endpoint=endpoint(),
            survivability=survivability(),
            screening=screening(),
        )
        self.assertEqual(decision.status, LIMITING_NODE_PROVEN)
        self.assertEqual(decision.node_region_id, NODE)
        self.assertEqual(decision.assessed_managed_peak_mw, PEAK)
        self.assertEqual(require_limiting_node(decision), NODE)

    def test_exact_authority_can_prove_non_limiting_node(self):
        decision = evaluate_limiting_node(
            record((evidence(NON_LIMITING_NODE),)),
            topology_endpoint=endpoint(),
            survivability=survivability(),
        )
        self.assertEqual(decision.status, NON_LIMITING_NODE_PROVEN)
        with self.assertRaises(B10LimitingNodeError):
            require_limiting_node(decision)

    def test_missing_claim_specific_support_returns_q(self):
        weak = LimitingNodeEvidence(
            source_id="SRC-LIMIT",
            authority_level=2,
            truth_status="OBS",
            supports=(LIMITING_NODE,),
        )
        decision = evaluate_limiting_node(
            record((weak,)),
            topology_endpoint=endpoint(),
            survivability=survivability(),
        )
        self.assertEqual(decision.status, Q_LIMITING_NODE_UNRESOLVED)
        self.assertIsNone(decision.assessed_managed_peak_mw)
        self.assertIsNone(decision.constraint_kind)

    def test_headroom_exceedance_does_not_mint_limiting_node(self):
        weak = LimitingNodeEvidence(
            source_id="SRC-LIMIT",
            authority_level=2,
            truth_status="OBS",
            supports=(),
        )
        decision = evaluate_limiting_node(
            record((weak,)),
            topology_endpoint=endpoint(),
            survivability=survivability(),
            screening=screening(EXCEEDS_PUBLISHED_HEADROOM_SCREENING),
        )
        self.assertEqual(decision.status, Q_LIMITING_NODE_UNRESOLVED)

    def test_named_line_endpoint_cannot_be_limiting_dso_node(self):
        with self.assertRaises(B10LimitingNodeError):
            evaluate_limiting_node(
                record((evidence(),)),
                topology_endpoint=endpoint(
                    kind=NAMED_LINE,
                    node_link_status="CANONICAL_DSO_NODE_LINK_NOT_APPLICABLE",
                    node_ref=None,
                ),
                survivability=survivability(),
            )

    def test_survivability_node_and_peak_must_match(self):
        with self.assertRaises(B10LimitingNodeError):
            evaluate_limiting_node(
                record((evidence(),)),
                topology_endpoint=endpoint(),
                survivability=survivability(node="OTHER"),
            )
        with self.assertRaises(B10LimitingNodeError):
            evaluate_limiting_node(
                record((evidence(),)),
                topology_endpoint=endpoint(),
                survivability=survivability(peak=PEAK + 1),
            )

    def test_conflicting_limiting_and_non_limiting_claims_fail_closed(self):
        limiting = evidence(LIMITING_NODE)
        non_limiting = LimitingNodeEvidence(
            source_id="SRC-NONLIMIT",
            authority_level=2,
            truth_status="OBS",
            supports=tuple(
                NON_LIMITING_NODE if item == LIMITING_NODE else item
                for item in limiting.supports
            ),
        )
        candidate = LimitingNodeRecord(
            network_operator=OPERATOR,
            network_study_id=STUDY,
            study_case_id=CASE,
            node_region_id=NODE,
            horizon=CURRENT,
            truth_context=REAL,
            assessed_managed_peak_mw=PEAK,
            constraint_kind=THERMAL_LIMIT,
            source_refs=(limiting.source_id, non_limiting.source_id),
            evidence=(limiting, non_limiting),
        )
        with self.assertRaises(B10LimitingNodeError):
            evaluate_limiting_node(
                candidate,
                topology_endpoint=endpoint(),
                survivability=survivability(),
            )

    def test_real_case_rejects_scn_only_authority(self):
        scn_evidence = evidence(truth_status="SCN")
        decision = evaluate_limiting_node(
            record((scn_evidence,), truth_context=REAL),
            topology_endpoint=endpoint(),
            survivability=survivability(),
        )
        self.assertEqual(decision.status, Q_LIMITING_NODE_UNRESOLVED)

    def test_scn_case_requires_scn_binding(self):
        scn = LimitingNodeEvidence(
            source_id="SRC-LIMIT",
            authority_level=2,
            truth_status="SCN",
            supports=(
                LIMITING_NODE,
                f"NETWORK_OPERATOR:{OPERATOR}",
                f"NETWORK_STUDY_ID:{STUDY}",
                f"STUDY_CASE_ID:{CASE}",
                f"NODE_REGION_ID:{NODE}",
                "NODE_REGION_GRAIN:DSO_SUBSTATION",
                f"HORIZON:{CURRENT}",
                f"TRUTH_CONTEXT:{SCN}",
                f"ASSESSED_MANAGED_PEAK_MW:{PEAK}",
                f"CONSTRAINT_KIND:{THERMAL_LIMIT}",
            ),
        )
        decision = evaluate_limiting_node(
            record((scn,), truth_context=SCN),
            topology_endpoint=endpoint(),
            survivability=survivability(),
        )
        self.assertEqual(decision.status, LIMITING_NODE_PROVEN)
        self.assertEqual(decision.evidence_status, "SCN")

    def test_source_pack_preserves_no_readiness_inflation(self):
        text = DOC.read_text(encoding="utf-8")
        self.assertIn("PUBLISHED HEADROOM EXCEEDANCE != LIMITING NODE", text)
        self.assertIn("SURVIVABILITY_PROVEN != LIMITING_NODE_PROVEN", text)
        self.assertIn("header-only", text)
        self.assertIn("readiness remains **15%**", text)


if __name__ == "__main__":
    unittest.main()
