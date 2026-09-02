"""Fail-closed B10-P7 transmission/distribution authority contract.

The contract separates network-layer classification from voltage, ownership,
project attribution, headroom and programme causality.  A voltage level or an
operator name alone cannot mint a TRANSMISSION or DISTRIBUTION claim.
"""

from __future__ import annotations

from dataclasses import dataclass


class B10NetworkLayerAuthorityError(ValueError):
    """Raised when network-layer authority is ambiguous or overstated."""


TRANSMISSION = "TRANSMISSION"
DISTRIBUTION = "DISTRIBUTION"
COORDINATED_TSO_DSO = "COORDINATED_TSO_DSO"
Q_UNRESOLVED_NETWORK_LAYER = "Q_UNRESOLVED_NETWORK_LAYER"

NETWORK_LAYER_STATUSES = {
    TRANSMISSION,
    DISTRIBUTION,
    COORDINATED_TSO_DSO,
    Q_UNRESOLVED_NETWORK_LAYER,
}
EVIDENCE_STATUSES = {"OBS", "DER", "Q"}

TRANSMISSION_LAYER = "TRANSMISSION_LAYER"
DISTRIBUTION_LAYER = "DISTRIBUTION_LAYER"
TSO_DSO_INTERFACE = "TSO_DSO_INTERFACE"
PROJECT_ID_PREFIX = "PROJECT_ID:"
NETWORK_OPERATOR_PREFIX = "NETWORK_OPERATOR:"


@dataclass(frozen=True)
class NetworkLayerEvidence:
    source_id: str
    authority_level: int
    truth_status: str
    supports: tuple[str, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.source_id, str) or not self.source_id.strip():
            raise B10NetworkLayerAuthorityError("source_id is required")
        if self.authority_level not in {1, 2, 3, 4, 5}:
            raise B10NetworkLayerAuthorityError("authority_level must be 1..5")
        if self.truth_status not in EVIDENCE_STATUSES:
            raise B10NetworkLayerAuthorityError("truth_status must be OBS, DER or Q")
        if isinstance(self.supports, str):
            raise B10NetworkLayerAuthorityError("supports must be a collection")


@dataclass(frozen=True)
class NetworkLayerRecord:
    project_id: str
    network_operator: str
    voltage_kv: float | None
    source_refs: tuple[str, ...]
    evidence: tuple[NetworkLayerEvidence, ...]
    claimed_layer: str | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.project_id, str) or not self.project_id.strip():
            raise B10NetworkLayerAuthorityError("project_id is required")
        if not isinstance(self.network_operator, str) or not self.network_operator.strip():
            raise B10NetworkLayerAuthorityError("network_operator is required")
        if self.voltage_kv is not None:
            if isinstance(self.voltage_kv, bool) or not isinstance(self.voltage_kv, (int, float)):
                raise B10NetworkLayerAuthorityError("voltage_kv must be numeric or None")
            if self.voltage_kv <= 0:
                raise B10NetworkLayerAuthorityError("voltage_kv must be positive")
        if isinstance(self.source_refs, str) or not self.source_refs:
            raise B10NetworkLayerAuthorityError("source_refs must be non-empty")
        if isinstance(self.evidence, str) or not self.evidence:
            raise B10NetworkLayerAuthorityError("evidence must be non-empty")
        evidence_ids = {item.source_id for item in self.evidence}
        if not set(self.source_refs).issubset(evidence_ids):
            raise B10NetworkLayerAuthorityError("source_refs must identify supplied evidence")
        if self.claimed_layer is not None and self.claimed_layer not in NETWORK_LAYER_STATUSES:
            raise B10NetworkLayerAuthorityError("invalid claimed_layer")

    @property
    def referenced_evidence(self) -> tuple[NetworkLayerEvidence, ...]:
        refs = set(dict.fromkeys(self.source_refs))
        return tuple(item for item in self.evidence if item.source_id in refs)


@dataclass(frozen=True)
class NetworkLayerDecision:
    project_id: str
    network_operator: str
    voltage_kv: float | None
    network_layer: str
    evidence_status: str
    source_refs: tuple[str, ...]
    reason: str


def _bound_supports(record: NetworkLayerRecord, claim: str) -> bool:
    required = {
        claim,
        f"{PROJECT_ID_PREFIX}{record.project_id}",
        f"{NETWORK_OPERATOR_PREFIX}{record.network_operator}",
    }
    return any(
        item.authority_level <= 4
        and item.truth_status in {"OBS", "DER"}
        and required.issubset(set(item.supports))
        for item in record.referenced_evidence
    )


def classify_network_layer(record: NetworkLayerRecord) -> NetworkLayerDecision:
    """Classify layer only from referenced, claim-specific authority.

    Voltage is preserved as context but is never itself a classification rule.
    Evidence asserting both layers requires an explicit TSO_DSO_INTERFACE claim;
    otherwise the result fails closed to Q.
    """

    if not isinstance(record, NetworkLayerRecord):
        raise B10NetworkLayerAuthorityError("record must be NetworkLayerRecord")

    transmission = _bound_supports(record, TRANSMISSION_LAYER)
    distribution = _bound_supports(record, DISTRIBUTION_LAYER)
    interface = _bound_supports(record, TSO_DSO_INTERFACE)

    if transmission and distribution:
        if not interface:
            decision = Q_UNRESOLVED_NETWORK_LAYER
            reason = "both layer claims exist without explicit TSO/DSO interface authority"
        else:
            decision = COORDINATED_TSO_DSO
            reason = "referenced authority explicitly binds both layers and their interface"
    elif transmission:
        if interface:
            decision = Q_UNRESOLVED_NETWORK_LAYER
            reason = "interface claim cannot substitute for missing distribution-layer authority"
        else:
            decision = TRANSMISSION
            reason = "referenced authority explicitly binds the project/operator to transmission"
    elif distribution:
        if interface:
            decision = Q_UNRESOLVED_NETWORK_LAYER
            reason = "interface claim cannot substitute for missing transmission-layer authority"
        else:
            decision = DISTRIBUTION
            reason = "referenced authority explicitly binds the project/operator to distribution"
    else:
        decision = Q_UNRESOLVED_NETWORK_LAYER
        reason = "no referenced claim-specific network-layer authority"

    statuses = {item.truth_status for item in record.referenced_evidence}
    if decision == Q_UNRESOLVED_NETWORK_LAYER or "Q" in statuses:
        evidence_status = "Q"
    elif statuses == {"OBS"}:
        evidence_status = "OBS"
    else:
        evidence_status = "DER"

    if record.claimed_layer is not None and record.claimed_layer != decision:
        raise B10NetworkLayerAuthorityError(
            f"claimed_layer {record.claimed_layer!r} conflicts with evidence decision {decision!r}"
        )

    return NetworkLayerDecision(
        project_id=record.project_id,
        network_operator=record.network_operator,
        voltage_kv=float(record.voltage_kv) if record.voltage_kv is not None else None,
        network_layer=decision,
        evidence_status=evidence_status,
        source_refs=tuple(dict.fromkeys(record.source_refs)),
        reason=reason,
    )


def assert_voltage_not_layer_authority(record: NetworkLayerRecord) -> None:
    """Regression guard: voltage context alone must remain unresolved."""

    if record.voltage_kv is None:
        return
    decision = classify_network_layer(record)
    if not any(
        claim in item.supports
        for item in record.referenced_evidence
        for claim in (TRANSMISSION_LAYER, DISTRIBUTION_LAYER)
    ) and decision.network_layer != Q_UNRESOLVED_NETWORK_LAYER:
        raise B10NetworkLayerAuthorityError("voltage alone cannot classify network layer")


__all__ = [
    "B10NetworkLayerAuthorityError",
    "COORDINATED_TSO_DSO",
    "DISTRIBUTION",
    "DISTRIBUTION_LAYER",
    "NETWORK_LAYER_STATUSES",
    "NetworkLayerDecision",
    "NetworkLayerEvidence",
    "NetworkLayerRecord",
    "Q_UNRESOLVED_NETWORK_LAYER",
    "TRANSMISSION",
    "TRANSMISSION_LAYER",
    "TSO_DSO_INTERFACE",
    "assert_voltage_not_layer_authority",
    "classify_network_layer",
]
