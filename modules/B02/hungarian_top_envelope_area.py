"""B02-P93 Hungarian top-envelope area calibration.

P85 left ACTUAL_TOP_HEAT_LOSS_PLANE_AREA_INFERENCE_REQUIRED because its mean
storey floorplate and bbox plan quantities are not source-native thermal-envelope
areas.

P93 uses the TABULA/EPISCOPE Hungarian thermal-envelope ratio A_Roof/A_C_Ref,
where:

    A_Roof = A_Roof_1 + A_Roof_2

and A_C_Ref is conditioned floor area.

Published Hungarian class-average ratios:
- SFH: 0.84 m2/m2
- MFH: 0.35 m2/m2
- AB:  0.20 m2/m2

These ratios are averaged over construction-year classes and are admitted only
as reference-programme synthetic-average calibration values.

Critical boundaries:

A_ROOF_IS_THERMAL_ENVELOPE_TOP_AREA
A_ROOF_MAY_BE_ROOF_OR_UPPER_CEILING_DEPENDING_ATTIC_STATE
HU_CLASS_AVERAGE_RATIO != HOUSEHOLD_RATIO
HU_CLASS_AVERAGE_RATIO != AGE_SPECIFIC_RATIO
TOP_AREA_CALIBRATION != PITCHED_ROOF_U_RESOLUTION
TOP_AREA_CALIBRATION != BBOX_PLAN_AREA
REFERENCE_PROGRAMME_PROXY != REALIZED_PROJECT_GEOMETRY
"""

from __future__ import annotations

from dataclasses import dataclass
import csv
from functools import lru_cache
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
P85_SURFACE = (
    ROOT / "data" / "processed" / "b02"
    / "p85_reference_retrofit_physical_input_surface.csv"
)

FAMILY_HOUSE = "FAMILY_HOUSE"
MULTI_DWELLING = "MULTI_DWELLING"

TABULA_HU_SFH_TOP_TO_CONDITIONED_FLOOR_RATIO = 0.84
TABULA_HU_MFH_TOP_TO_CONDITIONED_FLOOR_RATIO = 0.35
TABULA_HU_AB_TOP_TO_CONDITIONED_FLOOR_RATIO = 0.20

QUALIFIED_HUNGARIAN_TOP_ENVELOPE_AREA_PROXY = (
    "QUALIFIED_HUNGARIAN_TOP_ENVELOPE_AREA_PROXY"
)
REALIZED_TOP_ENVELOPE_GEOMETRY_VERIFICATION_REQUIRED = (
    "REALIZED_TOP_ENVELOPE_GEOMETRY_VERIFICATION_REQUIRED"
)


@dataclass(frozen=True)
class TopAreaRatioBound:
    building_group: str
    lower: float
    upper: float
    source_classes: tuple[str, ...]
    status: str
    evidence_status: str


@dataclass(frozen=True)
class TopEnvelopeAreaBound:
    heated_floor_area_lower_m2: float
    heated_floor_area_upper_m2: float
    ratio_lower: float
    ratio_upper: float
    top_area_lower_m2: float
    top_area_upper_m2: float
    status: str
    evidence_status: str


@dataclass(frozen=True)
class StratumTopEnvelopeArea:
    surface_id: str
    wbl_period_code: str
    building_group: str
    candidate_type_ids: str
    heated_floor_area_lower_m2_per_dwelling: float
    heated_floor_area_upper_m2_per_dwelling: float
    top_to_conditioned_floor_ratio_lower: float
    top_to_conditioned_floor_ratio_upper: float
    top_envelope_area_lower_m2_per_dwelling: float
    top_envelope_area_upper_m2_per_dwelling: float
    status: str
    evidence_status: str


def top_area_ratio_bound(building_group: str) -> TopAreaRatioBound:
    if building_group == FAMILY_HOUSE:
        return TopAreaRatioBound(
            building_group=building_group,
            lower=TABULA_HU_SFH_TOP_TO_CONDITIONED_FLOOR_RATIO,
            upper=TABULA_HU_SFH_TOP_TO_CONDITIONED_FLOOR_RATIO,
            source_classes=("HU_SFH",),
            status=QUALIFIED_HUNGARIAN_TOP_ENVELOPE_AREA_PROXY,
            evidence_status="DER/SCN_PROXY",
        )
    if building_group == MULTI_DWELLING:
        values = (
            TABULA_HU_MFH_TOP_TO_CONDITIONED_FLOOR_RATIO,
            TABULA_HU_AB_TOP_TO_CONDITIONED_FLOOR_RATIO,
        )
        return TopAreaRatioBound(
            building_group=building_group,
            lower=min(values),
            upper=max(values),
            source_classes=("HU_MFH", "HU_AB"),
            status=QUALIFIED_HUNGARIAN_TOP_ENVELOPE_AREA_PROXY,
            evidence_status="DER/SCN_PROXY",
        )
    raise ValueError(f"unsupported building group: {building_group}")


def top_envelope_area_bound(
    *,
    heated_floor_area_lower_m2: float,
    heated_floor_area_upper_m2: float,
    building_group: str,
) -> TopEnvelopeAreaBound:
    floor_lo = float(heated_floor_area_lower_m2)
    floor_hi = float(heated_floor_area_upper_m2)
    if floor_lo <= 0 or floor_hi <= 0 or floor_lo > floor_hi:
        raise ValueError("invalid heated-floor-area interval")

    ratio = top_area_ratio_bound(building_group)

    # Positive interval multiplication.
    top_lo = floor_lo * ratio.lower
    top_hi = floor_hi * ratio.upper

    return TopEnvelopeAreaBound(
        heated_floor_area_lower_m2=floor_lo,
        heated_floor_area_upper_m2=floor_hi,
        ratio_lower=ratio.lower,
        ratio_upper=ratio.upper,
        top_area_lower_m2=top_lo,
        top_area_upper_m2=top_hi,
        status=QUALIFIED_HUNGARIAN_TOP_ENVELOPE_AREA_PROXY,
        evidence_status="DER/SCN_PROXY",
    )


@lru_cache(maxsize=None)
def reference_programme_top_envelope_surface() -> tuple[
    StratumTopEnvelopeArea, ...
]:
    with P85_SURFACE.open(encoding="utf-8", newline="") as handle:
        rows = tuple(csv.DictReader(handle))
    if len(rows) != 14:
        raise ValueError(f"expected 14 P85 strata, got {len(rows)}")

    out: list[StratumTopEnvelopeArea] = []
    for index, row in enumerate(rows, start=1):
        bound = top_envelope_area_bound(
            heated_floor_area_lower_m2=float(
                row["heated_floor_area_lower_m2_per_dwelling"]
            ),
            heated_floor_area_upper_m2=float(
                row["heated_floor_area_upper_m2_per_dwelling"]
            ),
            building_group=row["building_group"],
        )
        out.append(
            StratumTopEnvelopeArea(
                surface_id=f"B02-P93-T{index:02d}",
                wbl_period_code=row["wbl_period_code"],
                building_group=row["building_group"],
                candidate_type_ids=row["candidate_type_ids"],
                heated_floor_area_lower_m2_per_dwelling=(
                    bound.heated_floor_area_lower_m2
                ),
                heated_floor_area_upper_m2_per_dwelling=(
                    bound.heated_floor_area_upper_m2
                ),
                top_to_conditioned_floor_ratio_lower=bound.ratio_lower,
                top_to_conditioned_floor_ratio_upper=bound.ratio_upper,
                top_envelope_area_lower_m2_per_dwelling=bound.top_area_lower_m2,
                top_envelope_area_upper_m2_per_dwelling=bound.top_area_upper_m2,
                status=bound.status,
                evidence_status=bound.evidence_status,
            )
        )
    return tuple(out)


def p93_state() -> dict[str, object]:
    rows = reference_programme_top_envelope_surface()
    return {
        "hungarian_sfh_top_ratio": (
            TABULA_HU_SFH_TOP_TO_CONDITIONED_FLOOR_RATIO
        ),
        "hungarian_mfh_top_ratio": (
            TABULA_HU_MFH_TOP_TO_CONDITIONED_FLOOR_RATIO
        ),
        "hungarian_ab_top_ratio": (
            TABULA_HU_AB_TOP_TO_CONDITIONED_FLOOR_RATIO
        ),
        "stratum_count": len(rows),
        "top_area_global_lower_m2_per_dwelling": min(
            row.top_envelope_area_lower_m2_per_dwelling for row in rows
        ),
        "top_area_global_upper_m2_per_dwelling": max(
            row.top_envelope_area_upper_m2_per_dwelling for row in rows
        ),
        "status": QUALIFIED_HUNGARIAN_TOP_ENVELOPE_AREA_PROXY,
        "split_blocker": None,
        "remaining_geometry_residuals": (
            "ACTUAL_BOTTOM_HEAT_LOSS_PLANE_AREA_INFERENCE_REQUIRED",
            "BBOX_RECTANGULARIZATION_VALIDATION_REQUIRED",
            "PITCHED_ROOF_POSTSTATE_U_BOUND_REQUIRED",
        ),
        "realized_claim_residual": (
            REALIZED_TOP_ENVELOPE_GEOMETRY_VERIFICATION_REQUIRED
        ),
    }


def semantic_boundaries() -> tuple[str, ...]:
    return (
        "A_ROOF_IS_THERMAL_ENVELOPE_TOP_AREA",
        "A_ROOF_MAY_BE_ROOF_OR_UPPER_CEILING_DEPENDING_ATTIC_STATE",
        "HU_CLASS_AVERAGE_RATIO_IS_NOT_HOUSEHOLD_RATIO",
        "HU_CLASS_AVERAGE_RATIO_IS_NOT_AGE_SPECIFIC_RATIO",
        "TOP_AREA_CALIBRATION_IS_NOT_PITCHED_ROOF_U_RESOLUTION",
        "TOP_AREA_CALIBRATION_IS_NOT_BBOX_PLAN_AREA",
        "REFERENCE_PROGRAMME_PROXY_IS_NOT_REALIZED_PROJECT_GEOMETRY",
    )
