"""B02-P44 bounded public panel-radiator quantity anchors.

This module intentionally computes only source-bounded ratios.  It does not
extrapolate any panel/district-heating observation to the national occupied
stock and it cannot authorize the five national P42 quantity claims.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import isfinite
from typing import Optional


ALLOWED_EVIDENCE = {"OBS", "DER"}


@dataclass(frozen=True)
class BoundedQuantityAnchor:
    anchor_id: str
    source_id: str
    evidence_status: str
    scope_boundary: str
    dwelling_count: Optional[float] = None
    radiator_unit_count: Optional[float] = None
    cost_allocator_count: Optional[float] = None
    replacement_radiator_count: Optional[float] = None
    reproducible_binding: bool = False


@dataclass(frozen=True)
class BoundedQuantityDecision:
    status: str
    reasons: tuple[str, ...]
    radiators_per_dwelling: Optional[float]
    cost_allocators_per_dwelling: Optional[float]
    replacement_radiators_per_dwelling: Optional[float]
    replacement_share_of_allocator_positions: Optional[float]
    national_p42_authority: bool = False


def _valid_optional_count(value: Optional[float]) -> bool:
    return value is None or (isfinite(value) and value >= 0)


def _ratio(numerator: Optional[float], denominator: Optional[float]) -> Optional[float]:
    if numerator is None or denominator is None or denominator <= 0:
        return None
    return numerator / denominator


def assess_bounded_quantity_anchor(candidate: BoundedQuantityAnchor) -> BoundedQuantityDecision:
    """Validate a public bounded quantity anchor without national promotion."""

    reasons: list[str] = []
    if not candidate.anchor_id.strip():
        reasons.append("NO_ANCHOR_ID")
    if not candidate.source_id.strip():
        reasons.append("NO_SOURCE_ID")
    if candidate.evidence_status not in ALLOWED_EVIDENCE:
        reasons.append("INVALID_EVIDENCE_STATUS")
    if not candidate.scope_boundary.strip():
        reasons.append("NO_SCOPE_BOUNDARY")
    if not candidate.reproducible_binding:
        reasons.append("NO_REPRODUCIBLE_BINDING")

    for value, reason in (
        (candidate.dwelling_count, "INVALID_DWELLING_COUNT"),
        (candidate.radiator_unit_count, "INVALID_RADIATOR_UNIT_COUNT"),
        (candidate.cost_allocator_count, "INVALID_COST_ALLOCATOR_COUNT"),
        (candidate.replacement_radiator_count, "INVALID_REPLACEMENT_RADIATOR_COUNT"),
    ):
        if not _valid_optional_count(value):
            reasons.append(reason)

    if all(
        value is None
        for value in (
            candidate.dwelling_count,
            candidate.radiator_unit_count,
            candidate.cost_allocator_count,
            candidate.replacement_radiator_count,
        )
    ):
        reasons.append("NO_NUMERIC_QUANTITY")

    status = "QUALIFIED" if not reasons else "Q"
    return BoundedQuantityDecision(
        status=status,
        reasons=tuple(reasons),
        radiators_per_dwelling=_ratio(candidate.radiator_unit_count, candidate.dwelling_count),
        cost_allocators_per_dwelling=_ratio(candidate.cost_allocator_count, candidate.dwelling_count),
        replacement_radiators_per_dwelling=_ratio(candidate.replacement_radiator_count, candidate.dwelling_count),
        replacement_share_of_allocator_positions=_ratio(
            candidate.replacement_radiator_count, candidate.cost_allocator_count
        ),
        national_p42_authority=False,
    )
