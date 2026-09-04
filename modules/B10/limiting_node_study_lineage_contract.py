"""B10-P30 fail-closed REAL limiting-node study-lineage gate.

Core rules:

    P10 SURVIVABILITY_PROVEN != P29 COMPLETE STUDY RESULT
    P26 LIMITING_NODE_PROVEN != P29-LINKED REAL LIMITING NODE
    SAME NODE/PEAK != SAME STUDY/CASE/HORIZON LINEAGE
    P29 SURVIVABILITY STUDY RESULT != LIMITING/NON-LIMITING NODE
    MISSING P29 NODE RESULT != NON_LIMITING NODE
    LIMITING NODE != REINFORCEMENT REQUIRED

P26 is the canonical claim-specific limiting/non-limiting node authority gate. It
predates P29 and therefore accepts a P10 NetworkSurvivabilityDecision as its
survivability prerequisite. P29 now provides the stronger REAL study-case result
lineage: complete node coverage tied to the exact P28 study input, study id, case,
horizon and managed peak.

P30 keeps P26 intact as the lower-level claim gate but prevents a REAL programme
lineage from bypassing P29 by supplying an arbitrary P10 survivability decision.
"""

from __future__ import annotations

from dataclasses import dataclass

from .incremental_reinforcement_contract import HeadroomScreeningContext
from .limiting_node_contract import (
    B10LimitingNodeError,
    LIMITING_NODE_PROVEN,
    NON_LIMITING_NODE_PROVEN,
    Q_LIMITING_NODE_UNRESOLVED,
    REAL,
    LimitingNodeDecision,
    LimitingNodeRecord,
    evaluate_limiting_node,
)
from .survivability_study_result_contract import (
    REAL_SURVIVABILITY_STUDY_RESULT_PROVEN,
    SurvivabilityStudyNodeResult,
    SurvivabilityStudyResultDecision,
)
from .topology_endpoint_contract import TopologyEndpointDecision


class B10LimitingNodeStudyLineageError(ValueError):
    """Raised when a REAL limiting-node lineage is structurally invalid."""


REAL_LIMITING_NODE_LINEAGE_PROVEN = "REAL_LIMITING_NODE_LINEAGE_PROVEN"
REAL_NON_LIMITING_NODE_LINEAGE_PROVEN = "REAL_NON_LIMITING_NODE_LINEAGE_PROVEN"
Q_REAL_LIMITING_NODE_LINEAGE_UNRESOLVED = "Q_REAL_LIMITING_NODE_LINEAGE_UNRESOLVED"


@dataclass(frozen=True)
class LimitingNodeStudyLineageDecision:
    network_operator: str
    network_study_id: str
    study_case_id: str
    horizon: str
    node_region_id: str
    truth_context: str
    status: str
    evidence_status: str
    survivability_result_id: str | None
    limiting_node_decision: LimitingNodeDecision | None
    source_refs: tuple[str, ...]
    reason: str

    def __post_init__(self) -> None:
        if self.truth_context != REAL:
            raise B10LimitingNodeStudyLineageError("P30 decisions must preserve REAL truth context")
        if self.status not in {
            REAL_LIMITING_NODE_LINEAGE_PROVEN,
            REAL_NON_LIMITING_NODE_LINEAGE_PROVEN,
            Q_REAL_LIMITING_NODE_LINEAGE_UNRESOLVED,
        }:
            raise B10LimitingNodeStudyLineageError("invalid P30 limiting-node lineage status")
        if self.status == Q_REAL_LIMITING_NODE_LINEAGE_UNRESOLVED:
            if self.evidence_status != "Q":
                raise B10LimitingNodeStudyLineageError("Q lineage must preserve Q evidence status")
            if self.survivability_result_id is not None or self.limiting_node_decision is not None:
                raise B10LimitingNodeStudyLineageError(
                    "Q lineage must withhold authoritative survivability-result and P26 decision"
                )
        else:
            if self.evidence_status not in {"OBS", "DER"}:
                raise B10LimitingNodeStudyLineageError("proven REAL lineage requires OBS/DER evidence")
            if not self.survivability_result_id or self.limiting_node_decision is None:
                raise B10LimitingNodeStudyLineageError(
                    "proven REAL lineage requires an exact P29 node result and P26 decision"
                )
            expected = (
                LIMITING_NODE_PROVEN
                if self.status == REAL_LIMITING_NODE_LINEAGE_PROVEN
                else NON_LIMITING_NODE_PROVEN
            )
            if self.limiting_node_decision.status != expected:
                raise B10LimitingNodeStudyLineageError("P30 status must agree with the canonical P26 decision")
            if self.limiting_node_decision.node_region_id != self.node_region_id:
                raise B10LimitingNodeStudyLineageError("P26 node must equal the P30 exact node")


def _find_p29_node(
    study_result: SurvivabilityStudyResultDecision,
    node_region_id: str,
) -> SurvivabilityStudyNodeResult | None:
    matches = tuple(item for item in study_result.node_results if item.node_region_id == node_region_id)
    if len(matches) != 1:
        return None
    return matches[0]


def evaluate_real_limiting_node_study_lineage(
    record: LimitingNodeRecord,
    *,
    topology_endpoint: TopologyEndpointDecision,
    survivability_study_result: SurvivabilityStudyResultDecision,
    screening: HeadroomScreeningContext | None = None,
) -> LimitingNodeStudyLineageDecision:
    """Evaluate P26 only through an exact proven P29 REAL study-result lineage.

    P30 does not change the P26 limiting-node proof predicate. It strengthens the
    prerequisite path for REAL programme reasoning by requiring the P10
    survivability object consumed by P26 to be the exact node result carried by a
    complete P29 study-result decision for the same study, case and horizon.
    """

    if not isinstance(record, LimitingNodeRecord):
        raise B10LimitingNodeStudyLineageError("record must be LimitingNodeRecord")
    if not isinstance(topology_endpoint, TopologyEndpointDecision):
        raise B10LimitingNodeStudyLineageError("topology_endpoint must be TopologyEndpointDecision")
    if not isinstance(survivability_study_result, SurvivabilityStudyResultDecision):
        raise B10LimitingNodeStudyLineageError(
            "survivability_study_result must be SurvivabilityStudyResultDecision"
        )
    if record.truth_context != REAL:
        raise B10LimitingNodeStudyLineageError(
            "P30 is a REAL programme lineage gate; SCN P26 analysis remains separate"
        )

    refs = tuple(sorted(set(record.source_refs) | set(survivability_study_result.source_refs)))

    def q(reason: str) -> LimitingNodeStudyLineageDecision:
        return LimitingNodeStudyLineageDecision(
            record.network_operator,
            record.network_study_id,
            record.study_case_id,
            record.horizon,
            record.node_region_id,
            REAL,
            Q_REAL_LIMITING_NODE_LINEAGE_UNRESOLVED,
            "Q",
            None,
            None,
            refs,
            reason,
        )

    if survivability_study_result.status != REAL_SURVIVABILITY_STUDY_RESULT_PROVEN:
        return q("P29 complete REAL survivability study result is not proven")
    if survivability_study_result.truth_context != REAL:
        return q("P29 survivability study result does not preserve REAL truth context")

    identity_pairs = (
        (record.network_operator, survivability_study_result.network_operator, "network_operator"),
        (record.network_study_id, survivability_study_result.network_study_id, "network_study_id"),
        (record.study_case_id, survivability_study_result.study_case_id, "study_case_id"),
        (record.horizon, survivability_study_result.horizon, "horizon"),
    )
    for record_value, result_value, name in identity_pairs:
        if record_value != result_value:
            return q(f"P26 limiting-node {name} does not match the proven P29 study-result lineage")

    node_result = _find_p29_node(survivability_study_result, record.node_region_id)
    if node_result is None:
        return q("exact limiting-node candidate is not uniquely present in the proven P29 result set")
    if node_result.assessed_managed_peak_mw != record.assessed_managed_peak_mw:
        return q("P26 assessed managed peak does not exactly match the P29 node-result peak")

    try:
        p26 = evaluate_limiting_node(
            record,
            topology_endpoint=topology_endpoint,
            survivability=node_result.legacy_p10_decision,
            screening=screening,
        )
    except B10LimitingNodeError as exc:
        return q(f"canonical P26 limiting-node gate rejected the exact P29 lineage: {exc}")

    if p26.status == Q_LIMITING_NODE_UNRESOLVED:
        return q("canonical P26 limiting/non-limiting node authority remains unresolved")
    if p26.status not in {LIMITING_NODE_PROVEN, NON_LIMITING_NODE_PROVEN}:
        raise B10LimitingNodeStudyLineageError("unexpected canonical P26 status")

    evidence_status = (
        "OBS"
        if survivability_study_result.evidence_status == "OBS"
        and node_result.evidence_status == "OBS"
        and p26.evidence_status == "OBS"
        else "DER"
    )
    status = (
        REAL_LIMITING_NODE_LINEAGE_PROVEN
        if p26.status == LIMITING_NODE_PROVEN
        else REAL_NON_LIMITING_NODE_LINEAGE_PROVEN
    )
    refs = tuple(sorted(set(refs) | set(p26.source_refs) | set(node_result.legacy_p10_decision.source_refs)))
    return LimitingNodeStudyLineageDecision(
        record.network_operator,
        record.network_study_id,
        record.study_case_id,
        record.horizon,
        record.node_region_id,
        REAL,
        status,
        evidence_status,
        node_result.survivability_result_id,
        p26,
        refs,
        (
            "the canonical P26 limiting/non-limiting conclusion consumes the exact P10 survivability "
            "node result carried by the complete P29 REAL study/case/horizon lineage"
        ),
    )


def require_real_limiting_node_lineage(
    decision: LimitingNodeStudyLineageDecision,
) -> str:
    if not isinstance(decision, LimitingNodeStudyLineageDecision):
        raise B10LimitingNodeStudyLineageError("decision must be LimitingNodeStudyLineageDecision")
    if decision.status != REAL_LIMITING_NODE_LINEAGE_PROVEN:
        raise B10LimitingNodeStudyLineageError("proven REAL limiting-node study lineage is required")
    return decision.node_region_id


__all__ = [
    "B10LimitingNodeStudyLineageError",
    "LimitingNodeStudyLineageDecision",
    "Q_REAL_LIMITING_NODE_LINEAGE_UNRESOLVED",
    "REAL_LIMITING_NODE_LINEAGE_PROVEN",
    "REAL_NON_LIMITING_NODE_LINEAGE_PROVEN",
    "evaluate_real_limiting_node_study_lineage",
    "require_real_limiting_node_lineage",
]
