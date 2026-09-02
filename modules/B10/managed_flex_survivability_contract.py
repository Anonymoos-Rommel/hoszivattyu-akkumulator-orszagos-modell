"""Fail-closed B10-P10 managed-flex and physical-survivability authority gate.

The contract keeps five truths separate:

1. physical flexibility capability;
2. committed/available flexibility;
3. dispatched/delivered flexibility;
4. managed programme node load;
5. physical network survivability.

Physical capability cannot reduce B10-P9 unmanaged demand. A managed load may be
computed only from explicit same-node, same-timestamp dispatch/delivery evidence
(or an explicit SCN dispatch in scenario truth). Even a valid managed load does
not prove hosting capacity, safe operation, MGT approval, reinforcement, or
network survivability; those require separate claim-specific network authority.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from math import isfinite
from typing import Iterable

from .programme_node_demand_contract import (
    BOUNDED_EXPLICIT_PANEL,
    NODE_DEMAND_PROVEN,
    ProgrammeNodeDemandAggregate,
    ProgrammeNodeDemandResult,
)
from .spatial_authority_contract import DSO_SUBSTATION


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

_FLEX_DELIVERY_AUTHORITY_MAX_LEVEL = 3
_SURVIVABILITY_AUTHORITY_MAX_LEVEL = 2


def _nonnegative(value: float, name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not isfinite(value) or value < 0:
        raise B10ManagedFlexSurvivabilityError(f"{name} must be finite and non-negative")
    return float(value)


def _required_text(value: str, name: str) -> str:
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
        _required_text(self.source_id, "source_id")
        if self.authority_level not in {1, 2, 3, 4, 5}:
            raise B10ManagedFlexSurvivabilityError("authority_level must be 1..5")
        if self.truth_status not in EVIDENCE_STATUSES:
            raise B10ManagedFlexSurvivabilityError("invalid truth_status")
        if isinstance(self.supports, str) or any(not isinstance(item, str) or not item.strip() for item in self.supports):
            raise B10ManagedFlexSurvivabilityError("supports must be an explicit non-blank collection")


@dataclass(frozen=True)
class FlexDispatchSnapshot:
    """One entity/timestep physical-flex and dispatch/delivery authority record."""

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
            _required_text(getattr(self, name), name)
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
    physical_up_flex_kw: float
    committed_up_flex_kw: float
    dispatched_up_flex_kw: float
    delivered_up_flex_kw: float
    evidence_status: str
    source_refs: tuple[str, ...]
    reason: str


def _binding_claims(snapshot: FlexDispatchSnapshot) -> set[str]:
    return {
        f"{ENTITY_ID_PREFIX}{snapshot.source_entity_id}",
        f"{NODE_REGION_ID_PREFIX}{snapshot.node_region_id}",
        NODE_REGION_GRAIN_BINDING,
        f"{TIMESTAMP_PREFIX}{snapshot.timestamp.isoformat()}",
    }


def _has_bound_claim(snapshot: FlexDispatchSnapshot, claim: str, *, max_authority_level: int) -> bool:
    required = _binding_claims(snapshot) | {claim}
    return any(
        item.authority_level <= max_authority_level
        and item.truth_status in ({"OBS", "DER"} if snapshot.truth_context == REAL else {"SCN"})
        and required.issubset(set(item.supports))
        for item in snapshot.referenced_evidence
    )


def classify_flex_authority(snapshot: FlexDispatchSnapshot) -> FlexAuthorityDecision:
    """Classify physical/commit/dispatch/delivery truth without substituting one for another."""

    if not isinstance(snapshot, FlexDispatchSnapshot):
        raise B10ManagedFlexSurvivabilityError("snapshot must be FlexDispatchSnapshot")

    physical = _has_bound_claim(snapshot, PHYSICAL_FLEX_CAPABILITY, max_authority_level=4)
    commitment = _has_bound_claim(snapshot, FLEX_COMMITMENT, max_authority_level=3)
    activation = _has_bound_claim(snapshot, FLEX_ACTIVATION, max_authority_level=3)
    delivery = _has_bound_claim(snapshot, FLEX_DELIVERY, max_authority_level=_FLEX_DELIVERY_AUTHORITY_MAX_LEVEL)

    if snapshot.physical_up_flex_kw > 0 and not physical:
        status = Q_FLEX_AUTHORITY_UNRESOLVED
        usable = None
        reason = "numeric physical flexibility lacks referenced entity/node/timestamp capability authority"
    elif snapshot.delivered_up_flex_kw > 0:
        if snapshot.truth_context == REAL and commitment and activation and delivery:
            status = DELIVERED_FLEX_PROVEN
            usable = snapshot.delivered_up_flex_kw
            reason = "referenced authority proves commitment, activation and delivered flex at the exact entity/node/timestamp"
        elif snapshot.truth_context == SCN and activation and delivery:
            status = SCN_DISPATCH_PROVEN
            usable = snapshot.delivered_up_flex_kw
            reason = "explicit SCN dispatch/delivery is bound to the exact entity/node/timestamp"
        else:
            status = Q_FLEX_AUTHORITY_UNRESOLVED
            usable = None
            reason = "delivered numeric flex cannot reduce load without bound activation/delivery authority"
    elif snapshot.dispatched_up_flex_kw > 0:
        if snapshot.truth_context == SCN and activation:
            status = SCN_DISPATCH_PROVEN
            usable = snapshot.dispatched_up_flex_kw
            reason = "explicit SCN dispatch is bound to the exact entity/node/timestamp"
        else:
            status = Q_FLEX_AUTHORITY_UNRESOLVED
            usable = None
            reason = "dispatch without proven delivery cannot reduce REAL managed load"
    elif snapshot.committed_up_flex_kw > 0:
        if commitment:
            status = COMMITTED_NOT_DELIVERED
            usable = 0.0
            reason = "commitment is proven but commitment is not delivery"
        else:
            status = Q_FLEX_AUTHORITY_UNRESOLVED
            usable = None
            reason = "numeric commitment lacks claim-specific authority"
    else:
        status = PHYSICAL_ONLY if physical or snapshot.physical_up_flex_kw == 0 else Q_FLEX_AUTHORITY_UNRESOLVED
        usable = 0.0 if status == PHYSICAL_ONLY else None
        reason = "physical flexibility capability is not committed/activated/delivered flexibility"

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
        source_entity_id=snapshot.source_entity_id,
        timestamp=snapshot.timestamp,
        node_region_id=snapshot.node_region_id,
        authority_status=status,
        usable_managed_reduction_kw=usable,
        physical_up_flex_kw=snapshot.physical_up_flex_kw,
        committed_up_flex_kw=snapshot.committed_up_flex_kw,
        dispatched_up_flex_kw=snapshot.dispatched_up_flex_kw,
        delivered_up_flex_kw=snapshot.delivered_up_flex_kw,
        evidence_status=evidence_status,
        source_refs=tuple(dict.fromkeys(snapshot.source_refs)),
        reason=reason,
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
    rows: tuple[ManagedNodeLoadRow, ...]
    peak_managed_import_mw_by_node: tuple[tuple[str, float], ...]
    source_refs: tuple[str, ...]
    reason: str


def build_managed_node_load(
    unmanaged: ProgrammeNodeDemandResult,
    flex_snapshots: Iterable[FlexDispatchSnapshot],
) -> ManagedNodeLoadResult:
    """Reduce P9 load only by exact-node/timestamp flex with sufficient authority.

    The P9 result must be a complete proven bounded panel. P10 also requires a
    complete flex entity/timestamp panel and exact scope/truth/timestep/node match.
    Any unresolved flex authority fails the whole managed-load result closed.
    """

    if not isinstance(unmanaged, ProgrammeNodeDemandResult):
        raise B10ManagedFlexSurvivabilityError("unmanaged must be ProgrammeNodeDemandResult")
    if unmanaged.status != NODE_DEMAND_PROVEN or unmanaged.scope != BOUNDED_EXPLICIT_PANEL or not unmanaged.rows:
        raise B10ManagedFlexSurvivabilityError("managed load requires a proven P9 bounded explicit node-demand result")

    values = tuple(flex_snapshots)
    if not values:
        raise B10ManagedFlexSurvivabilityError("flex_snapshots are required")
    if any(not isinstance(item, FlexDispatchSnapshot) for item in values):
        raise B10ManagedFlexSurvivabilityError("all flex rows must be FlexDispatchSnapshot")
    if {item.scope_id for item in values} != {unmanaged.scope_id}:
        raise B10ManagedFlexSurvivabilityError("flex scope must exactly match P9 scope_id")
    if {item.truth_context for item in values} != {unmanaged.truth_context}:
        raise B10ManagedFlexSurvivabilityError("flex truth context must exactly match P9")

    seen: set[tuple[str, datetime]] = set()
    for item in values:
        key = (item.source_entity_id, item.timestamp)
        if key in seen:
            raise B10ManagedFlexSurvivabilityError(f"duplicate flex entity/timestamp row: {key!r}")
        seen.add(key)
    entities = {item.source_entity_id for item in values}
    timestamps = {row.timestamp for row in unmanaged.rows}
    expected = {(entity, timestamp) for entity in entities for timestamp in timestamps}
    if seen != expected:
        raise B10ManagedFlexSurvivabilityError("flex entity/timestamp panel must be complete over all P9 timestamps")

    p9_by_key = {(row.timestamp, row.node_region_id): row for row in unmanaged.rows}
    decisions = tuple(classify_flex_authority(item) for item in values)
    if any(item.authority_status == Q_FLEX_AUTHORITY_UNRESOLVED for item in decisions):
        refs = tuple(sorted({ref for item in values for ref in item.source_refs} | set(unmanaged.source_refs)))
        return ManagedNodeLoadResult(
            status=Q_MANAGED_NODE_LOAD_UNRESOLVED,
            scope_id=unmanaged.scope_id,
            truth_context=unmanaged.truth_context,
            rows=(),
            peak_managed_import_mw_by_node=(),
            source_refs=refs,
            reason="one or more flex rows lack sufficient physical/commit/dispatch/delivery authority",
        )

    grouped_reduction_kw: dict[tuple[datetime, str], float] = {}
    refs_by_key: dict[tuple[datetime, str], set[str]] = {}
    for snapshot, decision in zip(values, decisions):
        key = (snapshot.timestamp, snapshot.node_region_id)
        if key not in p9_by_key:
            raise B10ManagedFlexSurvivabilityError("flex node/timestamp must exactly match a P9 node row")
        if snapshot.timestep_hours != p9_by_key[key].timestep_hours:
            raise B10ManagedFlexSurvivabilityError("flex timestep must exactly match P9 timestep")
        reduction = decision.usable_managed_reduction_kw
        if reduction is None:
            raise B10ManagedFlexSurvivabilityError("unresolved flex cannot enter managed-load arithmetic")
        grouped_reduction_kw[key] = grouped_reduction_kw.get(key, 0.0) + reduction
        refs_by_key.setdefault(key, set()).update(snapshot.source_refs)

    rows: list[ManagedNodeLoadRow] = []
    for key, p9_row in sorted(p9_by_key.items()):
        reduction_kw = grouped_reduction_kw.get(key, 0.0)
        # Flex cannot create a negative programme import in this gate. Export and
        # reverse-power-flow authority are distinct network questions.
        applied_kw = min(reduction_kw, p9_row.positive_programme_import_kw)
        managed_kw = p9_row.positive_programme_import_kw - applied_kw
        row_refs = tuple(sorted(set(p9_row.source_refs) | refs_by_key.get(key, set())))
        statuses = {d.evidence_status for d in decisions if d.timestamp == key[0] and d.node_region_id == key[1]}
        if unmanaged.truth_context == SCN:
            evidence_status = "SCN" if statuses <= {"SCN"} else "Q"
        else:
            evidence_status = "OBS" if statuses == {"OBS"} and p9_row.evidence_status == "OBS" else "DER"
        rows.append(
            ManagedNodeLoadRow(
                timestamp=p9_row.timestamp,
                scope_id=unmanaged.scope_id,
                node_region_id=p9_row.node_region_id,
                unmanaged_programme_import_mw=p9_row.incremental_demand_mw,
                proven_managed_reduction_mw=applied_kw / 1000.0,
                managed_programme_import_mw=managed_kw / 1000.0,
                truth_context=unmanaged.truth_context,
                evidence_status=evidence_status,
                source_refs=row_refs,
            )
        )

    peaks: list[tuple[str, float]] = []
    for node_id in sorted({row.node_region_id for row in rows}):
        node_rows = [row for row in rows if row.node_region_id == node_id]
        peaks.append((node_id, max(row.managed_programme_import_mw for row in node_rows)))
    refs = tuple(sorted({ref for row in rows for ref in row.source_refs} | set(unmanaged.source_refs)))
    status = SCN_MANAGED_NODE_LOAD if unmanaged.truth_context == SCN else MANAGED_NODE_LOAD_PROVEN
    return ManagedNodeLoadResult(
        status=status,
        scope_id=unmanaged.scope_id,
        truth_context=unmanaged.truth_context,
        rows=tuple(rows),
        peak_managed_import_mw_by_node=tuple(peaks),
        source_refs=refs,
        reason="managed load uses only exact-node/timestamp dispatch/delivery authority; physical or committed flex alone is not subtracted",
    )


@dataclass(frozen=True)
class NetworkSurvivabilityEvidence:
    source_id: str
    authority_level: int
    truth_status: str
    supports: tuple[str, ...]

    def __post_init__(self) -> None:
        _required_text(self.source_id, "source_id")
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
    source_refs: tuple[str, ...]
    evidence: tuple[NetworkSurvivabilityEvidence, ...]
    assessed_managed_peak_mw: float
    node_region_scheme: str = DSO_SUBSTATION

    def __post_init__(self) -> None:
        for name in ("network_operator", "network_study_id", "node_region_id"):
            _required_text(getattr(self, name), name)
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
    """Require claim-specific DSO/network-study authority; managed load is not enough."""

    if not isinstance(record, NetworkSurvivabilityRecord):
        raise B10ManagedFlexSurvivabilityError("record must be NetworkSurvivabilityRecord")
    required = {
        NETWORK_SURVIVABILITY,
        f"{NETWORK_OPERATOR_PREFIX}{record.network_operator}",
        f"{NETWORK_STUDY_ID_PREFIX}{record.network_study_id}",
        f"{NODE_REGION_ID_PREFIX}{record.node_region_id}",
        NODE_REGION_GRAIN_BINDING,
        f"ASSESSED_MANAGED_PEAK_MW:{record.assessed_managed_peak_mw}",
    }
    matches = [
        item for item in record.referenced_evidence
        if item.authority_level <= _SURVIVABILITY_AUTHORITY_MAX_LEVEL
        and item.truth_status in {"OBS", "DER"}
        and required.issubset(set(item.supports))
    ]
    if not matches:
        return NetworkSurvivabilityDecision(
            node_region_id=record.node_region_id,
            status=Q_NETWORK_SURVIVABILITY_UNRESOLVED,
            assessed_managed_peak_mw=None,
            evidence_status="Q",
            source_refs=tuple(dict.fromkeys(record.source_refs)),
            reason="managed peak/headroom/flex is not network survivability; no referenced claim-specific network-study authority",
        )
    evidence_status = "OBS" if all(item.truth_status == "OBS" for item in matches) else "DER"
    return NetworkSurvivabilityDecision(
        node_region_id=record.node_region_id,
        status=SURVIVABILITY_PROVEN,
        assessed_managed_peak_mw=record.assessed_managed_peak_mw,
        evidence_status=evidence_status,
        source_refs=tuple(dict.fromkeys(record.source_refs)),
        reason="referenced authoritative network study explicitly binds survivability to the exact node and assessed managed peak",
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
