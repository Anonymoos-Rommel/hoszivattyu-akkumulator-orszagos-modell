"""Materialize a bounded, reproducible HungaroMet B05 weather evidence panel.

Raw HungaroMet ZIP files are acquisition inputs and intentionally remain
outside Git. The generated CSVs contain only the selected observed windows
and source references.
"""

from __future__ import annotations

import argparse
import csv
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from modules.B05.weather import WeatherRecord, completeness, coverage, parse_hungaromet_zip, select_extreme_cold_spell, select_year


SOURCE_ID = "SRC-B05-HUNGARY-HOURLY-HIST-2026"
RETRIEVED_AT = "2026-08-22"
REFERENCE_YEAR = 2025
STATIONS = {
    "15310": ("Szombathely", 47.1983, 16.6478, 200.1),
    "44527": ("Budapest Pestszentlőrinc", 47.4292, 19.1822, 138.1),
    "58102": ("Szeged belterület", 46.2472, 20.1406, 103.9),
    "46304": ("Kecskemét K-puszta", 46.9656, 19.5450, 125.9),
    "52744": ("Miskolc Diósgyőr", 48.0947, 20.7267, 161.0),
}


def _iso(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def _record_rows(records: list[tuple[str, WeatherRecord]]) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for index, (profile_id, record) in enumerate(records, start=1):
        def fmt(value: float | None) -> str:
            return "" if value is None else f"{value:g}"

        rows.append(
            {
                "record_id": f"B05-WX-{index:05d}",
                "weather_profile_id": profile_id,
                "station_id": record.station_id,
                "timestamp_utc": _iso(record.timestamp_utc),
                "outdoor_temperature_C": fmt(record.outdoor_temperature_c),
                "temperature_source_variable": "ta",
                "instantaneous_temperature_C": fmt(record.instantaneous_temperature_c),
                "relative_humidity_pct": fmt(record.relative_humidity_pct),
                "hourly_min_temperature_C": fmt(record.hourly_min_temperature_c),
                "hourly_max_temperature_C": fmt(record.hourly_max_temperature_c),
                "evidence_status": "OBS",
                "source_id": record.source_id,
                "retrieved_at": RETRIEVED_AT,
            }
        )
    return rows


def materialize(raw_dir: Path, output_dir: Path) -> None:
    all_records: dict[str, tuple[WeatherRecord, ...]] = {}
    for station_id in STATIONS:
        matches = sorted(raw_dir.glob(f"*_{station_id}_*_hist.zip"))
        if len(matches) != 1:
            raise FileNotFoundError(f"expected one raw ZIP for station {station_id}, found {matches!r}")
        all_records[station_id] = parse_hungaromet_zip(matches[0], source_id=SOURCE_ID)

    output_dir.mkdir(parents=True, exist_ok=True)
    hourly: list[dict[str, str]] = []
    profiles: list[dict[str, str]] = []
    coverages: list[dict[str, str]] = []

    reference_start = datetime(REFERENCE_YEAR, 1, 1, tzinfo=timezone.utc)
    reference_end = datetime(REFERENCE_YEAR + 1, 1, 1, tzinfo=timezone.utc)
    selected_reference: list[tuple[str, WeatherRecord]] = []
    for station_id, records in all_records.items():
        profile_id = f"B05-REF-OBS-{REFERENCE_YEAR}-{station_id}"
        selected = select_year(records, REFERENCE_YEAR)
        selected_reference.extend((profile_id, record) for record in selected)
        expected, observed, ratio = completeness(records, start=reference_start, end_exclusive=reference_end)
        name, lat, lon, elevation = STATIONS[station_id]
        profiles.append(
            {
                "weather_profile_id": profile_id,
                "profile_type": "OBSERVED_REFERENCE_YEAR",
                "station_id": station_id,
                "station_name": name,
                "latitude": f"{lat:.4f}",
                "longitude": f"{lon:.4f}",
                "elevation_m": f"{elevation:.1f}",
                "period_start_utc": _iso(reference_start),
                "period_end_utc": _iso(reference_end - timedelta(hours=1)),
                "selection_method": "latest common complete calendar year available for all five selected stations; observed year only, not a 1991-2020 normal",
                "source_reference_period": "1991-2020 official normal retained as climate context; hourly rows are observed 2025",
                "retrieved_at": RETRIEVED_AT,
                "completeness": f"{ratio:.6f}",
                "status": "OBS" if ratio == 1.0 else "Q",
                "source_id": SOURCE_ID,
                "notes": f"{observed}/{expected} hours with non-missing ta; source archive {_iso(records[0].timestamp_utc)}..{_iso(records[-1].timestamp_utc)}; no imputation; station-specific panel, no national weighting.",
            }
        )
        stats = coverage(selected)
        coverages.append(
            {
                "weather_profile_id": profile_id,
                "station_id": station_id,
                **{key: "" if value is None else f"{value:g}" for key, value in stats.items()},
                "status": "OBS" if ratio == 1.0 else "Q",
                "source_id": SOURCE_ID,
                "notes": "Coverage is calculated only on non-missing canonical ta values; -7/+7 C bounds are the current STIEBEL product-map domain.",
            }
        )

    hourly.extend(_record_rows(selected_reference))

    extreme_candidates: list[tuple[float, str, tuple[WeatherRecord, ...]]] = []
    for station_id, records in all_records.items():
        window = select_extreme_cold_spell(records, window_hours=72)
        if window:
            mean = sum(record.outdoor_temperature_c for record in window if record.outdoor_temperature_c is not None) / len(window)
            extreme_candidates.append((mean, station_id, window))
    if not extreme_candidates:
        raise RuntimeError("no complete observed 72-hour cold spell found")
    mean, station_id, window = min(extreme_candidates, key=lambda item: (item[0], item[2][0].timestamp_utc, item[1]))
    profile_id = f"B05-EXTREME-OBSERVED-72H-{station_id}"
    profiles.append(
        {
            "weather_profile_id": profile_id,
            "profile_type": "OBSERVED_EXTREME_COLD_SPELL",
            "station_id": station_id,
            "station_name": STATIONS[station_id][0],
            "latitude": f"{STATIONS[station_id][1]:.4f}",
            "longitude": f"{STATIONS[station_id][2]:.4f}",
            "elevation_m": f"{STATIONS[station_id][3]:.1f}",
            "period_start_utc": _iso(window[0].timestamp_utc),
            "period_end_utc": _iso(window[-1].timestamp_utc),
            "selection_method": "coldest contiguous 72-hour mean of source-native ta across the full available panel records; no return-period claim",
            "source_reference_period": "station archive period in source ZIP",
            "retrieved_at": RETRIEVED_AT,
            "completeness": "1.000000",
            "status": "OBS",
            "source_id": SOURCE_ID,
            "notes": f"Observed 72-hour ta mean={mean:.3f} C; source archive {_iso(all_records[station_id][0].timestamp_utc)}..{_iso(all_records[station_id][-1].timestamp_utc)}; raw observed hourly layer, not homogenized climate series and not 1-in-10.",
        }
    )
    hourly.extend(_record_rows([(profile_id, record) for record in window]))
    stats = coverage(window)
    coverages.append(
        {
            "weather_profile_id": profile_id,
            "station_id": station_id,
            **{key: "" if value is None else f"{value:g}" for key, value in stats.items()},
            "status": "OBS",
            "source_id": SOURCE_ID,
            "notes": "Observed event coverage; this is not a return-period estimate.",
        }
    )

    def write(name: str, rows: list[dict[str, str]]) -> None:
        if not rows:
            raise RuntimeError(f"no rows for {name}")
        with (output_dir / name).open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(rows[0]), lineterminator="\n")
            writer.writeheader()
            writer.writerows(rows)

    write("heat_pump_weather_hourly.csv", hourly)
    write("heat_pump_weather_profiles.csv", profiles)
    write("heat_pump_weather_coverage.csv", coverages)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("raw_dir", type=Path)
    parser.add_argument("output_dir", type=Path)
    args = parser.parse_args()
    materialize(args.raw_dir, args.output_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
