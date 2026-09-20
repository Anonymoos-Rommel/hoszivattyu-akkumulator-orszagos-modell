"""B02/B06-P60 linked S1 demand-outcome gate.

S1 is a record/intervention completion state, not a national current-stock field.
A real S0 -> S1 transition requires a linked before/after outcome with explicit
epistemic authority, or an explicit source-backed NOT_REQUIRED decision.

NATIONAL OUTCOME DATASET != REQUIRED FOR EVERY RECORD
INTERVENTION COMPLETION != DEMAND REDUCTION PROVEN
MISSING OUTCOME != ZERO SAVING
MEASURED BEFORE/AFTER != CERTIFIED CALCULATION BEFORE/AFTER
"""

from __future__ import annotations

from dataclasses import dataclass
from math import isfinite


Q = "Q"
READY = "READY"
BLOCKED = "BLOCKED"

OBS = "OBS"
DER = "DER"
REAL_EVIDENCE = frozenset({OBS, DER})

MEASURED_USAGE = "MEASURED_USAGE"
CERTIFIED_CALCULATION = "CERTIFIED_CALCULATION"
NOT_REQUIRED = "NOT_REQUIRED"
OUTCOME_KINDS = frozenset({MEASURED_USAGE, CERTIFIED_CALCULATION, NOT_REQUIRED})


@dataclass(frozen=True)
class S1DemandOutcomeEvidence:
    record_id: str
    intervention_id: str
    evidence_kind: str
    evidence_status: str
    phase_link_id: str
    before_value: float | None = None
    after_value: float | None = None
    before_metric_id: str = ""
    after_metric_id: str = ""
    before_unit: str = ""
    after_unit: str = ""
    before_method_id: str = ""
    after_method_id: str = ""
    before_source_refs: tuple[str, ...] = ()
    after_source_refs: tuple[str, ...] = ()
    normalization_basis_documented: bool = False
    end_use_scope_documented: bool = False
    minimum_reduction_fraction: float | None = None
    not_required_reason: str = ""
    not_required_authority_refs: tuple[str, ...] = ()


@dataclass(frozen=True)
class S1DemandOutcomeDecision:
    status: str
    evidence_status: str
    reduction_fraction: float | None
    reasons: tuple[str, ...]


def _nonempty_refs(refs: tuple[str, ...]) -> bool:
    return bool(refs) and all(isinstance(ref, str) and ref.strip() for ref in refs)


def assess_s1_demand_outcome(
    evidence: S1DemandOutcomeEvidence,
) -> S1DemandOutcomeDecision:
    """Assess one record-linked S1 demand-reduction completion outcome."""

    reasons: list[str] = []

    if not evidence.record_id.strip():
        reasons.append("RECORD_ID_MISSING")
    if not evidence.intervention_id.strip():
        reasons.append("INTERVENTION_ID_MISSING")
    if not evidence.phase_link_id.strip():
        reasons.append("PHASE_LINK_ID_MISSING")
    if evidence.evidence_kind not in OUTCOME_KINDS:
        reasons.append("OUTCOME_KIND_UNKNOWN")
    if evidence.evidence_status not in REAL_EVIDENCE:
        reasons.append("OUTCOME_EVIDENCE_NOT_OBS_OR_DER")

    if evidence.minimum_reduction_fraction is not None:
        threshold = evidence.minimum_reduction_fraction
        if not isfinite(threshold) or not 0 <= threshold <= 1:
            reasons.append("MINIMUM_REDUCTION_FRACTION_INVALID")

    if evidence.evidence_kind == NOT_REQUIRED:
        if not evidence.not_required_reason.strip():
            reasons.append("NOT_REQUIRED_REASON_MISSING")
        if not _nonempty_refs(evidence.not_required_authority_refs):
            reasons.append("NOT_REQUIRED_AUTHORITY_MISSING")
        if evidence.before_value is not None or evidence.after_value is not None:
            reasons.append("NOT_REQUIRED_MUST_NOT_CARRY_SYNTHETIC_OUTCOME_VALUES")
        if reasons:
            return S1DemandOutcomeDecision(Q, Q, None, tuple(reasons))
        return S1DemandOutcomeDecision(
            READY, evidence.evidence_status, None, ()
        )

    before = evidence.before_value
    after = evidence.after_value
    if before is None or after is None:
        reasons.append("LINKED_BEFORE_AFTER_VALUES_MISSING")
    elif (
        not isfinite(before)
        or not isfinite(after)
        or before <= 0
        or after < 0
    ):
        reasons.append("LINKED_BEFORE_AFTER_VALUES_INVALID")

    for before_text, after_text, reason in (
        (evidence.before_metric_id, evidence.after_metric_id, "METRIC_ID_MISMATCH"),
        (evidence.before_unit, evidence.after_unit, "UNIT_MISMATCH"),
        (evidence.before_method_id, evidence.after_method_id, "METHOD_ID_MISMATCH"),
    ):
        if not before_text.strip() or not after_text.strip():
            reasons.append(reason.replace("MISMATCH", "MISSING"))
        elif before_text.strip() != after_text.strip():
            reasons.append(reason)

    if not _nonempty_refs(evidence.before_source_refs):
        reasons.append("BEFORE_SOURCE_REFS_MISSING")
    if not _nonempty_refs(evidence.after_source_refs):
        reasons.append("AFTER_SOURCE_REFS_MISSING")
    if not evidence.end_use_scope_documented:
        reasons.append("END_USE_SCOPE_NOT_DOCUMENTED")

    if evidence.evidence_kind == MEASURED_USAGE:
        if evidence.evidence_status != OBS:
            reasons.append("MEASURED_USAGE_REQUIRES_OBS")
        if not evidence.normalization_basis_documented:
            reasons.append("MEASURED_USAGE_NORMALIZATION_MISSING")
    elif evidence.evidence_kind == CERTIFIED_CALCULATION:
        if evidence.evidence_status != DER:
            reasons.append("CERTIFIED_CALCULATION_REQUIRES_DER")

    if reasons:
        return S1DemandOutcomeDecision(Q, Q, None, tuple(reasons))

    assert before is not None and after is not None
    reduction = (before - after) / before

    if reduction <= 0:
        return S1DemandOutcomeDecision(
            BLOCKED,
            evidence.evidence_status,
            reduction,
            ("DEMAND_REDUCTION_NOT_ACHIEVED",),
        )

    threshold = evidence.minimum_reduction_fraction
    if threshold is not None and reduction + 1e-12 < threshold:
        return S1DemandOutcomeDecision(
            BLOCKED,
            evidence.evidence_status,
            reduction,
            ("MINIMUM_DEMAND_REDUCTION_NOT_ACHIEVED",),
        )

    return S1DemandOutcomeDecision(
        READY,
        evidence.evidence_status,
        reduction,
        (),
    )
