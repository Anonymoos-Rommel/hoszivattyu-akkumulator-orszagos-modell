"""Materialize B05-P8 empirical winter extremes from local HungaroMet archives.

The raw HABP_1H historical ZIP files remain external acquisition inputs and are
not written to the repository. This tool emits only derived winter block
statistics and non-parametric return-period brackets.

Usage:
    python tools/materialize_b05_extreme_weather.py RAW_DIR OUTPUT_DIR
"""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from modules.B05.extreme_weather_return_period import (
    WINTER_MEAN_TA,
    WINTER_MIN_72H_MEAN_TA,
    empirical_return_period_bracket,
    materializable_winter_metrics,
    multi_station_stress_envelope,
)
from modules.B05.weather import parse_hungaromet_zip


SOURCE_ID = "SRC-B05-HUNGARY-HOURLY-HIST-2026"
TARGET_RETURN_PERIOD_YEARS = 10.0
STATION_IDS = ("15310", "44527", "58102", "46304", "52744")


def _iso(value) -> str:
    return value.isoformat().replace("+00:00", "Z")


def _fmt(value) -> str:
    if value is None:
        return ""
    if isinstance(value, float):
        return f"{value:.6f}".rstrip("0").rstrip(".")
    return str(value)


def materialize(raw_dir: Path, output_dir: Path) -> None:
    winter_rows: list[dict[str, str]] = []
    bracket_rows: list[dict[str, str]] = []
    brackets_by_metric = {WINTER_MEAN_TA: [], WINTER_MIN_72H_MEAN_TA: []}

    for station_id in STATION_IDS:
        matches = sorted(raw_dir.glob(f"*_{station_id}_*_hist.zip"))
        if len(matches) != 1:
            raise FileNotFoundError(
                f"expected exactly one historical ZIP for station {station_id}, found {matches!r}"
            )

        records = parse_hungaromet_zip(matches[0], source_id=SOURCE_ID)
        metrics = materializable_winter_metrics(records)
        if not metrics:
            raise RuntimeError(f"no complete meteorological winters for station {station_id}")

        for metric in metrics:
            winter_rows.append(
                {
                    "station_id": metric.station_id,
                    "winter_label_year": str(metric.winter_label_year),
                    "winter_start_utc": _iso(metric.window_start_utc),
                    "winter_end_exclusive_utc": _iso(metric.window_end_exclusive_utc),
                    "expected_hours": str(metric.expected_hours),
                    "observed_hours": str(metric.observed_hours),
                    "winter_mean_ta_C": _fmt(metric.winter_mean_ta_c),
                    "coldest_72h_mean_ta_C": _fmt(metric.coldest_72h_mean_ta_c),
                    "coldest_72h_start_utc": _iso(metric.coldest_72h_start_utc),
                    "coldest_72h_end_utc": _iso(metric.coldest_72h_end_utc),
                    "evidence_status": metric.evidence_status,
                    "source_id": SOURCE_ID,
                    "notes": (
                        "Complete Dec-Feb Europe/Budapest winter; source-native ta; "
                        "no imputation; 72h event wholly inside winter."
                    ),
                }
            )

        for metric_id in (WINTER_MEAN_TA, WINTER_MIN_72H_MEAN_TA):
            bracket = empirical_return_period_bracket(
                metrics,
                metric_id=metric_id,
                target_return_period_years=TARGET_RETURN_PERIOD_YEARS,
            )
            brackets_by_metric[metric_id].append(bracket)
            bracket_rows.append(
                {
                    "station_id": bracket.station_id,
                    "metric_id": bracket.metric_id,
                    "target_return_period_years": _fmt(
                        bracket.target_return_period_years
                    ),
                    "complete_winter_blocks": str(bracket.complete_winter_blocks),
                    "target_annual_exceedance_probability": _fmt(
                        bracket.target_annual_exceedance_probability
                    ),
                    "colder_bound_C": _fmt(bracket.colder_bound_c),
                    "warmer_bound_C": _fmt(bracket.warmer_bound_c),
                    "colder_rank": _fmt(bracket.colder_rank),
                    "warmer_rank": _fmt(bracket.warmer_rank),
                    "colder_rank_return_period_years": _fmt(
                        bracket.colder_rank_return_period_years
                    ),
                    "warmer_rank_return_period_years": _fmt(
                        bracket.warmer_rank_return_period_years
                    ),
                    "status": bracket.status,
                    "evidence_status": bracket.evidence_status,
                    "source_id": SOURCE_ID,
                    "notes": ";".join(bracket.notes),
                }
            )

    envelope_rows: list[dict[str, str]] = []
    for metric_id, brackets in brackets_by_metric.items():
        qualified = [row for row in brackets if row.evidence_status == "DER"]
        if len(qualified) != len(STATION_IDS):
            continue
        envelope = multi_station_stress_envelope(qualified)
        envelope_rows.append(
            {
                "metric_id": envelope.metric_id,
                "target_return_period_years": _fmt(
                    envelope.target_return_period_years
                ),
                "station_count": str(envelope.station_count),
                "colder_envelope_C": _fmt(envelope.colder_envelope_c),
                "warmer_envelope_C": _fmt(envelope.warmer_envelope_c),
                "status": envelope.status,
                "evidence_status": envelope.evidence_status,
                "source_id": SOURCE_ID,
                "notes": (
                    "Spatial station envelope only; no national population or climate-zone "
                    "weights; not an official HungaroMet 1-in-10 statistic."
                ),
            }
        )

    output_dir.mkdir(parents=True, exist_ok=True)

    def write(name: str, rows: list[dict[str, str]]) -> None:
        if not rows:
            raise RuntimeError(f"no rows for {name}")
        with (output_dir / name).open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(rows[0]), lineterminator="\n")
            writer.writeheader()
            writer.writerows(rows)

    write("b05_weather_winter_extremes.csv", winter_rows)
    write("b05_weather_empirical_return_period.csv", bracket_rows)
    if envelope_rows:
        write("b05_weather_empirical_station_envelope.csv", envelope_rows)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("raw_dir", type=Path)
    parser.add_argument("output_dir", type=Path)
    args = parser.parse_args()
    materialize(args.raw_dir, args.output_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
