"""B02-P114 current Hungarian window-glazing population bound.

P103-P113 pursued a current replaced-window compliance population surface through
record-level EKR/KEHOP administrative routes. P114 adds a direct current-stock
observation that is closer to the physical programme question.

EU-SILC 2023 household-energy-efficiency results for Hungary report the current
window-glazing mix:
- only single glazing: 16.2%
- only double glazing: 63.1%
- triple glazing or more: 12.2%
- mixed single and double/triple: 5.3%
- mixed double and triple: 3.2%

Thus 21.5% of Hungarian surveyed households have at least one single-glazed
window in the current dwelling.

The same survey reports Hungary's current main heating-system marginal:
- district heating: 15.4%
- non-district: 84.6%.

Without assuming independence, Frechet bounds imply that at least 6.1% of the
whole household population is simultaneously:
- non-district heated; and
- single-glazing-present.

Conditioned on the non-district household population this is a hard lower bound
of 6.1 / 84.6 = 7.2104018913%.

Current Hungarian technical authority sets the glazing requirement at
U <= 1.0 W/m2K. The official calculation appendix gives ordinary 4 mm
single glazing U_glass = 5.8 W/m2K. Therefore the single-glazing-present class
is a direct current glazing-deficit class against the current glazing reference.

Critical limitations:
- HC004 observes glazing type, not whole-window realized Uw.
- double glazing spans materially different U-values in the official reference
  table and cannot be promoted to compliant.
- household-weighted survey shares are not exact Census dwelling counts.
- the Frechet bound is intentionally dependence-free and does not identify the
  exact HC001 x HC004 joint distribution.

P114 therefore replaces the generic absence of current national window evidence
with an observed current glazing-type population surface and a hard
non-district single-glazing deficit floor. The remaining performance blocker is
the realized whole-window Uw distribution of the multi-glazed stock.

Boundaries:
SINGLE_GLAZING_PRESENT != WHOLE_WINDOW_UW_VALUE
DOUBLE_GLAZING != CURRENT_UW_COMPLIANCE
TRIPLE_GLAZING != CURRENT_UW_COMPLIANCE
HOUSEHOLD_WEIGHTED_SURVEY_SHARE != EXACT_DWELLING_COUNT
MARGINALS_PLUS_FRECHET != OBSERVED_JOINT_TABLE
"""

from __future__ import annotations

from dataclasses import dataclass

from modules.B02.current_replaced_window_u_quality import (
    P102_HP_ONLY_UPPER,
    P102_STRUCTURAL_CALIBRATED_RETROFIT_FLOOR,
)

HU_ONLY_SINGLE_GLAZING_SHARE = 0.162
HU_ONLY_DOUBLE_GLAZING_SHARE = 0.631
HU_TRIPLE_OR_MORE_GLAZING_SHARE = 0.122
HU_MIXED_SINGLE_AND_MULTIGLAZING_SHARE = 0.053
HU_MIXED_DOUBLE_AND_TRIPLE_SHARE = 0.032

HU_SINGLE_GLAZING_PRESENT_SHARE = (
    HU_ONLY_SINGLE_GLAZING_SHARE + HU_MIXED_SINGLE_AND_MULTIGLAZING_SHARE
)

HU_DISTRICT_HEATING_SHARE = 0.154
HU_NON_DISTRICT_HEATING_SHARE = 1.0 - HU_DISTRICT_HEATING_SHARE

CURRENT_GLAZING_U_REQUIREMENT_W_M2K = 1.0
OFFICIAL_SINGLE_GLAZING_REFERENCE_U_W_M2K = 5.8

P114_STATUS = "QUALIFIED_CURRENT_WINDOW_GLAZING_POPULATION_BOUND"
SUPERSEDED_GENERIC_GAP = "CURRENT_REPLACED_WINDOW_COMPLIANCE_POPULATION_SURFACE_REQUIRED"
PRIMARY_NEXT_RESIDUAL = "CURRENT_MULTIGLAZED_WINDOW_REALIZED_UW_DISTRIBUTION_REQUIRED"
DWELLING_GRAIN_RESIDUAL = "HC004_HOUSEHOLD_TO_B02_DWELLING_POPULATION_BINDING_REQUIRED"
KEHOP_RECORD_ROUTE = "FAIR_IH_KEHOP_1103_COMPLETION_RECORD_EXTRACT_REQUIRED"


@dataclass(frozen=True)
class FrechetBound:
    intersection_lower: float
    intersection_upper: float
    conditional_lower: float
    conditional_upper: float


def frechet_non_district_single_glazing_bound(
    *,
    single_glazing_present_share: float = HU_SINGLE_GLAZING_PRESENT_SHARE,
    non_district_share: float = HU_NON_DISTRICT_HEATING_SHARE,
) -> FrechetBound:
    for value in (single_glazing_present_share, non_district_share):
        if not 0.0 <= value <= 1.0:
            raise ValueError("shares must be in [0,1]")
    if non_district_share == 0.0:
        raise ValueError("non_district_share must be positive")

    lower = max(0.0, single_glazing_present_share + non_district_share - 1.0)
    upper = min(single_glazing_present_share, non_district_share)
    return FrechetBound(
        intersection_lower=lower,
        intersection_upper=upper,
        conditional_lower=lower / non_district_share,
        conditional_upper=upper / non_district_share,
    )


def single_glazing_is_current_glazing_deficit() -> bool:
    return (
        OFFICIAL_SINGLE_GLAZING_REFERENCE_U_W_M2K
        > CURRENT_GLAZING_U_REQUIREMENT_W_M2K
    )


def p114_state() -> dict[str, object]:
    b = frechet_non_district_single_glazing_bound()
    return {
        "status": P114_STATUS,
        "hungary_current_window_type_surface_observed": True,
        "only_single_glazing_share": HU_ONLY_SINGLE_GLAZING_SHARE,
        "only_double_glazing_share": HU_ONLY_DOUBLE_GLAZING_SHARE,
        "triple_or_more_glazing_share": HU_TRIPLE_OR_MORE_GLAZING_SHARE,
        "mixed_single_and_multiglazing_share": (
            HU_MIXED_SINGLE_AND_MULTIGLAZING_SHARE
        ),
        "mixed_double_and_triple_share": HU_MIXED_DOUBLE_AND_TRIPLE_SHARE,
        "single_glazing_present_share": HU_SINGLE_GLAZING_PRESENT_SHARE,
        "district_heating_share_same_survey": HU_DISTRICT_HEATING_SHARE,
        "non_district_heating_share_same_survey": HU_NON_DISTRICT_HEATING_SHARE,
        "non_district_single_glazing_intersection_lower": b.intersection_lower,
        "non_district_single_glazing_intersection_upper": b.intersection_upper,
        "non_district_single_glazing_conditional_lower": b.conditional_lower,
        "non_district_single_glazing_conditional_upper": b.conditional_upper,
        "current_glazing_u_requirement_w_m2k": CURRENT_GLAZING_U_REQUIREMENT_W_M2K,
        "official_single_glazing_reference_u_w_m2k": (
            OFFICIAL_SINGLE_GLAZING_REFERENCE_U_W_M2K
        ),
        "single_glazing_current_glazing_deficit_proven": (
            single_glazing_is_current_glazing_deficit()
        ),
        "double_glazing_current_whole_window_compliance_proven": False,
        "triple_glazing_current_whole_window_compliance_proven": False,
        "exact_hc001_x_hc004_joint_observed": False,
        "exact_b02_dwelling_count_transfer_admitted": False,
        "superseded_generic_gap": SUPERSEDED_GENERIC_GAP,
        "primary_residual": PRIMARY_NEXT_RESIDUAL,
        "dwelling_grain_residual": DWELLING_GRAIN_RESIDUAL,
        "kehop_record_route": KEHOP_RECORD_ROUTE,
        "p102_structural_calibrated_retrofit_floor_lower_share": (
            P102_STRUCTURAL_CALIBRATED_RETROFIT_FLOOR
        ),
        "hp_only_share_lower": 0.0,
        "hp_only_share_upper": P102_HP_ONLY_UPPER,
        "p114_numeric_overall_bound_tightening": False,
    }


def semantic_boundaries() -> tuple[str, ...]:
    return (
        "SINGLE_GLAZING_PRESENT_IS_NOT_WHOLE_WINDOW_UW_VALUE",
        "DOUBLE_GLAZING_IS_NOT_CURRENT_UW_COMPLIANCE",
        "TRIPLE_GLAZING_IS_NOT_CURRENT_UW_COMPLIANCE",
        "HOUSEHOLD_WEIGHTED_SURVEY_SHARE_IS_NOT_EXACT_DWELLING_COUNT",
        "MARGINALS_PLUS_FRECHET_IS_NOT_OBSERVED_JOINT_TABLE",
    )
