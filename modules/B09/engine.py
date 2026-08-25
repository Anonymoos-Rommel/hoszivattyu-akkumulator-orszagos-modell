"""Bounded physical supply versus B08 net-load adequacy ledger.

B09-P1 is deliberately not a dispatch, market, reserve, tariff, storage or
network model.  It compares an explicit B08 AC/grid-side load series with an
explicit delivered-generation panel and retains only physical residual and
surplus quantities.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from math import isfinite
from pathlib import Path
from typing import Any, Iterable, Mapping

from modules.B08.engine import GridLoadAggregate, run_fixture as run_b08_fixture


EVIDENCE_STATUSES = {"OBS", "DER", "ASS", "SCN", "POL", "Q"}
TRUTH_CONTEXTS = {"REAL", "SCN"}
ALLOWED_SCOPES = {"BOUNDED_REAL_AGGREGATE", "BOUNDED_SCN_FIXTURE"}
GENERATION_BOUNDARY = "GENERATION_AC"


class B09ContractError(ValueError):
    """Fail-closed B09 contract violation."""


def _nonnegative(value: float, name: str) -> float:
    if not isinstance(value, (int, float)) or isinstance(value, bool) or not isfinite(value) or value < 0:
        raise B09ContractError(f"{name} must be finite and non-negative")
    return float(value)


def _derived_status(truth_context: str, statuses: Iterable[str]) -> str:
    values = tuple(statuses)
    if not values:
        raise B09ContractError("evidence status is required")
    if any(value not in EVIDENCE_STATUSES for value in values):
        raise B09ContractError("invalid evidence status")
    if any(value in {"ASS", "POL"} for value in values):
        raise B09ContractError("ASS/POL evidence cannot enter a physical adequacy result")
    if truth_context == "SCN":
        if any(value not in {"SCN", "Q"} for value in values):
            raise B09ContractError("SCN adequacy requires SCN or Q evidence")
        return "SCN" if all(value == "SCN" for value in values) else "Q"
    if any(value not in {"OBS", "DER", "Q"} for value in values):
        raise B09ContractError("REAL adequacy requires OBS, DER or Q evidence")
    return "Q" if any(value == "Q" for value in values) else "DER"


def _validate_b08_evidence(row: GridLoadAggregate) -> None:
    statuses = tuple(row.evidence_statuses) or (row.evidence_status,)
    _derived_status(row.truth_context, (row.evidence_status, *statuses))


def _utc(value: datetime) -> datetime:
    if not isinstance(value, datetime) or value.tzinfo is None or value.utcoffset() is None:
        raise B09ContractError("timestamp must be timezone-aware")
    return value.astimezone(timezone.utc)


@dataclass(frozen=True)
class SupplyRecord:
    timestamp: datetime
    timestep_hours: float
    source_component_id: str
    region_id: str
    region_scheme: str
    truth_context: str
    evidence_status: str
    source_refs: tuple[str, ...]
    delivered_generation_kw: float
    boundary_id: str = GENERATION_BOUNDARY

    def __post_init__(self) -> None:
        object.__setattr__(self, "timestamp", _utc(self.timestamp))
        if not isinstance(self.timestep_hours, (int, float)) or not isfinite(self.timestep_hours) or self.timestep_hours <= 0:
            raise B09ContractError("timestep_hours must be finite and positive")
        for name, value in (("source_component_id", self.source_component_id), ("region_id", self.region_id), ("region_scheme", self.region_scheme), ("boundary_id", self.boundary_id)):
            if not isinstance(value, str) or not value.strip():
                raise B09ContractError(f"{name} is required")
        if self.boundary_id != GENERATION_BOUNDARY:
            raise B09ContractError("unsupported B09 generation boundary")
        if self.truth_context not in TRUTH_CONTEXTS:
            raise B09ContractError("truth_context must be REAL or SCN")
        allowed = {"SCN", "Q"} if self.truth_context == "SCN" else {"OBS", "DER", "Q"}
        if self.evidence_status not in allowed:
            raise B09ContractError("evidence status is incompatible with truth context")
        if isinstance(self.source_refs, str) or not isinstance(self.source_refs, (tuple, list)) or not self.source_refs or any(not isinstance(ref, str) or not ref.strip() for ref in self.source_refs):
            raise B09ContractError("source_refs must be a non-empty collection of strings")
        _nonnegative(self.delivered_generation_kw, "delivered_generation_kw")


@dataclass(frozen=True)
class AdequacyRecord:
    timestamp: datetime
    timestep_hours: float
    region_id: str
    region_scheme: str
    scope: str
    b08_net_grid_load_kw: float
    delivered_generation_kw: float
    residual_demand_kw: float
    unserved_or_residual_load_kw: float
    surplus_supply_kw: float
    net_load_kwh: float
    generation_kwh: float
    residual_demand_kwh: float
    unserved_or_residual_load_kwh: float
    surplus_supply_kwh: float
    truth_context: str
    evidence_status: str
    input_evidence_statuses: tuple[str, ...]
    source_refs: tuple[str, ...]


@dataclass(frozen=True)
class AdequacyResult:
    status: str
    truth_context: str
    scope: str
    region_scheme: str
    rows: tuple[AdequacyRecord, ...]
    scope_total_rows: tuple[AdequacyRecord, ...]
    peak_residual_demand_kw: float
    peak_residual_timestamps: tuple[datetime, ...]
    peak_surplus_supply_kw: float
    peak_surplus_timestamps: tuple[datetime, ...]
    source_refs: tuple[str, ...]
    explanations: tuple[Mapping[str, Any], ...]


def _coalesce_b08(rows: Iterable[GridLoadAggregate]) -> tuple[GridLoadAggregate, ...]:
    values = tuple(rows)
    if not values:
        raise B09ContractError("B09 requires explicit B08 rows")
    groups: dict[tuple[datetime, str, str], list[GridLoadAggregate]] = {}
    for row in values:
        if not isinstance(row, GridLoadAggregate):
            raise B09ContractError("B09 input must be canonical B08 GridLoadAggregate rows")
        _validate_b08_evidence(row)
        if row.region_id == "BOUNDED_SCOPE_TOTAL":
            key = (row.timestamp, row.region_id, row.region_scheme)
        else:
            key = (row.timestamp, row.region_id, row.region_scheme)
        groups.setdefault(key, []).append(row)
    result: list[GridLoadAggregate] = []
    for key, group in sorted(groups.items()):
        if len({row.timestep_hours for row in group}) != 1:
            raise B09ContractError(f"inconsistent B08 timestep at {key[0].isoformat()}")
        if len({row.truth_context for row in group}) != 1:
            raise B09ContractError("mixed B08 truth contexts are rejected")
        first = group[0]
        statuses = tuple(sorted({status for row in group for status in row.evidence_statuses}))
        refs = tuple(sorted({ref for row in group for ref in row.source_refs}))
        load = sum(row.net_grid_load_kw for row in group)
        imports = sum(row.gross_grid_import_kw for row in group)
        exports = sum(row.gross_grid_export_kw for row in group)
        up = sum(row.physical_up_flex_kw for row in group)
        down = sum(row.physical_down_flex_kw for row in group)
        result.append(GridLoadAggregate(
            timestamp=first.timestamp, timestep_hours=first.timestep_hours,
            region_id=first.region_id, region_scheme=first.region_scheme,
            b01_state_id="ALL_STATES", source_entity_count=sum(row.source_entity_count for row in group),
            gross_grid_import_kw=imports, gross_grid_export_kw=exports,
            net_grid_load_kw=load, physical_up_flex_kw=up, physical_down_flex_kw=down,
            battery_charge_kw=None, battery_discharge_kw=None, soc_fractions=(), diagnostic_complete=False,
            import_kwh=imports * first.timestep_hours,
            export_kwh=exports * first.timestep_hours, net_kwh=load * first.timestep_hours,
            truth_context=first.truth_context, evidence_status=first.evidence_status,
            evidence_statuses=statuses, source_refs=refs,
        ))
    return tuple(result)


def aggregate_adequacy(b08_rows: Iterable[GridLoadAggregate], supply_records: Iterable[SupplyRecord], *, scope: str) -> AdequacyResult:
    if scope not in ALLOWED_SCOPES:
        raise B09ContractError(f"unsupported B09 scope: {scope!r}")
    load_rows = _coalesce_b08(b08_rows)
    supplies = tuple(supply_records)
    if not supplies:
        raise B09ContractError("B09 requires explicit generation records")
    truths = {row.truth_context for row in load_rows} | {row.truth_context for row in supplies}
    if len(truths) != 1:
        raise B09ContractError("mixed B08/generation truth contexts are rejected")
    truth = next(iter(truths))
    expected_truth = "REAL" if scope == "BOUNDED_REAL_AGGREGATE" else "SCN"
    if truth != expected_truth:
        raise B09ContractError(f"scope {scope!r} is incompatible with truth_context {truth!r}")
    schemes = {row.region_scheme for row in load_rows} | {row.region_scheme for row in supplies}
    if len(schemes) != 1:
        raise B09ContractError("mixed region schemes are rejected")
    load_by_key: dict[tuple[datetime, str, str], GridLoadAggregate] = {}
    for row in load_rows:
        key = (row.timestamp, row.region_id, row.region_scheme)
        if key in load_by_key:
            raise B09ContractError("duplicate canonical B08 load key")
        load_by_key[key] = row
    seen: set[tuple[str, str, str, datetime]] = set()
    for row in supplies:
        key = (row.source_component_id, row.region_id, row.region_scheme, row.timestamp)
        if key in seen:
            raise B09ContractError(f"duplicate canonical generation key: {key!r}")
        seen.add(key)
        load = load_by_key.get((row.timestamp, row.region_id, row.region_scheme))
        if load is None:
            raise B09ContractError("generation row has no matching B08 load row")
        if row.timestep_hours != load.timestep_hours:
            raise B09ContractError("generation timestep does not match B08 timestep")
    timestamps = {row.timestamp for row in supplies}
    components = {(row.source_component_id, row.region_id, row.region_scheme) for row in supplies}
    expected_panel = {(component, region, scheme, timestamp) for component, region, scheme in components for timestamp in timestamps}
    if seen != expected_panel:
        raise B09ContractError(f"incomplete generation panel: {sorted(expected_panel - seen)!r}")
    rows: list[AdequacyRecord] = []
    supplies_by_key: dict[tuple[datetime, str, str], list[SupplyRecord]] = {}
    for row in supplies:
        supplies_by_key.setdefault((row.timestamp, row.region_id, row.region_scheme), []).append(row)
    for key, load in sorted(load_by_key.items()):
        component_rows = supplies_by_key.get(key)
        if not component_rows:
            raise B09ContractError(f"missing generation at B08 load key: {key!r}")
        generation = sum(row.delivered_generation_kw for row in component_rows)
        residual = load.net_grid_load_kw - generation
        status = _derived_status(truth, [load.evidence_status, *(row.evidence_status for row in component_rows)])
        refs = tuple(sorted(set(load.source_refs) | {ref for row in component_rows for ref in row.source_refs}))
        dt = load.timestep_hours
        rows.append(AdequacyRecord(
            timestamp=load.timestamp, timestep_hours=dt, region_id=load.region_id,
            region_scheme=load.region_scheme, scope=scope,
            b08_net_grid_load_kw=load.net_grid_load_kw, delivered_generation_kw=generation,
            residual_demand_kw=residual, unserved_or_residual_load_kw=max(residual, 0.0),
            surplus_supply_kw=max(-residual, 0.0), net_load_kwh=load.net_grid_load_kw * dt,
            generation_kwh=generation * dt, residual_demand_kwh=residual * dt,
            unserved_or_residual_load_kwh=max(residual, 0.0) * dt,
            surplus_supply_kwh=max(-residual, 0.0) * dt,
            truth_context=truth, evidence_status=status,
            input_evidence_statuses=tuple(sorted({load.evidence_status, *(row.evidence_status for row in component_rows)})),
            source_refs=refs,
        ))
    scope_rows: list[AdequacyRecord] = []
    for timestamp in sorted({row.timestamp for row in rows}):
        group = [row for row in rows if row.timestamp == timestamp]
        first = group[0]
        residual = sum(row.residual_demand_kw for row in group)
        generation = sum(row.delivered_generation_kw for row in group)
        load = sum(row.b08_net_grid_load_kw for row in group)
        dt = first.timestep_hours
        scope_rows.append(AdequacyRecord(
            timestamp=timestamp, timestep_hours=dt, region_id="BOUNDED_SCOPE_TOTAL",
            region_scheme=first.region_scheme, scope=scope, b08_net_grid_load_kw=load,
            delivered_generation_kw=generation, residual_demand_kw=residual,
            unserved_or_residual_load_kw=max(residual, 0.0), surplus_supply_kw=max(-residual, 0.0),
            net_load_kwh=load * dt, generation_kwh=generation * dt, residual_demand_kwh=residual * dt,
            unserved_or_residual_load_kwh=max(residual, 0.0) * dt,
            surplus_supply_kwh=max(-residual, 0.0) * dt, truth_context=truth,
            evidence_status=_derived_status(truth, (row.evidence_status for row in group)),
            input_evidence_statuses=tuple(sorted({status for row in group for status in row.input_evidence_statuses})),
            source_refs=tuple(sorted({ref for row in group for ref in row.source_refs})),
        ))
    def peak(field: str) -> tuple[float, tuple[datetime, ...]]:
        value = max(getattr(row, field) for row in scope_rows)
        return value, tuple(row.timestamp for row in scope_rows if getattr(row, field) == value)
    peak_residual, peak_residual_ts = peak("unserved_or_residual_load_kw")
    peak_surplus, peak_surplus_ts = peak("surplus_supply_kw")
    refs = tuple(sorted({ref for row in rows for ref in row.source_refs}))
    return AdequacyResult(
        status=_derived_status(truth, (row.evidence_status for row in rows)), truth_context=truth,
        scope=scope, region_scheme=next(iter(schemes)), rows=tuple(rows),
        scope_total_rows=tuple(scope_rows), peak_residual_demand_kw=peak_residual,
        peak_residual_timestamps=peak_residual_ts, peak_surplus_supply_kw=peak_surplus,
        peak_surplus_timestamps=peak_surplus_ts, source_refs=refs,
        explanations=({"scope": scope, "truth_context": truth, "region_scheme": next(iter(schemes)),
                       "bounded_scope_total_label": "BOUNDED_SCOPE_TOTAL",
                       "notes": "Physical residual/surplus only; no dispatch, curtailment, reserve, headroom, market, tariff, storage or national claim."},),
    )


def _supply_from_mapping(raw: Mapping[str, Any]) -> SupplyRecord:
    if not isinstance(raw, Mapping):
        raise B09ContractError("generation row must be an object")
    allowed = {"timestamp", "timestep_hours", "source_component_id", "region_id", "region_scheme", "truth_context", "evidence_status", "source_refs", "delivered_generation_kw", "boundary_id"}
    unknown = sorted(set(raw) - allowed)
    if unknown:
        raise B09ContractError(f"unsupported generation fields: {unknown!r}")
    required = allowed
    missing = sorted(field for field in required if field not in raw)
    if missing:
        raise B09ContractError(f"missing generation fields: {missing!r}")
    if not isinstance(raw["timestamp"], str):
        raise B09ContractError("generation timestamp must be a string")
    if not isinstance(raw["source_refs"], list) or not raw["source_refs"]:
        raise B09ContractError("generation source_refs must be an explicit list")
    try:
        timestamp = datetime.fromisoformat(raw["timestamp"].replace("Z", "+00:00"))
    except ValueError as exc:
        raise B09ContractError("invalid generation timestamp") from exc
    return SupplyRecord(timestamp=timestamp, timestep_hours=raw["timestep_hours"], source_component_id=raw["source_component_id"], region_id=raw["region_id"], region_scheme=raw["region_scheme"], truth_context=raw["truth_context"], evidence_status=raw["evidence_status"], source_refs=tuple(raw["source_refs"]), delivered_generation_kw=raw["delivered_generation_kw"], boundary_id=raw["boundary_id"])


def run_fixture(path: str | Path) -> AdequacyResult:
    try:
        fixture = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise B09ContractError(f"invalid B09 fixture: {exc}") from exc
    if fixture.get("status") != "SCN" or fixture.get("truth_context") != "SCN":
        raise B09ContractError("B09 fixture must remain SCN truth")
    if fixture.get("dataset_license") != "CC BY-SA 4.0":
        raise B09ContractError("B09 fixture requires a dataset-level license")
    if fixture.get("scope") != "BOUNDED_SCN_FIXTURE" or not isinstance(fixture.get("region_scheme"), str):
        raise B09ContractError("B09 fixture requires bounded scope and region scheme")
    b08_path = Path(path).resolve().parent / "b08_grid_load_scn.json"
    b08_result = run_b08_fixture(b08_path)
    if b08_result.truth_context != "SCN" or b08_result.scope != "BOUNDED_SCN_FIXTURE":
        raise B09ContractError("B08 fixture handoff is not bounded SCN")
    records = fixture.get("supply_records")
    if not isinstance(records, list) or not records:
        raise B09ContractError("B09 fixture requires explicit supply_records")
    supplies = []
    for raw in records:
        if raw.get("truth_context") != "SCN" or raw.get("evidence_status") != "SCN":
            raise B09ContractError("B09 fixture supply rows must remain SCN")
        if raw.get("region_scheme") != fixture["region_scheme"]:
            raise B09ContractError("B09 fixture supply region scheme mismatch")
        supplies.append(_supply_from_mapping(raw))
    return aggregate_adequacy(b08_result.rows, supplies, scope="BOUNDED_SCN_FIXTURE")
