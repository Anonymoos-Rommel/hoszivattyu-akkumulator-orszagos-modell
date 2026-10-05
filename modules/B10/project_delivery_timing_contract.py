"""B10-P6 fail-closed project delivery timing evidence contract.

This module keeps source-native timing claims separate from derived schedule
variance and from any forecast of future project completion. A planned or
expected completion date is not a completion probability. An actual completion
date is an exact event only when a referenced source explicitly dates that event.
Publication/completed-by bounds, project closure and physical operation are separate.

B10-P6 therefore permits retrospective schedule variance to be DER when both
an admissible ex-ante target and an exact, same-scope milestone are available, but
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

# Defaults preserve input construction, never an unsupported timing claim.
UNSPECIFIED = "UNSPECIFIED"
PROJECT_COMPLETION = "PROJECT_COMPLETION"
CAPABILITY_TARGET = "CAPABILITY_TARGET"
PHYSICAL_IN_SERVICE = "PHYSICAL_IN_SERVICE"
MILESTONE_TYPES = {UNSPECIFIED, PROJECT_COMPLETION, CAPABILITY_TARGET, PHYSICAL_IN_SERVICE}
EXACT = "EXACT"
ON_OR_BEFORE = "ON_OR_BEFORE"
OPEN = "OPEN"
SOURCE_STATED_TARGET_DATE = "SOURCE_STATED_TARGET_DATE"
SOURCE_STATED_EVENT_DATE = "SOURCE_STATED_EVENT_DATE"
PUBLICATION_REPORTING_BOUND = "PUBLICATION_REPORTING_BOUND"
VERIFIED_SAME_MILESTONE_SCOPE = "VERIFIED_SAME_MILESTONE_SCOPE"
UNRESOLVED_PAIRING = "UNRESOLVED"

FULFILMENT_PROBABILITY_UNAVAILABLE = "Q_NO_CALIBRATED_DELIVERY_MODEL"


def _iso_date(value: str, field_name: str) -> date:
    if not isinstance(value, str) or not value.strip():
        raise B10ProjectDeliveryTimingError(f"{field_name} is required")
    try:
        result = date.fromisoformat(value)
        if result.isoformat() != value:
            raise ValueError("noncanonical ISO date")
        return result
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
    milestone_type: str = UNSPECIFIED
    scope_id: str | None = None
    scope_source_id: str | None = None
    date_relation: str = OPEN
    date_precision: str = UNSPECIFIED
    date_authority: str = UNSPECIFIED

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

        if self.snapshot_status == EX_ANTE_VERIFIED and self.source_publication_date is None:
            raise B10ProjectDeliveryTimingError("EX_ANTE_VERIFIED requires dated source authority")
        if self.milestone_type not in MILESTONE_TYPES:
            raise B10ProjectDeliveryTimingError("invalid milestone_type")
        if self.date_relation not in {EXACT, ON_OR_BEFORE, OPEN}:
            raise B10ProjectDeliveryTimingError("invalid date_relation")
        if self.date_precision not in {"DAY", UNSPECIFIED}:
            raise B10ProjectDeliveryTimingError("invalid date_precision")
        if self.date_authority not in {
            UNSPECIFIED, SOURCE_STATED_TARGET_DATE, SOURCE_STATED_EVENT_DATE,
            PUBLICATION_REPORTING_BOUND,
        }:
            raise B10ProjectDeliveryTimingError("invalid date_authority")
        if self.scope_id is not None and (not isinstance(self.scope_id, str) or not self.scope_id.strip()):
            raise B10ProjectDeliveryTimingError("scope_id cannot be blank")
        if self.scope_source_id is not None and (
            self.scope_source_id != self.source_id or self.scope_id is None
            or self.milestone_type == UNSPECIFIED
        ):
            raise B10ProjectDeliveryTimingError(
                "scope_source_id must bind this source's explicit milestone and scope"
            )
        if self.date_relation != OPEN and self.date_precision != "DAY":
            raise B10ProjectDeliveryTimingError("bounded dates require explicit DAY precision")
        if self.claim_type == ACTUAL_COMPLETION:
            if self.date_relation == EXACT and self.date_authority != SOURCE_STATED_EVENT_DATE:
                raise B10ProjectDeliveryTimingError("exact event requires SOURCE_STATED_EVENT_DATE")
            if self.date_authority == SOURCE_STATED_TARGET_DATE:
                raise B10ProjectDeliveryTimingError("a target is not an actual event")
        elif self.date_relation != OPEN and (
            self.date_relation != EXACT or self.date_authority != SOURCE_STATED_TARGET_DATE
        ):
            raise B10ProjectDeliveryTimingError("target requires an exact source-stated target date")
        if self.date_authority == PUBLICATION_REPORTING_BOUND and (
            self.claim_type != ACTUAL_COMPLETION or self.date_relation != ON_OR_BEFORE
            or self.source_publication_date != self.claimed_date
        ):
            raise B10ProjectDeliveryTimingError(
                "publication reporting is only a completed-by bound, never an exact event"
            )
        if self.date_relation == ON_OR_BEFORE and self.date_authority != PUBLICATION_REPORTING_BOUND:
            raise B10ProjectDeliveryTimingError("completed-by bound requires publication reporting authority")
        if (self.claim_type == ACTUAL_COMPLETION and self.date_relation == EXACT
                and self.source_publication_date is not None
                and self.source_publication_date < self.claimed_date):
            raise B10ProjectDeliveryTimingError("observed event cannot post-date its reporting source")

    @property
    def has_bound_scope(self) -> bool:
        return bool(self.scope_id and self.scope_source_id == self.source_id
                    and self.milestone_type != UNSPECIFIED)

    @property
    def is_exact_event(self) -> bool:
        return (self.claim_type == ACTUAL_COMPLETION and self.date_relation == EXACT
                and self.date_authority == SOURCE_STATED_EVENT_DATE
                and self.date_precision == "DAY" and self.has_bound_scope)


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
    target_milestone_type: str = UNSPECIFIED
    actual_milestone_type: str = UNSPECIFIED
    actual_date_relation: str = OPEN
    actual_event_lower_bound: str | None = None
    actual_event_upper_bound: str | None = None
    pairing_status: str = UNRESOLVED_PAIRING
    physical_actual_completion_date: str | None = None
    physical_target_proven: bool = False
    target_scope_id: str | None = None
    actual_scope_id: str | None = None


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

    pairing_status = UNRESOLVED_PAIRING
    lower_bound = upper_bound = physical_actual = None
    if actual is not None:
        refs.append(actual.source_id)
        if actual.is_exact_event:
            actual_date = actual.claimed_date
            lower_bound = upper_bound = actual.claimed_date
            if actual.milestone_type == PHYSICAL_IN_SERVICE:
                physical_actual = actual.claimed_date
        elif actual.date_relation == ON_OR_BEFORE:
            upper_bound = actual.claimed_date
        if (target.has_bound_scope and actual.has_bound_scope
                and target.milestone_type == actual.milestone_type
                and target.scope_id == actual.scope_id):
            pairing_status = VERIFIED_SAME_MILESTONE_SCOPE
        if (target.snapshot_status == EX_ANTE_VERIFIED
                and target.date_relation == EXACT
                and target.date_authority == SOURCE_STATED_TARGET_DATE
                and actual.is_exact_event
                and pairing_status == VERIFIED_SAME_MILESTONE_SCOPE
                and target.source_publication_date <= actual.claimed_date):
            variance_days = (_iso_date(actual.claimed_date, "actual claimed_date")
                             - _iso_date(target.claimed_date, "target claimed_date")).days
            variance_status = DER

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
        target_milestone_type=target.milestone_type,
        actual_milestone_type=actual.milestone_type if actual else UNSPECIFIED,
        target_scope_id=target.scope_id,
        actual_scope_id=actual.scope_id if actual else None,
        actual_date_relation=actual.date_relation if actual else OPEN,
        actual_event_lower_bound=lower_bound,
        actual_event_upper_bound=upper_bound,
        pairing_status=pairing_status,
        physical_actual_completion_date=physical_actual,
        physical_target_proven=(target.milestone_type == PHYSICAL_IN_SERVICE
                                and target.has_bound_scope and target.date_relation == EXACT
                                and target.date_authority == SOURCE_STATED_TARGET_DATE),
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
    "CAPABILITY_TARGET",
    "EXACT",
    "ON_OR_BEFORE",
    "OPEN",
    "PHYSICAL_IN_SERVICE",
    "PROJECT_COMPLETION",
    "PUBLICATION_REPORTING_BOUND",
    "SOURCE_STATED_EVENT_DATE",
    "SOURCE_STATED_TARGET_DATE",
    "UNRESOLVED_PAIRING",
    "UNSPECIFIED",
    "VERIFIED_SAME_MILESTONE_SCOPE",
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
