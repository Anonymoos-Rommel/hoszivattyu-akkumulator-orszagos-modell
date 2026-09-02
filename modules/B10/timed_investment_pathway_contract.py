"""Fail-closed B10-P11 timed reinforcement / investment pathway gate.

The contract integrates already-authorized B10 truths without collapsing them:
project/reinforcement authority (P5), project-delivery timing (P6), programme
attribution/CAPEX (P3/P5), and claim-specific CAPEX cash-flow timing.

A project completion target or observed completion date is never treated as the
cash-flow date of its CAPEX. Numeric programme-incremental CAPEX can enter a
timed investment pathway only through a separately bound, complete cash-flow
schedule. Missing timing remains Q rather than being assigned to a completion
year or spread by a generic profile.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from math import isclose, isfinite
from typing import Iterable

from .baseline_infrastructure_contract import (
    BASELINE,
    PROGRAM_ACCELERATED,
    PROGRAM_INCREMENTAL,
    UNRESOLVED,
    InfrastructureRecord,
)
from .incremental_reinforcement_contract import (
    DSO_SUBSTATION,
    ReinforcementGateDecision,
    evaluate_programme_incremental_reinforcement,
)
from .project_delivery_timing_contract import (
    CURRENT_PAGE_ONLY,
    EX_ANTE_VERIFIED,
    FULFILMENT_PROBABILITY_UNAVAILABLE,
    ProjectDeliveryTimingDecision,
    ProjectTimingEvidence,
    evaluate_project_delivery_timing,
)


class B10TimedInvestmentPathwayError(ValueError):
    """Raised when project, timing, attribution or cash-flow identity drifts."""


PROGRAMME_INCREMENTAL_CAPEX_CASHFLOW = "PROGRAMME_INCREMENTAL_CAPEX_CASHFLOW"
COMPLETE_PROGRAMME_INCREMENTAL_CAPEX_SCHEDULE = "COMPLETE_PROGRAMME_INCREMENTAL_CAPEX_SCHEDULE"

PROJECT_ID_PREFIX = "PROJECT_ID:"
NETWORK_OPERATOR_PREFIX = "NETWORK_OPERATOR:"
REGION_ID_PREFIX = "REGION_ID:"
REGION_GRAIN_BINDING = "REGION_GRAIN:DSO_SUBSTATION"
COST_COMPONENT_PREFIX = "COST_COMPONENT:"
SCHEDULE_ID_PREFIX = "SCHEDULE_ID:"
PERIOD_START_PREFIX = "PERIOD_START:"
PERIOD_END_PREFIX = "PERIOD_END:"

DELIVERY_ACTUAL_OBSERVED = "DELIVERY_ACTUAL_OBSERVED"
DELIVERY_EX_ANTE_TARGET = "DELIVERY_EX_ANTE_TARGET"
DELIVERY_CURRENT_TARGET_ONLY = "DELIVERY_CURRENT_TARGET_ONLY"

TIMED_PROGRAMME_CAPEX_PROVEN = "TIMED_PROGRAMME_CAPEX_PROVEN"
SCN_TIMED_PROGRAMME_CAPEX = "SCN_TIMED_PROGRAMME_CAPEX"
Q_CAPEX_TIMING_UNRESOLVED = "Q_CAPEX_TIMING_UNRESOLVED"
Q_PROGRAMME_CAPEX_UNRESOLVED = "Q_PROGRAMME_CAPEX_UNRESOLVED"
Q_PROGRAMME_ATTRIBUTION_UNRESOLVED = "Q_PROGRAMME_ATTRIBUTION_UNRESOLVED"
BASELINE_NOT_PROGRAMME_INCREMENTAL = "BASELINE_NOT_PROGRAMME_INCREMENTAL"

CASHFLOW_TRUTH_STATUSES = {"OBS", "DER", "SCN", "Q"}
_REAL_CASHFLOW_AUTHORITY_MAX_LEVEL = 3


def _iso_date(value: str, field_name: str) -> date:
    if not isinstance(value, str) or not value.strip():
        raise B10TimedInvestmentPathwayError(f"{field_name} is required")
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise B10TimedInvestmentPathwayError(f"{field_name} must be ISO YYYY-MM-DD") from exc


def _money(value: float, field_name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not isfinite(value) or value < 0:
        raise B10TimedInvestmentPathwayError(f"{field_name} must be finite and non-negative")
    return float(value)


@dataclass(frozen=True)
class CapexCashflowEvidence:
    """One exact programme-incremental CAPEX amount assigned to one time period."""

    source_id: str
    authority_level: int
    truth_status: str
    project_id: str
    network_operator: str
    region_id: str
    region_grain: str
    cost_component_id: str
    schedule_id: str
    period_start: str
    period_end: str
    amount_huf: float
    supports: tuple[str, ...]

    def __post_init__(self) -> None:
        for field_name in (
            "source_id",
            "project_id",
            "network_operator",
            "region_id",
            "cost_component_id",
            "schedule_id",
        ):
            value = getattr(self, field_name)
            if not isinstance(value, str) or not value.strip():
                raise B10TimedInvestmentPathwayError(f"{field_name} is required")
        if self.authority_level not in {1, 2, 3, 4, 5}:
            raise B10TimedInvestmentPathwayError("authority_level must be 1..5")
        if self.truth_status not in CASHFLOW_TRUTH_STATUSES:
            raise B10TimedInvestmentPathwayError("invalid cash-flow truth_status")
        if self.region_grain != DSO_SUBSTATION:
            raise B10TimedInvestmentPathwayError("cash-flow evidence must remain at exact DSO_SUBSTATION project grain")
        start = _iso_date(self.period_start, "period_start")
        end = _iso_date(self.period_end, "period_end")
        if end < start:
            raise B10TimedInvestmentPathwayError("cash-flow period_end cannot precede period_start")
        object.__setattr__(self, "amount_huf", _money(self.amount_huf, "amount_huf"))
        if isinstance(self.supports, str) or not self.supports:
            raise B10TimedInvestmentPathwayError("supports must be a non-empty collection")
        if any(not isinstance(item, str) or not item.strip() for item in self.supports):
            raise B10TimedInvestmentPathwayError("supports cannot contain blank claims")

    @property
    def required_bindings(self) -> tuple[str, ...]:
        return (
            f"{PROJECT_ID_PREFIX}{self.project_id}",
            f"{NETWORK_OPERATOR_PREFIX}{self.network_operator}",
            f"{REGION_ID_PREFIX}{self.region_id}",
            REGION_GRAIN_BINDING,
            f"{COST_COMPONENT_PREFIX}{self.cost_component_id}",
            f"{SCHEDULE_ID_PREFIX}{self.schedule_id}",
            f"{PERIOD_START_PREFIX}{self.period_start}",
            f"{PERIOD_END_PREFIX}{self.period_end}",
        )


@dataclass(frozen=True)
class TimedInvestmentCashflowRow:
    project_id: str
    network_operator: str
    region_id: str
    region_grain: str
    cost_component_id: str
    schedule_id: str
    period_start: str
    period_end: str
    programme_incremental_capex_huf: float
    evidence_status: str
    source_refs: tuple[str, ...]


@dataclass(frozen=True)
class TimedInvestmentPathwayDecision:
    status: str
    project_id: str
    network_operator: str
    region_id: str
    region_grain: str
    horizon: str
    attribution_status: str
    reinforcement_required_proven: bool
    delivery_status: str
    target_date: str
    actual_completion_date: str | None
    schedule_variance_days: int | None
    schedule_variance_status: str
    completion_probability: float | None
    completion_probability_status: str
    untimed_programme_incremental_capex_huf: float | None
    cashflow_rows: tuple[TimedInvestmentCashflowRow, ...]
    source_refs: tuple[str, ...]
    reason: str


def _delivery_status(decision: ProjectDeliveryTimingDecision) -> str:
    if decision.actual_completion_date is not None:
        return DELIVERY_ACTUAL_OBSERVED
    if decision.target_snapshot_status == EX_ANTE_VERIFIED:
        return DELIVERY_EX_ANTE_TARGET
    if decision.target_snapshot_status == CURRENT_PAGE_ONLY:
        return DELIVERY_CURRENT_TARGET_ONLY
    raise B10TimedInvestmentPathwayError("unsupported P6 target snapshot status")


def _cashflow_claim_bound(item: CapexCashflowEvidence) -> bool:
    supports = set(item.supports)
    return (
        PROGRAMME_INCREMENTAL_CAPEX_CASHFLOW in supports
        and set(item.required_bindings).issubset(supports)
    )


def _schedule_complete_authority(item: CapexCashflowEvidence) -> bool:
    if COMPLETE_PROGRAMME_INCREMENTAL_CAPEX_SCHEDULE not in item.supports:
        return False
    if item.truth_status in {"OBS", "DER"}:
        return item.authority_level <= _REAL_CASHFLOW_AUTHORITY_MAX_LEVEL
    return item.truth_status == "SCN"


def _same_money(left: float | None, right: float | None) -> bool:
    if left is None or right is None:
        return left is right
    return isclose(float(left), float(right), rel_tol=0.0, abs_tol=0.5)


def build_timed_investment_pathway(
    record: InfrastructureRecord,
    reinforcement: ReinforcementGateDecision,
    target_timing: ProjectTimingEvidence,
    actual_timing: ProjectTimingEvidence | None = None,
    cashflow_evidence: Iterable[CapexCashflowEvidence] = (),
) -> TimedInvestmentPathwayDecision:
    """Build a timed programme-investment pathway without inventing cash-flow timing.

    P5 is re-evaluated from the original InfrastructureRecord so a hand-crafted
    decision cannot bypass its reinforcement/attribution/CAPEX gates. P6 is also
    evaluated from source timing evidence. Completion dates remain delivery
    milestones only; they never allocate CAPEX to a year or period.
    """

    if not isinstance(record, InfrastructureRecord):
        raise B10TimedInvestmentPathwayError("record must be canonical InfrastructureRecord")
    if not isinstance(reinforcement, ReinforcementGateDecision):
        raise B10TimedInvestmentPathwayError("reinforcement must be ReinforcementGateDecision")
    if record.region_grain != DSO_SUBSTATION:
        raise B10TimedInvestmentPathwayError("P11 programme pathway requires exact DSO_SUBSTATION project grain")

    expected = evaluate_programme_incremental_reinforcement(
        record,
        reinforcement_horizon=reinforcement.horizon,
        screening=None,
    )
    if (
        reinforcement.project_id != expected.project_id
        or reinforcement.region_id != expected.region_id
        or reinforcement.horizon != expected.horizon
        or reinforcement.reinforcement_required_proven != expected.reinforcement_required_proven
        or reinforcement.attribution.attribution_status != expected.attribution.attribution_status
        or reinforcement.attribution.evidence_status != expected.attribution.evidence_status
        or not _same_money(reinforcement.program_incremental_capex_huf, expected.program_incremental_capex_huf)
    ):
        raise B10TimedInvestmentPathwayError("P11 reinforcement input does not reproduce canonical P5 authority")

    timing = evaluate_project_delivery_timing(target_timing, actual_timing)
    if timing.project_id != record.project_id or timing.project_id != reinforcement.project_id:
        raise B10TimedInvestmentPathwayError("P5/P6 project_id must match exactly")
    if timing.network_operator != record.network_operator:
        raise B10TimedInvestmentPathwayError("P6 network_operator must match the P5 project operator")
    if timing.completion_probability is not None or timing.completion_probability_status != FULFILMENT_PROBABILITY_UNAVAILABLE:
        raise B10TimedInvestmentPathwayError("P11 cannot mint a completion probability")

    delivery_status = _delivery_status(timing)
    refs = set(reinforcement.attribution.source_refs) | set(timing.source_refs)
    base = dict(
        project_id=record.project_id,
        network_operator=record.network_operator,
        region_id=record.region_id,
        region_grain=record.region_grain,
        horizon=reinforcement.horizon,
        attribution_status=reinforcement.attribution.attribution_status,
        reinforcement_required_proven=reinforcement.reinforcement_required_proven,
        delivery_status=delivery_status,
        target_date=timing.target_date,
        actual_completion_date=timing.actual_completion_date,
        schedule_variance_days=timing.schedule_variance_days,
        schedule_variance_status=timing.schedule_variance_status,
        completion_probability=timing.completion_probability,
        completion_probability_status=timing.completion_probability_status,
        untimed_programme_incremental_capex_huf=reinforcement.program_incremental_capex_huf,
    )

    attribution_status = reinforcement.attribution.attribution_status
    if attribution_status == UNRESOLVED or reinforcement.attribution.evidence_status == "Q":
        return TimedInvestmentPathwayDecision(
            status=Q_PROGRAMME_ATTRIBUTION_UNRESOLVED,
            cashflow_rows=(),
            source_refs=tuple(sorted(refs)),
            reason="programme attribution is unresolved; no programme investment pathway can be published",
            **base,
        )
    if attribution_status == BASELINE:
        return TimedInvestmentPathwayDecision(
            status=BASELINE_NOT_PROGRAMME_INCREMENTAL,
            cashflow_rows=(),
            source_refs=tuple(sorted(refs)),
            reason="baseline project timing is not programme-incremental investment timing",
            **base,
        )
    if attribution_status not in {PROGRAM_INCREMENTAL, PROGRAM_ACCELERATED}:
        return TimedInvestmentPathwayDecision(
            status=Q_PROGRAMME_ATTRIBUTION_UNRESOLVED,
            cashflow_rows=(),
            source_refs=tuple(sorted(refs)),
            reason="unsupported programme attribution status for timed investment pathway",
            **base,
        )

    total_capex = reinforcement.program_incremental_capex_huf
    if total_capex is None:
        return TimedInvestmentPathwayDecision(
            status=Q_PROGRAMME_CAPEX_UNRESOLVED,
            cashflow_rows=(),
            source_refs=tuple(sorted(refs)),
            reason="programme-incremental reinforcement/attribution is proven but numeric programme CAPEX remains Q",
            **base,
        )
    if record.cost_component_id is None:
        raise B10TimedInvestmentPathwayError("P5 numeric programme CAPEX requires exact cost_component_id")

    cashflows = tuple(cashflow_evidence)
    if not cashflows:
        return TimedInvestmentPathwayDecision(
            status=Q_CAPEX_TIMING_UNRESOLVED,
            cashflow_rows=(),
            source_refs=tuple(sorted(refs)),
            reason="delivery timing exists but no claim-specific CAPEX cash-flow schedule is supplied",
            **base,
        )
    if any(not isinstance(item, CapexCashflowEvidence) for item in cashflows):
        raise B10TimedInvestmentPathwayError("cashflow_evidence must contain CapexCashflowEvidence rows")

    schedule_ids = {item.schedule_id for item in cashflows}
    truths = {item.truth_status for item in cashflows}
    periods = {(item.period_start, item.period_end) for item in cashflows}
    if len(schedule_ids) != 1:
        raise B10TimedInvestmentPathwayError("one pathway cannot mix CAPEX schedule_ids")
    if len(periods) != len(cashflows):
        raise B10TimedInvestmentPathwayError("duplicate CAPEX cash-flow periods are rejected")
    if "Q" in truths or ("SCN" in truths and truths != {"SCN"}):
        refs.update(item.source_id for item in cashflows)
        return TimedInvestmentPathwayDecision(
            status=Q_CAPEX_TIMING_UNRESOLVED,
            cashflow_rows=(),
            source_refs=tuple(sorted(refs)),
            reason="Q or mixed REAL/SCN cash-flow truth cannot authorize a timed CAPEX pathway",
            **base,
        )

    for item in cashflows:
        if (
            item.project_id != record.project_id
            or item.network_operator != record.network_operator
            or item.region_id != record.region_id
            or item.region_grain != record.region_grain
            or item.cost_component_id != record.cost_component_id
        ):
            raise B10TimedInvestmentPathwayError("cash-flow evidence must preserve exact project/operator/region/component identity")

    refs.update(item.source_id for item in cashflows)
    if not all(_cashflow_claim_bound(item) for item in cashflows):
        return TimedInvestmentPathwayDecision(
            status=Q_CAPEX_TIMING_UNRESOLVED,
            cashflow_rows=(),
            source_refs=tuple(sorted(refs)),
            reason="cash-flow rows lack claim-specific project/component/schedule/period bindings",
            **base,
        )
    if not any(_schedule_complete_authority(item) for item in cashflows):
        return TimedInvestmentPathwayDecision(
            status=Q_CAPEX_TIMING_UNRESOLVED,
            cashflow_rows=(),
            source_refs=tuple(sorted(refs)),
            reason="cash-flow rows do not prove a complete programme-incremental CAPEX schedule",
            **base,
        )
    if any(item.truth_status in {"OBS", "DER"} and item.authority_level > _REAL_CASHFLOW_AUTHORITY_MAX_LEVEL for item in cashflows):
        return TimedInvestmentPathwayDecision(
            status=Q_CAPEX_TIMING_UNRESOLVED,
            cashflow_rows=(),
            source_refs=tuple(sorted(refs)),
            reason="REAL cash-flow timing requires authority level 1..3",
            **base,
        )

    ordered = tuple(sorted(cashflows, key=lambda item: (item.period_start, item.period_end, item.source_id)))
    for previous, current in zip(ordered, ordered[1:]):
        if _iso_date(current.period_start, "period_start") <= _iso_date(previous.period_end, "period_end"):
            return TimedInvestmentPathwayDecision(
                status=Q_CAPEX_TIMING_UNRESOLVED,
                cashflow_rows=(),
                source_refs=tuple(sorted(refs)),
                reason="overlapping period totals cannot be summed as a complete CAPEX schedule",
                **base,
            )

    scheduled_total = sum(item.amount_huf for item in ordered)
    if not _same_money(scheduled_total, total_capex):
        return TimedInvestmentPathwayDecision(
            status=Q_CAPEX_TIMING_UNRESOLVED,
            cashflow_rows=(),
            source_refs=tuple(sorted(refs)),
            reason="cash-flow schedule total does not reconcile exactly to P5 programme-incremental CAPEX",
            **base,
        )

    evidence_status = "SCN" if truths == {"SCN"} or reinforcement.attribution.evidence_status == "SCN" else "DER"
    rows = tuple(
        TimedInvestmentCashflowRow(
            project_id=item.project_id,
            network_operator=item.network_operator,
            region_id=item.region_id,
            region_grain=item.region_grain,
            cost_component_id=item.cost_component_id,
            schedule_id=item.schedule_id,
            period_start=item.period_start,
            period_end=item.period_end,
            programme_incremental_capex_huf=item.amount_huf,
            evidence_status=evidence_status,
            source_refs=(item.source_id,),
        )
        for item in ordered
    )
    status = SCN_TIMED_PROGRAMME_CAPEX if evidence_status == "SCN" else TIMED_PROGRAMME_CAPEX_PROVEN
    return TimedInvestmentPathwayDecision(
        status=status,
        cashflow_rows=rows,
        source_refs=tuple(sorted(refs)),
        reason="P5 programme CAPEX reconciles to a separately authorized complete cash-flow schedule; P6 delivery dates remain separate milestones",
        **base,
    )


__all__ = [
    "BASELINE_NOT_PROGRAMME_INCREMENTAL",
    "B10TimedInvestmentPathwayError",
    "COMPLETE_PROGRAMME_INCREMENTAL_CAPEX_SCHEDULE",
    "CapexCashflowEvidence",
    "DELIVERY_ACTUAL_OBSERVED",
    "DELIVERY_CURRENT_TARGET_ONLY",
    "DELIVERY_EX_ANTE_TARGET",
    "PROGRAMME_INCREMENTAL_CAPEX_CASHFLOW",
    "Q_CAPEX_TIMING_UNRESOLVED",
    "Q_PROGRAMME_ATTRIBUTION_UNRESOLVED",
    "Q_PROGRAMME_CAPEX_UNRESOLVED",
    "SCN_TIMED_PROGRAMME_CAPEX",
    "TIMED_PROGRAMME_CAPEX_PROVEN",
    "TimedInvestmentCashflowRow",
    "TimedInvestmentPathwayDecision",
    "build_timed_investment_pathway",
]
