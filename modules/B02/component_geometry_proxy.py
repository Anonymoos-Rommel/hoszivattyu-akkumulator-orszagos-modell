"""B02-P85 bounded component-geometry proxy surface.

P85 consumes only the already-canonical KEOP23 synthetic geometry and P79
set-valued WBL/P21 crosswalk. It does not invent household component areas.

The purpose is to expose geometry quantities that are reproducibly derivable
from the source synthetic type table and to narrow the previous broad
component-area blocker.

Critical boundaries:

KEOP23 SYNTHETIC GEOMETRY != HOUSEHOLD GEOMETRY
BOUNDING RECTANGLE FACADE PROXY != NET EXTERNAL WALL AREA
BOUNDING PLAN AREA != ROOF OR GROUND CONTACT AREA
MAX USABLE ROOF AREA != TOTAL ROOF HEAT-LOSS AREA
CANDIDATE-TYPE MIN/MAX != WITHIN-TYPE CONFIDENCE INTERVAL
"""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache

from modules.B02.keop23_wbl_crosswalk import (
    GROUPS,
    WBL_PERIOD_INTERVALS,
    candidates_for,
    load_types,
)


@dataclass(frozen=True)
class TypeGeometryProxy:
    type_id: int
    building_group: str
    dwelling_count_model: int
    heated_volume_m3_per_dwelling: float
    mean_storey_floorplate_m2_per_dwelling: float
    bbox_plan_area_m2_per_dwelling: float
    bbox_rectangular_facade_proxy_m2_per_dwelling: float
    max_usable_roof_area_m2_per_dwelling: float
    heated_to_total_floor_area_ratio: float
    status: str = "DERIVED_SYNTHETIC_GEOMETRY_PROXY"


@dataclass(frozen=True)
class StratumGeometryEnvelope:
    wbl_period_code: str
    building_group: str
    candidate_type_ids: tuple[int, ...]
    candidate_count: int
    heated_volume_lower_m3_per_dwelling: float
    heated_volume_upper_m3_per_dwelling: float
    mean_storey_floorplate_lower_m2_per_dwelling: float
    mean_storey_floorplate_upper_m2_per_dwelling: float
    bbox_plan_area_lower_m2_per_dwelling: float
    bbox_plan_area_upper_m2_per_dwelling: float
    bbox_facade_proxy_lower_m2_per_dwelling: float
    bbox_facade_proxy_upper_m2_per_dwelling: float
    max_usable_roof_area_lower_m2_per_dwelling: float
    max_usable_roof_area_upper_m2_per_dwelling: float
    heated_to_total_floor_ratio_lower: float
    heated_to_total_floor_ratio_upper: float
    status: str = "SET_VALUED_SYNTHETIC_GEOMETRY_PROXY"


def _positive(value: float, name: str) -> float:
    number = float(value)
    if number <= 0:
        raise ValueError(f"{name} must be positive")
    return number


@lru_cache(maxsize=None)
def type_geometry_proxy(type_id: int) -> TypeGeometryProxy:
    types = load_types()
    if type_id not in types:
        raise ValueError(f"unsupported KEOP23 type {type_id}")
    item = types[type_id]

    dwellings = _positive(item.dwelling_count_model, "dwelling_count_model")
    storeys = _positive(item.storeys, "storeys")
    ceiling = _positive(item.ceiling_height_m, "ceiling_height_m")
    bbox_x = _positive(item.bbox_x_m, "bbox_x_m")
    bbox_y = _positive(item.bbox_y_m, "bbox_y_m")
    total_floor = _positive(item.total_floor_area_m2, "total_floor_area_m2")
    heated_floor = _positive(item.heated_floor_area_m2, "heated_floor_area_m2")
    usable_roof = _positive(item.max_usable_roof_area_m2, "max_usable_roof_area_m2")

    if heated_floor > total_floor + 1e-9:
        raise ValueError("heated floor area cannot exceed total floor area")

    heated_volume = heated_floor * ceiling / dwellings
    mean_storey_floorplate = total_floor / storeys / dwellings
    bbox_plan = bbox_x * bbox_y / dwellings

    # Explicit rectangularization proxy only. The source fields provide the
    # synthetic building bounding x/y dimensions, storey count and ceiling
    # height. P85 does not promote this arithmetic to observed/net facade area.
    bbox_facade_proxy = (
        2.0 * (bbox_x + bbox_y) * ceiling * storeys / dwellings
    )

    return TypeGeometryProxy(
        type_id=item.type_id,
        building_group=item.building_group,
        dwelling_count_model=item.dwelling_count_model,
        heated_volume_m3_per_dwelling=heated_volume,
        mean_storey_floorplate_m2_per_dwelling=mean_storey_floorplate,
        bbox_plan_area_m2_per_dwelling=bbox_plan,
        bbox_rectangular_facade_proxy_m2_per_dwelling=bbox_facade_proxy,
        max_usable_roof_area_m2_per_dwelling=usable_roof / dwellings,
        heated_to_total_floor_area_ratio=heated_floor / total_floor,
    )


def all_type_geometry_proxies() -> tuple[TypeGeometryProxy, ...]:
    return tuple(type_geometry_proxy(type_id) for type_id in sorted(load_types()))


def _bounds(values: list[float]) -> tuple[float, float]:
    if not values:
        raise ValueError("cannot bound an empty geometry set")
    return min(values), max(values)


@lru_cache(maxsize=None)
def stratum_geometry_envelope(
    wbl_period_code: str,
    building_group: str,
) -> StratumGeometryEnvelope:
    rule = candidates_for(wbl_period_code, building_group)
    proxies = [type_geometry_proxy(type_id) for type_id in rule.candidate_type_ids]

    if any(proxy.building_group != building_group for proxy in proxies):
        raise ValueError("candidate type building-group mismatch")

    heated_volume = _bounds([x.heated_volume_m3_per_dwelling for x in proxies])
    floorplate = _bounds([x.mean_storey_floorplate_m2_per_dwelling for x in proxies])
    bbox_plan = _bounds([x.bbox_plan_area_m2_per_dwelling for x in proxies])
    facade = _bounds(
        [x.bbox_rectangular_facade_proxy_m2_per_dwelling for x in proxies]
    )
    usable_roof = _bounds([x.max_usable_roof_area_m2_per_dwelling for x in proxies])
    heated_ratio = _bounds([x.heated_to_total_floor_area_ratio for x in proxies])

    return StratumGeometryEnvelope(
        wbl_period_code=wbl_period_code,
        building_group=building_group,
        candidate_type_ids=rule.candidate_type_ids,
        candidate_count=len(rule.candidate_type_ids),
        heated_volume_lower_m3_per_dwelling=heated_volume[0],
        heated_volume_upper_m3_per_dwelling=heated_volume[1],
        mean_storey_floorplate_lower_m2_per_dwelling=floorplate[0],
        mean_storey_floorplate_upper_m2_per_dwelling=floorplate[1],
        bbox_plan_area_lower_m2_per_dwelling=bbox_plan[0],
        bbox_plan_area_upper_m2_per_dwelling=bbox_plan[1],
        bbox_facade_proxy_lower_m2_per_dwelling=facade[0],
        bbox_facade_proxy_upper_m2_per_dwelling=facade[1],
        max_usable_roof_area_lower_m2_per_dwelling=usable_roof[0],
        max_usable_roof_area_upper_m2_per_dwelling=usable_roof[1],
        heated_to_total_floor_ratio_lower=heated_ratio[0],
        heated_to_total_floor_ratio_upper=heated_ratio[1],
    )


def all_stratum_geometry_envelopes() -> tuple[StratumGeometryEnvelope, ...]:
    rows: list[StratumGeometryEnvelope] = []
    for period in WBL_PERIOD_INTERVALS:
        for group in GROUPS:
            rows.append(stratum_geometry_envelope(period, group))
    return tuple(rows)


def component_geometry_state() -> dict[str, object]:
    """Return the exact P85 blocker narrowing without false promotion."""

    return {
        "type_proxy_count": len(all_type_geometry_proxies()),
        "stratum_envelope_count": len(all_stratum_geometry_envelopes()),
        "generic_component_geometry_blocker": "PARTIAL_RESOLVED_SYNTHETIC_PROXY",
        "resolved_or_narrowed": (
            "HEATED_VOLUME_GEOMETRY_PROXY_MATERIALIZED",
            "MEAN_STOREY_FLOORPLATE_PROXY_MATERIALIZED",
            "BOUNDING_PLAN_PROXY_MATERIALIZED",
            "BOUNDING_RECTANGULAR_FACADE_PROXY_MATERIALIZED",
            "MAX_USABLE_ROOF_AREA_PER_DWELLING_MATERIALIZED",
        ),
        "residuals": (
            "NET_EXTERNAL_WALL_AND_WINDOW_AREA_SPLIT_INFERENCE_REQUIRED",
            "ACTUAL_TOP_HEAT_LOSS_PLANE_AREA_INFERENCE_REQUIRED",
            "ACTUAL_BOTTOM_HEAT_LOSS_PLANE_AREA_INFERENCE_REQUIRED",
            "BBOX_RECTANGULARIZATION_VALIDATION_REQUIRED",
            "PITCHED_ROOF_POSTSTATE_U_BOUND_REQUIRED",
        ),
    }


def record_level_boundary() -> tuple[str, ...]:
    return (
        "P85_SYNTHETIC_PROXY_CANNOT_PASS_A_SPECIFIC_BUILDING",
        "P85_BBOX_FACADE_PROXY_IS_NOT_NET_WALL_AREA",
        "P85_BBOX_PLAN_IS_NOT_ROOF_OR_GROUND_CONTACT_AREA",
        "P85_CANDIDATE_SET_MIN_MAX_IS_NOT_WITHIN_TYPE_STATISTICAL_BOUND",
    )
