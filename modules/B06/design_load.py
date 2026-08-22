"""Fail-closed physical design heat-load helpers for B06-P3.

This module is deliberately separate from the P1 annual/factor engine.  It
calculates a design-point heat loss from explicit envelope geometry, U-values,
thermal bridges and ventilation inputs.  No annual consumption, installed
boiler/heat-pump capacity or full-load-hours proxy is accepted here.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import isfinite, log
from typing import Iterable, Mapping

from .engine import EVIDENCE_STATUSES, EvidenceValue


@dataclass(frozen=True)
class EnvelopeComponent:
    """One boundary component in the transmission-loss sum."""

    component: str
    u_value_w_m2k: EvidenceValue[float]
    area_m2: EvidenceValue[float]
    boundary: str
    correction_factor: EvidenceValue[float]


@dataclass(frozen=True)
class VentilationInput:
    """Explicit ventilation/infiltration input; no hidden ACH default."""

    volume_m3: EvidenceValue[float]
    air_change_rate_h: EvidenceValue[float] | None = None
    airflow_m3_h: EvidenceValue[float] | None = None
    heat_recovery_efficiency: EvidenceValue[float] = EvidenceValue(None, "Q")
    air_volumetric_heat_capacity_wh_m3k: EvidenceValue[float] = EvidenceValue(None, "Q")


@dataclass(frozen=True)
class DesignLoadInputs:
    building_id: str
    location_or_climate_zone: EvidenceValue[str]
    design_outdoor_temperature_c: EvidenceValue[float]
    design_indoor_temperature_c: EvidenceValue[float]
    components: tuple[EnvelopeComponent, ...]
    thermal_bridge_h_w_per_k: EvidenceValue[float]
    ventilation: VentilationInput
    method_id: str = "B06-P3-TRANSMISSION-VENTILATION-DERIVATION"
    source_ids: tuple[str, ...] = ()


@dataclass(frozen=True)
class DesignLoadResult:
    status: str
    design_heat_load_kw: float | None
    transmission_h_w_per_k: float | None
    ventilation_h_w_per_k: float | None
    thermal_bridge_h_w_per_k: float | None
    delta_t_k: float | None
    gaps: tuple[str, ...]
    provenance: str = "DIRECT_PHYSICAL_DERIVATION"


@dataclass(frozen=True)
class BeforeAfterDesignResult:
    status: str
    baseline: DesignLoadResult
    post: DesignLoadResult
    peak_reduction_kw: float | None
    peak_reduction_fraction: float | None
    gaps: tuple[str, ...]


@dataclass(frozen=True)
class EmitterRating:
    """Source-native emitter curve parameters; no universal exponent default."""

    nominal_output_kw: EvidenceValue[float]
    nominal_flow_temperature_c: EvidenceValue[float]
    nominal_return_temperature_c: EvidenceValue[float]
    room_temperature_c: EvidenceValue[float]
    temperature_exponent: EvidenceValue[float]
    source_ids: tuple[str, ...] = ()
    quantity: EvidenceValue[float] = EvidenceValue(None, "Q")
    emitter_id: str = ""
    manufacturer: str = ""
    model_type: str = ""
    dimensions_mm: str = ""
    correction_method: EvidenceValue[str] = EvidenceValue(None, "Q")


@dataclass(frozen=True)
class EmitterOperatingPoint:
    supply_temperature_c: EvidenceValue[float]
    return_temperature_c: EvidenceValue[float]
    room_temperature_c: EvidenceValue[float]


@dataclass(frozen=True)
class SupplyTemperatureResult:
    status: str
    required_supply_temperature_c: float | None
    estimated_output_kw: float | None
    gaps: tuple[str, ...]
    provenance: str = "DIRECT_PHYSICAL_DERIVATION"


@dataclass(frozen=True)
class B05DesignPointBridge:
    """Complete B06 design-point handoff plus an explicit B05 map result."""

    status: str
    space_heating_required_kw: float | None
    required_supply_temperature_c: float | None
    design_outdoor_temperature_c: float | None
    dhw_required_kw: float | None
    equipment_id: str
    available_capacity_kw: float | None
    electrical_input_kw: float | None
    cop: float | None
    capacity_shortfall_kw: float | None
    source_ids: tuple[str, ...]
    notes: str


def _check_value(value: EvidenceValue[float], name: str, *, nonnegative: bool = True) -> str | None:
    value.validate(name)
    if value.value is None:
        return f"{name} is Q"
    if not isfinite(float(value.value)):
        return f"{name} is not finite"
    if nonnegative and float(value.value) < 0:
        return f"{name} is negative"
    return None


def _check_text(value: EvidenceValue[str], name: str) -> str | None:
    value.validate(name)
    if value.value is None or not str(value.value).strip():
        return f"{name} is Q"
    return None


def _status_for_values(values: Iterable[EvidenceValue[object]]) -> str:
    statuses = tuple(value.status for value in values)
    if "Q" in statuses:
        return "Q"
    if "SCN" in statuses:
        return "SCN"
    if "ASS" in statuses:
        return "ASS"
    if "POL" in statuses:
        return "POL"
    return "DER"


def _result_q(gaps: Iterable[str]) -> DesignLoadResult:
    return DesignLoadResult("Q", None, None, None, None, None, tuple(gaps))


def calculate_design_heat_load(inputs: DesignLoadInputs) -> DesignLoadResult:
    """Calculate H = sum(U*A*correction) + H_vent + H_bridge, then Q=H*ΔT."""

    gaps: list[str] = []
    if not inputs.building_id:
        gaps.append("building_id is required")
    inputs.location_or_climate_zone.validate("location_or_climate_zone")
    if inputs.location_or_climate_zone.value is None:
        gaps.append("location_or_climate_zone is Q")
    gaps.extend(filter(None, (
        _check_value(inputs.design_outdoor_temperature_c, "design_outdoor_temperature_c", nonnegative=False),
        _check_value(inputs.design_indoor_temperature_c, "design_indoor_temperature_c", nonnegative=False),
        _check_value(inputs.thermal_bridge_h_w_per_k, "thermal_bridge_h_w_per_k"),
    )))
    if not inputs.components:
        gaps.append("at least one envelope component is required")

    transmission = 0.0
    for item in inputs.components:
        if not item.component or not item.boundary:
            gaps.append(f"{item.component or 'component'} boundary is missing")
        gaps.extend(filter(None, (
            _check_value(item.u_value_w_m2k, f"{item.component}.u_value_w_m2k"),
            _check_value(item.area_m2, f"{item.component}.area_m2"),
            _check_value(item.correction_factor, f"{item.component}.correction_factor"),
        )))
        if all(value.value is not None for value in (item.u_value_w_m2k, item.area_m2, item.correction_factor)):
            transmission += float(item.u_value_w_m2k.value) * float(item.area_m2.value) * float(item.correction_factor.value)

    vent = inputs.ventilation
    gaps.extend(filter(None, (_check_value(vent.volume_m3, "ventilation.volume_m3"),
                              _check_value(vent.heat_recovery_efficiency, "ventilation.heat_recovery_efficiency"),
                              _check_value(vent.air_volumetric_heat_capacity_wh_m3k,
                                           "ventilation.air_volumetric_heat_capacity_wh_m3k"))))
    if vent.heat_recovery_efficiency.value is not None and not 0 <= float(vent.heat_recovery_efficiency.value) <= 1:
        gaps.append("ventilation.heat_recovery_efficiency must be between 0 and 1")
    if (vent.air_change_rate_h is None) == (vent.airflow_m3_h is None):
        gaps.append("exactly one of air_change_rate_h or airflow_m3_h is required")
    vent_rate = None
    if vent.air_change_rate_h is not None:
        gaps.append(_check_value(vent.air_change_rate_h, "ventilation.air_change_rate_h") or "")
        if vent.air_change_rate_h.value is not None and vent.volume_m3.value is not None:
            vent_rate = float(vent.volume_m3.value) * float(vent.air_change_rate_h.value)
    if vent.airflow_m3_h is not None:
        gaps.append(_check_value(vent.airflow_m3_h, "ventilation.airflow_m3_h") or "")
        if vent.airflow_m3_h.value is not None:
            vent_rate = float(vent.airflow_m3_h.value)
    gaps = [gap for gap in gaps if gap]
    if gaps:
        return _result_q(gaps)

    delta_t = float(inputs.design_indoor_temperature_c.value) - float(inputs.design_outdoor_temperature_c.value)
    if delta_t <= 0:
        return _result_q(("design indoor temperature must exceed design outdoor temperature",))
    ventilation_h = vent_rate * float(vent.air_volumetric_heat_capacity_wh_m3k.value) * (1 - float(vent.heat_recovery_efficiency.value))
    bridges = float(inputs.thermal_bridge_h_w_per_k.value)
    total_h = transmission + ventilation_h + bridges
    return DesignLoadResult(
        "DER", total_h * delta_t / 1000.0, transmission, ventilation_h, bridges, delta_t, (),
    )


def calculate_before_after_design_load(baseline: DesignLoadInputs, post: DesignLoadInputs) -> BeforeAfterDesignResult:
    """Recalculate baseline and post-intervention states independently."""

    gaps: list[str] = []
    if baseline.building_id != post.building_id:
        gaps.append("baseline and post building_id must match")
    if baseline.design_outdoor_temperature_c.value != post.design_outdoor_temperature_c.value:
        gaps.append("baseline and post design outdoor temperature must match")
    if baseline.design_indoor_temperature_c.value != post.design_indoor_temperature_c.value:
        gaps.append("baseline and post design indoor temperature must match")
    before = calculate_design_heat_load(baseline)
    after = calculate_design_heat_load(post)
    gaps.extend(before.gaps)
    gaps.extend(after.gaps)
    if gaps or before.design_heat_load_kw is None or after.design_heat_load_kw is None:
        return BeforeAfterDesignResult("Q", before, after, None, None, tuple(gaps))
    reduction = before.design_heat_load_kw - after.design_heat_load_kw
    return BeforeAfterDesignResult(
        "DER", before, after, reduction,
        reduction / before.design_heat_load_kw if before.design_heat_load_kw else 0.0, (),
    )


def derive_required_supply_temperature(
    design_heat_load_kw: EvidenceValue[float],
    emitter: EmitterRating,
    operating_points: Iterable[EmitterOperatingPoint],
) -> SupplyTemperatureResult:
    """Use only explicitly supplied emitter ratings and flow/return points.

    The Purmo public method uses arithmetic mean water temperature unless
    ``c = (T_return - T_room) / (T_flow - T_room) < 0.7``; below that boundary
    it uses the logarithmic mean.  The method must be explicitly declared on
    the emitter record, so an unsupported or missing correction method is Q.
    """

    gaps: list[str] = []
    gaps.append(_check_value(design_heat_load_kw, "design_heat_load_kw") or "")
    fields = (
        (emitter.nominal_output_kw, "emitter.nominal_output_kw"),
        (emitter.nominal_flow_temperature_c, "emitter.nominal_flow_temperature_c"),
        (emitter.nominal_return_temperature_c, "emitter.nominal_return_temperature_c"),
        (emitter.room_temperature_c, "emitter.room_temperature_c"),
        (emitter.temperature_exponent, "emitter.temperature_exponent"),
        (emitter.quantity, "emitter.quantity"),
    )
    for value, name in fields:
        gaps.append(_check_value(value, name, nonnegative=False) or "")
    gaps.append(_check_text(emitter.correction_method, "emitter.correction_method") or "")
    if not emitter.emitter_id:
        gaps.append("emitter.emitter_id is required")
    if emitter.correction_method.value not in {"PURMO_EN442_ARITHMETIC_OR_LOG_MEAN", "EXPLICIT_ARITHMETIC_MEAN"}:
        gaps.append("unsupported emitter correction method")
    if emitter.quantity.value is not None and float(emitter.quantity.value) <= 0:
        gaps.append("emitter.quantity must be positive")
    points = tuple(operating_points)
    if not points:
        gaps.append("no explicit emitter operating points")
    gaps = [gap for gap in gaps if gap]
    if gaps:
        return SupplyTemperatureResult("Q", None, None, tuple(gaps))
    nominal_flow = float(emitter.nominal_flow_temperature_c.value)
    nominal_return = float(emitter.nominal_return_temperature_c.value)
    nominal_room = float(emitter.room_temperature_c.value)
    nominal_delta = (nominal_flow + nominal_return) / 2 - nominal_room
    if nominal_delta <= 0 or float(emitter.temperature_exponent.value) <= 0 or nominal_return <= nominal_room:
        return SupplyTemperatureResult("Q", None, None, ("invalid nominal emitter temperature basis",))
    load = float(design_heat_load_kw.value)
    candidates: list[tuple[float, float]] = []
    point_values: list[EvidenceValue[object]] = [
        design_heat_load_kw,
        emitter.nominal_output_kw,
        emitter.nominal_flow_temperature_c,
        emitter.nominal_return_temperature_c,
        emitter.room_temperature_c,
        emitter.temperature_exponent,
        emitter.quantity,
        emitter.correction_method,
    ]
    for point in points:
        point_gaps = [
            _check_value(point.supply_temperature_c, "emitter operating-point supply", nonnegative=False),
            _check_value(point.return_temperature_c, "emitter operating-point return", nonnegative=False),
            _check_value(point.room_temperature_c, "emitter operating-point room", nonnegative=False),
        ]
        if any(point_gaps):
            return SupplyTemperatureResult("Q", None, None, tuple(g for g in point_gaps if g))
        point_values.extend((point.supply_temperature_c, point.return_temperature_c, point.room_temperature_c))
        flow = float(point.supply_temperature_c.value)
        return_temperature = float(point.return_temperature_c.value)
        room = float(point.room_temperature_c.value)
        if flow <= room or return_temperature <= room or flow <= return_temperature:
            continue
        ratio = (return_temperature - room) / (flow - room)
        if emitter.correction_method.value == "PURMO_EN442_ARITHMETIC_OR_LOG_MEAN" and ratio < 0.7:
            mean_delta = (flow - return_temperature) / log((flow - room) / (return_temperature - room))
        else:
            mean_delta = (flow + return_temperature) / 2 - room
        if mean_delta <= 0:
            continue
        output = float(emitter.nominal_output_kw.value) * float(emitter.quantity.value) * (mean_delta / nominal_delta) ** float(emitter.temperature_exponent.value)
        candidates.append((float(point.supply_temperature_c.value), output))
    sufficient = [(supply, output) for supply, output in candidates if output >= load]
    if not sufficient:
        return SupplyTemperatureResult("Q", None, None, ("no supported emitter point meets design load",))
    supply, output = min(sufficient, key=lambda item: item[0])
    status = _status_for_values(point_values)
    return SupplyTemperatureResult(status, supply, output, ())


def build_b05_design_point_bridge(
    design_load: DesignLoadResult,
    supply: SupplyTemperatureResult,
    design_outdoor_temperature_c: EvidenceValue[float],
    dhw_required_kw: EvidenceValue[float],
    performance_map: object,
    equipment_id: str,
) -> B05DesignPointBridge:
    """Pass the numeric B06 point through the existing bounded B05 map.

    ``performance_map`` is intentionally duck-typed to avoid making B06 a
    second performance-map authority; its canonical ``evaluate`` method is
    called and any unsupported outdoor/supply point remains Q.
    """

    gaps: list[str] = []
    if design_load.design_heat_load_kw is None or design_load.status == "Q":
        gaps.append("design heat load is Q")
    if supply.required_supply_temperature_c is None or supply.status == "Q":
        gaps.append("required supply temperature is Q")
    gaps.append(_check_value(design_outdoor_temperature_c, "design_outdoor_temperature_c", nonnegative=False) or "")
    gaps.append(_check_value(dhw_required_kw, "dhw_required_kw") or "")
    gaps = [gap for gap in gaps if gap]
    if gaps:
        return B05DesignPointBridge(
            "Q", design_load.design_heat_load_kw, supply.required_supply_temperature_c,
            design_outdoor_temperature_c.value, dhw_required_kw.value, equipment_id,
            None, None, None, None, (), "; ".join(gaps),
        )
    operating = performance_map.evaluate(
        float(design_outdoor_temperature_c.value), float(supply.required_supply_temperature_c),
    )
    source_ids = tuple(operating.point.source_ids) if operating.point is not None else ()
    if operating.point is None:
        return B05DesignPointBridge(
            operating.status, design_load.design_heat_load_kw, supply.required_supply_temperature_c,
            design_outdoor_temperature_c.value, dhw_required_kw.value, equipment_id,
            None, None, None, None, source_ids, operating.reason,
        )
    point = operating.point
    shortfall = max(float(design_load.design_heat_load_kw) - point.thermal_capacity_kw, 0.0)
    status = _status_for_values((design_outdoor_temperature_c, dhw_required_kw))
    if supply.status == "SCN" or design_load.status == "SCN":
        status = "SCN"
    if shortfall > 0:
        status = f"{status} / CAPACITY_SHORTFALL"
    else:
        status = f"{status} / VALID"
    return B05DesignPointBridge(
        status, design_load.design_heat_load_kw, supply.required_supply_temperature_c,
        design_outdoor_temperature_c.value, dhw_required_kw.value, equipment_id,
        point.thermal_capacity_kw, point.electrical_input_kw, point.cop, shortfall,
            source_ids, f"B05 {point.interpolation} at the explicit B06 design point.",
    )


def b05_design_point_coverage(
    points: Iterable[Mapping[str, object]], equipment_id: str, outdoor_temperature_c: float, supply_temperature_c: float,
) -> str:
    """Exact source-native point coverage check; no out-of-domain extrapolation."""

    for row in points:
        if row.get("equipment_id") != equipment_id or row.get("evidence_status") not in {"OBS", "DER"}:
            continue
        try:
            if float(row["outdoor_temperature_C"]) == outdoor_temperature_c and float(row["supply_temperature_C"]) == supply_temperature_c:
                return "VALIDATED"
        except (KeyError, TypeError, ValueError):
            continue
    return "Q / OUT_OF_PERFORMANCE_DOMAIN"
