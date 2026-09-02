"""B10-P12 fail-closed integration / closure assessment.

A bounded contract is not the same as populated real evidence, a populated
output, or a satisfied issue-closure gate.  P12 audits the current canonical B10
state and prevents the module from being marked closed merely because the
individual P1-P11 authority boundaries exist.
"""

from __future__ import annotations

from dataclasses import dataclass


class B10IntegrationClosureError(ValueError):
    """Raised when a closure assessment overstates current B10 readiness."""


B10_CLOSURE_BLOCKED = "B10_CLOSURE_BLOCKED"
B10_CLOSURE_READY = "B10_CLOSURE_READY"

CONTRACT_BOUNDED = "CONTRACT_BOUNDED"
PARTIALLY_BOUNDED = "PARTIALLY_BOUNDED"
Q_UNRESOLVED = "Q_UNRESOLVED"
LEGACY_LABEL_UNRESOLVED = "LEGACY_LABEL_UNRESOLVED"
ACCEPTANCE_SATISFIED = "ACCEPTANCE_SATISFIED"
OUTPUT_POPULATED = "OUTPUT_POPULATED"

GATE_STATUSES = {
    CONTRACT_BOUNDED,
    PARTIALLY_BOUNDED,
    Q_UNRESOLVED,
    LEGACY_LABEL_UNRESOLVED,
    ACCEPTANCE_SATISFIED,
    OUTPUT_POPULATED,
}

ACCEPTANCE_NETWORK_LAYER_SEPARATION = "TRANSMISSION_DISTRIBUTION_SEPARATION"
ACCEPTANCE_REGIONAL_PENETRATION_HOSTING = "REGIONAL_PENETRATION_AND_HOSTING"
ACCEPTANCE_MANAGED_PEAK_SURVIVABILITY = "MANAGED_PEAK_AND_PHYSICAL_SURVIVABILITY"
ACCEPTANCE_TIMED_INVESTMENT_PATHWAY = "TIMED_INVESTMENT_PATHWAY"
ACCEPTANCE_QUESTION_HANDLING = "LEGACY_Q05_Q07_HANDLING"

OUTPUT_REGIONAL_CAPEX = "REGIONAL_CAPEX"
OUTPUT_TIMING = "REGIONAL_TIMING"
OUTPUT_CONNECTION_DEMAND = "CONNECTION_DEMAND"
OUTPUT_LIMITING_NODES = "LIMITING_NODES"

CURRENT_CANONICAL_QUESTION_STATUSES = (
    ("Q-B01-002", "OPEN"),
    ("Q-B10-001", "OPEN"),
    ("Q-B10-002", "OPEN"),
)
CURRENT_LEGACY_ACCEPTANCE_LABELS = ("Q-05", "Q-07")


@dataclass(frozen=True)
class ClosureGateItem:
    gate_id: str
    status: str
    canonical_refs: tuple[str, ...]
    blocking_refs: tuple[str, ...]
    reason: str

    def __post_init__(self) -> None:
        if not isinstance(self.gate_id, str) or not self.gate_id.strip():
            raise B10IntegrationClosureError("gate_id is required")
        if self.status not in GATE_STATUSES:
            raise B10IntegrationClosureError("invalid closure gate status")
        if isinstance(self.canonical_refs, str) or not self.canonical_refs:
            raise B10IntegrationClosureError("canonical_refs must be non-empty")
        if any(not isinstance(ref, str) or not ref.strip() for ref in self.canonical_refs):
            raise B10IntegrationClosureError("canonical_refs cannot contain blanks")
        if isinstance(self.blocking_refs, str):
            raise B10IntegrationClosureError("blocking_refs must be a collection")
        if any(not isinstance(ref, str) or not ref.strip() for ref in self.blocking_refs):
            raise B10IntegrationClosureError("blocking_refs cannot contain blanks")
        if not isinstance(self.reason, str) or not self.reason.strip():
            raise B10IntegrationClosureError("reason is required")


@dataclass(frozen=True)
class B10ClosureAssessment:
    status: str
    module_status: str
    readiness_percent: int
    acceptance_gates: tuple[ClosureGateItem, ...]
    output_gates: tuple[ClosureGateItem, ...]
    canonical_question_statuses: tuple[tuple[str, str], ...]
    legacy_acceptance_labels: tuple[str, ...]
    blocking_refs: tuple[str, ...]
    issue_should_close: bool
    reason: str

    def __post_init__(self) -> None:
        if self.status not in {B10_CLOSURE_BLOCKED, B10_CLOSURE_READY}:
            raise B10IntegrationClosureError("invalid B10 closure status")
        if self.module_status not in {"IN_PROGRESS", "DONE"}:
            raise B10IntegrationClosureError("module_status must be IN_PROGRESS or DONE")
        if isinstance(self.readiness_percent, bool) or not isinstance(self.readiness_percent, int):
            raise B10IntegrationClosureError("readiness_percent must be an integer")
        if not 0 <= self.readiness_percent <= 100:
            raise B10IntegrationClosureError("readiness_percent must lie in [0,100]")
        if not self.acceptance_gates or not self.output_gates:
            raise B10IntegrationClosureError("closure assessment requires acceptance and output gates")
        if isinstance(self.legacy_acceptance_labels, str):
            raise B10IntegrationClosureError("legacy_acceptance_labels must be a collection")
        if self.status == B10_CLOSURE_READY:
            if self.module_status != "DONE" or not self.issue_should_close:
                raise B10IntegrationClosureError("closure-ready assessment must be DONE and issue-closeable")
            if self.blocking_refs:
                raise B10IntegrationClosureError("closure-ready assessment cannot carry blockers")
            if any(item.status != ACCEPTANCE_SATISFIED for item in self.acceptance_gates):
                raise B10IntegrationClosureError("all acceptance gates must be satisfied before closure")
            if any(item.status != OUTPUT_POPULATED for item in self.output_gates):
                raise B10IntegrationClosureError("all primary outputs must be populated before closure")
        else:
            if self.module_status != "IN_PROGRESS" or self.issue_should_close:
                raise B10IntegrationClosureError("blocked closure must remain IN_PROGRESS and keep the issue open")
            if not self.blocking_refs:
                raise B10IntegrationClosureError("blocked closure requires explicit blockers")


def current_b10_closure_assessment() -> B10ClosureAssessment:
    """Return the exact P12 audit of the current P1-P11 canonical B10 state.

    This function is deliberately state-specific.  A later evidence slice must
    change the assessment explicitly; no caller-supplied boolean can silently
    promote B10 to DONE.
    """

    acceptance = (
        ClosureGateItem(
            ACCEPTANCE_NETWORK_LAYER_SEPARATION,
            CONTRACT_BOUNDED,
            ("B10-P7", "modules/B10/network_layer_authority_contract.py"),
            (),
            "transmission, distribution and TSO/DSO interface authority are explicitly separated, but contract existence is not a complete national constraint inventory",
        ),
        ClosureGateItem(
            ACCEPTANCE_REGIONAL_PENETRATION_HOSTING,
            Q_UNRESOLVED,
            ("B10-P8", "B10-P9", "registry/regional_readiness.csv"),
            ("Q-B01-002", "NO_NATIONAL_DSO_COVERAGE", "REGIONAL_READINESS_HEADER_ONLY"),
            "administrative/service-area/exact-node boundaries are bounded, but no complete regional programme penetration plus hosting/readiness population exists",
        ),
        ClosureGateItem(
            ACCEPTANCE_MANAGED_PEAK_SURVIVABILITY,
            CONTRACT_BOUNDED,
            ("B10-P9", "B10-P10", "modules/B10/managed_flex_survivability_contract.py"),
            ("NO_REAL_PROGRAMME_NODE_PANEL", "NO_REAL_MANAGED_PEAK_SURVIVABILITY_STUDY"),
            "managed-load and survivability authority are separated, but no real programme panel plus claim-specific survivability study populates the national/regional model",
        ),
        ClosureGateItem(
            ACCEPTANCE_TIMED_INVESTMENT_PATHWAY,
            CONTRACT_BOUNDED,
            ("B10-P11", "modules/B10/timed_investment_pathway_contract.py"),
            ("Q-B10-001", "Q-B10-002", "NO_REAL_TIMED_PROGRAMME_CAPEX"),
            "delivery timing and CAPEX cash-flow timing are bounded, but there is no authoritative programme-incremental timed investment schedule",
        ),
        ClosureGateItem(
            ACCEPTANCE_QUESTION_HANDLING,
            LEGACY_LABEL_UNRESOLVED,
            ("docs/methodology/question_identifiers.md", "registry/open_questions.csv"),
            ("LEGACY:Q-05", "LEGACY:Q-07"),
            "Issue #10 uses non-canonical short labels Q-05 and Q-07; the repository forbids guessing a mapping for ambiguous legacy question labels",
        ),
    )

    outputs = (
        ClosureGateItem(
            OUTPUT_REGIONAL_CAPEX,
            Q_UNRESOLVED,
            ("B10-P3", "B10-P5", "B10-P11", "registry/incremental_capex_attribution.csv"),
            ("Q-B10-001", "INCREMENTAL_CAPEX_ATTRIBUTION_HEADER_ONLY"),
            "programme-incremental CAPEX authority exists as a gate but no regional numeric programme CAPEX ledger is populated",
        ),
        ClosureGateItem(
            OUTPUT_TIMING,
            Q_UNRESOLVED,
            ("B10-P6", "B10-P11"),
            ("Q-B10-002", "NO_REAL_TIMED_PROGRAMME_CAPEX"),
            "two baseline project timing examples do not constitute a forward regional programme timing pathway",
        ),
        ClosureGateItem(
            OUTPUT_CONNECTION_DEMAND,
            Q_UNRESOLVED,
            ("B10-P8", "B10-P9"),
            ("Q-B01-002", "NO_REAL_PROGRAMME_NODE_PANEL"),
            "exact-node programme-demand aggregation is executable but no complete real programme entity-by-timestamp panel is canonical",
        ),
        ClosureGateItem(
            OUTPUT_LIMITING_NODES,
            Q_UNRESOLVED,
            ("B10-P1", "B10-P2", "B10-P10"),
            ("NO_NATIONAL_DSO_COVERAGE", "NO_REAL_MANAGED_PEAK_SURVIVABILITY_STUDY"),
            "source-native headroom screening and survivability gates do not yet establish a complete set of binding programme nodes",
        ),
    )

    blockers = tuple(
        dict.fromkeys(
            ref
            for item in (*acceptance, *outputs)
            for ref in item.blocking_refs
        )
    )
    return B10ClosureAssessment(
        status=B10_CLOSURE_BLOCKED,
        module_status="IN_PROGRESS",
        readiness_percent=15,
        acceptance_gates=acceptance,
        output_gates=outputs,
        canonical_question_statuses=CURRENT_CANONICAL_QUESTION_STATUSES,
        legacy_acceptance_labels=CURRENT_LEGACY_ACCEPTANCE_LABELS,
        blocking_refs=blockers,
        issue_should_close=False,
        reason="P1-P11 establish fail-closed authority boundaries, but Issue #10 primary outputs and multiple evidence/identifier gates remain unresolved",
    )


def require_b10_closure_ready(assessment: B10ClosureAssessment) -> None:
    """Fail closed unless a future explicit assessment satisfies every gate."""
    if not isinstance(assessment, B10ClosureAssessment):
        raise B10IntegrationClosureError("assessment must be B10ClosureAssessment")
    if assessment.status != B10_CLOSURE_READY:
        raise B10IntegrationClosureError(
            "B10 closure is blocked; do not mark module DONE or close Issue #10"
        )


__all__ = [
    "ACCEPTANCE_MANAGED_PEAK_SURVIVABILITY",
    "ACCEPTANCE_NETWORK_LAYER_SEPARATION",
    "ACCEPTANCE_QUESTION_HANDLING",
    "ACCEPTANCE_REGIONAL_PENETRATION_HOSTING",
    "ACCEPTANCE_SATISFIED",
    "ACCEPTANCE_TIMED_INVESTMENT_PATHWAY",
    "B10_CLOSURE_BLOCKED",
    "B10_CLOSURE_READY",
    "B10ClosureAssessment",
    "B10IntegrationClosureError",
    "CONTRACT_BOUNDED",
    "CURRENT_CANONICAL_QUESTION_STATUSES",
    "CURRENT_LEGACY_ACCEPTANCE_LABELS",
    "ClosureGateItem",
    "LEGACY_LABEL_UNRESOLVED",
    "OUTPUT_CONNECTION_DEMAND",
    "OUTPUT_LIMITING_NODES",
    "OUTPUT_POPULATED",
    "OUTPUT_REGIONAL_CAPEX",
    "OUTPUT_TIMING",
    "PARTIALLY_BOUNDED",
    "Q_UNRESOLVED",
    "current_b10_closure_assessment",
    "require_b10_closure_ready",
]
