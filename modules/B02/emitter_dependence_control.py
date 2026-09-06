"""Fail-closed dependence control for B02 emitter linkage candidates.

B02-P37 separates two questions that must not be conflated:

1. Is the building-type / emitter dependence explicitly controlled?
2. Are exact numeric joint cells available for executable cell assignment?

A same-record observed joint can close the first question while the second remains
non-executable. This prevents silent independent-marginal cross-products without
fabricating cell percentages that are not publicly released.
"""

from __future__ import annotations

from dataclasses import dataclass


Q = "Q"
CONTROLLED = "CONTROLLED"
EXECUTABLE = "EXECUTABLE"
NOT_EXECUTABLE = "NOT_EXECUTABLE"


@dataclass(frozen=True)
class EmitterDependenceControlInputs:
    control_id: str
    survey_source_id: str
    joint_publication_source_id: str
    reference_period: str
    building_type_variable: str
    emitter_variable: str
    target_emitter_code: str
    same_household_record: bool
    weighted_by_building_type: bool
    observed_joint_published: bool
    silent_cross_product_forbidden: bool
    historical_prior_override_forbidden: bool
    exact_numeric_joint_cells_available: bool


@dataclass(frozen=True)
class EmitterDependenceControlDecision:
    control_status: str
    control_blockers: tuple[str, ...]
    numeric_execution_status: str
    numeric_execution_blockers: tuple[str, ...]

    @property
    def independence_assumption_controlled(self) -> bool:
        return self.control_status == CONTROLLED


def assess_emitter_dependence_control(
    inputs: EmitterDependenceControlInputs,
) -> EmitterDependenceControlDecision:
    """Control dependence only with an explicit same-record observed-joint route."""

    blockers: list[str] = []

    if not inputs.control_id.strip():
        blockers.append("NO_CONTROL_ID")
    if not inputs.survey_source_id.strip():
        blockers.append("NO_SURVEY_SOURCE")
    if not inputs.joint_publication_source_id.strip():
        blockers.append("NO_JOINT_PUBLICATION_SOURCE")
    if not inputs.reference_period.strip():
        blockers.append("NO_REFERENCE_PERIOD")
    if not inputs.building_type_variable.strip():
        blockers.append("NO_BUILDING_TYPE_VARIABLE")
    if not inputs.emitter_variable.strip():
        blockers.append("NO_EMITTER_VARIABLE")
    if not inputs.target_emitter_code.strip():
        blockers.append("NO_TARGET_EMITTER_CODE")
    if not inputs.same_household_record:
        blockers.append("NO_SAME_RECORD_JOINT")
    if not inputs.weighted_by_building_type:
        blockers.append("NO_BUILDING_TYPE_WEIGHT_CONTROL")
    if not inputs.observed_joint_published:
        blockers.append("NO_OBSERVED_JOINT_PUBLICATION")
    if not inputs.silent_cross_product_forbidden:
        blockers.append("SILENT_CROSS_PRODUCT_NOT_FORBIDDEN")
    if not inputs.historical_prior_override_forbidden:
        blockers.append("HISTORICAL_PRIOR_CAN_OVERRIDE_CURRENT_JOINT")

    control_status = CONTROLLED if not blockers else Q

    numeric_blockers: list[str] = []
    if control_status != CONTROLLED:
        numeric_blockers.append("DEPENDENCE_CONTROL_NOT_QUALIFIED")
    if not inputs.exact_numeric_joint_cells_available:
        numeric_blockers.append("NO_EXACT_NUMERIC_JOINT_CELLS")

    numeric_status = EXECUTABLE if not numeric_blockers else NOT_EXECUTABLE

    return EmitterDependenceControlDecision(
        control_status=control_status,
        control_blockers=tuple(blockers),
        numeric_execution_status=numeric_status,
        numeric_execution_blockers=tuple(numeric_blockers),
    )
