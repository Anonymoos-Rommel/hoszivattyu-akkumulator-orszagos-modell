"""Fail-closed B10 integration / closure assessment.

A bounded contract is not the same as populated real evidence, a populated
output, or a satisfied issue-closure gate. P12 introduced the closure audit;
P13 resolved the source-scoped Issue #10 legacy Q-05/Q-07 identifier ambiguity.
P14 proved the current six-operator Hungarian electricity DSO inventory and the
DSO_SERVICE_AREA network-regional grain. P15 separates KSH settlement identity,
whole-settlement DSO membership and partial-settlement usage-location authority.
P16 separates a node-bearing publication from complete operator node inventory.
P17 refines operator-specific node-source discovery blockers. P18 separates
public source access and external snapshot verification from reuse clearance and
public-repository node-set materialization. P19 restores attributed public-node-
fact use without promoting those facts to a complete inventory. P23 pinned the
current MVM Emasz consumption node-bearing source. P34 pins the current E.ON
Szabad kapacitas publication page for ELMU, EDASZ and DDASZ through the joint
ENTSO-E / EU DSO Entity Capacitypedia E.On Hungary DSO submission. All six DSO
rows now have bounded consumption-side node-bearing sources, while national
inventory completeness, repository materialization and programme-specific
outputs remain unresolved.
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
class LegacyAcceptanceMapping:
    consumer_context: str
    legacy_label: str
    source_locator: str
    canonical_refs: tuple[str, ...]
    excluded_conflicts: tuple[str, ...]

    def __post_init__(self) -> None:
        for name in ("consumer_context", "legacy_label", "source_locator"):
            value = getattr(self, name)
            if not isinstance(value, str) or not value.strip():
                raise B10IntegrationClosureError(f"{name} is required")
        if not self.legacy_label.startswith("Q-"):
            raise B10IntegrationClosureError("legacy_label must preserve the source Q-xx label")
        if isinstance(self.canonical_refs, str) or not self.canonical_refs:
            raise B10IntegrationClosureError("canonical_refs must be a non-empty collection")
        if any(not isinstance(ref, str) or not ref.strip() for ref in self.canonical_refs):
            raise B10IntegrationClosureError("canonical_refs cannot contain blanks")
        if isinstance(self.excluded_conflicts, str):
            raise B10IntegrationClosureError("excluded_conflicts must be a collection")
        if any(not isinstance(ref, str) or not ref.strip() for ref in self.excluded_conflicts):
            raise B10IntegrationClosureError("excluded_conflicts cannot contain blanks")


CURRENT_LEGACY_ACCEPTANCE_MAPPINGS = (
    LegacyAcceptanceMapping(
        consumer_context="GITHUB_ISSUE_10_B10",
        legacy_label="Q-05",
        source_locator="V1.1_SECTION_6_B08_LOCAL_Q05",
        canonical_refs=("B10-P10", "NO_REAL_MANAGED_PEAK_SURVIVABILITY_STUDY"),
        excluded_conflicts=(),
    ),
    LegacyAcceptanceMapping(
        consumer_context="GITHUB_ISSUE_10_B10",
        legacy_label="Q-07",
        source_locator="V1.1_SECTION_23_FIRST_ROUND_Q07",
        canonical_refs=("Q-B01-002", "Q-B10-001", "Q-B10-002", "B10-P11"),
        excluded_conflicts=("V1.1_SECTION_11_B14_LOCAL_Q07_FINANCING",),
    ),
)


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
    legacy_acceptance_mappings: tuple[LegacyAcceptanceMapping, ...]
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
        if isinstance(self.legacy_acceptance_mappings, str):
            raise B10IntegrationClosureError("legacy_acceptance_mappings must be a collection")
        mapped_labels = tuple(item.legacy_label for item in self.legacy_acceptance_mappings)
        if len(mapped_labels) != len(set(mapped_labels)):
            raise B10IntegrationClosureError("legacy acceptance labels must map exactly once per consumer context")
        if set(mapped_labels) != set(self.legacy_acceptance_labels):
            raise B10IntegrationClosureError("every current legacy acceptance label requires an explicit scoped mapping")
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
    """Return the exact P34 audit of the current canonical B10 state.

    P34 clears the three exact E.ON publication-URL discovery blockers by pinning
    one current E.ON consumption-capacity page whose DSO-submitted Capacitypedia
    metadata explicitly covers ELMU, EDASZ and DDASZ at nodal HV/MV granularity.
    This source resolution does not prove exhaustive inventory, repository
    materialization, topology or any programme-specific output.
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
            (
                "B10-P8",
                "B10-P9",
                "B10-P14",
                "B10-P15",
                "registry/dso_service_area_inventory.csv",
                "registry/dso_service_area_membership_crosswalk.csv",
                "registry/regional_readiness.csv",
            ),
            (
                "Q-B01-002",
                "NO_COMPLETE_KSH_DSO_MEMBERSHIP_CROSSWALK",
                "PARTIAL_SETTLEMENT_USAGE_LOCATION_RESOLUTION_REQUIRED",
                "REGIONAL_READINESS_HEADER_ONLY",
            ),
            "the six DSO operators and DSO_SERVICE_AREA grain are bounded and P15 defines fail-closed membership semantics, but the normalized KSH-to-DSO crosswalk and partial-settlement usage-location resolution are not nationally populated",
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
            ACCEPTANCE_SATISFIED,
            ("B10-P13", "docs/methodology/question_identifiers.md", "docs/source_packs/P13_B10_LEGACY_QUESTION_MAPPING.md"),
            (),
            "Issue #10 Q-05 and Q-07 are source-scoped to exact V1.1 question semantics; identifier handling is satisfied without treating the short labels as global IDs or resolving their substantive evidence gaps",
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
            ("B10-P8", "B10-P9", "B10-P14", "B10-P15"),
            ("Q-B01-002", "NO_REAL_PROGRAMME_NODE_PANEL"),
            "service-area membership authority is bounded before exact-node aggregation, but no complete real programme entity-by-timestamp exact-node panel is canonical",
        ),
        ClosureGateItem(
            OUTPUT_LIMITING_NODES,
            Q_UNRESOLVED,
            (
                "B10-P1",
                "B10-P2",
                "B10-P10",
                "B10-P14",
                "B10-P15",
                "B10-P16",
                "B10-P17",
                "B10-P18",
                "B10-P19",
                "B10-P23",
                "B10-P34",
                "registry/dso_node_inventory_sources.csv",
                "registry/dso_consumption_publication_authorities.csv",
                "registry/dso_published_node_facts.csv",
                "registry/dso_published_node_facts_p23.csv",
                "registry/dso_published_node_set_materialization.csv",
                "registry/dso_node_inventory.csv",
            ),
            (
                "NO_COMPLETE_NATIONAL_DSO_NODE_INVENTORY",
                "PUBLISHED_NODE_SET_REPOSITORY_MATERIALIZATION_BLOCKED",
                "HEADROOM_NODE_SET_NOT_INVENTORY_COMPLETENESS",
                "NO_REAL_MANAGED_PEAK_SURVIVABILITY_STUDY",
            ),
            "P34 pins current consumption-side node-bearing publication sources for all six DSO operators, but bounded headroom node sets still do not prove exhaustive operator inventories, complete topology or binding programme nodes",
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
        legacy_acceptance_mappings=CURRENT_LEGACY_ACCEPTANCE_MAPPINGS,
        blocking_refs=blockers,
        issue_should_close=False,
        reason="P1-P34 establish fail-closed B10 boundaries and progressively stronger source coverage; P34 clears the three exact E.ON 2026 publication-URL blockers, while national membership/node completeness, repository materialization and programme-specific output evidence remain unresolved",
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
    "CURRENT_LEGACY_ACCEPTANCE_MAPPINGS",
    "ClosureGateItem",
    "LEGACY_LABEL_UNRESOLVED",
    "LegacyAcceptanceMapping",
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
