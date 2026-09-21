"""B02-P74 Hungarian distribution-path outcome authority.

P74 binds two already-public Hungarian evidence surfaces to the P73
REUSE_EXISTING_DISTRIBUTION / NEW_OR_REPLACE_DISTRIBUTION_REQUIRED model
without transferring either source beyond its actual scope.

1. EKR 2.11 is a current Hungarian legal/technical authority for secondary-side
   heating reconstruction in its covered building classes. It identifies
   concrete actions such as hydraulic balancing, emitter controls, one-pipe
   conversion and conditional replacement of large-water-volume cast-iron
   radiators.

2. KEHOP Plusz-4.1.7-24 Annex 1 is an official programme maximum-cost authority
   for a complete emitter + secondary-circuit replacement package.

Critical boundaries:

EKR TECHNICAL ACTION AUTHORITY != AWHP ENERGY-SAVING RESPONSE
EKR SOURCE-NATIVE SAVING PERCENTAGES != AWHP PROGRAMME SAVING PERCENTAGES
EKR 7 C REDUCTION CONDITION != AWHP DESIGN-TEMPERATURE DEFAULT
KEHOP MAXIMUM COST != MARKET-TYPICAL OR EXPECTED REALIZED COST
KEHOP ELIGIBLE PROJECT SET != ALL NATIONAL NONREUSE DWELLINGS
"""

from __future__ import annotations

from dataclasses import dataclass

from modules.B02.foreign_response_authority import (
    OfficialCostCeiling,
    Q,
    QUALIFIED_OFFICIAL_UPPER_BOUND,
    validate_official_cost_ceiling,
)


REUSE_EXISTING_DISTRIBUTION = "REUSE_EXISTING_DISTRIBUTION"
NEW_OR_REPLACE_DISTRIBUTION_REQUIRED = "NEW_OR_REPLACE_DISTRIBUTION_REQUIRED"

EKR_SOURCE_ID = "SRC-B02-HU-EKR-211-SECONDARY-HEATING-2026"
KEHOP_COST_SOURCE_ID = "SRC-B02-HU-KEHOP-417-MAX-COST-2025"
KEHOP_PROGRAMME_SOURCE_ID = "SRC-B02-HU-KEHOP-417-PROGRAMME-2026"

QUALIFIED_SCOPE_LIMITED_TECHNICAL_AUTHORITY = (
    "QUALIFIED_SCOPE_LIMITED_TECHNICAL_AUTHORITY"
)
QUALIFIED_SOURCE_NATIVE_EKR_ONLY = "QUALIFIED_SOURCE_NATIVE_EKR_ONLY"
QUALIFIED_TRANSITION_DERIVED_RESPONSE_METHOD = (
    "QUALIFIED_TRANSITION_DERIVED_RESPONSE_METHOD"
)

EKR_COVERED_BUILDING_SCOPES = frozenset(
    {
        "OWN_CENTRAL_HEAT_MULTI_DWELLING",
        "DISTRICT_HEATED_MULTI_DWELLING",
        "PUBLIC_BUILDING",
    }
)

EKR_BASE_SAVING_SHARES = (0.10, 0.06, 0.04)
EKR_CAST_IRON_REPLACEMENT_BONUS_SHARE = 0.03
EKR_MIN_SUPPLY_TEMP_REDUCTION_C = 7.0
EKR_HEAT_REFLECTOR_BONUS_SHARE = 0.01

KEHOP_EMITTER_PACKAGE_MATERIAL_MAX_HUF = 1_422_400.0
KEHOP_EMITTER_PACKAGE_LABOUR_MAX_HUF = 2_133_600.0
KEHOP_EMITTER_PACKAGE_TOTAL_MAX_HUF = 3_556_000.0


@dataclass(frozen=True)
class AuthorityDecision:
    status: str
    blockers: tuple[str, ...]


@dataclass(frozen=True)
class EkrSecondaryHeatingReference:
    required_or_conditional_actions: tuple[str, ...]
    base_saving_shares: tuple[float, ...]
    cast_iron_replacement_bonus_share: float
    min_supply_temp_reduction_c: float
    heat_reflector_bonus_share: float
    excludes_new_energy_carrier: bool
    source_id: str = EKR_SOURCE_ID


@dataclass(frozen=True)
class PathCostUpperBound:
    path: str
    upper_huf_per_set: float
    unit: str
    evidence_status: str
    source_id: str
    scope_status: str


def build_ekr_reference() -> EkrSecondaryHeatingReference:
    return EkrSecondaryHeatingReference(
        required_or_conditional_actions=(
            "ONE_PIPE_TO_TWO_PIPE_OR_BYPASS_CONVERSION",
            "INDIVIDUAL_EMITTER_CONTROL",
            "HYDRAULIC_BALANCING",
            "CONDITIONAL_LARGE_WATER_VOLUME_CAST_IRON_RADIATOR_REPLACEMENT",
            "HEAT_COST_ALLOCATOR_FOR_COVERED_RESIDENTIAL_CASES",
            "CONDITIONAL_HEAT_REFLECTOR",
        ),
        base_saving_shares=EKR_BASE_SAVING_SHARES,
        cast_iron_replacement_bonus_share=EKR_CAST_IRON_REPLACEMENT_BONUS_SHARE,
        min_supply_temp_reduction_c=EKR_MIN_SUPPLY_TEMP_REDUCTION_C,
        heat_reflector_bonus_share=EKR_HEAT_REFLECTOR_BONUS_SHARE,
        excludes_new_energy_carrier=True,
    )


def assess_ekr_use(
    *,
    requested_use: str,
    building_scope: str,
    new_energy_carrier: bool,
) -> AuthorityDecision:
    """Gate use of EKR 2.11 without transferring its accounting response."""

    if requested_use == "TECHNICAL_ACTION_REFERENCE":
        if building_scope not in EKR_COVERED_BUILDING_SCOPES:
            return AuthorityDecision(Q, ("EKR_211_BUILDING_SCOPE_NOT_COVERED",))
        return AuthorityDecision(QUALIFIED_SCOPE_LIMITED_TECHNICAL_AUTHORITY, ())

    if requested_use == "AWHP_ENERGY_SAVING_OUTCOME":
        blockers: list[str] = []
        if building_scope not in EKR_COVERED_BUILDING_SCOPES:
            blockers.append("EKR_211_BUILDING_SCOPE_NOT_COVERED")
        if new_energy_carrier:
            blockers.append("EKR_211_NEW_ENERGY_CARRIER_EXCLUSION")
        else:
            blockers.append("EKR_SOURCE_NATIVE_SAVING_IS_NOT_AWHP_RESPONSE")
        return AuthorityDecision(Q, tuple(blockers))

    if requested_use == "AWHP_DESIGN_TEMPERATURE":
        return AuthorityDecision(
            Q,
            ("EKR_7C_REDUCTION_IS_MEASURE_CONDITION_NOT_AWHP_DESIGN_SETPOINT",),
        )

    if requested_use == "SOURCE_NATIVE_EKR_ACCOUNTING_REFERENCE":
        if building_scope not in EKR_COVERED_BUILDING_SCOPES:
            return AuthorityDecision(Q, ("EKR_211_BUILDING_SCOPE_NOT_COVERED",))
        if new_energy_carrier:
            return AuthorityDecision(Q, ("EKR_211_NEW_ENERGY_CARRIER_EXCLUSION",))
        return AuthorityDecision(QUALIFIED_SOURCE_NATIVE_EKR_ONLY, ())

    return AuthorityDecision(Q, ("UNSUPPORTED_EKR_USE",))


def build_nonreuse_kehop_cost_upper_bound() -> PathCostUpperBound:
    ceiling = OfficialCostCeiling(
        cost_id="KEHOP-EMITTER-PACKAGE",
        material_max_huf=KEHOP_EMITTER_PACKAGE_MATERIAL_MAX_HUF,
        labour_max_huf=KEHOP_EMITTER_PACKAGE_LABOUR_MAX_HUF,
        total_max_huf=KEHOP_EMITTER_PACKAGE_TOTAL_MAX_HUF,
        unit="Ft/készlet",
    )
    decision = validate_official_cost_ceiling(ceiling)
    if decision.status != QUALIFIED_OFFICIAL_UPPER_BOUND:
        raise ValueError("canonical KEHOP emitter-package ceiling failed validation")
    return PathCostUpperBound(
        path=NEW_OR_REPLACE_DISTRIBUTION_REQUIRED,
        upper_huf_per_set=ceiling.total_max_huf,
        unit=ceiling.unit,
        evidence_status=QUALIFIED_OFFICIAL_UPPER_BOUND,
        source_id=KEHOP_COST_SOURCE_ID,
        scope_status="KEHOP_ELIGIBLE_PROJECT_SET_ONLY",
    )


def assess_kehop_path_cost_use(*, requested_use: str) -> AuthorityDecision:
    """Gate the P67 KEHOP maximum after binding it to the nonreuse path."""

    build_nonreuse_kehop_cost_upper_bound()

    if requested_use == "NONREUSE_PATH_PROGRAMME_COST_UPPER_BOUND":
        return AuthorityDecision(QUALIFIED_OFFICIAL_UPPER_BOUND, ())
    if requested_use == "NATIONAL_NONREUSE_POPULATION_COST_UPPER_BOUND":
        return AuthorityDecision(
            Q,
            ("KEHOP_PROJECT_SET_TO_NATIONAL_NONREUSE_SCOPE_CROSSWALK_REQUIRED",),
        )
    if requested_use in {"MARKET_TYPICAL", "EXPECTED_REALIZED_COST"}:
        return AuthorityDecision(
            Q,
            ("OFFICIAL_MAXIMUM_IS_NOT_MARKET_DISTRIBUTION",),
        )
    if requested_use == "REUSE_PATH_COST_BOUND":
        return AuthorityDecision(
            Q,
            ("KEHOP_COMPLETE_REPLACEMENT_PACKAGE_IS_NOT_REUSE_PATH_COST_BOUND",),
        )
    return AuthorityDecision(Q, ("UNSUPPORTED_KEHOP_PATH_COST_USE",))


def assess_awhp_physical_response_authority(*, requested_use: str) -> AuthorityDecision:
    """Bind P74 to the existing B06 -> B05 transition-derived response chain.

    B06-P65 supplies record/project post-retrofit design-temperature authority;
    B06 Q-B06-007/008 are resolved method authorities; B05 consumes the
    resulting design point for product capacity/COP.  What remains open at
    national scale is materialization/coverage, not a missing generic external
    percentage response authority.
    """

    if requested_use == "RECORD_OR_PROJECT_PHYSICAL_RESPONSE_METHOD":
        return AuthorityDecision(QUALIFIED_TRANSITION_DERIVED_RESPONSE_METHOD, ())
    if requested_use == "NATIONAL_PERCENT_SAVING_DEFAULT":
        return AuthorityDecision(
            Q,
            ("GENERIC_AWHP_PERCENT_RESPONSE_IS_NOT_CANONICAL_ESTIMAND",),
        )
    if requested_use == "NATIONAL_PROGRAMME_RESPONSE":
        return AuthorityDecision(
            Q,
            (
                "NATIONAL_TRANSITION_RESPONSE_MATERIALIZATION_BY_ARCHETYPE_REQUIRED",
                "B05_PRODUCT_OPERATING_POINT_COVERAGE_REQUIRED",
            ),
        )
    return AuthorityDecision(Q, ("UNSUPPORTED_AWHP_RESPONSE_USE",))


def assess_p74_path_outcome_completeness(metric: str) -> AuthorityDecision:
    """Expose the remaining claim-specific blockers after P74."""

    if metric == "TECHNICAL_ACTION_FAMILY":
        return AuthorityDecision(
            Q,
            (
                "REUSE_FAMILY_HOUSE_OR_FULL_NATIONAL_SCOPE_ACTION_AUTHORITY_REQUIRED",
                "NONREUSE_PACKAGE_TO_PATH_SCOPE_CROSSWALK_REQUIRED",
            ),
        )
    if metric == "CAPEX_HUF_PER_SET":
        return AuthorityDecision(
            Q,
            (
                "REUSE_PATH_CAPEX_BOUND_REQUIRED",
                "NONREUSE_KEHOP_SCOPE_CROSSWALK_REQUIRED",
            ),
        )
    if metric == "AWHP_ENERGY_SAVING_SHARE":
        return AuthorityDecision(
            Q,
            ("GENERIC_AWHP_PERCENT_RESPONSE_IS_NOT_CANONICAL_ESTIMAND",),
        )
    if metric == "AWHP_PHYSICAL_RESPONSE":
        return AuthorityDecision(
            Q,
            (
                "NATIONAL_TRANSITION_RESPONSE_MATERIALIZATION_BY_ARCHETYPE_REQUIRED",
                "B05_PRODUCT_OPERATING_POINT_COVERAGE_REQUIRED",
            ),
        )
    if metric == "AWHP_DESIGN_TEMPERATURE":
        return AuthorityDecision(
            Q,
            ("NATIONAL_TRANSITION_RESPONSE_MATERIALIZATION_BY_ARCHETYPE_REQUIRED",),
        )
    return AuthorityDecision(Q, ("UNSUPPORTED_PATH_OUTCOME_METRIC",))
