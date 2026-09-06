"""Predeclared uncertainty contract for calibrated B02 emitter linkage.

The contract defines the method before microdata are available. It never
reuses the full-sample 3.4% margin of error for the N=657 gas-heating subgroup
and never treats a weighted survey as simple random sampling by default.
"""

from __future__ import annotations

from dataclasses import dataclass

METHOD_ID = "B02-P29-DESIGN-AWARE-GAS-CONVECTOR-UNCERTAINTY"
ESTIMATOR = "HAJEK_WEIGHTED_PROPORTION"
PRIMARY_VARIANCE = "DESIGN_BASED_LINEARIZATION_OR_REPLICATE_WEIGHTS"
PROPAGATION = "MONTE_CARLO_FROM_ESTIMATED_COVARIANCE_WITH_0_1_BOUNDS"


@dataclass(frozen=True)
class UncertaintyExecutionDecision:
    method_defined: bool
    executable: bool
    blockers: tuple[str, ...]


def assess_uncertainty_execution(
    *,
    final_case_weights_available: bool,
    design_variables_available: bool,
    replicate_weights_available: bool,
) -> UncertaintyExecutionDecision:
    """Return whether the predeclared method can be executed on released data.

    Final weights are mandatory. Variance estimation additionally requires
    either design variables (for linearization) or valid replicate weights.
    Missing design information must not be replaced by an SRS/binomial CI.
    """
    blockers: list[str] = []
    if not final_case_weights_available:
        blockers.append("NO_FINAL_CASE_WEIGHTS")
    if not (design_variables_available or replicate_weights_available):
        blockers.append("NO_DESIGN_VARIANCE_INPUT")
    return UncertaintyExecutionDecision(
        method_defined=True,
        executable=not blockers,
        blockers=tuple(blockers),
    )
