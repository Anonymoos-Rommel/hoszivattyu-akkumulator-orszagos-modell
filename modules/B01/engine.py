"""Fail-closed household state-stock and portfolio-selection contract for B01.

The executable rules are loaded from ``registry/household_state_model.json``;
this module does not create a second state machine or a default national
objective.  Scenario fixtures can be ordered and capacity-limited, but their
outputs remain SCN and never promote a household's observed state.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import date
from math import isfinite
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence


ROOT = Path(__file__).resolve().parents[2]
MODEL_PATH = ROOT / "registry" / "household_state_model.json"
MODEL = json.loads(MODEL_PATH.read_text(encoding="utf-8"))

EVIDENCE_STATUSES = frozenset(MODEL["household_record_schema"]["evidence_statuses"])
USABLE_NUMERIC_STATUSES = frozenset(MODEL["portfolio_contract"]["usable_numeric_statuses"])
POLICY_PARAMETER_STATUSES = frozenset(MODEL["portfolio_contract"]["policy_parameter_statuses"])
STATE_ORDER = tuple(state["state_id"] for state in MODEL["states"])
STATE_INDEX = {state_id: index for index, state_id in enumerate(STATE_ORDER)}
TRANSITIONS = {row["transition_id"]: row for row in MODEL["transition_contract"]}
PORTFOLIO_COMPONENTS = tuple(MODEL["portfolio_contract"]["components"])
CAPACITY_CONSTRAINTS = tuple(MODEL["capacity_constraint_contract"]["constraints"])


class B01ContractError(ValueError):
    """Raised when an input would weaken a B01 evidence or policy gate."""


def _nonempty(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise B01ContractError(f"{field} must be non-empty")
    return value.strip()


def _iso_date(value: str, field: str) -> None:
    try:
        date.fromisoformat(_nonempty(value, field))
    except ValueError as exc:
        raise B01ContractError(f"{field} must be ISO date") from exc


def _transition_for(from_state: str, target_state: str) -> dict[str, Any]:
    for transition in TRANSITIONS.values():
        if transition["from_state"] == from_state and transition["to_state"] == target_state:
            return transition
    raise B01ContractError(f"only adjacent canonical states are allowed: {from_state!r}->{target_state!r}")


def _numeric(value: Any, field: str, *, minimum: float | None = None) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not isfinite(float(value)):
        raise B01ContractError(f"{field} must be a finite number")
    numeric = float(value)
    if minimum is not None and numeric < minimum:
        raise B01ContractError(f"{field} must be >= {minimum}")
    return numeric


@dataclass(frozen=True)
class TransitionEvidence:
    transition_id: str
    status: str
    evidence_refs: tuple[str, ...]
    completed: bool
    as_of: str
    owner: str
    skipped: bool = False
    skip_reason: str = ""
    truth_context: str = "REAL"

    def validate(self) -> None:
        transition = TRANSITIONS.get(self.transition_id)
        if transition is None:
            raise B01ContractError(f"unknown transition: {self.transition_id!r}")
        if self.status not in EVIDENCE_STATUSES:
            raise B01ContractError(f"invalid transition evidence status: {self.status!r}")
        if self.truth_context not in set(MODEL["household_record_schema"]["truth_contexts"]):
            raise B01ContractError(f"invalid transition truth_context: {self.truth_context!r}")
        if self.truth_context == "SCN" and self.status != "SCN":
            raise B01ContractError("SCN transition context cannot carry OBS/DER/ASS/Q labels")
        if self.truth_context == "REAL" and self.status == "SCN":
            raise B01ContractError("REAL transition context cannot carry SCN evidence")
        _iso_date(self.as_of, f"{self.transition_id}.as_of")
        _nonempty(self.owner, f"{self.transition_id}.owner")
        if any(not isinstance(ref, str) or not ref.strip() for ref in self.evidence_refs):
            raise B01ContractError(f"{self.transition_id} has an empty evidence reference")
        if self.completed and self.truth_context == "REAL":
            if self.status not in set(transition["allowed_completion_status"]):
                raise B01ContractError(
                    f"{self.transition_id} cannot complete with {self.status} evidence"
                )
            if not self.evidence_refs:
                raise B01ContractError(f"{self.transition_id} completion requires evidence_refs")
        if self.completed and self.truth_context == "SCN" and not self.evidence_refs:
            raise B01ContractError(f"{self.transition_id} SCN projection requires evidence_refs")
        if self.skipped and (not self.completed or not self.skip_reason.strip()):
            raise B01ContractError(f"skipped {self.transition_id} requires explicit satisfied gate and reason")


@dataclass(frozen=True)
class HouseholdStateRecord:
    household_id: str
    archetype_id: str
    region_id: str
    current_state: str
    evidence_refs: tuple[str, ...]
    state_as_of: str
    owner: str
    next_gate: str
    blocked_reason: str
    eligibility_status: str
    eligibility_evidence_status: str
    transition_evidence: tuple[TransitionEvidence, ...] = ()
    truth_context: str = "REAL"

    def validate(self) -> None:
        for field, value in (
            ("household_id", self.household_id),
            ("archetype_id", self.archetype_id),
            ("region_id", self.region_id),
            ("next_gate", self.next_gate),
        ):
            _nonempty(value, field)
        if not isinstance(self.blocked_reason, str):
            raise B01ContractError("blocked_reason must be a string")
        if self.current_state not in STATE_INDEX:
            raise B01ContractError(f"unknown current_state: {self.current_state!r}")
        if self.truth_context not in set(MODEL["household_record_schema"]["truth_contexts"]):
            raise B01ContractError(f"invalid truth_context: {self.truth_context!r}")
        _iso_date(self.state_as_of, "state_as_of")
        _nonempty(self.owner, "owner")
        if self.eligibility_status not in set(MODEL["household_record_schema"]["eligibility_statuses"]):
            raise B01ContractError(f"invalid eligibility_status: {self.eligibility_status!r}")
        if self.eligibility_evidence_status not in EVIDENCE_STATUSES:
            raise B01ContractError(f"invalid eligibility_evidence_status: {self.eligibility_evidence_status!r}")
        if self.truth_context == "SCN" and self.eligibility_evidence_status not in {"SCN", "Q"}:
            raise B01ContractError("SCN household context requires SCN or Q eligibility evidence")
        if self.truth_context == "REAL" and self.eligibility_evidence_status == "SCN":
            raise B01ContractError("REAL household context cannot carry SCN eligibility evidence")
        if any(not isinstance(ref, str) or not ref.strip() for ref in self.evidence_refs):
            raise B01ContractError("evidence_refs cannot contain empty values")
        seen: set[str] = set()
        for evidence in self.transition_evidence:
            if evidence.truth_context != self.truth_context:
                raise B01ContractError(
                    f"transition truth_context mismatch: household={self.truth_context!r} "
                    f"transition={evidence.truth_context!r}"
                )
            evidence.validate()
            if evidence.transition_id in seen:
                raise B01ContractError(f"duplicate transition evidence: {evidence.transition_id!r}")
            seen.add(evidence.transition_id)


def determine_current_state(record: HouseholdStateRecord) -> str:
    """Derive the highest contiguous state from explicit completed gates."""
    record.validate()
    by_transition = {item.transition_id: item for item in record.transition_evidence}
    computed = STATE_ORDER[0]
    for transition in TRANSITIONS.values():
        evidence = by_transition.get(transition["transition_id"])
        if evidence is None or not evidence.completed:
            later_completed = [
                item.transition_id
                for item in record.transition_evidence
                if item.completed and STATE_INDEX[TRANSITIONS[item.transition_id]["to_state"]] > STATE_INDEX[transition["to_state"]]
            ]
            if later_completed:
                raise B01ContractError(
                    f"state cannot skip incomplete predecessor gate: {transition['transition_id']!r}"
                )
            break
        computed = transition["to_state"]
    if computed != record.current_state:
        raise B01ContractError(
            f"current_state disagrees with completed evidence: declared={record.current_state!r} computed={computed!r}"
        )
    return computed


@dataclass(frozen=True)
class TransitionDecision:
    transition_id: str
    status: str
    from_state: str
    to_state: str
    required_gate: str
    evidence_status: str
    reason: str


def evaluate_next_transition(record: HouseholdStateRecord) -> TransitionDecision:
    current = determine_current_state(record)
    if current == STATE_ORDER[-1]:
        completion_status = "OBS" if record.truth_context == "REAL" else "SCN"
        return TransitionDecision("NONE", "COMPLETE", current, current, "NONE", completion_status, "S5 is already reached.")
    transition = _transition_for(current, STATE_ORDER[STATE_INDEX[current] + 1])
    required_gate = transition["target_completion_gate"]
    evidence = next(
        (item for item in record.transition_evidence if item.transition_id == transition["transition_id"]),
        None,
    )
    if evidence is None or not evidence.completed:
        return TransitionDecision(
            transition["transition_id"], "BLOCKED", current, transition["to_state"], required_gate,
            "Q", transition["fail_closed_reason"],
        )
    if record.eligibility_status != "ELIGIBLE":
        return TransitionDecision(
            transition["transition_id"], "BLOCKED", current, transition["to_state"], required_gate,
            "Q", "Eligibility is not explicitly ELIGIBLE; missing evidence remains Q.",
        )
    allowed_eligibility_statuses = {"OBS", "DER"} if record.truth_context == "REAL" else {"SCN"}
    if record.eligibility_evidence_status not in allowed_eligibility_statuses:
        return TransitionDecision(
            transition["transition_id"], "BLOCKED", current, transition["to_state"], required_gate,
            record.eligibility_evidence_status, "Eligibility evidence is not OBS/DER.",
        )
    return TransitionDecision(
        transition["transition_id"], "ELIGIBLE", current, transition["to_state"], required_gate,
        record.eligibility_evidence_status, "Current state and eligibility gate are explicit.",
    )


@dataclass(frozen=True)
class CandidateIntervention:
    household_id: str
    region_id: str
    intervention_id: str
    from_state: str
    target_state: str
    required_gate: str
    required_gate_status: str
    required_gate_evidence_refs: tuple[str, ...]
    scores: Mapping[str, float | None]
    score_statuses: Mapping[str, str]
    resource_needs: Mapping[str, float | None]
    evidence_status: str
    missing_next_gate: str
    why_now: str
    why_here: str
    binding_constraint: str = "UNASSIGNED"
    truth_context: str = "REAL"

    def validate(self) -> None:
        for field, value in (
            ("household_id", self.household_id),
            ("region_id", self.region_id),
            ("intervention_id", self.intervention_id),
            ("required_gate", self.required_gate),
            ("missing_next_gate", self.missing_next_gate),
            ("why_now", self.why_now),
            ("why_here", self.why_here),
            ("binding_constraint", self.binding_constraint),
        ):
            _nonempty(value, field)
        transition = _transition_for(self.from_state, self.target_state)
        canonical_gate = transition["target_completion_gate"]
        if self.required_gate != canonical_gate:
            raise B01ContractError(
                f"candidate required_gate mismatch for {transition['transition_id']}: "
                f"expected={canonical_gate!r} actual={self.required_gate!r}"
            )
        if self.truth_context not in set(MODEL["household_record_schema"]["truth_contexts"]):
            raise B01ContractError(f"invalid candidate truth_context: {self.truth_context!r}")
        if self.required_gate_status not in EVIDENCE_STATUSES:
            raise B01ContractError(f"invalid required_gate_status: {self.required_gate_status!r}")
        allowed_gate_statuses = {"OBS", "DER", "Q"} if self.truth_context == "REAL" else {"SCN", "Q"}
        if self.required_gate_status not in allowed_gate_statuses:
            raise B01ContractError(
                f"{self.truth_context} candidate gate requires {sorted(allowed_gate_statuses)!r} evidence"
            )
        if any(not ref.strip() for ref in self.required_gate_evidence_refs):
            raise B01ContractError("required_gate_evidence_refs cannot contain empty values")
        if self.required_gate_status == "Q" and self.required_gate_evidence_refs:
            raise B01ContractError("Q candidate gate cannot carry evidence_refs")
        if self.required_gate_status in {"OBS", "DER", "SCN"} and not self.required_gate_evidence_refs:
            raise B01ContractError("evidenced candidate gate requires evidence_refs")
        if self.evidence_status not in EVIDENCE_STATUSES:
            raise B01ContractError(f"invalid candidate evidence_status: {self.evidence_status!r}")
        if set(self.scores) != set(PORTFOLIO_COMPONENTS) or set(self.score_statuses) != set(PORTFOLIO_COMPONENTS):
            raise B01ContractError("candidate must expose every canonical portfolio component and status")
        for component in PORTFOLIO_COMPONENTS:
            status = self.score_statuses[component]
            value = self.scores[component]
            if status not in EVIDENCE_STATUSES:
                raise B01ContractError(f"invalid component status for {component}: {status!r}")
            if value is not None:
                _numeric(value, f"{component}.value", minimum=0.0)
                if float(value) > 1:
                    raise B01ContractError(f"{component}.value must be <= 1")
            if status in USABLE_NUMERIC_STATUSES and value is None:
                raise B01ContractError(f"{component} has {status} status but no numeric value")
        for constraint in CAPACITY_CONSTRAINTS:
            if constraint not in self.resource_needs:
                raise B01ContractError(f"candidate resource_needs missing {constraint}")
            value = self.resource_needs[constraint]
            if value is not None:
                _numeric(value, f"resource_needs.{constraint}", minimum=0.0)

    @property
    def score_complete(self) -> bool:
        return all(
            self.score_statuses[component] in USABLE_NUMERIC_STATUSES and self.scores[component] is not None
            for component in PORTFOLIO_COMPONENTS
        )


@dataclass(frozen=True)
class CandidateDecision:
    candidate: CandidateIntervention
    status: str
    reason: str
    next_missing_gate: str

    @property
    def evidence_status(self) -> str:
        return "Q" if self.status == "BLOCKED" else self.candidate.required_gate_status


def assess_candidate(record: HouseholdStateRecord, candidate: CandidateIntervention) -> CandidateDecision:
    candidate.validate()
    current = determine_current_state(record)
    if candidate.truth_context != record.truth_context:
        return CandidateDecision(candidate, "BLOCKED", "Candidate and household truth contexts differ.", candidate.missing_next_gate)
    if candidate.household_id != record.household_id or candidate.from_state != current:
        return CandidateDecision(candidate, "BLOCKED", "Candidate predecessor state does not match household state.", candidate.missing_next_gate)
    next_transition = evaluate_next_transition(record)
    expected = _transition_for(candidate.from_state, candidate.target_state)
    if next_transition.transition_id != expected["transition_id"]:
        return CandidateDecision(candidate, "BLOCKED", "Candidate is not the next monotone transition.", candidate.missing_next_gate)
    allowed_eligibility_statuses = {"OBS", "DER"} if record.truth_context == "REAL" else {"SCN"}
    if record.eligibility_status != "ELIGIBLE" or record.eligibility_evidence_status not in allowed_eligibility_statuses:
        return CandidateDecision(candidate, "BLOCKED", "Eligibility is not explicitly evidenced; physical inputs cannot create policy eligibility.", candidate.missing_next_gate)
    if candidate.required_gate_status == "Q":
        return CandidateDecision(candidate, "BLOCKED", "Required gate evidence is Q/unknown; candidate remains blocked.", candidate.required_gate)
    if candidate.required_gate_status not in allowed_eligibility_statuses or not candidate.required_gate_evidence_refs:
        return CandidateDecision(candidate, "BLOCKED", "Required gate evidence is missing or not usable.", candidate.required_gate)
    if not candidate.score_complete:
        return CandidateDecision(candidate, "BLOCKED", "A portfolio component is missing or not numerically evidenced.", candidate.missing_next_gate)
    return CandidateDecision(candidate, "ELIGIBLE", "Candidate gate and predecessor state are explicit.", candidate.missing_next_gate)


@dataclass(frozen=True)
class PolicyParameter:
    component: str
    weight: float | None
    weight_status: str
    hard_minimum: float | None
    hard_minimum_status: str
    direction: str
    missing_value_policy: str
    source_ref: str


def validate_policy(parameters: Mapping[str, PolicyParameter]) -> None:
    if set(parameters) != set(PORTFOLIO_COMPONENTS):
        missing = sorted(set(PORTFOLIO_COMPONENTS) - set(parameters))
        extra = sorted(set(parameters) - set(PORTFOLIO_COMPONENTS))
        raise B01ContractError(f"policy component mismatch: missing={missing!r} extra={extra!r}")
    for component in PORTFOLIO_COMPONENTS:
        parameter = parameters[component]
        if parameter.component != component:
            raise B01ContractError(f"policy component key mismatch: {component!r}")
        if parameter.weight_status not in POLICY_PARAMETER_STATUSES or parameter.weight is None:
            raise B01ContractError(f"missing explicit policy weight for {component}")
        _numeric(parameter.weight, f"{component}.weight")
        if parameter.hard_minimum_status not in POLICY_PARAMETER_STATUSES or parameter.hard_minimum is None:
            raise B01ContractError(f"missing explicit hard minimum for {component}")
        _numeric(parameter.hard_minimum, f"{component}.hard_minimum", minimum=0.0)
        if parameter.direction not in {"MAXIMIZE", "MINIMIZE"}:
            raise B01ContractError(f"invalid direction for {component}: {parameter.direction!r}")
        if parameter.missing_value_policy != "FAIL_CLOSED":
            raise B01ContractError(f"missing-value policy must be FAIL_CLOSED for {component}")
        _nonempty(parameter.source_ref, f"{component}.source_ref")


def _oriented(value: float, direction: str) -> float:
    return value if direction == "MAXIMIZE" else -value


def _meets_policy_hard_minimums(candidate: CandidateIntervention, parameters: Mapping[str, PolicyParameter]) -> bool:
    return all(
        float(candidate.scores[component]) >= float(parameters[component].hard_minimum)
        for component in PORTFOLIO_COMPONENTS
    )


def mcda_order(candidates: Sequence[CandidateIntervention], parameters: Mapping[str, PolicyParameter]) -> tuple[CandidateIntervention, ...]:
    """Return deterministic MCDA order; missing weights or values raise, never become zero."""
    validate_policy(parameters)
    scored: list[tuple[float, str, str, CandidateIntervention]] = []
    for candidate in candidates:
        candidate.validate()
        if not candidate.score_complete:
            raise B01ContractError(f"MCDA cannot score incomplete candidate: {candidate.intervention_id}")
        if not _meets_policy_hard_minimums(candidate, parameters):
            continue
        score = sum(
            float(parameters[component].weight) * _oriented(float(candidate.scores[component]), parameters[component].direction)
            for component in PORTFOLIO_COMPONENTS
        )
        scored.append((score, candidate.household_id, candidate.intervention_id, candidate))
    return tuple(item[3] for item in sorted(scored, key=lambda item: (-item[0], item[1], item[2])))


def stress_test_orders(
    candidates: Sequence[CandidateIntervention],
    parameter_sets: Sequence[Mapping[str, PolicyParameter]],
) -> tuple[tuple[str, ...], ...]:
    """Compare explicit alternative weight/minimum scenarios; no implicit baseline is supplied."""
    if not parameter_sets:
        raise B01ContractError("stress test requires at least one explicit policy/scenario parameter set")
    return tuple(
        tuple(candidate.intervention_id for candidate in mcda_order(candidates, parameters))
        for parameters in parameter_sets
    )


def lexicographic_order(candidates: Sequence[CandidateIntervention], parameters: Mapping[str, PolicyParameter], order: Sequence[str]) -> tuple[CandidateIntervention, ...]:
    validate_policy(parameters)
    if tuple(order) != tuple(PORTFOLIO_COMPONENTS) and set(order) != set(PORTFOLIO_COMPONENTS):
        raise B01ContractError("lexicographic order must explicitly cover every canonical component")
    eligible: list[CandidateIntervention] = []
    for candidate in candidates:
        candidate.validate()
        if not candidate.score_complete:
            raise B01ContractError(f"lexicographic method cannot score incomplete candidate: {candidate.intervention_id}")
        if _meets_policy_hard_minimums(candidate, parameters):
            eligible.append(candidate)
    return tuple(sorted(
        eligible,
        key=lambda candidate: tuple(
            -_oriented(float(candidate.scores[component]), parameters[component].direction) for component in order
        ) + (candidate.household_id, candidate.intervention_id),
    ))


@dataclass(frozen=True)
class CapacityConstraint:
    name: str
    available: float | None
    status: str
    unit: str
    constraint_type: str = "MAX_RESOURCE"
    region_id: str = ""

    def validate(self) -> None:
        if self.name not in CAPACITY_CONSTRAINTS:
            raise B01ContractError(f"unknown capacity constraint: {self.name!r}")
        if self.status not in USABLE_NUMERIC_STATUSES or self.available is None:
            raise B01ContractError(f"capacity {self.name} is Q/unavailable; infinite capacity is prohibited")
        _numeric(self.available, f"capacity.{self.name}", minimum=0.0)
        _nonempty(self.unit, f"capacity.{self.name}.unit")
        if self.constraint_type not in {"MAX_RESOURCE", "MIN_TOTAL", "MIN_REGION"}:
            raise B01ContractError(f"invalid capacity constraint type: {self.constraint_type!r}")
        if self.constraint_type == "MIN_REGION":
            _nonempty(self.region_id, f"capacity.{self.name}.region_id")


@dataclass(frozen=True)
class PortfolioSelection:
    selected: tuple[CandidateIntervention, ...]
    waiting: tuple[CandidateIntervention, ...]
    binding_constraints: tuple[str, ...]


def select_with_capacity(ordered: Sequence[CandidateIntervention], constraints: Sequence[CapacityConstraint]) -> PortfolioSelection:
    if not constraints:
        raise B01ContractError("explicit annual capacity constraints are required")
    for constraint in constraints:
        constraint.validate()
    if not set(CAPACITY_CONSTRAINTS).issubset({constraint.name for constraint in constraints}):
        raise B01ContractError("every canonical annual capacity constraint must be explicit")
    maxima = sorted(
        (constraint for constraint in constraints if constraint.constraint_type == "MAX_RESOURCE"),
        key=lambda constraint: (CAPACITY_CONSTRAINTS.index(constraint.name), constraint.region_id),
    )
    selected: list[CandidateIntervention] = []
    waiting: list[CandidateIntervention] = []
    totals = {constraint.name: 0.0 for constraint in maxima}
    blocked_by_capacity: set[str] = set()
    for candidate in ordered:
        candidate.validate()
        if not candidate.score_complete:
            raise B01ContractError(f"cannot capacity-select incomplete candidate: {candidate.intervention_id}")
        fits = all(
            candidate.resource_needs[constraint.name] is not None
            and totals[constraint.name] + float(candidate.resource_needs[constraint.name]) <= float(constraint.available) + 1e-9
            for constraint in maxima
        )
        if fits:
            selected.append(candidate)
            for constraint in maxima:
                totals[constraint.name] += float(candidate.resource_needs[constraint.name])
        else:
            waiting.append(candidate)
            blocked_by_capacity.update(
                constraint.name
                for constraint in maxima
                if candidate.resource_needs[constraint.name] is None
                or totals[constraint.name] + float(candidate.resource_needs[constraint.name]) > float(constraint.available) + 1e-9
            )
    for constraint in constraints:
        if constraint.constraint_type == "MIN_TOTAL":
            total = sum(float(candidate.resource_needs[constraint.name] or 0.0) for candidate in selected)
            if total + 1e-9 < float(constraint.available):
                raise B01ContractError(f"minimum capacity floor not met: {constraint.name}")
        elif constraint.constraint_type == "MIN_REGION":
            regional_count = sum(candidate.region_id == constraint.region_id for candidate in selected)
            if regional_count < int(constraint.available):
                raise B01ContractError(f"regional minimum not met: {constraint.region_id}")
    binding_names = {
        constraint.name
        for constraint in maxima
        if abs(totals[constraint.name] - float(constraint.available)) <= 1e-9
    } | blocked_by_capacity
    binding = tuple(
        constraint.name
        for constraint in maxima
        if constraint.name in binding_names
    )
    return PortfolioSelection(tuple(selected), tuple(waiting), binding)


@dataclass(frozen=True)
class EvidenceValue:
    value: int | float | None
    status: str
    source_ref: str

    def validate(self, name: str) -> None:
        if self.status not in EVIDENCE_STATUSES:
            raise B01ContractError(f"invalid evidence status for {name}: {self.status!r}")
        _nonempty(self.source_ref, f"{name}.source_ref")
        if self.value is not None:
            _numeric(self.value, name, minimum=0.0)
        if self.status in {"OBS", "DER", "SCN", "POL"} and self.value is None:
            raise B01ContractError(f"{name} has {self.status} status but no value")


def bounded_feasible_stock(policy_target: EvidenceValue, technically_eligible_stock: EvidenceValue, selected_count: EvidenceValue) -> EvidenceValue:
    """Apply min(policy target, eligible stock, annual selected) only with explicit values."""
    for name, value in (("policy_target", policy_target), ("technically_eligible_stock", technically_eligible_stock), ("selected_count", selected_count)):
        value.validate(name)
    if any(value.value is None or value.status not in USABLE_NUMERIC_STATUSES for value in (policy_target, technically_eligible_stock, selected_count)):
        return EvidenceValue(None, "Q", "B01_BOUNDARY_Q")
    return EvidenceValue(
        min(int(policy_target.value), int(technically_eligible_stock.value), int(selected_count.value)),
        "SCN" if any(value.status == "SCN" for value in (policy_target, technically_eligible_stock, selected_count)) else "DER",
        "B01_EXPLICIT_BOUNDARIES",
    )


@dataclass(frozen=True)
class StateStockOutput:
    status: str
    plan_year: int
    state_counts: Mapping[str, int]
    regional_state_counts: Mapping[str, Mapping[str, int]]
    selected_transitions: tuple[str, ...]
    blocked_transitions: tuple[str, ...]
    unmet_policy_target: int | None
    feasible_stock: EvidenceValue
    binding_constraints: tuple[str, ...]
    waiting_candidates: tuple[str, ...]
    explanations: tuple[Mapping[str, Any], ...]

    @property
    def selected_count(self) -> int:
        return len(self.selected_transitions)


def aggregate_state_stock(
    records: Sequence[HouseholdStateRecord],
    selected: Sequence[CandidateIntervention],
    blocked: Sequence[CandidateDecision],
    policy_target: EvidenceValue,
    technically_eligible_stock: EvidenceValue,
    binding_constraints: Sequence[str],
    waiting: Sequence[CandidateIntervention],
    plan_year: int,
    status: str = "SCN",
) -> StateStockOutput:
    if status != "SCN":
        raise B01ContractError("state-stock fixture/output must remain SCN in this slice")
    state_counts = {state_id: 0 for state_id in STATE_ORDER}
    regional: dict[str, dict[str, int]] = {}
    by_household = {record.household_id: record for record in records}
    for record in records:
        current = determine_current_state(record)
        state_counts[current] += 1
        regional.setdefault(record.region_id, {state_id: 0 for state_id in STATE_ORDER})[current] += 1
    selected_households: set[str] = set()
    explanations: list[Mapping[str, Any]] = []
    for candidate in selected:
        candidate.validate()
        if candidate.household_id in selected_households:
            raise B01ContractError(f"household selected more than once: {candidate.household_id}")
        selected_households.add(candidate.household_id)
        record = by_household.get(candidate.household_id)
        if record is None:
            raise B01ContractError(f"selected household is not in state stock: {candidate.household_id}")
        if candidate.truth_context != record.truth_context:
            raise B01ContractError("selected candidate and household truth contexts differ")
        decision = assess_candidate(record, candidate)
        if decision.status != "ELIGIBLE":
            raise B01ContractError(
                f"selected candidate is not B01-eligible: {candidate.intervention_id} ({decision.evidence_status})"
            )
        current = determine_current_state(record)
        if current != candidate.from_state or STATE_INDEX[candidate.target_state] != STATE_INDEX[current] + 1:
            raise B01ContractError("selected transition is not monotone")
        state_counts[current] -= 1
        state_counts[candidate.target_state] += 1
        regional[record.region_id][current] -= 1
        regional[record.region_id][candidate.target_state] += 1
        explanations.append({
            "intervention_id": candidate.intervention_id,
            "why_now": candidate.why_now,
            "why_here": candidate.why_here,
            "binding_constraints": tuple(binding_constraints),
            "next_missing_gate": candidate.missing_next_gate,
        })
    if sum(state_counts.values()) != len(records):
        raise B01ContractError("state-stock conservation failed")
    for region_counts in regional.values():
        if sum(region_counts.values()) == 0:
            raise B01ContractError("regional state-stock conservation failed")
    for decision in blocked:
        explanations.append({
            "intervention_id": decision.candidate.intervention_id,
            "why_now": "blocked",
            "why_here": decision.candidate.why_here,
            "binding_constraints": (),
            "next_missing_gate": decision.next_missing_gate,
        })
    feasible = bounded_feasible_stock(
        policy_target,
        technically_eligible_stock,
        EvidenceValue(len(selected), status, "B01_SELECTED_SCN"),
    )
    unmet = None if feasible.value is None or policy_target.value is None else int(policy_target.value) - int(feasible.value)
    return StateStockOutput(
        status,
        int(_numeric(plan_year, "plan_year", minimum=0)),
        state_counts,
        regional,
        tuple(candidate.intervention_id for candidate in selected),
        tuple(decision.candidate.intervention_id for decision in blocked),
        unmet,
        feasible,
        tuple(binding_constraints),
        tuple(candidate.intervention_id for candidate in waiting),
        tuple(explanations),
    )


def _record_from_payload(payload: Mapping[str, Any]) -> HouseholdStateRecord:
    truth_context = payload.get("truth_context", "REAL")
    evidence = tuple(
        TransitionEvidence(
            transition_id=item["transition_id"],
            status=item["status"],
            evidence_refs=tuple(item.get("evidence_refs", [])),
            completed=bool(item.get("completed", False)),
            as_of=item["as_of"],
            owner=item["owner"],
            skipped=bool(item.get("skipped", False)),
            skip_reason=item.get("skip_reason", ""),
            truth_context=item.get("truth_context", truth_context),
        )
        for item in payload.get("transition_evidence", [])
    )
    return HouseholdStateRecord(
        household_id=payload["household_id"],
        archetype_id=payload["archetype_id"],
        region_id=payload["region_id"],
        current_state=payload["current_state"],
        evidence_refs=tuple(payload.get("evidence_refs", [])),
        state_as_of=payload["state_as_of"],
        owner=payload["owner"],
        next_gate=payload["next_gate"],
        blocked_reason=payload["blocked_reason"],
        eligibility_status=payload["eligibility_status"],
        eligibility_evidence_status=payload["eligibility_evidence_status"],
        transition_evidence=evidence,
        truth_context=truth_context,
    )


def _candidate_from_payload(payload: Mapping[str, Any]) -> CandidateIntervention:
    return CandidateIntervention(
        household_id=payload["household_id"],
        region_id=payload["region_id"],
        intervention_id=payload["intervention_id"],
        from_state=payload["from_state"],
        target_state=payload["target_state"],
        required_gate=payload["required_gate"],
        required_gate_status=payload["required_gate_status"],
        required_gate_evidence_refs=tuple(payload.get("required_gate_evidence_refs", [])),
        scores=payload["scores"],
        score_statuses=payload["score_statuses"],
        resource_needs=payload["resource_needs"],
        evidence_status=payload["evidence_status"],
        missing_next_gate=payload["missing_next_gate"],
        why_now=payload["why_now"],
        why_here=payload["why_here"],
        binding_constraint=payload.get("binding_constraint", "UNASSIGNED"),
        truth_context=payload.get("truth_context", "REAL"),
    )


def _policy_from_payload(payload: Mapping[str, Any]) -> dict[str, PolicyParameter]:
    return {
        component: PolicyParameter(component=component, **values)
        for component, values in payload.items()
    }


def _constraints_from_payload(payload: Sequence[Mapping[str, Any]]) -> tuple[CapacityConstraint, ...]:
    return tuple(CapacityConstraint(**item) for item in payload)


def run_fixture(path: str | Path) -> StateStockOutput:
    """Load and execute one bounded SCN fixture without producing a national result."""
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if payload.get("status") != "SCN" or payload.get("dataset_license") != "CC BY-SA 4.0":
        raise B01ContractError("B01 fixture must be explicit SCN with dataset-level license")
    if payload.get("truth_context", "SCN") != "SCN":
        raise B01ContractError("SCN fixture must use SCN truth_context")
    records = tuple(_record_from_payload(item) for item in payload["households"])
    candidates = tuple(_candidate_from_payload(item) for item in payload["candidates"])
    policy = _policy_from_payload(payload["policy"])
    constraints = _constraints_from_payload(payload["constraints"])
    decisions = tuple(assess_candidate(record, candidate) for record in records for candidate in candidates if record.household_id == candidate.household_id)
    eligible = tuple(decision.candidate for decision in decisions if decision.status == "ELIGIBLE")
    blocked = tuple(decision for decision in decisions if decision.status == "BLOCKED")
    ordered = mcda_order(eligible, policy)
    selection = select_with_capacity(ordered, constraints)
    return aggregate_state_stock(
        records,
        selection.selected,
        blocked,
        EvidenceValue(payload["policy_target"]["value"], payload["policy_target"]["status"], payload["policy_target"]["source_ref"]),
        EvidenceValue(payload["technically_eligible_stock"]["value"], payload["technically_eligible_stock"]["status"], payload["technically_eligible_stock"]["source_ref"]),
        selection.binding_constraints,
        selection.waiting,
        int(payload["plan_year"]),
        status="SCN",
    )
