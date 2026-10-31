"""B02-P114 conditional interval from published Hungarian 2023 marginals.

HC004 reports only single glazing 16.2%, only double 63.1%, triple or more
12.2%, mixed single/multi 5.3%, mixed double/triple 3.2%. The published
single-glazing-present share is 21.5%. HC001 reports district heating 15.4%
and hence non-district 84.6%. HC001 means the mainly used heating system.

The assessment corroborates a common household/current/H-file scope and
published near-complete survey coverage. Its rounded HU flags report missing
0.0% for both variables and survey/interview 100% for both; these are not exact
denominator, weighting or revision identifiers. Missing table-level metadata
does not establish incompatible populations or unweighted tables.

If both published marginals refer to the same empirical probability measure,
dependence-free Frechet algebra yields intersection [0.061, 0.215] and
conditional interval [7.2104018913%, 25.4137115839%]. The computation is
preserved, but is not a proven uncertainty-free national population bound.
Sampling and publication rounding uncertainty remain separate validation debt.
No new confidence level, replacement bound or independence assumption is chosen.

The recorded technical references compare ordinary 4 mm glazing 5.8 W/m2K
with glazing requirement 1.0 W/m2K. This is a reference-class comparison, not
a measured Ug/Uw value or legal retrofit obligation for each surveyed record.

Critical limitations:
- the exact common table denominator, weight and release are not pinned;
- the reference period is 2023, with no admitted transfer to a later stock;
- household shares are not an admitted Census dwelling-count estimator;
- HC004 glazing categories do not identify realized whole-window Uw;
- no observed HC001 x HC004 joint table is manufactured;
- P102/HP_ONLY numbers and overall readiness remain unchanged.
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

P114_STATUS = "CONDITIONAL_CURRENT_WINDOW_GLAZING_EMPIRICAL_INTERVAL"
CONDITIONAL_INTERVAL_STATUS = "DERIVED_CONDITIONAL_EMPIRICAL_INTERVAL"
VALIDATION_DEBTS = (
    "HC001_HC004_TABLE_DENOMINATOR_WEIGHT_RELEASE_BINDING_REQUIRED",
    "HC001_HC004_SAMPLING_AND_PUBLICATION_ROUNDING_UNCERTAINTY_REQUIRED",
    "HC004_HOUSEHOLD_TO_B02_DWELLING_POPULATION_BINDING_REQUIRED",
    "CURRENT_MULTIGLAZED_WINDOW_REALIZED_UW_DISTRIBUTION_REQUIRED",
    "HC001_HC004_2023_TO_TARGET_PERIOD_STOCK_BRIDGE_REQUIRED",
)
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
        "conditional_interval_status": CONDITIONAL_INTERVAL_STATUS,
        "reference_period": "2023",
        "common_household_current_scope_corroborated": True,
        "published_survey_coverage_corroborated": True,
        "exact_common_table_measure_proven": False,
        "incompatible_populations_proven": False,
        "unweighted_tables_proven": False,
        "true_population_hard_bound_proven": False,
        "exact_table_denominator": None,
        "table_weight_revision": None,
        "table_release_binding": None,
        "sampling_and_rounding_uncertainty": None,
        "target_period_stock_transfer_admitted": False,
        "reference_glazing_comparison_only": True,
        "record_level_glazing_deficit_proven": False,
        "validation_debt": VALIDATION_DEBTS,
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
        "CONDITIONAL_EMPIRICAL_INTERVAL_IS_NOT_TRUE_POPULATION_HARD_BOUND",
        "PUBLISHED_COVERAGE_IS_NOT_EXACT_TABLE_WEIGHT_RELEASE_BINDING",
        "MISSING_WEIGHT_METADATA_IS_NOT_PROOF_OF_INCOMPATIBILITY",
        "ROUNDED_MARGINALS_ARE_NOT_EXACT_POPULATION_PARAMETERS",
        "GLAZING_REFERENCE_COMPARISON_IS_NOT_RECORD_LEVEL_DEFICIT_OR_LEGAL_DUTY",
        "REFERENCE_2023_IS_NOT_LATER_TARGET_STOCK",
    )
