"""Fail-closed recovery of missing ENTSO-E A75 cells from MAVIR signed net measurements.

This module never overwrites a numeric A75 value. It only supplies an exact
source-native MAVIR net-operational value where the corresponding A75 cell is
missing, and preserves the sign through the B09 signed-net generation boundary.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from math import isfinite
from typing import Iterable

from modules.B08.observed_load_contract import CONTROL_AREA_SCHEME, HUNGARY_CONTROL_AREA
from modules.B09.engine import (
    SupplyRecord,
    supply_record_from_signed_net_generation,
)
from modules.B09.observed_generation_contract import ObservedGenerationRecord, PSR_TYPE_RE


class SignedNetRecoveryContractError(ValueError):
    """Fail-closed signed-net recovery contract violation."""


MAVIR_NET_OPERATIONAL_SOURCE_ID = "SRC-B09-MAVIR-FUEL-NET-OPERATIONAL-2026"
MAVIR_NET_OPERATIONAL_BASIS = "NET_OPERATIONAL"
ALLOWED_RECOVERY_TYPES = {"B04", "B06", "B12"}
MAVIR_OPERATIONAL_SHA256 = {
    "2c1bfd1f4fe9a0fc0b1262a86376037a5ae8c17bc2e6a412e4f996afaa46cb8f",
    "a47a8b7b923a5ed2418a6475c14dd0fd3ba7e3fd1ae0608e8b6756846e250563",
    "12571dc0993b48ad05b8a0d5c757360a8e81c22969c36d012bc2cad03e4f9547",
    "e768fe72e719a075eaac707b951af6be1854248dc4e7de1d530efdb1ecb946ad",
}


def _utc(value: datetime, name: str) -> datetime:
    if not isinstance(value, datetime) or value.tzinfo is None or value.utcoffset() is None:
        raise SignedNetRecoveryContractError(f"{name} must be timezone-aware")
    return value.astimezone(timezone.utc)


@dataclass(frozen=True)
class SignedNetRecoveryRecord:
    timestamp_utc: datetime
    timestep_hours: float
    production_type_code: str
    signed_power_mw: float
    source_sha256: str
    source_id: str = MAVIR_NET_OPERATIONAL_SOURCE_ID
    measurement_basis: str = MAVIR_NET_OPERATIONAL_BASIS
    region_id: str = HUNGARY_CONTROL_AREA
    region_scheme: str = CONTROL_AREA_SCHEME

    def __post_init__(self) -> None:
        object.__setattr__(self, "timestamp_utc", _utc(self.timestamp_utc, "timestamp_utc"))
        if not isinstance(self.timestep_hours, (int, float)) or isinstance(self.timestep_hours, bool) or not isfinite(self.timestep_hours) or self.timestep_hours <= 0:
            raise SignedNetRecoveryContractError("timestep_hours must be finite and positive")
        if self.timestep_hours != 0.25:
            raise SignedNetRecoveryContractError("MAVIR recovery must remain PT15M")
        if not isinstance(self.production_type_code, str) or not PSR_TYPE_RE.fullmatch(self.production_type_code):
            raise SignedNetRecoveryContractError("production_type_code must be an ENTSO-E Bxx code")
        if self.production_type_code not in ALLOWED_RECOVERY_TYPES:
            raise SignedNetRecoveryContractError("production type is outside the validated P6 recovery set")
        if not isinstance(self.signed_power_mw, (int, float)) or isinstance(self.signed_power_mw, bool) or not isfinite(self.signed_power_mw):
            raise SignedNetRecoveryContractError("signed_power_mw must be finite")
        if self.source_id != MAVIR_NET_OPERATIONAL_SOURCE_ID or self.measurement_basis != MAVIR_NET_OPERATIONAL_BASIS:
            raise SignedNetRecoveryContractError("recovery source must be MAVIR net operational")
        if self.source_sha256 not in MAVIR_OPERATIONAL_SHA256:
            raise SignedNetRecoveryContractError("recovery source hash is not an admitted P6 artifact")
        if self.region_id != HUNGARY_CONTROL_AREA or self.region_scheme != CONTROL_AREA_SCHEME:
            raise SignedNetRecoveryContractError("recovery grain must remain the Hungarian control area")


@dataclass(frozen=True)
class RecoveredGenerationPanel:
    records: tuple[SupplyRecord, ...]
    recovered_cell_count: int
    negative_recovery_count: int
    zero_recovery_count: int
    positive_recovery_count: int
    source_refs: tuple[str, ...]


def materialize_recovered_generation_panel(
    a75_records: Iterable[ObservedGenerationRecord],
    recovery_records: Iterable[SignedNetRecoveryRecord],
    *,
    expected_production_types: Iterable[str],
    request_start_utc: datetime,
    request_end_utc: datetime,
) -> RecoveredGenerationPanel:
    """Materialize a complete B09 supply panel without overwriting numeric A75 cells."""
    source_rows = tuple(a75_records)
    recoveries = tuple(recovery_records)
    if not source_rows:
        raise SignedNetRecoveryContractError("A75 source panel is required")
    expected_types = tuple(sorted(set(expected_production_types)))
    if not expected_types or any(not isinstance(code, str) or not PSR_TYPE_RE.fullmatch(code) for code in expected_types):
        raise SignedNetRecoveryContractError("expected_production_types must be explicit Bxx codes")

    start = _utc(request_start_utc, "request_start_utc")
    end = _utc(request_end_utc, "request_end_utc")
    if end <= start:
        raise SignedNetRecoveryContractError("request window end must be after start")

    timesteps = {row.timestep_hours for row in source_rows}
    if timesteps != {0.25}:
        raise SignedNetRecoveryContractError("A75 recovery panel must remain PT15M")

    timestamps: list[datetime] = []
    cursor = start
    while cursor < end:
        timestamps.append(cursor)
        cursor += timedelta(minutes=15)
    if cursor != end:
        raise SignedNetRecoveryContractError("request window must be divisible by PT15M")

    source_by_key: dict[tuple[str, datetime], ObservedGenerationRecord] = {}
    for row in source_rows:
        if not isinstance(row, ObservedGenerationRecord):
            raise SignedNetRecoveryContractError("A75 rows must be ObservedGenerationRecord")
        if row.region_id != HUNGARY_CONTROL_AREA or row.region_scheme != CONTROL_AREA_SCHEME:
            raise SignedNetRecoveryContractError("A75 grain must remain the Hungarian control area")
        key = (row.production_type_code, row.timestamp_utc)
        if key in source_by_key:
            raise SignedNetRecoveryContractError("duplicate A75 production-type/timestamp key")
        source_by_key[key] = row

    expected_keys = {(code, timestamp) for code in expected_types for timestamp in timestamps}
    if set(source_by_key) != expected_keys:
        raise SignedNetRecoveryContractError("A75 source panel must expose every expected cell, including missing cells")

    missing_keys = {key for key, row in source_by_key.items() if row.power_mw is None}
    if any(code not in ALLOWED_RECOVERY_TYPES for code, _timestamp in missing_keys):
        raise SignedNetRecoveryContractError("A75 missing cell lies outside the validated P6 recovery set")

    recovery_by_key: dict[tuple[str, datetime], SignedNetRecoveryRecord] = {}
    for row in recoveries:
        if not isinstance(row, SignedNetRecoveryRecord):
            raise SignedNetRecoveryContractError("recovery rows must be SignedNetRecoveryRecord")
        key = (row.production_type_code, row.timestamp_utc)
        if key in recovery_by_key:
            raise SignedNetRecoveryContractError("duplicate recovery production-type/timestamp key")
        recovery_by_key[key] = row

    if set(recovery_by_key) != missing_keys:
        extras = sorted(set(recovery_by_key) - missing_keys)
        missing = sorted(missing_keys - set(recovery_by_key))
        raise SignedNetRecoveryContractError(
            f"recovery keys must exactly equal A75 missing keys; extras={extras!r}, missing={missing!r}"
        )

    result: list[SupplyRecord] = []
    negative = zero = positive = 0
    for key in sorted(expected_keys, key=lambda item: (item[1], item[0])):
        source = source_by_key[key]
        component_id = f"ENTSOE_PSR_{source.production_type_code}"
        if source.power_mw is not None:
            result.append(SupplyRecord(
                timestamp=source.timestamp_utc,
                timestep_hours=source.timestep_hours,
                source_component_id=component_id,
                region_id=source.region_id,
                region_scheme=source.region_scheme,
                truth_context="REAL",
                evidence_status="DER" if source.evidence_status == "OBS" else "Q",
                source_refs=source.source_refs,
                delivered_generation_kw=float(source.power_mw) * 1000.0,
            ))
            continue

        recovery = recovery_by_key[key]
        signed_kw = float(recovery.signed_power_mw) * 1000.0
        if signed_kw < 0:
            negative += 1
        elif signed_kw > 0:
            positive += 1
        else:
            zero += 1
        refs = tuple(sorted(set(source.source_refs) | {recovery.source_id}))
        result.append(supply_record_from_signed_net_generation(
            timestamp=source.timestamp_utc,
            timestep_hours=source.timestep_hours,
            source_component_id=component_id,
            region_id=source.region_id,
            region_scheme=source.region_scheme,
            truth_context="REAL",
            evidence_status="Q",
            source_refs=refs,
            signed_net_generation_kw=signed_kw,
        ))

    return RecoveredGenerationPanel(
        records=tuple(result),
        recovered_cell_count=len(recovery_by_key),
        negative_recovery_count=negative,
        zero_recovery_count=zero,
        positive_recovery_count=positive,
        source_refs=tuple(sorted({ref for row in result for ref in row.source_refs})),
    )
