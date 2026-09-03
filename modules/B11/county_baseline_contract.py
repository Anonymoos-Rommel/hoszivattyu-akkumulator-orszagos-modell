"""B11-P2 county household-gas utility baseline contract.

Core rule:

    KSH UTILITY CUSTOMER != KSH HEATING CUSTOMER
    != CENSUS GAS-USING DWELLING != PROGRAMME PARTICIPANT

The 2024 KSH territorial statistical yearbook provides county/capital utility
counts and household gas sales. These rows are an observed physical baseline,
not authority to allocate gas volume to programme households or heating end use.
"""

from __future__ import annotations

from dataclasses import dataclass
import csv
import math
from pathlib import Path


EXPECTED_COUNTY_CODES = {
    "HU110", "HU120", "HU211", "HU212", "HU213", "HU221", "HU222",
    "HU223", "HU231", "HU232", "HU233", "HU311", "HU312", "HU313",
    "HU321", "HU322", "HU323", "HU331", "HU332", "HU333",
}

NATIONAL_HOUSEHOLD_CONSUMERS_2024 = 3_241_811
NATIONAL_HEATING_CONSUMERS_2024 = 3_022_115
NATIONAL_HOUSEHOLD_GAS_SOLD_THOUSAND_M3_2024 = 2_654_311
NATIONAL_MONTHLY_M3_PER_HOUSEHOLD_2024 = 68.2


@dataclass(frozen=True)
class CountyGasBaseline:
    county_code: str
    county_name: str
    household_consumers: int
    heating_consumers: int
    household_gas_sold_thousand_m3: int
    monthly_m3_per_household: float
    evidence_status: str
    source_id: str


@dataclass(frozen=True)
class CountyBaselineReconciliation:
    county_count: int
    household_consumers_sum: int
    heating_consumers_sum: int
    household_gas_sold_thousand_m3_sum: int
    national_gas_rounding_delta_thousand_m3: int
    derived_monthly_m3_per_household: float
    programme_volume_authorized: bool


def load_county_baseline(path: str | Path) -> tuple[CountyGasBaseline, ...]:
    rows: list[CountyGasBaseline] = []
    with Path(path).open("r", encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            rows.append(
                CountyGasBaseline(
                    county_code=row["county_code"],
                    county_name=row["county_name"],
                    household_consumers=int(row["household_consumers"]),
                    heating_consumers=int(row["heating_consumers"]),
                    household_gas_sold_thousand_m3=int(row["household_gas_sold_thousand_m3"]),
                    monthly_m3_per_household=float(row["monthly_m3_per_household"]),
                    evidence_status=row["evidence_status"],
                    source_id=row["source_id"],
                )
            )
    return tuple(rows)


def validate_county_baseline(rows: tuple[CountyGasBaseline, ...]) -> CountyBaselineReconciliation:
    codes = [row.county_code for row in rows]
    if len(codes) != len(set(codes)):
        raise ValueError("duplicate county code")
    if set(codes) != EXPECTED_COUNTY_CODES:
        raise ValueError("county baseline must contain the exact 20 county/capital codes")

    for row in rows:
        if row.evidence_status != "OBS":
            raise ValueError("county utility baseline rows must remain OBS")
        if not row.source_id:
            raise ValueError("source lineage is required")
        if row.household_consumers < 0 or row.heating_consumers < 0:
            raise ValueError("consumer counts cannot be negative")
        if row.heating_consumers > row.household_consumers:
            raise ValueError("heating consumers cannot exceed household consumers")
        if row.household_gas_sold_thousand_m3 < 0:
            raise ValueError("household gas sales cannot be negative")
        if not math.isfinite(row.monthly_m3_per_household) or row.monthly_m3_per_household < 0:
            raise ValueError("monthly household gas use must be finite and non-negative")

    household_sum = sum(row.household_consumers for row in rows)
    heating_sum = sum(row.heating_consumers for row in rows)
    gas_sum = sum(row.household_gas_sold_thousand_m3 for row in rows)

    if household_sum != NATIONAL_HOUSEHOLD_CONSUMERS_2024:
        raise ValueError("county household-consumer sum does not match KSH national control")
    if heating_sum != NATIONAL_HEATING_CONSUMERS_2024:
        raise ValueError("county heating-consumer sum does not match KSH national control")

    gas_delta = gas_sum - NATIONAL_HOUSEHOLD_GAS_SOLD_THOUSAND_M3_2024
    if abs(gas_delta) > 1:
        raise ValueError("county gas-volume sum exceeds KSH source-native rounding tolerance")

    derived_monthly = gas_sum * 1000.0 / household_sum / 12.0
    if round(derived_monthly, 1) != NATIONAL_MONTHLY_M3_PER_HOUSEHOLD_2024:
        raise ValueError("derived monthly household use does not reconcile to KSH control")

    return CountyBaselineReconciliation(
        county_count=len(rows),
        household_consumers_sum=household_sum,
        heating_consumers_sum=heating_sum,
        household_gas_sold_thousand_m3_sum=gas_sum,
        national_gas_rounding_delta_thousand_m3=gas_delta,
        derived_monthly_m3_per_household=derived_monthly,
        programme_volume_authorized=False,
    )
