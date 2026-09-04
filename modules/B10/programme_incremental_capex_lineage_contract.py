"""B10-P32 fail-closed REAL reinforcement -> programme-incremental CAPEX lineage gate.

Core rules:

    P31 REINFORCEMENT LINK != PROGRAMME-INCREMENTAL CAPEX
    P5 NUMERIC CAPEX != P31-LINKED NUMERIC CAPEX
    SAME PROJECT != SAME COST COMPONENT
    TOTAL PROJECT COST != PROGRAMME-INCREMENTAL CAPEX
    CUSTOMER CONNECTION CHARGE != PROGRAMME-INCREMENTAL CAPEX
    HANDCRAFTED P31 DECISION != CANONICAL P31 AUTHORITY

P31 links an exact P30 limiting-node lineage to an independently P5-proven
reinforcement project, but deliberately withholds numeric CAPEX. P32 closes the
next boundary. It reproduces canonical P31 authority, reproduces canonical P5
numeric programme-incremental CAPEX from the same InfrastructureRecord, and then
requires separate component-specific lineage evidence linking that exact amount
and cost component to the exact P31 reinforcement_link_id/study/case/node/horizon.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import isfinite

from .baseline_infrastructure_contract import (
    PROGRAM_ACCELERATED,
    PROGRAM_INCREMENTAL,
    InfrastructureRecord,
)
from .incremental_reinforcement_contract import (
    B10IncrementalReinforcementContractError,
    HeadroomScreeningContext,
    evaluate_programme_incremental_reinforcement,
)
from .limiting_node_reinforcement_lineage_contract import (
    REAL_LIMITING_NODE_REINFORCEMENT_LINK_PROVEN,
    LimitingNodeReinforcementLineageDecision,
    LimitingNodeReinforcementLinkRecord,
    evaluate_real_limiting_node_reinforcement_lineage,
)
from .limiting_node_study_lineage_contract import LimitingNodeStudyLineageDecision


class B10ProgrammeIncrementalCapexLineageError(ValueError):
    """Raised when REAL programme-incremental CAPEX lineage is ambiguous or forged."""


PROGRAMME_INCREMENTAL_CAPEX_LINEAGE = "PROGRAMME_INCREMENTAL_CAPEX_LINEAGE"
REAL_PROGRAMME_INCREMENTAL_CAPEX_LINEAGE_PROVEN = (
    "REAL_PROGRAMME_INCREMENTAL_CAPEX_LINEAGE_PROVEN"
)
Q_REAL_PROGRAMME_INCREMENTAL_CAPEX_LINEAGE_UNRESOLVED = (
    "Q_REAL_PROGRAMME_INCREMENTAL_CAPEX_LINEAGE_UNRESOLVED"
)

REAL = "REAL"
EVIDENCE_STATUSES = {"OBS", "DER", "Q"}

CAPEX_LINEAGE_ID_PREFIX = "CAPEX_LINEAGE_ID:"
REINFORCEMENT_LINK_ID_PREFIX = "REINFORCEMENT_LINK_ID:"
PROJECT_ID_PREFIX = "PROJECT_ID:"
NETWORK_OPERATOR_PREFIX = "NETWORK_OPERATOR:"
NETWORK_STUDY_ID_PREFIX = "NETWORK_STUDY_ID:"
STUDY_CASE_ID_PREFIX = "STUDY_CASE_ID:"
NODE_REGION_ID_PREFIX = "NODE_REGION_ID:"
HORIZON_PREFIX = "HORIZON:"
COST_COMPONENT_PREFIX = "COST_COMPONENT:"
PROGRAMME_INCREMENTAL_CAPEX_HUF_PREFIX = "PROGRAMME_INCREMENTAL_CAPEX_HUF:"
ATTRIBUTION_STATUS_PREFIX = "ATTRIBUTION_STATUS:"

_CAPEX_LINEAGE_AUTHORITY_MAX_LEVEL = 3
_ALLOWED_ATTRIBUTION_STATUSES = {PROGRAM_INCREMENTAL, PROGRAM_ACCELERATED}


def _text(value: str, name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise B10ProgrammeIncrementalCapexLineageError(f"{name} is required")
    return value


def _money(value: float, name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not isfinite(value) or value < 0:
        raise B10ProgrammeIncrementalCapexLineageError(f"{name} must be finite and non-negative")
    return float(value)


@dataclass(frozen=True)
class ProgrammeIncrementalCapexLineageEvidence:
    source_id: str
    authority_level: int
    truth_status: str
    supports: tuple[str, ...]

    def __post_init__(self) -> None:
        _text(self.source_id, "source_id")
        if self.authority_level not in {1, 2, 3, 4, 5}:
            raise B10ProgrammeIncrementalCapexLineageError("authority_level must be 1..5")
        if self.truth_status not in EVIDENCE_STATUSES:
            raise B10ProgrammeIncrementalCapexLineageError("truth_status must be OBS, DER or Q")
        if isinstance(self.supports, str):
            raise B10ProgrammeIncrementalCapexLineageError("supports must be a collection")
        if any(not isinstance(item, str) or not item.strip() for item in self.supports):
            raise B10ProgrammeIncrementalCapexLineageError("supports cannot contain blanks")


@dataclass(frozen=True)
class ProgrammeIncrementalCapexLineageRecord:
    capex_lineage_id: str
    reinforcement_link_id: str
    project_id: str
    network_operator: str
    network_study_id: str
    study_case_id: str
    node_region_id: str
    horizon: str
    cost_component_id: str
    programme_incremental_capex_huf: float
    attribution_status: str
    source_refs: tuple[str, ...]
    evidence: tuple[ProgrammeIncrementalCapexLineageEvidence, ...]
    truth_context: str = REAL

    def __post_init__(self) -> None:
        for name in (
            "capex_lineage_id",
            "reinforcement_link_id",
            "project_id",
            "network_operator",
            "network_study_id",
            "study_case_id",
            "node_region_id",
            "horizon",
            "cost_component_id",
        ):
            _text(getattr(self, name), name)
        object.__setattr__(
            self,
            "programme_incremental_capex_huf",
            _money(self.programme_incremental_capex_huf, "programme_incremental_capex_huf"),
        )
        if self.attribution_status not in _ALLOWED_ATTRIBUTION_STATUSES:
            raise B10ProgrammeIncrementalCapexLineageError(
                "attribution_status must be PROGRAM_INCREMENTAL or PROGRAM_ACCELERATED_OR_UPSIZED"
            )
        if self.truth_context != REAL:
            raise B10ProgrammeIncrementalCapexLineageError("P32 admits REAL lineage only")
        if isinstance(self.source_refs, str) or not self.source_refs:
            raise B10ProgrammeIncrementalCapexLineageError("source_refs must be non-empty")
        if isinstance(self.evidence, str) or not self.evidence:
            raise B10ProgrammeIncrementalCapexLineageError("evidence must be non-empty")
        evidence_ids = {item.source_id for item in self.evidence}
        if not set(self.source_refs).issubset(evidence_ids):
            raise B10ProgrammeIncrementalCapexLineageError(
                "source_refs must identify supplied CAPEX-lineage evidence"
            )

    @property
    def referenced_evidence(self) -> tuple[ProgrammeIncrementalCapexLineageEvidence, ...]:
        refs = set(self.source_refs)
        return tuple(item for item in self.evidence if item.source_id in refs)


@dataclass(frozen=True)
class ProgrammeIncrementalCapexLineageDecision:
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
    programme_incremental_capex_huf: float | None
    attribution_status: str | None
    source_refs: tuple[str, ...]
    reason: str

    def __post_init__(self) -> None:
        if self.truth_context != REAL:
            raise B10ProgrammeIncrementalCapexLineageError("P32 decision must preserve REAL")
        if self.status not in {
            REAL_PROGRAMME_INCREMENTAL_CAPEX_LINEAGE_PROVEN,
            Q_REAL_PROGRAMME_INCREMENTAL_CAPEX_LINEAGE_UNRESOLVED,
        }:
            raise B10ProgrammeIncrementalCapexLineageError("invalid P32 status")
        if self.status == REAL_PROGRAMME_INCREMENTAL_CAPEX_LINEAGE_PROVEN:
            if self.evidence_status not in {"OBS", "DER"}:
                raise B10ProgrammeIncrementalCapexLineageError("proven P32 lineage requires OBS/DER")
            if self.cost_component_id is None or self.programme_incremental_capex_huf is None:
                raise B10ProgrammeIncrementalCapexLineageError(
                    "proven P32 lineage requires exact component and numeric CAPEX"
                )
            if self.attribution_status not in _ALLOWED_ATTRIBUTION_STATUSES:
                raise B10ProgrammeIncrementalCapexLineageError(
                    "proven P32 lineage requires programme incremental/accelerated attribution"
                )
        else:
            if self.evidence_status != "Q":
                raise B10ProgrammeIncrementalCapexLineageError("Q P32 lineage must preserve Q")
            if (
                self.cost_component_id is not None
                or self.programme_incremental_capex_huf is not None
                or self.attribution_status is not None
            ):
                raise B10ProgrammeIncrementalCapexLineageError(
                    "Q P32 lineage must withhold authoritative component, amount and attribution"
                )


def _required(record: ProgrammeIncrementalCapexLineageRecord) -> set[str]:
    return {
        PROGRAMME_INCREMENTAL_CAPEX_LINEAGE,
        f"{CAPEX_LINEAGE_ID_PREFIX}{record.capex_lineage_id}",
        f"{REINFORCEMENT_LINK_ID_PREFIX}{record.reinforcement_link_id}",
        f"{PROJECT_ID_PREFIX}{record.project_id}",
        f"{NETWORK_OPERATOR_PREFIX}{record.network_operator}",
        f"{NETWORK_STUDY_ID_PREFIX}{record.network_study_id}",
        f"{STUDY_CASE_ID_PREFIX}{record.study_case_id}",
        f"{NODE_REGION_ID_PREFIX}{record.node_region_id}",
        f"{HORIZON_PREFIX}{record.horizon}",
        f"{COST_COMPONENT_PREFIX}{record.cost_component_id}",
        f"{PROGRAMME_INCREMENTAL_CAPEX_HUF_PREFIX}{record.programme_incremental_capex_huf}",
        f"{ATTRIBUTION_STATUS_PREFIX}{record.attribution_status}",
    }


def _qualifying(
    record: ProgrammeIncrementalCapexLineageRecord,
) -> tuple[ProgrammeIncrementalCapexLineageEvidence, ...]:
    required = _required(record)
    return tuple(
        item
        for item in record.referenced_evidence
        if item.authority_level <= _CAPEX_LINEAGE_AUTHORITY_MAX_LEVEL
        and item.truth_status in {"OBS", "DER"}
        and required.issubset(set(item.supports))
    )


def evaluate_real_programme_incremental_capex_lineage(
    capex_lineage: ProgrammeIncrementalCapexLineageRecord,
    *,
    reinforcement_lineage: LimitingNodeReinforcementLineageDecision,
    reinforcement_link: LimitingNodeReinforcementLinkRecord,
    limiting_node_lineage: LimitingNodeStudyLineageDecision,
    reinforcement_record: InfrastructureRecord,
    screening: HeadroomScreeningContext | None = None,
) -> ProgrammeIncrementalCapexLineageDecision:
    """Admit numeric CAPEX only after reproducing canonical P31 and P5 authority."""

    if not isinstance(capex_lineage, ProgrammeIncrementalCapexLineageRecord):
        raise B10ProgrammeIncrementalCapexLineageError(
            "capex_lineage must be ProgrammeIncrementalCapexLineageRecord"
        )
    if not isinstance(reinforcement_lineage, LimitingNodeReinforcementLineageDecision):
        raise B10ProgrammeIncrementalCapexLineageError(
            "reinforcement_lineage must be LimitingNodeReinforcementLineageDecision"
        )
    if not isinstance(reinforcement_link, LimitingNodeReinforcementLinkRecord):
        raise B10ProgrammeIncrementalCapexLineageError(
            "reinforcement_link must be LimitingNodeReinforcementLinkRecord"
        )
    if not isinstance(limiting_node_lineage, LimitingNodeStudyLineageDecision):
        raise B10ProgrammeIncrementalCapexLineageError(
            "limiting_node_lineage must be LimitingNodeStudyLineageDecision"
        )
    if not isinstance(reinforcement_record, InfrastructureRecord):
        raise B10ProgrammeIncrementalCapexLineageError(
            "reinforcement_record must be InfrastructureRecord"
        )

    expected_p31 = evaluate_real_limiting_node_reinforcement_lineage(
        reinforcement_link,
        limiting_node_lineage=limiting_node_lineage,
        reinforcement_record=reinforcement_record,
        screening=screening,
    )
    if reinforcement_lineage != expected_p31:
        raise B10ProgrammeIncrementalCapexLineageError(
            "supplied P31 decision does not reproduce canonical P31 authority"
        )

    refs = tuple(
        sorted(
            set(capex_lineage.source_refs)
            | set(reinforcement_lineage.source_refs)
            | set(reinforcement_record.source_refs)
        )
    )

    def q(reason: str) -> ProgrammeIncrementalCapexLineageDecision:
        return ProgrammeIncrementalCapexLineageDecision(
            capex_lineage.capex_lineage_id,
            capex_lineage.reinforcement_link_id,
            capex_lineage.project_id,
            capex_lineage.network_operator,
            capex_lineage.network_study_id,
            capex_lineage.study_case_id,
            capex_lineage.node_region_id,
            capex_lineage.horizon,
            REAL,
            Q_REAL_PROGRAMME_INCREMENTAL_CAPEX_LINEAGE_UNRESOLVED,
            "Q",
            None,
            None,
            None,
            refs,
            reason,
        )

    if reinforcement_lineage.status != REAL_LIMITING_NODE_REINFORCEMENT_LINK_PROVEN:
        return q("canonical P31 REAL limiting-node reinforcement lineage is not proven")

    lineage_pairs = (
        (capex_lineage.reinforcement_link_id, reinforcement_lineage.reinforcement_link_id, "reinforcement_link_id"),
        (capex_lineage.project_id, reinforcement_lineage.project_id, "project_id"),
        (capex_lineage.network_operator, reinforcement_lineage.network_operator, "network_operator"),
        (capex_lineage.network_study_id, reinforcement_lineage.network_study_id, "network_study_id"),
        (capex_lineage.study_case_id, reinforcement_lineage.study_case_id, "study_case_id"),
        (capex_lineage.node_region_id, reinforcement_lineage.node_region_id, "node_region_id"),
        (capex_lineage.horizon, reinforcement_lineage.horizon, "horizon"),
    )
    for candidate, proven, name in lineage_pairs:
        if candidate != proven:
            return q(f"CAPEX lineage {name} does not match the exact proven P31 lineage")

    if reinforcement_record.project_id != capex_lineage.project_id:
        return q("P5 project_id does not match P32 CAPEX lineage")
    if reinforcement_record.network_operator != capex_lineage.network_operator:
        return q("P5 network_operator does not match P32 CAPEX lineage")
    if reinforcement_record.region_id != capex_lineage.node_region_id:
        return q("P5 exact node does not match P32 CAPEX lineage")
    if reinforcement_record.cost_component_id != capex_lineage.cost_component_id:
        return q("P5 cost_component_id does not match P32 CAPEX lineage")

    try:
        p5 = evaluate_programme_incremental_reinforcement(
            reinforcement_record,
            reinforcement_horizon=capex_lineage.horizon,
            screening=screening,
        )
    except B10IncrementalReinforcementContractError as exc:
        return q(f"canonical P5 CAPEX gate rejected the linked project: {exc}")

    if not p5.reinforcement_required_proven:
        return q("canonical P5 does not preserve REINFORCEMENT_REQUIRED")
    if p5.attribution.attribution_status != reinforcement_lineage.attribution_status:
        return q("canonical P5 attribution does not match the proven P31 attribution")
    if p5.attribution.attribution_status not in _ALLOWED_ATTRIBUTION_STATUSES:
        return q("P5 attribution is not programme incremental or accelerated/up-sized")
    if p5.program_incremental_capex_huf is None:
        return q("P5 programme-incremental CAPEX remains unquantified; missing is not zero")
    if p5.program_incremental_capex_huf != capex_lineage.programme_incremental_capex_huf:
        return q("P32 numeric CAPEX does not exactly reproduce canonical P5 numeric CAPEX")
    if p5.attribution.attribution_status != capex_lineage.attribution_status:
        return q("P32 attribution_status does not exactly reproduce canonical P5 attribution")

    matches = _qualifying(capex_lineage)
    if not matches:
        return q(
            "no referenced authority-level 1-3 OBS/DER evidence explicitly binds the exact P31 "
            "reinforcement lineage to the exact P5 cost component and numeric programme-incremental CAPEX"
        )

    lineage_status = "OBS" if all(item.truth_status == "OBS" for item in matches) else "DER"
    evidence_status = (
        "OBS"
        if reinforcement_lineage.evidence_status == "OBS" and lineage_status == "OBS"
        else "DER"
    )
    return ProgrammeIncrementalCapexLineageDecision(
        capex_lineage.capex_lineage_id,
        capex_lineage.reinforcement_link_id,
        capex_lineage.project_id,
        capex_lineage.network_operator,
        capex_lineage.network_study_id,
        capex_lineage.study_case_id,
        capex_lineage.node_region_id,
        capex_lineage.horizon,
        REAL,
        REAL_PROGRAMME_INCREMENTAL_CAPEX_LINEAGE_PROVEN,
        evidence_status,
        capex_lineage.cost_component_id,
        capex_lineage.programme_incremental_capex_huf,
        capex_lineage.attribution_status,
        refs,
        (
            "canonical P31 and P5 authority are reproduced and separate component-specific evidence "
            "binds the exact programme-incremental CAPEX amount to the exact reinforcement lineage"
        ),
    )


def require_real_programme_incremental_capex_lineage(
    decision: ProgrammeIncrementalCapexLineageDecision,
) -> tuple[str, float]:
    if not isinstance(decision, ProgrammeIncrementalCapexLineageDecision):
        raise B10ProgrammeIncrementalCapexLineageError(
            "decision must be ProgrammeIncrementalCapexLineageDecision"
        )
    if decision.status != REAL_PROGRAMME_INCREMENTAL_CAPEX_LINEAGE_PROVEN:
        raise B10ProgrammeIncrementalCapexLineageError(
            "proven REAL programme-incremental CAPEX lineage is required"
        )
    assert decision.cost_component_id is not None
    assert decision.programme_incremental_capex_huf is not None
    return decision.cost_component_id, decision.programme_incremental_capex_huf


__all__ = [
    "B10ProgrammeIncrementalCapexLineageError",
    "PROGRAMME_INCREMENTAL_CAPEX_LINEAGE",
    "ProgrammeIncrementalCapexLineageDecision",
    "ProgrammeIncrementalCapexLineageEvidence",
    "ProgrammeIncrementalCapexLineageRecord",
    "Q_REAL_PROGRAMME_INCREMENTAL_CAPEX_LINEAGE_UNRESOLVED",
    "REAL_PROGRAMME_INCREMENTAL_CAPEX_LINEAGE_PROVEN",
    "evaluate_real_programme_incremental_capex_lineage",
    "require_real_programme_incremental_capex_lineage",
]
