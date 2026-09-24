"""B05-P16 fail-closed part-load runtime state contract.

This module decides only whether an hourly load is OFF, continuously
modulatable, below the explicit minimum continuous capacity, or above available
capacity. It does not apply a numeric cycling-energy correction.
"""

from __future__ import annotations

from dataclasses import dataclass


OFF = "OFF"
CONTINUOUS = "CONTINUOUS_MODULATION"
CYCLING = "BELOW_MINIMUM_MODULATION / CYCLING_REQUIRED"
CAPACITY_SHORTFALL = "CAPACITY_SHORTFALL"
MODULATION_FLOOR_REQUIRED = "Q / MODULATION_FLOOR_REQUIRED"
MIN_MOD_COVERAGE_REQUIRED = "MULTI_PRODUCT_MIN_MODULATION_COVERAGE_REQUIRED"
NUMERIC_CYCLING_METHOD_REQUIRED = "CYCLING_DEGRADATION_NUMERIC_METHOD_AUTHORITY_REQUIRED"


@dataclass(frozen=True)
class PartLoadRuntimeState:
    required_capacity_kw: float
    available_capacity_kw: float
    minimum_continuous_capacity_kw: float | None
    load_ratio: float
    minimum_continuous_load_ratio: float | None
    state: str
    cdh_evidence_can_be_considered: bool
    direct_numeric_cdh_application_allowed: bool
    residual_gap: str | None


def classify_part_load_runtime(
    required_capacity_kw: float,
    available_capacity_kw: float,
    minimum_continuous_capacity_kw: float | None,
) -> PartLoadRuntimeState:
    """Classify part-load state without inventing a cycling penalty.

    The ordering is deliberate:
    load -> available capacity -> explicit minimum continuous capacity ->
    continuous/cycling state -> only then may product-specific degradation
    evidence be considered.

    Cdh is never applied numerically by this contract.
    """
    if required_capacity_kw < 0:
        raise ValueError("required capacity cannot be negative")
    if available_capacity_kw <= 0:
        raise ValueError("available capacity must be positive")
    if minimum_continuous_capacity_kw is not None:
        if minimum_continuous_capacity_kw <= 0:
            raise ValueError("minimum continuous capacity must be positive")
        if minimum_continuous_capacity_kw > available_capacity_kw:
            raise ValueError("minimum continuous capacity cannot exceed available capacity")

    load_ratio = required_capacity_kw / available_capacity_kw
    minimum_ratio = (
        None
        if minimum_continuous_capacity_kw is None
        else minimum_continuous_capacity_kw / available_capacity_kw
    )

    if required_capacity_kw == 0:
        return PartLoadRuntimeState(
            required_capacity_kw,
            available_capacity_kw,
            minimum_continuous_capacity_kw,
            load_ratio,
            minimum_ratio,
            OFF,
            False,
            False,
            None,
        )

    if required_capacity_kw > available_capacity_kw:
        return PartLoadRuntimeState(
            required_capacity_kw,
            available_capacity_kw,
            minimum_continuous_capacity_kw,
            load_ratio,
            minimum_ratio,
            CAPACITY_SHORTFALL,
            False,
            False,
            None,
        )

    if minimum_continuous_capacity_kw is None:
        return PartLoadRuntimeState(
            required_capacity_kw,
            available_capacity_kw,
            None,
            load_ratio,
            None,
            MODULATION_FLOOR_REQUIRED,
            False,
            False,
            MIN_MOD_COVERAGE_REQUIRED,
        )

    if required_capacity_kw < minimum_continuous_capacity_kw:
        return PartLoadRuntimeState(
            required_capacity_kw,
            available_capacity_kw,
            minimum_continuous_capacity_kw,
            load_ratio,
            minimum_ratio,
            CYCLING,
            True,
            False,
            NUMERIC_CYCLING_METHOD_REQUIRED,
        )

    return PartLoadRuntimeState(
        required_capacity_kw,
        available_capacity_kw,
        minimum_continuous_capacity_kw,
        load_ratio,
        minimum_ratio,
        CONTINUOUS,
        False,
        False,
        None,
    )


def runtime_boundary() -> tuple[str, ...]:
    return (
        "MINIMUM_MODULATION_IS_EXPLICIT_INPUT",
        "CYCLING_STATE_PRECEDES_DEGRADATION_APPLICATION",
        "CERTIFIED_CDH_NOT_DIRECT_HOURLY_MULTIPLIER",
        "NO_COP_TIMES_CDH_SHORTCUT",
        NUMERIC_CYCLING_METHOD_REQUIRED,
    )
