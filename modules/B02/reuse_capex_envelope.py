"""B02-P76 conservative reuse-path CAPEX envelope from the current KEHOP call.

P76 separates three questions that earlier slices partially conflated:

1. technical action authority;
2. technical CAPEX reference;
3. current-programme legal/funding eligibility.

The current KEHOP Plusz-4.1.7-24 call explicitly permits:
- secondary heating-circuit adaptation;
- heat-emitter modernization or replacement;
- automatic central/source-side and local/emitter-side controls.

Annex 1 publishes a 3,556,000 HUF/set maximum for the broader complete
"heat emitters replacement" package including new emitters, secondary circuit,
controls, modern pipework, HMV tank, installation materials and demolition.

There is no separate source-native reuse-only price line. P76 therefore uses the
complete replacement package only as an explicit modelled *superset ceiling*
for the narrower reuse-path secondary-side work, and only when the counted reuse
work scope is a subset of that complete package.

Critical boundaries:

OFFICIAL REPLACEMENT PACKAGE CEILING != OFFICIAL REUSE PRICE
CONSERVATIVE SUPERSET CAP != MARKET-TYPICAL OR EXPECTED COST
TECHNICAL REFERENCE COST != CURRENT KEHOP FUNDING ELIGIBILITY
KEHOP FAMILY-HOUSE TECHNICAL ACTION AUTHORITY != FULL NATIONAL ACTION AUTHORITY
"""

from __future__ import annotations

from dataclasses import dataclass

from modules.B02.kehop_scope_crosswalk import build_kehop_scope_crosswalk
from modules.B02.hungarian_path_outcome_authority import (
    KEHOP_EMITTER_PACKAGE_TOTAL_MAX_HUF,
)


REUSE_EXISTING_DISTRIBUTION = "REUSE_EXISTING_DISTRIBUTION"
ASS_CONSERVATIVE_SUPERSET_UPPER_BOUND = "ASS_CONSERVATIVE_SUPERSET_UPPER_BOUND"
QUALIFIED_SCOPE_LIMITED_TECHNICAL_ACTION_AUTHORITY = (
    "QUALIFIED_SCOPE_LIMITED_TECHNICAL_ACTION_AUTHORITY"
)
Q = "Q"


@dataclass(frozen=True)
class ReuseCapexEnvelope:
    path: str
    per_set_lower_huf: float
    per_set_upper_huf: float
    definite_pre2007_reuse_candidate_upper: float
    possible_pre2007_reuse_candidate_upper: float
    definite_pre2007_aggregate_upper_huf: float
    possible_pre2007_aggregate_upper_huf: float
    evidence_status: str
    work_scope_status: str


@dataclass(frozen=True)
class P76Decision:
    status: str
    blockers: tuple[str, ...]


def _central_family_bounds() -> tuple[float, float]:
    x = build_kehop_scope_crosswalk()
    definite_upper = max(
        x.central.central_family_definite_pre2007,
        x.flat.central_family_definite_pre2007,
    )
    possible_upper = max(
        x.central.central_family_possible_pre2007,
        x.flat.central_family_possible_pre2007,
    )
    if not 0.0 <= definite_upper <= possible_upper <= x.physical_scope_dwellings:
        raise ValueError("reuse structural candidate bounds invalid")
    return definite_upper, possible_upper


def build_reuse_capex_envelope() -> ReuseCapexEnvelope:
    """Build the conservative KEHOP-compatible reuse-path CAPEX envelope.

    Lower reuse count is zero because P73 keeps the CENTRAL_HEATING split latent.
    The upper population is the maximum structurally compatible CENTRAL_HEATING
    FAMILY_HOUSE count from P75. The per-set upper bound is *not* promoted to an
    official reuse tariff; it is an ASS cost-dominance envelope from the broader
    official replacement package.
    """

    definite_upper, possible_upper = _central_family_bounds()
    ceiling = float(KEHOP_EMITTER_PACKAGE_TOTAL_MAX_HUF)
    return ReuseCapexEnvelope(
        path=REUSE_EXISTING_DISTRIBUTION,
        per_set_lower_huf=0.0,
        per_set_upper_huf=ceiling,
        definite_pre2007_reuse_candidate_upper=definite_upper,
        possible_pre2007_reuse_candidate_upper=possible_upper,
        definite_pre2007_aggregate_upper_huf=definite_upper * ceiling,
        possible_pre2007_aggregate_upper_huf=possible_upper * ceiling,
        evidence_status=ASS_CONSERVATIVE_SUPERSET_UPPER_BOUND,
        work_scope_status="REUSE_SECONDARY_WORK_SUBSET_OF_COMPLETE_REPLACEMENT_PACKAGE",
    )


def assess_reuse_cost_use(
    *,
    requested_use: str,
    structural_scope_compatible: bool,
    reuse_work_scope_is_subset: bool,
) -> P76Decision:
    """Fail closed outside the explicit conservative transfer contract."""

    if requested_use == "TECHNICAL_REUSE_CAPEX_UPPER_BOUND":
        blockers: list[str] = []
        if not structural_scope_compatible:
            blockers.append("OUTSIDE_KEHOP_STRUCTURAL_SCOPE_CAPEX_AUTHORITY")
        if not reuse_work_scope_is_subset:
            blockers.append("REUSE_WORK_SCOPE_NOT_PROVEN_SUBSET_OF_REPLACEMENT_PACKAGE")
        if blockers:
            return P76Decision(Q, tuple(blockers))
        return P76Decision(ASS_CONSERVATIVE_SUPERSET_UPPER_BOUND, ())

    if requested_use == "OFFICIAL_REUSE_PRICE":
        return P76Decision(Q, ("NO_SOURCE_NATIVE_REUSE_ONLY_PRICE_LINE",))
    if requested_use in {"MARKET_TYPICAL", "EXPECTED_REALIZED_COST"}:
        return P76Decision(Q, ("SUPERSET_CEILING_IS_NOT_MARKET_DISTRIBUTION",))
    if requested_use == "CURRENT_KEHOP_FUNDING_ELIGIBILITY":
        return P76Decision(Q, ("PROJECT_SPECIFIC_LEGAL_ELIGIBILITY_REQUIRED",))
    return P76Decision(Q, ("UNSUPPORTED_REUSE_COST_USE",))


def assess_family_house_reuse_action_authority(
    *,
    structural_scope_compatible: bool,
    requested_use: str,
) -> P76Decision:
    """Bind current KEHOP 3.4.1.2/3.4.1.3 to the P75 family-house scope."""

    if requested_use != "TECHNICAL_ACTION_FAMILY":
        return P76Decision(Q, ("UNSUPPORTED_ACTION_AUTHORITY_USE",))
    if not structural_scope_compatible:
        return P76Decision(
            Q,
            ("REUSE_ACTION_AUTHORITY_OUTSIDE_KEHOP_STRUCTURAL_SCOPE_REQUIRED",),
        )
    return P76Decision(QUALIFIED_SCOPE_LIMITED_TECHNICAL_ACTION_AUTHORITY, ())


def assess_legal_eligibility_relevance(*, requested_use: str) -> P76Decision:
    """Keep programme eligibility separate from the national technical model."""

    if requested_use == "TECHNICAL_CAPEX_REFERENCE":
        return P76Decision("NOT_REQUIRED_FOR_TECHNICAL_REFERENCE_COST", ())
    if requested_use == "TECHNICAL_ACTION_REFERENCE":
        return P76Decision("NOT_REQUIRED_FOR_TECHNICAL_ACTION_REFERENCE", ())
    if requested_use == "CURRENT_KEHOP_FUNDING_ELIGIBILITY":
        return P76Decision(Q, ("PROJECT_SPECIFIC_LEGAL_ELIGIBILITY_REQUIRED",))
    return P76Decision(Q, ("UNSUPPORTED_LEGAL_ELIGIBILITY_USE",))
