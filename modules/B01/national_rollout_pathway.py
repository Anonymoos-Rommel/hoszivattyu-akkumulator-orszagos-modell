"""B01-P2 national programme rollout policy-pathway contract.

This module makes the policy/scenario rollout envelope executable without
promoting policy targets or scenario paths to observed eligible-stock or real
household-selection claims.

Core boundary:

POLICY TARGET != TECHNICALLY ELIGIBLE STOCK != REAL ANNUAL CAPACITY !=
REAL SELECTED HOUSEHOLDS.

The P1-A policy envelope is canonical here: 2,000,000 baseline households,
0..2,500,000 sensitivity range, 8..25 year horizon, report points at 12/15/20
years, and explicit LINEAR / LOGISTIC / CAPACITY_LIMITED profiles.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import exp, isfinite
from typing import Iterable


POLICY_TARGET_BASELINE_HOUSEHOLDS = 2_000_000
POLICY_TARGET_MIN_HOUSEHOLDS = 0
POLICY_TARGET_MAX_HOUSEHOLDS = 2_500_000
HORIZON_MIN_YEARS = 8
HORIZON_MAX_YEARS = 25
REPORT_POINTS_YEARS = (12, 15, 20)

LINEAR = "LINEAR"
LOGISTIC = "LOGISTIC"
CAPACITY_LIMITED = "CAPACITY_LIMITED"
SUPPORTED_PROFILES = (LINEAR, LOGISTIC, CAPACITY_LIMITED)

POLICY_STATUSES = {"POL", "SCN"}
REAL_GATE_STATUSES = {"OBS", "DER"}

NATIONAL_SELECTION_READY = "NATIONAL_SELECTION_READY"
Q_UPSTREAM_EVIDENCE = "Q_UPSTREAM_EVIDENCE"


class B01RolloutError(ValueError):
    """Raised when rollout inputs would create hidden assumptions."""


def _nonempty(value: str, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise B01RolloutError(f"{field} must be non-empty")
    return value.strip()


def _int(value: int, field: str, *, minimum: int | None = None, maximum: int | None = None) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise B01RolloutError(f"{field} must be an integer")
    if minimum is not None and value < minimum:
        raise B01RolloutError(f"{field} must be >= {minimum}")
    if maximum is not None and value > maximum:
        raise B01RolloutError(f"{field} must be <= {maximum}")
    return value


def _finite(value: float, field: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not isfinite(float(value)):
        raise B01RolloutError(f"{field} must be finite")
    return float(value)


@dataclass(frozen=True)
class RolloutScenario:
    scenario_id: str
    start_year: int
    horizon_years: int
    policy_target_households: int
    profile: str
    target_status: str
    source_refs: tuple[str, ...]
    logistic_midpoint_fraction: float | None = None
    logistic_steepness: float | None = None
    annual_capacity_households: tuple[int, ...] = ()

    def validate(self) -> None:
        _nonempty(self.scenario_id, "scenario_id")
        _int(self.start_year, "start_year", minimum=1900, maximum=2200)
        _int(self.horizon_years, "horizon_years", minimum=HORIZON_MIN_YEARS, maximum=HORIZON_MAX_YEARS)
        _int(
            self.policy_target_households,
            "policy_target_households",
            minimum=POLICY_TARGET_MIN_HOUSEHOLDS,
            maximum=POLICY_TARGET_MAX_HOUSEHOLDS,
        )
        if self.profile not in SUPPORTED_PROFILES:
            raise B01RolloutError(f"unsupported profile: {self.profile!r}")
        if self.target_status not in POLICY_STATUSES:
            raise B01RolloutError("policy target must remain POL or SCN")
        if not self.source_refs or any(not isinstance(ref, str) or not ref.strip() for ref in self.source_refs):
            raise B01RolloutError("source_refs must contain non-empty provenance references")

        if self.profile == LOGISTIC:
            if self.logistic_midpoint_fraction is None or self.logistic_steepness is None:
                raise B01RolloutError("LOGISTIC requires explicit midpoint and steepness; hidden defaults are prohibited")
            midpoint = _finite(self.logistic_midpoint_fraction, "logistic_midpoint_fraction")
            steepness = _finite(self.logistic_steepness, "logistic_steepness")
            if not 0.0 < midpoint < 1.0:
                raise B01RolloutError("logistic_midpoint_fraction must lie in (0,1)")
            if steepness <= 0.0:
                raise B01RolloutError("logistic_steepness must be > 0")
            if self.annual_capacity_households:
                raise B01RolloutError("LOGISTIC cannot silently consume annual capacity values")
        elif self.profile == CAPACITY_LIMITED:
            if self.logistic_midpoint_fraction is not None or self.logistic_steepness is not None:
                raise B01RolloutError("CAPACITY_LIMITED cannot carry logistic parameters")
            if len(self.annual_capacity_households) != self.horizon_years:
                raise B01RolloutError("CAPACITY_LIMITED requires one explicit capacity value for every plan year")
            for index, value in enumerate(self.annual_capacity_households, start=1):
                _int(value, f"annual_capacity_households[{index}]", minimum=0)
        else:
            if self.logistic_midpoint_fraction is not None or self.logistic_steepness is not None:
                raise B01RolloutError("LINEAR cannot carry logistic parameters")
            if self.annual_capacity_households:
                raise B01RolloutError("LINEAR cannot silently consume annual capacity values")


@dataclass(frozen=True)
class RolloutYear:
    scenario_id: str
    plan_year_index: int
    calendar_year: int
    profile: str
    new_households: int
    cumulative_households: int
    unmet_policy_target: int
    evidence_status: str
    source_refs: tuple[str, ...]


@dataclass(frozen=True)
class NationalSelectionGate:
    technically_eligible_stock: int | None
    technically_eligible_status: str
    real_annual_capacity_status: str
    target_definition_status: str
    source_refs: tuple[str, ...]

    def validate(self) -> None:
        if self.technically_eligible_status not in {"OBS", "DER", "Q"}:
            raise B01RolloutError("technically_eligible_status must be OBS, DER or Q")
        if self.real_annual_capacity_status not in {"OBS", "DER", "Q"}:
            raise B01RolloutError("real_annual_capacity_status must be OBS, DER or Q")
        if self.target_definition_status not in {"OBS", "DER", "POL", "Q"}:
            raise B01RolloutError("target_definition_status must be OBS, DER, POL or Q")
        if self.technically_eligible_stock is not None:
            _int(self.technically_eligible_stock, "technically_eligible_stock", minimum=0)
        if not self.source_refs or any(not isinstance(ref, str) or not ref.strip() for ref in self.source_refs):
            raise B01RolloutError("selection-gate source_refs must be non-empty")


def assess_national_selection_gate(gate: NationalSelectionGate) -> str:
    """Return ready only when real/derived upstream stock, capacity and target definition exist."""
    gate.validate()
    if gate.technically_eligible_stock is None:
        return Q_UPSTREAM_EVIDENCE
    if gate.technically_eligible_status not in REAL_GATE_STATUSES:
        return Q_UPSTREAM_EVIDENCE
    if gate.real_annual_capacity_status not in REAL_GATE_STATUSES:
        return Q_UPSTREAM_EVIDENCE
    if gate.target_definition_status not in {"OBS", "DER"}:
        return Q_UPSTREAM_EVIDENCE
    return NATIONAL_SELECTION_READY


def _linear_cumulative(target: int, step: int, horizon: int) -> int:
    # Integer floor allocation is deterministic and closes exactly on target at step=horizon.
    return target * step // horizon


def _logistic_cumulative(target: int, step: int, horizon: int, midpoint: float, steepness: float) -> int:
    def logistic(x: float) -> float:
        return 1.0 / (1.0 + exp(-steepness * (x - midpoint)))

    lo = logistic(0.0)
    hi = logistic(1.0)
    if hi <= lo:
        raise B01RolloutError("logistic normalization is degenerate")
    fraction = (logistic(step / horizon) - lo) / (hi - lo)
    if step == horizon:
        return target
    return min(target, max(0, int(round(target * fraction))))


def build_rollout_pathway(scenario: RolloutScenario) -> tuple[RolloutYear, ...]:
    """Build one explicit national policy/scenario path.

    Output is always SCN because this function is an envelope generator. It does
    not select real households, prove B02 eligibility, or create observed annual
    installation capacity.
    """
    scenario.validate()
    target = scenario.policy_target_households
    previous = 0
    rows: list[RolloutYear] = []

    for step in range(1, scenario.horizon_years + 1):
        if scenario.profile == LINEAR:
            cumulative = _linear_cumulative(target, step, scenario.horizon_years)
        elif scenario.profile == LOGISTIC:
            cumulative = _logistic_cumulative(
                target,
                step,
                scenario.horizon_years,
                float(scenario.logistic_midpoint_fraction),
                float(scenario.logistic_steepness),
            )
            cumulative = max(previous, cumulative)
        else:
            capacity = scenario.annual_capacity_households[step - 1]
            cumulative = min(target, previous + capacity)

        new_households = cumulative - previous
        if new_households < 0:
            raise B01RolloutError("rollout path must be monotone")
        rows.append(
            RolloutYear(
                scenario_id=scenario.scenario_id,
                plan_year_index=step,
                calendar_year=scenario.start_year + step - 1,
                profile=scenario.profile,
                new_households=new_households,
                cumulative_households=cumulative,
                unmet_policy_target=target - cumulative,
                evidence_status="SCN",
                source_refs=scenario.source_refs,
            )
        )
        previous = cumulative

    return tuple(rows)


def report_points(pathway: Iterable[RolloutYear]) -> tuple[RolloutYear, ...]:
    """Return canonical 12/15/20-year report points that exist in the path."""
    rows = tuple(pathway)
    return tuple(row for row in rows if row.plan_year_index in REPORT_POINTS_YEARS)
