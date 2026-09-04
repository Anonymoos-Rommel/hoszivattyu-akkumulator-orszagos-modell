import csv
import unittest
from dataclasses import replace
from pathlib import Path

from modules.B10.baseline_infrastructure_contract import (
    ANNOUNCED_UNFUNDED,
    InfrastructureEvidence,
    InfrastructureRecord,
    PROGRAM_INCREMENTAL,
)
from modules.B10.incremental_reinforcement_contract import (
    CURRENT,
    DSO_SUBSTATION,
    INCREMENTAL_SCOPE,
    REINFORCEMENT_REQUIRED,
)
from modules.B10.limiting_node_contract import (
    LIMITING_NODE_PROVEN,
    REAL,
    THERMAL_LIMIT,
    LimitingNodeDecision,
)
from modules.B10.limiting_node_reinforcement_lineage_contract import (
    B10LimitingNodeReinforcementLineageError,
    LIMITING_NODE_REINFORCEMENT_LINK,
    Q_REAL_LIMITING_NODE_REINFORCEMENT_LINK_UNRESOLVED,
    REAL_LIMITING_NODE_REINFORCEMENT_LINK_PROVEN,
    LimitingNodeReinforcementLinkEvidence,
    LimitingNodeReinforcementLinkRecord,
    evaluate_real_limiting_node_reinforcement_lineage,
    require_real_limiting_node_reinforcement_link,
)
from modules.B10.limiting_node_study_lineage_contract import (
    Q_REAL_LIMITING_NODE_LINEAGE_UNRESOLVED,
    REAL_LIMITING_NODE_LINEAGE_PROVEN,
    LimitingNodeStudyLineageDecision,
)


ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "registry" / "limiting_node_reinforcement_lineage.csv"
DOC = ROOT / "docs" / "source_packs" / "P31_B10_LIMITING_NODE_REINFORCEMENT_LINEAGE.md"

PROJECT = "PROJECT-R1"
OPERATOR = "MVM_DEMASZ"
STUDY = "STUDY-1"
CASE = "CASE-1"
NODE = "MVM_DEMASZ:CSON:132KV"
RESULT = "SURV-RESULT-1"
LINK = "LINK-1"
PEAK = 12.5


def p26_decision():
    return LimitingNodeDecision(
        OPERATOR,
        STUDY,
        CASE,
        NODE,
        CURRENT,
        REAL,
        LIMITING_NODE_PROVEN,
        PEAK,
        THERMAL_LIMIT,
        "OBS",
        ("SRC-LIMIT",),
        "fixture",
    )


def p30(status=REAL_LIMITING_NODE_LINEAGE_PROVEN, **overrides):
    proven = status == REAL_LIMITING_NODE_LINEAGE_PROVEN
    values = dict(
        network_operator=OPERATOR,
        network_study_id=STUDY,
        study_case_id=CASE,
        horizon=CURRENT,
        node_region_id=NODE,
        truth_context=REAL,
        status=status,
        evidence_status="OBS" if proven else "Q",
        survivability_result_id=RESULT if proven else None,
        limiting_node_decision=p26_decision() if proven else None,
        source_refs=("SRC-LIMIT", "SRC-SURV"),
        reason="fixture",
    )
    values.update(overrides)
    return LimitingNodeStudyLineageDecision(**values)


def p5_record(*, reinforcement=True, project=PROJECT, operator=OPERATOR, node=NODE):
    bindings = (
        f"PROJECT_ID:{project}",
        f"NETWORK_OPERATOR:{operator}",
        f"REGION_ID:{node}",
        "REGION_GRAIN:DSO_SUBSTATION",
        f"HORIZON:{CURRENT}",
    )
    status = InfrastructureEvidence(
        "SRC-STATUS",
        2,
        "DER",
        "2026-09-04",
        "P31-1",
        ("PROJECT_ID", *bindings),
    )
    claims = (REINFORCEMENT_REQUIRED, INCREMENTAL_SCOPE) if reinforcement else (INCREMENTAL_SCOPE,)
    reinforcement_evidence = InfrastructureEvidence(
        "SRC-REINFORCEMENT",
        2,
        "DER",
        "2026-09-04",
        "P31-1",
        (*claims, *bindings),
    )
    return InfrastructureRecord(
        project_id=project,
        network_operator=operator,
        owner="DSO",
        region_id=node,
        region_grain=DSO_SUBSTATION,
        infrastructure_type="SUBSTATION_REINFORCEMENT",
        status_taxonomy=ANNOUNCED_UNFUNDED,
        status_effective_date="2026-09-04",
        source_refs=(status.source_id, reinforcement_evidence.source_id),
        evidence=(status, reinforcement_evidence),
        evidence_status="DER",
        without_program_required=False,
        with_program_required=True,
        program_causality_status="DER",
        incremental_scope_proven=True,
    )


def link_evidence(*, level=2, truth="OBS", supports=None):
    if supports is None:
        supports = (
            LIMITING_NODE_REINFORCEMENT_LINK,
            REINFORCEMENT_REQUIRED,
            f"REINFORCEMENT_LINK_ID:{LINK}",
            f"PROJECT_ID:{PROJECT}",
            f"NETWORK_OPERATOR:{OPERATOR}",
            f"NETWORK_STUDY_ID:{STUDY}",
            f"STUDY_CASE_ID:{CASE}",
            f"NODE_REGION_ID:{NODE}",
            "NODE_REGION_GRAIN:DSO_SUBSTATION",
            f"HORIZON:{CURRENT}",
            f"TRUTH_CONTEXT:{REAL}",
            f"SURVIVABILITY_RESULT_ID:{RESULT}",
        )
    return LimitingNodeReinforcementLinkEvidence(
        "SRC-LINK",
        level,
        truth,
        tuple(supports),
    )


def link_record(item=None, **overrides):
    item = item or link_evidence()
    values = dict(
        reinforcement_link_id=LINK,
        project_id=PROJECT,
        network_operator=OPERATOR,
        network_study_id=STUDY,
        study_case_id=CASE,
        node_region_id=NODE,
        horizon=CURRENT,
        survivability_result_id=RESULT,
        source_refs=(item.source_id,),
        evidence=(item,),
        truth_context=REAL,
        node_region_scheme=DSO_SUBSTATION,
    )
    values.update(overrides)
    return LimitingNodeReinforcementLinkRecord(**values)


class TestB10P31LimitingNodeReinforcementLineage(unittest.TestCase):
    def test_exact_p30_to_p5_link_proves_reinforcement_lineage(self):
        decision = evaluate_real_limiting_node_reinforcement_lineage(
            link_record(),
            limiting_node_lineage=p30(),
            reinforcement_record=p5_record(),
        )
        self.assertEqual(REAL_LIMITING_NODE_REINFORCEMENT_LINK_PROVEN, decision.status)
        self.assertTrue(decision.reinforcement_required_proven)
        self.assertEqual(PROGRAM_INCREMENTAL, decision.attribution_status)
        self.assertEqual(PROJECT, require_real_limiting_node_reinforcement_link(decision))
        self.assertFalse(hasattr(decision, "program_incremental_capex_huf"))

    def test_limiting_node_without_authoritative_link_stays_q(self):
        weak = link_evidence(supports=(LIMITING_NODE_REINFORCEMENT_LINK,))
        decision = evaluate_real_limiting_node_reinforcement_lineage(
            link_record(weak),
            limiting_node_lineage=p30(),
            reinforcement_record=p5_record(),
        )
        self.assertEqual(Q_REAL_LIMITING_NODE_REINFORCEMENT_LINK_UNRESOLVED, decision.status)
        self.assertFalse(decision.reinforcement_required_proven)

    def test_unproven_p30_lineage_stays_q(self):
        decision = evaluate_real_limiting_node_reinforcement_lineage(
            link_record(),
            limiting_node_lineage=p30(Q_REAL_LIMITING_NODE_LINEAGE_UNRESOLVED),
            reinforcement_record=p5_record(),
        )
        self.assertEqual(Q_REAL_LIMITING_NODE_REINFORCEMENT_LINK_UNRESOLVED, decision.status)

    def test_study_case_node_horizon_and_result_mismatch_stay_q(self):
        candidates = (
            link_record(network_study_id="OTHER-STUDY"),
            link_record(study_case_id="OTHER-CASE"),
            link_record(node_region_id="OTHER:NODE"),
            link_record(horizon="FIVE_YEAR"),
            link_record(survivability_result_id="OTHER-RESULT"),
        )
        for candidate in candidates:
            decision = evaluate_real_limiting_node_reinforcement_lineage(
                candidate,
                limiting_node_lineage=p30(),
                reinforcement_record=p5_record(),
            )
            self.assertEqual(Q_REAL_LIMITING_NODE_REINFORCEMENT_LINK_UNRESOLVED, decision.status)

    def test_project_identity_mismatch_stays_q(self):
        decision = evaluate_real_limiting_node_reinforcement_lineage(
            link_record(),
            limiting_node_lineage=p30(),
            reinforcement_record=p5_record(project="OTHER-PROJECT"),
        )
        self.assertEqual(Q_REAL_LIMITING_NODE_REINFORCEMENT_LINK_UNRESOLVED, decision.status)

    def test_p5_without_reinforcement_required_cannot_be_linked(self):
        decision = evaluate_real_limiting_node_reinforcement_lineage(
            link_record(),
            limiting_node_lineage=p30(),
            reinforcement_record=p5_record(reinforcement=False),
        )
        self.assertEqual(Q_REAL_LIMITING_NODE_REINFORCEMENT_LINK_UNRESOLVED, decision.status)
        self.assertFalse(decision.reinforcement_required_proven)

    def test_low_authority_link_stays_q(self):
        decision = evaluate_real_limiting_node_reinforcement_lineage(
            link_record(link_evidence(level=3)),
            limiting_node_lineage=p30(),
            reinforcement_record=p5_record(),
        )
        self.assertEqual(Q_REAL_LIMITING_NODE_REINFORCEMENT_LINK_UNRESOLVED, decision.status)

    def test_require_helper_fails_closed_on_q(self):
        decision = evaluate_real_limiting_node_reinforcement_lineage(
            link_record(link_evidence(supports=())),
            limiting_node_lineage=p30(),
            reinforcement_record=p5_record(),
        )
        with self.assertRaises(B10LimitingNodeReinforcementLineageError):
            require_real_limiting_node_reinforcement_link(decision)

    def test_registry_is_header_only(self):
        with REGISTRY.open(newline="", encoding="utf-8") as handle:
            rows = list(csv.reader(handle))
        self.assertEqual(1, len(rows))
        self.assertIn("reinforcement_link_id", rows[0])
        self.assertIn("reinforcement_required_proven", rows[0])

    def test_source_pack_preserves_boundary_and_readiness(self):
        text = DOC.read_text(encoding="utf-8")
        self.assertIn("REAL LIMITING NODE != REINFORCEMENT REQUIRED", text)
        self.assertIn("REINFORCEMENT REQUIRED != PROGRAMME-INCREMENTAL CAPEX", text)
        self.assertIn("header-only", text)
        self.assertIn("readiness remains **15%**", text)


if __name__ == "__main__":
    unittest.main()
