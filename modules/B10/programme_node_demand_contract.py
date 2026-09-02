"""Fail-closed B10-P9 programme-demand to exact DSO-node aggregation gate.

The contract consumes explicit, timestamped programme-positive grid-import
components only after B10-P8 has proven the exact DSO_SUBSTATION mapping for the
same entity.  It does not infer topology, invent diversity factors, net battery
flexibility against load, scale a bounded panel, or turn a headroom screening
result into hosting-capacity / reinforcement authority.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from math import isfinite
from typing import Iterable

from .dso_headroom_contract import (
    DsoHeadroomRecord,
    HeadroomAssessment,
    assess_incremental_demand,
)
from .spatial_authority_contract import (
    DSO_SUBSTATION,
    EXACT_NODE_PROVEN,
    SpatialAuthorityDecision,
    require_exact_dso_substation_mapping,
)


class B10ProgrammeNodeDemandError(ValueError):
    """Raised when programme demand cannot enter exact-node aggregation safely."""


REAL = "REAL"
SCN = "SCN"
TRUTH_CONTEXTS = {REAL, SCN}
EVIDENCE_STATUSES = {"OBS", "DER", "SCN", "Q"}
BOUNDED_EXPLICIT_PANEL = "BOUNDED_EXPLICIT_PANEL"
UNMANAGED_POSITIVE_PROGRAMME_IMPORT = "UNMANAGED_POSITIVE_PROGRAMME_IMPORT"
NO_DIVERSITY_OR_FLEX_AUTHORITY = "NO_DIVERSITY_OR_FLEX_AUTHORITY"
Q_NODE_DEMAND_UNRESOLVED = "Q_NODE_DEMAND_UNRESOLVED"
NODE_DEMAND_PROVEN = "NODE_DEMAND_PROVEN"


def _nonnegative(value: float, name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not isfinite(value) or value < 0:
        raise B10ProgrammeNodeDemandError(f"{name} must be finite and non-negative")
    return float(value)


def _status(statuses: Iterable[str], truth_context: str) -> str:
    values = tuple(statuses)
    if not values:
        raise B10ProgrammeNodeDemandError("at least one evidence status is required")
    if any(value not in EVIDENCE_STATUSES for value in values):
        raise B10ProgrammeNodeDemandError("invalid evidence status")
    if "Q" in values:
        return "Q"
    if truth_context == SCN:
        return "SCN"
    return "OBS" if all(value == "OBS" for value in values) else "DER"


@dataclass(frozen=True)
class ProgrammeDemandSnapshot:
    """One complete positive programme-import decomposition for one entity/timestep.

    Explicit zero is required for an absent component; omission is not interpreted
    as zero. Battery discharge / VPP flexibility is deliberately absent because it
    belongs to the later managed-peak gate.
    """

    timestamp: datetime
    timestep_hours: float
    scope_id: str
    source_entity_id: str
    truth_context: str
    evidence_status: str
    source_refs: tuple[str, ...]
    spatial_authority: SpatialAuthorityDecision
    heat_pump_import_kw: float
    battery_charge_import_kw: float
    other_programme_import_excluding_hp_and_battery_kw: float

    def __post_init__(self) -> None:
        if not isinstance(self.timestamp, datetime) or self.timestamp.tzinfo is None or self.timestamp.utcoffset() is None:
            raise B10ProgrammeNodeDemandError("timestamp must be timezone-aware")
        object.__setattr__(self, "timestamp", self.timestamp.astimezone(timezone.utc))
        if isinstance(self.timestep_hours, bool) or not isinstance(self.timestep_hours, (int, float)) or not isfinite(self.timestep_hours) or self.timestep_hours <= 0:
            raise B10ProgrammeNodeDemandError("timestep_hours must be finite and positive")
        object.__setattr__(self, "timestep_hours", float(self.timestep_hours))
        for name in ("scope_id", "source_entity_id"):
            value = getattr(self, name)
            if not isinstance(value, str) or not value.strip():
                raise B10ProgrammeNodeDemandError(f"{name} is required")
        if self.truth_context not in TRUTH_CONTEXTS:
            raise B10ProgrammeNodeDemandError("truth_context must be REAL or SCN")
        if self.evidence_status not in EVIDENCE_STATUSES:
            raise B10ProgrammeNodeDemandError("invalid evidence_status")
        allowed = {"OBS", "DER", "Q"} if self.truth_context == REAL else {"SCN", "Q"}
        if self.evidence_status not in allowed:
            raise B10ProgrammeNodeDemandError("evidence_status is incompatible with truth_context")
        if isinstance(self.source_refs, str) or not self.source_refs or any(not isinstance(ref, str) or not ref.strip() for ref in self.source_refs):
            raise B10ProgrammeNodeDemandError("source_refs must be a non-empty explicit collection")
        if not isinstance(self.spatial_authority, SpatialAuthorityDecision):
            raise B10ProgrammeNodeDemandError("spatial_authority must be a B10-P8 decision")
        if self.spatial_authority.entity_id != self.source_entity_id:
            raise B10ProgrammeNodeDemandError("P8 spatial authority must bind the same source entity")
        for field_name in (
            "heat_pump_import_kw",
            "battery_charge_import_kw",
            "other_programme_import_excluding_hp_and_battery_kw",
        ):
            object.__setattr__(self, field_name, _nonnegative(getattr(self, field_name), field_name))

    @property
    def positive_programme_import_kw(self) -> float:
        return (
            self.heat_pump_import_kw
            + self.battery_charge_import_kw
            + self.other_programme_import_excluding_hp_and_battery_kw
        )


@dataclass(frozen=True)
class ProgrammeNodeDemandAggregate:
    timestamp: datetime
    timestep_hours: float
    scope_id: str
    node_region_id: str
    node_region_scheme: str
    source_entity_count: int
    heat_pump_import_kw: float
    battery_charge_import_kw: float
    other_programme_import_kw: float
    positive_programme_import_kw: float
    incremental_demand_mw: float
    truth_context: str
    evidence_status: str
    source_refs: tuple[str, ...]
    demand_semantics: str = UNMANAGED_POSITIVE_PROGRAMME_IMPORT
    management_authority: str = NO_DIVERSITY_OR_FLEX_AUTHORITY


@dataclass(frozen=True)
class ProgrammeNodePeak:
    scope_id: str
    node_region_id: str
    node_region_scheme: str
    peak_positive_programme_import_mw: float
    peak_timestamps: tuple[datetime, ...]
    truth_context: str
    evidence_status: str
    source_refs: tuple[str, ...]
    demand_semantics: str = UNMANAGED_POSITIVE_PROGRAMME_IMPORT
    management_authority: str = NO_DIVERSITY_OR_FLEX_AUTHORITY


@dataclass(frozen=True)
class ProgrammeNodeDemandResult:
    status: str
    scope: str
    scope_id: str
    truth_context: str
    rows: tuple[ProgrammeNodeDemandAggregate, ...]
    peaks: tuple[ProgrammeNodePeak, ...]
    unresolved_entity_ids: tuple[str, ...]
    source_refs: tuple[str, ...]
    reason: str


def aggregate_programme_node_demand(
    snapshots: Iterable[ProgrammeDemandSnapshot],
) -> ProgrammeNodeDemandResult:
    """Aggregate only a complete explicit entity/timestamp panel at exact P8 nodes.

    Any unresolved P8 mapping, Q demand evidence, duplicate row, incomplete panel,
    mixed scope/truth context, or entity whose node changes inside the panel returns
    a Q result with no numeric node rows. This prevents unresolved households from
    silently disappearing from a node total.
    """

    values = tuple(snapshots)
    if not values:
        raise B10ProgrammeNodeDemandError("at least one programme demand snapshot is required")
    if any(not isinstance(row, ProgrammeDemandSnapshot) for row in values):
        raise B10ProgrammeNodeDemandError("all rows must be ProgrammeDemandSnapshot")

    scopes = {row.scope_id for row in values}
    truths = {row.truth_context for row in values}
    if len(scopes) != 1:
        raise B10ProgrammeNodeDemandError("mixed programme scope_ids are rejected")
    if len(truths) != 1:
        raise B10ProgrammeNodeDemandError("mixed REAL and SCN truth contexts are rejected")
    scope_id = next(iter(scopes))
    truth = next(iter(truths))

    seen: set[tuple[str, datetime]] = set()
    for row in values:
        key = (row.source_entity_id, row.timestamp)
        if key in seen:
            raise B10ProgrammeNodeDemandError(f"duplicate entity/timestamp row: {key!r}")
        seen.add(key)

    entities = {row.source_entity_id for row in values}
    timestamps = {row.timestamp for row in values}
    expected_panel = {(entity, timestamp) for entity in entities for timestamp in timestamps}
    if seen != expected_panel:
        missing = sorted(expected_panel - seen)
        raise B10ProgrammeNodeDemandError(f"incomplete programme entity/timestamp panel: {missing!r}")

    timestep_by_timestamp: dict[datetime, set[float]] = {}
    for row in values:
        timestep_by_timestamp.setdefault(row.timestamp, set()).add(row.timestep_hours)
    if any(len(steps) != 1 for steps in timestep_by_timestamp.values()):
        raise B10ProgrammeNodeDemandError("all entities must use one timestep per timestamp")

    unresolved = sorted({
        row.source_entity_id
        for row in values
        if row.spatial_authority.exact_node_status != EXACT_NODE_PROVEN
        or row.spatial_authority.target_node_region_id is None
        or row.evidence_status == "Q"
    })
    refs = tuple(sorted({ref for row in values for ref in (row.source_refs + row.spatial_authority.source_refs)}))
    if unresolved:
        return ProgrammeNodeDemandResult(
            status=Q_NODE_DEMAND_UNRESOLVED,
            scope=BOUNDED_EXPLICIT_PANEL,
            scope_id=scope_id,
            truth_context=truth,
            rows=(),
            peaks=(),
            unresolved_entity_ids=tuple(unresolved),
            source_refs=refs,
            reason="unresolved exact-node mapping or Q demand evidence makes the bounded node panel incomplete",
        )

    entity_nodes: dict[str, set[str]] = {}
    for row in values:
        try:
            node_id = require_exact_dso_substation_mapping(row.spatial_authority)
        except ValueError as exc:
            raise B10ProgrammeNodeDemandError(str(exc)) from exc
        entity_nodes.setdefault(row.source_entity_id, set()).add(node_id)
    moved = sorted(entity for entity, node_ids in entity_nodes.items() if len(node_ids) != 1)
    if moved:
        return ProgrammeNodeDemandResult(
            status=Q_NODE_DEMAND_UNRESOLVED,
            scope=BOUNDED_EXPLICIT_PANEL,
            scope_id=scope_id,
            truth_context=truth,
            rows=(),
            peaks=(),
            unresolved_entity_ids=tuple(moved),
            source_refs=refs,
            reason="one or more entity-to-node bindings change inside the aggregation panel",
        )

    grouped: dict[tuple[datetime, str], list[ProgrammeDemandSnapshot]] = {}
    for row in values:
        node_id = next(iter(entity_nodes[row.source_entity_id]))
        grouped.setdefault((row.timestamp, node_id), []).append(row)

    aggregates: list[ProgrammeNodeDemandAggregate] = []
    for (timestamp, node_id), group in sorted(grouped.items()):
        status = _status((row.evidence_status for row in group), truth)
        hp = sum(row.heat_pump_import_kw for row in group)
        charge = sum(row.battery_charge_import_kw for row in group)
        other = sum(row.other_programme_import_excluding_hp_and_battery_kw for row in group)
        total_kw = hp + charge + other
        row_refs = tuple(sorted({ref for row in group for ref in (row.source_refs + row.spatial_authority.source_refs)}))
        aggregates.append(
            ProgrammeNodeDemandAggregate(
                timestamp=timestamp,
                timestep_hours=group[0].timestep_hours,
                scope_id=scope_id,
                node_region_id=node_id,
                node_region_scheme=DSO_SUBSTATION,
                source_entity_count=len(group),
                heat_pump_import_kw=hp,
                battery_charge_import_kw=charge,
                other_programme_import_kw=other,
                positive_programme_import_kw=total_kw,
                incremental_demand_mw=total_kw / 1000.0,
                truth_context=truth,
                evidence_status=status,
                source_refs=row_refs,
            )
        )

    peaks: list[ProgrammeNodePeak] = []
    for node_id in sorted({row.node_region_id for row in aggregates}):
        node_rows = [row for row in aggregates if row.node_region_id == node_id]
        peak_mw = max(row.incremental_demand_mw for row in node_rows)
        peak_rows = [row for row in node_rows if row.incremental_demand_mw == peak_mw]
        peak_status = _status((row.evidence_status for row in peak_rows), truth)
        peaks.append(
            ProgrammeNodePeak(
                scope_id=scope_id,
                node_region_id=node_id,
                node_region_scheme=DSO_SUBSTATION,
                peak_positive_programme_import_mw=peak_mw,
                peak_timestamps=tuple(row.timestamp for row in peak_rows),
                truth_context=truth,
                evidence_status=peak_status,
                source_refs=tuple(sorted({ref for row in peak_rows for ref in row.source_refs})),
            )
        )

    result_status = _status((row.evidence_status for row in values), truth)
    return ProgrammeNodeDemandResult(
        status=NODE_DEMAND_PROVEN if result_status != "Q" else Q_NODE_DEMAND_UNRESOLVED,
        scope=BOUNDED_EXPLICIT_PANEL,
        scope_id=scope_id,
        truth_context=truth,
        rows=tuple(aggregates),
        peaks=tuple(peaks),
        unresolved_entity_ids=(),
        source_refs=refs,
        reason="complete explicit panel aggregated at P8-proven exact DSO_SUBSTATION nodes; no diversity/flex offset applied",
    )


def screen_programme_node_peak_against_mvm_headroom(
    peak: ProgrammeNodePeak,
    headroom: DsoHeadroomRecord,
) -> HeadroomAssessment:
    """Hand one proven unmanaged node peak to the existing P1 screening contract.

    This is screening only. The output is neither hosting-capacity authority nor a
    reinforcement, MGT, safe/unsafe, managed-peak, or programme-CAPEX decision.
    """

    if not isinstance(peak, ProgrammeNodePeak):
        raise B10ProgrammeNodeDemandError("peak must be ProgrammeNodePeak")
    if peak.node_region_scheme != DSO_SUBSTATION:
        raise B10ProgrammeNodeDemandError("programme peak must remain at DSO_SUBSTATION grain")
    if peak.evidence_status == "Q":
        raise B10ProgrammeNodeDemandError("Q programme peak cannot enter headroom screening")
    return assess_incremental_demand(
        headroom,
        incremental_demand_mw=peak.peak_positive_programme_import_mw,
        demand_region_id=peak.node_region_id,
        demand_region_scheme=peak.node_region_scheme,
        demand_evidence_status=peak.evidence_status,
        demand_source_refs=peak.source_refs,
    )


__all__ = [
    "BOUNDED_EXPLICIT_PANEL",
    "B10ProgrammeNodeDemandError",
    "NODE_DEMAND_PROVEN",
    "NO_DIVERSITY_OR_FLEX_AUTHORITY",
    "ProgrammeDemandSnapshot",
    "ProgrammeNodeDemandAggregate",
    "ProgrammeNodeDemandResult",
    "ProgrammeNodePeak",
    "Q_NODE_DEMAND_UNRESOLVED",
    "UNMANAGED_POSITIVE_PROGRAMME_IMPORT",
    "aggregate_programme_node_demand",
    "screen_programme_node_peak_against_mvm_headroom",
]
