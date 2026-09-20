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
from modules.B06.peak_effect_gate import (
    PLANNED_DESIGN,
    PeakEffectEvidence,
)


ROOT = Path(__file__).resolve().parents[1]
EFFECTS = ROOT / "data" / "processed" / "retrofit_peak_effect_evidence.csv"
QUESTIONS = ROOT / "registry" / "open_questions.csv"
READINESS = ROOT / "registry" / "retrofit_readiness.csv"


def rows(path):
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def test_zalavar_effect_pair_is_exact_and_independent():
    record = rows(EFFECTS)[0]
    assert record["record_id"] == "B06-P62-HU-ZALAVAR-2015"
    assert record["before_phase_id"] == "PRE_RETROFIT"
    assert record["after_phase_id"] == "POST_RETROFIT_PLANNED"
    assert record["post_state_kind"] == "PLANNED_DESIGN"
    assert float(record["before_annual_net_space_heat_kwh"]) == 207172.0
    assert float(record["after_annual_net_space_heat_kwh"]) == 36687.0
    assert float(record["before_peak_heat_load_kw"]) == 132.35
    assert float(record["after_peak_heat_load_kw"]) == 46.47
    annual_fraction = (207172.0 - 36687.0) / 207172.0
    peak_fraction = (132.35 - 46.47) / 132.35
    assert abs(float(record["annual_reduction_fraction"]) - annual_fraction) < 1e-15
    assert abs(float(record["peak_reduction_fraction"]) - peak_fraction) < 1e-15
    assert annual_fraction != peak_fraction
    assert record["method_id"] == "KESZ-ZBR-EH09-3"
    assert record["evidence_status"] == "DER"
    assert record["status"] == "QUALIFIED"


def test_q_b06_011_is_resolved_but_transferability_and_completion_remain_open():
    q = {row["question_id"]: row for row in rows(QUESTIONS)}
    assert q["Q-B06-011"]["status"] == "RESOLVED"
    assert "132.35 -> 46.47 kW" in q["Q-B06-011"]["notes"]
    assert "PLANNED_DESIGN DER" in q["Q-B06-011"]["notes"]
    assert q["Q-B06-007"]["status"] == "OPEN"
    assert "one 19-dwelling case" in q["Q-B06-007"]["notes"]
    assert q["Q-B06-009"]["status"] == "OPEN"
    assert "does not prove realized completion" in q["Q-B06-009"]["notes"]


def test_peak_readiness_records_real_calibration_without_national_uplift():
    row = next(r for r in rows(READINESS) if r["component_id"] == "PEAK_LOAD_EFFECT")
    assert row["status"] == "PARTIAL"
    assert row["readiness_percent"] == "50"
    assert "SRC-B06-HU-ZALAVAR-ZBR-PRE-2015" in row["source_ids"]
    assert "SRC-B06-HU-ZALAVAR-ZBR-POST-2015" in row["source_ids"]
    assert "readiness percentage intentionally unchanged" in row["notes"]


def test_engine_accepts_exact_linked_zalavar_der_effect_but_does_not_complete_s1():
    baseline_pair = BaselineDemandEvidence(
        record_id="HU-ZALAVAR-2015",
        phase_id="PRE_RETROFIT",
        annual_space_heat_kwh=207172.0,
        annual_evidence_status=DER,
        annual_method=DIRECT_ANNUAL,
        annual_source_refs=("SRC-B06-HU-ZALAVAR-ZBR-PRE-2015",),
        peak_heat_load_kw=132.35,
        peak_evidence_status=DER,
        peak_method=DIRECT_PEAK,
        peak_source_refs=("SRC-B06-HU-ZALAVAR-ZBR-PRE-2015",),
        annual_record_link="HU-ZALAVAR-2015",
        peak_record_link="HU-ZALAVAR-2015",
        annual_phase_link="PRE_RETROFIT",
        peak_phase_link="PRE_RETROFIT",
        reproducible_repository_binding=True,
    )
    effect = PeakEffectEvidence(
        record_id="HU-ZALAVAR-2015",
        intervention_id="ZALAVAR-ENVELOPE-2015",
        evidence_status=DER,
        post_state_kind=PLANNED_DESIGN,
        before_annual_space_heat_kwh=207172.0,
        after_annual_space_heat_kwh=36687.0,
        before_peak_heat_load_kw=132.35,
        after_peak_heat_load_kw=46.47,
        before_method_id="KESZ-ZBR-EH09-3",
        after_method_id="KESZ-ZBR-EH09-3",
        before_source_refs=("SRC-B06-HU-ZALAVAR-ZBR-PRE-2015",),
        after_source_refs=("SRC-B06-HU-ZALAVAR-ZBR-POST-2015",),
        before_phase_id="PRE_RETROFIT",
        after_phase_id="POST_RETROFIT_PLANNED",
        before_design_indoor_temperature_c=20.0,
        after_design_indoor_temperature_c=20.0,
        before_design_outdoor_temperature_c=-13.0,
        after_design_outdoor_temperature_c=-13.0,
        before_heated_floor_area_m2=1419.63,
        after_heated_floor_area_m2=1419.63,
        before_heated_volume_m3=4174.5,
        after_heated_volume_m3=4174.5,
        intervention_scope_documented=True,
        dhw_separate_from_space_heat=True,
        reproducible_repository_binding=True,
    )
    annual_fraction = (207172.0 - 36687.0) / 207172.0
    peak_fraction = (132.35 - 46.47) / 132.35
    baseline = RetrofitBaseline(
        archetype_id=EvidenceValue("HU-ZALAVAR-2015", "DER"),
        baseline_annual_space_heat_kwh=EvidenceValue(207172.0, "DER"),
        baseline_peak_heat_load_kw=EvidenceValue(132.35, "DER"),
        baseline_demand_evidence=baseline_pair,
    )
    intervention = RetrofitIntervention(
        "ZALAVAR-ENVELOPE-2015",
        "envelope",
        annual_fraction,
        peak_fraction,
        evidence_status="DER",
        applicability_status="DER",
        peak_effect_evidence=effect,
    )
    result = evaluate_retrofit(baseline, [intervention])
    assert result.status == "DER"
    assert abs(result.post_retrofit_annual_space_heat_kwh - 36687.0) < 1e-9
    assert abs(result.post_retrofit_peak_heat_load_kw - 46.47) < 1e-12
    assert result.s1_gate == "BLOCKED"
    assert result.post_state_candidate == "S1_CANDIDATE"
    assert any("linked S1 demand outcome is missing" in gap for gap in result.remaining_readiness_gaps)


def test_engine_rejects_arbitrary_der_peak_fraction_even_with_valid_pair():
    baseline_pair = BaselineDemandEvidence(
        record_id="HU-ZALAVAR-2015",
        phase_id="PRE_RETROFIT",
        annual_space_heat_kwh=207172.0,
        annual_evidence_status=DER,
        annual_method=DIRECT_ANNUAL,
        annual_source_refs=("PRE",),
        peak_heat_load_kw=132.35,
        peak_evidence_status=DER,
        peak_method=DIRECT_PEAK,
        peak_source_refs=("PRE",),
        annual_record_link="HU-ZALAVAR-2015",
        peak_record_link="HU-ZALAVAR-2015",
        annual_phase_link="PRE_RETROFIT",
        peak_phase_link="PRE_RETROFIT",
        reproducible_repository_binding=True,
    )
    effect = PeakEffectEvidence(
        record_id="HU-ZALAVAR-2015",
        intervention_id="ZALAVAR-ENVELOPE-2015",
        evidence_status=DER,
        post_state_kind=PLANNED_DESIGN,
        before_annual_space_heat_kwh=207172.0,
        after_annual_space_heat_kwh=36687.0,
        before_peak_heat_load_kw=132.35,
        after_peak_heat_load_kw=46.47,
        before_method_id="M",
        after_method_id="M",
        before_source_refs=("PRE",),
        after_source_refs=("POST",),
        before_phase_id="PRE",
        after_phase_id="POST",
        before_design_indoor_temperature_c=20.0,
        after_design_indoor_temperature_c=20.0,
        before_design_outdoor_temperature_c=-13.0,
        after_design_outdoor_temperature_c=-13.0,
        intervention_scope_documented=True,
        dhw_separate_from_space_heat=True,
        reproducible_repository_binding=True,
    )
    baseline = RetrofitBaseline(
        archetype_id=EvidenceValue("HU-ZALAVAR-2015", "DER"),
        baseline_annual_space_heat_kwh=EvidenceValue(207172.0, "DER"),
        baseline_peak_heat_load_kw=EvidenceValue(132.35, "DER"),
        baseline_demand_evidence=baseline_pair,
    )
    intervention = RetrofitIntervention(
        "ZALAVAR-ENVELOPE-2015",
        "envelope",
        (207172.0 - 36687.0) / 207172.0,
        0.10,
        evidence_status="DER",
        applicability_status="DER",
        peak_effect_evidence=effect,
    )
    result = evaluate_retrofit(baseline, [intervention])
    assert result.status == "Q"
    assert any("peak reduction fraction does not match P62 evidence" in gap for gap in result.remaining_readiness_gaps)
