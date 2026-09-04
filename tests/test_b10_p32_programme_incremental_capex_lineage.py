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
    COST_COMPONENT_BINDING_PREFIX,
    CURRENT,
    DSO_SUBSTATION,
    INCREMENTAL_SCOPE,
    PROGRAM_INCREMENTAL_COST,
    REINFORCEMENT_REQUIRED,
)
from modules.B10.limiting_node_contract import (
    LIMITING_NODE_PROVEN,
    REAL,
    THERMAL_LIMIT,
    LimitingNodeDecision,
)
from modules.B10.limiting_node_reinforcement_lineage_contract import (
    LIMITING_NODE_REINFORCEMENT_LINK,
    LimitingNodeReinforcementLinkEvidence,
    LimitingNodeReinforcementLinkRecord,
    evaluate_real_limiting_node_reinforcement_lineage,
)
from modules.B10.limiting_node_study_lineage_contract import (
    REAL_LIMITING_NODE_LINEAGE_PROVEN,
    LimitingNodeStudyLineageDecision,
)
from modules.B10.programme_incremental_capex_lineage_contract import (
    B10ProgrammeIncrementalCapexLineageError,
    PROGRAMME_INCREMENTAL_CAPEX_LINEAGE,
    Q_REAL_PROGRAMME_INCREMENTAL_CAPEX_LINEAGE_UNRESOLVED,
    REAL_PROGRAMME_INCREMENTAL_CAPEX_LINEAGE_PROVEN,
    ProgrammeIncrementalCapexLineageEvidence,
    ProgrammeIncrementalCapexLineageRecord,
    evaluate_real_programme_incremental_capex_lineage,
    require_real_programme_incremental_capex_lineage,
)


ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "registry" / "programme_incremental_capex_lineage.csv"
DOC = ROOT / "docs" / "source_packs" / "P32_B10_PROGRAMME_INCREMENTAL_CAPEX_LINEAGE.md"

PROJECT = "PROJECT-R1"
OPERATOR = "MVM_DEMASZ"
STUDY = "STUDY-1"
CASE = "CASE-1"
NODE = "MVM_DEMASZ:CSON:132KV"
RESULT = "SURV-RESULT-1"
LINK = "LINK-1"
CAPEX_LINEAGE = "CAPEX-LINEAGE-1"
COMPONENT = "TX-UPSIZING-1"
CAPEX = 10.0
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


def p30():
    return LimitingNodeStudyLineageDecision(
        network_operator=OPERATOR,
        network_study_id=STUDY,
        study_case_id=CASE,
        horizon=CURRENT,
        node_region_id=NODE,
        truth_context=REAL,
        status=REAL_LIMITING_NODE_LINEAGE_PROVEN,
        evidence_status="OBS",
        survivability_result_id=RESULT,
        limiting_node_decision=p26_decision(),
        source_refs=("SRC-LIMIT", "SRC-SURV"),
        reason="fixture",
    )


def p5_record(*, capex=CAPEX, component=COMPONENT):
    bindings = (
        f"PROJECT_ID:{PROJECT}",
        f"NETWORK_OPERATOR:{OPERATOR}",
        f"REGION_ID:{NODE}",
        "REGION_GRAIN:DSO_SUBSTATION",
        f"HORIZON:{CURRENT}",
    )
    status = InfrastructureEvidence(
        "SRC-STATUS",
        2,
        "DER",
        "2026-09-04",
        "P32-1",
        ("PROJECT_ID", *bindings),
    )
    reinforcement = InfrastructureEvidence(
        "SRC-REINFORCEMENT",
        2,
        "DER",
        "2026-09-04",
        "P32-1",
        (REINFORCEMENT_REQUIRED, INCREMENTAL_SCOPE, *bindings),
    )
    evidence = [status, reinforcement]
    if capex is not None:
        evidence.append(
            InfrastructureEvidence(
                "SRC-COST",
                3,
                "DER",
                "2026-09-04",
                "P32-1",
                (
                    "COST",
                    PROGRAM_INCREMENTAL_COST,
                    *bindings,
                    f"{COST_COMPONENT_BINDING_PREFIX}{component}",
                ),
            )
        )
    return InfrastructureRecord(
        project_id=PROJECT,
        network_operator=OPERATOR,
        owner="DSO",
        region_id=NODE,
        region_grain=DSO_SUBSTATION,
        infrastructure_type="SUBSTATION_REINFORCEMENT",
        status_taxonomy=ANNOUNCED_UNFUNDED,
        status_effective_date="2026-09-04",
        source_refs=tuple(item.source_id for item in evidence),
        evidence=tuple(evidence),
        evidence_status="DER",
        without_program_required=False,
        with_program_required=True,
        program_causality_status="DER",
        incremental_cost_huf=capex,
        cost_component_id=component if capex is not None else None,
        incremental_scope_proven=True,
    )


def p31_link():
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
    item = LimitingNodeReinforcementLinkEvidence("SRC-LINK", 2, "OBS", supports)
    return LimitingNodeReinforcementLinkRecord(
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
    )


def p31(record=None):
    record = record or p5_record()
    return evaluate_real_limiting_node_reinforcement_lineage(
        p31_link(),
        limiting_node_lineage=p30(),
        reinforcement_record=record,
    )


def capex_evidence(*, level=3, truth="DER", amount=CAPEX, component=COMPONENT, supports=None):
    if supports is None:
        supports = (
            PROGRAMME_INCREMENTAL_CAPEX_LINEAGE,
            f"CAPEX_LINEAGE_ID:{CAPEX_LINEAGE}",
            f"REINFORCEMENT_LINK_ID:{LINK}",
            f"PROJECT_ID:{PROJECT}",
            f"NETWORK_OPERATOR:{OPERATOR}",
            f"NETWORK_STUDY_ID:{STUDY}",
            f"STUDY_CASE_ID:{CASE}",
            f"NODE_REGION_ID:{NODE}",
            f"HORIZON:{CURRENT}",
            f"COST_COMPONENT:{component}",
            f"PROGRAMME_INCREMENTAL_CAPEX_HUF:{float(amount)}",
            f"ATTRIBUTION_STATUS:{PROGRAM_INCREMENTAL}",
        )
    return ProgrammeIncrementalCapexLineageEvidence("SRC-CAPEX-LINK", level, truth, tuple(supports))


def capex_record(item=None, **overrides):
    item = item or capex_evidence()
    values = dict(
        capex_lineage_id=CAPEX_LINEAGE,
        reinforcement_link_id=LINK,
        project_id=PROJECT,
        network_operator=OPERATOR,
        network_study_id=STUDY,
        study_case_id=CASE,
        node_region_id=NODE,
        horizon=CURRENT,
        cost_component_id=COMPONENT,
        programme_incremental_capex_huf=CAPEX,
        attribution_status=PROGRAM_INCREMENTAL,
        source_refs=(item.source_id,),
        evidence=(item,),
    )
    values.update(overrides)
    return ProgrammeIncrementalCapexLineageRecord(**values)


def evaluate(candidate=None, *, record=None, lineage=None):
    record = record or p5_record()
    lineage = lineage or p31(record)
    return evaluate_real_programme_incremental_capex_lineage(
        candidate or capex_record(),
        reinforcement_lineage=lineage,
        reinforcement_link=p31_link(),
        limiting_node_lineage=p30(),
        reinforcement_record=record,
    )


class TestB10P32ProgrammeIncrementalCapexLineage(unittest.TestCase):
    def test_exact_p31_and_p5_numeric_lineage_proves_capex(self):
        decision = evaluate()
        self.assertEqual(REAL_PROGRAMME_INCREMENTAL_CAPEX_LINEAGE_PROVEN, decision.status)
        self.assertEqual(COMPONENT, decision.cost_component_id)
        self.assertEqual(CAPEX, decision.programme_incremental_capex_huf)
        self.assertEqual((COMPONENT, CAPEX), require_real_programme_incremental_capex_lineage(decision))

    def test_missing_numeric_p5_capex_is_not_zero(self):
        record = p5_record(capex=None)
        decision = evaluate(record=record)
        self.assertEqual(Q_REAL_PROGRAMME_INCREMENTAL_CAPEX_LINEAGE_UNRESOLVED, decision.status)
        self.assertIsNone(decision.programme_incremental_capex_huf)

    def test_wrong_cost_component_stays_q(self):
        decision = evaluate(capex_record(cost_component_id="OTHER-COMPONENT"))
        self.assertEqual(Q_REAL_PROGRAMME_INCREMENTAL_CAPEX_LINEAGE_UNRESOLVED, decision.status)
        self.assertIsNone(decision.cost_component_id)

    def test_wrong_numeric_amount_stays_q(self):
        candidate = capex_record(programme_incremental_capex_huf=CAPEX + 1)
        decision = evaluate(candidate)
        self.assertEqual(Q_REAL_PROGRAMME_INCREMENTAL_CAPEX_LINEAGE_UNRESOLVED, decision.status)

    def test_missing_explicit_capex_lineage_evidence_stays_q(self):
        weak = capex_evidence(supports=(PROGRAMME_INCREMENTAL_CAPEX_LINEAGE,))
        decision = evaluate(capex_record(weak))
        self.assertEqual(Q_REAL_PROGRAMME_INCREMENTAL_CAPEX_LINEAGE_UNRESOLVED, decision.status)

    def test_low_authority_capex_lineage_evidence_stays_q(self):
        decision = evaluate(capex_record(capex_evidence(level=4)))
        self.assertEqual(Q_REAL_PROGRAMME_INCREMENTAL_CAPEX_LINEAGE_UNRESOLVED, decision.status)

    def test_forged_p31_decision_is_rejected(self):
        canonical = p31()
        forged = replace(canonical, project_id="OTHER-PROJECT")
        with self.assertRaisesRegex(B10ProgrammeIncrementalCapexLineageError, "canonical P31"):
            evaluate(lineage=forged)

    def test_p31_project_lineage_mismatch_stays_q(self):
        decision = evaluate(capex_record(network_study_id="OTHER-STUDY"))
        self.assertEqual(Q_REAL_PROGRAMME_INCREMENTAL_CAPEX_LINEAGE_UNRESOLVED, decision.status)

    def test_registry_is_header_only(self):
        with REGISTRY.open(newline="", encoding="utf-8") as handle:
            rows = list(csv.reader(handle))
        self.assertEqual(1, len(rows))
        self.assertIn("programme_incremental_capex_huf", rows[0])
        self.assertIn("cost_component_id", rows[0])

    def test_source_pack_preserves_boundaries_and_readiness(self):
        text = DOC.read_text(encoding="utf-8")
        self.assertIn("P31 REINFORCEMENT LINK != PROGRAMME-INCREMENTAL CAPEX", text)
        self.assertIn("TOTAL PROJECT COST != PROGRAMME-INCREMENTAL CAPEX", text)
        self.assertIn("header-only", text)
        self.assertIn("readiness remains **15%**", text)


if __name__ == "__main__":
    unittest.main()
