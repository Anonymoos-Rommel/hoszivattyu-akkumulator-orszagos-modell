"""Fail-closed admission gate for calibrated B02 linkage models.

B02-P12 does not approve or instantiate a statistical linkage model.  It only
specifies the minimum evidence and governance conditions that must be satisfied
before a calibrated model may be consumed by the P9 stock-archetype gate.
"""

from __future__ import annotations

from dataclasses import dataclass


Q = "Q"
QUALIFIED = "QUALIFIED"
APPROVED = "APPROVED"
JOSEPH = "JOSEPH"

ALLOWED_MODEL_OUTPUT_EVIDENCE = frozenset({"ASS", "MODELLED"})


@dataclass(frozen=True)
class LinkageModelDecision:
    status: str
    blockers: tuple[str, ...]


@dataclass(frozen=True)
class CalibratedLinkageModelInputs:
    model_id: str
    approval_status: str
    approval_authority: str
    calibration_source_ids: tuple[str, ...]
    calibration_reference_period_defined: bool
    target_grain_wbl_compatible: bool
    representativeness_diagnostics_present: bool
    validation_metrics_present: bool
    marginal_reconciliation_present: bool
    uncertainty_method_defined: bool
    uncertainty_propagation_required: bool
    independence_assumption_controlled: bool
    output_evidence_status: str


def assess_calibrated_linkage_model(
    inputs: CalibratedLinkageModelInputs,
) -> LinkageModelDecision:
    """Admit a calibrated linkage model only when every gate is explicit."""

    blockers: list[str] = []

    if not inputs.model_id.strip():
        blockers.append("NO_MODEL_ID")
    if inputs.approval_status != APPROVED or inputs.approval_authority != JOSEPH:
        blockers.append("NO_JOSEPH_APPROVAL")
    if not inputs.calibration_source_ids:
        blockers.append("NO_CALIBRATION_SOURCES")
    if not inputs.calibration_reference_period_defined:
        blockers.append("NO_CALIBRATION_REFERENCE_PERIOD")
    if not inputs.target_grain_wbl_compatible:
        blockers.append("TARGET_GRAIN_NOT_WBL_COMPATIBLE")
    if not inputs.representativeness_diagnostics_present:
        blockers.append("NO_REPRESENTATIVENESS_DIAGNOSTICS")
    if not inputs.validation_metrics_present:
        blockers.append("NO_VALIDATION_METRICS")
    if not inputs.marginal_reconciliation_present:
        blockers.append("NO_MARGINAL_RECONCILIATION")
    if not inputs.uncertainty_method_defined:
        blockers.append("NO_UNCERTAINTY_METHOD")
    if not inputs.uncertainty_propagation_required:
        blockers.append("NO_UNCERTAINTY_PROPAGATION")
    if not inputs.independence_assumption_controlled:
        blockers.append("UNCONTROLLED_INDEPENDENCE_ASSUMPTION")
    if inputs.output_evidence_status not in ALLOWED_MODEL_OUTPUT_EVIDENCE:
        blockers.append("MODEL_OUTPUT_EVIDENCE_INVALID")

    if blockers:
        return LinkageModelDecision(Q, tuple(blockers))
    return LinkageModelDecision(QUALIFIED, ())
