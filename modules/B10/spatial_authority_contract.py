"""Fail-closed B10-P8 DSO coverage and spatial-authority boundary.

B10-P8 keeps administrative geography, DSO service-area membership, exact
DSO-substation topology, household/building geography and B08 control-area
geography as separate truths.  It does not create a county/settlement-to-node
crosswalk and it does not permit proximity or confidence heuristics to mint an
electrical mapping.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import isfinite


class B10SpatialAuthorityError(ValueError):
    """Raised when spatial/electrical authority is ambiguous or overstated."""


ADMINISTRATIVE_LOCATION = "ADMINISTRATIVE_LOCATION"
DSO_SERVICE_AREA = "DSO_SERVICE_AREA"
DSO_SUBSTATION = "DSO_SUBSTATION"
HOUSEHOLD_BUILDING_LOCATION = "HOUSEHOLD_BUILDING_LOCATION"
ENTSOE_CONTROL_AREA = "ENTSOE_CONTROL_AREA"

SERVICE_AREA_PROVEN = "SERVICE_AREA_PROVEN"
Q_SERVICE_AREA_UNRESOLVED = "Q_SERVICE_AREA_UNRESOLVED"
EXACT_NODE_PROVEN = "EXACT_NODE_PROVEN"
Q_EXACT_NODE_UNRESOLVED = "Q_EXACT_NODE_UNRESOLVED"

DSO_SERVICE_AREA_MEMBERSHIP = "DSO_SERVICE_AREA_MEMBERSHIP"
EXACT_DSO_SUBSTATION_MAPPING = "EXACT_DSO_SUBSTATION_MAPPING"
AMBIGUOUS_OR_MULTI_SUPPLY = "AMBIGUOUS_OR_MULTI_SUPPLY"
ADMINISTRATIVE_ONLY = "ADMINISTRATIVE_ONLY"
PROXIMITY_ONLY = "PROXIMITY_ONLY"
CONTROL_AREA_ONLY = "CONTROL_AREA_ONLY"

ENTITY_ID_PREFIX = "ENTITY_ID:"
NETWORK_OPERATOR_PREFIX = "NETWORK_OPERATOR:"
SERVICE_AREA_ID_PREFIX = "SERVICE_AREA_ID:"
NODE_REGION_ID_PREFIX = "NODE_REGION_ID:"
NODE_REGION_GRAIN_BINDING = "NODE_REGION_GRAIN:DSO_SUBSTATION"

EVIDENCE_STATUSES = {"OBS", "DER", "Q"}
_SERVICE_AREA_AUTHORITY_MAX_LEVEL = 4
_EXACT_NODE_AUTHORITY_MAX_LEVEL = 3


@dataclass(frozen=True)
class SpatialAuthorityEvidence:
    source_id: str
    authority_level: int
    truth_status: str
    supports: tuple[str, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.source_id, str) or not self.source_id.strip():
            raise B10SpatialAuthorityError("source_id is required")
        if self.authority_level not in {1, 2, 3, 4, 5}:
            raise B10SpatialAuthorityError("authority_level must be 1..5")
        if self.truth_status not in EVIDENCE_STATUSES:
            raise B10SpatialAuthorityError("truth_status must be OBS, DER or Q")
        if isinstance(self.supports, str):
            raise B10SpatialAuthorityError("supports must be a collection")
        if any(not isinstance(item, str) or not item.strip() for item in self.supports):
            raise B10SpatialAuthorityError("supports cannot contain blank claims")


@dataclass(frozen=True)
class SpatialAuthorityRecord:
    entity_id: str
    network_operator: str
    service_area_id: str | None
    target_node_region_id: str | None
    source_refs: tuple[str, ...]
    evidence: tuple[SpatialAuthorityEvidence, ...]
    administrative_region_id: str | None = None
    household_location_id: str | None = None
    b08_region_id: str | None = None
    b08_region_scheme: str | None = None
    confidence_score: float | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.entity_id, str) or not self.entity_id.strip():
            raise B10SpatialAuthorityError("entity_id is required")
        if not isinstance(self.network_operator, str) or not self.network_operator.strip():
            raise B10SpatialAuthorityError("network_operator is required")
        for field_name in (
            "service_area_id",
            "target_node_region_id",
            "administrative_region_id",
            "household_location_id",
            "b08_region_id",
            "b08_region_scheme",
        ):
            value = getattr(self, field_name)
            if value is not None and (not isinstance(value, str) or not value.strip()):
                raise B10SpatialAuthorityError(f"{field_name} must be non-blank or None")
        if (self.b08_region_id is None) != (self.b08_region_scheme is None):
            raise B10SpatialAuthorityError("b08_region_id and b08_region_scheme must be supplied together")
        if isinstance(self.source_refs, str) or not self.source_refs:
            raise B10SpatialAuthorityError("source_refs must be non-empty")
        if isinstance(self.evidence, str) or not self.evidence:
            raise B10SpatialAuthorityError("evidence must be non-empty")
        evidence_ids = {item.source_id for item in self.evidence}
        if not set(self.source_refs).issubset(evidence_ids):
            raise B10SpatialAuthorityError("source_refs must identify supplied evidence")
        if self.confidence_score is not None:
            if isinstance(self.confidence_score, bool) or not isinstance(self.confidence_score, (int, float)):
                raise B10SpatialAuthorityError("confidence_score must be numeric or None")
            score = float(self.confidence_score)
            if not isfinite(score) or score < 0 or score > 1:
                raise B10SpatialAuthorityError("confidence_score must be within 0..1")
            object.__setattr__(self, "confidence_score", score)

    @property
    def referenced_evidence(self) -> tuple[SpatialAuthorityEvidence, ...]:
        refs = set(dict.fromkeys(self.source_refs))
        return tuple(item for item in self.evidence if item.source_id in refs)


@dataclass(frozen=True)
class SpatialAuthorityDecision:
    entity_id: str
    network_operator: str
    service_area_id: str | None
    service_area_status: str
    target_node_region_id: str | None
    target_node_region_scheme: str
    exact_node_status: str
    evidence_status: str
    source_refs: tuple[str, ...]
    reason: str


def _supports(record: SpatialAuthorityRecord, claim: str, *, max_authority_level: int) -> bool:
    required = {
        claim,
        f"{ENTITY_ID_PREFIX}{record.entity_id}",
        f"{NETWORK_OPERATOR_PREFIX}{record.network_operator}",
    }
    return any(
        item.authority_level <= max_authority_level
        and item.truth_status in {"OBS", "DER"}
        and required.issubset(set(item.supports))
        for item in record.referenced_evidence
    )


def _service_area_proven(record: SpatialAuthorityRecord) -> bool:
    if record.service_area_id is None:
        return False
    required = {
        DSO_SERVICE_AREA_MEMBERSHIP,
        f"{ENTITY_ID_PREFIX}{record.entity_id}",
        f"{NETWORK_OPERATOR_PREFIX}{record.network_operator}",
        f"{SERVICE_AREA_ID_PREFIX}{record.service_area_id}",
    }
    return any(
        item.authority_level <= _SERVICE_AREA_AUTHORITY_MAX_LEVEL
        and item.truth_status in {"OBS", "DER"}
        and required.issubset(set(item.supports))
        for item in record.referenced_evidence
    )


def _exact_node_proven(record: SpatialAuthorityRecord) -> bool:
    if record.target_node_region_id is None:
        return False
    required = {
        EXACT_DSO_SUBSTATION_MAPPING,
        f"{ENTITY_ID_PREFIX}{record.entity_id}",
        f"{NETWORK_OPERATOR_PREFIX}{record.network_operator}",
        f"{NODE_REGION_ID_PREFIX}{record.target_node_region_id}",
        NODE_REGION_GRAIN_BINDING,
    }
    return any(
        item.authority_level <= _EXACT_NODE_AUTHORITY_MAX_LEVEL
        and item.truth_status in {"OBS", "DER"}
        and required.issubset(set(item.supports))
        for item in record.referenced_evidence
    )


def classify_spatial_authority(record: SpatialAuthorityRecord) -> SpatialAuthorityDecision:
    """Classify service-area and exact-node authority without inferring topology.

    Administrative, postal/municipal, household/building and ENTSO-E control-area
    geography are context only.  Service-area membership cannot mint an exact
    supplying substation.  Exact-node status requires referenced claim-specific
    electrical/network authority bound to the entity, operator and exact
    DSO_SUBSTATION region id.
    """

    if not isinstance(record, SpatialAuthorityRecord):
        raise B10SpatialAuthorityError("record must be SpatialAuthorityRecord")

    referenced = record.referenced_evidence
    ambiguous = any(
        item.truth_status in {"OBS", "DER"} and AMBIGUOUS_OR_MULTI_SUPPLY in item.supports
        for item in referenced
    )
    service_area = _service_area_proven(record)
    exact_node = _exact_node_proven(record)

    if exact_node and ambiguous:
        exact_node = False

    service_area_status = SERVICE_AREA_PROVEN if service_area else Q_SERVICE_AREA_UNRESOLVED
    exact_node_status = EXACT_NODE_PROVEN if exact_node else Q_EXACT_NODE_UNRESOLVED

    if exact_node:
        reason = "referenced claim-specific electrical authority binds the entity/operator to the exact DSO_SUBSTATION node"
    elif ambiguous:
        reason = "referenced evidence identifies ambiguous or multi-supply topology; exact node remains Q"
    elif service_area:
        reason = "DSO service-area membership is proven but does not identify the exact supplying substation"
    else:
        reason = "administrative/control-area/proximity context does not prove DSO service area or exact electrical topology"

    statuses = {item.truth_status for item in referenced}
    if exact_node_status == Q_EXACT_NODE_UNRESOLVED or service_area_status == Q_SERVICE_AREA_UNRESOLVED or "Q" in statuses:
        evidence_status = "Q"
    elif statuses == {"OBS"}:
        evidence_status = "OBS"
    else:
        evidence_status = "DER"

    return SpatialAuthorityDecision(
        entity_id=record.entity_id,
        network_operator=record.network_operator,
        service_area_id=record.service_area_id if service_area else None,
        service_area_status=service_area_status,
        target_node_region_id=record.target_node_region_id if exact_node else None,
        target_node_region_scheme=DSO_SUBSTATION,
        exact_node_status=exact_node_status,
        evidence_status=evidence_status,
        source_refs=tuple(dict.fromkeys(record.source_refs)),
        reason=reason,
    )


def require_exact_dso_substation_mapping(decision: SpatialAuthorityDecision) -> str:
    """Authorize a P1/P5 node handoff only after exact-node authority is proven."""

    if not isinstance(decision, SpatialAuthorityDecision):
        raise B10SpatialAuthorityError("decision must be SpatialAuthorityDecision")
    if decision.exact_node_status != EXACT_NODE_PROVEN or decision.target_node_region_id is None:
        raise B10SpatialAuthorityError("exact DSO_SUBSTATION mapping authority is required before headroom/reinforcement handoff")
    return decision.target_node_region_id


def assert_context_not_topology_authority(record: SpatialAuthorityRecord) -> None:
    """Regression guard for administrative/control-area/proximity-only evidence."""

    decision = classify_spatial_authority(record)
    topology_claimed = any(EXACT_DSO_SUBSTATION_MAPPING in item.supports for item in record.referenced_evidence)
    if not topology_claimed and decision.exact_node_status != Q_EXACT_NODE_UNRESOLVED:
        raise B10SpatialAuthorityError("context geography cannot mint exact electrical topology")


__all__ = [
    "ADMINISTRATIVE_LOCATION",
    "ADMINISTRATIVE_ONLY",
    "AMBIGUOUS_OR_MULTI_SUPPLY",
    "B10SpatialAuthorityError",
    "CONTROL_AREA_ONLY",
    "DSO_SERVICE_AREA",
    "DSO_SERVICE_AREA_MEMBERSHIP",
    "DSO_SUBSTATION",
    "ENTSOE_CONTROL_AREA",
    "EXACT_DSO_SUBSTATION_MAPPING",
    "EXACT_NODE_PROVEN",
    "HOUSEHOLD_BUILDING_LOCATION",
    "PROXIMITY_ONLY",
    "Q_EXACT_NODE_UNRESOLVED",
    "Q_SERVICE_AREA_UNRESOLVED",
    "SERVICE_AREA_PROVEN",
    "SpatialAuthorityDecision",
    "SpatialAuthorityEvidence",
    "SpatialAuthorityRecord",
    "assert_context_not_topology_authority",
    "classify_spatial_authority",
    "require_exact_dso_substation_mapping",
]
