"""B05-P30 hydraulic performance-axis admissibility.

A measured or fixed hydraulic condition is not automatically an independent
capacity/COP surface coordinate.  The gate below admits return temperature or
delta-T only when source-native same-product performance observations explicitly
vary that coordinate at otherwise matched outdoor and supply conditions.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

RETURN_TEMPERATURE = "return_temperature_c"
DELTA_T = "delta_temperature_c"

ADMITTED = "ADMISSIBLE_SOURCE_NATIVE_HYDRAULIC_PERFORMANCE_AXIS"
NO_VALUES = "NOT_ADMITTED_NO_SOURCE_NATIVE_AXIS_VALUES"
FIXED_ONLY = "NOT_ADMITTED_FIXED_TEST_CONDITION_OR_METADATA"
MIXED_EQUIPMENT = "Q_MIXED_EQUIPMENT_ID"
MIXED_BOUNDARY = "Q_MIXED_OR_NON_TOTAL_UNIT_BOUNDARY"
INCONSISTENT_COORDINATES = "Q_INCONSISTENT_SUPPLY_RETURN_DELTA"
DOUBLE_COUNT = "Q_RETURN_AND_DELTA_NOT_INDEPENDENT_WITH_SUPPLY"


@dataclass(frozen=True)
class HydraulicPerformancePoint:
    equipment_id: str
    outdoor_temperature_c: float
    supply_temperature_c: float
    thermal_capacity_kw: float
    electrical_input_kw: float
    cop: float
    return_temperature_c: float | None = None
    delta_temperature_c: float | None = None
    unit_boundary: str = "total_unit_input"
    source_id: str = ""


@dataclass(frozen=True)
class HydraulicAxisDecision:
    axis: str
    status: str
    admissible: bool
    evidence_status: str
    reason: str
    qualifying_matched_coordinates: int = 0


def _axis_value(point: HydraulicPerformancePoint, axis: str) -> float | None:
    if axis == RETURN_TEMPERATURE:
        return point.return_temperature_c
    if axis == DELTA_T:
        return point.delta_temperature_c
    raise ValueError(f"unsupported hydraulic axis: {axis!r}")


def assess_hydraulic_axis(
    points: Iterable[HydraulicPerformancePoint],
    axis: str,
    *,
    coordinate_tolerance_k: float = 0.25,
) -> HydraulicAxisDecision:
    """Assess whether a hydraulic coordinate is a real performance dimension.

    Admission requires at least one matched outdoor+supply coordinate with two
    or more explicit source-native values of the candidate hydraulic coordinate
    for the same equipment and total-unit input boundary.
    """

    rows = tuple(points)
    if axis not in {RETURN_TEMPERATURE, DELTA_T}:
        raise ValueError(f"unsupported hydraulic axis: {axis!r}")
    if not rows:
        return HydraulicAxisDecision(axis, NO_VALUES, False, "Q", "No performance observations were supplied.")

    equipment = {row.equipment_id for row in rows}
    if len(equipment) != 1:
        return HydraulicAxisDecision(axis, MIXED_EQUIPMENT, False, "Q", "Hydraulic-axis evidence cannot be pooled across equipment IDs.")

    if any(row.unit_boundary != "total_unit_input" for row in rows):
        return HydraulicAxisDecision(axis, MIXED_BOUNDARY, False, "Q", "B05 requires one exact total-unit electrical-input boundary.")

    for row in rows:
        if row.return_temperature_c is not None and row.delta_temperature_c is not None:
            expected_delta = row.supply_temperature_c - row.return_temperature_c
            if abs(expected_delta - row.delta_temperature_c) > coordinate_tolerance_k:
                return HydraulicAxisDecision(
                    axis,
                    INCONSISTENT_COORDINATES,
                    False,
                    "Q",
                    "Explicit supply, return and delta-T fields violate their hydraulic identity beyond tolerance.",
                )

    populated = [row for row in rows if _axis_value(row, axis) is not None]
    if not populated:
        return HydraulicAxisDecision(
            axis,
            NO_VALUES,
            False,
            "Q",
            "No source-native values exist for the candidate hydraulic coordinate.",
        )

    matched: dict[tuple[float, float], set[float]] = {}
    for row in populated:
        key = (row.outdoor_temperature_c, row.supply_temperature_c)
        matched.setdefault(key, set()).add(float(_axis_value(row, axis)))  # type: ignore[arg-type]

    qualifying = sum(1 for values in matched.values() if len(values) >= 2)
    if qualifying == 0:
        return HydraulicAxisDecision(
            axis,
            FIXED_ONLY,
            False,
            "Q",
            "The candidate is present only as a fixed/test/control condition; no matched outdoor+supply coordinate varies it independently.",
        )

    return HydraulicAxisDecision(
        axis,
        ADMITTED,
        True,
        "OBS",
        "Source-native same-product performance observations vary the candidate hydraulic coordinate at matched outdoor+supply conditions.",
        qualifying,
    )


def validate_axis_selection(*, use_return_axis: bool, use_delta_t_axis: bool) -> str:
    """Prevent double-counting algebraically equivalent hydraulic coordinates."""

    if use_return_axis and use_delta_t_axis:
        return DOUBLE_COUNT
    if use_return_axis:
        return RETURN_TEMPERATURE
    if use_delta_t_axis:
        return DELTA_T
    return "SUPPLY_ONLY_V1"


def p30_boundary() -> str:
    return (
        "FIXED_TEST_CONDITION_OR_SENSOR != PERFORMANCE_SENSITIVITY_AXIS; "
        "WITH_SUPPLY_RETAINED_RETURN_AND_DELTA_T_ARE_NOT_TWO_INDEPENDENT_AXES"
    )
