"""B05-P15 certified EN 14825 Cdh evidence contract.

This module classifies published certified Cdh values. It does not implement
the B05 hourly cycling-runtime correction.
"""

from __future__ import annotations

from dataclasses import dataclass


DEFAULT_CDH_A2W = 0.9
NONDEFAULT = "CERTIFIED_NONDEFAULT_MEASUREMENT_DETERMINED_CDH"
EXACT_DEFAULT = "DEFAULT_OR_MEASURED_EQUAL_TO_DEFAULT_UNRESOLVED"


@dataclass(frozen=True)
class CdhClassification:
    value: float
    classification: str
    usable_as_product_specific_nondefault_evidence: bool
    usable_as_direct_hourly_runtime_multiplier: bool


def classify_certified_cdh(value: float, *, tolerance: float = 1e-9) -> CdhClassification:
    if not 0 < value <= 1.0:
        raise ValueError("Cdh must be within (0, 1]")
    if abs(value - DEFAULT_CDH_A2W) <= tolerance:
        return CdhClassification(
            value=value,
            classification=EXACT_DEFAULT,
            usable_as_product_specific_nondefault_evidence=False,
            usable_as_direct_hourly_runtime_multiplier=False,
        )
    return CdhClassification(
        value=value,
        classification=NONDEFAULT,
        usable_as_product_specific_nondefault_evidence=True,
        usable_as_direct_hourly_runtime_multiplier=False,
    )


def runtime_boundary() -> tuple[str, ...]:
    return (
        "CERTIFIED_CDH_NOT_DIRECT_HOURLY_MULTIPLIER",
        "PDH_NOT_MINIMUM_STABLE_MODULATION",
        "NO_CROSS_PRODUCT_GENERALIZATION",
        "EN14825_TO_B05_RUNTIME_APPLICATION_CONTRACT_REQUIRED",
    )
