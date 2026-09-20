from modules.B06.design_load import EmitterOperatingPoint, EmitterRating
from modules.B06.emitter_temperature_gate import (
    MEASURED_DESIGN_POINT,
    QUALIFIED,
    Q,
    ROOM_BY_ROOM_DESIGN,
    SIGNED_MEP_DESIGN,
    EmitterTemperatureEvidence,
    RoomEmitterDesignEvidence,
    assess_emitter_temperature,
)
from modules.B06.engine import (
    EvidenceValue,
    RetrofitBaseline,
    RetrofitIntervention,
    evaluate_retrofit,
)


def ev(value, status="DER", source="TEST-P65"):
    return EvidenceValue(value, status, (source,))


def radiator(emitter_id):
    return EmitterRating(
        nominal_output_kw=ev(10.0, source="TEST-MANUFACTURER"),
        nominal_flow_temperature_c=ev(75.0, source="TEST-MANUFACTURER"),
        nominal_return_temperature_c=ev(65.0, source="TEST-MANUFACTURER"),
        room_temperature_c=ev(20.0, source="TEST-MANUFACTURER"),
        temperature_exponent=ev(1.0, source="TEST-MANUFACTURER"),
        source_ids=("TEST-MANUFACTURER",),
        quantity=ev(1.0, source="TEST-INVENTORY"),
        emitter_id=emitter_id,
        manufacturer="TEST",
        model_type="PANEL",
        dimensions_mm="600x1000",
        correction_method=ev("EXPLICIT_ARITHMETIC_MEAN", source="TEST-MANUFACTURER"),
    )


def points():
    return (
        EmitterOperatingPoint(ev(45.0), ev(35.0), ev(20.0)),
        EmitterOperatingPoint(ev(55.0), ev(45.0), ev(20.0)),
    )


def room(room_id, load):
    return RoomEmitterDesignEvidence(
        room_id=room_id,
        design_heat_load_kw=ev(load, source=f"TEST-LOAD-{room_id}"),
        design_indoor_temperature_c=ev(20.0, source=f"TEST-LOAD-{room_id}"),
        emitter=radiator(f"RAD-{room_id}"),
        operating_points=points(),
        source_refs=(f"TEST-ROOM-{room_id}",),
    )


def signed_design(intervention_id="EMITTER", supply=45.0):
    return EmitterTemperatureEvidence(
        record_id="TEST-RECORD",
        intervention_id=intervention_id,
        phase_id="POST_RETROFIT_PLANNED",
        route=SIGNED_MEP_DESIGN,
        evidence_status="DER",
        source_refs=("TEST-SIGNED-MEP",),
        building_design_heat_load_kw=ev(10.0, source="TEST-SIGNED-MEP"),
        explicit_supply_temperature_c=ev(supply, source="TEST-SIGNED-MEP"),
        explicit_return_temperature_c=ev(supply - 5.0, source="TEST-SIGNED-MEP"),
        design_outdoor_temperature_c=ev(-13.0, source="TEST-SIGNED-MEP"),
        design_indoor_temperature_c=ev(20.0, source="TEST-SIGNED-MEP"),
        room_heat_loss_complete=True,
        emitter_schedule_complete=True,
        hydraulic_design_documented=True,
        designer_or_engineer_id="TEST-ENGINEER",
        design_document_signed_or_sealed=True,
    )


def test_room_by_room_route_uses_worst_room_not_average():
    evidence = EmitterTemperatureEvidence(
        record_id="TEST-RECORD",
        intervention_id="EMITTER",
        phase_id="POST_RETROFIT_PLANNED",
        route=ROOM_BY_ROOM_DESIGN,
        evidence_status="DER",
        source_refs=("TEST-BUILDING-DESIGN",),
        heated_room_count=2,
        rooms=(room("LIVING", 3.5), room("BEDROOM", 4.5)),
    )
    result = assess_emitter_temperature(evidence)
    assert result.status == QUALIFIED
    assert result.required_supply_temperature_c == 55.0
    assert result.required_return_temperature_c == 45.0
    assert result.critical_room_id == "BEDROOM"


def test_room_by_room_route_requires_complete_heated_room_coverage():
    evidence = EmitterTemperatureEvidence(
        record_id="TEST-RECORD",
        intervention_id="EMITTER",
        phase_id="POST_RETROFIT_PLANNED",
        route=ROOM_BY_ROOM_DESIGN,
        evidence_status="DER",
        source_refs=("TEST-BUILDING-DESIGN",),
        heated_room_count=2,
        rooms=(room("LIVING", 3.5),),
    )
    result = assess_emitter_temperature(evidence)
    assert result.status == Q
    assert "coverage" in " ".join(result.gaps).lower()


def test_signed_mep_design_requires_heat_loss_emitter_and_hydraulic_basis():
    qualified = assess_emitter_temperature(signed_design())
    assert qualified.status == QUALIFIED
    assert qualified.required_supply_temperature_c == 45.0

    incomplete = signed_design()
    incomplete = EmitterTemperatureEvidence(
        **{**incomplete.__dict__, "emitter_schedule_complete": False}
    )
    result = assess_emitter_temperature(incomplete)
    assert result.status == Q
    assert "emitter schedule" in " ".join(result.gaps)


def test_signed_mep_design_requires_identified_signed_authority():
    evidence = signed_design()
    unsigned = EmitterTemperatureEvidence(
        **{
            **evidence.__dict__,
            "designer_or_engineer_id": "",
            "design_document_signed_or_sealed": False,
        }
    )
    result = assess_emitter_temperature(unsigned)
    assert result.status == Q
    joined = " ".join(result.gaps)
    assert "designer/engineer identity" in joined
    assert "signed or sealed" in joined


def test_measured_route_cannot_extrapolate_from_warmer_weather():
    evidence = EmitterTemperatureEvidence(
        record_id="TEST-RECORD",
        intervention_id="EMITTER",
        phase_id="POST_RETROFIT_REALIZED",
        route=MEASURED_DESIGN_POINT,
        evidence_status="OBS",
        source_refs=("TEST-MEASUREMENT",),
        building_design_heat_load_kw=ev(10.0, "DER", "TEST-DESIGN-LOAD"),
        explicit_supply_temperature_c=ev(45.0, "OBS", "TEST-MEASUREMENT"),
        explicit_return_temperature_c=ev(40.0, "OBS", "TEST-MEASUREMENT"),
        design_outdoor_temperature_c=ev(-13.0),
        design_indoor_temperature_c=ev(20.0),
        measured_outdoor_temperature_c=ev(-2.0, "OBS", "TEST-MEASUREMENT"),
        minimum_measured_room_temperature_c=ev(21.0, "OBS", "TEST-MEASUREMENT"),
        measurement_room_coverage_complete=True,
    )
    result = assess_emitter_temperature(evidence)
    assert result.status == Q
    assert "warmer" in " ".join(result.gaps)


def baseline():
    return RetrofitBaseline(
        archetype_id=EvidenceValue("TEST-HOUSE", "SCN"),
        baseline_annual_space_heat_kwh=EvidenceValue(10000.0, "SCN"),
        baseline_peak_heat_load_kw=EvidenceValue(10.0, "SCN"),
        required_supply_temperature_before_c=EvidenceValue(55.0, "SCN"),
        dhw_annual_kwh=EvidenceValue(1500.0, "SCN"),
        dhw_peak_heat_load_kw=EvidenceValue(2.0, "SCN"),
    )


def test_runtime_rejects_naked_supply_temperature_claim():
    intervention = RetrofitIntervention(
        "EMITTER",
        "emitter",
        0.0,
        0.0,
        evidence_status="SCN",
        applicability_status="SCN",
        supply_temperature_after_c=45.0,
    )
    result = evaluate_retrofit(baseline(), (intervention,))
    assert result.status == "Q"
    assert any("P65 emitter-temperature evidence" in gap for gap in result.remaining_readiness_gaps)


def test_runtime_accepts_only_the_temperature_minted_by_p65():
    evidence = signed_design(supply=45.0)
    intervention = RetrofitIntervention(
        "EMITTER",
        "emitter",
        0.0,
        0.0,
        evidence_status="SCN",
        applicability_status="SCN",
        supply_temperature_after_c=45.0,
        emitter_temperature_evidence=evidence,
    )
    result = evaluate_retrofit(baseline(), (intervention,))
    assert result.status == "SCN"
    assert result.required_supply_temperature_after_c == 45.0
    assert result.b05_handoff.required_supply_temperature_c == 45.0

    mismatch = RetrofitIntervention(
        "EMITTER",
        "emitter",
        0.0,
        0.0,
        evidence_status="SCN",
        applicability_status="SCN",
        supply_temperature_after_c=35.0,
        emitter_temperature_evidence=evidence,
    )
    blocked = evaluate_retrofit(baseline(), (mismatch,))
    assert blocked.status == "Q"
    assert any("does not match P65 evidence" in gap for gap in blocked.remaining_readiness_gaps)

def test_runtime_rejects_temperature_evidence_for_a_different_post_peak():
    evidence = signed_design(supply=45.0)
    evidence = EmitterTemperatureEvidence(
        **{**evidence.__dict__, "building_design_heat_load_kw": ev(8.0, source="TEST-SIGNED-MEP")}
    )
    intervention = RetrofitIntervention(
        "EMITTER",
        "emitter",
        0.0,
        0.0,
        evidence_status="SCN",
        applicability_status="SCN",
        supply_temperature_after_c=45.0,
        emitter_temperature_evidence=evidence,
    )
    result = evaluate_retrofit(baseline(), (intervention,))
    assert result.status == "Q"
    assert any("does not match current sequential peak" in gap for gap in result.remaining_readiness_gaps)

