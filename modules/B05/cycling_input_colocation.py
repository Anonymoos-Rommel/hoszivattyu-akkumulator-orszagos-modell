"""B05-P19 fail-closed cycling-input co-location gate."""
from __future__ import annotations
from dataclasses import dataclass

POINT_PAIRED_MINIMUM_CAPACITY_COP_REQUIRED="POINT_PAIRED_MINIMUM_CAPACITY_COP_REQUIRED"
PRODUCT_CDH_MEASUREMENT_STATUS_REQUIRED="PRODUCT_CDH_MEASUREMENT_STATUS_REQUIRED"
EXACT_MODULATION_FLOOR_REQUIRED="EXACT_MODULATION_FLOOR_REQUIRED"
QUALIFIED="QUALIFIED_CYCLING_INPUT_COLOCATION"
MEASUREMENT_DETERMINED="QUALIFIED_MEASUREMENT_DETERMINED"

@dataclass(frozen=True)
class CyclingInputColocation:
    status: str
    residual_gaps: tuple[str,...]

def derive_cop_from_capacity_input(*, capacity_kw: float, input_kw: float, point_pairing_explicit: bool) -> float | None:
    if capacity_kw <= 0 or input_kw <= 0:
        raise ValueError("capacity and input must be positive")
    if not point_pairing_explicit:
        return None
    return capacity_kw/input_kw

def assess_cycling_input_colocation(
    *,
    exact_modulation_floor: bool,
    point_paired_minimum_capacity_cop: bool,
    cdh_status: str,
) -> CyclingInputColocation:
    gaps=[]
    if not exact_modulation_floor:
        gaps.append(EXACT_MODULATION_FLOOR_REQUIRED)
    if not point_paired_minimum_capacity_cop:
        gaps.append(POINT_PAIRED_MINIMUM_CAPACITY_COP_REQUIRED)
    if cdh_status != MEASUREMENT_DETERMINED:
        gaps.append(PRODUCT_CDH_MEASUREMENT_STATUS_REQUIRED)
    if gaps:
        return CyclingInputColocation("Q / CYCLING_INPUT_COLOCATION_REQUIRED",tuple(gaps))
    return CyclingInputColocation(QUALIFIED,())

def p19_boundary() -> tuple[str,...]:
    return (
        "SAME_PRODUCT_REQUIRED",
        "SAME_OPERATING_COORDINATE_REQUIRED",
        "RANGE_ENDPOINTS_ARE_NOT_POINT_PAIRS",
        "NO_RANGE_ENDPOINT_DIVISION_WITHOUT_PAIRING_AUTHORITY",
        "EXACT_0_900_CDH_REMAINS_MEASUREMENT_DEFAULT_AMBIGUOUS",
        "NO_CROSS_PRODUCT_ASSEMBLY",
        POINT_PAIRED_MINIMUM_CAPACITY_COP_REQUIRED,
    )
