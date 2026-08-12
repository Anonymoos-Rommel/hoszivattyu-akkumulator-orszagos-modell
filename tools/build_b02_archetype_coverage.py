"""Build deterministic B02 archetype coverage and joinability outputs.

The tool works only from committed B02 derivatives.  It deliberately does not
cross-multiply separate margins into a synthetic full archetype table.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
from collections import defaultdict
from decimal import Decimal
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DATA = ROOT / "data" / "processed" / "b02"

BENCHMARK_FILE = "ksh_energy_archetype_benchmarks_2022.csv"
DISTRIBUTION_FILE = "ksh_energy_distribution_2022.csv"
PROXY_FILE = "ksh_building_type_proxy_2022.csv"
COVERAGE_FILE = "b02_archetype_cell_coverage_2022.csv"
JOINABILITY_FILE = "b02_archetype_joinability_2022.csv"
MANIFEST_FILE = "b02_archetype_coverage_manifest.json"

EXPECTED_BUILDING_TYPES = {"FAMILY_HOUSE", "MULTI_DWELLING"}
EXPECTED_PERIODS = {
    "1919 előtt",
    "1919–1945",
    "1946–1960",
    "1961–1980",
    "1981–2000",
    "2001–2010",
    "2011–2015",
    "2016–2022",
}
EXPECTED_BINS = set(range(10, 600, 10))


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, headers: list[str], rows: list[list[object]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle, lineterminator="\n")
        writer.writerow(headers)
        writer.writerows(rows)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def decimal_text(value: Decimal) -> str:
    return format(value, ".15f")


def build_coverage_rows(
    benchmarks: list[dict[str, str]], distributions: list[dict[str, str]]
) -> tuple[list[list[object]], dict[str, int]]:
    if len(benchmarks) != 16:
        raise ValueError(f"expected 16 benchmark cells, got {len(benchmarks)}")
    keys = {(row["building_type"], row["construction_period"]) for row in benchmarks}
    if {key[0] for key in keys} != EXPECTED_BUILDING_TYPES:
        raise ValueError(f"building-type drift: {sorted({key[0] for key in keys})!r}")
    if {key[1] for key in keys} != EXPECTED_PERIODS or len(keys) != 16:
        raise ValueError("construction-period benchmark grid is not 2 x 8")
    if {row["evidence_status"] for row in benchmarks} != {"MODELLED"}:
        raise ValueError("benchmark cells must remain MODELLED")
    if len(distributions) != 944:
        raise ValueError(f"expected 944 distribution bins, got {len(distributions)}")

    by_key: dict[tuple[str, str], list[dict[str, str]]] = defaultdict(list)
    for row in distributions:
        by_key[(row["building_type"], row["construction_period"])].append(row)
    if set(by_key) != keys:
        raise ValueError("distribution and benchmark cell keys differ")

    counts = {
        (row["building_type"], row["construction_period"]): int(
            row["published_bin_dwelling_count"]
        )
        for row in benchmarks
    }
    total = sum(counts.values())
    ranked_keys = sorted(keys, key=lambda key: (-counts[key], key[0], key[1]))
    rank = {key: index for index, key in enumerate(ranked_keys, start=1)}
    cumulative: dict[tuple[str, str], Decimal] = {}
    running = Decimal(0)
    for key in ranked_keys:
        running += Decimal(counts[key]) / Decimal(total)
        cumulative[key] = running

    output: list[list[object]] = []
    positive_bin_total = 0
    zero_bin_total = 0
    for index, benchmark in enumerate(benchmarks, start=1):
        key = (benchmark["building_type"], benchmark["construction_period"])
        group = by_key[key]
        bins = {int(row["published_energy_bin_kwh_m2_year"]) for row in group}
        if bins != EXPECTED_BINS or len(group) != 59:
            raise ValueError(f"energy-bin grid drift for {key!r}")
        if {row["evidence_status"] for row in group} != {"MODELLED"}:
            raise ValueError(f"distribution evidence status drift for {key!r}")
        group_total = sum(int(row["dwelling_count"]) for row in group)
        if group_total != counts[key]:
            raise ValueError(
                f"distribution total mismatch for {key!r}: {group_total} != {counts[key]}"
            )
        positive = [row for row in group if int(row["dwelling_count"]) > 0]
        zero_count = len(group) - len(positive)
        positive_bin_total += len(positive)
        zero_bin_total += zero_count
        positive_bins = [int(row["published_energy_bin_kwh_m2_year"]) for row in positive]
        positive_counts = [int(row["dwelling_count"]) for row in positive]
        share = Decimal(counts[key]) / Decimal(total)
        output.append(
            [
                f"COVCELL-B02-{index:02d}",
                "SRC-B02-KSH-ENERGY-2025",
                2022,
                "EKM_9_2023",
                key[0],
                key[1],
                counts[key],
                decimal_text(share),
                rank[key],
                decimal_text(cumulative[key]),
                len(group),
                len(positive),
                zero_count,
                min(positive_bins),
                max(positive_bins),
                min(positive_counts),
                max(positive_counts),
                "DER",
                "MODELLED",
                "Shares and bin diagnostics are derived from KSH-modelled dwelling counts; no extra archetype dimensions are joined.",
            ]
        )

    controls = {
        "benchmark_cells": len(benchmarks),
        "distribution_bins": len(distributions),
        "positive_distribution_bins": positive_bin_total,
        "zero_distribution_bins": zero_bin_total,
        "modelled_dwellings_in_published_bins": total,
        "smallest_benchmark_cell_dwellings": min(counts.values()),
        "largest_benchmark_cell_dwellings": max(counts.values()),
    }
    return output, controls


def build_joinability_rows(proxy_rows: list[dict[str, str]]) -> list[list[object]]:
    if len(proxy_rows) != 8 or {row["evidence_status"] for row in proxy_rows} != {"ASS"}:
        raise ValueError("building-type proxy must contain 8 ASS rows")
    proxy_total = sum(int(row["proxy_2022_dwelling_count"]) for row in proxy_rows)
    if proxy_total != 4_008_541:
        raise ValueError(f"building-type proxy total drift: {proxy_total}")

    return [
        [
            "JOIN-B02-WBL011-CORE",
            "county_x_settlement_type_x_construction_period_x_wall_material_x_floor_area_x_comfort_x_heating_mode_x_heating_fuel",
            "geography;construction_period;wall_material;floor_area;comfort;heating_mode;heating_fuel",
            "DATA-B02-KSH-WBL011",
            "OBS",
            "CONTRACTED_NOT_MATERIALIZED",
            "",
            "",
            "dwelling",
            "Only dimensions returned together by one pinned WBL011 query may be treated as an observed joint distribution.",
            "Do not attach building type, primary energy, heat emitter, or temperature as OBS/DER without new joint evidence.",
        ],
        [
            "JOIN-B02-WBL017-BASELINE",
            "county_x_settlement_type_x_construction_period_x_wall_material_x_floor_area_x_comfort_x_combined_heating_fuel_x_heat_pump_presence",
            "geography;construction_period;wall_material;floor_area;comfort;combined_heating_fuel;heat_pump_presence",
            "DATA-B02-KSH-WBL017",
            "OBS",
            "CONTRACTED_NOT_MATERIALIZED",
            "",
            "",
            "dwelling",
            "Only dimensions returned together by one pinned WBL017 query may be treated as an observed joint distribution.",
            "Existing heat-pump presence is a baseline flag, not heat-pump eligibility.",
        ],
        [
            "JOIN-B02-KSH-ENERGY",
            "building_type_x_construction_period_x_primary_energy_bin",
            "building_type;construction_period;primary_energy",
            "DATA-B02-KSH-ENERGY-HTML-2025",
            "MODELLED",
            "MATERIALIZED",
            944,
            4_575_790,
            "dwelling",
            "Building type and construction period may carry the published KSH-modelled primary-energy distribution.",
            "Do not inherit OBS status or distribute the modelled cells across WBL geography, wall, area, comfort, heating, or fuel margins.",
        ],
        [
            "JOIN-B02-BUILDING-TYPE-PROXY",
            "settlement_type_x_building_type",
            "settlement_type;building_type",
            "DATA-B02-KSH-HOUSING-SURVEY-2015;DATA-B02-KSH-WBL011",
            "ASS",
            "MATERIALIZED",
            8,
            proxy_total,
            "dwelling",
            "The 2015 occupied-dwelling building-type share may be applied only at the four contracted 2022 settlement-type totals.",
            "Do not propagate the proxy into county, construction-period, wall, area, comfort, heating-mode, or fuel subcells.",
        ],
        [
            "JOIN-B02-OENY-EMITTER",
            "document_x_heat_emitter_x_design_temperature",
            "heat_emitter;design_supply_temperature;design_return_temperature",
            "",
            "Q",
            "NOT_ACQUIRED",
            "",
            "",
            "document",
            "No join is permitted until an approved anonymised sample passes the P1-F protocol.",
            "Do not infer emitter type or design temperature from heating mode, fuel, proposal fields, or the 55/45 C reference system.",
        ],
        [
            "JOIN-B02-FULL-ARCHETYPE",
            "geography_x_building_type_x_construction_period_x_wall_x_area_x_comfort_x_heating_x_fuel_x_primary_energy_x_heat_emitter_x_temperature",
            "geography;building_type;construction_period;wall_material;floor_area;comfort;heating_mode;heating_fuel;primary_energy;heat_emitter;design_temperature",
            "",
            "Q",
            "NOT_IDENTIFIED",
            "",
            "",
            "dwelling",
            "A full joint table requires new joint evidence or an explicitly approved statistical model with uncertainty and calibration.",
            "Cross-multiplying the available margins under an undocumented independence assumption is prohibited.",
        ],
    ]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, default=DEFAULT_DATA)
    parser.add_argument("--retrieved-at", default="2026-08-12")
    args = parser.parse_args()

    benchmarks_path = args.data_dir / BENCHMARK_FILE
    distribution_path = args.data_dir / DISTRIBUTION_FILE
    proxy_path = args.data_dir / PROXY_FILE
    inputs = [benchmarks_path, distribution_path, proxy_path]
    for path in inputs:
        if not path.is_file():
            raise FileNotFoundError(path)

    benchmarks = read_csv(benchmarks_path)
    distributions = read_csv(distribution_path)
    proxy_rows = read_csv(proxy_path)
    coverage_rows, controls = build_coverage_rows(benchmarks, distributions)
    joinability_rows = build_joinability_rows(proxy_rows)

    coverage_path = args.data_dir / COVERAGE_FILE
    joinability_path = args.data_dir / JOINABILITY_FILE
    manifest_path = args.data_dir / MANIFEST_FILE
    write_csv(
        coverage_path,
        [
            "coverage_cell_id",
            "source_id",
            "reference_year",
            "regulation",
            "building_type",
            "construction_period",
            "modelled_dwelling_count",
            "modelled_dwelling_share",
            "dwelling_count_rank_desc",
            "cumulative_modelled_dwelling_share_desc",
            "published_energy_bin_count",
            "positive_energy_bin_count",
            "zero_energy_bin_count",
            "minimum_positive_energy_bin_kwh_m2_year",
            "maximum_positive_energy_bin_kwh_m2_year",
            "minimum_positive_bin_dwelling_count",
            "maximum_bin_dwelling_count",
            "evidence_status",
            "source_evidence_status",
            "notes",
        ],
        coverage_rows,
    )
    write_csv(
        joinability_path,
        [
            "join_id",
            "grain",
            "dimensions",
            "source_dataset_ids",
            "evidence_status",
            "materialization_status",
            "record_count",
            "population_count",
            "unit",
            "permitted_link",
            "prohibited_inference",
        ],
        joinability_rows,
    )

    controls.update(
        {
            "building_type_proxy_rows": len(proxy_rows),
            "building_type_proxy_dwellings": sum(
                int(row["proxy_2022_dwelling_count"]) for row in proxy_rows
            ),
            "joinability_rows": len(joinability_rows),
            "full_joint_evidence_status": "Q",
        }
    )
    manifest = {
        "schema_version": "1.0",
        "module_id": "B02",
        "retrieved_at": args.retrieved_at,
        "method": {
            "coverage": "rank and cumulative share over the 16 published KSH-modelled building-type x construction-period cells",
            "rarity": "exact positive/zero energy-bin counts and extrema; no arbitrary rare-cell threshold",
            "joinability": "fail-closed grain inventory; separate margins are not cross-multiplied",
        },
        "inputs": {
            path.name: {"sha256": sha256(path), "bytes": path.stat().st_size}
            for path in inputs
        },
        "controls": controls,
        "outputs": {
            path.name: {"sha256": sha256(path), "bytes": path.stat().st_size}
            for path in (coverage_path, joinability_path)
        },
    }
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(
        "VALID: B02 archetype coverage "
        f"cells={controls['benchmark_cells']} bins={controls['distribution_bins']} "
        f"positive_bins={controls['positive_distribution_bins']} "
        f"zero_bins={controls['zero_distribution_bins']} full_joint=Q"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
