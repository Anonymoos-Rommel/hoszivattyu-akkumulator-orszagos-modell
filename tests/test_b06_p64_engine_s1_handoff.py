from modules.B06.engine import (
    EvidenceValue,
    RetrofitBaseline,
    RetrofitIntervention,
    evaluate_retrofit,
)
from modules.B06.realized_completion_gate import OBS, RealizedCompletionEvidence
from modules.B06.s1_demand_outcome_gate import (
    CERTIFIED_CALCULATION,
    DER,
    S1DemandOutcomeEvidence,
)


def baseline():
    return RetrofitBaseline(
        archetype_id=EvidenceValue("P64-SCN", "SCN"),
        baseline_annual_space_heat_kwh=EvidenceValue(10000.0, "SCN"),
        baseline_peak_heat_load_kw=EvidenceValue(10.0, "SCN"),
    )


def realized(record_id="REC-1", intervention_id="RETROFIT-1", **changes):
    values = dict(
        record_id=record_id,
        intervention_id=intervention_id,
        project_id="PROJECT-1",
        site_link_id="SITE-1",
        completion_evidence_status=OBS,
        physical_completion_date="2026-06-30",
        final_het_date="2026-07-05",
        contract_scope_ids=("WALL", "ROOF"),
        realized_scope_ids=("WALL", "ROOF"),
        final_invoice_refs=("FINAL-INVOICE",),
        performance_confirmation_refs=("PERFORMANCE-CONFIRMATION",),
        final_het_refs=("FINAL-HET",),
        final_energy_calculation_refs=("FINAL-HET-CALC",),
        verifier_id="TE-001",
        final_het_record_link=record_id,
        final_het_site_link="SITE-1",
        physical_completion_declared=True,
        reproducible_repository_binding=True,
    )
    values.update(changes)
    return RealizedCompletionEvidence(**values)


def outcome(record_id="REC-1", intervention_id="RETROFIT-1"):
    return S1DemandOutcomeEvidence(
        record_id=record_id,
        intervention_id=intervention_id,
        evidence_kind=CERTIFIED_CALCULATION,
        evidence_status=DER,
        phase_link_id=f"S0_TO_S1:{record_id}:{intervention_id}",
        before_value=200.0,
        after_value=120.0,
        before_metric_id="ANNUAL_PRIMARY_ENERGY",
        after_metric_id="ANNUAL_PRIMARY_ENERGY",
        before_unit="kWh_m2a",
        after_unit="kWh_m2a",
        before_method_id="HET-SAME-METHOD",
        after_method_id="HET-SAME-METHOD",
        before_source_refs=("OPENING-HET",),
        after_source_refs=("FINAL-HET",),
        end_use_scope_documented=True,
        minimum_reduction_fraction=0.30,
    )


def intervention(*, realized_completion=None, completion_outcome=None, completion_status="OBS"):
    return RetrofitIntervention(
        "RETROFIT-1",
        "envelope",
        0.20,
        0.10,
        evidence_status="SCN",
        applicability_status="SCN",
        completion_status=completion_status,
        completion_source_ids=("FINAL-INVOICE", "PERFORMANCE-CONFIRMATION", "FINAL-HET"),
        completion_outcome=completion_outcome,
        realized_completion=realized_completion,
    )


def test_outcome_without_realized_completion_cannot_open_s1():
    result = evaluate_retrofit(
        baseline(),
        [intervention(completion_outcome=outcome())],
    )
    assert result.s1_gate == "BLOCKED"
    assert result.post_state_candidate == "S1_CANDIDATE"
    assert any("P64 realized completion evidence is missing" in gap for gap in result.remaining_readiness_gaps)


def test_realized_completion_without_outcome_cannot_open_s1():
    result = evaluate_retrofit(
        baseline(),
        [intervention(realized_completion=realized())],
    )
    assert result.s1_gate == "BLOCKED"
    assert result.post_state_candidate == "S1_CANDIDATE"
    assert any("linked S1 demand outcome is missing" in gap for gap in result.remaining_readiness_gaps)


def test_completion_obs_and_outcome_der_can_jointly_open_s1():
    result = evaluate_retrofit(
        baseline(),
        [intervention(realized_completion=realized(), completion_outcome=outcome())],
    )
    assert result.s1_gate == "READY"
    assert result.post_state_candidate == "S1_DEMAND_REDUCED"
    assert result.status == "SCN"


def test_completion_status_is_bound_to_realized_obs_not_outcome_der():
    result = evaluate_retrofit(
        baseline(),
        [
            intervention(
                realized_completion=realized(),
                completion_outcome=outcome(),
                completion_status="DER",
            )
        ],
    )
    assert result.s1_gate == "BLOCKED"
    assert any(
        "completion status does not match realized completion evidence" in gap
        for gap in result.remaining_readiness_gaps
    )


def test_completion_and_outcome_must_link_same_record():
    result = evaluate_retrofit(
        baseline(),
        [
            intervention(
                realized_completion=realized(record_id="REC-1"),
                completion_outcome=outcome(record_id="REC-2"),
            )
        ],
    )
    assert result.s1_gate == "BLOCKED"
    assert any(
        "completion outcome record does not match realized completion" in gap
        for gap in result.remaining_readiness_gaps
    )


def test_unapproved_scope_deviation_blocks_s1():
    result = evaluate_retrofit(
        baseline(),
        [
            intervention(
                realized_completion=realized(realized_scope_ids=("WALL",)),
                completion_outcome=outcome(),
            )
        ],
    )
    assert result.s1_gate == "BLOCKED"
    assert any("UNAPPROVED_SCOPE_DEVIATION" in gap for gap in result.remaining_readiness_gaps)
