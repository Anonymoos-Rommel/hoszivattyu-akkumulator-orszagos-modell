import csv
from pathlib import Path

from modules.B06.design_load import (
    DesignLoadInputs,
    EmitterOperatingPoint,
    EmitterRating,
    EnvelopeComponent,
    VentilationInput,
    b05_design_point_coverage,
    calculate_before_after_design_load,
    calculate_design_heat_load,
    derive_required_supply_temperature,
)
from modules.B06.engine import EvidenceValue


ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "data" / "processed" / "retrofit_peak_design_evidence.csv"


def ev(value, status="SCN"):
    return EvidenceValue(value, status)


def case(*, wall_u=0.8, design_outdoor=-10.0, area=100.0):
    components = (
        EnvelopeComponent("wall", ev(wall_u), ev(area), "external", ev(1.0)),
        EnvelopeComponent("roof", ev(0.2), ev(80.0), "external", ev(1.0)),
        EnvelopeComponent("floor", ev(0.4), ev(80.0), "ground", ev(1.0)),
        EnvelopeComponent("window", ev(1.4), ev(20.0), "external", ev(1.0)),
    )
    ventilation = VentilationInput(
        volume_m3=ev(300.0),
        air_change_rate_h=ev(0.5),
        heat_recovery_efficiency=ev(0.0),
        air_volumetric_heat_capacity_wh_m3k=ev(0.33),
    )
    return DesignLoadInputs(
        "CASE-1", ev("SCN-HU"), ev(design_outdoor), ev(20.0), components, ev(0.0), ventilation,
    )


def test_known_transmission_and_ventilation_loss_are_dimensional():
    result = calculate_design_heat_load(case())
    assert result.status == "DER"
    assert result.transmission_h_w_per_k == 156.0
    assert result.ventilation_h_w_per_k == 49.5
    assert result.design_heat_load_kw == 6.165


def test_before_after_recomputes_physical_state_not_annual_factor():
    result = calculate_before_after_design_load(case(), case(wall_u=0.3))
    assert result.status == "DER"
    assert result.baseline.design_heat_load_kw == 6.165
    assert result.post.design_heat_load_kw == 4.665
    assert result.peak_reduction_kw == 1.5
    assert result.peak_reduction_fraction == 1.5 / 6.165


def test_missing_area_u_design_temperature_and_ventilation_fail_closed():
    missing = case()
    bad_component = EnvelopeComponent("wall", ev(None, "Q"), ev(None, "Q"), "external", ev(1.0))
    missing = DesignLoadInputs(
        missing.building_id, missing.location_or_climate_zone, ev(None, "Q"), missing.design_indoor_temperature_c,
        (bad_component,), missing.thermal_bridge_h_w_per_k,
        VentilationInput(ev(300.0), heat_recovery_efficiency=ev(None, "Q"), air_volumetric_heat_capacity_wh_m3k=ev(None, "Q")),
    )
    result = calculate_design_heat_load(missing)
    assert result.status == "Q"
    assert result.design_heat_load_kw is None
    assert result.gaps


def test_annual_factor_and_installed_capacity_are_not_inputs():
    assert "capacity" not in DesignLoadInputs.__annotations__
    assert "annual" not in DesignLoadInputs.__annotations__


def test_supply_requires_explicit_emitter_and_return_temperature():
    emitter = EmitterRating(ev(10.0), ev(75.0), ev(65.0), ev(20.0), ev(1.3))
    points = (EmitterOperatingPoint(ev(45.0), ev(35.0), ev(20.0)), EmitterOperatingPoint(ev(55.0), ev(45.0), ev(20.0)))
    result = derive_required_supply_temperature(ev(1.0), emitter, points)
    assert result.status == "DER"
    assert result.required_supply_temperature_c == 45.0

    missing_return = (EmitterOperatingPoint(ev(35.0), ev(None, "Q"), ev(20.0)),)
    assert derive_required_supply_temperature(ev(1.0), emitter, missing_return).status == "Q"


def test_no_automatic_w35_and_b05_out_of_domain_is_q():
    emitter = EmitterRating(ev(10.0), ev(75.0), ev(65.0), ev(20.0), ev(1.3))
    result = derive_required_supply_temperature(ev(4.0), emitter, (EmitterOperatingPoint(ev(35.0), ev(25.0), ev(20.0)),))
    assert result.status == "Q"
    assert b05_design_point_coverage([], "VAILLANT", -10.0, 35.0) == "Q / OUT_OF_PERFORMANCE_DOMAIN"


def test_peak_evidence_layer_is_explicit_synthetic_fixture_only():
    with EVIDENCE.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    assert rows
    assert all(row["evidence_status"] == "SCN" for row in rows)
    assert all(row["provenance"] == "DIRECT_PHYSICAL_DERIVATION" for row in rows)
    assert all(row["baseline_design_heat_load_kw"] and row["post_design_heat_load_kw"] for row in rows)
