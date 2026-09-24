"""B05-P18 bounded EN14825-based to-water cycling method."""
from __future__ import annotations
from dataclasses import dataclass

MINIMUM_CAPACITY_COP_INPUT_REQUIRED="MINIMUM_CAPACITY_COP_INPUT_REQUIRED"
QUALIFIED="QUALIFIED_EN14825_WATER_SIDE_CYCLING_METHOD"

@dataclass(frozen=True)
class CyclingMethodResult:
    status: str
    capacity_ratio: float
    cop_bin: float | None
    residual_gap: str | None

def water_side_cycling_cop(cop_declared: float, capacity_ratio: float, cdh: float) -> float:
    if cop_declared <= 0:
        raise ValueError("cop_declared must be positive")
    if not (0 < capacity_ratio <= 1):
        raise ValueError("capacity_ratio must be in (0,1]")
    if not (0 < cdh <= 1):
        raise ValueError("cdh must be in (0,1]")
    return cop_declared * capacity_ratio / (cdh * capacity_ratio + (1.0-cdh))

def evaluate_below_minimum_modulation(
    *,
    required_capacity_kw: float,
    cycling_capacity_kw: float,
    cdh: float,
    cop_declared: float | None,
    cop_capacity_kw: float | None,
    tolerance_kw: float = 1e-9,
) -> CyclingMethodResult:
    if required_capacity_kw <= 0:
        raise ValueError("required_capacity_kw must be positive")
    if cycling_capacity_kw <= 0:
        raise ValueError("cycling_capacity_kw must be positive")
    if required_capacity_kw >= cycling_capacity_kw:
        raise ValueError("method requires proven below-minimum cycling state")
    if not (0 < cdh <= 1):
        raise ValueError("cdh must be in (0,1]")

    cr=required_capacity_kw/cycling_capacity_kw
    if cop_declared is None or cop_capacity_kw is None:
        return CyclingMethodResult("Q / "+MINIMUM_CAPACITY_COP_INPUT_REQUIRED,cr,None,MINIMUM_CAPACITY_COP_INPUT_REQUIRED)
    if cop_declared <= 0 or cop_capacity_kw <= 0:
        raise ValueError("COP inputs must be positive")
    if abs(cop_capacity_kw-cycling_capacity_kw) > tolerance_kw:
        return CyclingMethodResult("Q / "+MINIMUM_CAPACITY_COP_INPUT_REQUIRED,cr,None,MINIMUM_CAPACITY_COP_INPUT_REQUIRED)

    return CyclingMethodResult(QUALIFIED,cr,water_side_cycling_cop(cop_declared,cr,cdh),None)

def p18_boundary() -> tuple[str,...]:
    return (
        "CYCLING_STATE_MUST_BE_PROVEN_FIRST",
        "COPD_CAPACITY_MUST_EQUAL_CYCLING_CAPACITY",
        "CERTIFIED_PDH_COP_IS_NOT_AUTOMATICALLY_MINIMUM_CAPACITY_COP",
        "NO_DIRECT_COP_TIMES_CDH",
        "NO_REGULATORY_DEFAULT_AS_PRODUCT_OBS",
        MINIMUM_CAPACITY_COP_INPUT_REQUIRED,
    )
