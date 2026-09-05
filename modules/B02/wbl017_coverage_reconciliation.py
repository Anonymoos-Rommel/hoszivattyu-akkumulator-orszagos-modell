"""Fail-closed count reconciliation for the B02 WBL017 heat-pump projection.

B02-P10 does not explain or impute missing WBL017 dwellings.  It only checks
whether a bounded projection reconciles exactly to an independently identified
reference count.  Count reconciliation is narrower than cell-level joint
authority and narrower than technical eligibility.
"""

from __future__ import annotations

from dataclasses import dataclass


Q = "Q"
RECONCILED = "RECONCILED"
REAL_EVIDENCE = frozenset({"OBS", "DER"})


@dataclass(frozen=True)
class CoverageInputs:
    reference_count: int
    projection_count: int
    reference_evidence: str
    projection_evidence: str


@dataclass(frozen=True)
class CoverageDecision:
    status: str
    difference_count: int
    blockers: tuple[str, ...]


def _validate_count(name: str, value: int) -> None:
    if type(value) is not int or value < 0:
        raise ValueError(f"{name} must be a non-negative integer")


def assess_coverage(inputs: CoverageInputs) -> CoverageDecision:
    """Reconcile a projection count to a reference count without imputation.

    `RECONCILED` means only that the two counts are equal with OBS/DER lineage.
    It does not prove that every categorical combination is returned, that the
    projection can be joined to another WBL view, or that missing combinations
    are zero.
    """

    _validate_count("reference_count", inputs.reference_count)
    _validate_count("projection_count", inputs.projection_count)

    difference = inputs.reference_count - inputs.projection_count
    blockers: list[str] = []

    if inputs.reference_evidence not in REAL_EVIDENCE:
        blockers.append("REFERENCE_EVIDENCE_NOT_REAL")
    if inputs.projection_evidence not in REAL_EVIDENCE:
        blockers.append("PROJECTION_EVIDENCE_NOT_REAL")

    if inputs.projection_count > inputs.reference_count:
        blockers.append("PROJECTION_EXCEEDS_REFERENCE")
    elif inputs.projection_count < inputs.reference_count:
        blockers.append("INCOMPLETE_POPULATION_COVERAGE")

    if blockers:
        return CoverageDecision(Q, difference, tuple(blockers))
    return CoverageDecision(RECONCILED, 0, ())
