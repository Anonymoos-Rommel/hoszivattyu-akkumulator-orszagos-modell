import csv
from pathlib import Path

from modules.B06.engine import EvidenceValue, RetrofitBaseline, RetrofitIntervention, evaluate_retrofit
from modules.B06.baseline_demand_gate import (
    DER,
    DIRECT_ANNUAL,
    DIRECT_PEAK,
    BaselineDemandEvidence,
)


ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "data" / "processed" / "retrofit_effect_evidence.csv"


def rows():
    with EVIDENCE.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def der_baseline(record_id="CASE", annual=10000.0, peak=10.0, *, supply=None):
    pair = BaselineDemandEvidence(
        record_id=record_id,
        phase_id="PRE_RETROFIT",
        annual_space_heat_kwh=annual,
        annual_evidence_status=DER,
        annual_method=DIRECT_ANNUAL,
        annual_source_refs=("TEST-ANNUAL",),
        peak_heat_load_kw=peak,
        peak_evidence_status=DER,
        peak_method=DIRECT_PEAK,
        peak_source_refs=("TEST-PEAK",),
        annual_record_link=record_id,
        peak_record_link=record_id,
        annual_phase_link="PRE_RETROFIT",
        peak_phase_link="PRE_RETROFIT",
        reproducible_repository_binding=True,
    )
    return RetrofitBaseline(
        archetype_id=EvidenceValue(record_id, "DER"),
        baseline_annual_space_heat_kwh=EvidenceValue(annual, "DER"),
        baseline_peak_heat_load_kw=EvidenceValue(peak, "DER"),
        required_supply_temperature_before_c=EvidenceValue(supply, "DER" if supply is not None else "Q"),
        baseline_demand_evidence=pair,
    )


def test_annual_and_peak_effects_are_independent_fields():
    evidence = rows()
    assert any(row["annual_before_kwh_m2a"] for row in evidence)
    assert all(not row["peak_before_kw"] and not row["peak_after_kw"] for row in evidence)

    baseline = der_baseline("HVAR_CASE")
    intervention = RetrofitIntervention(
        "B06-COMBINED-PACKAGE", "package", 0.20, 0.10,
        evidence_status="DER", applicability_status="DER", completion_status="Q",
    )
    result = evaluate_retrofit(baseline, [intervention])
    assert result.post_retrofit_annual_space_heat_kwh == 8000.0
    assert result.post_retrofit_peak_heat_load_kw == 9.0
    assert result.annual_heat_reduction_pct != result.peak_heat_reduction_pct


def test_weather_normalization_and_observation_status_are_preserved():
    evidence = rows()
    measured = [row for row in evidence if row["evidence_class"] == "MEASURED_BEFORE_AFTER"]
    assert measured
    assert all(row["status"] == "Q" for row in measured)
    assert all(row["weather_normalization"] not in {"", "NOT_NORMALIZED", "NOT_DISCLOSED"} or row["status"] != "OBS" for row in evidence)


def test_dhw_contaminated_source_fails_closed():
    contaminated = [row for row in rows() if row["dhw_separation"] == "INCLUDED_NOT_SEPARABLE"]
    assert contaminated
    assert all(row["status"] == "Q" for row in contaminated)
    assert all(row["usable_for_engine"] == "NO" for row in contaminated)


def test_ranges_are_retained_without_midpoint_materialization():
    ranged = [row for row in rows() if row["annual_reduction_min"] and row["annual_reduction_max"]]
    assert ranged
    assert all(not row["annual_reduction_fraction"] for row in ranged)
    assert all(float(row["annual_reduction_min"]) < float(row["annual_reduction_max"]) for row in ranged)


def test_applicability_mismatch_keeps_real_evidence_non_usable():
    evidence = rows()
    assert all(row["applicability_status"] in {"CONTEXT_SPECIFIC", "PROGRAM_AGGREGATE"} for row in evidence)
    assert all(row["usable_for_engine"] == "NO" for row in evidence)


def test_completion_gate_remains_separate_from_effect_evidence():
    baseline = der_baseline("CASE")
    intervention = RetrofitIntervention(
        "B06-ENVELOPE-PACKAGE", "package", 0.25, 0.10,
        evidence_status="DER", applicability_status="DER", completion_status="Q",
    )
    result = evaluate_retrofit(baseline, [intervention])
    assert result.status == "DER"
    assert result.post_state_candidate == "S1_CANDIDATE"
    assert result.s1_gate == "BLOCKED"


def test_missing_supply_temperature_keeps_b05_handoff_q():
    baseline = der_baseline("CASE", supply=None)
    intervention = RetrofitIntervention(
        "B06-ENVELOPE-PACKAGE", "package", 0.25, 0.10,
        evidence_status="DER", applicability_status="SCN", completion_status="Q",
    )
    result = evaluate_retrofit(baseline, [intervention])
    assert result.b05_handoff.status == "Q"
    assert result.s1_gate == "BLOCKED"
