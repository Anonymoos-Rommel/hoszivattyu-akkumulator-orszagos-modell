"""B05-P12 cross-manufacturer cold high-supply physical-surface contract.

This module qualifies surface availability only. It deliberately does not
average product sizes or infer market shares.

SOURCE-NATIVE CAPACITY + SOURCE-NATIVE COP -> ELECTRICAL INPUT DER
TWO-MANUFACTURER PHYSICAL SURFACE != HUNGARIAN MARKET REPRESENTATIVENESS
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from modules.B05.engine import PerformanceMap


ROOT = Path(__file__).resolve().parents[2]
POINTS = ROOT / "data" / "processed" / "heat_pump_performance_points.csv"

P9_STRESS_ENDPOINTS = (-13.331944, -9.644444)
SUPPLY_ANCHORS = (35.0, 45.0, 55.0)

MANUFACTURER_BY_EQUIPMENT = {
    "TEKNOPOINT-ATHENA-R32-A0732": "TEKNO_POINT",
    "TEKNOPOINT-ATHENA-R32-A0932": "TEKNO_POINT",
    "ECPOWER-PMH-6": "EC_POWER",
    "ECPOWER-PMH-19": "EC_POWER",
}


@dataclass(frozen=True)
class SurfaceQualification:
    equipment_id: str
    manufacturer: str
    qualified: bool
    evaluated_coordinate_count: int
    status: str


def qualify_equipment_surface(equipment_id: str) -> SurfaceQualification:
    if equipment_id not in MANUFACTURER_BY_EQUIPMENT:
        raise ValueError(f"equipment is not admitted by P12: {equipment_id}")
    performance_map = PerformanceMap.from_csv(POINTS, equipment_id)
    count = 0
    for outdoor in P9_STRESS_ENDPOINTS:
        for supply in SUPPLY_ANCHORS:
            result = performance_map.evaluate(outdoor, supply)
            if result.point is None or result.status.startswith("Q"):
                return SurfaceQualification(
                    equipment_id,
                    MANUFACTURER_BY_EQUIPMENT[equipment_id],
                    False,
                    count,
                    result.status,
                )
            count += 1
    return SurfaceQualification(
        equipment_id,
        MANUFACTURER_BY_EQUIPMENT[equipment_id],
        True,
        count,
        "QUALIFIED_P9_COLD_HIGH_SUPPLY_SURFACE",
    )


def qualified_manufacturers() -> tuple[str, ...]:
    qualified = {
        qualification.manufacturer
        for equipment_id in MANUFACTURER_BY_EQUIPMENT
        for qualification in (qualify_equipment_surface(equipment_id),)
        if qualification.qualified
    }
    return tuple(sorted(qualified))


def cross_manufacturer_status() -> str:
    return (
        "RESOLVED_FOR_PROGRAMME_PHYSICAL_COHORT"
        if len(qualified_manufacturers()) >= 2
        else "Q / SECOND_MANUFACTURER_SURFACE_REQUIRED"
    )


def boundary() -> tuple[str, ...]:
    return (
        "NO_PRODUCT_SIZE_AVERAGING",
        "NO_MARKET_SHARE_INFERENCE",
        "NO_HUNGARY_PROCUREMENT_CLAIM",
        "NO_BELOW_MINUS15_PERFORMANCE_EXTRAPOLATION",
        "ECPOWER_ELECTRICAL_INPUT_IS_DER_NOT_OBS",
    )
