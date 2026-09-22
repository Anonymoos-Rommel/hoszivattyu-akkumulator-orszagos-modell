"""B05-P7 representative observed product-cohort performance envelope.

National/programme inference does not require one exact product to cover every
operating point. P7 admits a bounded cohort envelope only at coordinates where
multiple observed products from at least two manufacturers share the exact same
outdoor/supply condition.

PRODUCT-COHORT ENVELOPE != PRODUCT-SPECIFIC PERFORMANCE MAP
CROSS-MANUFACTURER COMMON POINT != NATIONAL MARKET SHARE
MISSING COMMON POINT != LICENSE TO EXTRAPOLATE
OPERATING LIMIT != PERFORMANCE POINT
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
POINTS = ROOT / "data" / "processed" / "heat_pump_performance_points.csv"

MANUFACTURER_BY_PREFIX = {
    "VAILLANT-": "VAILLANT",
    "STIEBEL-": "STIEBEL_ELTRON",
}


@dataclass(frozen=True)
class CohortEnvelope:
    outdoor_temperature_c: float
    supply_temperature_c: float
    equipment_count: int
    manufacturer_count: int
    capacity_min_kw: float
    capacity_max_kw: float
    electrical_input_min_kw: float
    electrical_input_max_kw: float
    cop_min: float
    cop_max: float
    status: str
    source_ids: tuple[str, ...]


def _manufacturer(equipment_id: str) -> str:
    for prefix, manufacturer in MANUFACTURER_BY_PREFIX.items():
        if equipment_id.startswith(prefix):
            return manufacturer
    return "UNKNOWN"


def _observed_rows() -> list[dict[str, str]]:
    with POINTS.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    return [
        row for row in rows
        if row["evidence_status"] == "OBS"
        and row["thermal_capacity_kW"] != ""
        and row["electrical_input_kW"] != ""
        and row["COP"] != ""
        and _manufacturer(row["equipment_id"]) != "UNKNOWN"
    ]


def envelope_at(
    outdoor_temperature_c: float,
    supply_temperature_c: float,
) -> CohortEnvelope:
    rows = [
        row for row in _observed_rows()
        if float(row["outdoor_temperature_C"]) == float(outdoor_temperature_c)
        and float(row["supply_temperature_C"]) == float(supply_temperature_c)
    ]
    if not rows:
        raise ValueError("no observed product points at requested coordinate")

    equipment = {row["equipment_id"] for row in rows}
    manufacturers = {_manufacturer(row["equipment_id"]) for row in rows}
    capacities = [float(row["thermal_capacity_kW"]) for row in rows]
    inputs = [float(row["electrical_input_kW"]) for row in rows]
    cops = [float(row["COP"]) for row in rows]

    status = (
        "QUALIFIED_CROSS_MANUFACTURER_COHORT_ENVELOPE"
        if len(manufacturers) >= 2
        else "CALIBRATION_ONLY_SINGLE_MANUFACTURER_COHORT"
    )

    return CohortEnvelope(
        outdoor_temperature_c=float(outdoor_temperature_c),
        supply_temperature_c=float(supply_temperature_c),
        equipment_count=len(equipment),
        manufacturer_count=len(manufacturers),
        capacity_min_kw=min(capacities),
        capacity_max_kw=max(capacities),
        electrical_input_min_kw=min(inputs),
        electrical_input_max_kw=max(inputs),
        cop_min=min(cops),
        cop_max=max(cops),
        status=status,
        source_ids=tuple(sorted({row["source_id"] for row in rows})),
    )


def materializable_coordinates() -> tuple[tuple[float, float], ...]:
    coordinates = sorted({
        (float(row["outdoor_temperature_C"]), float(row["supply_temperature_C"]))
        for row in _observed_rows()
    })
    return tuple(coordinates)


def qualified_cross_manufacturer_coordinates() -> tuple[tuple[float, float], ...]:
    return tuple(
        coordinate
        for coordinate in materializable_coordinates()
        if envelope_at(*coordinate).status
        == "QUALIFIED_CROSS_MANUFACTURER_COHORT_ENVELOPE"
    )


def national_envelope_boundary() -> tuple[str, ...]:
    return (
        "COHORT_ENVELOPE_MAY_SUPPORT_BOUNDED_PROGRAMME_INFERENCE",
        "COHORT_ENVELOPE_CANNOT_AUTHORIZE_A_SPECIFIC_PRODUCT",
        "NO_OUT_OF_COORDINATE_EXTRAPOLATION",
        "NO_MARKET_SHARE_CLAIM_FROM_PRODUCT_COUNT",
    )
