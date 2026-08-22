import csv
from pathlib import Path

from math import isclose

from modules.B06.design_load import (
    DesignLoadInputs,
    EmitterOperatingPoint,
    EmitterRating,
    EnvelopeComponent,
    VentilationInput,
    b05_design_point_coverage,
    B05DesignPointBridge,
    SupplyTemperatureResult,
    build_b05_design_point_bridge,
    calculate_before_after_design_load,
    calculate_design_heat_load,
    derive_required_supply_temperature,
)
from modules.B06.engine import EvidenceValue


ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "data" / "processed" / "retrofit_peak_design_evidence.csv"
EMITTER_EVIDENCE = ROOT / "data" / "processed" / "emitter_performance_evidence.csv"
SUPPLY_RESULTS = ROOT / "data" / "processed" / "emitter_supply_temperature_results.csv"
PERFORMANCE_POINTS = ROOT / "data" / "processed" / "heat_pump_performance_points.csv"


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
    emitter = EmitterRating(
        ev(10.0, "DER"), ev(75.0, "DER"), ev(65.0, "DER"), ev(20.0, "DER"), ev(1.3, "DER"),
        quantity=ev(1.0, "DER"), emitter_id="SCN-RADIATOR", correction_method=ev("EXPLICIT_ARITHMETIC_MEAN", "DER"),
    )
    points = (EmitterOperatingPoint(ev(45.0, "DER"), ev(35.0, "DER"), ev(20.0, "DER")), EmitterOperatingPoint(ev(55.0, "DER"), ev(45.0, "DER"), ev(20.0, "DER")))
    result = derive_required_supply_temperature(ev(1.0, "DER"), emitter, points)
    assert result.status == "DER"
    assert result.required_supply_temperature_c == 45.0

    missing_return = (EmitterOperatingPoint(ev(35.0), ev(None, "Q"), ev(20.0)),)
    assert derive_required_supply_temperature(ev(1.0), emitter, missing_return).status == "Q"


def test_no_automatic_w35_and_b05_out_of_domain_is_q():
    emitter = EmitterRating(
        ev(10.0, "DER"), ev(75.0, "DER"), ev(65.0, "DER"), ev(20.0, "DER"), ev(1.3, "DER"),
        quantity=ev(1.0, "DER"), emitter_id="SCN-RADIATOR", correction_method=ev("EXPLICIT_ARITHMETIC_MEAN", "DER"),
    )
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


def purmo_emitter(quantity=1.0, status="SCN", **overrides):
    values = {
        "nominal_output_kw": ev(6.927, status),
        "nominal_flow_temperature_c": ev(75.0, status),
        "nominal_return_temperature_c": ev(65.0, status),
        "room_temperature_c": ev(20.0, status),
        "temperature_exponent": ev(1.3417, status),
        "quantity": ev(quantity, status),
        "emitter_id": "PURMO-PLAN-COMPACT-FC33-600X3000",
        "manufacturer": "Purmo Group",
        "model_type": "PURMO Plan Compact FC type 33",
        "dimensions_mm": "600x3000",
        "correction_method": ev("PURMO_EN442_ARITHMETIC_OR_LOG_MEAN", status),
    }
    values.update(overrides)
    return EmitterRating(**values)


def explicit_points(start=41.0, stop=75.0, step=0.1):
    count = int(round((stop - start) / step))
    return tuple(
        EmitterOperatingPoint(ev(round(start + i * step, 1)), ev(round(start + i * step - 20, 1)), ev(20.0))
        for i in range(count + 1)
    )


def test_real_purmo_nominal_condition_reproduces_nominal_output():
    result = derive_required_supply_temperature(ev(6.927), purmo_emitter(), (EmitterOperatingPoint(ev(75.0), ev(65.0), ev(20.0)),))
    assert result.status == "SCN"
    assert result.required_supply_temperature_c == 75.0
    assert result.estimated_output_kw == 6.927


def test_purmo_logarithmic_mean_branch_and_lower_water_reduce_output():
    emitter = purmo_emitter()
    nominal = derive_required_supply_temperature(ev(6.927), emitter, (EmitterOperatingPoint(ev(75.0), ev(65.0), ev(20.0)),))
    low = derive_required_supply_temperature(ev(1.0), emitter, (EmitterOperatingPoint(ev(45.0), ev(25.0), ev(20.0)),))
    assert nominal.estimated_output_kw == 6.927
    assert low.estimated_output_kw is not None and low.estimated_output_kw < nominal.estimated_output_kw
    assert low.required_supply_temperature_c == 45.0


def test_lower_post_load_and_larger_emitter_each_reduce_required_supply():
    emitter = purmo_emitter(quantity=6.0)
    before = derive_required_supply_temperature(ev(6.165), emitter, explicit_points())
    after = derive_required_supply_temperature(ev(4.665), emitter, explicit_points())
    upgraded = derive_required_supply_temperature(ev(4.665), purmo_emitter(quantity=8.0), explicit_points())
    assert before.required_supply_temperature_c == 44.8
    assert after.required_supply_temperature_c == 43.0
    assert upgraded.required_supply_temperature_c == 41.8
    assert after.required_supply_temperature_c < before.required_supply_temperature_c
    assert upgraded.required_supply_temperature_c < after.required_supply_temperature_c


def test_missing_emitter_fields_fail_closed():
    assert derive_required_supply_temperature(ev(4.0), purmo_emitter(temperature_exponent=ev(None, "Q")), explicit_points()).status == "Q"
    assert derive_required_supply_temperature(ev(4.0), purmo_emitter(nominal_output_kw=ev(None, "Q")), explicit_points()).status == "Q"
    assert derive_required_supply_temperature(ev(4.0), purmo_emitter(correction_method=ev(None, "Q")), explicit_points()).status == "Q"
    missing_return = (EmitterOperatingPoint(ev(45.0), ev(None, "Q"), ev(20.0)),)
    assert derive_required_supply_temperature(ev(4.0), purmo_emitter(), missing_return).status == "Q"
    assert derive_required_supply_temperature(ev(4.0), purmo_emitter(emitter_id=""), explicit_points()).status == "Q"


def test_no_w35_w45_w55_snapping():
    result = derive_required_supply_temperature(
        ev(7.0), purmo_emitter(quantity=6.0),
        (EmitterOperatingPoint(ev(35.0), ev(15.0), ev(20.0)), EmitterOperatingPoint(ev(45.0), ev(25.0), ev(20.0))),
    )
    assert result.status == "Q"


def test_p3_post_load_enters_b05_bridge_and_capacity_shortfall_is_explicit():
    from modules.B05.engine import PerformanceMap

    post_load = calculate_design_heat_load(case(wall_u=0.3))
    supply = derive_required_supply_temperature(ev(post_load.design_heat_load_kw), purmo_emitter(quantity=6.0), explicit_points())
    performance_map = PerformanceMap.from_csv(PERFORMANCE_POINTS, "TEST-AWHP-REFERENCE")
    bridge = build_b05_design_point_bridge(post_load, supply, ev(-10.0), ev(0.0), performance_map, "TEST-AWHP-REFERENCE")
    assert isinstance(bridge, B05DesignPointBridge)
    assert bridge.required_supply_temperature_c == 43.0
    assert bridge.status == "SCN / CAPACITY_SHORTFALL"
    assert bridge.available_capacity_kw == 4.2
    assert isclose(bridge.capacity_shortfall_kw, 0.465, rel_tol=0.0, abs_tol=1e-12)
    unsupported = build_b05_design_point_bridge(
        post_load, SupplyTemperatureResult("SCN", 55.0, 5.0, ()), ev(-10.0), ev(0.0), performance_map, "TEST-AWHP-REFERENCE",
    )
    assert unsupported.status.startswith("Q / OUT_OF_PERFORMANCE_DOMAIN")


def test_emitter_and_result_datasets_are_lineaged_and_non_national():
    with EMITTER_EVIDENCE.open(encoding="utf-8", newline="") as handle:
        emitters = list(csv.DictReader(handle))
    with SUPPLY_RESULTS.open(encoding="utf-8", newline="") as handle:
        results = list(csv.DictReader(handle))
    assert len(emitters) == 1
    assert emitters[0]["status"] == "OBS"
    assert emitters[0]["correction_method"] == "PURMO_EN442_ARITHMETIC_OR_LOG_MEAN"
    assert len(results) == 3
    assert all(row["status"].startswith("SCN") for row in results)
    assert all("scenario" in row["notes"].lower() or "explicit" in row["notes"].lower() for row in results)
