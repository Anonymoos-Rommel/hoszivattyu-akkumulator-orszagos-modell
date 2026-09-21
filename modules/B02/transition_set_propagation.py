"""B02-P66 transition-action set propagation.

This module carries the B02-P65 set-identified emitter population forward
without inventing a point emitter mix or programme-average action split.

Canonical boundaries:

SET-IDENTIFIED COMPOSITION -> SET-IDENTIFIED ACTION ENVELOPE
CALIBRATED GAS-CONVECTOR MARGIN -> DISTRIBUTION TRANSITION LOWER BOUND
STRUCTURAL ACTION BOUNDS != NUMERIC DESIGN-TEMPERATURE/COP/CAPEX RESULT
NO PRICE AUTHORITY -> NO MONETARY CAPEX OUTPUT

The P39/P41 authority implies that the calibrated primary gas-convector share
cannot remain on a KEEP-existing-distribution path. At population level this
creates a hard lower bound on ADD + REPLACE distribution-transition actions.
It does not identify how that combined share splits between ADD and REPLACE.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import isclose

from modules.B02.emitter_marginal_reconciliation import (
    PRIMARY_HEATING_GAS_CONVECTOR_SHARE,
)
from modules.B02.emitter_set_identification import build_emitter_population_envelope


ACTIONS = ("KEEP", "UPSIZE", "CHANGE", "ADD", "REPLACE")
REAL_OR_MODEL_EVIDENCE = frozenset({"OBS", "DER", "ASS", "MODELLED", "SCN"})


@dataclass(frozen=True)
class ActionCandidate:
    keep_share: float
    upsize_share: float
    change_share: float
    add_share: float
    replace_share: float

    def as_dict(self) -> dict[str, float]:
        return {
            "KEEP": self.keep_share,
            "UPSIZE": self.upsize_share,
            "CHANGE": self.change_share,
            "ADD": self.add_share,
            "REPLACE": self.replace_share,
        }


@dataclass(frozen=True)
class ActionAssessment:
    admissible: bool
    blockers: tuple[str, ...]


@dataclass(frozen=True)
class ActionShareBounds:
    lower: float
    upper: float


@dataclass(frozen=True)
class TransitionActionEnvelope:
    occupied_dwellings: int
    add_or_replace_lower: float
    add_or_replace_upper: float
    non_keep_lower: float
    non_keep_upper: float
    action_bounds: dict[str, ActionShareBounds]
    evidence_status: str


@dataclass(frozen=True)
class OutcomeCoefficientBound:
    action: str
    metric: str
    lower: float | None
    upper: float | None
    evidence_status: str
    monetary: bool = False
    price_authority_status: str = "NOT_APPLICABLE"


@dataclass(frozen=True)
class MetricEnvelope:
    status: str
    metric: str
    lower: float | None
    upper: float | None
    blockers: tuple[str, ...]


def _unit_share(value: float, name: str) -> None:
    if not 0.0 <= float(value) <= 1.0:
        raise ValueError(f"{name} must be within [0,1]")


def assess_action_candidate(
    candidate: ActionCandidate,
    *,
    tolerance: float = 1e-12,
) -> ActionAssessment:
    shares = candidate.as_dict()
    for name, value in shares.items():
        _unit_share(value, name)

    blockers: list[str] = []
    total = sum(shares.values())
    if not isclose(total, 1.0, abs_tol=tolerance):
        blockers.append("ACTION_SHARES_MUST_SUM_TO_ONE")

    add_or_replace = candidate.add_share + candidate.replace_share
    if add_or_replace < PRIMARY_HEATING_GAS_CONVECTOR_SHARE - tolerance:
        blockers.append("ADD_OR_REPLACE_BELOW_GAS_CONVECTOR_TRANSITION_FLOOR")

    return ActionAssessment(not blockers, tuple(blockers))


def build_transition_action_envelope() -> TransitionActionEnvelope:
    population = build_emitter_population_envelope()
    floor = PRIMARY_HEATING_GAS_CONVECTOR_SHARE
    residual = 1.0 - floor

    return TransitionActionEnvelope(
        occupied_dwellings=population.occupied_dwellings,
        add_or_replace_lower=floor,
        add_or_replace_upper=1.0,
        non_keep_lower=floor,
        non_keep_upper=1.0,
        action_bounds={
            "KEEP": ActionShareBounds(0.0, residual),
            "UPSIZE": ActionShareBounds(0.0, residual),
            "CHANGE": ActionShareBounds(0.0, residual),
            "ADD": ActionShareBounds(0.0, 1.0),
            "REPLACE": ActionShareBounds(0.0, 1.0),
        },
        evidence_status="SET_IDENTIFIED_WITH_CALIBRATED_FLOOR",
    )


def action_count_bounds() -> dict[str, tuple[float, float]]:
    envelope = build_transition_action_envelope()
    n = float(envelope.occupied_dwellings)
    result = {
        action: (bounds.lower * n, bounds.upper * n)
        for action, bounds in envelope.action_bounds.items()
    }
    result["ADD_OR_REPLACE"] = (
        envelope.add_or_replace_lower * n,
        envelope.add_or_replace_upper * n,
    )
    result["NON_KEEP"] = (
        envelope.non_keep_lower * n,
        envelope.non_keep_upper * n,
    )
    return result


def _validate_outcome_bounds(
    bounds: tuple[OutcomeCoefficientBound, ...],
    metric: str,
) -> tuple[dict[str, OutcomeCoefficientBound], tuple[str, ...]]:
    blockers: list[str] = []
    rows = [row for row in bounds if row.metric == metric]
    by_action = {row.action: row for row in rows}

    if set(by_action) != set(ACTIONS):
        blockers.append("COMPLETE_ACTION_OUTCOME_BOUNDS_REQUIRED")
        return by_action, tuple(blockers)

    for action in ACTIONS:
        row = by_action[action]
        if row.evidence_status == "Q":
            blockers.append(f"Q_OUTCOME_BOUND:{action}")
        elif row.evidence_status not in REAL_OR_MODEL_EVIDENCE:
            blockers.append(f"INVALID_OUTCOME_EVIDENCE_STATUS:{action}")
        if row.lower is None or row.upper is None:
            blockers.append(f"MISSING_OUTCOME_BOUND:{action}")
        elif row.lower > row.upper:
            blockers.append(f"INVERTED_OUTCOME_BOUND:{action}")
        if row.monetary and row.price_authority_status != "QUALIFIED":
            blockers.append(f"NO_PRICE_AUTHORITY:{action}")

    return by_action, tuple(blockers)


def _linear_extreme(coefficients: dict[str, float], *, maximize: bool) -> float:
    """Solve the P66 action simplex with ADD+REPLACE >= calibrated floor.

    There are no action-specific lower bounds besides zero. KEEP/UPSIZE/CHANGE
    inherit the combined gas-convector restriction through the coupled
    ADD+REPLACE floor. The sharp optimum therefore has at most two active
    actions.
    """

    floor = PRIMARY_HEATING_GAS_CONVECTOR_SHARE
    ar_actions = ("ADD", "REPLACE")
    other_actions = ("KEEP", "UPSIZE", "CHANGE")

    key = max if maximize else min
    best_ar = key(coefficients[a] for a in ar_actions)
    best_other = key(coefficients[a] for a in other_actions)
    best_overall = key(coefficients.values())

    if best_overall == best_ar:
        return best_ar

    return floor * best_ar + (1.0 - floor) * best_other


def propagate_metric_bounds(
    bounds: tuple[OutcomeCoefficientBound, ...],
    metric: str,
) -> MetricEnvelope:
    """Propagate complete per-action coefficient bounds over the action set.

    The function is fail-closed. It does not invent missing physical outcome
    coefficients and it rejects monetary propagation without separately
    qualified price authority.
    """

    by_action, blockers = _validate_outcome_bounds(bounds, metric)
    if blockers:
        return MetricEnvelope("Q", metric, None, None, blockers)

    lower_coefficients = {
        action: float(by_action[action].lower) for action in ACTIONS
    }
    upper_coefficients = {
        action: float(by_action[action].upper) for action in ACTIONS
    }

    return MetricEnvelope(
        status="SET_BOUNDED",
        metric=metric,
        lower=_linear_extreme(lower_coefficients, maximize=False),
        upper=_linear_extreme(upper_coefficients, maximize=True),
        blockers=(),
    )
