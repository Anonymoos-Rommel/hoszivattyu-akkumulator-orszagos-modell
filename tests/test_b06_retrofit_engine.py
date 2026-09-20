from modules.B06.engine import EvidenceValue, RetrofitBaseline, RetrofitIntervention, evaluate_retrofit
from modules.B06.s1_demand_outcome_gate import (
    CERTIFIED_CALCULATION,
    DER,
    OBS,
    S1DemandOutcomeEvidence,
)
from modules.B06.realized_completion_gate import RealizedCompletionEvidence
from modules.B06.emitter_temperature_gate import (
    EmitterTemperatureEvidence,
    SIGNED_MEP_DESIGN,
)


def ev(value, status="SCN", *sources):
    return EvidenceValue(value, status, tuple(sources))


def baseline(*, supply=55.0, supply_status="SCN", annual=10000.0, peak=10.0):
    return RetrofitBaseline(
        archetype_id=ev("SCN-FAMILY-HOUSE", "SCN"),
        baseline_annual_space_heat_kwh=ev(annual, "SCN"),
        baseline_peak_heat_load_kw=ev(peak, "SCN"),
        floor_area_m2=ev(120.0),
        heated_floor_area_m2=ev(120.0),
        building_type=ev("FAMILY_HOUSE"),
        construction_period=ev("1961-1980"),
        required_supply_temperature_before_c=ev(supply, supply_status),
        dhw_annual_kwh=ev(1800.0),
        dhw_peak_heat_load_kw=ev(2.0),
    )


def intervention(
    intervention_id,
    annual,
    peak,
    *,
    family="envelope",
    supply=None,
    applicability="SCN",
    completion="Q",
    with_linked_outcome=False,
):
    outcome = None
    realized_completion = None
    completion_sources = ()
    if completion in {OBS, DER} and with_linked_outcome:
        outcome = S1DemandOutcomeEvidence(
            record_id="TEST-REC-001",
            intervention_id=intervention_id,
            evidence_kind=CERTIFIED_CALCULATION,
            evidence_status=DER,
            phase_link_id=f"S0_TO_S1:TEST-REC-001:{intervention_id}",
            before_value=100.0,
            after_value=80.0,
            before_metric_id="ANNUAL_PRIMARY_ENERGY",
            after_metric_id="ANNUAL_PRIMARY_ENERGY",
            before_unit="kWh_m2a",
            after_unit="kWh_m2a",
            before_method_id="TEST-SAME-METHOD",
            after_method_id="TEST-SAME-METHOD",
            before_source_refs=("TEST-HET-BEFORE",),
            after_source_refs=("TEST-HET-AFTER",),
            end_use_scope_documented=True,
        )
        realized_completion = RealizedCompletionEvidence(
            record_id="TEST-REC-001",
            intervention_id=intervention_id,
            project_id="TEST-PROJECT-001",
            site_link_id="TEST-SITE-001",
            completion_evidence_status=OBS,
            physical_completion_date="2026-06-30",
            final_het_date="2026-07-05",
            contract_scope_ids=(intervention_id,),
            realized_scope_ids=(intervention_id,),
            final_invoice_refs=("TEST-FINAL-INVOICE",),
            performance_confirmation_refs=("TEST-PERFORMANCE-CONFIRMATION",),
            final_het_refs=("TEST-HET-AFTER",),
            final_energy_calculation_refs=("TEST-HET-AFTER-CALC",),
            verifier_id="TEST-TE",
            final_het_record_link="TEST-REC-001",
            final_het_site_link="TEST-SITE-001",
            physical_completion_declared=True,
            reproducible_repository_binding=True,
        )
        completion = OBS
        completion_sources = (
            "TEST-FINAL-INVOICE",
            "TEST-PERFORMANCE-CONFIRMATION",
            "TEST-HET-AFTER",
        )
    emitter_temperature_evidence = None
    if supply is not None:
        emitter_temperature_evidence = EmitterTemperatureEvidence(
            record_id="TEST-REC-001",
            intervention_id=intervention_id,
            phase_id="POST_RETROFIT_PLANNED",
            route=SIGNED_MEP_DESIGN,
            evidence_status="DER",
            source_refs=("TEST-SIGNED-MEP",),
            building_design_heat_load_kw=ev(10.0 * (1 - peak) if peak is not None else 10.0, "DER", "TEST-SIGNED-MEP"),
            explicit_supply_temperature_c=ev(supply, "DER", "TEST-SIGNED-MEP"),
            explicit_return_temperature_c=ev(supply - 5.0, "DER", "TEST-SIGNED-MEP"),
            design_outdoor_temperature_c=ev(-13.0, "DER", "TEST-SIGNED-MEP"),
            design_indoor_temperature_c=ev(20.0, "DER", "TEST-SIGNED-MEP"),
            room_heat_loss_complete=True,
            emitter_schedule_complete=True,
            hydraulic_design_documented=True,
        )
    return RetrofitIntervention(
        intervention_id,
        family,
        annual,
        peak,
        evidence_status="SCN",
        applicability_status=applicability,
        completion_status=completion,
        supply_temperature_after_c=supply,
        emitter_temperature_evidence=emitter_temperature_evidence,
        completion_source_ids=completion_sources,
        completion_outcome=outcome,
        realized_completion=realized_completion,
    )


def test_no_retrofit_does_not_promote_s1():
    result = evaluate_retrofit(baseline(), [])
    assert result.post_state_candidate == "S0_BASELINE_AUDITED"
    assert result.s1_gate == "BLOCKED"
    assert result.annual_heat_reduction_kwh == 0.0
    assert result.b05_handoff.space_heating_required_kw == 10.0


def test_single_envelope_intervention_keeps_annual_and_peak_separate():
    result = evaluate_retrofit(baseline(), [intervention("roof", 0.20, 0.10)])
    assert result.status == "SCN"
    assert result.post_retrofit_annual_space_heat_kwh == 8000.0
    assert result.post_retrofit_peak_heat_load_kw == 9.0
    assert result.annual_heat_reduction_pct == 0.20
    assert result.peak_heat_reduction_pct == 0.10
    assert result.post_state_candidate == "S1_CANDIDATE"
    assert result.s1_gate == "BLOCKED"


def test_sequential_interventions_apply_to_prior_state_not_original_baseline():
    result = evaluate_retrofit(baseline(), [intervention("roof", 0.20, 0.10), intervention("wall", 0.30, 0.20)])
    assert result.post_retrofit_annual_space_heat_kwh == 5600.0
    assert result.post_retrofit_peak_heat_load_kw == 7.2
    assert result.annual_heat_reduction_pct != 0.50
    assert result.peak_heat_reduction_pct != 0.30


def test_emitter_only_upgrade_changes_supply_not_envelope_demand():
    result = evaluate_retrofit(baseline(), [intervention("emitter", 0.0, 0.0, family="emitter", supply=35.0)])
    assert result.post_retrofit_annual_space_heat_kwh == 10000.0
    assert result.post_retrofit_peak_heat_load_kw == 10.0
    assert result.required_supply_temperature_before_c == 55.0
    assert result.required_supply_temperature_after_c == 35.0
    assert result.b05_handoff.required_supply_temperature_c == 35.0


def test_missing_baseline_or_intervention_input_fails_closed():
    missing_baseline = baseline(annual=None)
    missing_baseline = RetrofitBaseline(
        archetype_id=missing_baseline.archetype_id,
        baseline_annual_space_heat_kwh=EvidenceValue(None, "Q"),
        baseline_peak_heat_load_kw=missing_baseline.baseline_peak_heat_load_kw,
    )
    assert evaluate_retrofit(missing_baseline, []).status == "Q"
    unknown_effect = evaluate_retrofit(baseline(), [intervention("unknown", None, 0.1)])
    assert unknown_effect.status == "Q"
    assert unknown_effect.post_retrofit_annual_space_heat_kwh is None


def test_conflicting_or_missing_applicability_is_not_promoted():
    result = evaluate_retrofit(baseline(), [intervention("wall", 0.2, 0.2, applicability="Q")])
    assert result.status == "Q"
    assert result.post_state_candidate == "S0_BASELINE_AUDITED"
    assert result.remaining_readiness_gaps


def test_dhw_is_unchanged_by_envelope_intervention():
    result = evaluate_retrofit(baseline(), [intervention("roof", 0.2, 0.1)])
    assert result.dhw_annual_kwh == 1800.0
    assert result.dhw_peak_heat_load_kw == 2.0
    assert result.b05_handoff.dhw_required_kw == 2.0


def test_realized_completion_and_linked_outcome_are_both_required_for_s1_gate():
    bare = evaluate_retrofit(
        baseline(),
        [intervention("verified-roof", 0.2, 0.1, completion="OBS")],
    )
    assert bare.post_state_candidate == "S1_CANDIDATE"
    assert bare.s1_gate == "BLOCKED"
    assert any("P64 realized completion evidence is missing" in item for item in bare.remaining_readiness_gaps)

    linked = evaluate_retrofit(
        baseline(),
        [intervention("verified-roof", 0.2, 0.1, completion="OBS", with_linked_outcome=True)],
    )
    assert linked.post_state_candidate == "S1_DEMAND_REDUCED"
    assert linked.s1_gate == "READY"


def test_supply_temperature_missing_keeps_b05_handoff_q():
    result = evaluate_retrofit(baseline(supply=None, supply_status="Q"), [intervention("roof", 0.2, 0.1)])
    assert result.status == "SCN"
    assert result.b05_handoff.status == "Q"
    assert result.b05_handoff.space_heating_required_kw is None
