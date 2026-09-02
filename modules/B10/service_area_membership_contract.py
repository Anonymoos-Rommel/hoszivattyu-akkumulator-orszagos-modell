"""B10-P15 fail-closed DSO service-area membership contract.

P15 separates administrative identity normalization from DSO service-area
membership and from exact electrical topology.

Core rule:

    SETTLEMENT NAME
    != KSH SETTLEMENT ID
    != WHOLE-SETTLEMENT DSO MEMBERSHIP
    != PARTIAL-SETTLEMENT USAGE-LOCATION MEMBERSHIP
    != EXACT DSO NODE
"""

from __future__ import annotations

from dataclasses import dataclass

from modules.B10.spatial_authority_contract import DSO_SERVICE_AREA


class B10ServiceAreaMembershipError(ValueError):
    """Raised when a service-area membership claim is ambiguous or overstated."""


WHOLE_SETTLEMENT = "WHOLE_SETTLEMENT"
PARTIAL_SETTLEMENT = "PARTIAL_SETTLEMENT"

KSH_SETTLEMENT_IDENTITY = "KSH_SETTLEMENT_IDENTITY"
DSO_SERVICE_AREA_MEMBERSHIP = "DSO_SERVICE_AREA_MEMBERSHIP"
PARTIAL_SETTLEMENT_BOUNDARY = "PARTIAL_SETTLEMENT_BOUNDARY"
USAGE_LOCATION_SERVICE_AREA_MEMBERSHIP = "USAGE_LOCATION_SERVICE_AREA_MEMBERSHIP"

WHOLE_SETTLEMENT_MEMBERSHIP_PROVEN = "WHOLE_SETTLEMENT_MEMBERSHIP_PROVEN"
USAGE_LOCATION_MEMBERSHIP_PROVEN = "USAGE_LOCATION_MEMBERSHIP_PROVEN"
Q_ADMINISTRATIVE_IDENTIFIER_NORMALIZATION = "Q_ADMINISTRATIVE_IDENTIFIER_NORMALIZATION"
Q_PARTIAL_SETTLEMENT_USAGE_LOCATION_REQUIRED = "Q_PARTIAL_SETTLEMENT_USAGE_LOCATION_REQUIRED"
Q_SERVICE_AREA_MEMBERSHIP_UNRESOLVED = "Q_SERVICE_AREA_MEMBERSHIP_UNRESOLVED"

SETTLEMENT_NAME_PREFIX = "SETTLEMENT_NAME:"
KSH_SETTLEMENT_CODE_PREFIX = "KSH_SETTLEMENT_CODE:"
NETWORK_OPERATOR_PREFIX = "NETWORK_OPERATOR:"
SERVICE_AREA_ID_PREFIX = "SERVICE_AREA_ID:"
USAGE_LOCATION_ID_PREFIX = "USAGE_LOCATION_ID:"

EVIDENCE_STATUSES = {"OBS", "DER", "Q"}


@dataclass(frozen=True)
class ServiceAreaMembershipEvidence:
    source_id: str
    authority_level: int
    truth_status: str
    supports: tuple[str, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.source_id, str) or not self.source_id.strip():
            raise B10ServiceAreaMembershipError("source_id is required")
        if self.authority_level not in {1, 2, 3, 4, 5}:
            raise B10ServiceAreaMembershipError("authority_level must be 1..5")
        if self.truth_status not in EVIDENCE_STATUSES:
            raise B10ServiceAreaMembershipError("truth_status must be OBS, DER or Q")
        if isinstance(self.supports, str):
            raise B10ServiceAreaMembershipError("supports must be a collection")
        if any(not isinstance(claim, str) or not claim.strip() for claim in self.supports):
            raise B10ServiceAreaMembershipError("supports cannot contain blanks")


@dataclass(frozen=True)
class ServiceAreaMembershipRecord:
    settlement_name: str
    ksh_settlement_code: str | None
    network_operator: str
    service_area_id: str
    coverage_scope: str
    source_refs: tuple[str, ...]
    evidence: tuple[ServiceAreaMembershipEvidence, ...]
    usage_location_id: str | None = None

    def __post_init__(self) -> None:
        for name in ("settlement_name", "network_operator", "service_area_id"):
            value = getattr(self, name)
            if not isinstance(value, str) or not value.strip():
                raise B10ServiceAreaMembershipError(f"{name} is required")
        if self.ksh_settlement_code is not None and (
            not isinstance(self.ksh_settlement_code, str) or not self.ksh_settlement_code.strip()
        ):
            raise B10ServiceAreaMembershipError("ksh_settlement_code must be non-blank or None")
        if self.usage_location_id is not None and (
            not isinstance(self.usage_location_id, str) or not self.usage_location_id.strip()
        ):
            raise B10ServiceAreaMembershipError("usage_location_id must be non-blank or None")
        if self.coverage_scope not in {WHOLE_SETTLEMENT, PARTIAL_SETTLEMENT}:
            raise B10ServiceAreaMembershipError("coverage_scope must be WHOLE_SETTLEMENT or PARTIAL_SETTLEMENT")
        if not self.service_area_id.endswith(":SERVICE_AREA"):
            raise B10ServiceAreaMembershipError("service_area_id must preserve canonical DSO service-area identity")
        if isinstance(self.source_refs, str) or not self.source_refs:
            raise B10ServiceAreaMembershipError("source_refs must be non-empty")
        if isinstance(self.evidence, str) or not self.evidence:
            raise B10ServiceAreaMembershipError("evidence must be non-empty")
        evidence_ids = {item.source_id for item in self.evidence}
        if not set(self.source_refs).issubset(evidence_ids):
            raise B10ServiceAreaMembershipError("source_refs must identify supplied evidence")

    @property
    def referenced_evidence(self) -> tuple[ServiceAreaMembershipEvidence, ...]:
        refs = set(dict.fromkeys(self.source_refs))
        return tuple(item for item in self.evidence if item.source_id in refs)


@dataclass(frozen=True)
class ServiceAreaMembershipDecision:
    settlement_name: str
    ksh_settlement_code: str | None
    network_operator: str
    service_area_id: str | None
    region_grain: str
    status: str
    coverage_scope: str
    usage_location_id: str | None
    evidence_status: str
    source_refs: tuple[str, ...]
    reason: str

    def __post_init__(self) -> None:
        if self.region_grain != DSO_SERVICE_AREA:
            raise B10ServiceAreaMembershipError("region_grain must remain DSO_SERVICE_AREA")
        if self.status not in {
            WHOLE_SETTLEMENT_MEMBERSHIP_PROVEN,
            USAGE_LOCATION_MEMBERSHIP_PROVEN,
            Q_ADMINISTRATIVE_IDENTIFIER_NORMALIZATION,
            Q_PARTIAL_SETTLEMENT_USAGE_LOCATION_REQUIRED,
            Q_SERVICE_AREA_MEMBERSHIP_UNRESOLVED,
        }:
            raise B10ServiceAreaMembershipError("invalid membership decision status")
        if self.status in {WHOLE_SETTLEMENT_MEMBERSHIP_PROVEN, USAGE_LOCATION_MEMBERSHIP_PROVEN}:
            if self.service_area_id is None:
                raise B10ServiceAreaMembershipError("proven membership requires service_area_id")
        elif self.service_area_id is not None:
            raise B10ServiceAreaMembershipError("Q membership cannot expose authoritative service_area_id")


def _has_bound_claim(
    record: ServiceAreaMembershipRecord,
    claim: str,
    extra: tuple[str, ...],
    *,
    max_authority_level: int,
) -> bool:
    required = {
        claim,
        f"{SETTLEMENT_NAME_PREFIX}{record.settlement_name}",
        f"{NETWORK_OPERATOR_PREFIX}{record.network_operator}",
        f"{SERVICE_AREA_ID_PREFIX}{record.service_area_id}",
        *extra,
    }
    return any(
        item.authority_level <= max_authority_level
        and item.truth_status in {"OBS", "DER"}
        and required.issubset(set(item.supports))
        for item in record.referenced_evidence
    )


def _ksh_identity_proven(record: ServiceAreaMembershipRecord) -> bool:
    if record.ksh_settlement_code is None:
        return False
    required = {
        KSH_SETTLEMENT_IDENTITY,
        f"{SETTLEMENT_NAME_PREFIX}{record.settlement_name}",
        f"{KSH_SETTLEMENT_CODE_PREFIX}{record.ksh_settlement_code}",
    }
    return any(
        item.authority_level <= 3
        and item.truth_status in {"OBS", "DER"}
        and required.issubset(set(item.supports))
        for item in record.referenced_evidence
    )


def classify_service_area_membership(record: ServiceAreaMembershipRecord) -> ServiceAreaMembershipDecision:
    """Classify DSO service-area membership without inferring topology.

    Whole-settlement membership can be promoted only when both the exact
    administrative settlement identity and the DSO membership claim are bound.
    Partial-settlement cases cannot be promoted at settlement grain; they require
    separate usage-location-specific authority.
    """

    if not isinstance(record, ServiceAreaMembershipRecord):
        raise B10ServiceAreaMembershipError("record must be ServiceAreaMembershipRecord")

    refs = record.referenced_evidence
    ksh_identity = _ksh_identity_proven(record)
    whole_membership = _has_bound_claim(
        record,
        DSO_SERVICE_AREA_MEMBERSHIP,
        (WHOLE_SETTLEMENT,),
        max_authority_level=3,
    )
    partial_boundary = _has_bound_claim(
        record,
        PARTIAL_SETTLEMENT_BOUNDARY,
        (PARTIAL_SETTLEMENT,),
        max_authority_level=3,
    )
    usage_membership = False
    if record.usage_location_id is not None:
        usage_membership = _has_bound_claim(
            record,
            USAGE_LOCATION_SERVICE_AREA_MEMBERSHIP,
            (f"{USAGE_LOCATION_ID_PREFIX}{record.usage_location_id}",),
            max_authority_level=2,
        )

    statuses = {item.truth_status for item in refs}
    if "Q" in statuses:
        evidence_status = "Q"
    elif statuses == {"OBS"}:
        evidence_status = "OBS"
    else:
        evidence_status = "DER"

    if not ksh_identity:
        return ServiceAreaMembershipDecision(
            settlement_name=record.settlement_name,
            ksh_settlement_code=None,
            network_operator=record.network_operator,
            service_area_id=None,
            region_grain=DSO_SERVICE_AREA,
            status=Q_ADMINISTRATIVE_IDENTIFIER_NORMALIZATION,
            coverage_scope=record.coverage_scope,
            usage_location_id=record.usage_location_id,
            evidence_status="Q",
            source_refs=tuple(dict.fromkeys(record.source_refs)),
            reason="settlement name is not yet authoritatively normalized to the KSH settlement identifier",
        )

    if "Q" in statuses:
        return ServiceAreaMembershipDecision(
            settlement_name=record.settlement_name,
            ksh_settlement_code=record.ksh_settlement_code,
            network_operator=record.network_operator,
            service_area_id=None,
            region_grain=DSO_SERVICE_AREA,
            status=Q_SERVICE_AREA_MEMBERSHIP_UNRESOLVED,
            coverage_scope=record.coverage_scope,
            usage_location_id=record.usage_location_id,
            evidence_status="Q",
            source_refs=tuple(dict.fromkeys(record.source_refs)),
            reason="referenced Q evidence prevents promotion of DSO service-area membership",
        )

    if record.coverage_scope == WHOLE_SETTLEMENT:
        if whole_membership:
            return ServiceAreaMembershipDecision(
                settlement_name=record.settlement_name,
                ksh_settlement_code=record.ksh_settlement_code,
                network_operator=record.network_operator,
                service_area_id=record.service_area_id,
                region_grain=DSO_SERVICE_AREA,
                status=WHOLE_SETTLEMENT_MEMBERSHIP_PROVEN,
                coverage_scope=record.coverage_scope,
                usage_location_id=None,
                evidence_status=evidence_status,
                source_refs=tuple(dict.fromkeys(record.source_refs)),
                reason="KSH settlement identity and source-bound whole-settlement DSO membership are both proven",
            )
        return ServiceAreaMembershipDecision(
            settlement_name=record.settlement_name,
            ksh_settlement_code=record.ksh_settlement_code,
            network_operator=record.network_operator,
            service_area_id=None,
            region_grain=DSO_SERVICE_AREA,
            status=Q_SERVICE_AREA_MEMBERSHIP_UNRESOLVED,
            coverage_scope=record.coverage_scope,
            usage_location_id=None,
            evidence_status="Q",
            source_refs=tuple(dict.fromkeys(record.source_refs)),
            reason="whole-settlement service-area membership lacks claim-specific referenced authority",
        )

    if partial_boundary and usage_membership:
        return ServiceAreaMembershipDecision(
            settlement_name=record.settlement_name,
            ksh_settlement_code=record.ksh_settlement_code,
            network_operator=record.network_operator,
            service_area_id=record.service_area_id,
            region_grain=DSO_SERVICE_AREA,
            status=USAGE_LOCATION_MEMBERSHIP_PROVEN,
            coverage_scope=record.coverage_scope,
            usage_location_id=record.usage_location_id,
            evidence_status=evidence_status,
            source_refs=tuple(dict.fromkeys(record.source_refs)),
            reason="partial-settlement boundary and exact usage-location DSO membership are separately proven",
        )

    return ServiceAreaMembershipDecision(
        settlement_name=record.settlement_name,
        ksh_settlement_code=record.ksh_settlement_code,
        network_operator=record.network_operator,
        service_area_id=None,
        region_grain=DSO_SERVICE_AREA,
        status=Q_PARTIAL_SETTLEMENT_USAGE_LOCATION_REQUIRED if partial_boundary else Q_SERVICE_AREA_MEMBERSHIP_UNRESOLVED,
        coverage_scope=record.coverage_scope,
        usage_location_id=record.usage_location_id,
        evidence_status="Q",
        source_refs=tuple(dict.fromkeys(record.source_refs)),
        reason=(
            "partial-settlement evidence cannot assign the entire administrative settlement; exact usage-location authority is required"
            if partial_boundary
            else "partial-settlement service-area membership lacks claim-specific referenced authority"
        ),
    )


def require_service_area_membership(decision: ServiceAreaMembershipDecision) -> str:
    """Authorize a DSO_SERVICE_AREA handoff only after membership is proven."""

    if not isinstance(decision, ServiceAreaMembershipDecision):
        raise B10ServiceAreaMembershipError("decision must be ServiceAreaMembershipDecision")
    if decision.status not in {WHOLE_SETTLEMENT_MEMBERSHIP_PROVEN, USAGE_LOCATION_MEMBERSHIP_PROVEN}:
        raise B10ServiceAreaMembershipError("proven DSO service-area membership is required")
    if decision.service_area_id is None:
        raise B10ServiceAreaMembershipError("proven membership must expose service_area_id")
    return decision.service_area_id


__all__ = [
    "B10ServiceAreaMembershipError",
    "DSO_SERVICE_AREA_MEMBERSHIP",
    "KSH_SETTLEMENT_IDENTITY",
    "PARTIAL_SETTLEMENT",
    "PARTIAL_SETTLEMENT_BOUNDARY",
    "Q_ADMINISTRATIVE_IDENTIFIER_NORMALIZATION",
    "Q_PARTIAL_SETTLEMENT_USAGE_LOCATION_REQUIRED",
    "Q_SERVICE_AREA_MEMBERSHIP_UNRESOLVED",
    "ServiceAreaMembershipDecision",
    "ServiceAreaMembershipEvidence",
    "ServiceAreaMembershipRecord",
    "USAGE_LOCATION_MEMBERSHIP_PROVEN",
    "USAGE_LOCATION_SERVICE_AREA_MEMBERSHIP",
    "WHOLE_SETTLEMENT",
    "WHOLE_SETTLEMENT_MEMBERSHIP_PROVEN",
    "classify_service_area_membership",
    "require_service_area_membership",
]
