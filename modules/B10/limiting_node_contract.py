"""B10-P26 fail-closed limiting-node authority gate.

Core rules:

    PUBLISHED HEADROOM EXCEEDANCE != LIMITING NODE
    BOUNDED TOPOLOGY EDGE != LIMITING NODE
    TOPOLOGY ENDPOINT != LIMITING NODE
    NETWORK SURVIVABILITY STUDY != LIMITING NODE
    LIMITING NODE != REINFORCEMENT REQUIRED
    LIMITING NODE != PROGRAMME-INCREMENTAL CAPEX

A limiting/binding node is admitted only when a claim-specific authoritative
network study binds that conclusion to the exact canonical DSO substation,
study case and assessed managed peak. P1/P5 screening, P24 topology and P25
endpoint typing may provide context but cannot mint the claim.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import isfinite

from .incremental_reinforcement_contract import (
    DSO_SUBSTATION,
    HORIZONS,
    HeadroomScreeningContext,
)
from .managed_flex_survivability_contract import (
    SURVIVABILITY_PROVEN,
    NetworkSurvivabilityDecision,
)
from .topology_endpoint_contract import (
    CANONICAL_DSO_NODE_LINK_PROVEN,
    DSO_SUBSTATION as ENDPOINT_DSO_SUBSTATION,
    TOPOLOGY_ENDPOINT_PROVEN,
    TopologyEndpointDecision,
)


class B10LimitingNodeError(ValueError):
    """Raised when a limiting-node claim is structurally or evidentially invalid."""


LIMITING_NODE = "LIMITING_NODE"
NON_LIMITING_NODE = "NON_LIMITING_NODE"

LIMITING_NODE_PROVEN = "LIMITING_NODE_PROVEN"
NON_LIMITING_NODE_PROVEN = "NON_LIMITING_NODE_PROVEN"
Q_LIMITING_NODE_UNRESOLVED = "Q_LIMITING_NODE_UNRESOLVED"

REAL = "REAL"
SCN = "SCN"
TRUTH_CONTEXTS = {REAL, SCN}
EVIDENCE_STATUSES = {"OBS", "DER", "SCN", "Q"}

THERMAL_LIMIT = "THERMAL_LIMIT"
VOLTAGE_LIMIT = "VOLTAGE_LIMIT"
CONTINGENCY_LIMIT = "CONTINGENCY_LIMIT"
SOURCE_STATED_UNSPECIFIED = "SOURCE_STATED_UNSPECIFIED"
CONSTRAINT_KINDS = {
    THERMAL_LIMIT,
    VOLTAGE_LIMIT,
    CONTINGENCY_LIMIT,
    SOURCE_STATED_UNSPECIFIED,
}

NETWORK_OPERATOR_PREFIX = "NETWORK_OPERATOR:"
NETWORK_STUDY_ID_PREFIX = "NETWORK_STUDY_ID:"
STUDY_CASE_ID_PREFIX = "STUDY_CASE_ID:"
NODE_REGION_ID_PREFIX = "NODE_REGION_ID:"
NODE_REGION_GRAIN_BINDING = "NODE_REGION_GRAIN:DSO_SUBSTATION"
HORIZON_PREFIX = "HORIZON:"
TRUTH_CONTEXT_PREFIX = "TRUTH_CONTEXT:"
ASSESSED_MANAGED_PEAK_PREFIX = "ASSESSED_MANAGED_PEAK_MW:"
CONSTRAINT_KIND_PREFIX = "CONSTRAINT_KIND:"


@dataclass(frozen=True)
class LimitingNodeEvidence:
    source_id: str
    authority_level: int
    truth_status: str
    supports: tuple[str, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.source_id, str) or not self.source_id.strip():
            raise B10LimitingNodeError("source_id is required")
        if self.authority_level not in {1, 2, 3, 4, 5}:
            raise B10LimitingNodeError("authority_level must be 1..5")
        if self.truth_status not in EVIDENCE_STATUSES:
            raise B10LimitingNodeError("invalid truth_status")
        if isinstance(self.supports, str):
            raise B10LimitingNodeError("supports must be a collection")
        if any(not isinstance(item, str) or not item.strip() for item in self.supports):
            raise B10LimitingNodeError("supports cannot contain blanks")


@dataclass(frozen=True)
class LimitingNodeRecord:
    network_operator: str
    network_study_id: str
    study_case_id: str
    node_region_id: str
    horizon: str
    truth_context: str
    assessed_managed_peak_mw: float
    constraint_kind: str
    source_refs: tuple[str, ...]
    evidence: tuple[LimitingNodeEvidence, ...]
    node_region_scheme: str = DSO_SUBSTATION

    def __post_init__(self) -> None:
        for name in (
            "network_operator",
            "network_study_id",
            "study_case_id",
            "node_region_id",
        ):
            value = getattr(self, name)
            if not isinstance(value, str) or not value.strip():
                raise B10LimitingNodeError(f"{name} is required")
        if self.node_region_scheme != DSO_SUBSTATION:
            raise B10LimitingNodeError("limiting-node claim requires exact DSO_SUBSTATION grain")
        if self.horizon not in HORIZONS:
            raise B10LimitingNodeError("horizon must be CURRENT or FIVE_YEAR")
        if self.truth_context not in TRUTH_CONTEXTS:
            raise B10LimitingNodeError("truth_context must be REAL or SCN")
        if self.constraint_kind not in CONSTRAINT_KINDS:
            raise B10LimitingNodeError("unsupported constraint_kind")
        value = self.assessed_managed_peak_mw
        if (
            isinstance(value, bool)
            or not isinstance(value, (int, float))
            or not isfinite(value)
            or value < 0
        ):
            raise B10LimitingNodeError("assessed_managed_peak_mw must be finite and non-negative")
        object.__setattr__(self, "assessed_managed_peak_mw", float(value))
        if isinstance(self.source_refs, str) or not self.source_refs:
            raise B10LimitingNodeError("source_refs must be non-empty")
        if any(not isinstance(ref, str) or not ref.strip() for ref in self.source_refs):
            raise B10LimitingNodeError("source_refs cannot contain blanks")
        if isinstance(self.evidence, str) or not self.evidence:
            raise B10LimitingNodeError("evidence must be non-empty")
        evidence_ids = {item.source_id for item in self.evidence}
        if not set(self.source_refs).issubset(evidence_ids):
            raise B10LimitingNodeError("source_refs must identify supplied evidence")

    @property
    def referenced_evidence(self) -> tuple[LimitingNodeEvidence, ...]:
        refs = set(self.source_refs)
        return tuple(item for item in self.evidence if item.source_id in refs)


@dataclass(frozen=True)
class LimitingNodeDecision:
    network_operator: str
    network_study_id: str
    study_case_id: str
    node_region_id: str
    horizon: str
    truth_context: str
    status: str
    assessed_managed_peak_mw: float | None
    constraint_kind: str | None
    evidence_status: str
    source_refs: tuple[str, ...]
    reason: str

    def __post_init__(self) -> None:
        if self.status not in {
            LIMITING_NODE_PROVEN,
            NON_LIMITING_NODE_PROVEN,
            Q_LIMITING_NODE_UNRESOLVED,
        }:
            raise B10LimitingNodeError("invalid limiting-node status")
        if self.status == Q_LIMITING_NODE_UNRESOLVED:
            if self.assessed_managed_peak_mw is not None or self.constraint_kind is not None:
                raise B10LimitingNodeError(
                    "Q limiting-node decision must withhold authoritative peak and constraint kind"
                )
        else:
            if self.assessed_managed_peak_mw is None or self.constraint_kind is None:
                raise B10LimitingNodeError(
                    "proven limiting/non-limiting decision requires peak and constraint kind"
                )


def _validate_contexts(
    record: LimitingNodeRecord,
    *,
    topology_endpoint: TopologyEndpointDecision,
    survivability: NetworkSurvivabilityDecision,
    screening: HeadroomScreeningContext | None,
) -> None:
    if not isinstance(topology_endpoint, TopologyEndpointDecision):
        raise B10LimitingNodeError("topology_endpoint must be TopologyEndpointDecision")
    if topology_endpoint.status != TOPOLOGY_ENDPOINT_PROVEN:
        raise B10LimitingNodeError("limiting-node evaluation requires proven endpoint identity")
    if topology_endpoint.endpoint_kind != ENDPOINT_DSO_SUBSTATION:
        raise B10LimitingNodeError("limiting node must be a DSO_SUBSTATION endpoint")
    if topology_endpoint.node_link_status != CANONICAL_DSO_NODE_LINK_PROVEN:
        raise B10LimitingNodeError("limiting node requires proven canonical DSO-node linkage")
    if topology_endpoint.canonical_dso_node_ref != record.node_region_id:
        raise B10LimitingNodeError("topology endpoint must link to the exact limiting-node candidate")

    if not isinstance(survivability, NetworkSurvivabilityDecision):
        raise B10LimitingNodeError("survivability must be NetworkSurvivabilityDecision")
    if survivability.status != SURVIVABILITY_PROVEN:
        raise B10LimitingNodeError("limiting-node evaluation requires a proven network survivability study")
    if survivability.node_region_id != record.node_region_id:
        raise B10LimitingNodeError("survivability study must bind the exact candidate node")
    if survivability.assessed_managed_peak_mw != record.assessed_managed_peak_mw:
        raise B10LimitingNodeError("survivability study must bind the same assessed managed peak")

    if screening is not None:
        if not isinstance(screening, HeadroomScreeningContext):
            raise B10LimitingNodeError("screening must be HeadroomScreeningContext or None")
        if screening.network_operator != record.network_operator:
            raise B10LimitingNodeError("screening operator must match limiting-node study operator")
        if screening.region_id != record.node_region_id:
            raise B10LimitingNodeError("screening node must match limiting-node candidate")
        if screening.horizon != record.horizon:
            raise B10LimitingNodeError("screening horizon must match limiting-node study horizon")


def evaluate_limiting_node(
    record: LimitingNodeRecord,
    *,
    topology_endpoint: TopologyEndpointDecision,
    survivability: NetworkSurvivabilityDecision,
    screening: HeadroomScreeningContext | None = None,
) -> LimitingNodeDecision:
    """Admit a limiting/non-limiting node only from explicit study authority.

    P5 headroom screening is optional context. Its status never enters the proof
    predicate, so WITHIN/EXCEEDS/Q cannot mint a limiting-node decision.
    """

    if not isinstance(record, LimitingNodeRecord):
        raise B10LimitingNodeError("record must be LimitingNodeRecord")
    _validate_contexts(
        record,
        topology_endpoint=topology_endpoint,
        survivability=survivability,
        screening=screening,
    )

    required_binding = {
        f"{NETWORK_OPERATOR_PREFIX}{record.network_operator}",
        f"{NETWORK_STUDY_ID_PREFIX}{record.network_study_id}",
        f"{STUDY_CASE_ID_PREFIX}{record.study_case_id}",
        f"{NODE_REGION_ID_PREFIX}{record.node_region_id}",
        NODE_REGION_GRAIN_BINDING,
        f"{HORIZON_PREFIX}{record.horizon}",
        f"{TRUTH_CONTEXT_PREFIX}{record.truth_context}",
        f"{ASSESSED_MANAGED_PEAK_PREFIX}{record.assessed_managed_peak_mw}",
        f"{CONSTRAINT_KIND_PREFIX}{record.constraint_kind}",
    }
    allowed_truth = {"OBS", "DER"} if record.truth_context == REAL else {"SCN"}

    limiting_matches = tuple(
        item
        for item in record.referenced_evidence
        if item.authority_level <= 2
        and item.truth_status in allowed_truth
        and required_binding.issubset(set(item.supports))
        and LIMITING_NODE in set(item.supports)
    )
    non_limiting_matches = tuple(
        item
        for item in record.referenced_evidence
        if item.authority_level <= 2
        and item.truth_status in allowed_truth
        and required_binding.issubset(set(item.supports))
        and NON_LIMITING_NODE in set(item.supports)
    )

    if limiting_matches and non_limiting_matches:
        raise B10LimitingNodeError(
            "the same exact study case cannot prove both LIMITING_NODE and NON_LIMITING_NODE"
        )

    matches = limiting_matches or non_limiting_matches
    if not matches:
        return LimitingNodeDecision(
            record.network_operator,
            record.network_study_id,
            record.study_case_id,
            record.node_region_id,
            record.horizon,
            record.truth_context,
            Q_LIMITING_NODE_UNRESOLVED,
            None,
            None,
            "Q",
            tuple(dict.fromkeys(record.source_refs)),
            "no referenced authoritative study evidence explicitly binds a limiting/non-limiting conclusion to the exact node, case, horizon and managed peak",
        )

    evidence_status = (
        "SCN"
        if record.truth_context == SCN
        else ("OBS" if all(item.truth_status == "OBS" for item in matches) else "DER")
    )
    status = LIMITING_NODE_PROVEN if limiting_matches else NON_LIMITING_NODE_PROVEN
    return LimitingNodeDecision(
        record.network_operator,
        record.network_study_id,
        record.study_case_id,
        record.node_region_id,
        record.horizon,
        record.truth_context,
        status,
        record.assessed_managed_peak_mw,
        record.constraint_kind,
        evidence_status,
        tuple(dict.fromkeys(record.source_refs)),
        "claim-specific authoritative network-study evidence binds the exact limiting-node conclusion",
    )


def require_limiting_node(decision: LimitingNodeDecision) -> str:
    """Return exact node identity only for a proven limiting-node conclusion."""

    if not isinstance(decision, LimitingNodeDecision):
        raise B10LimitingNodeError("decision must be LimitingNodeDecision")
    if decision.status != LIMITING_NODE_PROVEN:
        raise B10LimitingNodeError("proven limiting-node authority is required")
    return decision.node_region_id


__all__ = [
    "B10LimitingNodeError",
    "CONSTRAINT_KINDS",
    "CONTINGENCY_LIMIT",
    "LIMITING_NODE",
    "LIMITING_NODE_PROVEN",
    "LimitingNodeDecision",
    "LimitingNodeEvidence",
    "LimitingNodeRecord",
    "NON_LIMITING_NODE",
    "NON_LIMITING_NODE_PROVEN",
    "Q_LIMITING_NODE_UNRESOLVED",
    "REAL",
    "SCN",
    "SOURCE_STATED_UNSPECIFIED",
    "THERMAL_LIMIT",
    "VOLTAGE_LIMIT",
    "evaluate_limiting_node",
    "require_limiting_node",
]
