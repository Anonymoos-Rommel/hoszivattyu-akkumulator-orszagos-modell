"""B05-P32 stateful Dimplex DHW + exact W65 performance contract.

P32 binds two source-native evidence layers for the exact LA2030CP + WPM Touch
system:
1. DHW request state from the controller's setpoint/hysteresis/HP-maximum rules;
2. exact W65 minimum/maximum Qh, Pel and COP observations.

No graph digitization, interpolation or inferred inverter level is permitted.
"""

from __future__ import annotations

from dataclasses import dataclass

from modules.B05.dhw_dispatch_contract import (
    DIMPLEX_LA2030CP_WPM_TOUCH,
    classify_simultaneous_dispatch,
)

DIMPLEX_W65_SOURCE_ID = "SRC-B05-DIMPLEX-LA2030CP-W65-PERFORMANCE-2026"
DIMPLEX_WPM_SOURCE_ID = "SRC-B05-DIMPLEX-WPMTOUCH-DHW-CONTROL-2026"

MIN_LEVEL = "MIN"
MAX_LEVEL = "MAX"

Q_W65_TARGET_REQUIRED = "Q_DIMPLEX_DHW_HIGH_TEMP_PERFORMANCE_TARGET_NOT_W65"
Q_W65_LEVEL_REQUIRED = "Q_DIMPLEX_W65_PERFORMANCE_LEVEL_REQUIRED"
Q_W65_AMBIENT_POINT_REQUIRED = "Q_DIMPLEX_W65_EXACT_AMBIENT_POINT_REQUIRED"


@dataclass(frozen=True)
class DimplexDhwRequestState:
    request_active: bool
    status: str
    effective_hp_target_c: float
    request_on_threshold_c: float
    auxiliary_reheat_required: bool
    heat_pump_cannot_reach_requested_setpoint: bool
    evidence_status: str = "DER"


@dataclass(frozen=True)
class DimplexW65Point:
    outdoor_temperature_c: float
    performance_level: str
    thermal_capacity_kw: float
    electrical_input_kw: float
    cop: float
    water_outlet_temperature_c: float = 65.0
    evidence_status: str = "OBS"
    source_id: str = DIMPLEX_W65_SOURCE_ID


@dataclass(frozen=True)
class DimplexDhwRuntimeResult:
    status: str
    request_state: DimplexDhwRequestState
    active_mode: str | None
    performance_point: DimplexW65Point | None
    performance_ready: bool
    auxiliary_reheat_required: bool
    evidence_status: str
    residual_gap: str | None


# Exact source-native W65 table, System C planning manual v03/2026,
# LA2030CP technical product information section 3.10.4.
_W65 = {
    (-15.0, MIN_LEVEL): (8.72, 5.77, 1.51),
    (-15.0, MAX_LEVEL): (17.60, 12.39, 1.42),
    (-10.0, MIN_LEVEL): (8.32, 4.80, 1.73),
    (-10.0, MAX_LEVEL): (20.05, 12.43, 1.61),
    (-7.0, MIN_LEVEL): (7.84, 4.30, 1.82),
    (-7.0, MAX_LEVEL): (21.60, 12.36, 1.75),
    (2.0, MIN_LEVEL): (5.70, 2.69, 2.12),
    (2.0, MAX_LEVEL): (17.37, 8.19, 2.12),
    (7.0, MIN_LEVEL): (6.41, 2.60, 2.47),
    (7.0, MAX_LEVEL): (16.75, 6.54, 2.56),
    (12.0, MIN_LEVEL): (7.18, 2.58, 2.78),
    (12.0, MAX_LEVEL): (18.65, 6.53, 2.86),
    (20.0, MIN_LEVEL): (8.41, 2.60, 3.23),
    (20.0, MAX_LEVEL): (20.58, 6.55, 3.14),
    (30.0, MIN_LEVEL): (10.47, 2.56, 4.09),
    (30.0, MAX_LEVEL): (24.95, 6.48, 3.85),
    (40.0, MIN_LEVEL): (12.79, 2.49, 5.14),
    (40.0, MAX_LEVEL): (29.57, 6.37, 4.64),
}


def resolve_dimplex_dhw_request(
    *,
    tank_temperature_c: float,
    dhw_set_temperature_c: float,
    hysteresis_k: float,
    hp_max_temperature_c: float,
    previous_request_active: bool,
    flange_heater_reheat_enabled: bool,
) -> DimplexDhwRequestState:
    """Resolve the source-defined WPM Touch heat-pump DHW request state.

    The heat-pump target is capped by the controller's current HP maximum.
    A new request starts below target-hysteresis.  An existing request remains
    pending through the deadband until the effective HP target is reached.
    """

    if hysteresis_k <= 0:
        raise ValueError("hysteresis_k must be positive")
    if dhw_set_temperature_c <= 0 or hp_max_temperature_c <= 0:
        raise ValueError("DHW set temperature and HP maximum must be positive")

    target = min(float(dhw_set_temperature_c), float(hp_max_temperature_c))
    on_threshold = target - float(hysteresis_k)

    if tank_temperature_c < on_threshold:
        active = True
        status = "QUALIFIED_DHW_REQUEST_START_BELOW_TARGET_MINUS_HYSTERESIS"
    elif previous_request_active and tank_temperature_c < target:
        active = True
        status = "QUALIFIED_DHW_REQUEST_HOLD_THROUGH_HYSTERESIS_BAND"
    else:
        active = False
        status = "QUALIFIED_DHW_REQUEST_OFF_AT_OR_ABOVE_EFFECTIVE_TARGET_OR_IDLE_BAND"

    above_hp_max = dhw_set_temperature_c > hp_max_temperature_c
    auxiliary = bool(above_hp_max and flange_heater_reheat_enabled)

    return DimplexDhwRequestState(
        request_active=active,
        status=status,
        effective_hp_target_c=target,
        request_on_threshold_c=on_threshold,
        auxiliary_reheat_required=auxiliary,
        heat_pump_cannot_reach_requested_setpoint=above_hp_max,
    )


def lookup_dimplex_w65_point(
    *,
    outdoor_temperature_c: float,
    performance_level: str,
) -> DimplexW65Point | None:
    """Return only exact source-table coordinates; no interpolation."""
    if performance_level not in {MIN_LEVEL, MAX_LEVEL}:
        return None
    values = _W65.get((float(outdoor_temperature_c), performance_level))
    if values is None:
        return None
    qh, pel, cop = values
    return DimplexW65Point(
        outdoor_temperature_c=float(outdoor_temperature_c),
        performance_level=performance_level,
        thermal_capacity_kw=qh,
        electrical_input_kw=pel,
        cop=cop,
    )


def evaluate_dimplex_dhw_w65_runtime(
    *,
    tank_temperature_c: float,
    dhw_set_temperature_c: float,
    hysteresis_k: float,
    hp_max_temperature_c: float,
    previous_request_active: bool,
    flange_heater_reheat_enabled: bool,
    space_heating_request: bool,
    outdoor_temperature_c: float,
    performance_level: str | None,
) -> DimplexDhwRuntimeResult:
    """Join stateful controller dispatch to an exact W65 performance point."""

    request = resolve_dimplex_dhw_request(
        tank_temperature_c=tank_temperature_c,
        dhw_set_temperature_c=dhw_set_temperature_c,
        hysteresis_k=hysteresis_k,
        hp_max_temperature_c=hp_max_temperature_c,
        previous_request_active=previous_request_active,
        flange_heater_reheat_enabled=flange_heater_reheat_enabled,
    )

    dispatch = classify_simultaneous_dispatch(
        DIMPLEX_LA2030CP_WPM_TOUCH,
        space_heating_request=space_heating_request,
        dhw_request=request.request_active,
    )

    if not request.request_active:
        return DimplexDhwRuntimeResult(
            "QUALIFIED_NO_DHW_REQUEST",
            request,
            dispatch.active_mode,
            None,
            True,
            request.auxiliary_reheat_required,
            "DER",
            None,
        )

    if request.effective_hp_target_c != 65.0:
        return DimplexDhwRuntimeResult(
            Q_W65_TARGET_REQUIRED,
            request,
            dispatch.active_mode,
            None,
            False,
            request.auxiliary_reheat_required,
            "Q",
            "DHW_HIGH_TEMP_PERFORMANCE_OUTSIDE_DIMPLEX_W65_EXACT_GRID_REQUIRED",
        )

    if performance_level not in {MIN_LEVEL, MAX_LEVEL}:
        return DimplexDhwRuntimeResult(
            Q_W65_LEVEL_REQUIRED,
            request,
            dispatch.active_mode,
            None,
            False,
            request.auxiliary_reheat_required,
            "Q",
            "DIMPLEX_W65_RUNTIME_PERFORMANCE_LEVEL_REQUIRED",
        )

    point = lookup_dimplex_w65_point(
        outdoor_temperature_c=outdoor_temperature_c,
        performance_level=performance_level,
    )
    if point is None:
        return DimplexDhwRuntimeResult(
            Q_W65_AMBIENT_POINT_REQUIRED,
            request,
            dispatch.active_mode,
            None,
            False,
            request.auxiliary_reheat_required,
            "Q",
            "DHW_HIGH_TEMP_PERFORMANCE_OUTSIDE_DIMPLEX_W65_EXACT_GRID_REQUIRED",
        )

    status = (
        "QUALIFIED_DIMPLEX_W65_HP_SEGMENT_AUXILIARY_REHEAT_REQUIRED"
        if request.auxiliary_reheat_required
        else "QUALIFIED_DIMPLEX_W65_DHW_RUNTIME_POINT"
    )
    return DimplexDhwRuntimeResult(
        status,
        request,
        dispatch.active_mode,
        point,
        True,
        request.auxiliary_reheat_required,
        "OBS+DER",
        None if not request.auxiliary_reheat_required else "AUXILIARY_REHEAT_ENERGY_SEPARATE",
    )


def p32_boundary() -> tuple[str, ...]:
    return (
        "CONTROLLER_STATE_PLUS_EXACT_PRODUCT_PERFORMANCE_REQUIRED",
        "OPERATING_LIMIT_DOES_NOT_MINT_PERFORMANCE",
        "NO_GRAPH_DIGITIZATION",
        "NO_W65_AMBIENT_INTERPOLATION",
        "NO_RUNTIME_INVERTER_LEVEL_INFERENCE",
        "AUXILIARY_REHEAT_SEPARATE_FROM_HEAT_PUMP_COP",
    )
