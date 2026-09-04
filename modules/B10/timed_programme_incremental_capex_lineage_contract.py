"""B10-P33 fail-closed REAL P32 CAPEX -> P11 timed cash-flow lineage gate.

Core rules:

    P32 PROGRAMME-INCREMENTAL CAPEX LINEAGE != TIMED CAPEX SCHEDULE
    P11 TIMED_PROGRAMME_CAPEX_PROVEN != P32-LINKED TIMED CAPEX
    SAME PROJECT/COMPONENT/AMOUNT != SAME CAPEX LINEAGE
    DELIVERY DATE != CAPEX CASH-FLOW TIMING
    SCN TIMED CAPEX != REAL TIMED CAPEX
    HANDCRAFTED P32 DECISION != CANONICAL P32 AUTHORITY

P32 proves an exact REAL programme-incremental CAPEX amount and cost component on
an exact limiting-node/reinforcement lineage. P11 independently proves that an
exact project/component CAPEX amount reconciles to a complete cash-flow schedule.
P33 links those two authorities. It reproduces canonical P32, rebuilds canonical
P11 from the same P5 project, and requires separate authority-level 1..3 OBS/DER
evidence that explicitly binds the P32 capex_lineage_id to the exact P11
schedule_id. Project timing milestones remain non-cash-flow evidence.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import isclose, isfinite
from typing import Iterable

from .baseline_infrastructure_contract import InfrastructureRecord
from .incremental_reinforcement_contract import (
    HeadroomScreeningContext,
    evaluate_programme_incremental_reinforcement,
)
from .limiting_node_reinforcement_lineage_contract import (
    LimitingNodeReinforcementLineageDecision,
    LimitingNodeReinforcementLinkRecord,
)
from .limiting_node_study_lineage_contract import LimitingNodeStudyLineageDecision
from .programme_incremental_capex_lineage_contract import (
    REAL_PROGRAMME_INCREMENTAL_CAPEX_LINEAGE_PROVEN,
    ProgrammeIncrementalCapexLineageDecision,
    ProgrammeIncrementalCapexLineageRecord,
    evaluate_real_programme_incremental_capex_lineage,
)
from .project_delivery_timing_contract import ProjectTimingEvidence
from .timed_investment_pathway_contract import (
    TIMED_PROGRAMME_CAPEX_PROVEN,
    CapexCashflowEvidence,
    TimedInvestmentCashflowRow,
    build_timed_investment_pathway,
)


class B10TimedProgrammeIncrementalCapexLineageError(ValueError):
    """Raised when P32 -> P11 REAL timed-CAPEX lineage is ambiguous or forged."""


TIMED_PROGRAMME_INCREMENTAL_CAPEX_LINEAGE = "TIMED_PROGRAMME_INCREMENTAL_CAPEX_LINEAGE"
REAL_TIMED_PROGRAMME_INCREMENTAL_CAPEX_LINEAGE_PROVEN = (
    "REAL_TIMED_PROGRAMME_INCREMENTAL_CAPEX_LINEAGE_PROVEN"
)
Q_REAL_TIMED_PROGRAMME_INCREMENTAL_CAPEX_LINEAGE_UNRESOLVED = (
    "Q_REAL_TIMED_PROGRAMME_INCREMENTAL_CAPEX_LINEAGE_UNRESOLVED"
)

REAL = "REAL"
EVIDENCE_STATUSES = {"OBS", "DER", "Q"}

TIMED_CAPEX_LINEAGE_ID_PREFIX = "TIMED_CAPEX_LINEAGE_ID:"
CAPEX_LINEAGE_ID_PREFIX = "CAPEX_LINEAGE_ID:"
REINFORCEMENT_LINK_ID_PREFIX = "REINFORCEMENT_LINK_ID:"
PROJECT_ID_PREFIX = "PROJECT_ID:"
NETWORK_OPERATOR_PREFIX = "NETWORK_OPERATOR:"
NETWORK_STUDY_ID_PREFIX = "NETWORK_STUDY_ID:"
STUDY_CASE_ID_PREFIX = "STUDY_CASE_ID:"
NODE_REGION_ID_PREFIX = "NODE_REGION_ID:"
HORIZON_PREFIX = "HORIZON:"
COST_COMPONENT_PREFIX = "COST_COMPONENT:"
SCHEDULE_ID_PREFIX = "SCHEDULE_ID:"
PROGRAMME_INCREMENTAL_CAPEX_HUF_PREFIX = "PROGRAMME_INCREMENTAL_CAPEX_HUF:"
TIMED_PATHWAY_STATUS_PREFIX = "TIMED_PATHWAY_STATUS:"

_TIMED_LINEAGE_AUTHORITY_MAX_LEVEL = 3


def _text(value: str, name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise B10TimedProgrammeIncrementalCapexLineageError(f"{name} is required")
    return value


def _money(value: float, name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not isfinite(value) or value < 0:
        raise B10TimedProgrammeIncrementalCapexLineageError(
            f"{name} must be finite and non-negative"
        )
    return float(value)


def _same_money(left: float | None, right: float | None) -> bool:
    if left is None or right is None:
        return left is right
    return isclose(float(left), float(right), rel_tol=0.0, abs_tol=0.5)


@dataclass(frozen=True)
class TimedProgrammeIncrementalCapexLineageEvidence:
    source_id: str
    authority_level: int
    truth_status: str
    supports: tuple[str, ...]

    def __post_init__(self) -> None:
        _text(self.source_id, "source_id")
        if self.authority_level not in {1, 2, 3, 4, 5}:
            raise B10TimedProgrammeIncrementalCapexLineageError(
                "authority_level must be 1..5"
            )
        if self.truth_status not in EVIDENCE_STATUSES:
            raise B10TimedProgrammeIncrementalCapexLineageError(
                "truth_status must be OBS, DER or Q"
            )
        if isinstance(self.supports, str):
            raise B10TimedProgrammeIncrementalCapexLineageError(
                "supports must be a collection"
            )
        if any(not isinstance(item, str) or not item.strip() for item in self.supports):
            raise B10TimedProgrammeIncrementalCapexLineageError(
                "supports cannot contain blanks"
            )


@dataclass(frozen=True)
class TimedProgrammeIncrementalCapexLineageRecord:
    timed_capex_lineage_id: str
    capex_lineage_id: str
    reinforcement_link_id: str
    project_id: str
    network_operator: str
    network_study_id: str
    study_case_id: str
    node_region_id: str
    horizon: str
    cost_component_id: str
    schedule_id: str
    programme_incremental_capex_huf: float
    source_refs: tuple[str, ...]
    evidence: tuple[TimedProgrammeIncrementalCapexLineageEvidence, ...]
    truth_context: str = REAL

    def __post_init__(self) -> None:
        for name in (
            "timed_capex_lineage_id",
            "capex_lineage_id",
            "reinforcement_link_id",
            "project_id",
            "network_operator",
            "network_study_id",
            "study_case_id",
            "node_region_id",
            "horizon",
            "cost_component_id",
            "schedule_id",
        ):
            _text(getattr(self, name), name)
        object.__setattr__(
            self,
            "programme_incremental_capex_huf",
            _money(self.programme_incremental_capex_huf, "programme_incremental_capex_huf"),
        )
        if self.truth_context != REAL:
            raise B10TimedProgrammeIncrementalCapexLineageError(
                "P33 admits REAL lineage only"
            )
        if isinstance(self.source_refs, str) or not self.source_refs:
            raise B10TimedProgrammeIncrementalCapexLineageError(
                "source_refs must be non-empty"
            )
        if isinstance(self.evidence, str) or not self.evidence:
            raise B10TimedProgrammeIncrementalCapexLineageError(
                "evidence must be non-empty"
            )
        evidence_ids = {item.source_id for item in self.evidence}
        if not set(self.source_refs).issubset(evidence_ids):
            raise B10TimedProgrammeIncrementalCapexLineageError(
                "source_refs must identify supplied timed-lineage evidence"
            )

    @property
    def referenced_evidence(self) -> tuple[TimedProgrammeIncrementalCapexLineageEvidence, ...]:
        refs = set(self.source_refs)
        return tuple(item for item in self.evidence if item.source_id in refs)


@dataclass(frozen=True)
class TimedProgrammeIncrementalCapexLineageDecision:
    timed_capex_lineage_id: str
    capex_lineage_id: str
    reinforcement_link_id: str
    project_id: str
    network_operator: str
    network_study_id: str
    study_case_id: str
    node_region_id: str
    horizon: str
    truth_context: str
    status: str
    evidence_status: str
    cost_component_id: str | None
    schedule_id: str | None
    programme_incremental_capex_huf: float | None
    cashflow_rows: tuple[TimedInvestmentCashflowRow, ...]
    source_refs: tuple[str, ...]
    reason: str

    def __post_init__(self) -> None:
        if self.truth_context != REAL:
            raise B10TimedProgrammeIncrementalCapexLineageError(
                "P33 decision must preserve REAL"
            )
        if self.status not in {
            REAL_TIMED_PROGRAMME_INCREMENTAL_CAPEX_LINEAGE_PROVEN,
            Q_REAL_TIMED_PROGRAMME_INCREMENTAL_CAPEX_LINEAGE_UNRESOLVED,
        }:
            raise B10TimedProgrammeIncrementalCapexLineageError("invalid P33 status")
        if self.status == REAL_TIMED_PROGRAMME_INCREMENTAL_CAPEX_LINEAGE_PROVEN:
            if self.evidence_status not in {"OBS", "DER"}:
                raise B10TimedProgrammeIncrementalCapexLineageError(
                    "proven P33 lineage requires OBS/DER"
                )
            if (
                self.cost_component_id is None
                or self.schedule_id is None
                or self.programme_incremental_capex_huf is None
                or not self.cashflow_rows
            ):
                raise B10TimedProgrammeIncrementalCapexLineageError(
                    "proven P33 lineage requires component, schedule, amount and cash-flow rows"
                )
        else:
            if self.evidence_status != "Q":
                raise B10TimedProgrammeIncrementalCapexLineageError(
                    "Q P33 lineage must preserve Q"
                )
            if (
                self.cost_component_id is not None
                or self.schedule_id is not None
                or self.programme_incremental_capex_huf is not None
                or self.cashflow_rows
            ):
                raise B10TimedProgrammeIncrementalCapexLineageError(
                    "Q P33 lineage must withhold component, schedule, amount and rows"
                )


def _required(record: TimedProgrammeIncrementalCapexLineageRecord) -> set[str]:
    return {
        TIMED_PROGRAMME_INCREMENTAL_CAPEX_LINEAGE,
        f"{TIMED_CAPEX_LINEAGE_ID_PREFIX}{record.timed_capex_lineage_id}",
        f"{CAPEX_LINEAGE_ID_PREFIX}{record.capex_lineage_id}",
        f"{REINFORCEMENT_LINK_ID_PREFIX}{record.reinforcement_link_id}",
        f"{PROJECT_ID_PREFIX}{record.project_id}",
        f"{NETWORK_OPERATOR_PREFIX}{record.network_operator}",
        f"{NETWORK_STUDY_ID_PREFIX}{record.network_study_id}",
        f"{STUDY_CASE_ID_PREFIX}{record.study_case_id}",
        f"{NODE_REGION_ID_PREFIX}{record.node_region_id}",
        f"{HORIZON_PREFIX}{record.horizon}",
        f"{COST_COMPONENT_PREFIX}{record.cost_component_id}",
        f"{SCHEDULE_ID_PREFIX}{record.schedule_id}",
        f"{PROGRAMME_INCREMENTAL_CAPEX_HUF_PREFIX}{record.programme_incremental_capex_huf}",
        f"{TIMED_PATHWAY_STATUS_PREFIX}{TIMED_PROGRAMME_CAPEX_PROVEN}",
    }


def _qualifying(
    record: TimedProgrammeIncrementalCapexLineageRecord,
) -> tuple[TimedProgrammeIncrementalCapexLineageEvidence, ...]:
    required = _required(record)
    return tuple(
        item
        for item in record.referenced_evidence
        if item.authority_level <= _TIMED_LINEAGE_AUTHORITY_MAX_LEVEL
        and item.truth_status in {"OBS", "DER"}
        and required.issubset(set(item.supports))
    )


def evaluate_real_timed_programme_incremental_capex_lineage(
    timed_lineage: TimedProgrammeIncrementalCapexLineageRecord,
    *,
    capex_lineage: ProgrammeIncrementalCapexLineageDecision,
    capex_lineage_record: ProgrammeIncrementalCapexLineageRecord,
    reinforcement_lineage: LimitingNodeReinforcementLineageDecision,
    reinforcement_link: LimitingNodeReinforcementLinkRecord,
    limiting_node_lineage: LimitingNodeStudyLineageDecision,
    reinforcement_record: InfrastructureRecord,
    target_timing: ProjectTimingEvidence,
    actual_timing: ProjectTimingEvidence | None = None,
    cashflow_evidence: Iterable[CapexCashflowEvidence] = (),
    screening: HeadroomScreeningContext | None = None,
) -> TimedProgrammeIncrementalCapexLineageDecision:
    """Link canonical P32 numeric CAPEX to a canonical REAL P11 cash-flow schedule."""

    if not isinstance(timed_lineage, TimedProgrammeIncrementalCapexLineageRecord):
        raise B10TimedProgrammeIncrementalCapexLineageError(
            "timed_lineage must be TimedProgrammeIncrementalCapexLineageRecord"
        )
    if not isinstance(capex_lineage, ProgrammeIncrementalCapexLineageDecision):
        raise B10TimedProgrammeIncrementalCapexLineageError(
            "capex_lineage must be ProgrammeIncrementalCapexLineageDecision"
        )

    expected_p32 = evaluate_real_programme_incremental_capex_lineage(
        capex_lineage_record,
        reinforcement_lineage=reinforcement_lineage,
        reinforcement_link=reinforcement_link,
        limiting_node_lineage=limiting_node_lineage,
        reinforcement_record=reinforcement_record,
        screening=screening,
    )
    if capex_lineage != expected_p32:
        raise B10TimedProgrammeIncrementalCapexLineageError(
            "supplied P32 decision does not reproduce canonical P32 authority"
        )

    base_refs = set(timed_lineage.source_refs) | set(capex_lineage.source_refs)

    def q(reason: str, extra_refs: Iterable[str] = ()) -> TimedProgrammeIncrementalCapexLineageDecision:
        return TimedProgrammeIncrementalCapexLineageDecision(
            timed_lineage.timed_capex_lineage_id,
            timed_lineage.capex_lineage_id,
            timed_lineage.reinforcement_link_id,
            timed_lineage.project_id,
            timed_lineage.network_operator,
            timed_lineage.network_study_id,
            timed_lineage.study_case_id,
            timed_lineage.node_region_id,
            timed_lineage.horizon,
            REAL,
            Q_REAL_TIMED_PROGRAMME_INCREMENTAL_CAPEX_LINEAGE_UNRESOLVED,
            "Q",
            None,
            None,
            None,
            (),
            tuple(sorted(base_refs | set(extra_refs))),
            reason,
        )

    if capex_lineage.status != REAL_PROGRAMME_INCREMENTAL_CAPEX_LINEAGE_PROVEN:
        return q("canonical P32 REAL programme-incremental CAPEX lineage is not proven")

    p32_pairs = (
        (timed_lineage.capex_lineage_id, capex_lineage.capex_lineage_id, "capex_lineage_id"),
        (
            timed_lineage.reinforcement_link_id,
            capex_lineage.reinforcement_link_id,
            "reinforcement_link_id",
        ),
        (timed_lineage.project_id, capex_lineage.project_id, "project_id"),
        (timed_lineage.network_operator, capex_lineage.network_operator, "network_operator"),
        (timed_lineage.network_study_id, capex_lineage.network_study_id, "network_study_id"),
        (timed_lineage.study_case_id, capex_lineage.study_case_id, "study_case_id"),
        (timed_lineage.node_region_id, capex_lineage.node_region_id, "node_region_id"),
        (timed_lineage.horizon, capex_lineage.horizon, "horizon"),
        (timed_lineage.cost_component_id, capex_lineage.cost_component_id, "cost_component_id"),
    )
    for candidate, proven, name in p32_pairs:
        if candidate != proven:
            return q(f"timed CAPEX lineage {name} does not match exact proven P32 lineage")
    if not _same_money(
        timed_lineage.programme_incremental_capex_huf,
        capex_lineage.programme_incremental_capex_huf,
    ):
        return q("timed CAPEX lineage amount does not reproduce exact P32 CAPEX")

    p5 = evaluate_programme_incremental_reinforcement(
        reinforcement_record,
        reinforcement_horizon=timed_lineage.horizon,
        screening=None,
    )
    cashflows = tuple(cashflow_evidence)
    pathway = build_timed_investment_pathway(
        reinforcement_record,
        p5,
        target_timing,
        actual_timing,
        cashflows,
    )
    pathway_refs = set(pathway.source_refs)
    if pathway.status != TIMED_PROGRAMME_CAPEX_PROVEN:
        return q(
            "canonical P11 does not prove a REAL complete programme-incremental CAPEX schedule",
            pathway_refs,
        )
    if pathway.project_id != timed_lineage.project_id:
        return q("P11 project_id does not match P32/P33 lineage", pathway_refs)
    if pathway.network_operator != timed_lineage.network_operator:
        return q("P11 network_operator does not match P32/P33 lineage", pathway_refs)
    if pathway.region_id != timed_lineage.node_region_id:
        return q("P11 region_id does not match exact P32/P33 node", pathway_refs)
    if pathway.horizon != timed_lineage.horizon:
        return q("P11 horizon does not match P32/P33 lineage", pathway_refs)
    if not _same_money(
        pathway.untimed_programme_incremental_capex_huf,
        timed_lineage.programme_incremental_capex_huf,
    ):
        return q("P11 untimed CAPEX does not reproduce exact P32/P33 CAPEX", pathway_refs)
    if not pathway.cashflow_rows:
        return q("P11 proven pathway unexpectedly has no cash-flow rows", pathway_refs)

    schedule_ids = {row.schedule_id for row in pathway.cashflow_rows}
    components = {row.cost_component_id for row in pathway.cashflow_rows}
    if schedule_ids != {timed_lineage.schedule_id}:
        return q("P11 schedule_id does not match exact P33 schedule lineage", pathway_refs)
    if components != {timed_lineage.cost_component_id}:
        return q("P11 cash-flow component does not match exact P32/P33 component", pathway_refs)
    scheduled_total = sum(row.programme_incremental_capex_huf for row in pathway.cashflow_rows)
    if not _same_money(scheduled_total, timed_lineage.programme_incremental_capex_huf):
        return q("P11 schedule total does not reconcile to exact P32/P33 CAPEX", pathway_refs)

    matches = _qualifying(timed_lineage)
    if not matches:
        return q(
            "no referenced authority-level 1..3 OBS/DER evidence explicitly binds the exact "
            "P32 capex_lineage_id to the exact P11 complete schedule_id",
            pathway_refs,
        )

    link_status = "OBS" if all(item.truth_status == "OBS" for item in matches) else "DER"
    evidence_status = (
        "OBS"
        if capex_lineage.evidence_status == "OBS"
        and all(row.evidence_status == "OBS" for row in pathway.cashflow_rows)
        and link_status == "OBS"
        else "DER"
    )
    refs = tuple(sorted(base_refs | pathway_refs | {item.source_id for item in matches}))
    return TimedProgrammeIncrementalCapexLineageDecision(
        timed_lineage.timed_capex_lineage_id,
        timed_lineage.capex_lineage_id,
        timed_lineage.reinforcement_link_id,
        timed_lineage.project_id,
        timed_lineage.network_operator,
        timed_lineage.network_study_id,
        timed_lineage.study_case_id,
        timed_lineage.node_region_id,
        timed_lineage.horizon,
        REAL,
        REAL_TIMED_PROGRAMME_INCREMENTAL_CAPEX_LINEAGE_PROVEN,
        evidence_status,
        timed_lineage.cost_component_id,
        timed_lineage.schedule_id,
        timed_lineage.programme_incremental_capex_huf,
        pathway.cashflow_rows,
        refs,
        (
            "canonical P32 authority and canonical REAL P11 complete cash-flow schedule are "
            "reproduced, and separate evidence binds the exact capex_lineage_id to schedule_id"
        ),
    )


def require_real_timed_programme_incremental_capex_lineage(
    decision: TimedProgrammeIncrementalCapexLineageDecision,
) -> tuple[str, str, float]:
    if not isinstance(decision, TimedProgrammeIncrementalCapexLineageDecision):
        raise B10TimedProgrammeIncrementalCapexLineageError(
            "decision must be TimedProgrammeIncrementalCapexLineageDecision"
        )
    if decision.status != REAL_TIMED_PROGRAMME_INCREMENTAL_CAPEX_LINEAGE_PROVEN:
        raise B10TimedProgrammeIncrementalCapexLineageError(
            "proven REAL timed programme-incremental CAPEX lineage is required"
        )
    assert decision.cost_component_id is not None
    assert decision.schedule_id is not None
    assert decision.programme_incremental_capex_huf is not None
    return (
        decision.cost_component_id,
        decision.schedule_id,
        decision.programme_incremental_capex_huf,
    )


__all__ = [
    "B10TimedProgrammeIncrementalCapexLineageError",
    "Q_REAL_TIMED_PROGRAMME_INCREMENTAL_CAPEX_LINEAGE_UNRESOLVED",
    "REAL_TIMED_PROGRAMME_INCREMENTAL_CAPEX_LINEAGE_PROVEN",
    "TIMED_PROGRAMME_INCREMENTAL_CAPEX_LINEAGE",
    "TimedProgrammeIncrementalCapexLineageDecision",
    "TimedProgrammeIncrementalCapexLineageEvidence",
    "TimedProgrammeIncrementalCapexLineageRecord",
    "evaluate_real_timed_programme_incremental_capex_lineage",
    "require_real_timed_programme_incremental_capex_lineage",
]
