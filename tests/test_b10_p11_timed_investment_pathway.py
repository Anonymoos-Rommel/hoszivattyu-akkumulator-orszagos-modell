from __future__ import annotations

import unittest
from dataclasses import fields, replace

from modules.B10.baseline_infrastructure_contract import (
    ANNOUNCED_UNFUNDED,
    InfrastructureEvidence,
    InfrastructureRecord,
)
from modules.B10.incremental_reinforcement_contract import (
    COST_COMPONENT_BINDING_PREFIX,
    CURRENT,
    DSO_SUBSTATION,
    HORIZON_BINDING_PREFIX,
    INCREMENTAL_SCOPE,
    NETWORK_OPERATOR_BINDING_PREFIX,
    PROGRAM_INCREMENTAL_COST,
    PROJECT_BINDING_PREFIX,
    REGION_BINDING_PREFIX,
    REGION_GRAIN_BINDING,
    REINFORCEMENT_REQUIRED,
    evaluate_programme_incremental_reinforcement,
)
from modules.B10.project_delivery_timing_contract import (
    ACTUAL_COMPLETION,
    CURRENT_PAGE_ONLY,
    EX_ANTE_VERIFIED,
    EXPECTED_COMPLETION,
    FULFILMENT_PROBABILITY_UNAVAILABLE,
    NOT_APPLICABLE,
    OBS,
    ProjectTimingEvidence,
)
from modules.B10.timed_investment_pathway_contract import (
    B10TimedInvestmentPathwayError,
    COMPLETE_PROGRAMME_INCREMENTAL_CAPEX_SCHEDULE,
    CapexCashflowEvidence,
    DELIVERY_ACTUAL_OBSERVED,
    DELIVERY_CURRENT_TARGET_ONLY,
    DELIVERY_EX_ANTE_TARGET,
    PROGRAMME_INCREMENTAL_CAPEX_CASHFLOW,
    Q_CAPEX_TIMING_UNRESOLVED,
    Q_PROGRAMME_ATTRIBUTION_UNRESOLVED,
    Q_PROGRAMME_CAPEX_UNRESOLVED,
    SCN_TIMED_PROGRAMME_CAPEX,
    TIMED_PROGRAMME_CAPEX_PROVEN,
    build_timed_investment_pathway,
)


PROJECT_ID = "P11-PROJECT"
REGION_ID = "MVM_DEMASZ:ABCD:132KV"
OPERATOR = "DEMASZ"
COMPONENT = "P11-COMPONENT"
STATUS_SOURCE = "SRC-P11-STATUS"
REINFORCEMENT_SOURCE = "SRC-P11-REINFORCEMENT"
COST_SOURCE = "SRC-P11-COST"
SCHEDULE_ID = "P11-SCHEDULE-1"


def bindings(project_id=PROJECT_ID, region_id=REGION_ID, operator=OPERATOR, horizon=CURRENT):
    return (
        f"{PROJECT_BINDING_PREFIX}{project_id}",
        f"{NETWORK_OPERATOR_BINDING_PREFIX}{operator}",
        f"{REGION_BINDING_PREFIX}{region_id}",
        REGION_GRAIN_BINDING,
        f"{HORIZON_BINDING_PREFIX}{horizon}",
    )


def infrastructure_evidence(source_id, *, level=2, truth="DER", supports=()):
    return InfrastructureEvidence(
        source_id=source_id,
        authority_level=level,
        truth_status=truth,
        effective_date="2026-09-02",
        revision="P11-2026-09-02",
        supports=tuple(supports),
    )


def programme_record(*, capex=100.0, program_causality_status="DER") -> InfrastructureRecord:
    bind = bindings()
    status = infrastructure_evidence(STATUS_SOURCE, supports=("PROJECT_ID", *bind))
    reinforcement = infrastructure_evidence(
        REINFORCEMENT_SOURCE,
        supports=(REINFORCEMENT_REQUIRED, INCREMENTAL_SCOPE, *bind),
    )
    evidence = [status, reinforcement]
    if capex is not None:
        evidence.append(
            infrastructure_evidence(
                COST_SOURCE,
                level=3,
                supports=(
                    "COST",
                    PROGRAM_INCREMENTAL_COST,
                    *bind,
                    f"{COST_COMPONENT_BINDING_PREFIX}{COMPONENT}",
                ),
            )
        )
    return InfrastructureRecord(
        project_id=PROJECT_ID,
        network_operator=OPERATOR,
        owner="DSO",
        region_id=REGION_ID,
        region_grain=DSO_SUBSTATION,
        infrastructure_type="SUBSTATION_REINFORCEMENT",
        status_taxonomy=ANNOUNCED_UNFUNDED,
        status_effective_date="2026-09-02",
        source_refs=tuple(item.source_id for item in evidence),
        evidence=tuple(evidence),
        evidence_status="DER",
        without_program_required=False,
        with_program_required=True,
        program_causality_status=program_causality_status,
        incremental_cost_huf=capex,
        cost_component_id=COMPONENT if capex is not None else None,
        incremental_scope_proven=True,
    )


def target(*, project_id=PROJECT_ID, operator=OPERATOR, snapshot=EX_ANTE_VERIFIED):
    return ProjectTimingEvidence(
        project_id=project_id,
        network_operator=operator,
        claim_type=EXPECTED_COMPLETION,
        claimed_date="2028-12-31",
        source_id="SRC-P11-TARGET",
        source_publication_date="2026-09-02",
        evidence_status=OBS,
        snapshot_status=snapshot,
    )


def actual(*, project_id=PROJECT_ID, operator=OPERATOR):
    return ProjectTimingEvidence(
        project_id=project_id,
        network_operator=operator,
        claim_type=ACTUAL_COMPLETION,
        claimed_date="2029-02-15",
        source_id="SRC-P11-ACTUAL",
        source_publication_date="2029-02-16",
        evidence_status=OBS,
        snapshot_status=NOT_APPLICABLE,
    )


def cashflow(
    source_id: str,
    start: str,
    end: str,
    amount: float,
    *,
    truth="DER",
    level=3,
    complete=False,
    project_id=PROJECT_ID,
    operator=OPERATOR,
    region_id=REGION_ID,
    component=COMPONENT,
    schedule_id=SCHEDULE_ID,
    include_cashflow_claim=True,
):
    supports = [
        f"PROJECT_ID:{project_id}",
        f"NETWORK_OPERATOR:{operator}",
        f"REGION_ID:{region_id}",
        "REGION_GRAIN:DSO_SUBSTATION",
        f"COST_COMPONENT:{component}",
        f"SCHEDULE_ID:{schedule_id}",
        f"PERIOD_START:{start}",
        f"PERIOD_END:{end}",
    ]
    if include_cashflow_claim:
        supports.append(PROGRAMME_INCREMENTAL_CAPEX_CASHFLOW)
    if complete:
        supports.append(COMPLETE_PROGRAMME_INCREMENTAL_CAPEX_SCHEDULE)
    return CapexCashflowEvidence(
        source_id=source_id,
        authority_level=level,
        truth_status=truth,
        project_id=project_id,
        network_operator=operator,
        region_id=region_id,
        region_grain=DSO_SUBSTATION,
        cost_component_id=component,
        schedule_id=schedule_id,
        period_start=start,
        period_end=end,
        amount_huf=amount,
        supports=tuple(supports),
    )


def proven_inputs(*, capex=100.0, causality="DER"):
    record = programme_record(capex=capex, program_causality_status=causality)
    reinforcement = evaluate_programme_incremental_reinforcement(record, reinforcement_horizon=CURRENT)
    return record, reinforcement


class B10P11TimedInvestmentPathwayTests(unittest.TestCase):
    def test_delivery_target_does_not_allocate_capex_to_completion_year(self):
        record, reinforcement = proven_inputs()
        result = build_timed_investment_pathway(record, reinforcement, target())
        self.assertEqual(result.status, Q_CAPEX_TIMING_UNRESOLVED)
        self.assertEqual(result.delivery_status, DELIVERY_EX_ANTE_TARGET)
        self.assertEqual(result.target_date, "2028-12-31")
        self.assertEqual(result.untimed_programme_incremental_capex_huf, 100.0)
        self.assertEqual(result.cashflow_rows, ())

    def test_actual_completion_still_does_not_allocate_capex(self):
        record, reinforcement = proven_inputs()
        result = build_timed_investment_pathway(record, reinforcement, target(), actual())
        self.assertEqual(result.status, Q_CAPEX_TIMING_UNRESOLVED)
        self.assertEqual(result.delivery_status, DELIVERY_ACTUAL_OBSERVED)
        self.assertEqual(result.actual_completion_date, "2029-02-15")
        self.assertEqual(result.cashflow_rows, ())

    def test_current_page_target_remains_current_target_only(self):
        record, reinforcement = proven_inputs()
        result = build_timed_investment_pathway(
            record,
            reinforcement,
            target(snapshot=CURRENT_PAGE_ONLY),
        )
        self.assertEqual(result.delivery_status, DELIVERY_CURRENT_TARGET_ONLY)
        self.assertEqual(result.status, Q_CAPEX_TIMING_UNRESOLVED)

    def test_unquantified_programme_capex_remains_q(self):
        record, reinforcement = proven_inputs(capex=None)
        result = build_timed_investment_pathway(record, reinforcement, target())
        self.assertEqual(result.status, Q_PROGRAMME_CAPEX_UNRESOLVED)
        self.assertIsNone(result.untimed_programme_incremental_capex_huf)
        self.assertEqual(result.cashflow_rows, ())

    def test_unresolved_programme_attribution_blocks_pathway(self):
        record, reinforcement = proven_inputs(capex=None, causality="Q")
        result = build_timed_investment_pathway(record, reinforcement, target())
        self.assertEqual(result.status, Q_PROGRAMME_ATTRIBUTION_UNRESOLVED)
        self.assertEqual(result.cashflow_rows, ())

    def test_exact_complete_cashflow_schedule_can_time_programme_capex(self):
        record, reinforcement = proven_inputs()
        rows = (
            cashflow("CF-1", "2027-01-01", "2027-06-30", 40.0, complete=True),
            cashflow("CF-2", "2027-07-01", "2027-12-31", 60.0),
        )
        result = build_timed_investment_pathway(record, reinforcement, target(), cashflow_evidence=rows)
        self.assertEqual(result.status, TIMED_PROGRAMME_CAPEX_PROVEN)
        self.assertEqual(sum(row.programme_incremental_capex_huf for row in result.cashflow_rows), 100.0)
        self.assertEqual(result.cashflow_rows[0].period_start, "2027-01-01")
        self.assertEqual(result.cashflow_rows[1].period_end, "2027-12-31")

    def test_cashflow_total_must_reconcile_to_p5_incremental_capex(self):
        record, reinforcement = proven_inputs()
        rows = (
            cashflow("CF-1", "2027-01-01", "2027-06-30", 40.0, complete=True),
            cashflow("CF-2", "2027-07-01", "2027-12-31", 50.0),
        )
        result = build_timed_investment_pathway(record, reinforcement, target(), cashflow_evidence=rows)
        self.assertEqual(result.status, Q_CAPEX_TIMING_UNRESOLVED)
        self.assertEqual(result.cashflow_rows, ())

    def test_generic_cost_timing_without_cashflow_claim_is_q(self):
        record, reinforcement = proven_inputs()
        rows = (
            cashflow(
                "CF-1", "2027-01-01", "2027-12-31", 100.0,
                complete=True,
                include_cashflow_claim=False,
            ),
        )
        result = build_timed_investment_pathway(record, reinforcement, target(), cashflow_evidence=rows)
        self.assertEqual(result.status, Q_CAPEX_TIMING_UNRESOLVED)

    def test_schedule_completeness_must_be_explicit(self):
        record, reinforcement = proven_inputs()
        rows = (cashflow("CF-1", "2027-01-01", "2027-12-31", 100.0),)
        result = build_timed_investment_pathway(record, reinforcement, target(), cashflow_evidence=rows)
        self.assertEqual(result.status, Q_CAPEX_TIMING_UNRESOLVED)

    def test_scn_phasing_remains_scn(self):
        record, reinforcement = proven_inputs()
        rows = (
            cashflow("CF-1", "2027-01-01", "2027-06-30", 25.0, truth="SCN", level=5, complete=True),
            cashflow("CF-2", "2027-07-01", "2027-12-31", 75.0, truth="SCN", level=5),
        )
        result = build_timed_investment_pathway(record, reinforcement, target(), cashflow_evidence=rows)
        self.assertEqual(result.status, SCN_TIMED_PROGRAMME_CAPEX)
        self.assertTrue(all(row.evidence_status == "SCN" for row in result.cashflow_rows))

    def test_real_low_authority_cashflow_cannot_be_promoted(self):
        record, reinforcement = proven_inputs()
        rows = (
            cashflow("CF-1", "2027-01-01", "2027-12-31", 100.0, level=4, complete=True),
        )
        result = build_timed_investment_pathway(record, reinforcement, target(), cashflow_evidence=rows)
        self.assertEqual(result.status, Q_CAPEX_TIMING_UNRESOLVED)

    def test_overlapping_period_totals_fail_closed(self):
        record, reinforcement = proven_inputs()
        rows = (
            cashflow("CF-1", "2027-01-01", "2027-09-30", 60.0, complete=True),
            cashflow("CF-2", "2027-07-01", "2027-12-31", 40.0),
        )
        result = build_timed_investment_pathway(record, reinforcement, target(), cashflow_evidence=rows)
        self.assertEqual(result.status, Q_CAPEX_TIMING_UNRESOLVED)
        self.assertEqual(result.cashflow_rows, ())

    def test_p5_p6_project_and_operator_identity_must_match(self):
        record, reinforcement = proven_inputs()
        with self.assertRaisesRegex(B10TimedInvestmentPathwayError, "project_id"):
            build_timed_investment_pathway(record, reinforcement, target(project_id="OTHER"))
        with self.assertRaisesRegex(B10TimedInvestmentPathwayError, "network_operator"):
            build_timed_investment_pathway(record, reinforcement, target(operator="OTHER"))

    def test_cashflow_component_identity_must_match_p5(self):
        record, reinforcement = proven_inputs()
        bad = (
            cashflow(
                "CF-1", "2027-01-01", "2027-12-31", 100.0,
                complete=True,
                component="OTHER-COMPONENT",
            ),
        )
        with self.assertRaisesRegex(B10TimedInvestmentPathwayError, "component identity"):
            build_timed_investment_pathway(record, reinforcement, target(), cashflow_evidence=bad)

    def test_p11_does_not_mint_probability_network_or_total_project_cost(self):
        record, reinforcement = proven_inputs()
        rows = (cashflow("CF-1", "2027-01-01", "2027-12-31", 100.0, complete=True),)
        result = build_timed_investment_pathway(record, reinforcement, target(), cashflow_evidence=rows)
        names = {field.name for field in fields(type(result))}
        self.assertIsNone(result.completion_probability)
        self.assertEqual(result.completion_probability_status, FULFILMENT_PROBABILITY_UNAVAILABLE)
        self.assertNotIn("hosting_capacity_mw", names)
        self.assertNotIn("network_survivability", names)
        self.assertNotIn("total_project_cost_huf", names)
        self.assertNotIn("network_layer", names)

    def test_handcrafted_p5_decision_cannot_bypass_reproduction_gate(self):
        record, reinforcement = proven_inputs()
        forged = replace(reinforcement, program_incremental_capex_huf=999.0)
        with self.assertRaisesRegex(B10TimedInvestmentPathwayError, "canonical P5"):
            build_timed_investment_pathway(record, forged, target())


if __name__ == "__main__":
    unittest.main()
