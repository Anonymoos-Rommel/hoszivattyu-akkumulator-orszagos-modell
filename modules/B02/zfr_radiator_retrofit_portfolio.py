"""B02-P53 ZFR implemented residential radiator-retrofit portfolio contract.

P53 materializes bounded, implemented ZFR-TAV/2019 and ZFR-EMI-TAV/2020
portfolio quantities together with the official before/after radiator-documentation
schema. It deliberately does not promote contractor portfolio ratios into national
P42 weights or pretend that the still-missing filled per-radiator before/after table
has been recovered.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable


class ZfrRadiatorRetrofitPortfolioError(ValueError):
    """Raised when P53 evidence is malformed or overstated."""


OFFICIAL_PROGRAM_RULE = "OFFICIAL_PROGRAM_RULE"
IMPLEMENTED_CONTRACTOR_PORTFOLIO = "IMPLEMENTED_CONTRACTOR_PORTFOLIO"
IMPLEMENTATION_SERVICE_REPORT = "IMPLEMENTATION_SERVICE_REPORT"

DWELLING_COUNT = "DWELLING_COUNT"
NEW_RADIATOR_COUNT = "NEW_RADIATOR_COUNT"
COST_ALLOCATOR_COUNT = "COST_ALLOCATOR_COUNT"
BUILDING_COUNT = "BUILDING_COUNT"
ORIGINAL_NEW_MATRIX_REQUIRED = "ORIGINAL_NEW_MATRIX_REQUIRED"
ITEMIZED_DWELLING_SURVEY_EXECUTED = "ITEMIZED_DWELLING_SURVEY_EXECUTED"
RADIATOR_REPLACEMENT_OPTIONAL = "RADIATOR_REPLACEMENT_OPTIONAL"

EXACT = "EXACT"
REPORTED_INTEGER = "REPORTED_INTEGER"
APPROXIMATE = "APPROXIMATE"
BOOLEAN = "BOOLEAN"

_ALLOWED_ROLES = {
    OFFICIAL_PROGRAM_RULE,
    IMPLEMENTED_CONTRACTOR_PORTFOLIO,
    IMPLEMENTATION_SERVICE_REPORT,
}
_ALLOWED_METRICS = {
    DWELLING_COUNT,
    NEW_RADIATOR_COUNT,
    COST_ALLOCATOR_COUNT,
    BUILDING_COUNT,
    ORIGINAL_NEW_MATRIX_REQUIRED,
    ITEMIZED_DWELLING_SURVEY_EXECUTED,
    RADIATOR_REPLACEMENT_OPTIONAL,
}
_BOOLEAN_METRICS = {
    ORIGINAL_NEW_MATRIX_REQUIRED,
    ITEMIZED_DWELLING_SURVEY_EXECUTED,
    RADIATOR_REPLACEMENT_OPTIONAL,
}
_ALLOWED_PRECISION = {EXACT, REPORTED_INTEGER, APPROXIMATE, BOOLEAN}


@dataclass(frozen=True)
class ZfrRetrofitEvidence:
    evidence_id: str
    source_version: str
    source_role: str
    metric: str
    value: float
    unit: str
    precision: str
    residential_scope: bool
    implemented_scope: bool
    source_url: str
    source_locator: str
    source_date: str
    national_p42_authority_claimed: bool = False
    exact_before_after_pair_authority_claimed: bool = False
    programme_use_claimed: bool = False


@dataclass(frozen=True)
class ZfrRetrofitPortfolioSummary:
    dwelling_count: int
    new_radiators_reported: int
    cost_allocators_reported: int
    new_radiators_approximate: bool
    building_count: int | None
    building_count_conflict: bool
    reported_building_counts: tuple[int, ...]
    official_before_after_matrix_schema: bool
    itemized_dwelling_survey_executed: bool
    radiator_replacement_optional: bool
    new_radiators_per_dwelling: float
    cost_allocators_per_dwelling: float
    replacement_intensity_proxy: float
    exact_before_after_pair_recovered: bool = False
    current_installed_stock_census: bool = False
    representative_national_weight: bool = False
    national_p42_authority: bool = False
    programme_use_allowed: bool = False


def validate_zfr_retrofit_evidence(row: ZfrRetrofitEvidence) -> str:
    """Validate one bounded P53 source-native evidence row."""

    if not row.evidence_id.strip() or not row.source_version.strip():
        raise ZfrRadiatorRetrofitPortfolioError("MISSING_EVIDENCE_OR_SOURCE_VERSION")
    if row.source_role not in _ALLOWED_ROLES:
        raise ZfrRadiatorRetrofitPortfolioError("UNSUPPORTED_SOURCE_ROLE")
    if row.metric not in _ALLOWED_METRICS:
        raise ZfrRadiatorRetrofitPortfolioError("UNSUPPORTED_METRIC")
    if row.precision not in _ALLOWED_PRECISION:
        raise ZfrRadiatorRetrofitPortfolioError("UNSUPPORTED_PRECISION")
    if not row.residential_scope:
        raise ZfrRadiatorRetrofitPortfolioError("NON_RESIDENTIAL_ROW_FORBIDDEN")
    if row.value <= 0:
        raise ZfrRadiatorRetrofitPortfolioError("NON_POSITIVE_EVIDENCE_VALUE")
    if not row.unit.strip():
        raise ZfrRadiatorRetrofitPortfolioError("MISSING_UNIT")
    if not row.source_url.startswith("https://"):
        raise ZfrRadiatorRetrofitPortfolioError("SOURCE_URL_NOT_HTTPS")
    if not row.source_locator.strip() or not row.source_date.strip():
        raise ZfrRadiatorRetrofitPortfolioError("MISSING_SOURCE_LOCATOR_OR_DATE")

    if row.metric in _BOOLEAN_METRICS:
        if row.value != 1 or row.unit != "BOOL" or row.precision != BOOLEAN:
            raise ZfrRadiatorRetrofitPortfolioError("BOOLEAN_METRIC_ENCODING_INVALID")

    if row.metric == ORIGINAL_NEW_MATRIX_REQUIRED:
        if row.source_role != OFFICIAL_PROGRAM_RULE or row.implemented_scope:
            raise ZfrRadiatorRetrofitPortfolioError("PROGRAM_SCHEMA_ROLE_MISMATCH")
    elif row.source_role == OFFICIAL_PROGRAM_RULE:
        raise ZfrRadiatorRetrofitPortfolioError("OFFICIAL_RULE_CANNOT_CLAIM_IMPLEMENTED_QUANTITY")

    if row.metric in {DWELLING_COUNT, NEW_RADIATOR_COUNT, COST_ALLOCATOR_COUNT, BUILDING_COUNT}:
        if not row.implemented_scope:
            raise ZfrRadiatorRetrofitPortfolioError("IMPLEMENTED_QUANTITY_REQUIRES_IMPLEMENTED_SCOPE")

    if row.national_p42_authority_claimed:
        raise ZfrRadiatorRetrofitPortfolioError("CONTRACTOR_PORTFOLIO_IS_NOT_NATIONAL_P42_AUTHORITY")
    if row.exact_before_after_pair_authority_claimed:
        raise ZfrRadiatorRetrofitPortfolioError("FILLED_BEFORE_AFTER_PAIR_TABLE_NOT_RECOVERED")
    if row.programme_use_claimed:
        raise ZfrRadiatorRetrofitPortfolioError("BOUNDED_PORTFOLIO_DOES_NOT_SELF_AUTHORIZE_PROGRAMME_USE")

    return "QUALIFIED_BOUNDED_ZFR_RETROFIT_EVIDENCE"


def _values(rows: list[ZfrRetrofitEvidence], metric: str) -> list[ZfrRetrofitEvidence]:
    return [row for row in rows if row.metric == metric]


def _stable_integer(rows: list[ZfrRetrofitEvidence], metric: str) -> int:
    selected = _values(rows, metric)
    if not selected:
        raise ZfrRadiatorRetrofitPortfolioError(f"MISSING_{metric}")
    values = {int(row.value) for row in selected}
    if len(values) != 1:
        raise ZfrRadiatorRetrofitPortfolioError(f"CONFLICTING_{metric}")
    return next(iter(values))


def summarize_zfr_retrofit_portfolio(
    rows: Iterable[ZfrRetrofitEvidence],
) -> ZfrRetrofitPortfolioSummary:
    """Summarize bounded implemented ZFR evidence without national promotion."""

    materialized = list(rows)
    if not materialized:
        raise ZfrRadiatorRetrofitPortfolioError("EMPTY_EVIDENCE_SET")

    for row in materialized:
        validate_zfr_retrofit_evidence(row)

    evidence_ids = [row.evidence_id for row in materialized]
    if len(evidence_ids) != len(set(evidence_ids)):
        raise ZfrRadiatorRetrofitPortfolioError("DUPLICATE_EVIDENCE_ROW")

    dwelling_count = _stable_integer(materialized, DWELLING_COUNT)
    new_radiators = _stable_integer(materialized, NEW_RADIATOR_COUNT)
    cost_allocators = _stable_integer(materialized, COST_ALLOCATOR_COUNT)

    new_radiator_rows = _values(materialized, NEW_RADIATOR_COUNT)
    new_radiators_approximate = any(row.precision == APPROXIMATE for row in new_radiator_rows)
    if not new_radiators_approximate:
        raise ZfrRadiatorRetrofitPortfolioError("NEW_RADIATOR_COUNT_MUST_RETAIN_APPROXIMATE_PRECISION")

    building_counts = tuple(sorted({int(row.value) for row in _values(materialized, BUILDING_COUNT)}))
    if not building_counts:
        raise ZfrRadiatorRetrofitPortfolioError("MISSING_BUILDING_COUNT_SOURCE_VERSIONS")
    building_count_conflict = len(building_counts) > 1
    building_count = None if building_count_conflict else building_counts[0]

    matrix_schema = bool(_values(materialized, ORIGINAL_NEW_MATRIX_REQUIRED))
    itemized_survey = bool(_values(materialized, ITEMIZED_DWELLING_SURVEY_EXECUTED))
    replacement_optional = bool(_values(materialized, RADIATOR_REPLACEMENT_OPTIONAL))
    if not matrix_schema:
        raise ZfrRadiatorRetrofitPortfolioError("MISSING_OFFICIAL_BEFORE_AFTER_SCHEMA")
    if not itemized_survey:
        raise ZfrRadiatorRetrofitPortfolioError("MISSING_ITEMIZED_DWELLING_SURVEY_EVIDENCE")

    return ZfrRetrofitPortfolioSummary(
        dwelling_count=dwelling_count,
        new_radiators_reported=new_radiators,
        cost_allocators_reported=cost_allocators,
        new_radiators_approximate=True,
        building_count=building_count,
        building_count_conflict=building_count_conflict,
        reported_building_counts=building_counts,
        official_before_after_matrix_schema=matrix_schema,
        itemized_dwelling_survey_executed=itemized_survey,
        radiator_replacement_optional=replacement_optional,
        new_radiators_per_dwelling=new_radiators / dwelling_count,
        cost_allocators_per_dwelling=cost_allocators / dwelling_count,
        replacement_intensity_proxy=new_radiators / cost_allocators,
    )


def portfolio_grants_exact_before_after_pair_authority(
    _: ZfrRetrofitPortfolioSummary,
) -> bool:
    """Aggregate execution counts do not recover the filled per-radiator pair table."""

    return False


def portfolio_grants_national_p42_authority(
    _: ZfrRetrofitPortfolioSummary,
) -> bool:
    """A contractor portfolio cannot self-authorize a national stock weight."""

    return False
