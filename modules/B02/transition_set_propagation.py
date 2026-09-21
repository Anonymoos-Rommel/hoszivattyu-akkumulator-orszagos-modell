"""B02-P69 layered transition-set propagation.

P69 supersedes the P66 five-way dwelling-level action simplex after the
repository's own earlier evidence showed that it conflated two different
grains:

* P41: dwelling-level thermal-distribution path
  REUSE_EXISTING_DISTRIBUTION / REPLACE_EXISTING_DISTRIBUTION.
* P55: room/emitter-level actions KEEP / UPSIZE / CHANGE / ADD, where multiple
  action types can occur in the same dwelling.

Therefore:

DISTRIBUTION PATH IS EXCLUSIVE AT DWELLING GRAIN.
EMITTER ACTIONS ARE NON-EXCLUSIVE AT ROOM / EMITTER GRAIN.
GAS-CONVECTOR FLOOR -> REPLACE_EXISTING_DISTRIBUTION LOWER BOUND.
GAS-CONVECTOR FLOOR != ADD/REPLACE EMITTER-ACTION SIMPLEX.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import isclose, isfinite

from modules.B02.emitter_marginal_reconciliation import (
    PRIMARY_HEATING_GAS_CONVECTOR_SHARE,
)
from modules.B02.emitter_set_identification import build_emitter_population_envelope


REUSE_EXISTING_DISTRIBUTION = "REUSE_EXISTING_DISTRIBUTION"
REPLACE_EXISTING_DISTRIBUTION = "REPLACE_EXISTING_DISTRIBUTION"
DISTRIBUTION_PATHS = (
    REUSE_EXISTING_DISTRIBUTION,
    REPLACE_EXISTING_DISTRIBUTION,
)

KEEP = "KEEP"
UPSIZE = "UPSIZE"
CHANGE = "CHANGE"
ADD = "ADD"
EMITTER_ACTIONS = (KEEP, UPSIZE, CHANGE, ADD)

REAL_OR_MODEL_EVIDENCE = frozenset({"OBS", "DER", "ASS", "MODELLED", "SCN"})


@dataclass(frozen=True)
class DistributionPathCandidate:
    reuse_share: float
    replace_share: float


@dataclass(frozen=True)
class LayerAssessment:
    admissible: bool
    blockers: tuple[str, ...]


@dataclass(frozen=True)
class ShareBounds:
    lower: float
    upper: float


@dataclass(frozen=True)
class DistributionPathEnvelope:
    occupied_dwellings: int
    reuse_existing_distribution: ShareBounds
    replace_existing_distribution: ShareBounds
    evidence_status: str


@dataclass(frozen=True)
class EmitterActionIncidence:
    """Independent room/emitter action incidences.

    These are not a simplex. A dwelling can contain several rooms and may
    simultaneously contain KEEP, UPSIZE, CHANGE and ADD events.
    """

    keep: float
    upsize: float
    change: float
    add: float

    def as_dict(self) -> dict[str, float]:
        return {
            KEEP: self.keep,
            UPSIZE: self.upsize,
            CHANGE: self.change,
            ADD: self.add,
        }


@dataclass(frozen=True)
class DistributionOutcomeBound:
    path: str
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
    if not isfinite(float(value)) or not 0.0 <= float(value) <= 1.0:
        raise ValueError(f"{name} must be finite within [0,1]")


def assess_distribution_path_candidate(
    candidate: DistributionPathCandidate,
    *,
    tolerance: float = 1e-12,
) -> LayerAssessment:
    _unit_share(candidate.reuse_share, "reuse_share")
    _unit_share(candidate.replace_share, "replace_share")

    blockers: list[str] = []
    if not isclose(candidate.reuse_share + candidate.replace_share, 1.0, abs_tol=tolerance):
        blockers.append("DISTRIBUTION_PATH_SHARES_MUST_SUM_TO_ONE")
    if candidate.replace_share < PRIMARY_HEATING_GAS_CONVECTOR_SHARE - tolerance:
        blockers.append("REPLACE_DISTRIBUTION_BELOW_GAS_CONVECTOR_FLOOR")
    return LayerAssessment(not blockers, tuple(blockers))


def build_distribution_path_envelope() -> DistributionPathEnvelope:
    population = build_emitter_population_envelope()
    floor = PRIMARY_HEATING_GAS_CONVECTOR_SHARE
    return DistributionPathEnvelope(
        occupied_dwellings=population.occupied_dwellings,
        reuse_existing_distribution=ShareBounds(0.0, 1.0 - floor),
        replace_existing_distribution=ShareBounds(floor, 1.0),
        evidence_status="SET_IDENTIFIED_WITH_CALIBRATED_REPLACEMENT_FLOOR",
    )


def distribution_count_bounds() -> dict[str, tuple[float, float]]:
    e = build_distribution_path_envelope()
    n = float(e.occupied_dwellings)
    return {
        REUSE_EXISTING_DISTRIBUTION: (
            e.reuse_existing_distribution.lower * n,
            e.reuse_existing_distribution.upper * n,
        ),
        REPLACE_EXISTING_DISTRIBUTION: (
            e.replace_existing_distribution.lower * n,
            e.replace_existing_distribution.upper * n,
        ),
    }


def assess_emitter_action_incidence(
    incidence: EmitterActionIncidence,
) -> LayerAssessment:
    """Validate independent incidences without imposing a false simplex."""

    for name, value in incidence.as_dict().items():
        _unit_share(value, name)
    return LayerAssessment(True, ())


def _validate_distribution_outcome_bounds(
    bounds: tuple[DistributionOutcomeBound, ...],
    metric: str,
) -> tuple[dict[str, DistributionOutcomeBound], tuple[str, ...]]:
    blockers: list[str] = []
    rows = [row for row in bounds if row.metric == metric]
    by_path = {row.path: row for row in rows}

    if set(by_path) != set(DISTRIBUTION_PATHS):
        blockers.append("COMPLETE_DISTRIBUTION_PATH_OUTCOME_BOUNDS_REQUIRED")
        return by_path, tuple(blockers)

    for path in DISTRIBUTION_PATHS:
        row = by_path[path]
        if row.evidence_status == "Q":
            blockers.append(f"Q_OUTCOME_BOUND:{path}")
        elif row.evidence_status not in REAL_OR_MODEL_EVIDENCE:
            blockers.append(f"INVALID_OUTCOME_EVIDENCE_STATUS:{path}")
        if row.lower is None or row.upper is None:
            blockers.append(f"MISSING_OUTCOME_BOUND:{path}")
        elif row.lower > row.upper:
            blockers.append(f"INVERTED_OUTCOME_BOUND:{path}")
        if row.monetary and row.price_authority_status != "QUALIFIED":
            blockers.append(f"NO_PRICE_AUTHORITY:{path}")

    return by_path, tuple(blockers)


def propagate_distribution_metric_bounds(
    bounds: tuple[DistributionOutcomeBound, ...],
    metric: str,
) -> MetricEnvelope:
    """Sharp propagation over the two-path dwelling-level distribution set."""

    by_path, blockers = _validate_distribution_outcome_bounds(bounds, metric)
    if blockers:
        return MetricEnvelope("Q", metric, None, None, blockers)

    floor = PRIMARY_HEATING_GAS_CONVECTOR_SHARE
    reuse = by_path[REUSE_EXISTING_DISTRIBUTION]
    replace = by_path[REPLACE_EXISTING_DISTRIBUTION]

    low_reuse = float(reuse.lower)
    high_reuse = float(reuse.upper)
    low_replace = float(replace.lower)
    high_replace = float(replace.upper)

    # x = replacement share in [floor, 1]. Objective is affine in x, so each
    # extremum is attained at one interval endpoint.
    lower_candidates = (
        (1.0 - floor) * low_reuse + floor * low_replace,
        low_replace,
    )
    upper_candidates = (
        (1.0 - floor) * high_reuse + floor * high_replace,
        high_replace,
    )

    return MetricEnvelope(
        status="SET_BOUNDED",
        metric=metric,
        lower=min(lower_candidates),
        upper=max(upper_candidates),
        blockers=(),
    )


def legacy_five_way_action_simplex_status() -> str:
    """Machine-readable supersession marker for downstream callers."""

    return "SUPERSEDED_BY_B02_P69_LAYERED_ACTION_MODEL"
