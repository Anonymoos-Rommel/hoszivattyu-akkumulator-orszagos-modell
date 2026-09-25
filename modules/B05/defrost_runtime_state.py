"""B05-P33 bounded NIBE S2125 defrost controller-state contract.

This module intentionally stops before event energy.  Manufacturer evidence can
identify controller/telemetry state, but it does not provide source-native heat
removed or electrical kWh per defrost event.

EXACT DEFROST STATE != WEATHER-ONLY EVENT FREQUENCY != EVENT ENERGY PENALTY
"""

from __future__ import annotations

from dataclasses import dataclass


NIBE_S2125 = "NIBE_S2125"
OFF = "OFF"
ACTIVE = "ACTIVE"
PASSIVE = "PASSIVE"
REQUIREMENT_PENDING = "REQUIREMENT_PENDING"
TIMER_PENDING = "ACTIVE_DEFROST_TIMER_PENDING"
ACTIVE_DUE = "ACTIVE_DEFROST_DUE"
PASSIVE_DUE = "PASSIVE_DEFROST_DUE"

Q_EVENT_ENERGY = "Q_NIBE_DEFROST_EVENT_HEAT_ELECTRIC_ENERGY_REQUIRED"
Q_WEATHER_TO_BT16 = "Q_WEATHER_TO_NIBE_BT16_OR_OBS_TIMESERIES_REQUIRED"


@dataclass(frozen=True)
class NibeDefrostDecision:
    state: str
    evidence_status: str
    requirement_accumulating: bool
    energy_ready: bool
    heat_penalty_kwh: float | None
    electricity_penalty_kwh: float | None
    residual_gaps: tuple[str, ...]
    reason: str


@dataclass(frozen=True)
class ActiveDefrostTermination:
    terminate: bool
    reasons: tuple[str, ...]


def defrost_requirement_accumulating(
    *,
    bt16_evaporator_c: float,
    start_threshold_bt16_c: float,
    compressor_running: bool,
) -> bool:
    """Whether source-defined conditions are accumulating defrost requirement."""
    return bool(compressor_running and bt16_evaporator_c < start_threshold_bt16_c)


def classify_nibe_controller_state(
    *,
    bt16_evaporator_c: float,
    bt28_outdoor_c: float,
    compressor_running: bool,
    compressor_demand_fulfilled: bool,
    time_until_active_defrost_min: float,
    start_threshold_bt16_c: float,
    passive_cutout_bt28_c: float,
) -> NibeDefrostDecision:
    """Classify bounded S2125 controller state without inventing timer dynamics.

    The controller-provided time-until-active-defrost value is an explicit input.
    P33 does not calculate its initial value, reset rule or weather-only frequency.
    """
    if time_until_active_defrost_min < 0:
        raise ValueError("time_until_active_defrost_min must be non-negative")

    accumulating = defrost_requirement_accumulating(
        bt16_evaporator_c=bt16_evaporator_c,
        start_threshold_bt16_c=start_threshold_bt16_c,
        compressor_running=compressor_running,
    )

    if time_until_active_defrost_min > 0:
        return NibeDefrostDecision(
            state=TIMER_PENDING,
            evidence_status="DER",
            requirement_accumulating=accumulating,
            energy_ready=False,
            heat_penalty_kwh=None,
            electricity_penalty_kwh=None,
            residual_gaps=(Q_EVENT_ENERGY, Q_WEATHER_TO_BT16),
            reason=(
                "The source-native controller timer remains pending while above "
                "zero. BT16 below the configured start threshold while the compressor "
                "runs determines whether that timer/requirement is currently "
                "accumulating; P33 does not erase prior controller state or synthesize "
                "timer initialization/reset dynamics."
            ),
        )

    if compressor_demand_fulfilled and bt28_outdoor_c > passive_cutout_bt28_c:
        state = PASSIVE_DUE
        reason = (
            "Defrost requirement is due and source conditions for passive "
            "defrost are met: compressor demand fulfilled and BT28 above the "
            "configured passive-defrost cut-out."
        )
    else:
        state = ACTIVE_DUE
        reason = (
            "Defrost requirement is due and passive-defrost conditions are not "
            "all met; the bounded source path is active defrost."
        )

    return NibeDefrostDecision(
        state=state,
        evidence_status="DER",
        requirement_accumulating=accumulating,
        energy_ready=False,
        heat_penalty_kwh=None,
        electricity_penalty_kwh=None,
        residual_gaps=(Q_EVENT_ENERGY, Q_WEATHER_TO_BT16),
        reason=reason,
    )


def active_defrost_termination(
    *,
    elapsed_minutes: float,
    evaporator_stop_value_reached: bool,
    bt3_return_c: float,
    bp8_below_permitted_minimum: bool,
) -> ActiveDefrostTermination:
    """Apply the explicit S2125 active-defrost termination conditions."""
    if elapsed_minutes < 0:
        raise ValueError("elapsed_minutes must be non-negative")

    reasons: list[str] = []
    if evaporator_stop_value_reached:
        reasons.append("EVAPORATOR_STOP_VALUE_REACHED")
    if elapsed_minutes > 15.0:
        reasons.append("ACTIVE_DEFROST_LONGER_THAN_15_MIN")
    if bt3_return_c < 10.0:
        reasons.append("BT3_RETURN_BELOW_10C")
    if bp8_below_permitted_minimum:
        reasons.append("BP8_BELOW_PERMITTED_MINIMUM")

    return ActiveDefrostTermination(bool(reasons), tuple(reasons))


def decode_nibe_modbus_defrost_status(raw_status: int) -> str:
    """Decode manufacturer Modbus Defrost status: 0 off, 1 active, 2 passive."""
    mapping = {0: OFF, 1: ACTIVE, 2: PASSIVE}
    if raw_status not in mapping:
        raise ValueError(f"unsupported NIBE Modbus defrost status: {raw_status!r}")
    return mapping[raw_status]


def observe_nibe_modbus_defrost_state(raw_status: int) -> NibeDefrostDecision:
    """Direct OBS path from the manufacturer Defrost register.

    State is observable; event heat/electric energy remains Q.
    """
    state = decode_nibe_modbus_defrost_status(raw_status)
    return NibeDefrostDecision(
        state=state,
        evidence_status="OBS",
        requirement_accumulating=False,
        energy_ready=False,
        heat_penalty_kwh=None,
        electricity_penalty_kwh=None,
        residual_gaps=(Q_EVENT_ENERGY,),
        reason="Direct source-native NIBE Modbus Defrost status.",
    )


def p33_boundary() -> tuple[str, ...]:
    return (
        "EXACT_DEFROST_STATE != WEATHER_ONLY_EVENT_FREQUENCY",
        "EXACT_DEFROST_STATE != EVENT_ENERGY_PENALTY",
        "AMBIENT_T_RH != BT16_WITHOUT_PRODUCT_MAPPING_OR_TELEMETRY",
        "ACTIVE_COMPRESSOR_ON_DOES_NOT_QUANTIFY_KWH",
        "PASSIVE_FAN_ON_DOES_NOT_QUANTIFY_KWH",
        "NO_UNIVERSAL_DEFROST_PERCENT",
    )
