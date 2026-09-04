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
    PROGRAMME_INCREMENTAL_CAPEX_LINEAGE,
    ProgrammeIncrementalCapexLineageEvidence,
    ProgrammeIncrementalCapexLineageRecord,
    evaluate_real_programme_incremental_capex_lineage,
)
from modules.B10.project_delivery_timing_contract import (
    EXPECTED_COMPLETION,
    EX_ANTE_VERIFIED,
    OBS,
    ProjectTimingEvidence,
)
from modules.B10.timed_investment_pathway_contract import (
    COMPLETE_PROGRAMME_INCREMENTAL_CAPEX_SCHEDULE,
    PROGRAMME_INCREMENTAL_CAPEX_CASHFLOW,
    SCN_TIMED_PROGRAMME_CAPEX,
    TIMED_PROGRAMME_CAPEX_PROVEN,
    CapexCashflowEvidence,
)
from modules.B10.timed_programme_incremental_capex_lineage_contract import (
    B10TimedProgrammeIncrementalCapexLineageError,
    Q_REAL_TIMED_PROGRAMME_INCREMENTAL_CAPEX_LINEAGE_UNRESOLVED,
    REAL_TIMED_PROGRAMME_INCREMENTAL_CAPEX_LINEAGE_PROVEN,
    TIMED_PROGRAMME_INCREMENTAL_CAPEX_LINEAGE,
    TimedProgrammeIncrementalCapexLineageEvidence,
    TimedProgrammeIncrementalCapexLineageRecord,
    evaluate_real_timed_programme_incremental_capex_lineage,
    require_real_timed_programme_incremental_capex_lineage,
)


ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "registry" / "timed_programme_incremental_capex_lineage.csv"
DOC = ROOT / "docs" / "source_packs" / "P33_B10_TIMED_PROGRAMME_INCREMENTAL_CAPEX_LINEAGE.md"

PROJECT = "PROJECT-R1"
OPERATOR = "MVM_DEMASZ"
STUDY = "STUDY-1"
CASE = "CASE-1"
NODE = "MVM_DEMASZ:CSON:132KV"
RESULT = "SURV-RESULT-1"
LINK = "LINK-1"
CAPEX_LINEAGE = "CAPEX-LINEAGE-1"
TIMED_LINEAGE = "TIMED-CAPEX-LINEAGE-1"
COMPONENT = "TX-UPSIZING-1"
SCHEDULE = "CAPEX-SCHEDULE-1"
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


def p5_record():
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
        "P33-1",
        ("PROJECT_ID", *bindings),
    )
    reinforcement = InfrastructureEvidence(
        "SRC-REINFORCEMENT",
        2,
        "DER",
        "2026-09-04",
        "P33-1",
        (REINFORCEMENT_REQUIRED, INCREMENTAL_SCOPE, *bindings),
    )
    cost = InfrastructureEvidence(
        "SRC-COST",
        3,
        "DER",
        "2026-09-04",
        "P33-1",
        (
            "COST",
            PROGRAM_INCREMENTAL_COST,
            *bindings,
            f"{COST_COMPONENT_BINDING_PREFIX}{COMPONENT}",
        ),
    )
    evidence = (status, reinforcement, cost)
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
        evidence=evidence,
        evidence_status="DER",
        without_program_required=False,
        with_program_required=True,
        program_causality_status="DER",
        incremental_cost_huf=CAPEX,
        cost_component_id=COMPONENT,
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


def p32_evidence(amount=CAPEX):
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
        f"COST_COMPONENT:{COMPONENT}",
        f"PROGRAMME_INCREMENTAL_CAPEX_HUF:{float(amount)}",
        f"ATTRIBUTION_STATUS:{PROGRAM_INCREMENTAL}",
    )
    return ProgrammeIncrementalCapexLineageEvidence("SRC-CAPEX-LINK", 3, "DER", supports)


def p32_record(*, amount=CAPEX):
    item = p32_evidence(amount)
    return ProgrammeIncrementalCapexLineageRecord(
        capex_lineage_id=CAPEX_LINEAGE,
        reinforcement_link_id=LINK,
        project_id=PROJECT,
        network_operator=OPERATOR,
        network_study_id=STUDY,
        study_case_id=CASE,
        node_region_id=NODE,
        horizon=CURRENT,
        cost_component_id=COMPONENT,
        programme_incremental_capex_huf=amount,
        attribution_status=PROGRAM_INCREMENTAL,
        source_refs=(item.source_id,),
        evidence=(item,),
    )


def p32(record=None, candidate=None):
    record = record or p5_record()
    lineage = p31(record)
    return evaluate_real_programme_incremental_capex_lineage(
        candidate or p32_record(),
        reinforcement_lineage=lineage,
        reinforcement_link=p31_link(),
        limiting_node_lineage=p30(),
        reinforcement_record=record,
    )


def target():
    return ProjectTimingEvidence(
        project_id=PROJECT,
        network_operator=OPERATOR,
        claim_type=EXPECTED_COMPLETION,
        claimed_date="2028-12-31",
        source_id="SRC-TARGET",
        source_publication_date="2026-09-04",
        evidence_status=OBS,
        snapshot_status=EX_ANTE_VERIFIED,
    )


def cashflow(source_id, start, end, amount, *, truth="DER", level=3, complete=False, schedule=SCHEDULE):
    supports = [
        PROGRAMME_INCREMENTAL_CAPEX_CASHFLOW,
        f"PROJECT_ID:{PROJECT}",
        f"NETWORK_OPERATOR:{OPERATOR}",
        f"REGION_ID:{NODE}",
        "REGION_GRAIN:DSO_SUBSTATION",
        f"COST_COMPONENT:{COMPONENT}",
        f"SCHEDULE_ID:{schedule}",
        f"PERIOD_START:{start}",
        f"PERIOD_END:{end}",
    ]
    if complete:
        supports.append(COMPLETE_PROGRAMME_INCREMENTAL_CAPEX_SCHEDULE)
    return CapexCashflowEvidence(
        source_id=source_id,
        authority_level=level,
        truth_status=truth,
        project_id=PROJECT,
        network_operator=OPERATOR,
        region_id=NODE,
        region_grain=DSO_SUBSTATION,
        cost_component_id=COMPONENT,
        schedule_id=schedule,
        period_start=start,
        period_end=end,
        amount_huf=amount,
        supports=tuple(supports),
    )


def real_cashflows(schedule=SCHEDULE):
    return (
        cashflow("CF-1", "2027-01-01", "2027-06-30", 4.0, complete=True, schedule=schedule),
        cashflow("CF-2", "2027-07-01", "2027-12-31", 6.0, schedule=schedule),
    )


def timed_link_evidence(*, level=3, truth="DER", schedule=SCHEDULE, amount=CAPEX, supports=None):
    if supports is None:
        supports = (
            TIMED_PROGRAMME_INCREMENTAL_CAPEX_LINEAGE,
            f"TIMED_CAPEX_LINEAGE_ID:{TIMED_LINEAGE}",
            f"CAPEX_LINEAGE_ID:{CAPEX_LINEAGE}",
            f"REINFORCEMENT_LINK_ID:{LINK}",
            f"PROJECT_ID:{PROJECT}",
            f"NETWORK_OPERATOR:{OPERATOR}",
            f"NETWORK_STUDY_ID:{STUDY}",
            f"STUDY_CASE_ID:{CASE}",
            f"NODE_REGION_ID:{NODE}",
            f"HORIZON:{CURRENT}",
            f"COST_COMPONENT:{COMPONENT}",
            f"SCHEDULE_ID:{schedule}",
            f"PROGRAMME_INCREMENTAL_CAPEX_HUF:{float(amount)}",
            f"TIMED_PATHWAY_STATUS:{TIMED_PROGRAMME_CAPEX_PROVEN}",
        )
    return TimedProgrammeIncrementalCapexLineageEvidence(
        "SRC-TIMED-LINK",
        level,
        truth,
        tuple(supports),
    )


def timed_record(item=None, **overrides):
    item = item or timed_link_evidence()
    values = dict(
        timed_capex_lineage_id=TIMED_LINEAGE,
        capex_lineage_id=CAPEX_LINEAGE,
        reinforcement_link_id=LINK,
        project_id=PROJECT,
        network_operator=OPERATOR,
        network_study_id=STUDY,
        study_case_id=CASE,
        node_region_id=NODE,
        horizon=CURRENT,
        cost_component_id=COMPONENT,
        schedule_id=SCHEDULE,
        programme_incremental_capex_huf=CAPEX,
        source_refs=(item.source_id,),
        evidence=(item,),
    )
    values.update(overrides)
    return TimedProgrammeIncrementalCapexLineageRecord(**values)


def evaluate(candidate=None, *, capex_decision=None, capex_record=None, flows=None):
    record = p5_record()
    lineage = p31(record)
    capex_record = capex_record or p32_record()
    capex_decision = capex_decision or evaluate_real_programme_incremental_capex_lineage(
        capex_record,
        reinforcement_lineage=lineage,
        reinforcement_link=p31_link(),
        limiting_node_lineage=p30(),
        reinforcement_record=record,
    )
    return evaluate_real_timed_programme_incremental_capex_lineage(
        candidate or timed_record(),
        capex_lineage=capex_decision,
        capex_lineage_record=capex_record,
        reinforcement_lineage=lineage,
        reinforcement_link=p31_link(),
        limiting_node_lineage=p30(),
        reinforcement_record=record,
        target_timing=target(),
        cashflow_evidence=real_cashflows() if flows is None else flows,
    )


class TestB10P33TimedProgrammeIncrementalCapexLineage(unittest.TestCase):
    def test_exact_p32_to_p11_schedule_lineage_is_proven(self):
        decision = evaluate()
        self.assertEqual(REAL_TIMED_PROGRAMME_INCREMENTAL_CAPEX_LINEAGE_PROVEN, decision.status)
        self.assertEqual(COMPONENT, decision.cost_component_id)
        self.assertEqual(SCHEDULE, decision.schedule_id)
        self.assertEqual(CAPEX, decision.programme_incremental_capex_huf)
        self.assertEqual(2, len(decision.cashflow_rows))
        self.assertEqual(
            (COMPONENT, SCHEDULE, CAPEX),
            require_real_timed_programme_incremental_capex_lineage(decision),
        )

    def test_delivery_target_without_cashflow_schedule_stays_q(self):
        decision = evaluate(flows=())
        self.assertEqual(Q_REAL_TIMED_PROGRAMME_INCREMENTAL_CAPEX_LINEAGE_UNRESOLVED, decision.status)
        self.assertEqual((), decision.cashflow_rows)
        self.assertIsNone(decision.schedule_id)

    def test_scenario_p11_schedule_cannot_be_promoted_to_real(self):
        flows = (
            cashflow("CF-SCN", "2027-01-01", "2027-12-31", CAPEX, truth="SCN", level=5, complete=True),
        )
        decision = evaluate(flows=flows)
        self.assertEqual(Q_REAL_TIMED_PROGRAMME_INCREMENTAL_CAPEX_LINEAGE_UNRESOLVED, decision.status)
        self.assertIn("REAL complete", decision.reason)
        self.assertNotEqual(SCN_TIMED_PROGRAMME_CAPEX, decision.status)

    def test_schedule_id_mismatch_stays_q(self):
        decision = evaluate(timed_record(schedule_id="OTHER-SCHEDULE"))
        self.assertEqual(Q_REAL_TIMED_PROGRAMME_INCREMENTAL_CAPEX_LINEAGE_UNRESOLVED, decision.status)

    def test_wrong_p32_amount_stays_q(self):
        decision = evaluate(timed_record(programme_incremental_capex_huf=CAPEX + 1))
        self.assertEqual(Q_REAL_TIMED_PROGRAMME_INCREMENTAL_CAPEX_LINEAGE_UNRESOLVED, decision.status)
        self.assertIsNone(decision.programme_incremental_capex_huf)

    def test_missing_explicit_p32_to_p11_link_evidence_stays_q(self):
        weak = timed_link_evidence(supports=(TIMED_PROGRAMME_INCREMENTAL_CAPEX_LINEAGE,))
        decision = evaluate(timed_record(weak))
        self.assertEqual(Q_REAL_TIMED_PROGRAMME_INCREMENTAL_CAPEX_LINEAGE_UNRESOLVED, decision.status)

    def test_low_authority_timed_lineage_evidence_stays_q(self):
        item = timed_link_evidence(level=4)
        decision = evaluate(timed_record(item))
        self.assertEqual(Q_REAL_TIMED_PROGRAMME_INCREMENTAL_CAPEX_LINEAGE_UNRESOLVED, decision.status)

    def test_forged_p32_decision_is_rejected(self):
        canonical = p32()
        forged = replace(canonical, project_id="OTHER-PROJECT")
        with self.assertRaisesRegex(B10TimedProgrammeIncrementalCapexLineageError, "canonical P32"):
            evaluate(capex_decision=forged)

    def test_canonical_q_p32_cannot_become_timed_capex(self):
        bad_record = p32_record(amount=CAPEX + 1)
        canonical_q = p32(candidate=bad_record)
        decision = evaluate(capex_decision=canonical_q, capex_record=bad_record)
        self.assertEqual(Q_REAL_TIMED_PROGRAMME_INCREMENTAL_CAPEX_LINEAGE_UNRESOLVED, decision.status)
        self.assertEqual((), decision.cashflow_rows)

    def test_registry_is_header_only(self):
        with REGISTRY.open(newline="", encoding="utf-8") as handle:
            rows = list(csv.reader(handle))
        self.assertEqual(1, len(rows))
        self.assertIn("capex_lineage_id", rows[0])
        self.assertIn("schedule_id", rows[0])
        self.assertIn("cashflow_row_count", rows[0])

    def test_source_pack_preserves_boundaries_and_readiness(self):
        text = DOC.read_text(encoding="utf-8")
        self.assertIn("P32 PROGRAMME-INCREMENTAL CAPEX LINEAGE != TIMED CAPEX SCHEDULE", text)
        self.assertIn("DELIVERY DATE != CAPEX CASH-FLOW TIMING", text)
        self.assertIn("header-only", text)
        self.assertIn("readiness remains **15%**", text)


if __name__ == "__main__":
    unittest.main()
