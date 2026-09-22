"""B02-P92 Hungarian facade/opening split proxy for the reference programme.

P85 materialized a rectangularized gross facade proxy but explicitly prohibited
inventing a wall/window split. P92 adds a Hungarian TABULA/EPISCOPE
class-average calibration for that split.

Important source semantics:

TABULA A_Window = A_Window_1 + A_Window_2 + A_Door_1

Therefore P92 deliberately calls the quantity OPENING_AREA, not WINDOW_AREA.

Hungarian class-average values from the TABULA/EPISCOPE database evaluation:

SFH: wall 128 m2, openings 16 m2
MFH: wall 668 m2, openings 97 m2
AB:  wall 1197 m2, openings 359 m2

TH has no Hungarian value in the evaluated table.

These values are averages of example-building envelope data across construction
year classes. They are admissible as a preliminary synthetic-average-building
calibration, not as observed household distributions.

Critical boundaries:

TABULA_A_WINDOW_INCLUDES_DOOR
HU_CLASS_AVERAGE != HOUSEHOLD_AREA_SHARE
HU_CLASS_AVERAGE != AGE_SPECIFIC_OPENING_SHARE
P85_BBOX_FACADE_PROXY != SOURCE_NATIVE_TABULA_FACADE
SPLIT_CALIBRATION != BBOX_VALIDATION
OPENING_AREA != WINDOW_ONLY_AREA
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

TABULA_HU_SFH_WALL_M2 = 128.0
TABULA_HU_SFH_OPENING_M2 = 16.0
TABULA_HU_MFH_WALL_M2 = 668.0
TABULA_HU_MFH_OPENING_M2 = 97.0
TABULA_HU_AB_WALL_M2 = 1197.0
TABULA_HU_AB_OPENING_M2 = 359.0

# Current Hungarian 9/2023 EKM element limits. P92 uses the ordinary external
# door value as a conservative aggregate upper bound for the TABULA opening
# field, because that field includes windows plus one door component.
CURRENT_REFERENCE_WINDOW_U_MAX_W_M2K = 1.10
CURRENT_REFERENCE_EXTERNAL_DOOR_U_MAX_W_M2K = 1.40
REFERENCE_AGGREGATE_OPENING_U_UPPER_W_M2K = 1.40

# P91 conservative external-wall corrected U upper.
REFERENCE_WALL_CORRECTED_U_UPPER_W_M2K = 0.336

QUALIFIED_HUNGARIAN_FACADE_OPENING_SPLIT_PROXY = (
    "QUALIFIED_HUNGARIAN_FACADE_OPENING_SPLIT_PROXY"
)
BBOX_RECTANGULARIZATION_VALIDATION_REQUIRED = (
    "BBOX_RECTANGULARIZATION_VALIDATION_REQUIRED"
)
REALIZED_FACADE_GEOMETRY_VERIFICATION_REQUIRED = (
    "REALIZED_FACADE_GEOMETRY_VERIFICATION_REQUIRED"
)


@dataclass(frozen=True)
class OpeningShareBound:
    building_group: str
    lower: float
    upper: float
    source_classes: tuple[str, ...]
    status: str
    evidence_status: str


@dataclass(frozen=True)
class FacadeSplitEnvelope:
    gross_facade_lower_m2: float
    gross_facade_upper_m2: float
    opening_share_lower: float
    opening_share_upper: float
    opening_area_lower_m2: float
    opening_area_upper_m2: float
    net_wall_area_lower_m2: float
    net_wall_area_upper_m2: float
    facade_transmission_h_upper_w_per_k: float
    status: str
    evidence_status: str
    blocker: str


@dataclass(frozen=True)
class StratumFacadeSplit:
    surface_id: str
    wbl_period_code: str
    building_group: str
    gross_facade_proxy_lower_m2_per_dwelling: float
    gross_facade_proxy_upper_m2_per_dwelling: float
    opening_share_lower: float
    opening_share_upper: float
    opening_area_proxy_lower_m2_per_dwelling: float
    opening_area_proxy_upper_m2_per_dwelling: float
    net_wall_area_proxy_lower_m2_per_dwelling: float
    net_wall_area_proxy_upper_m2_per_dwelling: float
    facade_transmission_h_upper_w_per_k_per_dwelling: float
    status: str
    evidence_status: str
    blocker: str


def _opening_share(*, wall_m2: float, opening_m2: float) -> float:
    wall = float(wall_m2)
    opening = float(opening_m2)
    if wall <= 0 or opening < 0:
        raise ValueError("wall must be positive and opening nonnegative")
    return opening / (wall + opening)


HU_SFH_OPENING_SHARE = _opening_share(
    wall_m2=TABULA_HU_SFH_WALL_M2,
    opening_m2=TABULA_HU_SFH_OPENING_M2,
)
HU_MFH_OPENING_SHARE = _opening_share(
    wall_m2=TABULA_HU_MFH_WALL_M2,
    opening_m2=TABULA_HU_MFH_OPENING_M2,
)
HU_AB_OPENING_SHARE = _opening_share(
    wall_m2=TABULA_HU_AB_WALL_M2,
    opening_m2=TABULA_HU_AB_OPENING_M2,
)


def opening_share_bound(building_group: str) -> OpeningShareBound:
    """Return the P92 Hungarian class-average calibration envelope.

    FAMILY_HOUSE has one available Hungarian TABULA size class (SFH), so the
    lower/upper are identical *as a reference-class calibration*. This must not
    be interpreted as zero population variance.

    MULTI_DWELLING spans the available Hungarian MFH and AB classes; P92 keeps
    their min/max as a set rather than inventing a class mixture.
    """

    if building_group == FAMILY_HOUSE:
        return OpeningShareBound(
            building_group=building_group,
            lower=HU_SFH_OPENING_SHARE,
            upper=HU_SFH_OPENING_SHARE,
            source_classes=("HU_SFH",),
            status=QUALIFIED_HUNGARIAN_FACADE_OPENING_SPLIT_PROXY,
            evidence_status="DER/SCN_PROXY",
        )
    if building_group == MULTI_DWELLING:
        values = (HU_MFH_OPENING_SHARE, HU_AB_OPENING_SHARE)
        return OpeningShareBound(
            building_group=building_group,
            lower=min(values),
            upper=max(values),
            source_classes=("HU_MFH", "HU_AB"),
            status=QUALIFIED_HUNGARIAN_FACADE_OPENING_SPLIT_PROXY,
            evidence_status="DER/SCN_PROXY",
        )
    raise ValueError(f"unsupported building group: {building_group}")


def split_gross_facade_proxy(
    *,
    gross_facade_lower_m2: float,
    gross_facade_upper_m2: float,
    building_group: str,
) -> FacadeSplitEnvelope:
    """Split the P85 gross-facade proxy with a Hungarian class-average share.

    Interval arithmetic preserves all combinations of gross facade and admitted
    opening-share classes. It does not claim correlation or statistical
    confidence.

    A conservative transmission upper is also returned. Because the TABULA
    opening field contains windows + door, the whole opening proxy uses the
    current ordinary external-door limit 1.40 W/m2K as an upper bound. This is
    deliberately conservative relative to the 1.10 W/m2K wood/PVC glazed
    opening limit.
    """

    gross_lo = float(gross_facade_lower_m2)
    gross_hi = float(gross_facade_upper_m2)
    if gross_lo <= 0 or gross_hi <= 0 or gross_lo > gross_hi:
        raise ValueError("invalid gross facade interval")

    share = opening_share_bound(building_group)
    opening_lo = gross_lo * share.lower
    opening_hi = gross_hi * share.upper

    # Outer interval for net wall = gross * (1 - opening_share).
    wall_lo = gross_lo * (1.0 - share.upper)
    wall_hi = gross_hi * (1.0 - share.lower)

    # Correlated conservative upper at gross=max, share=max because
    # U_opening_upper > U_wall_corrected_upper.
    h_upper = gross_hi * (
        (1.0 - share.upper) * REFERENCE_WALL_CORRECTED_U_UPPER_W_M2K
        + share.upper * REFERENCE_AGGREGATE_OPENING_U_UPPER_W_M2K
    )

    return FacadeSplitEnvelope(
        gross_facade_lower_m2=gross_lo,
        gross_facade_upper_m2=gross_hi,
        opening_share_lower=share.lower,
        opening_share_upper=share.upper,
        opening_area_lower_m2=opening_lo,
        opening_area_upper_m2=opening_hi,
        net_wall_area_lower_m2=wall_lo,
        net_wall_area_upper_m2=wall_hi,
        facade_transmission_h_upper_w_per_k=h_upper,
        status=QUALIFIED_HUNGARIAN_FACADE_OPENING_SPLIT_PROXY,
        evidence_status="DER/SCN_PROXY",
        blocker=BBOX_RECTANGULARIZATION_VALIDATION_REQUIRED,
    )


@lru_cache(maxsize=None)
def reference_programme_facade_split_surface() -> tuple[StratumFacadeSplit, ...]:
    with P85_SURFACE.open(encoding="utf-8", newline="") as handle:
        rows = tuple(csv.DictReader(handle))
    if len(rows) != 14:
        raise ValueError(f"expected 14 P85 strata, got {len(rows)}")

    out: list[StratumFacadeSplit] = []
    for index, row in enumerate(rows, start=1):
        split = split_gross_facade_proxy(
            gross_facade_lower_m2=float(
                row["bbox_facade_proxy_lower_m2_per_dwelling"]
            ),
            gross_facade_upper_m2=float(
                row["bbox_facade_proxy_upper_m2_per_dwelling"]
            ),
            building_group=row["building_group"],
        )
        out.append(
            StratumFacadeSplit(
                surface_id=f"B02-P92-F{index:02d}",
                wbl_period_code=row["wbl_period_code"],
                building_group=row["building_group"],
                gross_facade_proxy_lower_m2_per_dwelling=(
                    split.gross_facade_lower_m2
                ),
                gross_facade_proxy_upper_m2_per_dwelling=(
                    split.gross_facade_upper_m2
                ),
                opening_share_lower=split.opening_share_lower,
                opening_share_upper=split.opening_share_upper,
                opening_area_proxy_lower_m2_per_dwelling=(
                    split.opening_area_lower_m2
                ),
                opening_area_proxy_upper_m2_per_dwelling=(
                    split.opening_area_upper_m2
                ),
                net_wall_area_proxy_lower_m2_per_dwelling=(
                    split.net_wall_area_lower_m2
                ),
                net_wall_area_proxy_upper_m2_per_dwelling=(
                    split.net_wall_area_upper_m2
                ),
                facade_transmission_h_upper_w_per_k_per_dwelling=(
                    split.facade_transmission_h_upper_w_per_k
                ),
                status=split.status,
                evidence_status=split.evidence_status,
                blocker=split.blocker,
            )
        )
    return tuple(out)


def p92_state() -> dict[str, object]:
    rows = reference_programme_facade_split_surface()
    return {
        "hungarian_sfh_wall_m2": TABULA_HU_SFH_WALL_M2,
        "hungarian_sfh_opening_m2": TABULA_HU_SFH_OPENING_M2,
        "hungarian_sfh_opening_share": HU_SFH_OPENING_SHARE,
        "hungarian_mfh_wall_m2": TABULA_HU_MFH_WALL_M2,
        "hungarian_mfh_opening_m2": TABULA_HU_MFH_OPENING_M2,
        "hungarian_mfh_opening_share": HU_MFH_OPENING_SHARE,
        "hungarian_ab_wall_m2": TABULA_HU_AB_WALL_M2,
        "hungarian_ab_opening_m2": TABULA_HU_AB_OPENING_M2,
        "hungarian_ab_opening_share": HU_AB_OPENING_SHARE,
        "stratum_count": len(rows),
        "split_status": QUALIFIED_HUNGARIAN_FACADE_OPENING_SPLIT_PROXY,
        "split_blocker": None,
        "remaining_geometry_blocker": BBOX_RECTANGULARIZATION_VALIDATION_REQUIRED,
        "realized_claim_residual": REALIZED_FACADE_GEOMETRY_VERIFICATION_REQUIRED,
    }


def semantic_boundaries() -> tuple[str, ...]:
    return (
        "TABULA_A_WINDOW_INCLUDES_DOOR",
        "OPENING_AREA_IS_NOT_WINDOW_ONLY_AREA",
        "HU_CLASS_AVERAGE_IS_NOT_HOUSEHOLD_AREA_SHARE",
        "HU_CLASS_AVERAGE_IS_NOT_AGE_SPECIFIC_OPENING_SHARE",
        "P85_BBOX_FACADE_PROXY_IS_NOT_SOURCE_NATIVE_TABULA_FACADE",
        "FACADE_SPLIT_CALIBRATION_IS_NOT_BBOX_VALIDATION",
        "REFERENCE_PROGRAMME_PROXY_IS_NOT_REALIZED_PROJECT_GEOMETRY",
        "NO_UNIVERSAL_TWENTY_PERCENT_WINDOW_DEFAULT",
    )
