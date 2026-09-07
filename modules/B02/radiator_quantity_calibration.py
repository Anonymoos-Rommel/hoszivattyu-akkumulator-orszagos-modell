"""B02-P49 bounded radiator/emitter quantity calibration.

P49 admits exact public quantity observations only inside their source-native
cohorts. It separates current dwelling stock from implemented retrofit
portfolios, exact counts from approximate counts, and cohort quantities from
national P42 authority.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


P42_CLAIMS = (
    "RADIATOR_STOCK_DWELLING_COUNT",
    "RADIATOR_STOCK_UNIT_COUNT",
    "RADIATOR_TYPE_SIZE_DISTRIBUTION",
    "RADIATOR_REUSE_UPGRADE_REQUIREMENT",
    "RADIATOR_REPLACEMENT_QUANTITY",
)

ALLOWED_ROLES = {
    "CURRENT_DWELLING_STOCK",
    "IMPLEMENTED_RETROFIT_PORTFOLIO",
}
ALLOWED_PRECISION = {"NONE", "EXACT", "APPROXIMATE"}


@dataclass(frozen=True)
class RadiatorQuantityCalibrationCandidate:
    anchor_id: str
    country: str
    role: str
    dwelling_count: int
    building_count_primary: Optional[int]
    building_count_crosscheck: Optional[int]
    radiator_unit_count: Optional[int]
    cost_allocator_count: Optional[int]
    reported_replacement_radiator_count: Optional[int]
    replacement_count_precision: str
    radiator_type: str
    per_emitter_binding: bool
    same_cohort_binding: bool
    residential_only_numerator_proven: bool
    current_stock_observation: bool
    implemented_works: bool
    primary_source_url: str
    crosscheck_source_url: str
    reproducible_binding: bool


@dataclass(frozen=True)
class RadiatorQuantityCalibrationDecision:
    status: str
    reasons: tuple[str, ...]
    emitter_position_count: Optional[int]
    radiators_per_dwelling: Optional[float]
    ratio_status: str
    exact_replacement_radiator_count: Optional[int]
    replacement_count_status: str
    building_count_status: str
    p42_national_authority: bool
    unresolved_p42_claims: tuple[str, ...]


def _valid_optional_nonnegative(value: Optional[int]) -> bool:
    return value is None or (
        isinstance(value, int) and not isinstance(value, bool) and value >= 0
    )


def _valid_positive_int(value: int) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value > 0


def assess_radiator_quantity_calibration(
    candidate: RadiatorQuantityCalibrationCandidate,
) -> RadiatorQuantityCalibrationDecision:
    """Validate one bounded quantity anchor without extrapolating it."""

    reasons: list[str] = []
    if not candidate.anchor_id.strip():
        reasons.append("NO_ANCHOR_ID")
    if candidate.country != "HU":
        reasons.append("NOT_HUNGARY")
    if candidate.role not in ALLOWED_ROLES:
        reasons.append("INVALID_ROLE")
    if not _valid_positive_int(candidate.dwelling_count):
        reasons.append("INVALID_DWELLING_COUNT")
    if candidate.replacement_count_precision not in ALLOWED_PRECISION:
        reasons.append("INVALID_REPLACEMENT_PRECISION")
    if not candidate.same_cohort_binding:
        reasons.append("COUNTS_NOT_BOUND_TO_SAME_COHORT")
    if not candidate.primary_source_url.strip():
        reasons.append("NO_PRIMARY_SOURCE")
    if not candidate.reproducible_binding:
        reasons.append("NO_REPRODUCIBLE_BINDING")

    for value, reason in (
        (candidate.building_count_primary, "INVALID_PRIMARY_BUILDING_COUNT"),
        (candidate.building_count_crosscheck, "INVALID_CROSSCHECK_BUILDING_COUNT"),
        (candidate.radiator_unit_count, "INVALID_RADIATOR_UNIT_COUNT"),
        (candidate.cost_allocator_count, "INVALID_COST_ALLOCATOR_COUNT"),
        (
            candidate.reported_replacement_radiator_count,
            "INVALID_REPLACEMENT_RADIATOR_COUNT",
        ),
    ):
        if not _valid_optional_nonnegative(value):
            reasons.append(reason)

    if candidate.radiator_unit_count is None and candidate.cost_allocator_count is None:
        reasons.append("NO_EMITTER_QUANTITY")
    if candidate.cost_allocator_count is not None and not candidate.per_emitter_binding:
        reasons.append("COST_ALLOCATOR_NOT_BOUND_PER_EMITTER")
    if (
        candidate.radiator_unit_count is not None
        and candidate.cost_allocator_count is not None
        and candidate.per_emitter_binding
        and candidate.radiator_unit_count != candidate.cost_allocator_count
    ):
        reasons.append("RADIATOR_ALLOCATOR_COUNT_MISMATCH")
    if (
        candidate.replacement_count_precision == "NONE"
        and candidate.reported_replacement_radiator_count is not None
    ):
        reasons.append("REPLACEMENT_COUNT_WITHOUT_PRECISION")
    if (
        candidate.replacement_count_precision in {"EXACT", "APPROXIMATE"}
        and candidate.reported_replacement_radiator_count is None
    ):
        reasons.append("REPLACEMENT_PRECISION_WITHOUT_COUNT")
    if candidate.role == "CURRENT_DWELLING_STOCK" and not candidate.current_stock_observation:
        reasons.append("CURRENT_ROLE_WITHOUT_CURRENT_STOCK_EVIDENCE")
    if candidate.role == "IMPLEMENTED_RETROFIT_PORTFOLIO" and not candidate.implemented_works:
        reasons.append("IMPLEMENTED_ROLE_WITHOUT_IMPLEMENTED_WORKS")

    qualified = not reasons
    emitter_position_count: Optional[int] = None
    if qualified:
        if candidate.radiator_unit_count is not None:
            emitter_position_count = candidate.radiator_unit_count
        elif candidate.cost_allocator_count is not None and candidate.per_emitter_binding:
            emitter_position_count = candidate.cost_allocator_count

    ratio_status = "Q"
    radiators_per_dwelling: Optional[float] = None
    if qualified and candidate.role == "CURRENT_DWELLING_STOCK":
        if (
            candidate.radiator_unit_count is not None
            and candidate.residential_only_numerator_proven
        ):
            radiators_per_dwelling = (
                candidate.radiator_unit_count / candidate.dwelling_count
            )
            ratio_status = "QUALIFIED_CURRENT_DWELLING_RATIO"
        else:
            ratio_status = "Q_NO_RESIDENTIAL_ONLY_RADIATOR_NUMERATOR"
    elif qualified and candidate.role == "IMPLEMENTED_RETROFIT_PORTFOLIO":
        # A retrofit-portfolio device count may include non-dwelling or common
        # positions unless the source explicitly proves a residential-only
        # numerator. Do not manufacture a current residential stock ratio.
        ratio_status = "Q_PORTFOLIO_NOT_CURRENT_RESIDENTIAL_STOCK_RATIO"

    exact_replacement_radiator_count: Optional[int] = None
    if not qualified or candidate.replacement_count_precision == "NONE":
        replacement_count_status = "Q" if not qualified else "NOT_REPORTED"
    elif candidate.replacement_count_precision == "EXACT":
        exact_replacement_radiator_count = candidate.reported_replacement_radiator_count
        replacement_count_status = "QUALIFIED_EXACT_BOUNDED_REPLACEMENT_COUNT"
    else:
        replacement_count_status = "APPROXIMATE_REFERENCE_ONLY"

    if candidate.building_count_primary is None:
        building_count_status = "Q_NO_PRIMARY_BUILDING_COUNT"
    elif candidate.building_count_crosscheck is None:
        building_count_status = "PRIMARY_ONLY"
    elif candidate.building_count_primary == candidate.building_count_crosscheck:
        building_count_status = "CONSISTENT"
    else:
        building_count_status = "Q_SOURCE_VERSION_CONFLICT"

    return RadiatorQuantityCalibrationDecision(
        status="QUALIFIED_BOUNDED_QUANTITY_CALIBRATION" if qualified else "Q",
        reasons=tuple(reasons),
        emitter_position_count=emitter_position_count,
        radiators_per_dwelling=radiators_per_dwelling,
        ratio_status=ratio_status,
        exact_replacement_radiator_count=exact_replacement_radiator_count,
        replacement_count_status=replacement_count_status,
        building_count_status=building_count_status,
        p42_national_authority=False,
        unresolved_p42_claims=P42_CLAIMS,
    )
