"""HungaroMet hourly weather evidence helpers for B05.

The parser keeps the source-native variables separate.  ``ta`` is projected
to the B05 hourly outdoor-temperature interface; ``t`` remains an independent
instantaneous observation.  No filling or time-zone conversion is performed.
"""

from __future__ import annotations

import csv
import io
import zipfile
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from statistics import fmean
from typing import Iterable, Iterator, Mapping, Sequence


MISSING_SENTINEL = "-999"
UTC = timezone.utc


@dataclass(frozen=True)
class WeatherRecord:
    station_id: str
    timestamp_utc: datetime
    instantaneous_temperature_c: float | None
    hourly_mean_temperature_c: float | None
    hourly_min_temperature_c: float | None
    hourly_max_temperature_c: float | None
    relative_humidity_pct: float | None
    source_id: str

    @property
    def outdoor_temperature_c(self) -> float | None:
        """Canonical B05 projection: source-native ``ta`` (previous-hour mean)."""

        return self.hourly_mean_temperature_c


def _clean(value: str | None) -> str:
    return (value or "").strip()


def _optional_float(value: str | None) -> float | None:
    cleaned = _clean(value)
    if not cleaned or cleaned == MISSING_SENTINEL:
        return None
    return float(cleaned)


def _field_map(fieldnames: Sequence[str]) -> dict[str, int]:
    return {_clean(name): index for index, name in enumerate(fieldnames)}


def parse_hungaromet_csv(
    text: str,
    *,
    source_id: str,
) -> Iterator[WeatherRecord]:
    """Parse a HungaroMet ``HABP_1H`` historical CSV.

    Metadata lines beginning with ``#`` and the terminal ``EOR`` token are
    ignored.  Source UTC timestamps are preserved as timezone-aware UTC.
    ``-999`` is materialized as ``None`` and is never imputed.
    """

    lines = [line for line in text.splitlines() if line.strip() and not line.lstrip().startswith("#")]
    if not lines:
        return
    reader = csv.reader(io.StringIO("\n".join(lines)), delimiter=";")
    rows = iter(reader)
    raw_header = next(rows)
    header = [_clean(item) for item in raw_header]
    positions = _field_map(header)
    required = {"StationNumber", "Time", "t", "ta", "tn", "tx", "u"}
    missing = required - positions.keys()
    if missing:
        raise ValueError(f"HungaroMet hourly CSV missing columns: {sorted(missing)}")
    for row in rows:
        if not row or _clean(row[-1]) == "EOR":
            if _clean(row[-1]) == "EOR":
                row = row[:-1]
        if not row:
            continue
        try:
            timestamp = datetime.strptime(_clean(row[positions["Time"]]), "%Y%m%d%H%M").replace(tzinfo=UTC)
        except (KeyError, ValueError) as exc:
            raise ValueError(f"invalid HungaroMet UTC timestamp: {row!r}") from exc
        yield WeatherRecord(
            station_id=_clean(row[positions["StationNumber"]]),
            timestamp_utc=timestamp,
            instantaneous_temperature_c=_optional_float(row[positions["t"]]),
            hourly_mean_temperature_c=_optional_float(row[positions["ta"]]),
            hourly_min_temperature_c=_optional_float(row[positions["tn"]]),
            hourly_max_temperature_c=_optional_float(row[positions["tx"]]),
            relative_humidity_pct=_optional_float(row[positions["u"]]),
            source_id=source_id,
        )


def parse_hungaromet_zip(path: str | Path, *, source_id: str) -> tuple[WeatherRecord, ...]:
    with zipfile.ZipFile(path) as archive:
        csv_names = [name for name in archive.namelist() if name.lower().endswith(".csv")]
        if len(csv_names) != 1:
            raise ValueError(f"expected exactly one CSV in {path}, found {csv_names!r}")
        text = archive.read(csv_names[0]).decode("utf-8-sig")
    return tuple(parse_hungaromet_csv(text, source_id=source_id))


def select_year(records: Iterable[WeatherRecord], year: int) -> tuple[WeatherRecord, ...]:
    selected = tuple(record for record in records if record.timestamp_utc.year == year)
    return tuple(sorted(selected, key=lambda record: record.timestamp_utc))


def select_extreme_cold_spell(
    records: Iterable[WeatherRecord],
    *,
    window_hours: int = 72,
) -> tuple[WeatherRecord, ...]:
    """Select the coldest contiguous observed window by ``ta`` mean.

    A window is eligible only when all hours are present, consecutive UTC
    hours, and have non-missing ``ta``. Ties resolve to the earliest window.
    """

    ordered = tuple(sorted(records, key=lambda record: record.timestamp_utc))
    best: tuple[float, datetime, tuple[WeatherRecord, ...]] | None = None
    segment: list[WeatherRecord] = []
    for record in ordered:
        if record.hourly_mean_temperature_c is None:
            segment = []
            continue
        contiguous = bool(segment) and record.timestamp_utc - segment[-1].timestamp_utc == timedelta(hours=1)
        if not contiguous:
            segment = []
        segment.append(record)
        if len(segment) < window_hours:
            continue
        window = tuple(segment[-window_hours:])
        mean = fmean(record.hourly_mean_temperature_c for record in window if record.hourly_mean_temperature_c is not None)
        key = (mean, window[0].timestamp_utc, window)
        if best is None or key[:2] < best[:2]:
            best = key
    return best[2] if best is not None else ()


def completeness(records: Sequence[WeatherRecord], *, start: datetime, end_exclusive: datetime) -> tuple[int, int, float]:
    expected = int((end_exclusive - start).total_seconds() // 3600)
    timestamps = {record.timestamp_utc for record in records if start <= record.timestamp_utc < end_exclusive}
    with_temperature = sum(
        1
        for record in records
        if start <= record.timestamp_utc < end_exclusive and record.outdoor_temperature_c is not None
    )
    return expected, with_temperature, (with_temperature / expected if expected else 0.0)


def coverage(records: Sequence[WeatherRecord], *, lower_c: float = -7.0, upper_c: float = 7.0) -> dict[str, float | int | None]:
    values = [record.outdoor_temperature_c for record in records if record.outdoor_temperature_c is not None]
    inside = sum(lower_c <= value <= upper_c for value in values)
    below = sum(value < lower_c for value in values)
    above = sum(value > upper_c for value in values)
    return {
        "hours_total": len(values),
        "hours_below_minus7C": below,
        "hours_inside_performance_domain": inside,
        "hours_above_plus7C": above,
        "share_inside_current_performance_domain": inside / len(values) if values else None,
        "minimum_observed_temperature_C": min(values) if values else None,
    }
