"""B02-P57 hydraulic transition gate.

Current hydraulic readiness is not treated as a national precondition for heat-pump
eligibility. The relevant technical question is whether the finished heat-pump
system has an explicit hydraulic transition path and a design that can be
commissioned to the required operating conditions.

This module keeps the decision fail-closed:

CURRENT SYSTEM READY != FINISHED SYSTEM HYDRAULICALLY ADEQUATE
CURRENT SYSTEM NOT READY != DWELLING TECHNICALLY INELIGIBLE
REUSE / UPGRADE / REPLACE -> EXPLICIT FINISHED-SYSTEM DESIGN -> COMMISSIONING
"""

from __future__ import annotations

from dataclasses import dataclass
from math import isfinite


Q = "Q"
QUALIFIED = "QUALIFIED"
OBS = "OBS"
DER = "DER"
REAL_EVIDENCE = frozenset({OBS, DER})

REUSE_EXISTING_HYDRAULICS = "REUSE_EXISTING_HYDRAULICS"
UPGRADE_EXISTING_HYDRAULICS = "UPGRADE_EXISTING_HYDRAULICS"
REPLACE_DISTRIBUTION_HYDRAULICS = "REPLACE_DISTRIBUTION_HYDRAULICS"
HYDRAULIC_PATHS = frozenset(
    {
        REUSE_EXISTING_HYDRAULICS,
        UPGRADE_EXISTING_HYDRAULICS,
        REPLACE_DISTRIBUTION_HYDRAULICS,
    }
)


@dataclass(frozen=True)
class HydraulicTransitionCandidate:
    record_id: str
    transition_path: str
    current_system_survey_status: str
    current_topology_known: bool
    current_pipe_or_manifold_basis_known: bool
    required_design_flow_rate_l_s: float | None
    required_pump_head_pa: float | None
    system_volume_or_defrost_basis_documented: bool
    balancing_and_control_plan_documented: bool
    water_quality_flush_fill_plan_documented: bool
    commissioning_plan_documented: bool
    evidence_refs_present: bool
    reproducible_repository_binding: bool


@dataclass(frozen=True)
class HydraulicTransitionDecision:
    status: str
    reasons: tuple[str, ...]


def assess_hydraulic_transition(
    candidate: HydraulicTransitionCandidate,
) -> HydraulicTransitionDecision:
    """Assess whether a finished-system hydraulic transition is designable.

    Reuse and upgrade paths require explicit current-system survey evidence because
    they rely on retained distribution assets. A full replacement path does not
    require current hydraulic adequacy, but it still requires an explicit finished-
    system hydraulic design and commissioning plan.
    """

    reasons: list[str] = []

    if not candidate.record_id.strip():
        reasons.append("RECORD_ID_MISSING")

    if candidate.transition_path not in HYDRAULIC_PATHS:
        reasons.append("HYDRAULIC_TRANSITION_PATH_UNKNOWN")

    if candidate.transition_path in {
        REUSE_EXISTING_HYDRAULICS,
        UPGRADE_EXISTING_HYDRAULICS,
    }:
        if candidate.current_system_survey_status not in REAL_EVIDENCE:
            reasons.append("CURRENT_HYDRAULIC_SURVEY_NOT_OBS_OR_DER")
        if not candidate.current_topology_known:
            reasons.append("CURRENT_HYDRAULIC_TOPOLOGY_UNKNOWN")
        if not candidate.current_pipe_or_manifold_basis_known:
            reasons.append("CURRENT_PIPE_OR_MANIFOLD_BASIS_UNKNOWN")

    flow = candidate.required_design_flow_rate_l_s
    if flow is None or not isfinite(flow) or flow <= 0:
        reasons.append("REQUIRED_DESIGN_FLOW_RATE_INVALID")

    head = candidate.required_pump_head_pa
    if head is None or not isfinite(head) or head <= 0:
        reasons.append("REQUIRED_PUMP_HEAD_INVALID")

    if not candidate.system_volume_or_defrost_basis_documented:
        reasons.append("SYSTEM_VOLUME_OR_DEFROST_BASIS_MISSING")
    if not candidate.balancing_and_control_plan_documented:
        reasons.append("BALANCING_AND_CONTROL_PLAN_MISSING")
    if not candidate.water_quality_flush_fill_plan_documented:
        reasons.append("WATER_QUALITY_FLUSH_FILL_PLAN_MISSING")
    if not candidate.commissioning_plan_documented:
        reasons.append("COMMISSIONING_PLAN_MISSING")
    if not candidate.evidence_refs_present:
        reasons.append("EVIDENCE_REFS_MISSING")
    if not candidate.reproducible_repository_binding:
        reasons.append("NO_REPRODUCIBLE_REPOSITORY_BINDING")

    if reasons:
        return HydraulicTransitionDecision(Q, tuple(reasons))

    return HydraulicTransitionDecision(QUALIFIED, ())
