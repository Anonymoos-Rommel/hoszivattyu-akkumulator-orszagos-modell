"""B07-P3 bounded household-battery product-cohort envelope.

P3 materializes only cross-product quantities that are semantically comparable
across the existing canonical product evidence.

PRODUCT COHORT != PRODUCT-SPECIFIC RUNTIME
WARRANTY RETENTION != DEGRADATION LAW
MANUFACTURING LOCATION != CELL OR SUPPLY-CHAIN ORIGIN
BATTERY-ONLY EFFICIENCY != WHOLE-SYSTEM EFFICIENCY
MISSING PRODUCT FIELD != LICENSE TO IMPUTE
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PRODUCT_EVIDENCE = ROOT / "data" / "processed" / "battery_product_evidence.csv"


@dataclass(frozen=True)
class BatteryCohortEnvelope:
    product_count: int
    manufacturer_count: int
    chemistry_count: int
    nominal_capacity_min_kwh: float
    nominal_capacity_max_kwh: float
    max_charge_power_min_kw: float
    max_charge_power_max_kw: float
    max_discharge_power_min_kw: float
    max_discharge_power_max_kw: float
    warranty_years_min: int
    warranty_years_max: int
    warranty_cycles_min: int
    warranty_cycles_max: int
    warranty_retention_min_pct: float
    warranty_retention_max_pct: float
    common_warranty_years: int | None
    common_warranty_retention_pct: float | None
    status: str
    residuals: tuple[str, ...]


def _rows() -> list[dict[str, str]]:
    with PRODUCT_EVIDENCE.open(encoding="utf-8", newline="") as handle:
        rows = [row for row in csv.DictReader(handle) if row["status"] == "PARTIAL"]
    if len(rows) < 2:
        raise ValueError("B07-P3 requires at least two canonical product records")
    return rows


def _required_float(rows: list[dict[str, str]], field: str) -> list[float]:
    values: list[float] = []
    for row in rows:
        value = row[field].strip()
        if value == "":
            raise ValueError(f"cohort field is incomplete: {field}")
        values.append(float(value))
    return values


def _required_int(rows: list[dict[str, str]], field: str) -> list[int]:
    return [int(float(x)) for x in _required_float(rows, field)]


def bounded_product_cohort() -> BatteryCohortEnvelope:
    rows = _rows()

    capacities = _required_float(rows, "nominal_capacity_kwh")
    charge = _required_float(rows, "max_charge_power_kw")
    discharge = _required_float(rows, "max_discharge_power_kw")
    years = _required_int(rows, "warranty_years")
    cycles = _required_int(rows, "warranty_cycles")
    retention = _required_float(rows, "warranty_retention_pct")

    common_years = years[0] if len(set(years)) == 1 else None
    common_retention = retention[0] if len(set(retention)) == 1 else None

    return BatteryCohortEnvelope(
        product_count=len(rows),
        manufacturer_count=len({row["manufacturer"] for row in rows}),
        chemistry_count=len({row["chemistry"] for row in rows}),
        nominal_capacity_min_kwh=min(capacities),
        nominal_capacity_max_kwh=max(capacities),
        max_charge_power_min_kw=min(charge),
        max_charge_power_max_kw=max(charge),
        max_discharge_power_min_kw=min(discharge),
        max_discharge_power_max_kw=max(discharge),
        warranty_years_min=min(years),
        warranty_years_max=max(years),
        warranty_cycles_min=min(cycles),
        warranty_cycles_max=max(cycles),
        warranty_retention_min_pct=min(retention),
        warranty_retention_max_pct=max(retention),
        common_warranty_years=common_years,
        common_warranty_retention_pct=common_retention,
        status="QUALIFIED_BOUNDED_PRODUCT_COHORT",
        residuals=(
            "PRODUCT_SPECIFIC_ONE_WAY_AC_GRID_EFFICIENCY_REQUIRED_FOR_RUNTIME",
            "VALIDATED_DEGRADATION_MODEL_REQUIRED_FOR_RUNTIME_AGING",
            "SECOND_PRODUCT_TEMPERATURE_ENVELOPE_REQUIRED_FOR_COHORT_DERATING",
            "CELL_INVERTER_UPSTREAM_ORIGIN_REQUIRED_FOR_SUPPLY_CHAIN_CLAIMS",
        ),
    )


def warranty_lifecycle_boundary() -> tuple[str, ...]:
    return (
        "WARRANTY_RETENTION_MAY_BOUND_CONTRACTUAL_LIFECYCLE_SCENARIOS",
        "WARRANTY_RETENTION_CANNOT_BE_INTERPOLATED_AS_DEGRADATION_CURVE",
        "WARRANTY_CYCLE_LIMIT_CANNOT_BE_CONVERTED_TO_ANNUAL_DEGRADATION_RATE",
    )


def efficiency_boundary() -> tuple[str, ...]:
    return (
        "VARTA_BATTERY_ONLY_EFFICIENCY_NOT_COMPARABLE_TO_SONNEN_WHOLE_SYSTEM_EXAMPLE",
        "NO_SQUARE_ROOT_SPLIT_TO_ONE_WAY_EFFICIENCIES",
        "PRODUCT_SPECIFIC_RUNTIME_EFFICIENCY_REMAINS_FAIL_CLOSED",
    )


def origin_boundary() -> tuple[str, ...]:
    return (
        "GERMAN_MANUFACTURING_CLAIM_IS_PRODUCT_ASSEMBLY_EVIDENCE_ONLY",
        "MANUFACTURING_LOCATION_DOES_NOT_PROVE_CELL_OR_INVERTER_ORIGIN",
        "SUPPLY_CHAIN_ORIGIN_IS_PROCUREMENT_POLICY_EVIDENCE_NOT_SOC_PHYSICS",
    )
