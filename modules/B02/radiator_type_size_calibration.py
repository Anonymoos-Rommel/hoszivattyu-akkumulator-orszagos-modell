"""B02-P50 bounded radiator type/size and low-temperature calibration.

P50 admits only source-bounded type/size observations and engineering
performance controls. It never promotes a household, one-pipe circuit,
property listing, or programme schema into a national radiator-stock
composition claim.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import isfinite
from typing import Optional, Sequence


P42_CLAIMS = (
    "RADIATOR_STOCK_DWELLING_COUNT",
    "RADIATOR_STOCK_UNIT_COUNT",
    "RADIATOR_TYPE_SIZE_DISTRIBUTION",
    "RADIATOR_REUSE_UPGRADE_REQUIREMENT",
    "RADIATOR_REPLACEMENT_QUANTITY",
)

ALLOWED_ROLES = {
    "CURRENT_RESIDENTIAL_WHOLE_DWELLING",
    "DOCUMENTED_RESIDENTIAL_PARTIAL_CIRCUIT",
    "NON_RESIDENTIAL_TECHNICAL_CONTROL",
}
ALLOWED_SOURCE_QUALITY = {
    "PUBLIC_SELF_REPORT",
    "PUBLIC_PROPERTY_LISTING",
    "PEER_REVIEWED_ENGINEERING_CASE",
    "OFFICIAL_PROJECT_TABLE",
}
ALLOWED_LENGTH_SEMANTICS = {
    "NOT_REPORTED",
    "SOURCE_REPORTED_DIMENSION",
    "SOURCE_NATIVE_SIZE_TOKEN",
}
ALLOWED_OUTPUT_SCOPES = {
    "NOT_REPORTED",
    "RADIATOR_ONLY",
    "RADIATOR_PLUS_PIPE",
}


@dataclass(frozen=True)
class RadiatorTypeSizeCandidate:
    anchor_id: str
    cohort_id: str
    role: str
    source_quality: str
    source_url: str
    exact_locator: str
    radiator_type_source_native: str
    unit_count: int
    residential_scope: bool
    current_stock_observation: bool
    whole_dwelling_inventory: bool
    same_cohort_binding: bool
    reproducible_binding: bool
    dwelling_count: Optional[int] = None
    floor_area_m2: Optional[float] = None
    height_mm: Optional[float] = None
    length_mm: Optional[float] = None
    length_semantics: str = "NOT_REPORTED"
    source_native_size_token: str = ""
    output_at_target_w: Optional[float] = None
    target_supply_temp_c: Optional[float] = None
    room_heat_loss_after_envelope_w: Optional[float] = None
    output_scope: str = "NOT_REPORTED"
    source_intervention_conclusion: str = ""


@dataclass(frozen=True)
class RadiatorTypeSizeDecision:
    status: str
    reasons: tuple[str, ...]
    type_size_observation_qualified: bool
    dwelling_ratio_qualified: bool
    radiators_per_dwelling: Optional[float]
    radiators_per_100m2: Optional[float]
    target_temp_performance_qualified: bool
    room_capacity_margin_w: Optional[float]
    national_p42_authority: bool
    unresolved_p42_claims: tuple[str, ...]


def _valid_positive_int(value: object) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value > 0


def _valid_optional_positive_int(value: object) -> bool:
    return value is None or _valid_positive_int(value)


def _valid_optional_positive_number(value: object) -> bool:
    if value is None or isinstance(value, bool):
        return value is None
    return isinstance(value, (int, float)) and isfinite(value) and value > 0


def assess_radiator_type_size(candidate: RadiatorTypeSizeCandidate) -> RadiatorTypeSizeDecision:
    """Validate one bounded type/size observation without national promotion."""

    reasons: list[str] = []

    if not candidate.anchor_id.strip():
        reasons.append("NO_ANCHOR_ID")
    if not candidate.cohort_id.strip():
        reasons.append("NO_COHORT_ID")
    if candidate.role not in ALLOWED_ROLES:
        reasons.append("INVALID_ROLE")
    if candidate.source_quality not in ALLOWED_SOURCE_QUALITY:
        reasons.append("INVALID_SOURCE_QUALITY")
    if not candidate.source_url.strip():
        reasons.append("NO_SOURCE_URL")
    if not candidate.exact_locator.strip():
        reasons.append("NO_EXACT_LOCATOR")
    if not candidate.radiator_type_source_native.strip():
        reasons.append("NO_SOURCE_NATIVE_RADIATOR_TYPE")
    if not _valid_positive_int(candidate.unit_count):
        reasons.append("INVALID_UNIT_COUNT")
    if not _valid_optional_positive_int(candidate.dwelling_count):
        reasons.append("INVALID_DWELLING_COUNT")
    if not _valid_optional_positive_number(candidate.floor_area_m2):
        reasons.append("INVALID_FLOOR_AREA")
    if not _valid_optional_positive_number(candidate.height_mm):
        reasons.append("INVALID_HEIGHT")
    if not _valid_optional_positive_number(candidate.length_mm):
        reasons.append("INVALID_LENGTH")
    if candidate.length_semantics not in ALLOWED_LENGTH_SEMANTICS:
        reasons.append("INVALID_LENGTH_SEMANTICS")
    if candidate.output_scope not in ALLOWED_OUTPUT_SCOPES:
        reasons.append("INVALID_OUTPUT_SCOPE")
    if not candidate.same_cohort_binding:
        reasons.append("NO_SAME_COHORT_BINDING")
    if not candidate.reproducible_binding:
        reasons.append("NO_REPRODUCIBLE_BINDING")

    if candidate.role.startswith("CURRENT_RESIDENTIAL") and not candidate.residential_scope:
        reasons.append("RESIDENTIAL_ROLE_WITHOUT_RESIDENTIAL_SCOPE")
    if candidate.role == "DOCUMENTED_RESIDENTIAL_PARTIAL_CIRCUIT" and not candidate.residential_scope:
        reasons.append("RESIDENTIAL_CIRCUIT_WITHOUT_RESIDENTIAL_SCOPE")
    if candidate.role == "NON_RESIDENTIAL_TECHNICAL_CONTROL" and candidate.residential_scope:
        reasons.append("NON_RESIDENTIAL_ROLE_WITH_RESIDENTIAL_SCOPE")

    if candidate.role == "CURRENT_RESIDENTIAL_WHOLE_DWELLING":
        if not candidate.current_stock_observation:
            reasons.append("CURRENT_ROLE_WITHOUT_CURRENT_OBSERVATION")
        if not candidate.whole_dwelling_inventory:
            reasons.append("WHOLE_DWELLING_ROLE_WITHOUT_COMPLETE_INVENTORY")
        if candidate.dwelling_count is None:
            reasons.append("WHOLE_DWELLING_ROLE_WITHOUT_DWELLING_COUNT")
    elif candidate.whole_dwelling_inventory:
        reasons.append("WHOLE_DWELLING_FLAG_OUTSIDE_WHOLE_DWELLING_ROLE")

    if candidate.length_mm is not None and candidate.length_semantics == "NOT_REPORTED":
        reasons.append("LENGTH_WITHOUT_SEMANTICS")
    if candidate.length_mm is None and candidate.length_semantics == "SOURCE_REPORTED_DIMENSION":
        reasons.append("REPORTED_LENGTH_SEMANTICS_WITHOUT_LENGTH")
    if candidate.source_native_size_token and candidate.length_semantics != "SOURCE_NATIVE_SIZE_TOKEN":
        reasons.append("SIZE_TOKEN_WITH_WRONG_SEMANTICS")

    performance_values = (
        candidate.output_at_target_w,
        candidate.target_supply_temp_c,
        candidate.room_heat_loss_after_envelope_w,
    )
    any_performance = any(value is not None for value in performance_values)
    all_performance = all(value is not None for value in performance_values)
    if any_performance and not all_performance:
        reasons.append("PARTIAL_TARGET_TEMP_PERFORMANCE_TUPLE")
    for value, reason in (
        (candidate.output_at_target_w, "INVALID_TARGET_OUTPUT"),
        (candidate.target_supply_temp_c, "INVALID_TARGET_SUPPLY_TEMPERATURE"),
        (candidate.room_heat_loss_after_envelope_w, "INVALID_POST_ENVELOPE_HEAT_LOSS"),
    ):
        if not _valid_optional_positive_number(value):
            reasons.append(reason)
    if all_performance and candidate.output_scope == "NOT_REPORTED":
        reasons.append("TARGET_PERFORMANCE_WITHOUT_OUTPUT_SCOPE")

    status = "QUALIFIED_BOUNDED_TYPE_SIZE_CALIBRATION" if not reasons else "Q"
    qualified = status != "Q"

    dwelling_ratio_qualified = (
        qualified
        and candidate.role == "CURRENT_RESIDENTIAL_WHOLE_DWELLING"
        and candidate.whole_dwelling_inventory
        and candidate.dwelling_count is not None
    )
    radiators_per_dwelling = (
        candidate.unit_count / candidate.dwelling_count
        if dwelling_ratio_qualified and candidate.dwelling_count
        else None
    )
    radiators_per_100m2 = (
        candidate.unit_count / candidate.floor_area_m2 * 100
        if dwelling_ratio_qualified and candidate.floor_area_m2
        else None
    )

    performance_qualified = qualified and all_performance
    capacity_margin = (
        float(candidate.output_at_target_w) - float(candidate.room_heat_loss_after_envelope_w)
        if performance_qualified
        else None
    )

    return RadiatorTypeSizeDecision(
        status=status,
        reasons=tuple(reasons),
        type_size_observation_qualified=qualified,
        dwelling_ratio_qualified=dwelling_ratio_qualified,
        radiators_per_dwelling=radiators_per_dwelling,
        radiators_per_100m2=radiators_per_100m2,
        target_temp_performance_qualified=performance_qualified,
        room_capacity_margin_w=capacity_margin,
        national_p42_authority=False,
        unresolved_p42_claims=P42_CLAIMS,
    )


def bounded_type_share(
    candidates: Sequence[RadiatorTypeSizeCandidate],
) -> dict[str, float]:
    """Return source-native type shares for one exact bounded cohort only.

    The helper deliberately refuses cross-cohort pooling. It is a calibration
    surface, not a weighting or national-stock estimator.
    """

    if not candidates:
        raise ValueError("EMPTY_COHORT")
    cohort_ids = {candidate.cohort_id for candidate in candidates}
    if len(cohort_ids) != 1:
        raise ValueError("CROSS_COHORT_POOLING_FORBIDDEN")

    decisions = [assess_radiator_type_size(candidate) for candidate in candidates]
    if any(decision.status == "Q" for decision in decisions):
        raise ValueError("UNQUALIFIED_CANDIDATE_IN_COHORT")

    total = sum(candidate.unit_count for candidate in candidates)
    by_type: dict[str, int] = {}
    for candidate in candidates:
        by_type[candidate.radiator_type_source_native] = (
            by_type.get(candidate.radiator_type_source_native, 0) + candidate.unit_count
        )
    return {key: value / total for key, value in sorted(by_type.items())}
