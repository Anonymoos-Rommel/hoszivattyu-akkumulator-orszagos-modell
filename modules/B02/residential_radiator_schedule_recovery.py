"""B02-P52 residential radiator schedule recovery contract.

P52 materializes exact type-size-quantity rows from publicly available
residential mechanical schedules without promoting design/procurement quantities
into current installed-stock observations or national P42 authority.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from typing import Iterable


class ResidentialRadiatorScheduleError(ValueError):
    """Raised when a recovered residential schedule is overstated or malformed."""


RESIDENTIAL_BUILDING_DESIGN_SCHEDULE = "RESIDENTIAL_BUILDING_DESIGN_SCHEDULE"
RESIDENTIAL_DWELLING_DESIGN_SCHEDULE = "RESIDENTIAL_DWELLING_DESIGN_SCHEDULE"
PLANNED_NEW_INSTALLATION = "PLANNED_NEW_INSTALLATION"
PANEL_STEEL = "PANEL_STEEL"
TOWEL_RADIATOR = "TOWEL_RADIATOR"
HYBRID_RADIATOR_FLOOR = "HYBRID_RADIATOR_FLOOR"
QUALIFIED_BOUNDED_RESIDENTIAL_SCHEDULE = "QUALIFIED_BOUNDED_RESIDENTIAL_SCHEDULE"

_ALLOWED_ROLES = {
    RESIDENTIAL_BUILDING_DESIGN_SCHEDULE,
    RESIDENTIAL_DWELLING_DESIGN_SCHEDULE,
}
_ALLOWED_EMITTER_FAMILIES = {PANEL_STEEL, TOWEL_RADIATOR}


@dataclass(frozen=True)
class ResidentialRadiatorScheduleRow:
    evidence_id: str
    cohort_id: str
    coverage_id: str
    source_role: str
    installation_status: str
    residential_scope: bool
    heating_system_scope: str
    manufacturer: str
    product_family: str
    type_size_token: str
    emitter_family: str
    quantity: int
    dwelling_count_scope: int
    source_url: str
    source_locator: str
    source_date: str
    hybrid_floor_heating_present: bool
    current_installed_stock_claimed: bool = False
    pre_retrofit_stock_claimed: bool = False
    national_p42_authority_claimed: bool = False
    programme_use_claimed: bool = False


@dataclass(frozen=True)
class ResidentialRadiatorScheduleSummary:
    cohort_id: str
    dwelling_count: int
    total_radiators: int
    panel_radiators: int
    towel_radiators: int
    radiators_per_dwelling: float
    configuration_counts: dict[str, int]
    type_size_counts: dict[str, int]
    heating_system_scope: str
    national_p42_authority: bool = False
    current_stock_authority: bool = False


def validate_residential_radiator_schedule_row(
    row: ResidentialRadiatorScheduleRow,
) -> str:
    """Validate one bounded residential design/procurement schedule row."""

    if not row.evidence_id.strip():
        raise ResidentialRadiatorScheduleError("MISSING_EVIDENCE_ID")
    if not row.cohort_id.strip() or not row.coverage_id.strip():
        raise ResidentialRadiatorScheduleError("MISSING_COHORT_OR_COVERAGE_ID")
    if row.source_role not in _ALLOWED_ROLES:
        raise ResidentialRadiatorScheduleError("UNSUPPORTED_SOURCE_ROLE")
    if row.installation_status != PLANNED_NEW_INSTALLATION:
        raise ResidentialRadiatorScheduleError("INSTALLATION_STATUS_NOT_DESIGN_SCHEDULE")
    if not row.residential_scope:
        raise ResidentialRadiatorScheduleError("NON_RESIDENTIAL_ROW_FORBIDDEN")
    if row.heating_system_scope != HYBRID_RADIATOR_FLOOR:
        raise ResidentialRadiatorScheduleError("HEATING_SYSTEM_SCOPE_MISMATCH")
    if not row.hybrid_floor_heating_present:
        raise ResidentialRadiatorScheduleError("HYBRID_FLOOR_HEATING_MUST_BE_DISCLOSED")
    if row.emitter_family not in _ALLOWED_EMITTER_FAMILIES:
        raise ResidentialRadiatorScheduleError("UNSUPPORTED_EMITTER_FAMILY")
    if row.quantity <= 0 or row.dwelling_count_scope <= 0:
        raise ResidentialRadiatorScheduleError("NON_POSITIVE_PHYSICAL_COUNT")
    if not row.manufacturer.strip() or not row.product_family.strip():
        raise ResidentialRadiatorScheduleError("MISSING_PRODUCT_IDENTITY")
    if not row.type_size_token.strip():
        raise ResidentialRadiatorScheduleError("MISSING_TYPE_SIZE_TOKEN")
    if not row.source_url.startswith("https://"):
        raise ResidentialRadiatorScheduleError("SOURCE_URL_NOT_HTTPS")
    if not row.source_locator.strip():
        raise ResidentialRadiatorScheduleError("MISSING_EXACT_SOURCE_LOCATOR")
    if not row.source_date.strip():
        raise ResidentialRadiatorScheduleError("MISSING_SOURCE_DATE")

    if row.current_installed_stock_claimed:
        raise ResidentialRadiatorScheduleError(
            "DESIGN_SCHEDULE_IS_NOT_CURRENT_INSTALLED_STOCK"
        )
    if row.pre_retrofit_stock_claimed:
        raise ResidentialRadiatorScheduleError(
            "NEW_BUILD_SCHEDULE_IS_NOT_PRE_RETROFIT_STOCK"
        )
    if row.national_p42_authority_claimed:
        raise ResidentialRadiatorScheduleError(
            "BOUNDED_SCHEDULE_IS_NOT_NATIONAL_P42_AUTHORITY"
        )
    if row.programme_use_claimed:
        raise ResidentialRadiatorScheduleError(
            "BOUNDED_SCHEDULE_DOES_NOT_SELF_AUTHORIZE_PROGRAMME_USE"
        )

    return QUALIFIED_BOUNDED_RESIDENTIAL_SCHEDULE


def _panel_configuration(type_size_token: str) -> str:
    """Return source-native panel configuration prefix, e.g. 22KV."""

    return type_size_token.split("-", 1)[0]


def summarize_residential_radiator_schedule(
    rows: Iterable[ResidentialRadiatorScheduleRow],
) -> ResidentialRadiatorScheduleSummary:
    """Summarize one exact bounded building schedule without national promotion."""

    materialized = list(rows)
    if not materialized:
        raise ResidentialRadiatorScheduleError("EMPTY_SCHEDULE")

    for row in materialized:
        validate_residential_radiator_schedule_row(row)

    cohort_ids = {row.cohort_id for row in materialized}
    if len(cohort_ids) != 1:
        raise ResidentialRadiatorScheduleError("CROSS_COHORT_POOLING_FORBIDDEN")

    evidence_ids = [row.evidence_id for row in materialized]
    if len(evidence_ids) != len(set(evidence_ids)):
        raise ResidentialRadiatorScheduleError("DUPLICATE_EVIDENCE_ROW")

    heating_scopes = {row.heating_system_scope for row in materialized}
    if heating_scopes != {HYBRID_RADIATOR_FLOOR}:
        raise ResidentialRadiatorScheduleError("MIXED_HEATING_SYSTEM_SCOPE")

    # The recovered cohort contains one aggregate schedule for dwellings 1-4 and
    # four separate schedules for dwellings 5-8.  Distinct coverage IDs prevent
    # double-counting while preserving source-native granularity.
    coverage_to_dwelling_count: dict[str, int] = {}
    for row in materialized:
        prior = coverage_to_dwelling_count.setdefault(
            row.coverage_id, row.dwelling_count_scope
        )
        if prior != row.dwelling_count_scope:
            raise ResidentialRadiatorScheduleError("COVERAGE_DENOMINATOR_MISMATCH")

    dwelling_count = sum(coverage_to_dwelling_count.values())
    total = sum(row.quantity for row in materialized)
    panel = sum(
        row.quantity for row in materialized if row.emitter_family == PANEL_STEEL
    )
    towel = sum(
        row.quantity for row in materialized if row.emitter_family == TOWEL_RADIATOR
    )

    config_counts: Counter[str] = Counter()
    type_size_counts: Counter[str] = Counter()
    for row in materialized:
        type_size_counts[row.type_size_token] += row.quantity
        if row.emitter_family == PANEL_STEEL:
            config_counts[_panel_configuration(row.type_size_token)] += row.quantity
        else:
            config_counts[TOWEL_RADIATOR] += row.quantity

    return ResidentialRadiatorScheduleSummary(
        cohort_id=next(iter(cohort_ids)),
        dwelling_count=dwelling_count,
        total_radiators=total,
        panel_radiators=panel,
        towel_radiators=towel,
        radiators_per_dwelling=total / dwelling_count,
        configuration_counts=dict(sorted(config_counts.items())),
        type_size_counts=dict(sorted(type_size_counts.items())),
        heating_system_scope=HYBRID_RADIATOR_FLOOR,
    )


def schedule_grants_current_stock_authority(
    _: ResidentialRadiatorScheduleSummary,
) -> bool:
    """A design/procurement schedule is not an observed current-stock census."""

    return False


def schedule_grants_national_p42_authority(
    _: ResidentialRadiatorScheduleSummary,
) -> bool:
    """A single bounded residential project never self-authorizes P42."""

    return False
