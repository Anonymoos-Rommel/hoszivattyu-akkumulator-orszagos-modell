"""B10-P16 fail-closed national DSO node inventory contract.

Core rule:

    PUBLISHED HEADROOM NODE SET
    != COMPLETE DSO NODE INVENTORY
    != ELECTRICAL TOPOLOGY
    != ENTITY-TO-NODE MAPPING
    != LIMITING NODE

P1/P2 prove that exact source-native substation identities can exist in a
published headroom dataset. They do not prove that the publication enumerates
all substations or all electrically relevant nodes operated by that DSO.
"""

from __future__ import annotations

from dataclasses import dataclass


class B10NodeInventoryError(ValueError):
    """Raised when a node-identity or inventory-completeness claim is overstated."""


DSO_SUBSTATION = "DSO_SUBSTATION"
NODE_BEARING_SOURCE = "NODE_BEARING_SOURCE"
EXACT_NODE_IDENTITY = "EXACT_NODE_IDENTITY"
COMPLETE_OPERATOR_NODE_POPULATION = "COMPLETE_OPERATOR_NODE_POPULATION"

NODE_IDENTITY_PROVEN = "NODE_IDENTITY_PROVEN"
Q_NODE_IDENTITY_UNRESOLVED = "Q_NODE_IDENTITY_UNRESOLVED"
NODE_BEARING_SOURCE_BOUNDED = "NODE_BEARING_SOURCE_BOUNDED"
Q_NODE_SOURCE_UNRESOLVED = "Q_NODE_SOURCE_UNRESOLVED"
OPERATOR_NODE_INVENTORY_COMPLETE = "OPERATOR_NODE_INVENTORY_COMPLETE"
Q_INVENTORY_COMPLETENESS_UNPROVEN = "Q_INVENTORY_COMPLETENESS_UNPROVEN"
NATIONAL_NODE_INVENTORY_COMPLETE = "NATIONAL_NODE_INVENTORY_COMPLETE"
Q_NATIONAL_NODE_INVENTORY_INCOMPLETE = "Q_NATIONAL_NODE_INVENTORY_INCOMPLETE"

CURRENT_OPERATOR_IDS = (
    "ELMU",
    "EON_DDASZ",
    "EON_EDASZ",
    "MVM_DEMASZ",
    "MVM_EMASZ",
    "OPUS_TITASZ",
)

TRUTH_STATUSES = {"OBS", "DER", "Q"}


@dataclass(frozen=True)
class NodeInventoryEvidence:
    source_id: str
    authority_level: int
    truth_status: str
    supports: tuple[str, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.source_id, str) or not self.source_id.strip():
            raise B10NodeInventoryError("source_id is required")
        if self.authority_level not in {1, 2, 3, 4, 5}:
            raise B10NodeInventoryError("authority_level must be 1..5")
        if self.truth_status not in TRUTH_STATUSES:
            raise B10NodeInventoryError("truth_status must be OBS, DER or Q")
        if isinstance(self.supports, str):
            raise B10NodeInventoryError("supports must be a collection")
        if any(not isinstance(value, str) or not value.strip() for value in self.supports):
            raise B10NodeInventoryError("supports cannot contain blanks")


@dataclass(frozen=True)
class DsoNodeIdentityRecord:
    operator_id: str
    network_operator: str
    service_area_id: str
    node_id: str
    node_label: str
    source_native_key: str
    source_refs: tuple[str, ...]
    evidence: tuple[NodeInventoryEvidence, ...]
    node_kind: str = DSO_SUBSTATION

    def __post_init__(self) -> None:
        for name in (
            "operator_id",
            "network_operator",
            "service_area_id",
            "node_id",
            "node_label",
            "source_native_key",
        ):
            value = getattr(self, name)
            if not isinstance(value, str) or not value.strip():
                raise B10NodeInventoryError(f"{name} is required")
        if self.operator_id not in CURRENT_OPERATOR_IDS:
            raise B10NodeInventoryError("operator_id is not in the canonical six-DSO inventory")
        if self.service_area_id != f"{self.operator_id}:SERVICE_AREA":
            raise B10NodeInventoryError("service_area_id must match the canonical operator service-area identity")
        if self.node_kind != DSO_SUBSTATION:
            raise B10NodeInventoryError("P16 admits only DSO_SUBSTATION node identity")
        if not self.node_id.startswith(f"{self.operator_id}:"):
            raise B10NodeInventoryError("node_id must preserve operator-scoped source-native identity")
        if isinstance(self.source_refs, str) or not self.source_refs:
            raise B10NodeInventoryError("source_refs must be non-empty")
        if isinstance(self.evidence, str) or not self.evidence:
            raise B10NodeInventoryError("evidence must be non-empty")
        evidence_ids = {item.source_id for item in self.evidence}
        if not set(self.source_refs).issubset(evidence_ids):
            raise B10NodeInventoryError("source_refs must identify supplied evidence")

    @property
    def referenced_evidence(self) -> tuple[NodeInventoryEvidence, ...]:
        refs = set(self.source_refs)
        return tuple(item for item in self.evidence if item.source_id in refs)


@dataclass(frozen=True)
class DsoNodeIdentityDecision:
    operator_id: str
    service_area_id: str
    node_id: str | None
    node_kind: str
    status: str
    evidence_status: str
    source_refs: tuple[str, ...]
    reason: str

    def __post_init__(self) -> None:
        if self.node_kind != DSO_SUBSTATION:
            raise B10NodeInventoryError("node_kind must remain DSO_SUBSTATION")
        if self.status not in {NODE_IDENTITY_PROVEN, Q_NODE_IDENTITY_UNRESOLVED}:
            raise B10NodeInventoryError("invalid node identity status")
        if self.status == NODE_IDENTITY_PROVEN and self.node_id is None:
            raise B10NodeInventoryError("proven node identity requires node_id")
        if self.status != NODE_IDENTITY_PROVEN and self.node_id is not None:
            raise B10NodeInventoryError("Q node identity cannot expose authoritative node_id")


def classify_node_identity(record: DsoNodeIdentityRecord) -> DsoNodeIdentityDecision:
    """Prove one exact source-native node identity without claiming completeness."""

    if not isinstance(record, DsoNodeIdentityRecord):
        raise B10NodeInventoryError("record must be DsoNodeIdentityRecord")
    required = {
        EXACT_NODE_IDENTITY,
        f"OPERATOR_ID:{record.operator_id}",
        f"SERVICE_AREA_ID:{record.service_area_id}",
        f"NODE_ID:{record.node_id}",
        f"SOURCE_NATIVE_KEY:{record.source_native_key}",
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
        return DsoNodeIdentityDecision(
            record.operator_id,
            record.service_area_id,
            record.node_id,
            record.node_kind,
            NODE_IDENTITY_PROVEN,
            evidence_status,
            tuple(dict.fromkeys(record.source_refs)),
            "exact operator/service-area/node/source-native identity is bound by referenced authority",
        )
    return DsoNodeIdentityDecision(
        record.operator_id,
        record.service_area_id,
        None,
        record.node_kind,
        Q_NODE_IDENTITY_UNRESOLVED,
        "Q",
        tuple(dict.fromkeys(record.source_refs)),
        "referenced evidence does not prove the exact operator-scoped node identity",
    )


@dataclass(frozen=True)
class OperatorNodeSourceRecord:
    operator_id: str
    network_operator: str
    service_area_id: str
    source_refs: tuple[str, ...]
    evidence: tuple[NodeInventoryEvidence, ...]

    def __post_init__(self) -> None:
        if self.operator_id not in CURRENT_OPERATOR_IDS:
            raise B10NodeInventoryError("operator_id is not canonical")
        if not isinstance(self.network_operator, str) or not self.network_operator.strip():
            raise B10NodeInventoryError("network_operator is required")
        if self.service_area_id != f"{self.operator_id}:SERVICE_AREA":
            raise B10NodeInventoryError("service_area_id must match operator_id")
        if isinstance(self.source_refs, str):
            raise B10NodeInventoryError("source_refs must be a collection")
        if isinstance(self.evidence, str):
            raise B10NodeInventoryError("evidence must be a collection")
        evidence_ids = {item.source_id for item in self.evidence}
        if not set(self.source_refs).issubset(evidence_ids):
            raise B10NodeInventoryError("source_refs must identify supplied evidence")

    @property
    def referenced_evidence(self) -> tuple[NodeInventoryEvidence, ...]:
        refs = set(self.source_refs)
        return tuple(item for item in self.evidence if item.source_id in refs)


@dataclass(frozen=True)
class OperatorNodeSourceDecision:
    operator_id: str
    source_status: str
    inventory_status: str
    reason: str

    def __post_init__(self) -> None:
        if self.source_status not in {NODE_BEARING_SOURCE_BOUNDED, Q_NODE_SOURCE_UNRESOLVED}:
            raise B10NodeInventoryError("invalid node-source status")
        if self.inventory_status not in {OPERATOR_NODE_INVENTORY_COMPLETE, Q_INVENTORY_COMPLETENESS_UNPROVEN}:
            raise B10NodeInventoryError("invalid operator inventory status")
        if self.inventory_status == OPERATOR_NODE_INVENTORY_COMPLETE and self.source_status != NODE_BEARING_SOURCE_BOUNDED:
            raise B10NodeInventoryError("complete inventory requires a bounded node-bearing source")


def classify_operator_node_source(record: OperatorNodeSourceRecord) -> OperatorNodeSourceDecision:
    """Separate node-bearing source authority from inventory completeness."""

    if not isinstance(record, OperatorNodeSourceRecord):
        raise B10NodeInventoryError("record must be OperatorNodeSourceRecord")
    base = {
        f"OPERATOR_ID:{record.operator_id}",
        f"SERVICE_AREA_ID:{record.service_area_id}",
    }
    source_ok = any(
        item.authority_level <= 3
        and item.truth_status in {"OBS", "DER"}
        and (base | {NODE_BEARING_SOURCE}).issubset(set(item.supports))
        for item in record.referenced_evidence
    )
    complete_ok = any(
        item.authority_level <= 2
        and item.truth_status in {"OBS", "DER"}
        and (base | {COMPLETE_OPERATOR_NODE_POPULATION}).issubset(set(item.supports))
        for item in record.referenced_evidence
    )
    if not source_ok:
        return OperatorNodeSourceDecision(
            record.operator_id,
            Q_NODE_SOURCE_UNRESOLVED,
            Q_INVENTORY_COMPLETENESS_UNPROVEN,
            "no referenced current authority establishes a node-bearing source for this operator",
        )
    if complete_ok:
        return OperatorNodeSourceDecision(
            record.operator_id,
            NODE_BEARING_SOURCE_BOUNDED,
            OPERATOR_NODE_INVENTORY_COMPLETE,
            "node-bearing source and complete operator node population are separately proven",
        )
    return OperatorNodeSourceDecision(
        record.operator_id,
        NODE_BEARING_SOURCE_BOUNDED,
        Q_INVENTORY_COMPLETENESS_UNPROVEN,
        "a node-bearing source is bounded, but source scope does not prove complete operator node population",
    )


@dataclass(frozen=True)
class NationalNodeInventoryAssessment:
    status: str
    source_covered_operator_ids: tuple[str, ...]
    complete_operator_ids: tuple[str, ...]
    unresolved_source_operator_ids: tuple[str, ...]
    incomplete_operator_ids: tuple[str, ...]
    reason: str

    def __post_init__(self) -> None:
        if self.status not in {NATIONAL_NODE_INVENTORY_COMPLETE, Q_NATIONAL_NODE_INVENTORY_INCOMPLETE}:
            raise B10NodeInventoryError("invalid national node inventory status")
        if self.status == NATIONAL_NODE_INVENTORY_COMPLETE:
            if set(self.complete_operator_ids) != set(CURRENT_OPERATOR_IDS):
                raise B10NodeInventoryError("national completion requires all six operator inventories")
            if self.unresolved_source_operator_ids or self.incomplete_operator_ids:
                raise B10NodeInventoryError("complete national inventory cannot carry unresolved operators")


def assess_national_node_inventory(
    decisions: tuple[OperatorNodeSourceDecision, ...],
) -> NationalNodeInventoryAssessment:
    """Require exactly one decision for every current DSO before national completion."""

    if isinstance(decisions, str) or not decisions:
        raise B10NodeInventoryError("decisions must be a non-empty collection")
    by_operator: dict[str, OperatorNodeSourceDecision] = {}
    for decision in decisions:
        if not isinstance(decision, OperatorNodeSourceDecision):
            raise B10NodeInventoryError("all decisions must be OperatorNodeSourceDecision")
        if decision.operator_id in by_operator:
            raise B10NodeInventoryError("duplicate operator decision")
        by_operator[decision.operator_id] = decision
    unexpected = set(by_operator) - set(CURRENT_OPERATOR_IDS)
    if unexpected:
        raise B10NodeInventoryError("unexpected operator decision")

    source_covered = tuple(
        operator_id
        for operator_id in CURRENT_OPERATOR_IDS
        if operator_id in by_operator
        and by_operator[operator_id].source_status == NODE_BEARING_SOURCE_BOUNDED
    )
    complete = tuple(
        operator_id
        for operator_id in CURRENT_OPERATOR_IDS
        if operator_id in by_operator
        and by_operator[operator_id].inventory_status == OPERATOR_NODE_INVENTORY_COMPLETE
    )
    unresolved_source = tuple(
        operator_id
        for operator_id in CURRENT_OPERATOR_IDS
        if operator_id not in by_operator
        or by_operator[operator_id].source_status == Q_NODE_SOURCE_UNRESOLVED
    )
    incomplete = tuple(operator_id for operator_id in CURRENT_OPERATOR_IDS if operator_id not in complete)

    if len(complete) == len(CURRENT_OPERATOR_IDS):
        return NationalNodeInventoryAssessment(
            NATIONAL_NODE_INVENTORY_COMPLETE,
            source_covered,
            complete,
            (),
            (),
            "all six current DSO node populations are independently proven complete",
        )
    return NationalNodeInventoryAssessment(
        Q_NATIONAL_NODE_INVENTORY_INCOMPLETE,
        source_covered,
        complete,
        unresolved_source,
        incomplete,
        "national node inventory remains Q until every current DSO has a bounded node-bearing source and separately proven complete node population",
    )


def require_node_identity(decision: DsoNodeIdentityDecision) -> str:
    if not isinstance(decision, DsoNodeIdentityDecision):
        raise B10NodeInventoryError("decision must be DsoNodeIdentityDecision")
    if decision.status != NODE_IDENTITY_PROVEN or decision.node_id is None:
        raise B10NodeInventoryError("proven exact DSO node identity is required")
    return decision.node_id


__all__ = [
    "B10NodeInventoryError",
    "COMPLETE_OPERATOR_NODE_POPULATION",
    "CURRENT_OPERATOR_IDS",
    "DSO_SUBSTATION",
    "DsoNodeIdentityDecision",
    "DsoNodeIdentityRecord",
    "EXACT_NODE_IDENTITY",
    "NATIONAL_NODE_INVENTORY_COMPLETE",
    "NODE_BEARING_SOURCE",
    "NODE_BEARING_SOURCE_BOUNDED",
    "NODE_IDENTITY_PROVEN",
    "NodeInventoryEvidence",
    "OPERATOR_NODE_INVENTORY_COMPLETE",
    "OperatorNodeSourceDecision",
    "OperatorNodeSourceRecord",
    "Q_INVENTORY_COMPLETENESS_UNPROVEN",
    "Q_NATIONAL_NODE_INVENTORY_INCOMPLETE",
    "Q_NODE_IDENTITY_UNRESOLVED",
    "Q_NODE_SOURCE_UNRESOLVED",
    "NationalNodeInventoryAssessment",
    "assess_national_node_inventory",
    "classify_node_identity",
    "classify_operator_node_source",
    "require_node_identity",
]
