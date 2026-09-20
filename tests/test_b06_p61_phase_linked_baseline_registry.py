import csv
from pathlib import Path

from modules.B06.baseline_demand_gate import (
    DER,
    DIRECT_ANNUAL,
    DIRECT_PEAK,
    BaselineDemandEvidence,
)
from modules.B06.engine import (
    EvidenceValue,
    RetrofitBaseline,
    RetrofitIntervention,
    evaluate_retrofit,
)


ROOT = Path(__file__).resolve().parents[1]
BASELINES = ROOT / "data" / "processed" / "baseline_demand_evidence.csv"
QUESTIONS = ROOT / "registry" / "open_questions.csv"
READINESS = ROOT / "registry" / "retrofit_readiness.csv"


def rows(path):
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def test_zalavar_record_is_exact_same_phase_annual_peak_pair():
    record = rows(BASELINES)[0]
    assert record["record_id"] == "B06-P61-HU-ZALAVAR-2015"
    assert record["phase_id"] == "PRE_RETROFIT"
    assert record["annual_evidence_status"] == "DER"
    assert record["peak_evidence_status"] == "DER"
    assert float(record["specific_annual_net_space_heat_kwh_m2a"]) == 145.9
    assert float(record["heated_floor_area_m2"]) == 1419.63
    assert float(record["annual_net_space_heat_kwh"]) == 207172.0
    assert record["annual_method"] == "DIRECT_ANNUAL"
    assert float(record["design_peak_heat_load_kw"]) == 132.35
    assert float(record["design_indoor_temperature_c"]) == 20.0
    assert float(record["design_outdoor_temperature_c"]) == -13.0
    assert record["status"] == "QUALIFIED"


def test_q_b06_006_is_resolved_without_national_claim():
    question = next(r for r in rows(QUESTIONS) if r["question_id"] == "Q-B06-006")
    assert question["status"] == "RESOLVED"
    assert "no national annual/peak distribution" in question["notes"]
    assert "universal ratio" in question["notes"]


def test_readiness_percentage_is_not_uplifted_from_one_case():
    row = next(r for r in rows(READINESS) if r["component_id"] == "BASELINE_DEMAND_INPUT")
    assert row["readiness_percent"] == "45"
    assert "intentionally unchanged" in row["notes"]
    assert (
        "SRC-B06-HU-ZALAVAR-ZBR-PRE-2015" in row["source_ids"]
        or "SRC-B06-HU-ZALAVAR-HET-ZBR-2015" in row["source_ids"]
    )


def test_real_der_engine_baseline_without_p61_pair_fails_closed():
    baseline = RetrofitBaseline(
        archetype_id=EvidenceValue("REAL-CASE", "DER"),
        baseline_annual_space_heat_kwh=EvidenceValue(10000.0, "DER"),
        baseline_peak_heat_load_kw=EvidenceValue(10.0, "DER"),
    )
    intervention = RetrofitIntervention(
        "TEST-RETROFIT",
        "package",
        0.2,
        0.1,
        evidence_status="DER",
        applicability_status="DER",
    )
    result = evaluate_retrofit(baseline, [intervention])
    assert result.status == "Q"
    assert any("P61 same-record/same-phase" in gap for gap in result.remaining_readiness_gaps)


def test_p61_pair_does_not_authorize_unlinked_real_intervention_effect():
    pair = BaselineDemandEvidence(
        record_id="REAL-CASE",
        phase_id="PRE_RETROFIT",
        annual_space_heat_kwh=10000.0,
        annual_evidence_status=DER,
        annual_method=DIRECT_ANNUAL,
        annual_source_refs=("ANNUAL-SRC",),
        peak_heat_load_kw=10.0,
        peak_evidence_status=DER,
        peak_method=DIRECT_PEAK,
        peak_source_refs=("PEAK-SRC",),
        annual_record_link="REAL-CASE",
        peak_record_link="REAL-CASE",
        annual_phase_link="PRE_RETROFIT",
        peak_phase_link="PRE_RETROFIT",
        reproducible_repository_binding=True,
    )
    baseline = RetrofitBaseline(
        archetype_id=EvidenceValue("REAL-CASE", "DER"),
        baseline_annual_space_heat_kwh=EvidenceValue(10000.0, "DER"),
        baseline_peak_heat_load_kw=EvidenceValue(10.0, "DER"),
        baseline_demand_evidence=pair,
    )
    intervention = RetrofitIntervention(
        "TEST-RETROFIT",
        "package",
        0.2,
        0.1,
        evidence_status="DER",
        applicability_status="DER",
    )
    result = evaluate_retrofit(baseline, [intervention])
    assert result.status == "Q"
    assert any("P62 linked annual/peak effect evidence" in gap for gap in result.remaining_readiness_gaps)
