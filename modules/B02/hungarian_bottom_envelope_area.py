"""B02-P94 Hungarian bottom-envelope area calibration.

P85 left ACTUAL_BOTTOM_HEAT_LOSS_PLANE_AREA_INFERENCE_REQUIRED unresolved.

P94 uses the Hungarian TABULA/EPISCOPE class-average thermal-envelope ratio
A_Floor/A_C_Ref, where A_Floor=A_Floor_1+A_Floor_2.

Published Hungarian class-average ratios:
- SFH: 0.80 m2/m2
- MFH: 0.33 m2/m2
- AB:  0.20 m2/m2

These are admitted only as reference-programme synthetic-average calibration
values. A_Floor is treated as BOTTOM_ENVELOPE_AREA; P94 does not infer whether
a given project boundary is ground floor, cellar ceiling or another floor
boundary type.

Critical boundaries:

A_FLOOR_IS_THERMAL_ENVELOPE_BOTTOM_AREA
BOTTOM_AREA != GROUND_FLOOR_ONLY
BOTTOM_AREA != BASEMENT_CEILING_ONLY
HU_CLASS_AVERAGE_RATIO != HOUSEHOLD_RATIO
HU_CLASS_AVERAGE_RATIO != AGE_SPECIFIC_RATIO
BOTTOM_AREA_CALIBRATION != BOUNDARY_TYPE_OR_U_RESOLUTION
REFERENCE_PROGRAMME_PROXY != REALIZED_PROJECT_GEOMETRY
"""

from __future__ import annotations

from dataclasses import dataclass
import csv
from functools import lru_cache
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
P85_SURFACE = ROOT / "data" / "processed" / "b02" / "p85_reference_retrofit_physical_input_surface.csv"

FAMILY_HOUSE = "FAMILY_HOUSE"
MULTI_DWELLING = "MULTI_DWELLING"

TABULA_HU_SFH_BOTTOM_TO_CONDITIONED_FLOOR_RATIO = 0.80
TABULA_HU_MFH_BOTTOM_TO_CONDITIONED_FLOOR_RATIO = 0.33
TABULA_HU_AB_BOTTOM_TO_CONDITIONED_FLOOR_RATIO = 0.20

QUALIFIED_HUNGARIAN_BOTTOM_ENVELOPE_AREA_PROXY = (
    "QUALIFIED_HUNGARIAN_BOTTOM_ENVELOPE_AREA_PROXY"
)
REALIZED_BOTTOM_ENVELOPE_GEOMETRY_VERIFICATION_REQUIRED = (
    "REALIZED_BOTTOM_ENVELOPE_GEOMETRY_VERIFICATION_REQUIRED"
)


@dataclass(frozen=True)
class BottomAreaRatioBound:
    building_group: str
    lower: float
    upper: float
    source_classes: tuple[str, ...]
    status: str
    evidence_status: str


@dataclass(frozen=True)
class BottomEnvelopeAreaBound:
    heated_floor_area_lower_m2: float
    heated_floor_area_upper_m2: float
    ratio_lower: float
    ratio_upper: float
    bottom_area_lower_m2: float
    bottom_area_upper_m2: float
    status: str
    evidence_status: str


@dataclass(frozen=True)
class StratumBottomEnvelopeArea:
    surface_id: str
    wbl_period_code: str
    building_group: str
    candidate_type_ids: str
    heated_floor_area_lower_m2_per_dwelling: float
    heated_floor_area_upper_m2_per_dwelling: float
    bottom_to_conditioned_floor_ratio_lower: float
    bottom_to_conditioned_floor_ratio_upper: float
    bottom_envelope_area_lower_m2_per_dwelling: float
    bottom_envelope_area_upper_m2_per_dwelling: float
    status: str
    evidence_status: str


def bottom_area_ratio_bound(building_group: str) -> BottomAreaRatioBound:
    if building_group == FAMILY_HOUSE:
        return BottomAreaRatioBound(
            building_group=building_group,
            lower=TABULA_HU_SFH_BOTTOM_TO_CONDITIONED_FLOOR_RATIO,
            upper=TABULA_HU_SFH_BOTTOM_TO_CONDITIONED_FLOOR_RATIO,
            source_classes=("HU_SFH",),
            status=QUALIFIED_HUNGARIAN_BOTTOM_ENVELOPE_AREA_PROXY,
            evidence_status="DER/SCN_PROXY",
        )
    if building_group == MULTI_DWELLING:
        vals=(TABULA_HU_MFH_BOTTOM_TO_CONDITIONED_FLOOR_RATIO,
              TABULA_HU_AB_BOTTOM_TO_CONDITIONED_FLOOR_RATIO)
        return BottomAreaRatioBound(
            building_group=building_group,
            lower=min(vals),
            upper=max(vals),
            source_classes=("HU_MFH","HU_AB"),
            status=QUALIFIED_HUNGARIAN_BOTTOM_ENVELOPE_AREA_PROXY,
            evidence_status="DER/SCN_PROXY",
        )
    raise ValueError(f"unsupported building group: {building_group}")


def bottom_envelope_area_bound(*, heated_floor_area_lower_m2: float,
                               heated_floor_area_upper_m2: float,
                               building_group: str) -> BottomEnvelopeAreaBound:
    lo=float(heated_floor_area_lower_m2)
    hi=float(heated_floor_area_upper_m2)
    if lo <= 0 or hi <= 0 or lo > hi:
        raise ValueError("invalid heated-floor-area interval")
    ratio=bottom_area_ratio_bound(building_group)
    return BottomEnvelopeAreaBound(
        heated_floor_area_lower_m2=lo,
        heated_floor_area_upper_m2=hi,
        ratio_lower=ratio.lower,
        ratio_upper=ratio.upper,
        bottom_area_lower_m2=lo*ratio.lower,
        bottom_area_upper_m2=hi*ratio.upper,
        status=QUALIFIED_HUNGARIAN_BOTTOM_ENVELOPE_AREA_PROXY,
        evidence_status="DER/SCN_PROXY",
    )


@lru_cache(maxsize=None)
def reference_programme_bottom_envelope_surface() -> tuple[StratumBottomEnvelopeArea,...]:
    with P85_SURFACE.open(encoding="utf-8",newline="") as handle:
        rows=tuple(csv.DictReader(handle))
    if len(rows) != 14:
        raise ValueError(f"expected 14 P85 strata, got {len(rows)}")
    out=[]
    for index,row in enumerate(rows,start=1):
        b=bottom_envelope_area_bound(
            heated_floor_area_lower_m2=float(row["heated_floor_area_lower_m2_per_dwelling"]),
            heated_floor_area_upper_m2=float(row["heated_floor_area_upper_m2_per_dwelling"]),
            building_group=row["building_group"],
        )
        out.append(StratumBottomEnvelopeArea(
            surface_id=f"B02-P94-B{index:02d}",
            wbl_period_code=row["wbl_period_code"],
            building_group=row["building_group"],
            candidate_type_ids=row["candidate_type_ids"],
            heated_floor_area_lower_m2_per_dwelling=b.heated_floor_area_lower_m2,
            heated_floor_area_upper_m2_per_dwelling=b.heated_floor_area_upper_m2,
            bottom_to_conditioned_floor_ratio_lower=b.ratio_lower,
            bottom_to_conditioned_floor_ratio_upper=b.ratio_upper,
            bottom_envelope_area_lower_m2_per_dwelling=b.bottom_area_lower_m2,
            bottom_envelope_area_upper_m2_per_dwelling=b.bottom_area_upper_m2,
            status=b.status,
            evidence_status=b.evidence_status,
        ))
    return tuple(out)


def p94_state() -> dict[str,object]:
    rows=reference_programme_bottom_envelope_surface()
    return {
        "hungarian_sfh_bottom_ratio": TABULA_HU_SFH_BOTTOM_TO_CONDITIONED_FLOOR_RATIO,
        "hungarian_mfh_bottom_ratio": TABULA_HU_MFH_BOTTOM_TO_CONDITIONED_FLOOR_RATIO,
        "hungarian_ab_bottom_ratio": TABULA_HU_AB_BOTTOM_TO_CONDITIONED_FLOOR_RATIO,
        "stratum_count": len(rows),
        "bottom_area_global_lower_m2_per_dwelling": min(r.bottom_envelope_area_lower_m2_per_dwelling for r in rows),
        "bottom_area_global_upper_m2_per_dwelling": max(r.bottom_envelope_area_upper_m2_per_dwelling for r in rows),
        "status": QUALIFIED_HUNGARIAN_BOTTOM_ENVELOPE_AREA_PROXY,
        "bottom_area_blocker": None,
        "remaining_geometry_residuals": (
            "BBOX_RECTANGULARIZATION_VALIDATION_REQUIRED",
            "PITCHED_ROOF_POSTSTATE_U_BOUND_REQUIRED",
        ),
        "realized_claim_residual": REALIZED_BOTTOM_ENVELOPE_GEOMETRY_VERIFICATION_REQUIRED,
    }


def semantic_boundaries() -> tuple[str,...]:
    return (
        "A_FLOOR_IS_THERMAL_ENVELOPE_BOTTOM_AREA",
        "BOTTOM_AREA_IS_NOT_GROUND_FLOOR_ONLY",
        "BOTTOM_AREA_IS_NOT_BASEMENT_CEILING_ONLY",
        "HU_CLASS_AVERAGE_RATIO_IS_NOT_HOUSEHOLD_RATIO",
        "HU_CLASS_AVERAGE_RATIO_IS_NOT_AGE_SPECIFIC_RATIO",
        "BOTTOM_AREA_CALIBRATION_IS_NOT_BOUNDARY_TYPE_OR_U_RESOLUTION",
        "REFERENCE_PROGRAMME_PROXY_IS_NOT_REALIZED_PROJECT_GEOMETRY",
    )
