"""B10-P29 fail-closed REAL network-survivability study-result admission.

Core rules:

    REAL MANAGED-PEAK STUDY INPUT != SURVIVABILITY STUDY RESULT
    P10 NETWORK SURVIVABILITY != EXACT STUDY-CASE/HORIZON RESULT
    NUMERIC PEAK MATCH != RESULT-LINEAGE BINDING
    MISSING RESULT NODE != SURVIVABILITY
    SURVIVABILITY STUDY RESULT != LIMITING NODE
    SURVIVABILITY STUDY RESULT != REINFORCEMENT REQUIRED

P28 proves that exact REAL managed node peaks were admitted to one exact network
study/case/horizon. P10 can prove a node-level NETWORK_SURVIVABILITY claim bound
to operator, study id, exact DSO substation and assessed peak, but P10 predates
P28 and does not bind study-case id or horizon. P29 closes that lineage gap.

A P29 case is proven only when every exact P28 study-input node has one and only
one authoritative survivability result bound to the same study, case, horizon,
node and managed peak. Missing/extra nodes or coincidentally equal numbers remain Q.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import isfinite
from typing import Iterable

from .managed_flex_survivability_contract import (
    NETWORK_SURVIVABILITY,
    Q_NETWORK_SURVIVABILITY_UNRESOLVED,
    SURVIVABILITY_PROVEN,
    NetworkSurvivabilityDecision,
    NetworkSurvivabilityEvidence,
    NetworkSurvivabilityRecord,
    evaluate_network_survivability,
)
from .managed_peak_study_input_contract import (
    REAL_MANAGED_PEAK_STUDY_INPUT_PROVEN,
    ManagedPeakStudyInputDecision,
)


class B10SurvivabilityStudyResultError(ValueError):
    """Raised when network-survivability result lineage is ambiguous or overstated."""


NETWORK_SURVIVABILITY_STUDY_RESULT = "NETWORK_SURVIVABILITY_STUDY_RESULT"
REAL_SURVIVABILITY_STUDY_RESULT_PROVEN = "REAL_SURVIVABILITY_STUDY_RESULT_PROVEN"
Q_REAL_SURVIVABILITY_STUDY_RESULT_UNRESOLVED = "Q_REAL_SURVIVABILITY_STUDY_RESULT_UNRESOLVED"

REAL = "REAL"
EVIDENCE_STATUSES = {"OBS", "DER", "Q"}
DSO_SUBSTATION = "DSO_SUBSTATION"

RESULT_ID_PREFIX = "SURVIVABILITY_RESULT_ID:"
STUDY_INPUT_ID_PREFIX = "STUDY_INPUT_ID:"
NETWORK_OPERATOR_PREFIX = "NETWORK_OPERATOR:"
NETWORK_STUDY_ID_PREFIX = "NETWORK_STUDY_ID:"
STUDY_CASE_ID_PREFIX = "STUDY_CASE_ID:"
HORIZON_PREFIX = "HORIZON:"
TRUTH_CONTEXT_PREFIX = "TRUTH_CONTEXT:"
NODE_REGION_ID_PREFIX = "NODE_REGION_ID:"
NODE_REGION_GRAIN_BINDING = "NODE_REGION_GRAIN:DSO_SUBSTATION"
ASSESSED_MANAGED_PEAK_PREFIX = "ASSESSED_MANAGED_PEAK_MW:"

_RESULT_AUTHORITY_MAX_LEVEL = 2


def _text(value: str, name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise B10SurvivabilityStudyResultError(f"{name} is required")
    return value


def _peak(value: float) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not isfinite(value) or value < 0:
        raise B10SurvivabilityStudyResultError("assessed_managed_peak_mw must be finite and non-negative")
    return float(value)


@dataclass(frozen=True)
class SurvivabilityStudyResultEvidence:
    source_id: str
    authority_level: int
    truth_status: str
    supports: tuple[str, ...]

    def __post_init__(self) -> None:
        _text(self.source_id, "source_id")
        if self.authority_level not in {1, 2, 3, 4, 5}:
            raise B10SurvivabilityStudyResultError("authority_level must be 1..5")
        if self.truth_status not in EVIDENCE_STATUSES:
            raise B10SurvivabilityStudyResultError("truth_status must be OBS, DER or Q")
        if isinstance(self.supports, str):
            raise B10SurvivabilityStudyResultError("supports must be a collection")
        if any(not isinstance(item, str) or not item.strip() for item in self.supports):
            raise B10SurvivabilityStudyResultError("supports cannot contain blanks")


@dataclass(frozen=True)
class SurvivabilityStudyResultRecord:
    survivability_result_id: str
    study_input_id: str
    network_operator: str
    network_study_id: str
    study_case_id: str
    horizon: str
    node_region_id: str
    assessed_managed_peak_mw: float
    source_refs: tuple[str, ...]
    evidence: tuple[SurvivabilityStudyResultEvidence, ...]
    truth_context: str = REAL
    node_region_scheme: str = DSO_SUBSTATION

    def __post_init__(self) -> None:
        for name in (
            "survivability_result_id",
            "study_input_id",
            "network_operator",
            "network_study_id",
            "study_case_id",
            "horizon",
            "node_region_id",
        ):
            _text(getattr(self, name), name)
        if self.truth_context != REAL:
            raise B10SurvivabilityStudyResultError("P29 admits REAL survivability results only")
        if self.node_region_scheme != DSO_SUBSTATION:
            raise B10SurvivabilityStudyResultError("survivability result must remain at DSO_SUBSTATION grain")
        object.__setattr__(self, "assessed_managed_peak_mw", _peak(self.assessed_managed_peak_mw))
        if isinstance(self.source_refs, str) or not self.source_refs:
            raise B10SurvivabilityStudyResultError("source_refs must be non-empty")
        if any(not isinstance(ref, str) or not ref.strip() for ref in self.source_refs):
            raise B10SurvivabilityStudyResultError("source_refs cannot contain blanks")
        if isinstance(self.evidence, str) or not self.evidence:
            raise B10SurvivabilityStudyResultError("evidence must be non-empty")
        evidence_ids = {item.source_id for item in self.evidence}
        if not set(self.source_refs).issubset(evidence_ids):
            raise B10SurvivabilityStudyResultError("source_refs must identify supplied evidence")

    @property
    def referenced_evidence(self) -> tuple[SurvivabilityStudyResultEvidence, ...]:
        refs = set(self.source_refs)
        return tuple(item for item in self.evidence if item.source_id in refs)


@dataclass(frozen=True)
class SurvivabilityStudyNodeResult:
    survivability_result_id: str
    node_region_id: str
    assessed_managed_peak_mw: float
    evidence_status: str
    legacy_p10_decision: NetworkSurvivabilityDecision

    def __post_init__(self) -> None:
        _text(self.survivability_result_id, "survivability_result_id")
        _text(self.node_region_id, "node_region_id")
        object.__setattr__(self, "assessed_managed_peak_mw", _peak(self.assessed_managed_peak_mw))
        if self.evidence_status not in {"OBS", "DER"}:
            raise B10SurvivabilityStudyResultError("proven node result evidence_status must be OBS or DER")
        if not isinstance(self.legacy_p10_decision, NetworkSurvivabilityDecision):
            raise B10SurvivabilityStudyResultError("legacy_p10_decision must be NetworkSurvivabilityDecision")
        if self.legacy_p10_decision.status != SURVIVABILITY_PROVEN:
            raise B10SurvivabilityStudyResultError("node result requires a P10 SURVIVABILITY_PROVEN decision")
        if self.legacy_p10_decision.node_region_id != self.node_region_id:
            raise B10SurvivabilityStudyResultError("P10 survivability node must match P29 node")
        if self.legacy_p10_decision.assessed_managed_peak_mw != self.assessed_managed_peak_mw:
            raise B10SurvivabilityStudyResultError("P10 survivability peak must match P29 peak")


@dataclass(frozen=True)
class SurvivabilityStudyResultDecision:
    study_input_id: str
    network_operator: str
    network_study_id: str
    study_case_id: str
    horizon: str
    truth_context: str
    status: str
    evidence_status: str
    node_results: tuple[SurvivabilityStudyNodeResult, ...]
    expected_node_count: int
    actual_node_count: int
    missing_node_ids: tuple[str, ...]
    extra_node_ids: tuple[str, ...]
    source_refs: tuple[str, ...]
    reason: str

    def __post_init__(self) -> None:
        if self.status not in {
            REAL_SURVIVABILITY_STUDY_RESULT_PROVEN,
            Q_REAL_SURVIVABILITY_STUDY_RESULT_UNRESOLVED,
        }:
            raise B10SurvivabilityStudyResultError("invalid survivability study-result status")
        if self.truth_context != REAL:
            raise B10SurvivabilityStudyResultError("P29 decision must preserve REAL truth context")
        if self.status == REAL_SURVIVABILITY_STUDY_RESULT_PROVEN:
            if self.evidence_status not in {"OBS", "DER"}:
                raise B10SurvivabilityStudyResultError("proven study result requires OBS/DER evidence")
            if not self.node_results:
                raise B10SurvivabilityStudyResultError("proven study result requires node results")
            if self.expected_node_count != self.actual_node_count:
                raise B10SurvivabilityStudyResultError("proven study result requires complete node coverage")
            if self.missing_node_ids or self.extra_node_ids:
                raise B10SurvivabilityStudyResultError("proven study result cannot carry node-set gaps")
        else:
            if self.evidence_status != "Q":
                raise B10SurvivabilityStudyResultError("Q study result must preserve Q evidence status")
            if self.node_results:
                raise B10SurvivabilityStudyResultError("Q study result must withhold proven node results")


def _required(record: SurvivabilityStudyResultRecord) -> set[str]:
    return {
        NETWORK_SURVIVABILITY_STUDY_RESULT,
        NETWORK_SURVIVABILITY,
        f"{RESULT_ID_PREFIX}{record.survivability_result_id}",
        f"{STUDY_INPUT_ID_PREFIX}{record.study_input_id}",
        f"{NETWORK_OPERATOR_PREFIX}{record.network_operator}",
        f"{NETWORK_STUDY_ID_PREFIX}{record.network_study_id}",
        f"{STUDY_CASE_ID_PREFIX}{record.study_case_id}",
        f"{HORIZON_PREFIX}{record.horizon}",
        f"{TRUTH_CONTEXT_PREFIX}{record.truth_context}",
        f"{NODE_REGION_ID_PREFIX}{record.node_region_id}",
        NODE_REGION_GRAIN_BINDING,
        f"{ASSESSED_MANAGED_PEAK_PREFIX}{record.assessed_managed_peak_mw}",
    }


def _qualifying(record: SurvivabilityStudyResultRecord) -> tuple[SurvivabilityStudyResultEvidence, ...]:
    required = _required(record)
    return tuple(
        item
        for item in record.referenced_evidence
        if item.authority_level <= _RESULT_AUTHORITY_MAX_LEVEL
        and item.truth_status in {"OBS", "DER"}
        and required.issubset(set(item.supports))
    )


def _legacy_p10(record: SurvivabilityStudyResultRecord) -> NetworkSurvivabilityDecision:
    evidence = tuple(
        NetworkSurvivabilityEvidence(
            source_id=item.source_id,
            authority_level=item.authority_level,
            truth_status=item.truth_status,
            supports=item.supports,
        )
        for item in record.referenced_evidence
    )
    legacy = NetworkSurvivabilityRecord(
        network_operator=record.network_operator,
        network_study_id=record.network_study_id,
        node_region_id=record.node_region_id,
        assessed_managed_peak_mw=record.assessed_managed_peak_mw,
        source_refs=record.source_refs,
        evidence=evidence,
    )
    return evaluate_network_survivability(legacy)


def certify_real_survivability_study_result(
    study_input: ManagedPeakStudyInputDecision,
    records: Iterable[SurvivabilityStudyResultRecord],
) -> SurvivabilityStudyResultDecision:
    """Admit a complete REAL survivability result set for the exact P28 study case.

    The result set must cover exactly every P28 study-input node. Every result must
    carry claim-specific authority for the same study-input id, operator, study id,
    study-case id, horizon, node and exact assessed managed peak. P10 is re-used as
    the node-level survivability authority gate; P29 adds the missing case/horizon
    lineage and complete node-set requirement.
    """

    if not isinstance(study_input, ManagedPeakStudyInputDecision):
        raise B10SurvivabilityStudyResultError("study_input must be ManagedPeakStudyInputDecision")
    values = tuple(records)
    if any(not isinstance(item, SurvivabilityStudyResultRecord) for item in values):
        raise B10SurvivabilityStudyResultError("all records must be SurvivabilityStudyResultRecord")

    expected_nodes = {item.node_region_id: item.assessed_managed_peak_mw for item in study_input.nodes}
    actual_nodes = {item.node_region_id for item in values}
    missing = tuple(sorted(set(expected_nodes) - actual_nodes))
    extra = tuple(sorted(actual_nodes - set(expected_nodes)))
    refs = tuple(sorted(set(study_input.source_refs) | {ref for item in values for ref in item.source_refs}))

    def q(reason: str) -> SurvivabilityStudyResultDecision:
        return SurvivabilityStudyResultDecision(
            study_input.study_input_id,
            study_input.network_operator,
            study_input.network_study_id,
            study_input.study_case_id,
            study_input.horizon,
            REAL,
            Q_REAL_SURVIVABILITY_STUDY_RESULT_UNRESOLVED,
            "Q",
            (),
            len(expected_nodes),
            len(actual_nodes),
            missing,
            extra,
            refs,
            reason,
        )

    if study_input.status != REAL_MANAGED_PEAK_STUDY_INPUT_PROVEN:
        return q("P28 REAL managed-peak study input is not proven")
    if study_input.truth_context != REAL or not expected_nodes:
        return q("P28 input must preserve a non-empty REAL exact-node study-input set")
    if not values:
        return q("no survivability result records were supplied for the proven P28 study input")
    if len(actual_nodes) != len(values):
        return q("duplicate survivability result records for the same exact study-input node are rejected")
    if missing or extra:
        return q("survivability result node set does not exactly equal the P28 managed-peak study-input node set")

    node_results: list[SurvivabilityStudyNodeResult] = []
    for record in values:
        identity_pairs = (
            (record.study_input_id, study_input.study_input_id, "study_input_id"),
            (record.network_operator, study_input.network_operator, "network_operator"),
            (record.network_study_id, study_input.network_study_id, "network_study_id"),
            (record.study_case_id, study_input.study_case_id, "study_case_id"),
            (record.horizon, study_input.horizon, "horizon"),
        )
        for record_value, input_value, name in identity_pairs:
            if record_value != input_value:
                return q(f"survivability result {name} does not match the proven P28 study input")
        expected_peak = expected_nodes[record.node_region_id]
        if record.assessed_managed_peak_mw != expected_peak:
            return q("survivability result managed peak does not exactly match the proven P28 node peak")

        matches = _qualifying(record)
        if not matches:
            return q(
                "one or more exact node results lack authoritative study-input/study/case/horizon/peak survivability binding"
            )
        legacy = _legacy_p10(record)
        if legacy.status != SURVIVABILITY_PROVEN:
            if legacy.status != Q_NETWORK_SURVIVABILITY_UNRESOLVED:
                raise B10SurvivabilityStudyResultError("unexpected P10 survivability status")
            return q("P10 node-level network-survivability authority remains unresolved")
        status = "OBS" if all(item.truth_status == "OBS" for item in matches) and legacy.evidence_status == "OBS" else "DER"
        node_results.append(
            SurvivabilityStudyNodeResult(
                survivability_result_id=record.survivability_result_id,
                node_region_id=record.node_region_id,
                assessed_managed_peak_mw=record.assessed_managed_peak_mw,
                evidence_status=status,
                legacy_p10_decision=legacy,
            )
        )

    evidence_status = (
        "OBS"
        if study_input.evidence_status == "OBS"
        and node_results
        and all(item.evidence_status == "OBS" for item in node_results)
        else "DER"
    )
    return SurvivabilityStudyResultDecision(
        study_input.study_input_id,
        study_input.network_operator,
        study_input.network_study_id,
        study_input.study_case_id,
        study_input.horizon,
        REAL,
        REAL_SURVIVABILITY_STUDY_RESULT_PROVEN,
        evidence_status,
        tuple(sorted(node_results, key=lambda item: item.node_region_id)),
        len(expected_nodes),
        len(actual_nodes),
        (),
        (),
        refs,
        (
            "every exact P28 managed-peak study-input node has one authoritative P10-compatible "
            "survivability result bound to the same study input, study case, horizon and peak"
        ),
    )


def require_real_survivability_study_result(
    decision: SurvivabilityStudyResultDecision,
) -> tuple[SurvivabilityStudyNodeResult, ...]:
    if not isinstance(decision, SurvivabilityStudyResultDecision):
        raise B10SurvivabilityStudyResultError("decision must be SurvivabilityStudyResultDecision")
    if decision.status != REAL_SURVIVABILITY_STUDY_RESULT_PROVEN:
        raise B10SurvivabilityStudyResultError("proven REAL survivability study result is required")
    return decision.node_results


def require_survivability_node_result(
    decision: SurvivabilityStudyResultDecision,
    node_region_id: str,
) -> NetworkSurvivabilityDecision:
    _text(node_region_id, "node_region_id")
    values = require_real_survivability_study_result(decision)
    matches = [item for item in values if item.node_region_id == node_region_id]
    if len(matches) != 1:
        raise B10SurvivabilityStudyResultError("exact survivability node result is not uniquely proven")
    return matches[0].legacy_p10_decision


__all__ = [
    "B10SurvivabilityStudyResultError",
    "NETWORK_SURVIVABILITY_STUDY_RESULT",
    "Q_REAL_SURVIVABILITY_STUDY_RESULT_UNRESOLVED",
    "REAL_SURVIVABILITY_STUDY_RESULT_PROVEN",
    "SurvivabilityStudyNodeResult",
    "SurvivabilityStudyResultDecision",
    "SurvivabilityStudyResultEvidence",
    "SurvivabilityStudyResultRecord",
    "certify_real_survivability_study_result",
    "require_real_survivability_study_result",
    "require_survivability_node_result",
]
