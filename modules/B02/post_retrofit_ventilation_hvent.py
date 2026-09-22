"""B02-P87 bounded post-retrofit ventilation / infiltration H_vent surface.

P87 combines:
- current Hungarian calculation-method ventilation semantics;
- the P85 14-stratum heated-volume envelopes;
- the 2026 BME Type-5 empirical ventilation/infiltration calibration.

It does NOT promote the Type-5 empirical distribution to all Hungary.

Canonical boundaries:

REQUIRED_RESIDENTIAL_AIR_CHANGE != OBSERVED_POPULATION_AIR_CHANGE
TYPE5_EMPIRICAL_DISTRIBUTION != ALL_ARCHETYPE_POST_RETROFIT_DISTRIBUTION
AIRTIGHTNESS_METHOD_CLASS != POPULATION_PREVALENCE
NATURAL_VENTILATION_HVENT != HRV_HVENT
BOUNDING_HVENT_SCENARIO != HOUSEHOLD_DESIGN_LOAD
"""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
import csv
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
P85_SURFACE = ROOT / "data" / "processed" / "b02" / "p85_reference_retrofit_physical_input_surface.csv"

AIR_VOLUMETRIC_HEAT_CAPACITY_WH_M3K = 0.35
RESIDENTIAL_REQUIRED_AIR_CHANGE_H = 0.5

# Current Hungarian method, 2nd appendix table 2.4, across all listed
# airtightness / facade exposure / storey cases.
OFFICIAL_INFILTRATION_MIN_H = 0.0
OFFICIAL_INFILTRATION_MAX_H = 1.0

# Explicit optional current-method "good airtightness" scenario.
# The method gives 0.03 1/h for one facade and 0.06 1/h for multiple facades /
# ventilation shaft. P87 does not assume every reference retrofit reaches it.
GOOD_AIRTIGHTNESS_INFILTRATION_MIN_H = 0.03
GOOD_AIRTIGHTNESS_INFILTRATION_MAX_H = 0.06

# 2026 BME RBSM Type-5 detached-house calibration only.
BME_TYPE5_VENTILATION_MIN_H = 0.110
BME_TYPE5_VENTILATION_MAX_H = 0.860
BME_TYPE5_INFILTRATION_MEAN_H = 0.280
BME_TYPE5_INFILTRATION_STD_H = 0.100


@dataclass(frozen=True)
class VentilationHBound:
    wbl_period_code: str
    building_group: str
    heated_volume_lower_m3_per_dwelling: float
    heated_volume_upper_m3_per_dwelling: float
    required_air_change_h: float
    infiltration_lower_h: float
    infiltration_upper_h: float
    h_vent_lower_w_per_k: float
    h_vent_upper_w_per_k: float
    status: str
    evidence_status: str


def ventilation_h_w_per_k(
    *,
    volume_m3: float,
    required_air_change_h: float,
    infiltration_air_change_h: float,
    air_volumetric_heat_capacity_wh_m3k: float = AIR_VOLUMETRIC_HEAT_CAPACITY_WH_M3K,
) -> float:
    """Current-method natural-ventilation heat-transfer coefficient.

    For full-use residential operation:
        H_vent = 0.35 * (n_required + n_infiltration) * V

    P87 uses this only as a bounded physical-method scenario. Mechanical heat
    recovery requires its own explicit path.
    """

    values = (
        volume_m3,
        required_air_change_h,
        infiltration_air_change_h,
        air_volumetric_heat_capacity_wh_m3k,
    )
    if any(float(v) < 0 for v in values):
        raise ValueError("ventilation inputs must be nonnegative")
    return (
        float(air_volumetric_heat_capacity_wh_m3k)
        * (float(required_air_change_h) + float(infiltration_air_change_h))
        * float(volume_m3)
    )


def _load_p85_surface(path: Path = P85_SURFACE) -> tuple[dict[str, str], ...]:
    with path.open(encoding="utf-8", newline="") as handle:
        rows = tuple(csv.DictReader(handle))
    if len(rows) != 14:
        raise ValueError(f"expected 14 P85 strata, got {len(rows)}")
    return rows


@lru_cache(maxsize=None)
def current_method_ventilation_surface() -> tuple[VentilationHBound, ...]:
    """Return 14-stratum current-method natural-ventilation H_vent bounds.

    The lower/upper bound spans the full current-method infiltration table,
    because P85's reference-retrofit action does not yet bind an airtightness
    class or mechanical ventilation state.
    """

    out: list[VentilationHBound] = []
    for row in _load_p85_surface():
        v_lo = float(row["heated_volume_lower_m3_per_dwelling"])
        v_hi = float(row["heated_volume_upper_m3_per_dwelling"])
        if not (0 < v_lo <= v_hi):
            raise ValueError("invalid P85 heated-volume envelope")
        h_lo = ventilation_h_w_per_k(
            volume_m3=v_lo,
            required_air_change_h=RESIDENTIAL_REQUIRED_AIR_CHANGE_H,
            infiltration_air_change_h=OFFICIAL_INFILTRATION_MIN_H,
        )
        h_hi = ventilation_h_w_per_k(
            volume_m3=v_hi,
            required_air_change_h=RESIDENTIAL_REQUIRED_AIR_CHANGE_H,
            infiltration_air_change_h=OFFICIAL_INFILTRATION_MAX_H,
        )
        out.append(
            VentilationHBound(
                wbl_period_code=row["wbl_period_code"],
                building_group=row["building_group"],
                heated_volume_lower_m3_per_dwelling=v_lo,
                heated_volume_upper_m3_per_dwelling=v_hi,
                required_air_change_h=RESIDENTIAL_REQUIRED_AIR_CHANGE_H,
                infiltration_lower_h=OFFICIAL_INFILTRATION_MIN_H,
                infiltration_upper_h=OFFICIAL_INFILTRATION_MAX_H,
                h_vent_lower_w_per_k=h_lo,
                h_vent_upper_w_per_k=h_hi,
                status="BOUNDED_CURRENT_METHOD_NATURAL_VENTILATION_HVENT",
                evidence_status="POL/DER/SCN",
            )
        )
    return tuple(out)


@lru_cache(maxsize=None)
def good_airtightness_sensitivity_surface() -> tuple[VentilationHBound, ...]:
    """Optional good-airtightness sensitivity, not a population default."""

    out: list[VentilationHBound] = []
    for row in _load_p85_surface():
        v_lo = float(row["heated_volume_lower_m3_per_dwelling"])
        v_hi = float(row["heated_volume_upper_m3_per_dwelling"])
        out.append(
            VentilationHBound(
                wbl_period_code=row["wbl_period_code"],
                building_group=row["building_group"],
                heated_volume_lower_m3_per_dwelling=v_lo,
                heated_volume_upper_m3_per_dwelling=v_hi,
                required_air_change_h=RESIDENTIAL_REQUIRED_AIR_CHANGE_H,
                infiltration_lower_h=GOOD_AIRTIGHTNESS_INFILTRATION_MIN_H,
                infiltration_upper_h=GOOD_AIRTIGHTNESS_INFILTRATION_MAX_H,
                h_vent_lower_w_per_k=ventilation_h_w_per_k(
                    volume_m3=v_lo,
                    required_air_change_h=RESIDENTIAL_REQUIRED_AIR_CHANGE_H,
                    infiltration_air_change_h=GOOD_AIRTIGHTNESS_INFILTRATION_MIN_H,
                ),
                h_vent_upper_w_per_k=ventilation_h_w_per_k(
                    volume_m3=v_hi,
                    required_air_change_h=RESIDENTIAL_REQUIRED_AIR_CHANGE_H,
                    infiltration_air_change_h=GOOD_AIRTIGHTNESS_INFILTRATION_MAX_H,
                ),
                status="GOOD_AIRTIGHTNESS_SENSITIVITY_ONLY",
                evidence_status="POL/SCN",
            )
        )
    return tuple(out)


def type5_empirical_calibration() -> dict[str, float | str]:
    return {
        "ventilation_min_h": BME_TYPE5_VENTILATION_MIN_H,
        "ventilation_max_h": BME_TYPE5_VENTILATION_MAX_H,
        "infiltration_mean_h": BME_TYPE5_INFILTRATION_MEAN_H,
        "infiltration_std_h": BME_TYPE5_INFILTRATION_STD_H,
        "status": "TYPE5_EMPIRICAL_CALIBRATION_ONLY",
    }


def ventilation_state() -> dict[str, object]:
    return {
        "stratum_count": len(current_method_ventilation_surface()),
        "required_residential_air_change_h": RESIDENTIAL_REQUIRED_AIR_CHANGE_H,
        "official_infiltration_method_range_h": (
            OFFICIAL_INFILTRATION_MIN_H,
            OFFICIAL_INFILTRATION_MAX_H,
        ),
        "generic_post_retrofit_ventilation_blocker": (
            "PARTIAL_RESOLVED_CURRENT_METHOD_HVENT_SURFACE"
        ),
        "residuals": (
            "POST_RETROFIT_AIRTIGHTNESS_CLASS_PREVALENCE_REQUIRED",
            "POST_RETROFIT_MECHANICAL_VENTILATION_PREVALENCE_REQUIRED",
            "POST_RETROFIT_HEAT_RECOVERY_EFFICIENCY_DISTRIBUTION_REQUIRED",
            "ACTION_TO_AIRTIGHTNESS_AND_VENTILATION_SYSTEM_MAPPING_REQUIRED",
        ),
    }


def semantic_boundaries() -> tuple[str, ...]:
    return (
        "REQUIRED_RESIDENTIAL_AIR_CHANGE_IS_NOT_OBSERVED_POPULATION_AIR_CHANGE",
        "TYPE5_EMPIRICAL_DISTRIBUTION_CANNOT_BE_PROMOTED_TO_ALL_ARCHETYPES",
        "GOOD_AIRTIGHTNESS_SCENARIO_IS_NOT_REFERENCE_RETROFIT_DEFAULT",
        "CURRENT_METHOD_HVENT_ENVELOPE_IS_NOT_POPULATION_PROBABILITY_INTERVAL",
        "HRV_REQUIRES_EXPLICIT_AIRFLOW_RECOVERY_AND_PREVALENCE_AUTHORITY",
    )
