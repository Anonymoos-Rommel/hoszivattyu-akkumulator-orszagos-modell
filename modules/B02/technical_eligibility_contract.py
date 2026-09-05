"""B02-P2 fail-closed technical eligibility and S2-readiness admission contract.

This module turns the existing P1-I/P1-J/P1-K evidence rules into an executable
boundary without manufacturing a national eligible-dwelling count.

Core separations:

PHYSICAL SCREENING SCOPE != TECHNICAL ELIGIBILITY != S2 TRANSITION READINESS
!= LEGAL/ECONOMIC PROGRAMME ELIGIBILITY.

A missing value is Q. A technical FAIL is allowed only with explicit OBS/DER
evidence. ASS/SCN/POL evidence can never prove a real household technically
eligible or technically blocked.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Iterable


ROOT = Path(__file__).resolve().parents[2]
GAP_MATRIX_PATH = ROOT / "registry" / "b02_s0_s2_evidence_gap_matrix.csv"
B01_ROLLOUT_PATH = ROOT / "registry" / "b01_national_rollout_policy_contract.csv"

REAL_EVIDENCE_STATUSES = frozenset({"OBS", "DER"})
EVIDENCE_STATUSES = frozenset({"OBS", "DER", "Q"})
GATE_DECISIONS = frozenset({"PASS", "FAIL", "Q"})
SCOPE_DECISIONS = frozenset({"IN_SCOPE", "OUT_OF_SCOPE", "Q"})

THERMAL_DISTRIBUTION = "THERMAL_DISTRIBUTION"
HYDRAULIC = "HYDRAULIC"
ELECTRICAL = "ELECTRICAL"
PERMIT = "PERMIT"
REQUIRED_TECHNICAL_COMPONENTS = (
    THERMAL_DISTRIBUTION,
    HYDRAULIC,
    ELECTRICAL,
    PERMIT,
)

ELIGIBLE = "ELIGIBLE"
BLOCKED = "BLOCKED"
Q = "Q"
OUT_OF_SCOPE = "OUT_OF_SCOPE"

S2_READY = "S2_READY"
S2_BLOCKED = "S2_BLOCKED"
S2_Q = "S2_Q"

CURRENT_REQUIRED_GAP_IDS = (
    "GAP-B02-S2-HEAT-EMITTER",
    "GAP-B02-S2-DESIGN-TEMPERATURE",
    "GAP-B02-S2-HYDRAULIC",
    "GAP-B02-S2-ELECTRICAL",
    "GAP-B02-S2-PERMIT",
)


class B02EligibilityError(ValueError):
    """Raised when an input weakens the B02 evidence boundary."""


def _nonempty(value: str, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise B02EligibilityError(f"{field} must be non-empty")
    return value.strip()


def _refs(value: tuple[str, ...], field: str, *, required: bool) -> None:
    if any(not isinstance(ref, str) or not ref.strip() for ref in value):
        raise B02EligibilityError(f"{field} cannot contain empty references")
    if required and not value:
        raise B02EligibilityError(f"{field} requires at least one evidence reference")


def _iso_date(value: str, field: str) -> None:
    try:
        date.fromisoformat(_nonempty(value, field))
    except ValueError as exc:
        raise B02EligibilityError(f"{field} must be an ISO date") from exc


def _combined_real_status(statuses: Iterable[str]) -> str:
    values = tuple(statuses)
    if not values or any(value not in REAL_EVIDENCE_STATUSES for value in values):
        return Q
    return "DER" if "DER" in values else "OBS"


@dataclass(frozen=True)
class PhysicalScopeEvidence:
    decision: str
    evidence_status: str
    evidence_refs: tuple[str, ...]
    criterion_ref: str

    def validate(self) -> None:
        if self.decision not in SCOPE_DECISIONS:
            raise B02EligibilityError(f"invalid physical-scope decision: {self.decision!r}")
        if self.evidence_status not in EVIDENCE_STATUSES:
            raise B02EligibilityError(f"invalid physical-scope evidence status: {self.evidence_status!r}")
        _nonempty(self.criterion_ref, "physical_scope.criterion_ref")
        if self.decision == Q:
            if self.evidence_status != Q:
                raise B02EligibilityError("Q physical scope must carry Q evidence status")
            _refs(self.evidence_refs, "physical_scope.evidence_refs", required=False)
        else:
            if self.evidence_status not in REAL_EVIDENCE_STATUSES:
                raise B02EligibilityError("IN_SCOPE/OUT_OF_SCOPE requires OBS/DER evidence")
            _refs(self.evidence_refs, "physical_scope.evidence_refs", required=True)


@dataclass(frozen=True)
class TechnicalComponentEvidence:
    component_id: str
    decision: str
    evidence_status: str
    evidence_refs: tuple[str, ...]
    criterion_ref: str

    def validate(self) -> None:
        if self.component_id not in REQUIRED_TECHNICAL_COMPONENTS:
            raise B02EligibilityError(f"unknown technical component: {self.component_id!r}")
        if self.decision not in GATE_DECISIONS:
            raise B02EligibilityError(f"invalid component decision: {self.decision!r}")
        if self.evidence_status not in EVIDENCE_STATUSES:
            raise B02EligibilityError(f"invalid component evidence status: {self.evidence_status!r}")
        _nonempty(self.criterion_ref, f"{self.component_id}.criterion_ref")
        if self.decision == Q:
            if self.evidence_status != Q:
                raise B02EligibilityError(f"Q {self.component_id} decision must carry Q evidence")
            _refs(self.evidence_refs, f"{self.component_id}.evidence_refs", required=False)
        else:
            if self.evidence_status not in REAL_EVIDENCE_STATUSES:
                raise B02EligibilityError(
                    f"{self.component_id} PASS/FAIL requires OBS/DER evidence"
                )
            _refs(self.evidence_refs, f"{self.component_id}.evidence_refs", required=True)


@dataclass(frozen=True)
class TechnicalEligibilityRecord:
    record_id: str
    as_of: str
    physical_scope: PhysicalScopeEvidence
    components: tuple[TechnicalComponentEvidence, ...]

    def validate(self) -> None:
        _nonempty(self.record_id, "record_id")
        _iso_date(self.as_of, "as_of")
        self.physical_scope.validate()
        seen: set[str] = set()
        for component in self.components:
            component.validate()
            if component.component_id in seen:
                raise B02EligibilityError(f"duplicate component: {component.component_id!r}")
            seen.add(component.component_id)
        missing = set(REQUIRED_TECHNICAL_COMPONENTS) - seen
        extra = seen - set(REQUIRED_TECHNICAL_COMPONENTS)
        if missing or extra:
            raise B02EligibilityError(
                f"technical component set must be exact; missing={sorted(missing)} extra={sorted(extra)}"
            )


@dataclass(frozen=True)
class TechnicalEligibilityDecision:
    record_id: str
    status: str
    evidence_status: str
    blocked_components: tuple[str, ...]
    unresolved_components: tuple[str, ...]
    reason: str


@dataclass(frozen=True)
class PredecessorGateEvidence:
    decision: str
    evidence_status: str
    evidence_refs: tuple[str, ...]
    gate_ref: str = "demand_reduction_measured_or_not_required"

    def validate(self) -> None:
        if self.decision not in GATE_DECISIONS:
            raise B02EligibilityError(f"invalid predecessor decision: {self.decision!r}")
        if self.evidence_status not in EVIDENCE_STATUSES:
            raise B02EligibilityError(f"invalid predecessor evidence status: {self.evidence_status!r}")
        _nonempty(self.gate_ref, "predecessor.gate_ref")
        if self.decision == Q:
            if self.evidence_status != Q:
                raise B02EligibilityError("Q predecessor must carry Q evidence")
            _refs(self.evidence_refs, "predecessor.evidence_refs", required=False)
        else:
            if self.evidence_status not in REAL_EVIDENCE_STATUSES:
                raise B02EligibilityError("PASS/FAIL predecessor requires OBS/DER evidence")
            _refs(self.evidence_refs, "predecessor.evidence_refs", required=True)


@dataclass(frozen=True)
class S2TransitionDecision:
    status: str
    evidence_status: str
    reason: str


@dataclass(frozen=True)
class CurrentRepositoryEligibilityGate:
    status: str
    eligible_dwellings: int | None
    physical_screening_reference_households: int
    physical_screening_reference_status: str
    blocking_gap_ids: tuple[str, ...]
    source_refs: tuple[str, ...]


def assess_technical_eligibility(record: TechnicalEligibilityRecord) -> TechnicalEligibilityDecision:
    """Evaluate a real record without converting missing evidence into eligibility or failure."""
    record.validate()
    scope = record.physical_scope
    by_component = {item.component_id: item for item in record.components}

    if scope.decision == Q:
        return TechnicalEligibilityDecision(
            record.record_id,
            Q,
            Q,
            (),
            REQUIRED_TECHNICAL_COMPONENTS,
            "Physical screening scope is unresolved; technical eligibility is not admitted.",
        )
    if scope.decision == OUT_OF_SCOPE:
        return TechnicalEligibilityDecision(
            record.record_id,
            OUT_OF_SCOPE,
            scope.evidence_status,
            (),
            (),
            "Record is explicitly outside the admitted physical screening scope; this is not a technical FAIL.",
        )

    failed = tuple(
        component_id
        for component_id in REQUIRED_TECHNICAL_COMPONENTS
        if by_component[component_id].decision == "FAIL"
    )
    if failed:
        status = _combined_real_status(
            (scope.evidence_status,) + tuple(by_component[item].evidence_status for item in failed)
        )
        return TechnicalEligibilityDecision(
            record.record_id,
            BLOCKED,
            status,
            failed,
            (),
            "At least one technical blocker is explicitly proven; unknown unrelated components do not erase the blocker.",
        )

    unresolved = tuple(
        component_id
        for component_id in REQUIRED_TECHNICAL_COMPONENTS
        if by_component[component_id].decision == Q
    )
    if unresolved:
        return TechnicalEligibilityDecision(
            record.record_id,
            Q,
            Q,
            (),
            unresolved,
            "No technical blocker is proven, but one or more required technical components are unresolved.",
        )

    status = _combined_real_status(
        (scope.evidence_status,) + tuple(by_component[item].evidence_status for item in REQUIRED_TECHNICAL_COMPONENTS)
    )
    if status == Q:
        raise B02EligibilityError("completed technical eligibility unexpectedly lacks OBS/DER evidence")
    return TechnicalEligibilityDecision(
        record.record_id,
        ELIGIBLE,
        status,
        (),
        (),
        "All required technical components pass with explicit OBS/DER evidence.",
    )


def assess_s2_transition_readiness(
    eligibility: TechnicalEligibilityDecision,
    predecessor: PredecessorGateEvidence,
) -> S2TransitionDecision:
    """Evaluate S1->S2 transition readiness separately from technical eligibility."""
    predecessor.validate()
    if eligibility.status == OUT_OF_SCOPE:
        return S2TransitionDecision(S2_BLOCKED, eligibility.evidence_status, "Record is outside programme physical scope.")
    if eligibility.status == BLOCKED:
        return S2TransitionDecision(S2_BLOCKED, eligibility.evidence_status, "Technical readiness contains an explicit blocker.")
    if eligibility.status != ELIGIBLE:
        return S2TransitionDecision(S2_Q, Q, "Technical eligibility remains unresolved.")
    if predecessor.decision == "FAIL":
        return S2TransitionDecision(S2_BLOCKED, predecessor.evidence_status, "S1 predecessor gate is explicitly not satisfied.")
    if predecessor.decision == Q:
        return S2TransitionDecision(S2_Q, Q, "S1 predecessor gate remains unresolved.")
    evidence_status = _combined_real_status((eligibility.evidence_status, predecessor.evidence_status))
    return S2TransitionDecision(
        S2_READY,
        evidence_status,
        "Technical eligibility and the S1 predecessor gate are both explicitly satisfied.",
    )


def _load_b01_physical_reference() -> tuple[int, str]:
    with B01_ROLLOUT_PATH.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    if len(rows) != 1:
        raise B02EligibilityError("B01 rollout policy registry must contain exactly one canonical row")
    row = rows[0]
    value = row.get("exact_non_district_heated_occupied_dwellings_2022", "").strip()
    status = row.get("exact_population_status", "").strip()
    if not value.isdigit() or int(value) <= 0:
        raise B02EligibilityError("B01 exact physical population reference is missing or invalid")
    if status != "DER_FROM_OBS_WBL011_CELLS":
        raise B02EligibilityError("B01 exact physical population reference status drifted")
    return int(value), status


def assess_current_repository_gate() -> CurrentRepositoryEligibilityGate:
    """Expose the current repository state without inventing a national eligible count."""
    with GAP_MATRIX_PATH.open(encoding="utf-8", newline="") as handle:
        rows = {row["gap_id"]: row for row in csv.DictReader(handle)}
    missing_ids = tuple(gap_id for gap_id in CURRENT_REQUIRED_GAP_IDS if gap_id not in rows)
    if missing_ids:
        raise B02EligibilityError(f"required B02 gap-matrix rows are missing: {missing_ids}")

    blocking = tuple(
        gap_id
        for gap_id in CURRENT_REQUIRED_GAP_IDS
        if rows[gap_id]["allow_for_gate"].strip().lower() != "yes"
        or rows[gap_id]["evidence_status"].strip() not in REAL_EVIDENCE_STATUSES
    )
    population, population_status = _load_b01_physical_reference()
    return CurrentRepositoryEligibilityGate(
        status=Q if blocking else "GATE_EVIDENCE_AVAILABLE",
        eligible_dwellings=None,
        physical_screening_reference_households=population,
        physical_screening_reference_status=population_status,
        blocking_gap_ids=blocking,
        source_refs=(
            "registry/b02_s0_s2_evidence_gap_matrix.csv",
            "registry/b01_national_rollout_policy_contract.csv",
            "Q-B02-001",
            "Q-B02-004",
        ),
    )
