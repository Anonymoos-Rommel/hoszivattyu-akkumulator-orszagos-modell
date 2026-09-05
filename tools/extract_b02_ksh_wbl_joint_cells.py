"""Materialize bounded, observed B02 projections from KSH Census WBL flows.

The extractor materializes source-native observed projections only. It never
cross-multiplies margins and never interprets an API combination that was not
returned as a zero observation.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import re
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = ROOT / "data" / "processed" / "b02"
API_BASE = "https://nepszamlalas2022.ksh.hu"
PINNED_VERSION = "V67"
SOURCE_ID = "SRC-B02-KSH-CENSUS-API-2022"

COUNTIES = (
    "HU110", "HU120", "HU211", "HU212", "HU213", "HU221", "HU222",
    "HU223", "HU231", "HU232", "HU233", "HU311", "HU312", "HU313",
    "HU321", "HU322", "HU323", "HU331", "HU332", "HU333",
)
SETTLEMENT_TYPES = ("FV", "MJV", "EV", "K")
PERIODS = (
    "Y_LT1919", "Y1919-1945", "Y1946-1960", "Y1961-1980",
    "Y1981-2000", "Y2001-2010", "Y_GE2011",
)
WALLS = ("WALL1", "WALL2", "WALL3", "WALL5", "WALL6")
FLOOR_AREAS = (
    "SQM_LT30", "SQM30-39", "SQM40-49", "SQM50-59", "SQM60-79",
    "SQM80-99", "SQM100-119", "SQM_GE120",
)
COMFORTS = ("COMF1", "COMF2", "COMF3", "COMF4", "COMF5")
# The published CL_FUTES_TOH parent pointer places NHEAT21 under HEAT12, while
# the API returns NHEAT21 as an exact duplicate of NHEAT.  The four codes below
# form the disjoint analytical partition that reconciles to the occupied-
# dwelling universe; selecting all childless codes would double-count NHEAT.
HEATING_MODES = ("HEAT111", "HEAT112", "HEAT12", "NHEAT")
HEATING_FUELS = (
    "FUEL11", "FUEL12", "FUEL13", "FUEL14", "FUEL21", "FUEL22",
    "FUEL23", "FUEL3",
)
COMBINED_HEATING_FUELS = (
    "01", "02", "03", "04-05", "06-12", "13", "14", "15",
    "16-17", "18", "19", "20-24", "25",
)
PRESENCE_CODES = ("1", "0", "9")

EXPECTED_DIMENSIONS = {
    "WBL011": (
        "TIME_PERIOD", "TERUL_GEO3", "TERUL_TELTIP2", "LAKAS_OCS",
        "EPEV_POC1", "FALA_V", "LAT_V", "KOMF", "FUTES_TOH", "FUTAGOK",
    ),
    "WBL017": (
        "TIME_PERIOD22", "TERUL_GEO3", "TERUL_TELTIP2", "LAKAS_OCS",
        "EPEV_POC1", "FALA_V", "LAT_V", "KOMF", "FUTMODAG_V3",
        "INTERNET", "LEGKONDI", "HOSZIV", "NAPELEM", "NAPKOLL",
    ),
}


@dataclass(frozen=True)
class Projection:
    projection_id: str
    prefix: str
    dataflow_id: str
    grain: str
    selections: dict[str, tuple[str, ...]]
    varied_dimensions: tuple[str, ...]


PROJECTIONS = (
    Projection(
        projection_id="WBL011_ENVELOPE",
        prefix="ENV",
        dataflow_id="WBL011",
        grain=(
            "county_x_settlement_type_x_construction_period_x_wall_material_"
            "x_floor_area_x_comfort"
        ),
        selections={
            "TIME_PERIOD": ("2022",),
            "TERUL_GEO3": (),
            "TERUL_TELTIP2": SETTLEMENT_TYPES,
            "LAKAS_OCS": ("DW_OC",),
            "EPEV_POC1": PERIODS,
            "FALA_V": WALLS,
            "LAT_V": FLOOR_AREAS,
            "KOMF": COMFORTS,
            "FUTES_TOH": ("TOTAL",),
            "FUTAGOK": ("TOTAL",),
        },
        varied_dimensions=(
            "TERUL_GEO3", "TERUL_TELTIP2", "EPEV_POC1", "FALA_V",
            "LAT_V", "KOMF",
        ),
    ),
    Projection(
        projection_id="WBL011_HEATING_FUEL",
        prefix="HEAT",
        dataflow_id="WBL011",
        grain=(
            "county_x_settlement_type_x_construction_period_x_heating_mode_"
            "x_heating_fuel"
        ),
        selections={
            "TIME_PERIOD": ("2022",),
            "TERUL_GEO3": (),
            "TERUL_TELTIP2": SETTLEMENT_TYPES,
            "LAKAS_OCS": ("DW_OC",),
            "EPEV_POC1": PERIODS,
            "FALA_V": ("TOTAL",),
            "LAT_V": ("TOTAL",),
            "KOMF": ("TOTAL",),
            "FUTES_TOH": HEATING_MODES,
            "FUTAGOK": HEATING_FUELS,
        },
        varied_dimensions=(
            "TERUL_GEO3", "TERUL_TELTIP2", "EPEV_POC1", "FUTES_TOH",
            "FUTAGOK",
        ),
    ),
    Projection(
        projection_id="WBL011_FULL_STOCK_JOINT",
        prefix="FULL",
        dataflow_id="WBL011",
        grain=(
            "county_x_settlement_type_x_construction_period_x_wall_material_"
            "x_floor_area_x_comfort_x_heating_mode_x_heating_fuel"
        ),
        selections={
            "TIME_PERIOD": ("2022",),
            "TERUL_GEO3": (),
            "TERUL_TELTIP2": SETTLEMENT_TYPES,
            "LAKAS_OCS": ("DW_OC",),
            "EPEV_POC1": PERIODS,
            "FALA_V": WALLS,
            "LAT_V": FLOOR_AREAS,
            "KOMF": COMFORTS,
            "FUTES_TOH": HEATING_MODES,
            "FUTAGOK": HEATING_FUELS,
        },
        varied_dimensions=(
            "TERUL_GEO3", "TERUL_TELTIP2", "EPEV_POC1", "FALA_V",
            "LAT_V", "KOMF", "FUTES_TOH", "FUTAGOK",
        ),
    ),
    Projection(
        projection_id="WBL017_HEAT_PUMP_BASELINE",
        prefix="HP",
        dataflow_id="WBL017",
        grain=(
            "county_x_settlement_type_x_construction_period_"
            "x_combined_heating_fuel_x_heat_pump_presence"
        ),
        selections={
            "TIME_PERIOD22": ("2022",),
            "TERUL_GEO3": (),
            "TERUL_TELTIP2": SETTLEMENT_TYPES,
            "LAKAS_OCS": ("DW_OC",),
            "EPEV_POC1": PERIODS,
            "FALA_V": ("TOTAL",),
            "LAT_V": ("TOTAL",),
            "KOMF": ("TOTAL",),
            "FUTMODAG_V3": COMBINED_HEATING_FUELS,
            "INTERNET": ("TOTAL",),
            "LEGKONDI": ("TOTAL",),
            "HOSZIV": PRESENCE_CODES,
            "NAPELEM": ("TOTAL",),
            "NAPKOLL": ("TOTAL",),
        },
        varied_dimensions=(
            "TERUL_GEO3", "TERUL_TELTIP2", "EPEV_POC1", "FUTMODAG_V3",
            "HOSZIV",
        ),
    ),
)

OUTPUT_FILE = "ksh_wbl_joint_cells_2022.csv"
COVERAGE_FILE = "ksh_wbl_joint_cell_coverage_2022.csv"
MANIFEST_FILE = "ksh_wbl_joint_manifest.json"


def fetch_bytes(url: str, attempts: int = 3) -> bytes:
    request = Request(url, headers={"User-Agent": "B02-research-extractor/1.0"})
    last_error: Exception | None = None
    for attempt in range(attempts):
        try:
            with urlopen(request, timeout=60) as response:  # noqa: S310
                return response.read()
        except Exception as error:  # noqa: BLE001
            last_error = error
            if attempt + 1 < attempts:
                time.sleep(0.5 * (attempt + 1))
    assert last_error is not None
    raise last_error


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def write_csv(path: Path, headers: list[str], rows: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=headers, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def codelist_id(enumeration: str) -> str:
    match = re.search(r"Codelist=HCSO:([^()]+)", enumeration)
    if not match:
        raise ValueError(f"unrecognised codelist URN: {enumeration!r}")
    return match.group(1)


def read_structure(flow: str) -> tuple[bytes, dict[str, Any], dict[str, dict[str, str]]]:
    url = f"{API_BASE}/api/structure/{flow}/{PINNED_VERSION}"
    raw = fetch_bytes(url)
    payload = json.loads(raw)
    dimensions = sorted(
        payload["data"]["dataStructures"][0]["dataStructureComponents"]
        ["dimensionList"]["dimensions"],
        key=lambda item: item["position"],
    )
    actual = tuple(item["id"] for item in dimensions)
    if actual != EXPECTED_DIMENSIONS[flow]:
        raise ValueError(
            f"{flow} dimension drift: expected={EXPECTED_DIMENSIONS[flow]!r} "
            f"actual={actual!r}"
        )
    codelists = {item["id"]: item for item in payload["data"]["codelists"]}
    labels: dict[str, dict[str, str]] = {}
    available: dict[str, set[str]] = {}
    for dimension in dimensions:
        cid = codelist_id(dimension["localRepresentation"]["enumeration"])
        codes = codelists[cid]["codes"]
        labels[dimension["id"]] = {
            code["id"]: code.get("names", {}).get("hu", code.get("name", code["id"]))
            for code in codes
        }
        available[dimension["id"]] = {code["id"] for code in codes}
    for projection in (item for item in PROJECTIONS if item.dataflow_id == flow):
        for dimension, selected in projection.selections.items():
            if dimension == "TERUL_GEO3":
                selected = COUNTIES
            missing = set(selected) - available[dimension]
            if missing:
                raise ValueError(
                    f"{flow}/{dimension} code drift: missing={sorted(missing)!r}"
                )
    return raw, payload, labels


def query_url(projection: Projection, county: str) -> str:
    dimensions = EXPECTED_DIMENSIONS[projection.dataflow_id]
    parts: list[str] = []
    for dimension in dimensions:
        selected = (county,) if dimension == "TERUL_GEO3" else projection.selections[dimension]
        parts.append(f"{dimension}:{'+'.join(selected)}")
    return (
        f"{API_BASE}/api/dataflows/{projection.dataflow_id}/{PINNED_VERSION}/d/"
        + ",".join(parts)
    )


def frequency_band(value: int | None) -> str:
    if value is None:
        return "NOT_NUMERIC"
    if value == 0:
        return "COUNT_0_RETURNED"
    if value == 1:
        return "COUNT_1"
    if value <= 4:
        return "COUNT_2_4"
    if value <= 9:
        return "COUNT_5_9"
    if value <= 49:
        return "COUNT_10_49"
    if value <= 99:
        return "COUNT_50_99"
    return "COUNT_100_PLUS"


def fetch_query(projection: Projection, county: str) -> dict[str, Any]:
    url = query_url(projection, county)
    raw = fetch_bytes(url)
    payload = json.loads(raw)
    if not isinstance(payload, list):
        raise ValueError(f"unexpected {projection.projection_id}/{county} response")
    return {
        "projection": projection,
        "county": county,
        "query_id": f"KSH-{projection.prefix}-{county}",
        "url": url,
        "raw": raw,
        "payload": payload,
    }


def normalize_rows(
    results: list[dict[str, Any]],
    labels_by_flow: dict[str, dict[str, dict[str, str]]],
    retrieved_at: str,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]]:
    normalized: list[dict[str, Any]] = []
    queries: list[dict[str, Any]] = []
    seen: set[tuple[str, ...]] = set()
    projection_lookup = {item.projection_id: item for item in PROJECTIONS}

    for result in sorted(
        results, key=lambda item: (item["projection"].projection_id, item["county"])
    ):
        projection: Projection = result["projection"]
        labels = labels_by_flow[projection.dataflow_id]
        queries.append(
            {
                "query_id": result["query_id"],
                "projection_id": projection.projection_id,
                "county_code": result["county"],
                "url": result["url"],
                "response_sha256": sha256_bytes(result["raw"]),
                "response_bytes": len(result["raw"]),
                "returned_records": len(result["payload"]),
            }
        )
        for observation in result["payload"]:
            dimensions = EXPECTED_DIMENSIONS[projection.dataflow_id]
            key = (projection.projection_id,) + tuple(
                str(observation.get(dimension, "")) for dimension in dimensions
            )
            if key in seen:
                raise ValueError(f"duplicate observation key: {key!r}")
            seen.add(key)

            for dimension in dimensions:
                actual = str(observation.get(dimension, ""))
                selected = (
                    (result["county"],)
                    if dimension == "TERUL_GEO3"
                    else projection.selections[dimension]
                )
                if actual not in selected:
                    raise ValueError(
                        f"unexpected {projection.projection_id}/{dimension}={actual!r}"
                    )

            raw_value = observation.get("OBS_VALUE")
            try:
                value = int(raw_value) if raw_value not in (None, "") else None
            except (TypeError, ValueError) as error:
                raise ValueError(f"non-integer OBS_VALUE: {observation!r}") from error
            if value is not None and value < 0:
                raise ValueError(f"negative OBS_VALUE: {observation!r}")
            status = observation.get("OBS_STATUS") or ""
            availability = (
                "RETURNED_POSITIVE"
                if value is not None and value > 0
                else "RETURNED_ZERO"
                if value == 0
                else "RETURNED_NON_NUMERIC"
            )
            evidence = "OBS" if value is not None else "Q"

            def code_and_name(dimension: str) -> tuple[str, str]:
                code = str(observation.get(dimension, ""))
                return code, labels[dimension].get(code, code)

            county_code, county_name = code_and_name("TERUL_GEO3")
            settlement_code, settlement_name = code_and_name("TERUL_TELTIP2")
            period_code, period_name = code_and_name("EPEV_POC1")
            wall_code, wall_name = code_and_name("FALA_V")
            area_code, area_name = code_and_name("LAT_V")
            comfort_code, comfort_name = code_and_name("KOMF")
            heating_code = heating_name = fuel_code = fuel_name = ""
            combined_code = combined_name = heat_pump_code = heat_pump_name = ""
            if projection.dataflow_id == "WBL011":
                heating_code, heating_name = code_and_name("FUTES_TOH")
                fuel_code, fuel_name = code_and_name("FUTAGOK")
            else:
                combined_code, combined_name = code_and_name("FUTMODAG_V3")
                heat_pump_code, heat_pump_name = code_and_name("HOSZIV")
            normalized.append(
                {
                    "cell_id": "",
                    "projection_id": projection.projection_id,
                    "source_id": SOURCE_ID,
                    "dataset_id": f"DATA-B02-KSH-{projection.dataflow_id}",
                    "dataflow_id": projection.dataflow_id,
                    "source_version": PINNED_VERSION,
                    "reference_year": 2022,
                    "county_code": county_code,
                    "county_name_hu": county_name,
                    "settlement_type_code": settlement_code,
                    "settlement_type_name_hu": settlement_name,
                    "occupancy_code": str(observation["LAKAS_OCS"]),
                    "construction_period_code": period_code,
                    "construction_period_name_hu": period_name,
                    "wall_material_code": wall_code,
                    "wall_material_name_hu": wall_name,
                    "floor_area_code": area_code,
                    "floor_area_name_hu": area_name,
                    "comfort_code": comfort_code,
                    "comfort_name_hu": comfort_name,
                    "heating_mode_code": heating_code,
                    "heating_mode_name_hu": heating_name,
                    "heating_fuel_code": fuel_code,
                    "heating_fuel_name_hu": fuel_name,
                    "combined_heating_fuel_code": combined_code,
                    "combined_heating_fuel_name_hu": combined_name,
                    "heat_pump_code": heat_pump_code,
                    "heat_pump_name_hu": heat_pump_name,
                    "dwelling_count": "" if value is None else value,
                    "ksh_observation_status": status,
                    "evidence_status": evidence,
                    "availability_status": availability,
                    "frequency_band": frequency_band(value),
                    "query_id": result["query_id"],
                    "retrieved_at": retrieved_at,
                }
            )

    sort_fields = (
        "projection_id", "county_code", "settlement_type_code",
        "construction_period_code", "wall_material_code", "floor_area_code",
        "comfort_code", "heating_mode_code", "heating_fuel_code",
        "combined_heating_fuel_code", "heat_pump_code",
    )
    normalized.sort(key=lambda row: tuple(str(row[field]) for field in sort_fields))
    counters: dict[str, int] = {item.projection_id: 0 for item in PROJECTIONS}
    for row in normalized:
        counters[row["projection_id"]] += 1
        projection = projection_lookup[row["projection_id"]]
        row["cell_id"] = (
            f"WBLCELL-B02-{projection.prefix}-{counters[row['projection_id']]:06d}"
        )

    coverage: list[dict[str, Any]] = []
    controls: dict[str, Any] = {}
    for projection in PROJECTIONS:
        rows = [row for row in normalized if row["projection_id"] == projection.projection_id]
        values = [int(row["dwelling_count"]) for row in rows if row["dwelling_count"] != ""]
        candidate_count = len(COUNTIES) * math.prod(
            len(projection.selections[dimension])
            for dimension in projection.varied_dimensions
            if dimension != "TERUL_GEO3"
        )
        bands = {name: 0 for name in (
            "COUNT_0_RETURNED", "COUNT_1", "COUNT_2_4", "COUNT_5_9",
            "COUNT_10_49", "COUNT_50_99", "COUNT_100_PLUS", "NOT_NUMERIC",
        )}
        for row in rows:
            bands[row["frequency_band"]] += 1
        coverage_row = {
            "projection_id": projection.projection_id,
            "dataflow_id": projection.dataflow_id,
            "grain": projection.grain,
            "cartesian_candidate_combinations": candidate_count,
            "returned_records": len(rows),
            "unreturned_candidate_combinations": candidate_count - len(rows),
            "returned_record_share": format(len(rows) / candidate_count, ".15f"),
            "returned_numeric_dwelling_sum": sum(values),
            "returned_zero_records": bands["COUNT_0_RETURNED"],
            "count_1_records": bands["COUNT_1"],
            "count_2_4_records": bands["COUNT_2_4"],
            "count_5_9_records": bands["COUNT_5_9"],
            "count_10_49_records": bands["COUNT_10_49"],
            "count_50_99_records": bands["COUNT_50_99"],
            "count_100_plus_records": bands["COUNT_100_PLUS"],
            "minimum_returned_dwelling_count": min(values) if values else "",
            "maximum_returned_dwelling_count": max(values) if values else "",
            "evidence_status": "DER",
            "unreturned_interpretation": (
                "Not returned by the API within the Cartesian candidate grid; "
                "not proven zero and may be structurally invalid or unavailable."
            ),
        }
        coverage.append(coverage_row)
        controls[projection.projection_id] = coverage_row.copy()
    return normalized, coverage, {"queries": queries, "projections": controls}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--retrieved-at", default="2026-08-12")
    parser.add_argument("--workers", type=int, default=6)
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)

    structures: dict[str, bytes] = {}
    labels_by_flow: dict[str, dict[str, dict[str, str]]] = {}
    for flow in EXPECTED_DIMENSIONS:
        raw, _payload, labels = read_structure(flow)
        structures[flow] = raw
        labels_by_flow[flow] = labels

    jobs = [(projection, county) for projection in PROJECTIONS for county in COUNTIES]
    results: list[dict[str, Any]] = []
    with ThreadPoolExecutor(max_workers=args.workers) as executor:
        futures = {
            executor.submit(fetch_query, projection, county): (projection, county)
            for projection, county in jobs
        }
        for future in as_completed(futures):
            results.append(future.result())

    rows, coverage, details = normalize_rows(results, labels_by_flow, args.retrieved_at)
    output_path = args.output_dir / OUTPUT_FILE
    coverage_path = args.output_dir / COVERAGE_FILE
    manifest_path = args.output_dir / MANIFEST_FILE
    write_csv(output_path, list(rows[0]), rows)
    write_csv(coverage_path, list(coverage[0]), coverage)

    manifest = {
        "schema_version": "1.0",
        "module_id": "B02",
        "source_id": SOURCE_ID,
        "source_version": PINNED_VERSION,
        "retrieved_at": args.retrieved_at,
        "source_attribution": "Forrás: Központi Statisztikai Hivatal (KSH)",
        "method": {
            "universe": "2022 occupied conventional dwellings (LAKAS_OCS=DW_OC)",
            "materialization": (
                "Four source-native observed projections; WBL011_FULL_STOCK_JOINT is "
                "returned directly by KSH; no synthetic cross-projection join "
                "or independence multiplication."
            ),
            "leaf_rule": (
                "Explicit leaf codes are selected for varied dimensions; TOTAL is "
                "used only to hold non-varied dimensions fixed. FUTES_TOH uses the "
                "disjoint analytical partition HEAT111+HEAT112+HEAT12+NHEAT because "
                "the published NHEAT21 parent pointer is inconsistent and its API "
                "cells duplicate NHEAT exactly."
            ),
            "missing_rule": (
                "An unreturned candidate combination is not encoded as zero; it may "
                "be structurally invalid, zero, suppressed, or otherwise unavailable."
            ),
            "frequency_bands": (
                "Descriptive exact-count bands only; they are not KSH suppression "
                "thresholds and do not define statistical reliability."
            ),
            "eligibility_rule": (
                "HOSZIV records existing equipment presence only and is not a heat-"
                "pump technical-eligibility label."
            ),
        },
        "structures": {
            flow: {
                "url": f"{API_BASE}/api/structure/{flow}/{PINNED_VERSION}",
                "sha256": sha256_bytes(raw),
                "bytes": len(raw),
                "dimensions": list(EXPECTED_DIMENSIONS[flow]),
            }
            for flow, raw in structures.items()
        },
        "queries": details["queries"],
        "controls": {
            "query_count": len(details["queries"]),
            "county_count": len(COUNTIES),
            "projection_count": len(PROJECTIONS),
            "wbl011_full_stock_joint_materialization_status": "MATERIALIZED",
            "projections": details["projections"],
            "full_cross_projection_joint_status": "Q",
            "technical_eligibility_status": "Q",
        },
        "outputs": {
            output_path.name: {
                "sha256": hashlib.sha256(output_path.read_bytes()).hexdigest(),
                "bytes": output_path.stat().st_size,
                "records": len(rows),
            },
            coverage_path.name: {
                "sha256": hashlib.sha256(coverage_path.read_bytes()).hexdigest(),
                "bytes": coverage_path.stat().st_size,
                "records": len(coverage),
            },
        },
    }
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    summaries = ", ".join(
        f"{row['projection_id']}={row['returned_records']}"
        for row in coverage
    )
    print(
        f"VALID: B02 KSH WBL joint projections queries={len(jobs)} "
        f"cells={len(rows)} {summaries} full_wbl011_joint=MATERIALIZED "
        f"full_archetype=Q eligibility=Q"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
