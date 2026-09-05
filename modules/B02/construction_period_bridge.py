from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable


SOURCE_PERIODS = ("2011–2015", "2016–2022")
TARGET_PERIOD = "Y_GE2011"
SUPPORTED_BUILDING_TYPES = ("FAMILY_HOUSE", "MULTI_DWELLING")
EXPECTED_ENERGY_BINS = tuple(range(10, 600, 10))
SOURCE_EVIDENCE_STATUS = "MODELLED"
OUTPUT_EVIDENCE_STATUS = "DER"


@dataclass(frozen=True)
class EnergyDistributionRecord:
    building_type: str
    construction_period: str
    energy_bin_kwh_m2_year: int
    dwelling_count: int
    evidence_status: str


@dataclass(frozen=True)
class BridgedEnergyBin:
    building_type: str
    construction_period: str
    energy_bin_kwh_m2_year: int
    dwelling_count: int
    evidence_status: str
    source_periods: tuple[str, str]
    source_evidence_status: str


def _validate_record(record: EnergyDistributionRecord) -> None:
    if record.building_type not in SUPPORTED_BUILDING_TYPES:
        raise ValueError(f"unsupported building type: {record.building_type}")
    if record.construction_period not in SOURCE_PERIODS:
        raise ValueError(f"unsupported source period: {record.construction_period}")
    if record.evidence_status != SOURCE_EVIDENCE_STATUS:
        raise ValueError(
            f"source evidence must remain {SOURCE_EVIDENCE_STATUS}: {record.evidence_status}"
        )
    if record.energy_bin_kwh_m2_year not in EXPECTED_ENERGY_BINS:
        raise ValueError(f"unexpected energy bin: {record.energy_bin_kwh_m2_year}")
    if record.dwelling_count < 0:
        raise ValueError("dwelling_count must be non-negative")


def bridge_y_ge2011(
    records: Iterable[EnergyDistributionRecord],
) -> tuple[BridgedEnergyBin, ...]:
    """Aggregate the two published KSH 2011+ periods into WBL Y_GE2011.

    This is a lossless count aggregation at fixed building-type and energy-bin grain.
    It does not create a building-type join to WBL and does not upgrade MODELLED
    source evidence to OBS.
    """

    indexed: dict[tuple[str, str, int], int] = {}
    for record in records:
        _validate_record(record)
        key = (
            record.building_type,
            record.construction_period,
            record.energy_bin_kwh_m2_year,
        )
        if key in indexed:
            raise ValueError(f"duplicate source row: {key}")
        indexed[key] = record.dwelling_count

    expected_keys = {
        (building_type, period, energy_bin)
        for building_type in SUPPORTED_BUILDING_TYPES
        for period in SOURCE_PERIODS
        for energy_bin in EXPECTED_ENERGY_BINS
    }
    actual_keys = set(indexed)
    missing = sorted(expected_keys - actual_keys)
    unexpected = sorted(actual_keys - expected_keys)
    if missing or unexpected:
        raise ValueError(
            f"incomplete canonical period panel: missing={missing[:3]} unexpected={unexpected[:3]}"
        )

    output: list[BridgedEnergyBin] = []
    for building_type in SUPPORTED_BUILDING_TYPES:
        for energy_bin in EXPECTED_ENERGY_BINS:
            count = sum(
                indexed[(building_type, period, energy_bin)]
                for period in SOURCE_PERIODS
            )
            output.append(
                BridgedEnergyBin(
                    building_type=building_type,
                    construction_period=TARGET_PERIOD,
                    energy_bin_kwh_m2_year=energy_bin,
                    dwelling_count=count,
                    evidence_status=OUTPUT_EVIDENCE_STATUS,
                    source_periods=SOURCE_PERIODS,
                    source_evidence_status=SOURCE_EVIDENCE_STATUS,
                )
            )
    return tuple(output)


def dwelling_totals_by_building_type(
    rows: Iterable[BridgedEnergyBin],
) -> dict[str, int]:
    totals = {building_type: 0 for building_type in SUPPORTED_BUILDING_TYPES}
    for row in rows:
        if row.building_type not in totals:
            raise ValueError(f"unsupported bridged building type: {row.building_type}")
        if row.construction_period != TARGET_PERIOD:
            raise ValueError(f"unexpected bridged period: {row.construction_period}")
        if row.evidence_status != OUTPUT_EVIDENCE_STATUS:
            raise ValueError(f"unexpected bridged evidence: {row.evidence_status}")
        if row.source_evidence_status != SOURCE_EVIDENCE_STATUS:
            raise ValueError(
                f"unexpected source lineage evidence: {row.source_evidence_status}"
            )
        totals[row.building_type] += row.dwelling_count
    return totals
