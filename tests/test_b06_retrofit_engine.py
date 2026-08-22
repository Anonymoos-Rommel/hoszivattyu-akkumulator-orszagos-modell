from modules.B06.engine import EvidenceValue, RetrofitBaseline, RetrofitIntervention, evaluate_retrofit


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


def intervention(intervention_id, annual, peak, *, family="envelope", supply=None, applicability="SCN", completion="Q"):
    return RetrofitIntervention(
        intervention_id,
        family,
        annual,
        peak,
        evidence_status="SCN",
        applicability_status=applicability,
        completion_status=completion,
        supply_temperature_after_c=supply,
        completion_source_ids=("SRC-B06-ENGINE-CONTRACT-2026",) if completion == "OBS" else (),
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


def test_completion_evidence_is_required_for_s1_gate():
    result = evaluate_retrofit(baseline(), [intervention("verified-roof", 0.2, 0.1, completion="OBS")])
    assert result.post_state_candidate == "S1_DEMAND_REDUCED"
    assert result.s1_gate == "READY"


def test_supply_temperature_missing_keeps_b05_handoff_q():
    result = evaluate_retrofit(baseline(supply=None, supply_status="Q"), [intervention("roof", 0.2, 0.1)])
    assert result.status == "SCN"
    assert result.b05_handoff.status == "Q"
    assert result.b05_handoff.space_heating_required_kw is None
