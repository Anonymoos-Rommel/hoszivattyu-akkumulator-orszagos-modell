"""B02-P45 bounded public detached-house hydronic radiator anchors.

This module validates only source-bounded household/reference anchors. It does
not extrapolate any public listing, installer case, or engineering example to
the national occupied stock and it cannot authorize the five national P42
quantity claims.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import isfinite
from typing import Optional


ALLOWED_EVIDENCE = {"OBS", "DER"}
ALLOWED_SOURCE_QUALITY = {"PUBLIC_LISTING", "IMPLEMENTED_REFERENCE", "ENGINEERING_GUIDANCE"}


@dataclass(frozen=True)
class DetachedHydronicAnchor:
    anchor_id: str
    source_id: str
    evidence_status: str
    source_quality: str
    scope_boundary: str
    floor_area_m2: Optional[float] = None
    dwelling_count: Optional[float] = None
    radiator_unit_count: Optional[float] = None
    replacement_radiator_count: Optional[float] = None
    radiator_type: str = ""
    generator_type: str = ""
    technical_control: str = ""
    reproducible_binding: bool = False


@dataclass(frozen=True)
class DetachedHydronicDecision:
    status: str
    reasons: tuple[str, ...]
    radiators_per_dwelling: Optional[float]
    radiators_per_100m2: Optional[float]
    replacement_radiators_per_dwelling: Optional[float]
    national_p42_authority: bool = False


def _valid_optional_count(value: Optional[float]) -> bool:
    return value is None or (isfinite(value) and value >= 0)


def _ratio(numerator: Optional[float], denominator: Optional[float]) -> Optional[float]:
    if numerator is None or denominator is None or denominator <= 0:
        return None
    return numerator / denominator


def assess_detached_hydronic_anchor(candidate: DetachedHydronicAnchor) -> DetachedHydronicDecision:
    """Validate a bounded detached-house hydronic anchor without national promotion."""

    reasons: list[str] = []
    if not candidate.anchor_id.strip():
        reasons.append("NO_ANCHOR_ID")
    if not candidate.source_id.strip():
        reasons.append("NO_SOURCE_ID")
    if candidate.evidence_status not in ALLOWED_EVIDENCE:
        reasons.append("INVALID_EVIDENCE_STATUS")
    if candidate.source_quality not in ALLOWED_SOURCE_QUALITY:
        reasons.append("INVALID_SOURCE_QUALITY")
    if not candidate.scope_boundary.strip():
        reasons.append("NO_SCOPE_BOUNDARY")
    if not candidate.reproducible_binding:
        reasons.append("NO_REPRODUCIBLE_BINDING")

    for value, reason in (
        (candidate.floor_area_m2, "INVALID_FLOOR_AREA"),
        (candidate.dwelling_count, "INVALID_DWELLING_COUNT"),
        (candidate.radiator_unit_count, "INVALID_RADIATOR_UNIT_COUNT"),
        (candidate.replacement_radiator_count, "INVALID_REPLACEMENT_RADIATOR_COUNT"),
    ):
        if not _valid_optional_count(value):
            reasons.append(reason)

    if not any(
        (
            candidate.radiator_unit_count is not None,
            candidate.replacement_radiator_count is not None,
            bool(candidate.radiator_type.strip()),
            bool(candidate.technical_control.strip()),
        )
    ):
        reasons.append("NO_RADIATOR_OR_TECHNICAL_PAYLOAD")

    status = "QUALIFIED" if not reasons else "Q"
    return DetachedHydronicDecision(
        status=status,
        reasons=tuple(reasons),
        radiators_per_dwelling=_ratio(candidate.radiator_unit_count, candidate.dwelling_count),
        radiators_per_100m2=(
            _ratio(candidate.radiator_unit_count, candidate.floor_area_m2) * 100
            if candidate.radiator_unit_count is not None
            and candidate.floor_area_m2 is not None
            and candidate.floor_area_m2 > 0
            else None
        ),
        replacement_radiators_per_dwelling=_ratio(
            candidate.replacement_radiator_count, candidate.dwelling_count
        ),
        national_p42_authority=False,
    )
