"""Evidence-aware, bounded AC/grid-side system-load aggregation.

The module aggregates explicit household boundary records. It does not
dispatch assets, infer missing values, scale a fixture to a population, or
make tariff, legal-export, seasonal, headroom, or reinforcement decisions.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from math import isfinite
from pathlib import Path
from typing import Any, Iterable, Mapping

from modules.B01.engine import STATE_ORDER
from modules.B07.engine import B08PhysicalHandoff

EVIDENCE_STATUSES = {"OBS", "DER", "ASS", "SCN", "POL", "Q"}
TRUTH_CONTEXTS = {"REAL", "SCN"}


class B08ContractError(ValueError):
    """Fail-closed B08 contract violation."""


def _finite_nonnegative(value: float, name: str) -> float:
    if not isinstance(value, (int, float)) or isinstance(value, bool) or not isfinite(value) or value < 0:
        raise B08ContractError(f"{name} must be finite and non-negative")
    return float(value)


def _status(statuses: Iterable[str]) -> str:
    values = tuple(statuses)
    if not values or any(value not in EVIDENCE_STATUSES for value in values):
        raise B08ContractError("invalid evidence status")
    if all(value == "SCN" for value in values):
        return "SCN"
    if all(value == values[0] for value in values):
        return values[0]
    return "Q"


@dataclass(frozen=True)
class GridBoundaryRecord:
    timestamp: datetime
    timestep_hours: float
    source_entity_id: str
    region_id: str
    region_scheme: str
    b01_state_id: str
    truth_context: str
    evidence_status: str
    source_refs: tuple[str, ...]
    net_grid_import_kw: float
    net_grid_export_kw: float
    physical_up_flex_kw: float
    physical_down_flex_kw: float
    boundary_id: str = "AC_GRID"

    def __post_init__(self) -> None:
        if not isinstance(self.timestamp, datetime):
            raise B08ContractError("timestamp must be datetime")
        if not isinstance(self.timestep_hours, (int, float)) or not isfinite(self.timestep_hours) or self.timestep_hours <= 0:
            raise B08ContractError("timestep_hours must be finite and positive")
        for name, value in (("source_entity_id", self.source_entity_id), ("region_id", self.region_id), ("region_scheme", self.region_scheme), ("boundary_id", self.boundary_id)):
            if not isinstance(value, str) or not value.strip():
                raise B08ContractError(f"{name} is required")
        if self.b01_state_id not in STATE_ORDER:
            raise B08ContractError(f"unknown B01 state: {self.b01_state_id!r}")
        if self.truth_context not in TRUTH_CONTEXTS:
            raise B08ContractError("truth_context must be REAL or SCN")
        if self.evidence_status not in EVIDENCE_STATUSES:
            raise B08ContractError("invalid evidence_status")
        if not self.source_refs or any(not isinstance(ref, str) or not ref.strip() for ref in self.source_refs):
            raise B08ContractError("source_refs are required")
        for name in ("net_grid_import_kw", "net_grid_export_kw", "physical_up_flex_kw", "physical_down_flex_kw"):
            _finite_nonnegative(getattr(self, name), name)
        if self.truth_context == "SCN" and self.evidence_status not in {"SCN", "Q"}:
            raise B08ContractError("SCN truth cannot carry real evidence status")

    @classmethod
    def from_b07_handoff(cls, *, timestamp: datetime, timestep_hours: float, source_entity_id: str,
                         region_id: str, region_scheme: str, b01_state_id: str,
                         handoff: B08PhysicalHandoff, truth_context: str,
                         evidence_status: str, source_refs: tuple[str, ...]) -> "GridBoundaryRecord":
        """Lossless B07 handoff; B05 electricity is already in the B07 balance."""
        return cls(timestamp, timestep_hours, source_entity_id, region_id, region_scheme,
                   b01_state_id, truth_context, evidence_status, tuple(source_refs),
                   handoff.net_grid_import_kw, handoff.net_grid_export_kw,
                   handoff.physical_up_flex_kw, handoff.physical_down_flex_kw)


@dataclass(frozen=True)
class GridLoadAggregate:
    timestamp: datetime
    timestep_hours: float
    region_id: str
    region_scheme: str
    b01_state_id: str
    source_entity_count: int
    gross_grid_import_kw: float
    gross_grid_export_kw: float
    net_grid_load_kw: float
    physical_up_flex_kw: float
    physical_down_flex_kw: float
    import_kwh: float
    export_kwh: float
    net_kwh: float
    truth_context: str
    evidence_status: str
    evidence_statuses: tuple[str, ...]
    source_refs: tuple[str, ...]


@dataclass(frozen=True)
class GridLoadResult:
    status: str
    truth_context: str
    scope: str
    region_scheme: str
    rows: tuple[GridLoadAggregate, ...]
    national_rows: tuple[GridLoadAggregate, ...]
    peak_gross_import_kw: float
    peak_gross_import_timestamps: tuple[datetime, ...]
    peak_gross_export_kw: float
    peak_gross_export_timestamps: tuple[datetime, ...]
    peak_net_grid_load_kw: float
    peak_net_grid_load_timestamps: tuple[datetime, ...]
    source_refs: tuple[str, ...]
    explanations: tuple[Mapping[str, Any], ...]


def _aggregate_group(records: tuple[GridBoundaryRecord, ...], *, region_id: str, state_id: str) -> GridLoadAggregate:
    dt = records[0].timestep_hours
    imports = sum(row.net_grid_import_kw for row in records)
    exports = sum(row.net_grid_export_kw for row in records)
    up = sum(row.physical_up_flex_kw for row in records)
    down = sum(row.physical_down_flex_kw for row in records)
    statuses = tuple(sorted({row.evidence_status for row in records}))
    refs = tuple(sorted({ref for row in records for ref in row.source_refs}))
    net = imports - exports
    return GridLoadAggregate(
        timestamp=records[0].timestamp, timestep_hours=dt, region_id=region_id,
        region_scheme=records[0].region_scheme, b01_state_id=state_id,
        source_entity_count=len(records), gross_grid_import_kw=imports,
        gross_grid_export_kw=exports, net_grid_load_kw=net,
        physical_up_flex_kw=up, physical_down_flex_kw=down,
        import_kwh=imports * dt, export_kwh=exports * dt, net_kwh=net * dt,
        truth_context=records[0].truth_context, evidence_status=_status(row.evidence_status for row in records),
        evidence_statuses=statuses, source_refs=refs,
    )


def aggregate_grid_load(records: Iterable[GridBoundaryRecord], *, scope: str = "BOUNDED_REAL_AGGREGATE") -> GridLoadResult:
    values = tuple(records)
    if not values:
        raise B08ContractError("at least one explicit grid boundary record is required")
    for row in values:
        if not isinstance(row, GridBoundaryRecord):
            raise B08ContractError("all records must be GridBoundaryRecord")
    schemes = {row.region_scheme for row in values}
    truths = {row.truth_context for row in values}
    if len(schemes) != 1:
        raise B08ContractError("mixed region schemes are rejected")
    if len(truths) != 1:
        raise B08ContractError("mixed REAL and SCN truth contexts are rejected")
    seen: set[tuple[datetime, str, str]] = set()
    for row in values:
        key = (row.timestamp, row.source_entity_id, row.boundary_id)
        if key in seen:
            raise B08ContractError(f"duplicate canonical grid boundary key: {key!r}")
        seen.add(key)
    by_timestamp: dict[datetime, list[GridBoundaryRecord]] = {}
    for row in values:
        by_timestamp.setdefault(row.timestamp, []).append(row)
    for timestamp, rows_at_time in by_timestamp.items():
        if len({row.timestep_hours for row in rows_at_time}) != 1:
            raise B08ContractError(f"inconsistent timestep at {timestamp.isoformat()}")
    regional: list[GridLoadAggregate] = []
    for timestamp in sorted(by_timestamp):
        grouped: dict[tuple[str, str], list[GridBoundaryRecord]] = {}
        for row in by_timestamp[timestamp]:
            grouped.setdefault((row.region_id, row.b01_state_id), []).append(row)
        for (region_id, state_id), group in sorted(grouped.items()):
            regional.append(_aggregate_group(tuple(group), region_id=region_id, state_id=state_id))
    national = tuple(_aggregate_group(tuple(by_timestamp[timestamp]), region_id="NATIONAL_FIXTURE_TOTAL", state_id="ALL_STATES") for timestamp in sorted(by_timestamp))

    def peak(field: str) -> tuple[float, tuple[datetime, ...]]:
        maximum = max(getattr(row, field) for row in national)
        return maximum, tuple(row.timestamp for row in national if getattr(row, field) == maximum)

    peak_import, peak_import_ts = peak("gross_grid_import_kw")
    peak_export, peak_export_ts = peak("gross_grid_export_kw")
    peak_net, peak_net_ts = peak("net_grid_load_kw")
    refs = tuple(sorted({ref for row in values for ref in row.source_refs}))
    status = _status(row.evidence_status for row in values)
    truth = next(iter(truths))
    scheme = next(iter(schemes))
    explanation = {
        "scope": scope, "region_scheme": scheme, "truth_context": truth,
        "evidence_status": status, "source_refs": refs,
        "regional_row_count": len(regional), "timestamp_count": len(national),
        "national_label_is_fixture_total": True,
        "notes": "Explicit bounded aggregation only; no population scaling, dispatch, legal export, seasonal, headroom, or reinforcement claim.",
    }
    return GridLoadResult(status, truth, scope, scheme, tuple(regional), national,
                          peak_import, peak_import_ts, peak_export, peak_export_ts,
                          peak_net, peak_net_ts, refs, (explanation,))


def _record_from_mapping(raw: Mapping[str, Any]) -> GridBoundaryRecord:
    required = {"timestamp", "timestep_hours", "source_entity_id", "region_id", "region_scheme", "b01_state_id", "truth_context", "evidence_status", "source_refs", "net_grid_import_kw", "net_grid_export_kw", "physical_up_flex_kw", "physical_down_flex_kw"}
    missing = sorted(required - set(raw))
    if missing:
        raise B08ContractError(f"missing grid boundary fields: {missing!r}")
    try:
        timestamp = datetime.fromisoformat(str(raw["timestamp"]))
    except (TypeError, ValueError) as exc:
        raise B08ContractError("timestamp must be ISO datetime") from exc
    return GridBoundaryRecord(timestamp=timestamp, timestep_hours=raw["timestep_hours"], source_entity_id=str(raw["source_entity_id"]), region_id=str(raw["region_id"]), region_scheme=str(raw["region_scheme"]), b01_state_id=str(raw["b01_state_id"]), truth_context=str(raw["truth_context"]), evidence_status=str(raw["evidence_status"]), source_refs=tuple(raw["source_refs"]), net_grid_import_kw=raw["net_grid_import_kw"], net_grid_export_kw=raw["net_grid_export_kw"], physical_up_flex_kw=raw["physical_up_flex_kw"], physical_down_flex_kw=raw["physical_down_flex_kw"])


def run_fixture(path: str | Path) -> GridLoadResult:
    try:
        fixture = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise B08ContractError(f"invalid B08 fixture: {exc}") from exc
    if fixture.get("status") != "SCN" or fixture.get("truth_context") != "SCN":
        raise B08ContractError("B08 fixture must remain SCN truth")
    if fixture.get("dataset_license") != "CC BY-SA 4.0":
        raise B08ContractError("B08 fixture requires a dataset-level license")
    if fixture.get("scope") != "BOUNDED_SCN_FIXTURE":
        raise B08ContractError("B08 fixture scope must be BOUNDED_SCN_FIXTURE")
    records = fixture.get("records")
    if not isinstance(records, list) or not records:
        raise B08ContractError("B08 fixture requires explicit records")
    return aggregate_grid_load((_record_from_mapping(row) for row in records), scope="BOUNDED_SCN_FIXTURE")
