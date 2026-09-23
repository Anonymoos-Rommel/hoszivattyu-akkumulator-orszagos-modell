"""B02-P99 fresh envelope-action evidence audit.

P81 already defines the admissible national route:
representative public evidence -> semantic/freshness admission ->
bounded population inference -> uncertainty propagation.

P99 supplies real current/fresh evidence to that contract without confusing
three different estimands:

1. national observed envelope-action rates;
2. regional/structural renovation-pattern validation;
3. recent programme implementation volumes.

The binding national action-rate source is the representative TARKI-REKK 2022
survey. It reports the previous-12-month shares for four envelope actions:

- facade insulation: 3.7%
- roof insulation: 2.4%
- attic-floor insulation: 4.1%
- window replacement: 8.2%

The source does not publish overlap between these actions. Therefore the sharp
set-theoretic bound for ANY of the four actions is:

    lower = max(component shares) = 8.2%
    upper = min(1, sum(component shares)) = 18.4%

No independence assumption and no sum-as-point-estimate are allowed.

The 2023 Budapest CARES survey is independent structural validation only.
The 2025-26 EKR/Takarekos Otthon implementation volume is recent realized
implementation validation only.
MEHI's 2025/26 data-gap assessment explicitly says Hungary still lacks a
unified renovation-monitoring system capable of reliable annual-rate tracking.

Consequently P99 resolves the generic claim that fresh envelope-action evidence
is absent, but it does NOT convert observed historical/current renovation
activity into the future reference-programme split between HP_ONLY and
REFERENCE_ENVELOPE_RETROFIT_PLUS_AWHP.

Critical boundaries:

OBSERVED_RECENT_ENVELOPE_ACTION_RATE != REFERENCE_PROGRAMME_ACTION_SHARE
SUM_OF_COMPONENT_ACTION_RATES != ANY_ACTION_POINT_RATE
BUDAPEST_REPRESENTATIVE != HUNGARY_REPRESENTATIVE
REALIZED_EKR_ACTION_VOLUME != NATIONAL_ANNUAL_RATE
PUBLICATION_YEAR != OBSERVATION_YEAR
FRESH_ACTION_EVIDENCE != REFERENCE_U_COMPLIANCE
"""

from __future__ import annotations

from dataclasses import dataclass


REKK_SOURCE_ID = "SRC-B02-HU-REKK-TARKI-ENVELOPE-2022"
CARES_SOURCE_ID = "SRC-B02-BUDAPEST-CARES-HOUSEHOLD-SURVEY-2023"
EKR_SOURCE_ID = "SRC-B02-HU-EKR-ATTIC-IMPLEMENTATION-2026"
MEHI_MONITORING_SOURCE_ID = "SRC-B02-HU-MEHI-RENOVATION-DATA-GAPS-2025"

REKK_OBSERVATION_YEAR = 2022
FRESHNESS_FLOOR_YEAR = 2021

REKK_LAST_12M_ACTION_SHARES = {
    "FACADE_INSULATION": 0.037,
    "ROOF_INSULATION": 0.024,
    "ATTIC_FLOOR_INSULATION": 0.041,
    "WINDOW_REPLACEMENT": 0.082,
}

REKK_2022_STOCK_STATE_SHARES = {
    "INSULATED_FACADE": 0.350,
    "INSULATED_ATTIC_OR_CEILING": 0.297,
    "WINDOW_REPLACED": 0.527,
}

RECENT_EKR_ATTIC_INSULATION_PROPERTIES = 50_000

P99_STATUS = "PARTIAL_RESOLVED_FRESH_MULTI_SOURCE_ACTION_EVIDENCE"
NEXT_RESIDUAL = "REFERENCE_PROGRAMME_ENVELOPE_ACTION_SELECTION_CROSSWALK_REQUIRED"


@dataclass(frozen=True)
class EnvelopeActionRateEnvelope:
    observation_year: int
    lower_share: float
    upper_share: float
    component_shares: tuple[tuple[str, float], ...]
    status: str
    evidence_status: str
    source_id: str
    warnings: tuple[str, ...]


@dataclass(frozen=True)
class EnvelopeActionEvidenceState:
    status: str
    binding_national_source_id: str
    independent_validation_source_ids: tuple[str, ...]
    current_monitoring_boundary_source_id: str
    any_major_envelope_action_lower_share: float
    any_major_envelope_action_upper_share: float
    national_point_rate_for_2026_available: bool
    reference_programme_action_share_identified: bool
    residual: str
    warnings: tuple[str, ...]


def union_bounds_without_overlap_information(
    shares: tuple[float, ...],
) -> tuple[float, float]:
    """Sharp generic union bounds when marginal shares are known but overlap is not."""

    if not shares:
        raise ValueError("at least one share is required")
    if any(value < 0.0 or value > 1.0 for value in shares):
        raise ValueError("shares must lie within [0,1]")
    return max(shares), min(1.0, sum(shares))


def national_2022_recent_envelope_action_rate() -> EnvelopeActionRateEnvelope:
    shares = tuple(REKK_LAST_12M_ACTION_SHARES.values())
    lower, upper = union_bounds_without_overlap_information(shares)
    return EnvelopeActionRateEnvelope(
        observation_year=REKK_OBSERVATION_YEAR,
        lower_share=lower,
        upper_share=upper,
        component_shares=tuple(REKK_LAST_12M_ACTION_SHARES.items()),
        status="QUALIFIED_REPRESENTATIVE_NATIONAL_BOUNDED_ACTION_RATE",
        evidence_status="OBS/DER",
        source_id=REKK_SOURCE_ID,
        warnings=(
            "COMPONENT_ACTION_OVERLAP_NOT_PUBLISHED",
            "ANNUAL_ACTION_RATE_IS_NOT_REFERENCE_PROGRAMME_ACTION_SHARE",
            "2022_OBSERVATION_IS_NOT_2026_POINT_RATE",
        ),
    )


def current_p99_evidence_state() -> EnvelopeActionEvidenceState:
    rate = national_2022_recent_envelope_action_rate()
    return EnvelopeActionEvidenceState(
        status=P99_STATUS,
        binding_national_source_id=REKK_SOURCE_ID,
        independent_validation_source_ids=(
            CARES_SOURCE_ID,
            EKR_SOURCE_ID,
        ),
        current_monitoring_boundary_source_id=MEHI_MONITORING_SOURCE_ID,
        any_major_envelope_action_lower_share=rate.lower_share,
        any_major_envelope_action_upper_share=rate.upper_share,
        national_point_rate_for_2026_available=False,
        reference_programme_action_share_identified=False,
        residual=NEXT_RESIDUAL,
        warnings=(
            "BUDAPEST_CARES_IS_REGIONAL_STRUCTURAL_VALIDATION_ONLY",
            "EKR_50000_ATTIC_ACTIONS_ARE_REALIZED_VOLUME_NOT_COMPARABLE_NATIONAL_RATE",
            "MEHI_MONITORING_GAP_PREVENTS_2026_POINT_RATE_PROMOTION",
            "OBSERVED_ACTION_ACTIVITY_DOES_NOT_IDENTIFY_FUTURE_PROGRAMME_SELECTION",
        ),
    )


def p99_state() -> dict[str, object]:
    rate = national_2022_recent_envelope_action_rate()
    state = current_p99_evidence_state()
    return {
        "observation_year": rate.observation_year,
        "component_action_shares": dict(rate.component_shares),
        "any_major_envelope_action_bound": (rate.lower_share, rate.upper_share),
        "stock_state_shares": dict(REKK_2022_STOCK_STATE_SHARES),
        "recent_ekr_attic_insulation_properties": (
            RECENT_EKR_ATTIC_INSULATION_PROPERTIES
        ),
        "fresh_multi_source_evidence_status": state.status,
        "fresh_multi_source_evidence_blocker": None,
        "reference_programme_selection_residual": state.residual,
        "national_2026_point_rate_available": (
            state.national_point_rate_for_2026_available
        ),
        "reference_programme_action_share_identified": (
            state.reference_programme_action_share_identified
        ),
    }


def semantic_boundaries() -> tuple[str, ...]:
    return (
        "OBSERVED_RECENT_ENVELOPE_ACTION_RATE_IS_NOT_REFERENCE_PROGRAMME_ACTION_SHARE",
        "SUM_OF_COMPONENT_ACTION_RATES_IS_NOT_ANY_ACTION_POINT_RATE",
        "BUDAPEST_REPRESENTATIVE_IS_NOT_HUNGARY_REPRESENTATIVE",
        "REALIZED_EKR_ACTION_VOLUME_IS_NOT_NATIONAL_ANNUAL_RATE",
        "PUBLICATION_YEAR_IS_NOT_OBSERVATION_YEAR",
        "FRESH_ACTION_EVIDENCE_IS_NOT_REFERENCE_U_COMPLIANCE",
    )
