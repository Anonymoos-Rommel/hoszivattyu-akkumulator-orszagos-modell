"""B08-P3 canonical seasonal reporting and national-load layer.

P3 separates reporting methodology from external evidence acquisition.

NATIONAL CONTROL-AREA BASELINE != REGIONAL DSO/COUNTY BASELINE
SEASON WINDOW != WEATHER EVENT
NATIONAL PEAK != SUM OF REGIONAL PEAKS
PUBLIC REPOSITORY MATERIALIZATION != MODEL-USE AUTHORITY

The calendar/season definition is a project reporting policy (POL), not an
observed physical fact. Real national load values still require admissible
source-native numeric evidence and model-use authority.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from zoneinfo import ZoneInfo
from typing import Iterable

from .observed_load_contract import (
    CONTROL_AREA_SCHEME,
    HUNGARY_CONTROL_AREA,
    ObservedLoadRecord,
)


BUDAPEST_TZ = ZoneInfo("Europe/Budapest")


class ReportingWindowKind(str, Enum):
    CALENDAR_YEAR = "CALENDAR_YEAR"
    METEOROLOGICAL_WINTER = "METEOROLOGICAL_WINTER"


@dataclass(frozen=True)
class ReportingWindow:
    kind: ReportingWindowKind
    label_year: int
    local_start: datetime
    local_end: datetime
    utc_start: datetime
    utc_end: datetime
    evidence_status: str = "POL"


@dataclass(frozen=True)
class SeasonalPeak:
    window_kind: str
    label_year: int
    peak_mw: float
    tied_timestamps_utc: tuple[datetime, ...]
    evidence_status: str


@dataclass(frozen=True)
class NationalBaselineAdmission:
    status: str
    blockers: tuple[str, ...]
    warnings: tuple[str, ...]


def canonical_reporting_window(
    kind: ReportingWindowKind,
    label_year: int,
) -> ReportingWindow:
    if not isinstance(label_year, int) or label_year < 2000 or label_year > 2200:
        raise ValueError("label_year outside supported reporting range")

    if kind == ReportingWindowKind.CALENDAR_YEAR:
        start = datetime(label_year, 1, 1, 0, 0, tzinfo=BUDAPEST_TZ)
        end = datetime(label_year + 1, 1, 1, 0, 0, tzinfo=BUDAPEST_TZ)
    elif kind == ReportingWindowKind.METEOROLOGICAL_WINTER:
        # Project reporting policy: winter labelled by its Jan/Feb year.
        start = datetime(label_year - 1, 12, 1, 0, 0, tzinfo=BUDAPEST_TZ)
        end = datetime(label_year, 3, 1, 0, 0, tzinfo=BUDAPEST_TZ)
    else:
        raise ValueError(f"unsupported reporting window: {kind!r}")

    return ReportingWindow(
        kind=kind,
        label_year=label_year,
        local_start=start,
        local_end=end,
        utc_start=start.astimezone(timezone.utc),
        utc_end=end.astimezone(timezone.utc),
    )


def _combined_status(records: tuple[ObservedLoadRecord, ...]) -> str:
    statuses = {record.evidence_status for record in records}
    if "Q" in statuses:
        return "Q"
    if "SCN" in statuses:
        return "SCN"
    if "DER" in statuses:
        return "DER"
    return "OBS"


def seasonal_peak(
    records: Iterable[ObservedLoadRecord],
    window: ReportingWindow,
) -> SeasonalPeak:
    """Extract a complete-window peak without resampling or hidden gap filling."""

    values = tuple(sorted(records, key=lambda x: x.timestamp_utc))
    if not values:
        raise ValueError("seasonal peak requires a non-empty panel")

    for record in values:
        if (
            record.region_id != HUNGARY_CONTROL_AREA
            or record.region_scheme != CONTROL_AREA_SCHEME
        ):
            raise ValueError("P3 national seasonal peak requires Hungarian control-area grain")
        if record.power_mw is None or record.evidence_status == "Q":
            raise ValueError("missing/Q load cannot authorize seasonal peak")
        if record.timestamp_utc < window.utc_start or record.interval_end_utc > window.utc_end:
            raise ValueError("record lies outside reporting window")

    if values[0].timestamp_utc != window.utc_start:
        raise ValueError("reporting window start is not covered")
    if values[-1].interval_end_utc != window.utc_end:
        raise ValueError("reporting window end is not covered")

    previous_end = values[0].interval_end_utc
    for record in values[1:]:
        if record.timestamp_utc != previous_end:
            raise ValueError("seasonal panel contains a gap or overlap")
        previous_end = record.interval_end_utc

    peak = max(float(record.power_mw) for record in values)
    tied = tuple(
        record.timestamp_utc
        for record in values
        if float(record.power_mw) == peak
    )
    return SeasonalPeak(
        window_kind=window.kind.value,
        label_year=window.label_year,
        peak_mw=peak,
        tied_timestamps_utc=tied,
        evidence_status=_combined_status(values),
    )


def assess_national_baseline(
    *,
    source_is_hungarian_control_area: bool,
    numeric_panel_available: bool,
    model_use_authorized: bool,
    provenance_complete: bool,
    regional_mapping_available: bool,
) -> NationalBaselineAdmission:
    """Regional mapping is intentionally not a national-baseline prerequisite."""

    blockers: list[str] = []
    warnings: list[str] = []

    if not source_is_hungarian_control_area:
        blockers.append("HUNGARIAN_CONTROL_AREA_SOURCE_REQUIRED")
    if not numeric_panel_available:
        blockers.append("REAL_NUMERIC_LOAD_PANEL_REQUIRED")
    if not model_use_authorized:
        blockers.append("SOURCE_SPECIFIC_MODEL_USE_AUTHORITY_REQUIRED")
    if not provenance_complete:
        blockers.append("COMPLETE_ACQUISITION_PROVENANCE_REQUIRED")
    if not regional_mapping_available:
        warnings.append("REGIONAL_DSO_COUNTY_CLAIMS_REMAIN_SEPARATE_Q")

    return NationalBaselineAdmission(
        status=(
            "QUALIFIED_NATIONAL_CONTROL_AREA_BASELINE"
            if not blockers
            else "Q_NATIONAL_NUMERIC_BASELINE"
        ),
        blockers=tuple(blockers),
        warnings=tuple(warnings),
    )


def regional_claim_boundary() -> tuple[str, ...]:
    return (
        "NATIONAL_CONTROL_AREA_SERIES_CANNOT_BE_DOWNSCALED_TO_DSO_OR_COUNTY_WITHOUT_AUTHORITY",
        "REGIONAL_PEAK_REQUIRES_REGIONAL_SERIES_OR_EXPLICIT_CALIBRATED_MAPPING",
        "NATIONAL_PEAK_IS_NOT_SUM_OF_NONCOINCIDENT_REGIONAL_PEAKS",
    )


def materialization_boundary() -> tuple[str, ...]:
    return (
        "MODEL_USE_AUTHORITY_IS_SEPARATE_FROM_PUBLIC_REPOSITORY_REPUBLICATION",
        "PUBLIC_REPOSITORY_RAW_SNAPSHOT_REQUIRES_REUSE_PERMISSION",
        "NO_REUSE_CLEARANCE_DOES_NOT_CREATE_A_REGIONAL_DATA_REQUIREMENT",
    )
