"""B05-P56 Trane FCC06 state-dependent physical response contract.

The peer-reviewed FCC06 experiment provides an exact heating-mode dynamic
record and an identified switched-linear physical surface.  It does not report
one universal HEM tau_out scalar.  This module preserves that distinction.
"""

from __future__ import annotations

from dataclasses import dataclass

SOURCE_ID = "SRC-B05-FCU-FCC06-CONTROL-DYNAMIC-2019"

FAN_SPEEDS = ("OFF", "L", "M", "H")
A_W_PER_K = {
    "OFF": 5.30,
    "L": 96.45,
    "M": 152.90,
    "H": 201.80,
}
B_FLOW = {
    "OFF": 0.0,
    "L": 1.73e-3,
    "M": 3.58e-3,
    "H": 5.40e-3,
}
BETA = 1.86
HEATING_EPSILON = 1.0

EXPERIMENT_STEP_DURATION_S = 480
THERMODYNAMIC_IDENTIFICATION_RUNS = 32
MODEL_VALIDATION_NRMSE_UPPER_PERCENT = 6.0

EXACT_DYNAMIC_RECORD_QUALIFIED = "EXACT_FCC06_HEATING_STATE_DEPENDENT_DYNAMIC_RECORD_QUALIFIED"
Q_WATER_MASS_REQUIRED = "Q / EXACT_FCC06_WATER_MASS_REQUIRED"
DER_STATE_TIME_CONSTANT = "DER / FCC06_WATER_STATE_TIME_CONSTANT"
HEM_TAU_OUT_NOT_ADMITTED = "HEM_TAU_OUT_NOT_ADMITTED_FROM_FCC06_STATE_SURFACE"


@dataclass(frozen=True)
class StateTimeConstant:
    status: str
    value_s: float | None
    source_id: str
    reason: str


def heat_transfer_coefficient_w_per_k(fan_speed: str, water_flow_kg_s: float) -> float:
    """Heating-season Uo(x, qw) from the identified FCC06 source surface."""

    speed = fan_speed.upper()
    if speed not in FAN_SPEEDS:
        raise ValueError("fan_speed must be OFF, L, M or H")
    if water_flow_kg_s <= 0:
        raise ValueError("water_flow_kg_s must be positive")

    a = A_W_PER_K[speed]
    b = B_FLOW[speed]
    return HEATING_EPSILON * a / (1.0 + b * water_flow_kg_s ** (-BETA))


def resolve_water_state_time_constant_s(
    *,
    fan_speed: str,
    water_flow_kg_s: float,
    water_mass_kg: float | None,
    water_heat_capacity_j_per_kg_k: float,
) -> StateTimeConstant:
    """Derive the first-order *water-state* time constant from the published ODE.

    This is not the HEM/EN15316 emitter tau_out.  The source states that the
    in-coil water mass is available from the manufacturer catalogue, but the
    exact FCC06 value is not present in the peer-reviewed article layer used by
    P56.  Missing mass therefore fails closed.
    """

    if water_mass_kg is None:
        return StateTimeConstant(
            Q_WATER_MASS_REQUIRED,
            None,
            SOURCE_ID,
            "Exact FCC06 in-coil water mass is required before numeric derivation.",
        )
    if water_mass_kg <= 0:
        raise ValueError("water_mass_kg must be positive")
    if water_heat_capacity_j_per_kg_k <= 0:
        raise ValueError("water_heat_capacity_j_per_kg_k must be positive")

    u = heat_transfer_coefficient_w_per_k(fan_speed, water_flow_kg_s)
    # Published ODE:
    # dTout/dt = -(qw/mw + Uo/(2*mw*cw))*Tout + ...
    # Therefore tau_water = 1 / (qw/mw + Uo/(2*mw*cw)).
    denominator_kg_s = water_flow_kg_s + u / (2.0 * water_heat_capacity_j_per_kg_k)
    tau_s = water_mass_kg / denominator_kg_s
    return StateTimeConstant(
        DER_STATE_TIME_CONSTANT,
        tau_s,
        SOURCE_ID,
        "Derived from the exact FCC06 switched-linear water-state ODE; not HEM tau_out.",
    )


def p56_boundaries() -> tuple[str, ...]:
    return (
        "EXACT_FCC06_HEATING_DYNAMIC_RECORD != UNIVERSAL_FANCOIL_RESPONSE_CONSTANT",
        "EIGHT_MINUTE_EXPERIMENT_WINDOW != RESPONSE_TIME_480_SECONDS",
        "FCC06_WATER_STATE_TIME_CONSTANT != HEM_EN15316_TAU_OUT",
        "STATE_DEPENDENT_FCU_PHYSICS != SINGLE_SCALAR_WITHOUT_MAPPING_AUTHORITY",
        "PEER_REVIEWED_DYNAMIC_RECORD != CROSS_PRODUCT_FANCOIL_TRANSFER",
        "PART_LOAD_READINESS_NO_MECHANICAL_UPLIFT",
    )
