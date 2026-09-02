"""B10-P6 fail-closed project delivery timing evidence contract.

This module keeps source-native timing claims separate from derived schedule
variance and from any forecast of future project completion. A planned or
expected completion date is not a completion probability. An actual completion
date is an observed event only when an exact completion source is referenced.

B10-P6 therefore permits retrospective schedule variance to be DER when both
an admissible ex-ante target and an observed completion date are available, but
it never mints a forward-looking fulfilment probability without a separately
calibrated cohort/model authority.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date


class B10ProjectDeliveryTimingError(ValueError):
    """Raised when timing truth, provenance or chronology is ambiguous."""


PLANNED_COMPLETION = "PLANNED_COMPLETION"
EXPECTED_COMPLETION = "EXPECTED_COMPLETION"
ACTUAL_COMPLETION = "ACTUAL_COMPLETION"

TIMING_CLAIM_TYPES = {
    PLANNED_COMPLETION,
    EXPECTED_COMPLETION,
    ACTUAL_COMPLETION,
}

OBS = "OBS"
DER = "DER"
Q = "Q"
TIMING_EVIDENCE_STATUSES = {OBS, DER, Q}

EX_ANTE_VERIFIED = "EX_ANTE_VERIFIED"
CURRENT_PAGE_ONLY = "CURRENT_PAGE_ONLY"
NOT_APPLICABLE = "NOT_APPLICABLE"
SNAPSHOT_STATUSES = {EX_ANTE_VERIFIED, CURRENT_PAGE_ONLY, NOT_APPLICABLE}

FULFILMENT_PROBABILITY_UNAVAILABLE = "Q_NO_CALIBRATED_DELIVERY_MODEL"


def _iso_date(value: str, field_name: str) -> date:
    if not isinstance(value, str) or not value.strip():
        raise B10ProjectDeliveryTimingError(f"{field_name} is required")
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise B10ProjectDeliveryTimingError(f"{field_name} must be ISO YYYY-MM-DD") from exc


@dataclass(frozen=True)
class ProjectTimingEvidence:
    project_id: str
    network_operator: str
    claim_type: str
    claimed_date: str
    source_id: str
    source_publication_date: str | None
    evidence_status: str
    snapshot_status: str
    notes: str = ""

    def __post_init__(self) -> None:
        for field_name in ("project_id", "network_operator", "source_id"):
            value = getattr(self, field_name)
            if not isinstance(value, str) or not value.strip():
                raise B10ProjectDeliveryTimingError(f"{field_name} is required")
        if self.claim_type not in TIMING_CLAIM_TYPES:
            raise B10ProjectDeliveryTimingError("invalid timing claim_type")
        _iso_date(self.claimed_date, "claimed_date")
        if self.source_publication_date is not None:
            publication_date = _iso_date(self.source_publication_date, "source_publication_date")
            claimed = _iso_date(self.claimed_date, "claimed_date")
            if self.claim_type in {PLANNED_COMPLETION, EXPECTED_COMPLETION} and publication_date > claimed:
                raise B10ProjectDeliveryTimingError(
                    "planned/expected target publication cannot post-date its claimed completion date"
                )
        if self.evidence_status not in TIMING_EVIDENCE_STATUSES:
            raise B10ProjectDeliveryTimingError("invalid timing evidence_status")
        if self.snapshot_status not in SNAPSHOT_STATUSES:
            raise B10ProjectDeliveryTimingError("invalid snapshot_status")

        if self.claim_type == ACTUAL_COMPLETION:
            if self.snapshot_status != NOT_APPLICABLE:
                raise B10ProjectDeliveryTimingError(
                    "actual completion evidence must use NOT_APPLICABLE snapshot status"
                )
            if self.evidence_status != OBS:
                raise B10ProjectDeliveryTimingError(
                    "actual completion can be source-native only when OBS"
                )
        else:
            if self.evidence_status != OBS:
                raise B10ProjectDeliveryTimingError(
                    "source-native planned/expected date claims must remain OBS"
                )
            if self.snapshot_status not in {EX_ANTE_VERIFIED, CURRENT_PAGE_ONLY}:
                raise B10ProjectDeliveryTimingError(
                    "planned/expected timing requires explicit snapshot qualification"
                )


@dataclass(frozen=True)
class ProjectDeliveryTimingDecision:
    project_id: str
    network_operator: str
    target_claim_type: str
    target_date: str
    target_snapshot_status: str
    actual_completion_date: str | None
    schedule_variance_days: int | None
    schedule_variance_status: str
    completion_probability: float | None
    completion_probability_status: str
    source_refs: tuple[str, ...]


def evaluate_project_delivery_timing(
    target: ProjectTimingEvidence,
    actual: ProjectTimingEvidence | None,
) -> ProjectDeliveryTimingDecision:
    """Evaluate timing without manufacturing a forward completion probability."""

    if target.claim_type not in {PLANNED_COMPLETION, EXPECTED_COMPLETION}:
        raise B10ProjectDeliveryTimingError(
            "target must be PLANNED_COMPLETION or EXPECTED_COMPLETION"
        )
    if actual is not None:
        if actual.claim_type != ACTUAL_COMPLETION:
            raise B10ProjectDeliveryTimingError("actual evidence must be ACTUAL_COMPLETION")
        if actual.project_id != target.project_id:
            raise B10ProjectDeliveryTimingError("target and actual project_id must match")
        if actual.network_operator != target.network_operator:
            raise B10ProjectDeliveryTimingError("target and actual network_operator must match")

    variance_days: int | None = None
    variance_status = Q
    actual_date: str | None = None
    refs = [target.source_id]

    if actual is not None:
        refs.append(actual.source_id)
        actual_date = actual.claimed_date
        if target.snapshot_status == EX_ANTE_VERIFIED:
            target_date = _iso_date(target.claimed_date, "target claimed_date")
            completed = _iso_date(actual.claimed_date, "actual claimed_date")
            variance_days = (completed - target_date).days
            variance_status = DER
        else:
            # A current page may contain a planned date but cannot prove that the
            # same value was published before completion. Therefore it cannot
            # support a retrospective forecast-performance metric.
            variance_days = None
            variance_status = Q

    return ProjectDeliveryTimingDecision(
        project_id=target.project_id,
        network_operator=target.network_operator,
        target_claim_type=target.claim_type,
        target_date=target.claimed_date,
        target_snapshot_status=target.snapshot_status,
        actual_completion_date=actual_date,
        schedule_variance_days=variance_days,
        schedule_variance_status=variance_status,
        completion_probability=None,
        completion_probability_status=FULFILMENT_PROBABILITY_UNAVAILABLE,
        source_refs=tuple(refs),
    )


def validate_completion_probability_claim(
    probability: float | None,
    *,
    calibrated_model_source_ids: tuple[str, ...] = (),
) -> None:
    """Fail closed unless a future slice supplies an explicit calibrated model."""

    if probability is None:
        return
    if isinstance(probability, bool) or not isinstance(probability, (int, float)):
        raise B10ProjectDeliveryTimingError("completion probability must be numeric")
    if not 0 <= float(probability) <= 1:
        raise B10ProjectDeliveryTimingError("completion probability must lie in [0,1]")
    if not calibrated_model_source_ids:
        raise B10ProjectDeliveryTimingError(
            "numeric completion probability requires separately calibrated delivery-model authority"
        )
    raise B10ProjectDeliveryTimingError(
        "B10-P6 does not authorize any calibrated completion-probability model"
    )


__all__ = [
    "ACTUAL_COMPLETION",
    "B10ProjectDeliveryTimingError",
    "CURRENT_PAGE_ONLY",
    "DER",
    "EXPECTED_COMPLETION",
    "EX_ANTE_VERIFIED",
    "FULFILMENT_PROBABILITY_UNAVAILABLE",
    "NOT_APPLICABLE",
    "OBS",
    "PLANNED_COMPLETION",
    "ProjectDeliveryTimingDecision",
    "ProjectTimingEvidence",
    "Q",
    "evaluate_project_delivery_timing",
    "validate_completion_probability_claim",
]
