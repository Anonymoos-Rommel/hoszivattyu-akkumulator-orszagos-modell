"""B05-P8 empirical cold-winter / multi-day return-period contract.

This module derives station-specific block-extreme statistics from the already
canonical HungaroMet HABP_1H hourly observations when the external raw archives
are available locally.

It deliberately does NOT claim an official HungaroMet "1-in-10" definition.

Core boundaries:

PROJECT_DERIVED_EMPIRICAL_RETURN_PERIOD != OFFICIAL_HUNGAROMET_1_IN_10
STATION_RETURN_PERIOD != NATIONAL_POPULATION_WEIGHTED_CLIMATE
OBSERVED_RECORD_EXTREME != RETURN_PERIOD_ESTIMATE
PARAMETRIC_EXTRAPOLATION != DEFAULT

Two cold metrics are supported for each complete meteorological winter:

1. winter mean source-native ta;
2. coldest contiguous 72-hour mean source-native ta.

Lower temperatures are more severe. A target return period is represented by
an order-statistic bracket, not a point interpolation. This avoids inventing a
parametric tail model from the relatively short station archives.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from statistics import fmean
from typing import Iterable, Sequence
from zoneinfo import ZoneInfo

from .weather import WeatherRecord, select_extreme_cold_spell


BUDAPEST_TZ = ZoneInfo("Europe/Budapest")

WINTER_MEAN_TA = "WINTER_MEAN_TA_C"
WINTER_MIN_72H_MEAN_TA = "WINTER_MIN_72H_MEAN_TA_C"
SUPPORTED_METRICS = frozenset({WINTER_MEAN_TA, WINTER_MIN_72H_MEAN_TA})

EMPIRICAL_ORDER_STATISTIC_BRACKET = "EMPIRICAL_ORDER_STATISTIC_BRACKET"
Q_INSUFFICIENT_BLOCKS = "Q_INSUFFICIENT_COMPLETE_WINTER_BLOCKS"


@dataclass(frozen=True)
class WinterExtremeMetric:
    station_id: str
    winter_label_year: int
    window_start_utc: datetime
    window_end_exclusive_utc: datetime
    expected_hours: int
    observed_hours: int
    winter_mean_ta_c: float
    coldest_72h_mean_ta_c: float
    coldest_72h_start_utc: datetime
    coldest_72h_end_utc: datetime
    evidence_status: str = "DER"


@dataclass(frozen=True)
class EmpiricalReturnPeriodBracket:
    station_id: str
    metric_id: str
    target_return_period_years: float
    complete_winter_blocks: int
    target_annual_exceedance_probability: float
    colder_bound_c: float | None
    warmer_bound_c: float | None
    colder_rank: int | None
    warmer_rank: int | None
    colder_rank_return_period_years: float | None
    warmer_rank_return_period_years: float | None
    status: str
    evidence_status: str
    notes: tuple[str, ...]


@dataclass(frozen=True)
class MultiStationStressEnvelope:
    metric_id: str
    target_return_period_years: float
    station_count: int
    colder_envelope_c: float
    warmer_envelope_c: float
    evidence_status: str = "DER"
    status: str = "PROJECT_STATION_ENVELOPE"


def winter_bounds_utc(label_year: int) -> tuple[datetime, datetime]:
    """Return Dec-1(Y-1) .. Mar-1(Y) Europe/Budapest as half-open UTC bounds."""

    if not isinstance(label_year, int) or label_year < 1900 or label_year > 2200:
        raise ValueError("invalid winter label year")
    local_start = datetime(label_year - 1, 12, 1, 0, 0, tzinfo=BUDAPEST_TZ)
    local_end = datetime(label_year, 3, 1, 0, 0, tzinfo=BUDAPEST_TZ)
    return (
        local_start.astimezone(timezone.utc),
        local_end.astimezone(timezone.utc),
    )


def _records_in_window(
    records: Sequence[WeatherRecord],
    *,
    start: datetime,
    end_exclusive: datetime,
) -> tuple[WeatherRecord, ...]:
    return tuple(
        sorted(
            (
                record
                for record in records
                if start <= record.timestamp_utc < end_exclusive
            ),
            key=lambda record: record.timestamp_utc,
        )
    )


def complete_winter_metric(
    records: Sequence[WeatherRecord],
    *,
    winter_label_year: int,
) -> WinterExtremeMetric | None:
    """Return one winter block only when every hourly ta is present exactly once."""

    if not records:
        return None
    station_ids = {record.station_id for record in records}
    if len(station_ids) != 1:
        raise ValueError("winter metric requires one station at a time")

    start, end_exclusive = winter_bounds_utc(winter_label_year)
    selected = _records_in_window(records, start=start, end_exclusive=end_exclusive)
    expected = int((end_exclusive - start).total_seconds() // 3600)

    if len(selected) != expected:
        return None

    for index, record in enumerate(selected):
        expected_timestamp = start + timedelta(hours=index)
        if record.timestamp_utc != expected_timestamp:
            return None
        if record.hourly_mean_temperature_c is None:
            return None

    cold72 = select_extreme_cold_spell(selected, window_hours=72)
    if len(cold72) != 72:
        return None

    winter_mean = fmean(
        float(record.hourly_mean_temperature_c)
        for record in selected
        if record.hourly_mean_temperature_c is not None
    )
    cold72_mean = fmean(
        float(record.hourly_mean_temperature_c)
        for record in cold72
        if record.hourly_mean_temperature_c is not None
    )

    return WinterExtremeMetric(
        station_id=next(iter(station_ids)),
        winter_label_year=winter_label_year,
        window_start_utc=start,
        window_end_exclusive_utc=end_exclusive,
        expected_hours=expected,
        observed_hours=len(selected),
        winter_mean_ta_c=winter_mean,
        coldest_72h_mean_ta_c=cold72_mean,
        coldest_72h_start_utc=cold72[0].timestamp_utc,
        coldest_72h_end_utc=cold72[-1].timestamp_utc,
    )


def materializable_winter_metrics(
    records: Sequence[WeatherRecord],
) -> tuple[WinterExtremeMetric, ...]:
    """Derive all complete meteorological-winter blocks in a station archive."""

    if not records:
        return ()
    station_ids = {record.station_id for record in records}
    if len(station_ids) != 1:
        raise ValueError("materializable_winter_metrics requires one station")

    first_year = min(record.timestamp_utc.year for record in records)
    last_year = max(record.timestamp_utc.year for record in records)

    metrics: list[WinterExtremeMetric] = []
    for label_year in range(first_year, last_year + 2):
        metric = complete_winter_metric(records, winter_label_year=label_year)
        if metric is not None:
            metrics.append(metric)
    return tuple(metrics)


def _metric_value(metric: WinterExtremeMetric, metric_id: str) -> float:
    if metric_id == WINTER_MEAN_TA:
        return metric.winter_mean_ta_c
    if metric_id == WINTER_MIN_72H_MEAN_TA:
        return metric.coldest_72h_mean_ta_c
    raise ValueError(f"unsupported cold metric: {metric_id!r}")


def empirical_return_period_bracket(
    metrics: Iterable[WinterExtremeMetric],
    *,
    metric_id: str,
    target_return_period_years: float = 10.0,
) -> EmpiricalReturnPeriodBracket:
    """Bracket a target recurrence level using non-parametric plotting positions.

    For the r-th coldest annual block among n complete winters:
        annual exceedance probability = r / (n + 1)
        empirical return period = (n + 1) / r

    No interpolation is used.
    """

    if metric_id not in SUPPORTED_METRICS:
        raise ValueError(f"unsupported metric: {metric_id!r}")
    if target_return_period_years <= 1.0:
        raise ValueError("target return period must be > 1 year")

    values = tuple(metrics)
    if not values:
        raise ValueError("at least one winter metric is required")
    station_ids = {metric.station_id for metric in values}
    if len(station_ids) != 1:
        raise ValueError("return-period bracket requires one station")
    station_id = next(iter(station_ids))

    ordered = sorted(
        ((_metric_value(metric, metric_id), metric.winter_label_year) for metric in values),
        key=lambda item: (item[0], item[1]),
    )
    n = len(ordered)
    p_target = 1.0 / target_return_period_years

    plotting = [
        (rank, value, rank / (n + 1), (n + 1) / rank)
        for rank, (value, _year) in enumerate(ordered, start=1)
    ]

    if p_target < plotting[0][2]:
        return EmpiricalReturnPeriodBracket(
            station_id=station_id,
            metric_id=metric_id,
            target_return_period_years=target_return_period_years,
            complete_winter_blocks=n,
            target_annual_exceedance_probability=p_target,
            colder_bound_c=None,
            warmer_bound_c=None,
            colder_rank=None,
            warmer_rank=None,
            colder_rank_return_period_years=None,
            warmer_rank_return_period_years=None,
            status=Q_INSUFFICIENT_BLOCKS,
            evidence_status="Q",
            notes=(
                "TARGET_RETURN_PERIOD_EXCEEDS_NONPARAMETRIC_RECORD_SUPPORT",
                "NO_PARAMETRIC_TAIL_EXTRAPOLATION",
            ),
        )

    for rank, value, p, return_period in plotting:
        if abs(p - p_target) <= 1e-12:
            return EmpiricalReturnPeriodBracket(
                station_id=station_id,
                metric_id=metric_id,
                target_return_period_years=target_return_period_years,
                complete_winter_blocks=n,
                target_annual_exceedance_probability=p_target,
                colder_bound_c=value,
                warmer_bound_c=value,
                colder_rank=rank,
                warmer_rank=rank,
                colder_rank_return_period_years=return_period,
                warmer_rank_return_period_years=return_period,
                status=EMPIRICAL_ORDER_STATISTIC_BRACKET,
                evidence_status="DER",
                notes=(
                    "PROJECT_DERIVED_EMPIRICAL_RECURRENCE",
                    "NOT_OFFICIAL_HUNGAROMET_1_IN_10",
                ),
            )

    for idx in range(len(plotting) - 1):
        cold = plotting[idx]
        warm = plotting[idx + 1]
        if cold[2] < p_target < warm[2]:
            return EmpiricalReturnPeriodBracket(
                station_id=station_id,
                metric_id=metric_id,
                target_return_period_years=target_return_period_years,
                complete_winter_blocks=n,
                target_annual_exceedance_probability=p_target,
                colder_bound_c=cold[1],
                warmer_bound_c=warm[1],
                colder_rank=cold[0],
                warmer_rank=warm[0],
                colder_rank_return_period_years=cold[3],
                warmer_rank_return_period_years=warm[3],
                status=EMPIRICAL_ORDER_STATISTIC_BRACKET,
                evidence_status="DER",
                notes=(
                    "NO_POINT_INTERPOLATION",
                    "PROJECT_DERIVED_EMPIRICAL_RECURRENCE",
                    "NOT_OFFICIAL_HUNGAROMET_1_IN_10",
                ),
            )

    return EmpiricalReturnPeriodBracket(
        station_id=station_id,
        metric_id=metric_id,
        target_return_period_years=target_return_period_years,
        complete_winter_blocks=n,
        target_annual_exceedance_probability=p_target,
        colder_bound_c=None,
        warmer_bound_c=None,
        colder_rank=None,
        warmer_rank=None,
        colder_rank_return_period_years=None,
        warmer_rank_return_period_years=None,
        status=Q_INSUFFICIENT_BLOCKS,
        evidence_status="Q",
        notes=("TARGET_OUTSIDE_EMPIRICAL_PLOTTING_POSITION_SUPPORT",),
    )


def multi_station_stress_envelope(
    brackets: Iterable[EmpiricalReturnPeriodBracket],
) -> MultiStationStressEnvelope:
    """Create a spatial stress envelope without inventing national station weights."""

    rows = tuple(brackets)
    if not rows:
        raise ValueError("at least one station bracket is required")
    if any(row.status != EMPIRICAL_ORDER_STATISTIC_BRACKET for row in rows):
        raise ValueError("all station brackets must be empirically qualified")

    metric_ids = {row.metric_id for row in rows}
    targets = {row.target_return_period_years for row in rows}
    stations = {row.station_id for row in rows}
    if len(metric_ids) != 1 or len(targets) != 1:
        raise ValueError("station brackets must share metric and target return period")
    if len(stations) != len(rows):
        raise ValueError("duplicate station bracket")

    colder = min(float(row.colder_bound_c) for row in rows if row.colder_bound_c is not None)
    warmer = max(float(row.warmer_bound_c) for row in rows if row.warmer_bound_c is not None)
    return MultiStationStressEnvelope(
        metric_id=next(iter(metric_ids)),
        target_return_period_years=next(iter(targets)),
        station_count=len(stations),
        colder_envelope_c=colder,
        warmer_envelope_c=warmer,
    )


def return_period_boundaries() -> tuple[str, ...]:
    return (
        "PROJECT_DERIVED_EMPIRICAL_RETURN_PERIOD != OFFICIAL_HUNGAROMET_1_IN_10",
        "STATION_RETURN_PERIOD != NATIONAL_POPULATION_WEIGHTED_CLIMATE",
        "OBSERVED_RECORD_EXTREME != RETURN_PERIOD_ESTIMATE",
        "NO_PARAMETRIC_TAIL_EXTRAPOLATION_BY_DEFAULT",
        "ONLY_COMPLETE_METEOROLOGICAL_WINTERS_MAY_ENTER",
        "MISSING_HOURLY_TA_INVALIDATES_THE_WINTER_BLOCK",
    )
