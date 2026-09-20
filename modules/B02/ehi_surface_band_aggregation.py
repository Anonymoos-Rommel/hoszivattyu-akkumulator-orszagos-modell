"""B02-P64 EHI denominator-invariance helper.

This module proves a narrow mathematical fact only:

If every source-native residential stratum has the same prevalence interval
[L, U], then any convex mixture of those strata is also bounded by [L, U],
regardless of the denominator weights.

It does not map EHI houses/apartments to P21 FAMILY_HOUSE/MULTI_DWELLING,
does not create an emitter point estimate, and does not solve mixed-system
overlap.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import isclose
from typing import Iterable, Sequence


LOWER = 0.33
UPPER = 0.66
EVIDENCE_STATUS = "DER"
USE = "NATIONAL_VALIDATION_BAND_ONLY"


@dataclass(frozen=True)
class BoundedStratum:
    name: str
    lower: float
    upper: float


@dataclass(frozen=True)
class AggregateEnvelope:
    lower: float
    upper: float
    denominator_weights_required: bool
    evidence_status: str
    use: str


def _validate_bound(lower: float, upper: float) -> None:
    if not (0.0 <= lower <= upper <= 1.0):
        raise ValueError("prevalence bounds must satisfy 0 <= lower <= upper <= 1")


def aggregate_envelope(
    strata: Sequence[BoundedStratum],
    weights: Iterable[float] | None = None,
) -> AggregateEnvelope:
    """Return the sharp convex-mixture envelope for bounded strata.

    If weights is omitted, this function may return a denominator-invariant
    envelope only when every stratum has the same lower and upper bounds.

    If weights are provided they must be non-negative and sum to one.
    """

    if not strata:
        raise ValueError("at least one stratum is required")

    for stratum in strata:
        _validate_bound(stratum.lower, stratum.upper)

    if weights is None:
        common_lower = strata[0].lower
        common_upper = strata[0].upper
        if not all(
            isclose(s.lower, common_lower, abs_tol=1e-12)
            and isclose(s.upper, common_upper, abs_tol=1e-12)
            for s in strata
        ):
            raise ValueError("denominator weights are required for non-identical stratum bounds")
        return AggregateEnvelope(
            lower=common_lower,
            upper=common_upper,
            denominator_weights_required=False,
            evidence_status=EVIDENCE_STATUS,
            use=USE,
        )

    w = tuple(float(x) for x in weights)
    if len(w) != len(strata):
        raise ValueError("weights must align one-to-one with strata")
    if any(x < 0.0 for x in w):
        raise ValueError("weights must be non-negative")
    if not isclose(sum(w), 1.0, abs_tol=1e-12):
        raise ValueError("weights must sum to one")

    lower = sum(weight * stratum.lower for weight, stratum in zip(w, strata))
    upper = sum(weight * stratum.upper for weight, stratum in zip(w, strata))
    return AggregateEnvelope(
        lower=lower,
        upper=upper,
        denominator_weights_required=True,
        evidence_status=EVIDENCE_STATUS,
        use=USE,
    )


def ehi_hungary_residential_validation_envelope() -> AggregateEnvelope:
    """Return the P62 EHI Hungary residential validation envelope.

    EHI 2024 reports the same 33-66% category for its source-native houses
    and apartments strata. Therefore the convex aggregate envelope is
    33-66% independently of their relative denominator weights.

    Source-taxonomy coverage and P21 stratum allocation remain separate
    modelling questions.
    """

    strata = (
        BoundedStratum("EHI_HOUSES", LOWER, UPPER),
        BoundedStratum("EHI_APARTMENTS", LOWER, UPPER),
    )
    return aggregate_envelope(strata)
