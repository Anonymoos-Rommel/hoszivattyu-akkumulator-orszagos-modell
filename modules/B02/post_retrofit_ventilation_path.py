"""B02-P88 post-retrofit ventilation path and HRV response contract.

P87 materialized a bounded 14-stratum natural-ventilation H_vent surface from
current Hungarian calculation-method semantics. P88 separates the physical
response into the two terms that matter for a controlled retrofit state:

    H_required_air = c_air * n_required * V
    H_infiltration = c_air * n_infiltration * V

For heat-recovery ventilation, the recoverable required-air term is reduced by
the explicit project/procurement heat-recovery efficiency eta:

    H_vent,HRV = H_infiltration + (1 - eta) * H_required_air

This follows the current Hungarian EKR heat-recovery accounting structure,
which applies eta to the required ventilation flow. Infiltration is not silently
credited with heat recovery.

Critical evidence boundaries:

POST_RETROFIT VENTILATION PATH != OBSERVED NATIONAL PREVALENCE
HRV EFFICIENCY != NATIONAL POPULATION DISTRIBUTION
PRODUCT-DECLARED ETA != INSTALLED/COMMISSIONED PERFORMANCE
WINDOW/ENVELOPE ACTION != PROVEN POST-RETROFIT INFILTRATION
MECHANICAL EXHAUST != HEAT RECOVERY
VENTILATION THERMAL LOAD != FAN ELECTRICITY

The path is a programme/project state. National path shares may be scenario
inputs and must never be relabelled as observed prevalence. Infiltration remains
fail-closed until action-conditioned inference, a target, or project evidence
is supplied.
"""

from __future__ import annotations

from dataclasses import dataclass
import csv
from functools import lru_cache
from pathlib import Path

from modules.B02.post_retrofit_ventilation_hvent import (
    AIR_VOLUMETRIC_HEAT_CAPACITY_WH_M3K,
    RESIDENTIAL_REQUIRED_AIR_CHANGE_H,
)


ROOT = Path(__file__).resolve().parents[2]
P87_SURFACE = ROOT / "data" / "processed" / "b02" / "p87_post_retrofit_ventilation_hvent_surface.csv"

NATURAL_WINDOW = "NATURAL_WINDOW"
MECHANICAL_EXHAUST_WITH_AIR_INLETS = "MECHANICAL_EXHAUST_WITH_AIR_INLETS"
MECHANICAL_HEAT_RECOVERY = "MECHANICAL_HEAT_RECOVERY"

ALLOWED_POST_RETROFIT_VENTILATION_PATHS = (
    NATURAL_WINDOW,
    MECHANICAL_EXHAUST_WITH_AIR_INLETS,
    MECHANICAL_HEAT_RECOVERY,
)


@dataclass(frozen=True)
class VentilationResponseCoefficient:
    wbl_period_code: str
    building_group: str
    heated_volume_lower_m3_per_dwelling: float
    heated_volume_upper_m3_per_dwelling: float
    required_air_h_lower_w_per_k: float
    required_air_h_upper_w_per_k: float
    full_eta_recoverable_h_lower_w_per_k: float
    full_eta_recoverable_h_upper_w_per_k: float
    infiltration_h_upper_w_per_k: float
    status: str
    evidence_status: str


@dataclass(frozen=True)
class VentilationPathResult:
    path: str
    volume_m3: float
    infiltration_air_change_h: float
    heat_recovery_efficiency: float | None
    required_air_h_w_per_k: float
    infiltration_h_w_per_k: float
    recovered_h_w_per_k: float
    h_vent_w_per_k: float
    status: str


def _require_nonnegative(name: str, value: float) -> float:
    value = float(value)
    if value < 0:
        raise ValueError(f"{name} must be nonnegative")
    return value


def required_air_h_w_per_k(*, volume_m3: float) -> float:
    volume = _require_nonnegative("volume_m3", volume_m3)
    return (
        AIR_VOLUMETRIC_HEAT_CAPACITY_WH_M3K
        * RESIDENTIAL_REQUIRED_AIR_CHANGE_H
        * volume
    )


def infiltration_h_w_per_k(
    *,
    volume_m3: float,
    infiltration_air_change_h: float,
) -> float:
    volume = _require_nonnegative("volume_m3", volume_m3)
    infiltration = _require_nonnegative(
        "infiltration_air_change_h",
        infiltration_air_change_h,
    )
    return AIR_VOLUMETRIC_HEAT_CAPACITY_WH_M3K * infiltration * volume


def hrv_recovered_h_w_per_k(
    *,
    volume_m3: float,
    heat_recovery_efficiency: float,
) -> float:
    eta = float(heat_recovery_efficiency)
    if not 0.0 <= eta <= 1.0:
        raise ValueError("heat_recovery_efficiency must be within [0, 1]")
    return required_air_h_w_per_k(volume_m3=volume_m3) * eta


def ventilation_path_h_w_per_k(
    *,
    path: str,
    volume_m3: float,
    infiltration_air_change_h: float,
    heat_recovery_efficiency: float | None = None,
) -> VentilationPathResult:
    if path not in ALLOWED_POST_RETROFIT_VENTILATION_PATHS:
        raise ValueError(f"unsupported ventilation path: {path}")

    h_required = required_air_h_w_per_k(volume_m3=volume_m3)
    h_infiltration = infiltration_h_w_per_k(
        volume_m3=volume_m3,
        infiltration_air_change_h=infiltration_air_change_h,
    )

    if path == MECHANICAL_HEAT_RECOVERY:
        if heat_recovery_efficiency is None:
            raise ValueError(
                "heat_recovery_efficiency is required for MECHANICAL_HEAT_RECOVERY"
            )
        recovered = hrv_recovered_h_w_per_k(
            volume_m3=volume_m3,
            heat_recovery_efficiency=heat_recovery_efficiency,
        )
        eta = float(heat_recovery_efficiency)
        status = "PROJECT_ETA_BOUND_HRV_RESPONSE"
    else:
        if heat_recovery_efficiency is not None:
            raise ValueError(
                "heat_recovery_efficiency is only valid for MECHANICAL_HEAT_RECOVERY"
            )
        recovered = 0.0
        eta = None
        status = "NO_HEAT_RECOVERY_RESPONSE"

    return VentilationPathResult(
        path=path,
        volume_m3=float(volume_m3),
        infiltration_air_change_h=float(infiltration_air_change_h),
        heat_recovery_efficiency=eta,
        required_air_h_w_per_k=h_required,
        infiltration_h_w_per_k=h_infiltration,
        recovered_h_w_per_k=recovered,
        h_vent_w_per_k=h_required + h_infiltration - recovered,
        status=status,
    )


def ventilation_design_load_kw(
    *,
    h_vent_w_per_k: float,
    indoor_temperature_c: float,
    outdoor_temperature_c: float,
) -> float:
    delta_t = float(indoor_temperature_c) - float(outdoor_temperature_c)
    if delta_t < 0:
        raise ValueError("indoor_temperature_c must not be below outdoor_temperature_c")
    return float(h_vent_w_per_k) * delta_t / 1000.0


@lru_cache(maxsize=None)
def fourteen_stratum_response_coefficients() -> tuple[VentilationResponseCoefficient, ...]:
    with P87_SURFACE.open(encoding="utf-8", newline="") as handle:
        rows = tuple(csv.DictReader(handle))
    if len(rows) != 14:
        raise ValueError(f"expected 14 P87 strata, got {len(rows)}")

    out: list[VentilationResponseCoefficient] = []
    for row in rows:
        v_lo = float(row["heated_volume_lower_m3_per_dwelling"])
        v_hi = float(row["heated_volume_upper_m3_per_dwelling"])
        required_lo = required_air_h_w_per_k(volume_m3=v_lo)
        required_hi = required_air_h_w_per_k(volume_m3=v_hi)
        infiltration_hi = infiltration_h_w_per_k(
            volume_m3=v_hi,
            infiltration_air_change_h=float(row["official_infiltration_upper_h"]),
        )
        out.append(
            VentilationResponseCoefficient(
                wbl_period_code=row["wbl_period_code"],
                building_group=row["building_group"],
                heated_volume_lower_m3_per_dwelling=v_lo,
                heated_volume_upper_m3_per_dwelling=v_hi,
                required_air_h_lower_w_per_k=required_lo,
                required_air_h_upper_w_per_k=required_hi,
                full_eta_recoverable_h_lower_w_per_k=required_lo,
                full_eta_recoverable_h_upper_w_per_k=required_hi,
                infiltration_h_upper_w_per_k=infiltration_hi,
                status="MATERIALIZED_HRV_RESPONSE_COEFFICIENT",
                evidence_status="POL/DER",
            )
        )
    return tuple(out)


def response_envelope_state() -> dict[str, object]:
    rows = fourteen_stratum_response_coefficients()
    return {
        "stratum_count": len(rows),
        "allowed_paths": ALLOWED_POST_RETROFIT_VENTILATION_PATHS,
        "required_air_h_global_lower_w_per_k": min(
            row.required_air_h_lower_w_per_k for row in rows
        ),
        "required_air_h_global_upper_w_per_k": max(
            row.required_air_h_upper_w_per_k for row in rows
        ),
        "full_eta_recoverable_h_global_lower_w_per_k": min(
            row.full_eta_recoverable_h_lower_w_per_k for row in rows
        ),
        "full_eta_recoverable_h_global_upper_w_per_k": max(
            row.full_eta_recoverable_h_upper_w_per_k for row in rows
        ),
        "infiltration_h_global_upper_w_per_k": max(
            row.infiltration_h_upper_w_per_k for row in rows
        ),
        "population_prevalence_required_for_response_engine": False,
        "heat_recovery_efficiency_population_distribution_required": False,
        "hrv_eta_requirement": "EXPLICIT_PROJECT_OR_PROCUREMENT_EVIDENCE",
        "remaining_physical_residual": (
            "ACTION_CONDITIONED_POST_RETROFIT_INFILTRATION_REQUIRED"
        ),
    }


def semantic_boundaries() -> tuple[str, ...]:
    return (
        "POST_RETROFIT_VENTILATION_PATH_IS_PROGRAMME_OR_PROJECT_STATE_NOT_OBSERVED_PREVALENCE",
        "HRV_ETA_IS_PROJECT_OR_PROCUREMENT_EVIDENCE_NOT_POPULATION_DISTRIBUTION",
        "PRODUCT_DECLARED_ETA_IS_NOT_INSTALLED_COMMISSIONED_PERFORMANCE",
        "WINDOW_OR_ENVELOPE_ACTION_DOES_NOT_PROVE_POST_RETROFIT_INFILTRATION",
        "MECHANICAL_EXHAUST_DOES_NOT_IMPLY_HEAT_RECOVERY",
        "INFILTRATION_BYPASSES_HRV_UNLESS_SEPARATELY_PROVEN",
        "VENTILATION_THERMAL_LOAD_EXCLUDES_FAN_ELECTRICITY",
    )
