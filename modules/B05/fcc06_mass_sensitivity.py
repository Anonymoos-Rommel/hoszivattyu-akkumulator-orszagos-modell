"""B05-P58 FCC06 water-mass sensitivity and cross-revision stability.

P58 does not promote cross-revision catalogue values to exact study identity.
It proves two structural properties of the published FCC06 ODE:

1. the steady-state outlet temperature is independent of in-coil water mass;
2. the first-order state time constant scales linearly with water mass.

A repeated 1.7 L size-06 / 2-pipe / 3-row water-content value across two
Trane catalogue revisions is admitted only for explicit sensitivity analysis.
"""

from __future__ import annotations

from dataclasses import dataclass

from modules.B05.fcu_state_dependent_response import heat_transfer_coefficient_w_per_k

CROSS_REVISION_WATER_CONTENT_L = 1.7
CROSS_REVISION_SOURCE_IDS = (
    "SRC-B05-TRANE-UNITRANE-PROD-PRC011-E4-2004",
    "SRC-B05-TRANE-UNITRANE-PROD-PRC014-E4-2006",
)

ASS_CROSS_REVISION_SENSITIVITY = "ASS / CROSS_REVISION_FCC06_WATER_MASS_SENSITIVITY"
Q_DENSITY_REQUIRED = "Q / EXPLICIT_MEDIUM_DENSITY_REQUIRED"
OBS_EXACT_MASS_NOT_ADMITTED = "OBS_EXACT_MASS_NOT_ADMITTED_FROM_CROSS_REVISION_VALUE"


@dataclass(frozen=True)
class SensitivityMass:
    status: str
    water_mass_kg: float | None
    evidence_status: str
    reason: str


def steady_state_outlet_temperature_c(
    *,
    inlet_temperature_c: float,
    zone_air_temperature_c: float,
    fan_speed: str,
    water_flow_kg_s: float,
    medium_heat_capacity_j_per_kg_k: float,
) -> float:
    """Steady state of the published FCC06 water-side ODE.

    Water mass cancels algebraically.  This function therefore requires no
    m_w and is valid only for the source-model steady-state semantics.
    """

    if water_flow_kg_s <= 0:
        raise ValueError("water_flow_kg_s must be positive")
    if medium_heat_capacity_j_per_kg_k <= 0:
        raise ValueError("medium_heat_capacity_j_per_kg_k must be positive")

    u = heat_transfer_coefficient_w_per_k(fan_speed, water_flow_kg_s)
    half_u_over_c = u / (2.0 * medium_heat_capacity_j_per_kg_k)
    denominator = water_flow_kg_s + half_u_over_c
    numerator = (
        (water_flow_kg_s - half_u_over_c) * inlet_temperature_c
        + (u / medium_heat_capacity_j_per_kg_k) * zone_air_temperature_c
    )
    return numerator / denominator


def normalized_state_time_constant_s_per_kg(
    *,
    fan_speed: str,
    water_flow_kg_s: float,
    medium_heat_capacity_j_per_kg_k: float,
) -> float:
    """Return tau/m_w for the published FCC06 first-order water state.

    tau = m_w / (q_w + U_o/(2*c_w)), therefore tau/m_w is fully determined
    without knowing the exact in-coil mass.
    """

    if water_flow_kg_s <= 0:
        raise ValueError("water_flow_kg_s must be positive")
    if medium_heat_capacity_j_per_kg_k <= 0:
        raise ValueError("medium_heat_capacity_j_per_kg_k must be positive")

    u = heat_transfer_coefficient_w_per_k(fan_speed, water_flow_kg_s)
    return 1.0 / (water_flow_kg_s + u / (2.0 * medium_heat_capacity_j_per_kg_k))


def cross_revision_sensitivity_mass_kg(
    *,
    density_kg_m3: float | None,
) -> SensitivityMass:
    """Convert the repeated 1.7 L catalogue value for sensitivity only."""

    if density_kg_m3 is None:
        return SensitivityMass(
            Q_DENSITY_REQUIRED,
            None,
            "Q",
            "A volume-to-mass sensitivity still requires explicit medium density.",
        )
    if density_kg_m3 <= 0:
        raise ValueError("density_kg_m3 must be positive")

    return SensitivityMass(
        ASS_CROSS_REVISION_SENSITIVITY,
        CROSS_REVISION_WATER_CONTENT_L / 1000.0 * density_kg_m3,
        "ASS",
        "Repeated 1.7 L across 2004 and 2006 Trane revisions; sensitivity only, not exact 2010 study mass.",
    )


def p58_boundaries() -> tuple[str, ...]:
    return (
        "PRC011_2004_1_7_L_AND_PRC014_2006_1_7_L != EXACT_PRC006_2010_CELL",
        "CROSS_REVISION_STABILITY != EXACT_STUDY_IDENTITY",
        "STEADY_STATE_FCC06_OUTPUT_IS_INDEPENDENT_OF_M_W_WITHIN_SOURCE_ODE",
        "FCC06_TAU_SCALES_LINEARLY_WITH_M_W",
        "ASS_SENSITIVITY_MASS != OBS_EXACT_STUDY_MASS",
        "EXACT_MASS_REMAINS_REQUIRED_FOR_OBS_TRANSIENT_VALIDATION",
    )
