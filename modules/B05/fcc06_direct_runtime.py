"""B05-P57 exact FCC06 direct state-dependent runtime path.

P57 resolves the P56 mapping-or-direct-runtime fork by implementing the
published FCC06 water-side ODE directly.  The direct physical path does not
map the state-dependent response to a HEM/EN15316 scalar tau_out.

The numeric runtime remains fail-closed until exact study-compatible water
mass is supplied.  A cross-revision Trane guide exposes 1.7 L for size-06
2-pipe/3-row water content, but P57 does not promote that value to the exact
2010 study-unit mass without cited-edition binding and explicit density.
"""
from __future__ import annotations

from dataclasses import dataclass
from math import exp

from modules.B05.fcu_state_dependent_response import (
    SOURCE_ID as FCC06_DYNAMIC_SOURCE_ID,
    heat_transfer_coefficient_w_per_k,
)

SOURCE_MEAN_MEDIUM_HEAT_CAPACITY_J_PER_KG_K = 4504.0
CROSS_REVISION_FCC06_2PIPE_3ROW_WATER_CONTENT_L = 1.7

DIRECT_RUNTIME_QUALIFIED = "QUALIFIED_FCC06_DIRECT_STATE_DEPENDENT_RUNTIME"
Q_EXACT_WATER_MASS_REQUIRED = "Q / EXACT_STUDY_COMPATIBLE_FCC06_WATER_MASS_REQUIRED"
Q_EXPLICIT_DENSITY_REQUIRED = "Q / EXPLICIT_MEDIUM_DENSITY_REQUIRED"
CROSS_REVISION_VOLUME_NOT_EXACT_MASS = "CROSS_REVISION_VOLUME_CANDIDATE_NOT_EXACT_STUDY_MASS"


@dataclass(frozen=True)
class WaterMassResolution:
    status: str
    water_mass_kg: float | None
    reason: str


@dataclass(frozen=True)
class FCC06RuntimeStep:
    status: str
    outlet_temperature_c: float | None
    thermal_power_w: float | None
    state_time_constant_s: float | None
    residual_gap: str | None


def mass_from_volume_l(
    *,
    volume_l: float,
    density_kg_m3: float | None,
    exact_study_volume_binding: bool,
) -> WaterMassResolution:
    """Convert source volume to mass only with explicit density and exact binding."""

    if volume_l <= 0:
        raise ValueError("volume_l must be positive")
    if not exact_study_volume_binding:
        return WaterMassResolution(
            CROSS_REVISION_VOLUME_NOT_EXACT_MASS,
            None,
            "A cross-revision FCC06 water-content value is not the exact 2010 study-unit mass.",
        )
    if density_kg_m3 is None:
        return WaterMassResolution(
            Q_EXPLICIT_DENSITY_REQUIRED,
            None,
            "Volume-to-mass conversion requires explicit working-medium density.",
        )
    if density_kg_m3 <= 0:
        raise ValueError("density_kg_m3 must be positive")
    return WaterMassResolution(
        "DER / EXACT_BOUND_VOLUME_TO_MASS",
        volume_l / 1000.0 * density_kg_m3,
        "Mass derived from exact-bound coil volume and explicit medium density.",
    )


def direct_runtime_step(
    *,
    previous_outlet_temperature_c: float,
    inlet_temperature_c: float,
    zone_air_temperature_c: float,
    fan_speed: str,
    water_flow_kg_s: float,
    water_mass_kg: float | None,
    medium_heat_capacity_j_per_kg_k: float,
    timestep_s: float,
) -> FCC06RuntimeStep:
    """Exact constant-input step of the published first-order FCC06 water ODE.

    Published model:
        mw*cw*dTout/dt =
            qw*cw*(Tin-Tout) - Uo*(0.5*(Tin+Tout)-Ta)

    This function analytically integrates one constant-input timestep.
    """

    if water_mass_kg is None:
        return FCC06RuntimeStep(
            Q_EXACT_WATER_MASS_REQUIRED,
            None,
            None,
            None,
            "EXACT_STUDY_COMPATIBLE_FCC06_WATER_MASS_REQUIRED",
        )
    if water_mass_kg <= 0:
        raise ValueError("water_mass_kg must be positive")
    if water_flow_kg_s <= 0:
        raise ValueError("water_flow_kg_s must be positive")
    if medium_heat_capacity_j_per_kg_k <= 0:
        raise ValueError("medium_heat_capacity_j_per_kg_k must be positive")
    if timestep_s <= 0:
        raise ValueError("timestep_s must be positive")

    u = heat_transfer_coefficient_w_per_k(fan_speed, water_flow_kg_s)

    a_per_s = (
        water_flow_kg_s / water_mass_kg
        + u / (2.0 * water_mass_kg * medium_heat_capacity_j_per_kg_k)
    )
    b_c_per_s = (
        (water_flow_kg_s / water_mass_kg
         - u / (2.0 * water_mass_kg * medium_heat_capacity_j_per_kg_k))
        * inlet_temperature_c
        + u / (water_mass_kg * medium_heat_capacity_j_per_kg_k)
        * zone_air_temperature_c
    )

    steady_outlet_c = b_c_per_s / a_per_s
    outlet_c = steady_outlet_c + (
        previous_outlet_temperature_c - steady_outlet_c
    ) * exp(-a_per_s * timestep_s)

    mean_water_c = 0.5 * (inlet_temperature_c + outlet_c)
    transmitted_power_w = u * (mean_water_c - zone_air_temperature_c)

    return FCC06RuntimeStep(
        DIRECT_RUNTIME_QUALIFIED,
        outlet_c,
        transmitted_power_w,
        1.0 / a_per_s,
        None,
    )


def p57_boundaries() -> tuple[str, ...]:
    return (
        "FCC06_DIRECT_PHYSICAL_RUNTIME != HEM_TAU_OUT_MAPPING",
        "CROSS_REVISION_1_7_L != EXACT_2010_STUDY_WATER_MASS",
        "WATER_CONTENT_VOLUME != WATER_MASS_WITHOUT_DENSITY",
        "SOURCE_MEAN_CW_4504 != UNIVERSAL_WATER_HEAT_CAPACITY",
        "DIRECT_RUNTIME_PATH_RESOLVES_MAPPING_FORK_BUT_NOT_MASS_AUTHORITY",
        "NO_MECHANICAL_READINESS_UPLIFT",
    )
