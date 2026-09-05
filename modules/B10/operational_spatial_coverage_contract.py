"""B10 operational spatial coverage acceptance with explicit residual accounting.

P64 does not turn unresolved geography into evidence. It records the project
policy decision that the P63 resolved-only surface is sufficient for downstream
national B10 modelling while the residual remains explicit and fail-closed.
"""

from __future__ import annotations

from dataclasses import dataclass


NATIONAL_SETTLEMENT_TOTAL = 3155
EXACT_WHOLE_SETTLEMENT_PROVEN = 3052
EXACT_PARTIAL_ONLY_SETTLEMENTS = 1

OPERATIONALLY_COMPLETE_WITH_DISCLOSED_RESIDUAL = (
    "OPERATIONALLY_COMPLETE_WITH_DISCLOSED_RESIDUAL"
)
EVIDENCE_NOT_EXHAUSTIVE = "EVIDENCE_NOT_EXHAUSTIVE"


class B10OperationalSpatialCoverageError(ValueError):
    """Raised when P64 operational coverage accounting is internally inconsistent."""


@dataclass(frozen=True)
class OperationalSpatialCoverage:
    total_settlements: int
    exact_whole_proven: int
    exact_partial_only: int
    operational_status: str
    evidence_completeness_status: str

    def __post_init__(self) -> None:
        for name in ("total_settlements", "exact_whole_proven", "exact_partial_only"):
            value = getattr(self, name)
            if isinstance(value, bool) or not isinstance(value, int) or value < 0:
                raise B10OperationalSpatialCoverageError(f"{name} must be a non-negative integer")
        if self.exact_whole_proven > self.total_settlements:
            raise B10OperationalSpatialCoverageError("whole-settlement count cannot exceed national total")
        if self.exact_whole_proven + self.exact_partial_only > self.total_settlements:
            raise B10OperationalSpatialCoverageError("resolved settlement count cannot exceed national total")
        if self.operational_status != OPERATIONALLY_COMPLETE_WITH_DISCLOSED_RESIDUAL:
            raise B10OperationalSpatialCoverageError("P64 operational status must preserve the accepted policy")
        if self.evidence_completeness_status != EVIDENCE_NOT_EXHAUSTIVE:
            raise B10OperationalSpatialCoverageError("P64 must not claim exhaustive national evidence")

    @property
    def whole_not_proven(self) -> int:
        return self.total_settlements - self.exact_whole_proven

    @property
    def no_effective_resolution(self) -> int:
        return self.total_settlements - self.exact_whole_proven - self.exact_partial_only

    @property
    def exact_whole_share_pct(self) -> float:
        return 100.0 * self.exact_whole_proven / self.total_settlements

    @property
    def any_effective_resolution_share_pct(self) -> float:
        return 100.0 * (self.exact_whole_proven + self.exact_partial_only) / self.total_settlements

    @property
    def whole_not_proven_share_pct(self) -> float:
        return 100.0 * self.whole_not_proven / self.total_settlements

    @property
    def no_effective_resolution_share_pct(self) -> float:
        return 100.0 * self.no_effective_resolution / self.total_settlements


def current_operational_spatial_coverage() -> OperationalSpatialCoverage:
    """Return the exact P64 accepted national coverage accounting."""
    return OperationalSpatialCoverage(
        total_settlements=NATIONAL_SETTLEMENT_TOTAL,
        exact_whole_proven=EXACT_WHOLE_SETTLEMENT_PROVEN,
        exact_partial_only=EXACT_PARTIAL_ONLY_SETTLEMENTS,
        operational_status=OPERATIONALLY_COMPLETE_WITH_DISCLOSED_RESIDUAL,
        evidence_completeness_status=EVIDENCE_NOT_EXHAUSTIVE,
    )


def require_operational_spatial_coverage(coverage: OperationalSpatialCoverage) -> None:
    """Admit the P64 surface for modelling without imputing the disclosed residual."""
    if not isinstance(coverage, OperationalSpatialCoverage):
        raise B10OperationalSpatialCoverageError("coverage must be OperationalSpatialCoverage")
    if coverage.operational_status != OPERATIONALLY_COMPLETE_WITH_DISCLOSED_RESIDUAL:
        raise B10OperationalSpatialCoverageError("operational spatial coverage is not accepted")
    if coverage.exact_whole_proven != EXACT_WHOLE_SETTLEMENT_PROVEN:
        raise B10OperationalSpatialCoverageError("exact whole-settlement evidence count changed")
    if coverage.exact_partial_only != EXACT_PARTIAL_ONLY_SETTLEMENTS:
        raise B10OperationalSpatialCoverageError("exact partial-only evidence count changed")


__all__ = [
    "B10OperationalSpatialCoverageError",
    "EVIDENCE_NOT_EXHAUSTIVE",
    "EXACT_PARTIAL_ONLY_SETTLEMENTS",
    "EXACT_WHOLE_SETTLEMENT_PROVEN",
    "NATIONAL_SETTLEMENT_TOTAL",
    "OPERATIONALLY_COMPLETE_WITH_DISCLOSED_RESIDUAL",
    "OperationalSpatialCoverage",
    "current_operational_spatial_coverage",
    "require_operational_spatial_coverage",
]
