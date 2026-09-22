"""B02-P95 TABULA facade estimator supersession of the P85 bbox facade proxy.

P85 exposed a rectangularized facade proxy from synthetic bbox x/y dimensions.
P92 could split that proxy into net wall and aggregate openings, but the facade
magnitude remained gated by BBOX_RECTANGULARIZATION_VALIDATION_REQUIRED.

P95 independently audits the bbox route against the official TABULA/EPISCOPE
simplified facade estimator and then replaces it for the prospective reference
programme.

TABULA simplified facade estimator:
    A_facade = b + 0.7 * A_C_Ref
with:
    b = 50 m2 for 0 attached neighbours
    b = 25 m2 for 1 attached neighbour
    b = 5 m2 for 2 attached neighbours

The KEOP23 type surface does not provide attached-neighbour count and does not
prove exact TABULA A_C_Ref semantics. P95 therefore preserves both uncertainties
as sets:

    attached neighbours in {0,1,2}
    A_C_Ref proxy in [heated_floor_area, total_floor_area]

The proxy upper is deliberately conservative: total floor area can include
unheated area and is not promoted to observed conditioned area.

Critical boundaries:

BBOX_AUDIT_FAILURE != DATA_DELETION
BBOX_PROXY != CANONICAL_REFERENCE_PROGRAMME_FACADE_AFTER_P95
TABULA_ESTIMATOR != OBSERVED_FACADE_AREA
HEATED_FLOOR_AREA != EXACT_TABULA_A_C_REF
TOTAL_FLOOR_AREA != EXACT_TABULA_A_C_REF
UNKNOWN_NEIGHBOUR_COUNT != DETACHED_DEFAULT
TOTAL_ENVELOPE_PM30_QUALITY != FACADE_SPECIFIC_ERROR_BOUND
REFERENCE_PROGRAMME_PROXY != REALIZED_PROJECT_GEOMETRY
"""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache

from modules.B02.component_geometry_proxy import type_geometry_proxy
from modules.B02.hungarian_facade_opening_split import (
    REFERENCE_AGGREGATE_OPENING_U_UPPER_W_M2K,
    REFERENCE_WALL_CORRECTED_U_UPPER_W_M2K,
    opening_share_bound,
)
from modules.B02.keop23_wbl_crosswalk import (
    GROUPS,
    WBL_PERIOD_INTERVALS,
    candidates_for,
    load_types,
)


TABULA_FACADE_SLOPE = 0.7
TABULA_FACADE_INTERCEPT_BY_NEIGHBOURS = {
    0: 50.0,
    1: 25.0,
    2: 5.0,
}

QUALIFIED_TABULA_FACADE_ESTIMATOR_PROXY = (
    "QUALIFIED_TABULA_FACADE_ESTIMATOR_PROXY"
)
BBOX_ROUTE_SUPERSEDED = "BBOX_ROUTE_SUPERSEDED"
REALIZED_FACADE_GEOMETRY_VERIFICATION_REQUIRED = (
    "REALIZED_FACADE_GEOMETRY_VERIFICATION_REQUIRED"
)


@dataclass(frozen=True)
class TypeFacadeAudit:
    type_id: int
    building_group: str
    dwelling_count_model: int
    heated_floor_area_m2: float
    total_floor_area_m2: float
    bbox_facade_proxy_m2_per_dwelling: float
    tabula_heated_ref_lower_m2_per_dwelling: float
    tabula_heated_ref_upper_m2_per_dwelling: float
    tabula_area_proxy_lower_m2_per_dwelling: float
    tabula_area_proxy_upper_m2_per_dwelling: float
    bbox_overlap_heated_ref_neighbour_set: bool
    bbox_overlap_area_proxy_neighbour_set: bool
    status: str
    evidence_status: str


@dataclass(frozen=True)
class StratumFacadeSurface:
    surface_id: str
    wbl_period_code: str
    building_group: str
    candidate_type_ids: tuple[int, ...]
    gross_facade_lower_m2_per_dwelling: float
    gross_facade_upper_m2_per_dwelling: float
    opening_share_lower: float
    opening_share_upper: float
    opening_area_lower_m2_per_dwelling: float
    opening_area_upper_m2_per_dwelling: float
    net_wall_area_lower_m2_per_dwelling: float
    net_wall_area_upper_m2_per_dwelling: float
    facade_transmission_h_upper_w_per_k_per_dwelling: float
    status: str
    evidence_status: str


def tabula_facade_estimate_m2(
    *, a_c_ref_m2: float, attached_neighbours: int
) -> float:
    area = float(a_c_ref_m2)
    if area <= 0:
        raise ValueError("a_c_ref_m2 must be positive")
    if attached_neighbours not in TABULA_FACADE_INTERCEPT_BY_NEIGHBOURS:
        raise ValueError("attached_neighbours must be 0, 1 or 2")
    return (
        TABULA_FACADE_INTERCEPT_BY_NEIGHBOURS[attached_neighbours]
        + TABULA_FACADE_SLOPE * area
    )


@lru_cache(maxsize=None)
def type_facade_audit(type_id: int) -> TypeFacadeAudit:
    types = load_types()
    if type_id not in types:
        raise ValueError(f"unsupported KEOP23 type {type_id}")
    item = types[type_id]
    dwellings = float(item.dwelling_count_model)
    if item.heated_floor_area_m2 <= 0 or item.total_floor_area_m2 <= 0:
        raise ValueError("floor areas must be positive")
    if item.heated_floor_area_m2 > item.total_floor_area_m2:
        raise ValueError("heated floor area cannot exceed total floor area")

    bbox = type_geometry_proxy(type_id).bbox_rectangular_facade_proxy_m2_per_dwelling

    # Narrow audit: take KEOP heated area as the closest available A_C_Ref proxy,
    # vary only the unknown attached-neighbour class.
    heated_lower = tabula_facade_estimate_m2(
        a_c_ref_m2=item.heated_floor_area_m2,
        attached_neighbours=2,
    ) / dwellings
    heated_upper = tabula_facade_estimate_m2(
        a_c_ref_m2=item.heated_floor_area_m2,
        attached_neighbours=0,
    ) / dwellings

    # Canonical P95 reference proxy: preserve floor-area semantic uncertainty
    # from heated to total floor area, and neighbour uncertainty from 2 to 0.
    proxy_lower = tabula_facade_estimate_m2(
        a_c_ref_m2=item.heated_floor_area_m2,
        attached_neighbours=2,
    ) / dwellings
    proxy_upper = tabula_facade_estimate_m2(
        a_c_ref_m2=item.total_floor_area_m2,
        attached_neighbours=0,
    ) / dwellings

    return TypeFacadeAudit(
        type_id=type_id,
        building_group=item.building_group,
        dwelling_count_model=item.dwelling_count_model,
        heated_floor_area_m2=item.heated_floor_area_m2,
        total_floor_area_m2=item.total_floor_area_m2,
        bbox_facade_proxy_m2_per_dwelling=bbox,
        tabula_heated_ref_lower_m2_per_dwelling=heated_lower,
        tabula_heated_ref_upper_m2_per_dwelling=heated_upper,
        tabula_area_proxy_lower_m2_per_dwelling=proxy_lower,
        tabula_area_proxy_upper_m2_per_dwelling=proxy_upper,
        bbox_overlap_heated_ref_neighbour_set=(heated_lower <= bbox <= heated_upper),
        bbox_overlap_area_proxy_neighbour_set=(proxy_lower <= bbox <= proxy_upper),
        status=QUALIFIED_TABULA_FACADE_ESTIMATOR_PROXY,
        evidence_status="DER/SCN_PROXY",
    )


def all_type_facade_audits() -> tuple[TypeFacadeAudit, ...]:
    return tuple(type_facade_audit(i) for i in sorted(load_types()))


@lru_cache(maxsize=None)
def stratum_facade_surface(
    wbl_period_code: str,
    building_group: str,
) -> StratumFacadeSurface:
    rule = candidates_for(wbl_period_code, building_group)
    audits = [type_facade_audit(i) for i in rule.candidate_type_ids]
    if any(a.building_group != building_group for a in audits):
        raise ValueError("candidate building-group mismatch")

    gross_lo = min(a.tabula_area_proxy_lower_m2_per_dwelling for a in audits)
    gross_hi = max(a.tabula_area_proxy_upper_m2_per_dwelling for a in audits)

    share = opening_share_bound(building_group)
    opening_lo = gross_lo * share.lower
    opening_hi = gross_hi * share.upper
    wall_lo = gross_lo * (1.0 - share.upper)
    wall_hi = gross_hi * (1.0 - share.lower)

    # Conservative facade-only transmission upper.
    h_upper = gross_hi * (
        (1.0 - share.upper) * REFERENCE_WALL_CORRECTED_U_UPPER_W_M2K
        + share.upper * REFERENCE_AGGREGATE_OPENING_U_UPPER_W_M2K
    )

    periods = list(WBL_PERIOD_INTERVALS)
    groups = list(GROUPS)
    index = periods.index(wbl_period_code) * len(groups) + groups.index(building_group) + 1

    return StratumFacadeSurface(
        surface_id=f"B02-P95-F{index:02d}",
        wbl_period_code=wbl_period_code,
        building_group=building_group,
        candidate_type_ids=rule.candidate_type_ids,
        gross_facade_lower_m2_per_dwelling=gross_lo,
        gross_facade_upper_m2_per_dwelling=gross_hi,
        opening_share_lower=share.lower,
        opening_share_upper=share.upper,
        opening_area_lower_m2_per_dwelling=opening_lo,
        opening_area_upper_m2_per_dwelling=opening_hi,
        net_wall_area_lower_m2_per_dwelling=wall_lo,
        net_wall_area_upper_m2_per_dwelling=wall_hi,
        facade_transmission_h_upper_w_per_k_per_dwelling=h_upper,
        status=QUALIFIED_TABULA_FACADE_ESTIMATOR_PROXY,
        evidence_status="DER/SCN_PROXY",
    )


def all_stratum_facade_surfaces() -> tuple[StratumFacadeSurface, ...]:
    return tuple(
        stratum_facade_surface(period, group)
        for period in WBL_PERIOD_INTERVALS
        for group in GROUPS
    )


def p95_state() -> dict[str, object]:
    audits = all_type_facade_audits()
    strata = all_stratum_facade_surfaces()
    return {
        "type_count": len(audits),
        "strict_heated_ref_bbox_overlap_count": sum(
            a.bbox_overlap_heated_ref_neighbour_set for a in audits
        ),
        "area_proxy_bbox_overlap_count": sum(
            a.bbox_overlap_area_proxy_neighbour_set for a in audits
        ),
        "bbox_route_status": BBOX_ROUTE_SUPERSEDED,
        "canonical_facade_status": QUALIFIED_TABULA_FACADE_ESTIMATOR_PROXY,
        "stratum_count": len(strata),
        "gross_facade_global_lower_m2_per_dwelling": min(
            x.gross_facade_lower_m2_per_dwelling for x in strata
        ),
        "gross_facade_global_upper_m2_per_dwelling": max(
            x.gross_facade_upper_m2_per_dwelling for x in strata
        ),
        "bbox_blocker": None,
        "realized_claim_residual": REALIZED_FACADE_GEOMETRY_VERIFICATION_REQUIRED,
    }


def semantic_boundaries() -> tuple[str, ...]:
    return (
        "BBOX_AUDIT_FAILURE_IS_NOT_DATA_DELETION",
        "BBOX_PROXY_IS_NOT_CANONICAL_REFERENCE_PROGRAMME_FACADE_AFTER_P95",
        "TABULA_ESTIMATOR_IS_NOT_OBSERVED_FACADE_AREA",
        "HEATED_FLOOR_AREA_IS_NOT_EXACT_TABULA_A_C_REF",
        "TOTAL_FLOOR_AREA_IS_NOT_EXACT_TABULA_A_C_REF",
        "UNKNOWN_NEIGHBOUR_COUNT_IS_NOT_DETACHED_DEFAULT",
        "TOTAL_ENVELOPE_PM30_QUALITY_IS_NOT_FACADE_SPECIFIC_ERROR_BOUND",
        "REFERENCE_PROGRAMME_PROXY_IS_NOT_REALIZED_PROJECT_GEOMETRY",
    )
