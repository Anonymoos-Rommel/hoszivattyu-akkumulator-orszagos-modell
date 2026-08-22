import csv
from pathlib import Path

from modules.B06.engine import EvidenceValue, RetrofitBaseline, RetrofitIntervention, evaluate_retrofit


ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "data" / "processed" / "retrofit_effect_evidence.csv"


def rows():
    with EVIDENCE.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def test_annual_and_peak_effects_are_independent_fields():
    evidence = rows()
    assert any(row["annual_before_kwh_m2a"] for row in evidence)
    assert all(not row["peak_before_kw"] and not row["peak_after_kw"] for row in evidence)

    baseline = RetrofitBaseline(
        archetype_id=EvidenceValue("HVAR_CASE", "DER"),
        baseline_annual_space_heat_kwh=EvidenceValue(10000.0, "DER"),
        baseline_peak_heat_load_kw=EvidenceValue(10.0, "DER"),
    )
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
    baseline = RetrofitBaseline(
        archetype_id=EvidenceValue("CASE", "DER"),
        baseline_annual_space_heat_kwh=EvidenceValue(10000.0, "DER"),
        baseline_peak_heat_load_kw=EvidenceValue(10.0, "DER"),
    )
    intervention = RetrofitIntervention(
        "B06-ENVELOPE-PACKAGE", "package", 0.25, 0.10,
        evidence_status="DER", applicability_status="DER", completion_status="Q",
    )
    result = evaluate_retrofit(baseline, [intervention])
    assert result.status == "DER"
    assert result.post_state_candidate == "S1_CANDIDATE"
    assert result.s1_gate == "BLOCKED"


def test_missing_supply_temperature_keeps_b05_handoff_q():
    baseline = RetrofitBaseline(
        archetype_id=EvidenceValue("CASE", "DER"),
        baseline_annual_space_heat_kwh=EvidenceValue(10000.0, "DER"),
        baseline_peak_heat_load_kw=EvidenceValue(10.0, "DER"),
        required_supply_temperature_before_c=EvidenceValue(None, "Q"),
    )
    intervention = RetrofitIntervention(
        "B06-ENVELOPE-PACKAGE", "package", 0.25, 0.10,
        evidence_status="DER", applicability_status="SCN", completion_status="Q",
    )
    result = evaluate_retrofit(baseline, [intervention])
    assert result.b05_handoff.status == "Q"
    assert result.s1_gate == "BLOCKED"
