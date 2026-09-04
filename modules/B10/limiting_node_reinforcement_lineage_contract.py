"""B10-P31 fail-closed REAL limiting-node -> reinforcement lineage gate.

Core rules:

    REAL LIMITING NODE != REINFORCEMENT REQUIRED
    SAME NODE/HORIZON != SAME REINFORCEMENT DETERMINATION
    P30 LIMITING-NODE LINEAGE != P5 REINFORCEMENT PROJECT
    P5 REINFORCEMENT_REQUIRED != STUDY-CASE LINK
    REINFORCEMENT REQUIRED != PROGRAMME-INCREMENTAL CAPEX

P30 proves that a REAL limiting-node conclusion is on the exact P29/P28
study/case/horizon lineage. P5 independently proves reinforcement requirement,
programme attribution and, when separately evidenced, programme-incremental
CAPEX. P31 links only the reinforcement requirement back to the exact limiting
study case and project. It does not mint scope, cost or programme causality.
"""

from __future__ import annotations

from dataclasses import dataclass

from .baseline_infrastructure_contract import InfrastructureRecord
from .incremental_reinforcement_contract import (
    B10IncrementalReinforcementContractError,
    DSO_SUBSTATION,
    HeadroomScreeningContext,
    REINFORCEMENT_REQUIRED,
    evaluate_programme_incremental_reinforcement,
)
from .limiting_node_study_lineage_contract import (
    REAL_LIMITING_NODE_LINEAGE_PROVEN,
    LimitingNodeStudyLineageDecision,
)


class B10LimitingNodeReinforcementLineageError(ValueError):
    """Raised when limiting-node -> reinforcement lineage is overstated."""


LIMITING_NODE_REINFORCEMENT_LINK = "LIMITING_NODE_REINFORCEMENT_LINK"
REAL_LIMITING_NODE_REINFORCEMENT_LINK_PROVEN = (
    "REAL_LIMITING_NODE_REINFORCEMENT_LINK_PROVEN"
)
Q_REAL_LIMITING_NODE_REINFORCEMENT_LINK_UNRESOLVED = (
    "Q_REAL_LIMITING_NODE_REINFORCEMENT_LINK_UNRESOLVED"
)

REAL = "REAL"
EVIDENCE_STATUSES = {"OBS", "DER", "Q"}

LINK_ID_PREFIX = "REINFORCEMENT_LINK_ID:"
PROJECT_ID_PREFIX = "PROJECT_ID:"
NETWORK_OPERATOR_PREFIX = "NETWORK_OPERATOR:"
NETWORK_STUDY_ID_PREFIX = "NETWORK_STUDY_ID:"
STUDY_CASE_ID_PREFIX = "STUDY_CASE_ID:"
NODE_REGION_ID_PREFIX = "NODE_REGION_ID:"
NODE_REGION_GRAIN_BINDING = "NODE_REGION_GRAIN:DSO_SUBSTATION"
HORIZON_PREFIX = "HORIZON:"
TRUTH_CONTEXT_PREFIX = "TRUTH_CONTEXT:"
SURVIVABILITY_RESULT_ID_PREFIX = "SURVIVABILITY_RESULT_ID:"

_LINK_AUTHORITY_MAX_LEVEL = 2


def _text(value: str, name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise B10LimitingNodeReinforcementLineageError(f"{name} is required")
    return value


@dataclass(frozen=True)
class LimitingNodeReinforcementLinkEvidence:
    source_id: str
    authority_level: int
    truth_status: str
    supports: tuple[str, ...]

    def __post_init__(self) -> None:
        _text(self.source_id, "source_id")
        if self.authority_level not in {1, 2, 3, 4, 5}:
            raise B10LimitingNodeReinforcementLineageError("authority_level must be 1..5")
        if self.truth_status not in EVIDENCE_STATUSES:
            raise B10LimitingNodeReinforcementLineageError("truth_status must be OBS, DER or Q")
        if isinstance(self.supports, str):
            raise B10LimitingNodeReinforcementLineageError("supports must be a collection")
        if any(not isinstance(item, str) or not item.strip() for item in self.supports):
            raise B10LimitingNodeReinforcementLineageError("supports cannot contain blanks")


@dataclass(frozen=True)
class LimitingNodeReinforcementLinkRecord:
    reinforcement_link_id: str
    project_id: str
    network_operator: str
    network_study_id: str
    study_case_id: str
    node_region_id: str
    horizon: str
    survivability_result_id: str
    source_refs: tuple[str, ...]
    evidence: tuple[LimitingNodeReinforcementLinkEvidence, ...]
    truth_context: str = REAL
    node_region_scheme: str = DSO_SUBSTATION

    def __post_init__(self) -> None:
        for name in (
            "reinforcement_link_id",
            "project_id",
            "network_operator",
            "network_study_id",
            "study_case_id",
            "node_region_id",
            "horizon",
            "survivability_result_id",
        ):
            _text(getattr(self, name), name)
        if self.truth_context != REAL:
            raise B10LimitingNodeReinforcementLineageError("P31 admits REAL lineage only")
        if self.node_region_scheme != DSO_SUBSTATION:
            raise B10LimitingNodeReinforcementLineageError(
                "P31 reinforcement link must remain at DSO_SUBSTATION grain"
            )
        if isinstance(self.source_refs, str) or not self.source_refs:
            raise B10LimitingNodeReinforcementLineageError("source_refs must be non-empty")
        if isinstance(self.evidence, str) or not self.evidence:
            raise B10LimitingNodeReinforcementLineageError("evidence must be non-empty")
        evidence_ids = {item.source_id for item in self.evidence}
        if not set(self.source_refs).issubset(evidence_ids):
            raise B10LimitingNodeReinforcementLineageError(
                "source_refs must identify supplied link evidence"
            )

    @property
    def referenced_evidence(self) -> tuple[LimitingNodeReinforcementLinkEvidence, ...]:
        refs = set(self.source_refs)
        return tuple(item for item in self.evidence if item.source_id in refs)


@dataclass(frozen=True)
class LimitingNodeReinforcementLineageDecision:
    reinforcement_link_id: str
    project_id: str
    network_operator: str
    network_study_id: str
    study_case_id: str
    node_region_id: str
    horizon: str
    truth_context: str
    status: str
    evidence_status: str
    reinforcement_required_proven: bool
    attribution_status: str | None
    source_refs: tuple[str, ...]
    reason: str

    def __post_init__(self) -> None:
        if self.truth_context != REAL:
            raise B10LimitingNodeReinforcementLineageError("P31 decision must preserve REAL")
        if self.status not in {
            REAL_LIMITING_NODE_REINFORCEMENT_LINK_PROVEN,
            Q_REAL_LIMITING_NODE_REINFORCEMENT_LINK_UNRESOLVED,
        }:
            raise B10LimitingNodeReinforcementLineageError("invalid P31 status")
        if self.status == REAL_LIMITING_NODE_REINFORCEMENT_LINK_PROVEN:
            if self.evidence_status not in {"OBS", "DER"}:
                raise B10LimitingNodeReinforcementLineageError("proven P31 lineage requires OBS/DER")
            if not self.reinforcement_required_proven:
                raise B10LimitingNodeReinforcementLineageError(
                    "proven P31 lineage requires P5 reinforcement_required_proven"
                )
            if self.attribution_status is None:
                raise B10LimitingNodeReinforcementLineageError(
                    "proven P31 lineage requires preserved P5 attribution status"
                )
        else:
            if self.evidence_status != "Q":
                raise B10LimitingNodeReinforcementLineageError("Q P31 lineage must preserve Q")
            if self.reinforcement_required_proven or self.attribution_status is not None:
                raise B10LimitingNodeReinforcementLineageError(
                    "Q P31 lineage must withhold reinforcement and attribution outputs"
                )


def _required(record: LimitingNodeReinforcementLinkRecord) -> set[str]:
    return {
        LIMITING_NODE_REINFORCEMENT_LINK,
        REINFORCEMENT_REQUIRED,
        f"{LINK_ID_PREFIX}{record.reinforcement_link_id}",
        f"{PROJECT_ID_PREFIX}{record.project_id}",
        f"{NETWORK_OPERATOR_PREFIX}{record.network_operator}",
        f"{NETWORK_STUDY_ID_PREFIX}{record.network_study_id}",
        f"{STUDY_CASE_ID_PREFIX}{record.study_case_id}",
        f"{NODE_REGION_ID_PREFIX}{record.node_region_id}",
        NODE_REGION_GRAIN_BINDING,
        f"{HORIZON_PREFIX}{record.horizon}",
        f"{TRUTH_CONTEXT_PREFIX}{record.truth_context}",
        f"{SURVIVABILITY_RESULT_ID_PREFIX}{record.survivability_result_id}",
    }


def _qualifying(
    record: LimitingNodeReinforcementLinkRecord,
) -> tuple[LimitingNodeReinforcementLinkEvidence, ...]:
    required = _required(record)
    return tuple(
        item
        for item in record.referenced_evidence
        if item.authority_level <= _LINK_AUTHORITY_MAX_LEVEL
        and item.truth_status in {"OBS", "DER"}
        and required.issubset(set(item.supports))
    )


def evaluate_real_limiting_node_reinforcement_lineage(
    link: LimitingNodeReinforcementLinkRecord,
    *,
    limiting_node_lineage: LimitingNodeStudyLineageDecision,
    reinforcement_record: InfrastructureRecord,
    screening: HeadroomScreeningContext | None = None,
) -> LimitingNodeReinforcementLineageDecision:
    """Link a P30 REAL limiting node to an independently proven P5 reinforcement.

    Same node/horizon is insufficient. An authoritative link must explicitly bind
    the exact P30 study/case/survivability-result lineage to the exact P5 project.
    P31 preserves only P5 reinforcement-required and attribution status; it does
    not expose or create numeric CAPEX.
    """

    if not isinstance(link, LimitingNodeReinforcementLinkRecord):
        raise B10LimitingNodeReinforcementLineageError(
            "link must be LimitingNodeReinforcementLinkRecord"
        )
    if not isinstance(limiting_node_lineage, LimitingNodeStudyLineageDecision):
        raise B10LimitingNodeReinforcementLineageError(
            "limiting_node_lineage must be LimitingNodeStudyLineageDecision"
        )
    if not isinstance(reinforcement_record, InfrastructureRecord):
        raise B10LimitingNodeReinforcementLineageError(
            "reinforcement_record must be InfrastructureRecord"
        )

    refs = tuple(
        sorted(
            set(link.source_refs)
            | set(limiting_node_lineage.source_refs)
            | set(reinforcement_record.source_refs)
        )
    )

    def q(reason: str) -> LimitingNodeReinforcementLineageDecision:
        return LimitingNodeReinforcementLineageDecision(
            link.reinforcement_link_id,
            link.project_id,
            link.network_operator,
            link.network_study_id,
            link.study_case_id,
            link.node_region_id,
            link.horizon,
            REAL,
            Q_REAL_LIMITING_NODE_REINFORCEMENT_LINK_UNRESOLVED,
            "Q",
            False,
            None,
            refs,
            reason,
        )

    if limiting_node_lineage.status != REAL_LIMITING_NODE_LINEAGE_PROVEN:
        return q("P30 REAL limiting-node lineage is not proven")
    if limiting_node_lineage.truth_context != REAL:
        return q("P30 limiting-node lineage does not preserve REAL truth context")
    if limiting_node_lineage.survivability_result_id is None:
        return q("P30 limiting-node lineage does not expose an exact P29 survivability result")

    lineage_pairs = (
        (link.network_operator, limiting_node_lineage.network_operator, "network_operator"),
        (link.network_study_id, limiting_node_lineage.network_study_id, "network_study_id"),
        (link.study_case_id, limiting_node_lineage.study_case_id, "study_case_id"),
        (link.node_region_id, limiting_node_lineage.node_region_id, "node_region_id"),
        (link.horizon, limiting_node_lineage.horizon, "horizon"),
        (
            link.survivability_result_id,
            limiting_node_lineage.survivability_result_id,
            "survivability_result_id",
        ),
    )
    for link_value, lineage_value, name in lineage_pairs:
        if link_value != lineage_value:
            return q(f"reinforcement link {name} does not match the exact P30 lineage")

    reinforcement_pairs = (
        (link.project_id, reinforcement_record.project_id, "project_id"),
        (link.network_operator, reinforcement_record.network_operator, "network_operator"),
        (link.node_region_id, reinforcement_record.region_id, "node_region_id"),
    )
    for link_value, reinforcement_value, name in reinforcement_pairs:
        if link_value != reinforcement_value:
            return q(f"reinforcement link {name} does not match the exact P5 project")
    if reinforcement_record.region_grain != DSO_SUBSTATION:
        return q("P5 reinforcement project is not at exact DSO_SUBSTATION grain")

    matches = _qualifying(link)
    if not matches:
        return q(
            "no authoritative evidence explicitly links the exact P30 study/case/result lineage "
            "to the exact P5 reinforcement project"
        )

    try:
        p5 = evaluate_programme_incremental_reinforcement(
            reinforcement_record,
            reinforcement_horizon=link.horizon,
            screening=screening,
        )
    except B10IncrementalReinforcementContractError as exc:
        return q(f"canonical P5 reinforcement gate rejected the linked project: {exc}")

    if not p5.reinforcement_required_proven:
        return q("canonical P5 does not prove REINFORCEMENT_REQUIRED for the linked project")

    link_status = "OBS" if all(item.truth_status == "OBS" for item in matches) else "DER"
    evidence_status = (
        "OBS"
        if limiting_node_lineage.evidence_status == "OBS" and link_status == "OBS"
        else "DER"
    )
    return LimitingNodeReinforcementLineageDecision(
        link.reinforcement_link_id,
        link.project_id,
        link.network_operator,
        link.network_study_id,
        link.study_case_id,
        link.node_region_id,
        link.horizon,
        REAL,
        REAL_LIMITING_NODE_REINFORCEMENT_LINK_PROVEN,
        evidence_status,
        True,
        p5.attribution.attribution_status,
        refs,
        (
            "authoritative evidence links the exact P30 limiting-node study/case/result lineage "
            "to an independently P5-proven reinforcement-required project; CAPEX remains separate"
        ),
    )


def require_real_limiting_node_reinforcement_link(
    decision: LimitingNodeReinforcementLineageDecision,
) -> str:
    if not isinstance(decision, LimitingNodeReinforcementLineageDecision):
        raise B10LimitingNodeReinforcementLineageError(
            "decision must be LimitingNodeReinforcementLineageDecision"
        )
    if decision.status != REAL_LIMITING_NODE_REINFORCEMENT_LINK_PROVEN:
        raise B10LimitingNodeReinforcementLineageError(
            "proven REAL limiting-node reinforcement lineage is required"
        )
    return decision.project_id


__all__ = [
    "B10LimitingNodeReinforcementLineageError",
    "LIMITING_NODE_REINFORCEMENT_LINK",
    "LimitingNodeReinforcementLineageDecision",
    "LimitingNodeReinforcementLinkEvidence",
    "LimitingNodeReinforcementLinkRecord",
    "Q_REAL_LIMITING_NODE_REINFORCEMENT_LINK_UNRESOLVED",
    "REAL_LIMITING_NODE_REINFORCEMENT_LINK_PROVEN",
    "evaluate_real_limiting_node_reinforcement_lineage",
    "require_real_limiting_node_reinforcement_link",
]
