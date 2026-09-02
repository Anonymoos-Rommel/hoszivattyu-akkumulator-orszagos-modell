"""Fail-closed B10-P10 managed-flex and physical-survivability authority gate.

Five truths remain separate:

PHYSICAL FLEX CAPABILITY
!= COMMITTED/AVAILABLE FLEX
!= DISPATCHED/DELIVERED FLEX
!= MANAGED NODE LOAD
!= NETWORK SURVIVABILITY

P10 consumes the original P9 entity/timestamp demand snapshots, re-runs the P9
aggregation contract, and requires the flex panel to contain exactly the same
entities and timestamps at the same P8-proven DSO_SUBSTATION nodes. This keeps
entity lineage exact without inventing a proxy crosswalk.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from math import isfinite
from typing import Iterable

from .programme_node_demand_contract import (
    NODE_DEMAND_PROVEN,
    ProgrammeDemandSnapshot,
    ProgrammeNodeDemandResult,
    aggregate_programme_node_demand,
)
from .spatial_authority_contract import DSO_SUBSTATION, require_exact_dso_substation_mapping


class B10ManagedFlexSurvivabilityError(ValueError):
    """Raised when flex, managed-load or survivability authority is overstated."""


REAL = "REAL"
SCN = "SCN"
TRUTH_CONTEXTS = {REAL, SCN}
EVIDENCE_STATUSES = {"OBS", "DER", "SCN", "Q"}

PHYSICAL_FLEX_CAPABILITY = "PHYSICAL_FLEX_CAPABILITY"
FLEX_COMMITMENT = "FLEX_COMMITMENT"
FLEX_ACTIVATION = "FLEX_ACTIVATION"
FLEX_DELIVERY = "FLEX_DELIVERY"
NETWORK_SURVIVABILITY = "NETWORK_SURVIVABILITY"

PHYSICAL_ONLY = "PHYSICAL_ONLY"
COMMITTED_NOT_DELIVERED = "COMMITTED_NOT_DELIVERED"
DELIVERED_FLEX_PROVEN = "DELIVERED_FLEX_PROVEN"
SCN_DISPATCH_PROVEN = "SCN_DISPATCH_PROVEN"
Q_FLEX_AUTHORITY_UNRESOLVED = "Q_FLEX_AUTHORITY_UNRESOLVED"

MANAGED_NODE_LOAD_PROVEN = "MANAGED_NODE_LOAD_PROVEN"
SCN_MANAGED_NODE_LOAD = "SCN_MANAGED_NODE_LOAD"
Q_MANAGED_NODE_LOAD_UNRESOLVED = "Q_MANAGED_NODE_LOAD_UNRESOLVED"

SURVIVABILITY_PROVEN = "SURVIVABILITY_PROVEN"
Q_NETWORK_SURVIVABILITY_UNRESOLVED = "Q_NETWORK_SURVIVABILITY_UNRESOLVED"

ENTITY_ID_PREFIX = "ENTITY_ID:"
NODE_REGION_ID_PREFIX = "NODE_REGION_ID:"
TIMESTAMP_PREFIX = "TIMESTAMP:"
NETWORK_OPERATOR_PREFIX = "NETWORK_OPERATOR:"
NETWORK_STUDY_ID_PREFIX = "NETWORK_STUDY_ID:"
NODE_REGION_GRAIN_BINDING = "NODE_REGION_GRAIN:DSO_SUBSTATION"
ASSESSED_MANAGED_PEAK_PREFIX = "ASSESSED_MANAGED_PEAK_MW:"


def _nonnegative(value: float, name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not isfinite(value) or value < 0:
        raise B10ManagedFlexSurvivabilityError(f"{name} must be finite and non-negative")
    return float(value)


def _text(value: str, name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise B10ManagedFlexSurvivabilityError(f"{name} is required")
    return value


@dataclass(frozen=True)
class FlexAuthorityEvidence:
    source_id: str
    authority_level: int
    truth_status: str
    supports: tuple[str, ...]

    def __post_init__(self) -> None:
        _text(self.source_id, "source_id")
        if self.authority_level not in {1, 2, 3, 4, 5}:
            raise B10ManagedFlexSurvivabilityError("authority_level must be 1..5")
        if self.truth_status not in EVIDENCE_STATUSES:
            raise B10ManagedFlexSurvivabilityError("invalid truth_status")
        if isinstance(self.supports, str) or any(not isinstance(item, str) or not item.strip() for item in self.supports):
            raise B10ManagedFlexSurvivabilityError("supports must be an explicit non-blank collection")


@dataclass(frozen=True)
class FlexDispatchSnapshot:
    timestamp: datetime
    timestep_hours: float
    scope_id: str
    source_entity_id: str
    node_region_id: str
    truth_context: str
    physical_up_flex_kw: float
    committed_up_flex_kw: float
    dispatched_up_flex_kw: float
    delivered_up_flex_kw: float
    source_refs: tuple[str, ...]
    evidence: tuple[FlexAuthorityEvidence, ...]
    node_region_scheme: str = DSO_SUBSTATION

    def __post_init__(self) -> None:
        if not isinstance(self.timestamp, datetime) or self.timestamp.tzinfo is None or self.timestamp.utcoffset() is None:
            raise B10ManagedFlexSurvivabilityError("timestamp must be timezone-aware")
        object.__setattr__(self, "timestamp", self.timestamp.astimezone(timezone.utc))
        if isinstance(self.timestep_hours, bool) or not isinstance(self.timestep_hours, (int, float)) or not isfinite(self.timestep_hours) or self.timestep_hours <= 0:
            raise B10ManagedFlexSurvivabilityError("timestep_hours must be finite and positive")
        object.__setattr__(self, "timestep_hours", float(self.timestep_hours))
        for name in ("scope_id", "source_entity_id", "node_region_id"):
            _text(getattr(self, name), name)
        if self.node_region_scheme != DSO_SUBSTATION:
            raise B10ManagedFlexSurvivabilityError("P10 flex must remain at exact DSO_SUBSTATION grain")
        if self.truth_context not in TRUTH_CONTEXTS:
            raise B10ManagedFlexSurvivabilityError("truth_context must be REAL or SCN")
        for name in ("physical_up_flex_kw", "committed_up_flex_kw", "dispatched_up_flex_kw", "delivered_up_flex_kw"):
            object.__setattr__(self, name, _nonnegative(getattr(self, name), name))
        if self.committed_up_flex_kw > self.physical_up_flex_kw:
            raise B10ManagedFlexSurvivabilityError("commitment cannot exceed physical capability")
        if self.dispatched_up_flex_kw > self.committed_up_flex_kw:
            raise B10ManagedFlexSurvivabilityError("dispatch cannot exceed committed flexibility")
        if self.delivered_up_flex_kw > self.dispatched_up_flex_kw:
            raise B10ManagedFlexSurvivabilityError("delivered flex cannot exceed dispatched flex")
        if isinstance(self.source_refs, str) or not self.source_refs or any(not isinstance(ref, str) or not ref.strip() for ref in self.source_refs):
            raise B10ManagedFlexSurvivabilityError("source_refs must be non-empty")
        if isinstance(self.evidence, str) or not self.evidence:
            raise B10ManagedFlexSurvivabilityError("evidence must be non-empty")
        evidence_ids = {item.source_id for item in self.evidence}
        if not set(self.source_refs).issubset(evidence_ids):
            raise B10ManagedFlexSurvivabilityError("source_refs must identify supplied evidence")

    @property
    def referenced_evidence(self) -> tuple[FlexAuthorityEvidence, ...]:
        refs = set(self.source_refs)
        return tuple(item for item in self.evidence if item.source_id in refs)


@dataclass(frozen=True)
class FlexAuthorityDecision:
    source_entity_id: str
    timestamp: datetime
    node_region_id: str
    authority_status: str
    usable_managed_reduction_kw: float | None
    evidence_status: str
    source_refs: tuple[str, ...]
    reason: str


def _bound_claim(snapshot: FlexDispatchSnapshot, claim: str, max_level: int) -> bool:
    required = {
        claim,
        f"{ENTITY_ID_PREFIX}{snapshot.source_entity_id}",
        f"{NODE_REGION_ID_PREFIX}{snapshot.node_region_id}",
        NODE_REGION_GRAIN_BINDING,
        f"{TIMESTAMP_PREFIX}{snapshot.timestamp.isoformat()}",
    }
    allowed_truth = {"OBS", "DER"} if snapshot.truth_context == REAL else {"SCN"}
    return any(
        item.authority_level <= max_level
        and item.truth_status in allowed_truth
        and required.issubset(set(item.supports))
        for item in snapshot.referenced_evidence
    )


def classify_flex_authority(snapshot: FlexDispatchSnapshot) -> FlexAuthorityDecision:
    """Do not let capability, commitment, dispatch and delivery substitute for each other."""
    if not isinstance(snapshot, FlexDispatchSnapshot):
        raise B10ManagedFlexSurvivabilityError("snapshot must be FlexDispatchSnapshot")

    physical = _bound_claim(snapshot, PHYSICAL_FLEX_CAPABILITY, 4)
    commitment = _bound_claim(snapshot, FLEX_COMMITMENT, 3)
    activation = _bound_claim(snapshot, FLEX_ACTIVATION, 3)
    delivery = _bound_claim(snapshot, FLEX_DELIVERY, 3)

    status: str
    usable: float | None
    reason: str
    if snapshot.physical_up_flex_kw > 0 and not physical:
        status, usable = Q_FLEX_AUTHORITY_UNRESOLVED, None
        reason = "numeric physical capability lacks referenced entity/node/timestamp authority"
    elif snapshot.truth_context == REAL and snapshot.delivered_up_flex_kw > 0:
        if commitment and activation and delivery:
            status, usable = DELIVERED_FLEX_PROVEN, snapshot.delivered_up_flex_kw
            reason = "REAL commitment, activation and delivery are separately proven at the exact entity/node/timestamp"
        else:
            status, usable = Q_FLEX_AUTHORITY_UNRESOLVED, None
            reason = "REAL managed reduction requires bound commitment, activation and delivered-flex authority"
    elif snapshot.truth_context == REAL and snapshot.dispatched_up_flex_kw > 0:
        status, usable = Q_FLEX_AUTHORITY_UNRESOLVED, None
        reason = "REAL dispatch without proven delivery cannot reduce managed load"
    elif snapshot.truth_context == SCN and snapshot.dispatched_up_flex_kw > 0:
        if activation:
            status = SCN_DISPATCH_PROVEN
            usable = snapshot.delivered_up_flex_kw if delivery and snapshot.delivered_up_flex_kw > 0 else snapshot.dispatched_up_flex_kw
            reason = "explicit SCN dispatch is bound to the exact entity/node/timestamp"
        else:
            status, usable = Q_FLEX_AUTHORITY_UNRESOLVED, None
            reason = "SCN numeric dispatch requires explicit bound activation authority"
    elif snapshot.committed_up_flex_kw > 0:
        if commitment:
            status, usable = COMMITTED_NOT_DELIVERED, 0.0
            reason = "commitment is proven but commitment is not dispatch/delivery"
        else:
            status, usable = Q_FLEX_AUTHORITY_UNRESOLVED, None
            reason = "numeric commitment lacks claim-specific authority"
    else:
        status = PHYSICAL_ONLY if physical or snapshot.physical_up_flex_kw == 0 else Q_FLEX_AUTHORITY_UNRESOLVED
        usable = 0.0 if status == PHYSICAL_ONLY else None
        reason = "physical flexibility capability alone does not reduce managed load"

    statuses = {item.truth_status for item in snapshot.referenced_evidence}
    if status == Q_FLEX_AUTHORITY_UNRESOLVED or "Q" in statuses:
        evidence_status = "Q"
    elif snapshot.truth_context == SCN:
        evidence_status = "SCN"
    elif statuses == {"OBS"}:
        evidence_status = "OBS"
    else:
        evidence_status = "DER"
    return FlexAuthorityDecision(
        snapshot.source_entity_id,
        snapshot.timestamp,
        snapshot.node_region_id,
        status,
        usable,
        evidence_status,
        tuple(dict.fromkeys(snapshot.source_refs)),
        reason,
    )


@dataclass(frozen=True)
class ManagedNodeLoadRow:
    timestamp: datetime
    scope_id: str
    node_region_id: str
    unmanaged_programme_import_mw: float
    proven_managed_reduction_mw: float
    managed_programme_import_mw: float
    truth_context: str
    evidence_status: str
    source_refs: tuple[str, ...]
    node_region_scheme: str = DSO_SUBSTATION


@dataclass(frozen=True)
class ManagedNodeLoadResult:
    status: str
    scope_id: str
    truth_context: str
    unmanaged: ProgrammeNodeDemandResult
    rows: tuple[ManagedNodeLoadRow, ...]
    peak_managed_import_mw_by_node: tuple[tuple[str, float], ...]
    source_refs: tuple[str, ...]
    reason: str


def build_managed_node_load(
    programme_snapshots: Iterable[ProgrammeDemandSnapshot],
    flex_snapshots: Iterable[FlexDispatchSnapshot],
) -> ManagedNodeLoadResult:
    """Build managed load only from exact P9 entity lineage plus exact flex lineage."""
    demand_values = tuple(programme_snapshots)
    flex_values = tuple(flex_snapshots)
    unmanaged = aggregate_programme_node_demand(demand_values)
    if unmanaged.status != NODE_DEMAND_PROVEN or not unmanaged.rows:
        raise B10ManagedFlexSurvivabilityError("managed load requires a proven P9 programme-node demand panel")
    if not flex_values:
        raise B10ManagedFlexSurvivabilityError("flex_snapshots are required")

    demand_entities = {item.source_entity_id for item in demand_values}
    demand_timestamps = {item.timestamp for item in demand_values}
    flex_entities = {item.source_entity_id for item in flex_values}
    flex_timestamps = {item.timestamp for item in flex_values}
    if flex_entities != demand_entities or flex_timestamps != demand_timestamps:
        raise B10ManagedFlexSurvivabilityError("flex panel must contain exactly the P9 entities and timestamps")
    expected = {(entity, timestamp) for entity in demand_entities for timestamp in demand_timestamps}
    actual = {(item.source_entity_id, item.timestamp) for item in flex_values}
    if len(actual) != len(flex_values):
        raise B10ManagedFlexSurvivabilityError("duplicate flex entity/timestamp row")
    if actual != expected:
        raise B10ManagedFlexSurvivabilityError("flex entity/timestamp panel must be complete")
    if {item.scope_id for item in flex_values} != {unmanaged.scope_id}:
        raise B10ManagedFlexSurvivabilityError("flex scope must exactly match P9 scope_id")
    if {item.truth_context for item in flex_values} != {unmanaged.truth_context}:
        raise B10ManagedFlexSurvivabilityError("flex truth context must exactly match P9")

    demand_by_entity_time = {(item.source_entity_id, item.timestamp): item for item in demand_values}
    p9_by_node_time = {(item.timestamp, item.node_region_id): item for item in unmanaged.rows}
    decisions: list[FlexAuthorityDecision] = []
    for flex in flex_values:
        demand = demand_by_entity_time[(flex.source_entity_id, flex.timestamp)]
        node_id = require_exact_dso_substation_mapping(demand.spatial_authority)
        if flex.node_region_id != node_id:
            raise B10ManagedFlexSurvivabilityError("flex entity must remain on its exact P9/P8 DSO_SUBSTATION node")
        if flex.timestep_hours != demand.timestep_hours:
            raise B10ManagedFlexSurvivabilityError("flex timestep must exactly match P9 entity timestep")
        decisions.append(classify_flex_authority(flex))

    if any(item.authority_status == Q_FLEX_AUTHORITY_UNRESOLVED or item.evidence_status == "Q" for item in decisions):
        refs = tuple(sorted(set(unmanaged.source_refs) | {ref for item in flex_values for ref in item.source_refs}))
        return ManagedNodeLoadResult(
            Q_MANAGED_NODE_LOAD_UNRESOLVED,
            unmanaged.scope_id,
            unmanaged.truth_context,
            unmanaged,
            (),
            (),
            refs,
            "one or more exact-lineage flex rows lack sufficient authority",
        )

    reduction_kw: dict[tuple[datetime, str], float] = {}
    refs_by_key: dict[tuple[datetime, str], set[str]] = {}
    for flex, decision in zip(flex_values, decisions):
        key = (flex.timestamp, flex.node_region_id)
        usable = decision.usable_managed_reduction_kw
        if usable is None:
            raise B10ManagedFlexSurvivabilityError("unresolved flex cannot enter managed-load arithmetic")
        reduction_kw[key] = reduction_kw.get(key, 0.0) + usable
        refs_by_key.setdefault(key, set()).update(flex.source_refs)

    rows: list[ManagedNodeLoadRow] = []
    for key, p9_row in sorted(p9_by_node_time.items()):
        available_kw = reduction_kw.get(key, 0.0)
        applied_kw = min(available_kw, p9_row.positive_programme_import_kw)
        managed_kw = p9_row.positive_programme_import_kw - applied_kw
        row_decisions = [d for d in decisions if d.timestamp == key[0] and d.node_region_id == key[1]]
        if unmanaged.truth_context == SCN:
            evidence_status = "SCN"
        else:
            evidence_status = "OBS" if p9_row.evidence_status == "OBS" and all(d.evidence_status == "OBS" for d in row_decisions) else "DER"
        refs = tuple(sorted(set(p9_row.source_refs) | refs_by_key.get(key, set())))
        rows.append(ManagedNodeLoadRow(
            p9_row.timestamp,
            unmanaged.scope_id,
            p9_row.node_region_id,
            p9_row.incremental_demand_mw,
            applied_kw / 1000.0,
            managed_kw / 1000.0,
            unmanaged.truth_context,
            evidence_status,
            refs,
        ))

    peaks = tuple(
        (node_id, max(row.managed_programme_import_mw for row in rows if row.node_region_id == node_id))
        for node_id in sorted({row.node_region_id for row in rows})
    )
    refs = tuple(sorted(set(unmanaged.source_refs) | {ref for row in rows for ref in row.source_refs}))
    status = SCN_MANAGED_NODE_LOAD if unmanaged.truth_context == SCN else MANAGED_NODE_LOAD_PROVEN
    return ManagedNodeLoadResult(
        status,
        unmanaged.scope_id,
        unmanaged.truth_context,
        unmanaged,
        tuple(rows),
        peaks,
        refs,
        "only bound SCN dispatch or proven REAL delivered flex reduces exact-node programme load",
    )


@dataclass(frozen=True)
class NetworkSurvivabilityEvidence:
    source_id: str
    authority_level: int
    truth_status: str
    supports: tuple[str, ...]

    def __post_init__(self) -> None:
        _text(self.source_id, "source_id")
        if self.authority_level not in {1, 2, 3, 4, 5}:
            raise B10ManagedFlexSurvivabilityError("authority_level must be 1..5")
        if self.truth_status not in {"OBS", "DER", "Q"}:
            raise B10ManagedFlexSurvivabilityError("survivability truth_status must be OBS, DER or Q")
        if isinstance(self.supports, str):
            raise B10ManagedFlexSurvivabilityError("supports must be a collection")


@dataclass(frozen=True)
class NetworkSurvivabilityRecord:
    network_operator: str
    network_study_id: str
    node_region_id: str
    assessed_managed_peak_mw: float
    source_refs: tuple[str, ...]
    evidence: tuple[NetworkSurvivabilityEvidence, ...]
    node_region_scheme: str = DSO_SUBSTATION

    def __post_init__(self) -> None:
        for name in ("network_operator", "network_study_id", "node_region_id"):
            _text(getattr(self, name), name)
        if self.node_region_scheme != DSO_SUBSTATION:
            raise B10ManagedFlexSurvivabilityError("survivability study must bind exact DSO_SUBSTATION grain")
        object.__setattr__(self, "assessed_managed_peak_mw", _nonnegative(self.assessed_managed_peak_mw, "assessed_managed_peak_mw"))
        if isinstance(self.source_refs, str) or not self.source_refs:
            raise B10ManagedFlexSurvivabilityError("source_refs are required")
        evidence_ids = {item.source_id for item in self.evidence}
        if not set(self.source_refs).issubset(evidence_ids):
            raise B10ManagedFlexSurvivabilityError("source_refs must identify supplied survivability evidence")

    @property
    def referenced_evidence(self) -> tuple[NetworkSurvivabilityEvidence, ...]:
        refs = set(self.source_refs)
        return tuple(item for item in self.evidence if item.source_id in refs)


@dataclass(frozen=True)
class NetworkSurvivabilityDecision:
    node_region_id: str
    status: str
    assessed_managed_peak_mw: float | None
    evidence_status: str
    source_refs: tuple[str, ...]
    reason: str


def evaluate_network_survivability(record: NetworkSurvivabilityRecord) -> NetworkSurvivabilityDecision:
    """Managed peak/headroom/flex cannot mint survivability without a network study."""
    if not isinstance(record, NetworkSurvivabilityRecord):
        raise B10ManagedFlexSurvivabilityError("record must be NetworkSurvivabilityRecord")
    required = {
        NETWORK_SURVIVABILITY,
        f"{NETWORK_OPERATOR_PREFIX}{record.network_operator}",
        f"{NETWORK_STUDY_ID_PREFIX}{record.network_study_id}",
        f"{NODE_REGION_ID_PREFIX}{record.node_region_id}",
        NODE_REGION_GRAIN_BINDING,
        f"{ASSESSED_MANAGED_PEAK_PREFIX}{record.assessed_managed_peak_mw}",
    }
    matches = [item for item in record.referenced_evidence if item.authority_level <= 2 and item.truth_status in {"OBS", "DER"} and required.issubset(set(item.supports))]
    if not matches:
        return NetworkSurvivabilityDecision(
            record.node_region_id,
            Q_NETWORK_SURVIVABILITY_UNRESOLVED,
            None,
            "Q",
            tuple(dict.fromkeys(record.source_refs)),
            "no referenced claim-specific DSO/network-study survivability authority",
        )
    evidence_status = "OBS" if all(item.truth_status == "OBS" for item in matches) else "DER"
    return NetworkSurvivabilityDecision(
        record.node_region_id,
        SURVIVABILITY_PROVEN,
        record.assessed_managed_peak_mw,
        evidence_status,
        tuple(dict.fromkeys(record.source_refs)),
        "authoritative network study binds survivability to the exact node and assessed managed peak",
    )


__all__ = [
    "B10ManagedFlexSurvivabilityError",
    "COMMITTED_NOT_DELIVERED",
    "DELIVERED_FLEX_PROVEN",
    "FLEX_ACTIVATION",
    "FLEX_COMMITMENT",
    "FLEX_DELIVERY",
    "FlexAuthorityDecision",
    "FlexAuthorityEvidence",
    "FlexDispatchSnapshot",
    "MANAGED_NODE_LOAD_PROVEN",
    "ManagedNodeLoadResult",
    "ManagedNodeLoadRow",
    "NETWORK_SURVIVABILITY",
    "NetworkSurvivabilityDecision",
    "NetworkSurvivabilityEvidence",
    "NetworkSurvivabilityRecord",
    "PHYSICAL_FLEX_CAPABILITY",
    "PHYSICAL_ONLY",
    "Q_FLEX_AUTHORITY_UNRESOLVED",
    "Q_MANAGED_NODE_LOAD_UNRESOLVED",
    "Q_NETWORK_SURVIVABILITY_UNRESOLVED",
    "SCN_DISPATCH_PROVEN",
    "SCN_MANAGED_NODE_LOAD",
    "SURVIVABILITY_PROVEN",
    "build_managed_node_load",
    "classify_flex_authority",
    "evaluate_network_survivability",
]
