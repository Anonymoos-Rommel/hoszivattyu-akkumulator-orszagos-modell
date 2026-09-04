"""B10-P25 fail-closed topology endpoint typing and DSO-node link gate.

Core rules:

    EDGE ENDPOINT TOKEN != DSO SUBSTATION NODE
    DSO SUBSTATION ENDPOINT != CANONICAL DSO NODE LINK
    TSO SUBSTATION != DSO NODE INVENTORY
    NAMED LINE != SUBSTATION
    TYPED ENDPOINTS != COMPLETE TOPOLOGY != CONNECTED COMPONENT

P25 types the heterogeneous endpoint tokens introduced by P24. Endpoint identity
and linkage into the canonical DSO node layer are separate claims.
"""

from __future__ import annotations

from dataclasses import dataclass


class B10TopologyEndpointError(ValueError):
    """Raised when topology endpoint identity or node linkage is overstated."""


TOPOLOGY_ENDPOINT = "TOPOLOGY_ENDPOINT"
CANONICAL_DSO_NODE_LINK = "CANONICAL_DSO_NODE_LINK"

DSO_SUBSTATION = "DSO_SUBSTATION"
TSO_SUBSTATION = "TSO_SUBSTATION"
NAMED_LINE = "NAMED_LINE"
ENDPOINT_KINDS = {DSO_SUBSTATION, TSO_SUBSTATION, NAMED_LINE}

TOPOLOGY_ENDPOINT_PROVEN = "TOPOLOGY_ENDPOINT_PROVEN"
Q_TOPOLOGY_ENDPOINT_UNRESOLVED = "Q_TOPOLOGY_ENDPOINT_UNRESOLVED"

CANONICAL_DSO_NODE_LINK_PROVEN = "CANONICAL_DSO_NODE_LINK_PROVEN"
Q_CANONICAL_DSO_NODE_LINK_UNRESOLVED = "Q_CANONICAL_DSO_NODE_LINK_UNRESOLVED"
CANONICAL_DSO_NODE_LINK_NOT_APPLICABLE = "CANONICAL_DSO_NODE_LINK_NOT_APPLICABLE"

TRUTH_STATUSES = {"OBS", "DER", "Q"}


@dataclass(frozen=True)
class TopologyEndpointEvidence:
    source_id: str
    authority_level: int
    truth_status: str
    supports: tuple[str, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.source_id, str) or not self.source_id.strip():
            raise B10TopologyEndpointError("source_id is required")
        if self.authority_level not in {1, 2, 3, 4, 5}:
            raise B10TopologyEndpointError("authority_level must be 1..5")
        if self.truth_status not in TRUTH_STATUSES:
            raise B10TopologyEndpointError("truth_status must be OBS, DER or Q")
        if isinstance(self.supports, str):
            raise B10TopologyEndpointError("supports must be a collection")
        if any(not isinstance(value, str) or not value.strip() for value in self.supports):
            raise B10TopologyEndpointError("supports cannot contain blanks")


@dataclass(frozen=True)
class TopologyEndpointRecord:
    endpoint_id: str
    endpoint_kind: str
    operator_context_id: str
    scope_id: str
    edge_refs: tuple[str, ...]
    source_refs: tuple[str, ...]
    evidence: tuple[TopologyEndpointEvidence, ...]
    canonical_dso_node_ref: str | None = None

    def __post_init__(self) -> None:
        for name in ("endpoint_id", "operator_context_id", "scope_id"):
            value = getattr(self, name)
            if not isinstance(value, str) or not value.strip():
                raise B10TopologyEndpointError(f"{name} is required")
        if self.endpoint_kind not in ENDPOINT_KINDS:
            raise B10TopologyEndpointError("unsupported endpoint_kind")
        if isinstance(self.edge_refs, str) or not self.edge_refs:
            raise B10TopologyEndpointError("edge_refs must be non-empty")
        if any(not isinstance(value, str) or not value.strip() for value in self.edge_refs):
            raise B10TopologyEndpointError("edge_refs cannot contain blanks")
        if len(set(self.edge_refs)) != len(self.edge_refs):
            raise B10TopologyEndpointError("edge_refs cannot contain duplicates")
        if isinstance(self.source_refs, str) or not self.source_refs:
            raise B10TopologyEndpointError("source_refs must be non-empty")
        if isinstance(self.evidence, str) or not self.evidence:
            raise B10TopologyEndpointError("evidence must be non-empty")
        evidence_ids = {item.source_id for item in self.evidence}
        if not set(self.source_refs).issubset(evidence_ids):
            raise B10TopologyEndpointError("source_refs must identify supplied evidence")
        if self.canonical_dso_node_ref is not None:
            if not isinstance(self.canonical_dso_node_ref, str) or not self.canonical_dso_node_ref.strip():
                raise B10TopologyEndpointError("canonical_dso_node_ref cannot be blank")
            if self.endpoint_kind != DSO_SUBSTATION:
                raise B10TopologyEndpointError(
                    "only DSO_SUBSTATION endpoints can reference the canonical DSO node layer"
                )

    @property
    def referenced_evidence(self) -> tuple[TopologyEndpointEvidence, ...]:
        refs = set(self.source_refs)
        return tuple(item for item in self.evidence if item.source_id in refs)


@dataclass(frozen=True)
class TopologyEndpointDecision:
    endpoint_id: str
    endpoint_kind: str
    operator_context_id: str
    scope_id: str
    edge_refs: tuple[str, ...]
    status: str
    evidence_status: str
    node_link_status: str
    canonical_dso_node_ref: str | None
    source_refs: tuple[str, ...]
    reason: str

    def __post_init__(self) -> None:
        if self.status not in {TOPOLOGY_ENDPOINT_PROVEN, Q_TOPOLOGY_ENDPOINT_UNRESOLVED}:
            raise B10TopologyEndpointError("invalid topology endpoint status")
        if self.node_link_status not in {
            CANONICAL_DSO_NODE_LINK_PROVEN,
            Q_CANONICAL_DSO_NODE_LINK_UNRESOLVED,
            CANONICAL_DSO_NODE_LINK_NOT_APPLICABLE,
        }:
            raise B10TopologyEndpointError("invalid canonical DSO node-link status")
        if self.node_link_status == CANONICAL_DSO_NODE_LINK_PROVEN:
            if self.endpoint_kind != DSO_SUBSTATION or self.canonical_dso_node_ref is None:
                raise B10TopologyEndpointError("proven DSO node link requires DSO endpoint and node ref")
        elif self.canonical_dso_node_ref is not None:
            raise B10TopologyEndpointError("unproven or inapplicable DSO node link must withhold node ref")
        if self.endpoint_kind != DSO_SUBSTATION:
            if self.node_link_status != CANONICAL_DSO_NODE_LINK_NOT_APPLICABLE:
                raise B10TopologyEndpointError("non-DSO endpoint cannot carry a DSO node-link claim")


def classify_topology_endpoint(record: TopologyEndpointRecord) -> TopologyEndpointDecision:
    """Type one edge endpoint and independently assess canonical DSO-node linkage."""

    if not isinstance(record, TopologyEndpointRecord):
        raise B10TopologyEndpointError("record must be TopologyEndpointRecord")

    identity_required = {
        TOPOLOGY_ENDPOINT,
        f"ENDPOINT_ID:{record.endpoint_id}",
        f"ENDPOINT_KIND:{record.endpoint_kind}",
        f"OPERATOR_CONTEXT_ID:{record.operator_context_id}",
        f"SCOPE_ID:{record.scope_id}",
        *(f"EDGE_REF:{edge_ref}" for edge_ref in record.edge_refs),
    }
    identity_evidence = tuple(
        item
        for item in record.referenced_evidence
        if item.authority_level <= 3
        and item.truth_status in {"OBS", "DER"}
        and identity_required.issubset(set(item.supports))
    )

    if not identity_evidence:
        node_link_status = (
            Q_CANONICAL_DSO_NODE_LINK_UNRESOLVED
            if record.endpoint_kind == DSO_SUBSTATION
            else CANONICAL_DSO_NODE_LINK_NOT_APPLICABLE
        )
        return TopologyEndpointDecision(
            record.endpoint_id,
            record.endpoint_kind,
            record.operator_context_id,
            record.scope_id,
            record.edge_refs,
            Q_TOPOLOGY_ENDPOINT_UNRESOLVED,
            "Q",
            node_link_status,
            None,
            tuple(dict.fromkeys(record.source_refs)),
            "referenced evidence does not explicitly bind the exact endpoint identity and type",
        )

    statuses = {item.truth_status for item in identity_evidence}
    evidence_status = "OBS" if statuses == {"OBS"} else "DER"

    if record.endpoint_kind != DSO_SUBSTATION:
        return TopologyEndpointDecision(
            record.endpoint_id,
            record.endpoint_kind,
            record.operator_context_id,
            record.scope_id,
            record.edge_refs,
            TOPOLOGY_ENDPOINT_PROVEN,
            evidence_status,
            CANONICAL_DSO_NODE_LINK_NOT_APPLICABLE,
            None,
            tuple(dict.fromkeys(record.source_refs)),
            "endpoint identity/type is proven; canonical DSO node linkage is not applicable",
        )

    if record.canonical_dso_node_ref is not None:
        link_required = {
            CANONICAL_DSO_NODE_LINK,
            f"ENDPOINT_ID:{record.endpoint_id}",
            f"CANONICAL_DSO_NODE_REF:{record.canonical_dso_node_ref}",
        }
        link_ok = any(
            item.authority_level <= 3
            and item.truth_status in {"OBS", "DER"}
            and link_required.issubset(set(item.supports))
            for item in record.referenced_evidence
        )
        if link_ok:
            return TopologyEndpointDecision(
                record.endpoint_id,
                record.endpoint_kind,
                record.operator_context_id,
                record.scope_id,
                record.edge_refs,
                TOPOLOGY_ENDPOINT_PROVEN,
                evidence_status,
                CANONICAL_DSO_NODE_LINK_PROVEN,
                record.canonical_dso_node_ref,
                tuple(dict.fromkeys(record.source_refs)),
                "DSO substation endpoint identity and canonical node linkage are separately proven",
            )

    return TopologyEndpointDecision(
        record.endpoint_id,
        record.endpoint_kind,
        record.operator_context_id,
        record.scope_id,
        record.edge_refs,
        TOPOLOGY_ENDPOINT_PROVEN,
        evidence_status,
        Q_CANONICAL_DSO_NODE_LINK_UNRESOLVED,
        None,
        tuple(dict.fromkeys(record.source_refs)),
        "DSO substation endpoint identity is proven but canonical DSO node linkage remains unresolved",
    )


def require_topology_endpoint(decision: TopologyEndpointDecision) -> str:
    if not isinstance(decision, TopologyEndpointDecision):
        raise B10TopologyEndpointError("decision must be TopologyEndpointDecision")
    if decision.status != TOPOLOGY_ENDPOINT_PROVEN:
        raise B10TopologyEndpointError("proven topology endpoint identity is required")
    return decision.endpoint_id


def require_canonical_dso_node_link(decision: TopologyEndpointDecision) -> str:
    if not isinstance(decision, TopologyEndpointDecision):
        raise B10TopologyEndpointError("decision must be TopologyEndpointDecision")
    if (
        decision.node_link_status != CANONICAL_DSO_NODE_LINK_PROVEN
        or decision.canonical_dso_node_ref is None
    ):
        raise B10TopologyEndpointError("proven canonical DSO node linkage is required")
    return decision.canonical_dso_node_ref


__all__ = [
    "B10TopologyEndpointError",
    "CANONICAL_DSO_NODE_LINK",
    "CANONICAL_DSO_NODE_LINK_NOT_APPLICABLE",
    "CANONICAL_DSO_NODE_LINK_PROVEN",
    "DSO_SUBSTATION",
    "ENDPOINT_KINDS",
    "NAMED_LINE",
    "Q_CANONICAL_DSO_NODE_LINK_UNRESOLVED",
    "Q_TOPOLOGY_ENDPOINT_UNRESOLVED",
    "TOPOLOGY_ENDPOINT",
    "TOPOLOGY_ENDPOINT_PROVEN",
    "TSO_SUBSTATION",
    "TopologyEndpointDecision",
    "TopologyEndpointEvidence",
    "TopologyEndpointRecord",
    "classify_topology_endpoint",
    "require_canonical_dso_node_link",
    "require_topology_endpoint",
]
