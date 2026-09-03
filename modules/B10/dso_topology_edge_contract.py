"""B10-P24 fail-closed bounded DSO topology-edge evidence contract.

Core rule:

    PUBLIC PROJECT FACT CAN PROVE BOUNDED TOPOLOGY EDGE
    != COMPLETE DSO TOPOLOGY
    != POWER FLOW DIRECTION
    != THERMAL CAPACITY
    != HEADROOM
    != LIMITING NODE
    != PROGRAMME REINFORCEMENT REQUIREMENT
    != PROGRAMME-INCREMENTAL CAPEX

P24 admits only source-explicit physical network relations. Geographic proximity,
settlement-name coincidence and missing-edge inference are not topology evidence.
"""

from __future__ import annotations

from dataclasses import dataclass


class B10TopologyEdgeError(ValueError):
    """Raised when a bounded topology-edge claim is overstated."""


TOPOLOGY_EDGE = "TOPOLOGY_EDGE"
TOPOLOGY_EDGE_PROVEN = "TOPOLOGY_EDGE_PROVEN"
Q_TOPOLOGY_EDGE_UNRESOLVED = "Q_TOPOLOGY_EDGE_UNRESOLVED"

NAMED_LINE_SEGMENT = "NAMED_LINE_SEGMENT"
SUBSTATION_INSERTION_INTO_NAMED_LINE = "SUBSTATION_INSERTION_INTO_NAMED_LINE"
SUBSTATION_TO_SUBSTATION_LINE = "SUBSTATION_TO_SUBSTATION_LINE"

EDGE_KINDS = {
    NAMED_LINE_SEGMENT,
    SUBSTATION_INSERTION_INTO_NAMED_LINE,
    SUBSTATION_TO_SUBSTATION_LINE,
}
TRUTH_STATUSES = {"OBS", "DER", "Q"}


@dataclass(frozen=True)
class TopologyEdgeEvidence:
    source_id: str
    authority_level: int
    truth_status: str
    supports: tuple[str, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.source_id, str) or not self.source_id.strip():
            raise B10TopologyEdgeError("source_id is required")
        if self.authority_level not in {1, 2, 3, 4, 5}:
            raise B10TopologyEdgeError("authority_level must be 1..5")
        if self.truth_status not in TRUTH_STATUSES:
            raise B10TopologyEdgeError("truth_status must be OBS, DER or Q")
        if isinstance(self.supports, str):
            raise B10TopologyEdgeError("supports must be a collection")
        if any(not isinstance(value, str) or not value.strip() for value in self.supports):
            raise B10TopologyEdgeError("supports cannot contain blanks")


@dataclass(frozen=True)
class DsoTopologyEdgeRecord:
    operator_id: str
    service_area_id: str
    edge_id: str
    endpoint_a: str
    endpoint_b: str
    edge_kind: str
    voltage_kv: int
    source_refs: tuple[str, ...]
    evidence: tuple[TopologyEdgeEvidence, ...]

    def __post_init__(self) -> None:
        for name in (
            "operator_id",
            "service_area_id",
            "edge_id",
            "endpoint_a",
            "endpoint_b",
        ):
            value = getattr(self, name)
            if not isinstance(value, str) or not value.strip():
                raise B10TopologyEdgeError(f"{name} is required")
        if self.service_area_id != f"{self.operator_id}:SERVICE_AREA":
            raise B10TopologyEdgeError("service_area_id must match operator_id")
        if not self.edge_id.startswith(f"{self.operator_id}:"):
            raise B10TopologyEdgeError("edge_id must be operator-scoped")
        if self.endpoint_a == self.endpoint_b:
            raise B10TopologyEdgeError("topology edge endpoints must differ")
        if self.edge_kind not in EDGE_KINDS:
            raise B10TopologyEdgeError("unsupported edge_kind")
        if isinstance(self.voltage_kv, bool) or not isinstance(self.voltage_kv, int):
            raise B10TopologyEdgeError("voltage_kv must be an integer")
        if self.voltage_kv <= 0:
            raise B10TopologyEdgeError("voltage_kv must be positive")
        if isinstance(self.source_refs, str) or not self.source_refs:
            raise B10TopologyEdgeError("source_refs must be non-empty")
        if isinstance(self.evidence, str) or not self.evidence:
            raise B10TopologyEdgeError("evidence must be non-empty")
        evidence_ids = {item.source_id for item in self.evidence}
        if not set(self.source_refs).issubset(evidence_ids):
            raise B10TopologyEdgeError("source_refs must identify supplied evidence")

    @property
    def referenced_evidence(self) -> tuple[TopologyEdgeEvidence, ...]:
        refs = set(self.source_refs)
        return tuple(item for item in self.evidence if item.source_id in refs)


@dataclass(frozen=True)
class DsoTopologyEdgeDecision:
    operator_id: str
    service_area_id: str
    edge_id: str
    endpoint_a: str | None
    endpoint_b: str | None
    edge_kind: str
    voltage_kv: int | None
    evidence_status: str
    status: str
    source_refs: tuple[str, ...]
    reason: str

    def __post_init__(self) -> None:
        if self.status not in {TOPOLOGY_EDGE_PROVEN, Q_TOPOLOGY_EDGE_UNRESOLVED}:
            raise B10TopologyEdgeError("invalid topology-edge status")
        if self.status == TOPOLOGY_EDGE_PROVEN:
            if self.endpoint_a is None or self.endpoint_b is None or self.voltage_kv is None:
                raise B10TopologyEdgeError("proven topology edge requires exact endpoints and voltage")
        else:
            if self.endpoint_a is not None or self.endpoint_b is not None or self.voltage_kv is not None:
                raise B10TopologyEdgeError("Q topology edge cannot expose authoritative endpoints or voltage")


def classify_topology_edge(record: DsoTopologyEdgeRecord) -> DsoTopologyEdgeDecision:
    """Prove one bounded source-explicit physical topology relation."""

    if not isinstance(record, DsoTopologyEdgeRecord):
        raise B10TopologyEdgeError("record must be DsoTopologyEdgeRecord")
    required = {
        TOPOLOGY_EDGE,
        f"OPERATOR_ID:{record.operator_id}",
        f"SERVICE_AREA_ID:{record.service_area_id}",
        f"EDGE_ID:{record.edge_id}",
        f"ENDPOINT_A:{record.endpoint_a}",
        f"ENDPOINT_B:{record.endpoint_b}",
        f"EDGE_KIND:{record.edge_kind}",
        f"VOLTAGE_KV:{record.voltage_kv}",
    }
    qualifying = tuple(
        item
        for item in record.referenced_evidence
        if item.authority_level <= 3
        and item.truth_status in {"OBS", "DER"}
        and required.issubset(set(item.supports))
    )
    if qualifying:
        statuses = {item.truth_status for item in qualifying}
        evidence_status = "OBS" if statuses == {"OBS"} else "DER"
        return DsoTopologyEdgeDecision(
            record.operator_id,
            record.service_area_id,
            record.edge_id,
            record.endpoint_a,
            record.endpoint_b,
            record.edge_kind,
            record.voltage_kv,
            evidence_status,
            TOPOLOGY_EDGE_PROVEN,
            tuple(dict.fromkeys(record.source_refs)),
            "referenced authority explicitly binds the bounded physical network relation",
        )
    return DsoTopologyEdgeDecision(
        record.operator_id,
        record.service_area_id,
        record.edge_id,
        None,
        None,
        record.edge_kind,
        None,
        "Q",
        Q_TOPOLOGY_EDGE_UNRESOLVED,
        tuple(dict.fromkeys(record.source_refs)),
        "referenced evidence does not explicitly bind the exact topology relation",
    )


def require_topology_edge(decision: DsoTopologyEdgeDecision) -> tuple[str, str]:
    """Return exact proven endpoints or fail closed."""

    if not isinstance(decision, DsoTopologyEdgeDecision):
        raise B10TopologyEdgeError("decision must be DsoTopologyEdgeDecision")
    if (
        decision.status != TOPOLOGY_EDGE_PROVEN
        or decision.endpoint_a is None
        or decision.endpoint_b is None
    ):
        raise B10TopologyEdgeError("proven bounded topology edge is required")
    return decision.endpoint_a, decision.endpoint_b


__all__ = [
    "B10TopologyEdgeError",
    "DsoTopologyEdgeDecision",
    "DsoTopologyEdgeRecord",
    "EDGE_KINDS",
    "NAMED_LINE_SEGMENT",
    "Q_TOPOLOGY_EDGE_UNRESOLVED",
    "SUBSTATION_INSERTION_INTO_NAMED_LINE",
    "SUBSTATION_TO_SUBSTATION_LINE",
    "TOPOLOGY_EDGE",
    "TOPOLOGY_EDGE_PROVEN",
    "TopologyEdgeEvidence",
    "classify_topology_edge",
    "require_topology_edge",
]
