"""B01-P3 exact non-district-heated occupied-dwelling population projection.

Consumes only the committed B02 WBL011_HEATING_FUEL OBS projection.
No rounded shares, utility-customer counts, cross-projection joins, technical
eligibility, or programme selection are inferred here.

Core boundary:

OCCUPIED DWELLING != NON-DISTRICT-HEATED DWELLING != TECHNICALLY ELIGIBLE
DWELLING != PROGRAMME PARTICIPANT.
"""

from __future__ import annotations

import csv
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


SOURCE_PROJECTION = "WBL011_HEATING_FUEL"
DISTRICT_HEATING_CODE = "HEAT12"
ALLOWED_HEATING_CODES = frozenset({"HEAT111", "HEAT112", "HEAT12", "NHEAT"})
EXPECTED_OCCUPIED_DWELLINGS = 4_008_541
EXPECTED_DISTRICT_HEATED_DWELLINGS = 618_724
EXPECTED_NON_DISTRICT_HEATED_DWELLINGS = 3_389_817


class B01PopulationError(ValueError):
    """Raised when source rows violate the frozen B02/P3 contract."""


@dataclass(frozen=True)
class PopulationRow:
    county_code: str
    county_name_hu: str
    settlement_type_code: str
    settlement_type_name_hu: str
    occupied_dwellings: int
    district_heated_dwellings: int
    non_district_heated_dwellings: int
    evidence_status: str = "DER"
    source_projection: str = SOURCE_PROJECTION


def _positive_int(text: str, field: str) -> int:
    try:
        value = int(text)
    except (TypeError, ValueError) as exc:
        raise B01PopulationError(f"{field} must be an integer") from exc
    if value <= 0:
        raise B01PopulationError(f"{field} must be positive")
    return value


def aggregate_rows(rows: Iterable[dict[str, str]]) -> tuple[PopulationRow, ...]:
    """Aggregate exact WBL011 heating-fuel OBS cells by county and settlement type."""
    totals: dict[tuple[str, str, str, str], list[int]] = defaultdict(lambda: [0, 0])
    seen = 0
    for row in rows:
        if row.get("projection_id") != SOURCE_PROJECTION:
            continue
        seen += 1
        if row.get("evidence_status") != "OBS":
            raise B01PopulationError("WBL011_HEATING_FUEL source rows must remain OBS")
        if row.get("occupancy_code") != "DW_OC":
            raise B01PopulationError("population base must remain occupied dwellings only")
        heating_code = row.get("heating_mode_code", "")
        if heating_code not in ALLOWED_HEATING_CODES:
            raise B01PopulationError(f"unexpected heating mode code: {heating_code!r}")
        value = _positive_int(row.get("dwelling_count", ""), "dwelling_count")
        key = (
            row.get("county_code", ""),
            row.get("county_name_hu", ""),
            row.get("settlement_type_code", ""),
            row.get("settlement_type_name_hu", ""),
        )
        if not all(key):
            raise B01PopulationError("county and settlement-type identity must be complete")
        totals[key][0] += value
        if heating_code == DISTRICT_HEATING_CODE:
            totals[key][1] += value

    if seen != 7_682:
        raise B01PopulationError(f"expected 7,682 WBL011_HEATING_FUEL rows, got {seen}")

    output = tuple(
        PopulationRow(
            county_code=key[0],
            county_name_hu=key[1],
            settlement_type_code=key[2],
            settlement_type_name_hu=key[3],
            occupied_dwellings=values[0],
            district_heated_dwellings=values[1],
            non_district_heated_dwellings=values[0] - values[1],
        )
        for key, values in sorted(totals.items())
    )

    occupied = sum(row.occupied_dwellings for row in output)
    district = sum(row.district_heated_dwellings for row in output)
    non_district = sum(row.non_district_heated_dwellings for row in output)
    if occupied != EXPECTED_OCCUPIED_DWELLINGS:
        raise B01PopulationError(f"occupied-dwelling control drift: {occupied}")
    if district != EXPECTED_DISTRICT_HEATED_DWELLINGS:
        raise B01PopulationError(f"district-heating control drift: {district}")
    if non_district != EXPECTED_NON_DISTRICT_HEATED_DWELLINGS:
        raise B01PopulationError(f"non-district control drift: {non_district}")
    if district + non_district != occupied:
        raise B01PopulationError("population conservation failed")
    return output


def load_committed_projection(path: Path) -> tuple[PopulationRow, ...]:
    with path.open(encoding="utf-8", newline="") as handle:
        return aggregate_rows(csv.DictReader(handle))


def county_projection(rows: Iterable[PopulationRow]) -> tuple[PopulationRow, ...]:
    """Roll settlement-type rows up to exact county totals without new inference."""
    totals: dict[tuple[str, str], list[int]] = defaultdict(lambda: [0, 0, 0])
    for row in rows:
        key = (row.county_code, row.county_name_hu)
        totals[key][0] += row.occupied_dwellings
        totals[key][1] += row.district_heated_dwellings
        totals[key][2] += row.non_district_heated_dwellings
    return tuple(
        PopulationRow(
            county_code=key[0],
            county_name_hu=key[1],
            settlement_type_code="ALL",
            settlement_type_name_hu="Összes településtípus",
            occupied_dwellings=values[0],
            district_heated_dwellings=values[1],
            non_district_heated_dwellings=values[2],
        )
        for key, values in sorted(totals.items())
    )
