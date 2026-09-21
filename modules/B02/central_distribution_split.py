"""B02-P73 central-heating latent distribution split.

P72 fixes the canonical B02 transition denominator at 3,389,817 non-district
occupied dwellings and leaves exactly 2,216,178 CENTRAL_HEATING dwellings
unassigned between the two programme distribution paths.

P73 does not invent a central-heating reuse percentage. It represents that
unknown assignment as a bounded nuisance parameter:

    x = share of CENTRAL_HEATING dwellings requiring NEW_OR_REPLACE distribution
    x in [0, 1]

The aggregate programme path shares are then exactly:

    nonreuse = (NHEAT + x * CENTRAL) / PHYSICAL_SCOPE
    reuse    = ((1 - x) * CENTRAL) / PHYSICAL_SCOPE

Therefore a point value for x is not required for bounded propagation when
claim-specific outcome bounds exist for both programme paths.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import isfinite

from modules.B02.programme_scope_transition import (
    EXPECTED_CENTRAL_DWELLINGS,
    EXPECTED_NHEAT_DWELLINGS,
    EXPECTED_PHYSICAL_SCOPE_DWELLINGS,
    NHEAT_PROGRAMME_SCOPE_SHARE,
)


REUSE_EXISTING_DISTRIBUTION = "REUSE_EXISTING_DISTRIBUTION"
NEW_OR_REPLACE_DISTRIBUTION_REQUIRED = "NEW_OR_REPLACE_DISTRIBUTION_REQUIRED"


@dataclass(frozen=True)
class CentralDistributionSplit:
    central_nonreuse_fraction: float
    central_reuse_fraction: float
    central_nonreuse_dwellings: float
    central_reuse_dwellings: float
    total_nonreuse_dwellings: float
    total_reuse_dwellings: float
    total_nonreuse_share: float
    total_reuse_share: float
    evidence_status: str = "SET_LATENT"


@dataclass(frozen=True)
class AssignmentRequirementDecision:
    status: str
    point_assignment_required: bool
    blockers: tuple[str, ...]


def project_central_distribution_split(
    central_nonreuse_fraction: float,
) -> CentralDistributionSplit:
    """Project one admissible latent central split into programme path totals."""

    x = float(central_nonreuse_fraction)
    if not isfinite(x) or not 0.0 <= x <= 1.0:
        raise ValueError("central_nonreuse_fraction must be finite within [0,1]")

    central_nonreuse = x * EXPECTED_CENTRAL_DWELLINGS
    central_reuse = (1.0 - x) * EXPECTED_CENTRAL_DWELLINGS
    total_nonreuse = EXPECTED_NHEAT_DWELLINGS + central_nonreuse
    total_reuse = central_reuse

    if abs(total_nonreuse + total_reuse - EXPECTED_PHYSICAL_SCOPE_DWELLINGS) > 1e-9:
        raise ValueError("programme path conservation failed")

    return CentralDistributionSplit(
        central_nonreuse_fraction=x,
        central_reuse_fraction=1.0 - x,
        central_nonreuse_dwellings=central_nonreuse,
        central_reuse_dwellings=central_reuse,
        total_nonreuse_dwellings=total_nonreuse,
        total_reuse_dwellings=total_reuse,
        total_nonreuse_share=total_nonreuse / EXPECTED_PHYSICAL_SCOPE_DWELLINGS,
        total_reuse_share=total_reuse / EXPECTED_PHYSICAL_SCOPE_DWELLINGS,
    )


def central_split_endpoint_envelope() -> tuple[CentralDistributionSplit, CentralDistributionSplit]:
    """Return exact x=0 and x=1 endpoints of the admissible assignment set."""

    return (
        project_central_distribution_split(0.0),
        project_central_distribution_split(1.0),
    )


def assess_point_assignment_requirement(
    *,
    reuse_path_outcome_bounds_complete: bool,
    nonreuse_path_outcome_bounds_complete: bool,
) -> AssignmentRequirementDecision:
    """Separate missing path outcomes from missing point assignment.

    If both path-specific outcome envelopes are complete, the full latent x
    interval can be propagated and no central point share is required.
    """

    blockers: list[str] = []
    if not reuse_path_outcome_bounds_complete:
        blockers.append("REUSE_PATH_OUTCOME_BOUNDS_INCOMPLETE")
    if not nonreuse_path_outcome_bounds_complete:
        blockers.append("NONREUSE_PATH_OUTCOME_BOUNDS_INCOMPLETE")

    if blockers:
        return AssignmentRequirementDecision(
            status="Q_PATH_OUTCOME_BOUNDS_REQUIRED",
            point_assignment_required=False,
            blockers=tuple(blockers),
        )

    return AssignmentRequirementDecision(
        status="POINT_ASSIGNMENT_NOT_REQUIRED_FOR_BOUNDED_PROPAGATION",
        point_assignment_required=False,
        blockers=(),
    )


def p72_floor_reproduced() -> bool:
    """Machine-check that x=0 reproduces the P72 lower-bound endpoint."""

    lower, _upper = central_split_endpoint_envelope()
    return abs(lower.total_nonreuse_share - NHEAT_PROGRAMME_SCOPE_SHARE) <= 1e-12
