"""B02-P105 EKR 1103 technical-cohort discovery gate.

P104 qualified verified EKR action type 1103 as a record-level window
compliance route, but left:
EKR_1103_TECHNICAL_COHORT_AGGREGATE_REQUIRED.

P105 audits whether the current public MEKH/HEM surface can enumerate that
cohort. The answer is fail-closed:

- known HEM identifiers can be looked up publicly;
- the public summary exposes all-HEM totals;
- the handbook exposes a public "Megtakarítás típusa" label, but separately
  defines HEM/saving type and Intézkedés típusa, so the public label is not
  silently promoted to action code 1103;
- the administrative submission schema contains measure name/type and
  technical context;
- historical official market monitoring proves coded measure-level
  aggregation from registry/admin data was technically possible;
- no current public 1103 enumeration/filter/export or technical-U cohort was
  identified.

Therefore the generic aggregate blocker narrows to an exact acquisition/access
residual:
MEKH_EKR_1103_ADMIN_EXTRACT_OR_PUBLISHED_AGGREGATE_REQUIRED.

Critical boundaries:

PUBLIC_SAVING_TYPE != PROVEN_MEASURE_CODE
KNOWN_HEM_ID_LOOKUP != COHORT_ENUMERATION
GLOBAL_HEM_COUNT != EKR_1103_COUNT
CEEGEX_MARKET_PRODUCT != MEASURE_CODE_1103
HISTORICAL_CODE_AGGREGATION != CURRENT_1103_AGGREGATE
ADMIN_SCHEMA_CAPABILITY != PUBLIC_DATA_AVAILABILITY
EKR_1103_COHORT != ALL_REPLACED_WINDOW_STOCK
"""

from __future__ import annotations

from dataclasses import dataclass

from modules.B02.ekr_verified_window_compliance import (
    EKR_WINDOW_ACTION_TYPE,
    P102_HP_ONLY_UPPER,
    P102_STRUCTURAL_CALIBRATED_RETROFIT_FLOOR,
)


P105_STATUS = "QUALIFIED_EKR_1103_ADMIN_AGGREGATION_CAPABILITY_PUBLIC_ACCESS_BOUNDARY"

SUPERSEDED_SUB_BLOCKER = "EKR_1103_TECHNICAL_COHORT_AGGREGATE_REQUIRED"
PRIMARY_NEXT_RESIDUAL = "MEKH_EKR_1103_ADMIN_EXTRACT_OR_PUBLISHED_AGGREGATE_REQUIRED"
POST_EXTRACT_RESIDUAL = "EKR_1103_COHORT_POPULATION_BINDING_REQUIRED"
NON_EKR_RESIDUAL = "NON_EKR_REPLACED_WINDOW_UW_DISTRIBUTION_REQUIRED"
COVERAGE_RESIDUAL = "FULL_DWELLING_WINDOW_COVERAGE_OR_REMAINING_STATE_REQUIRED"
OVERALL_WINDOW_RESIDUAL = "CURRENT_REPLACED_WINDOW_COMPLIANCE_POPULATION_SURFACE_REQUIRED"
WALL_SECONDARY_RESIDUAL = "MISSING_HISTORICAL_RENOVATED_WALL_U_TIGHTENING_REQUIRED"

HISTORICAL_ACCEPTED_PROJECTS = 541
HISTORICAL_ENTITLEMENTS = 597
HISTORICAL_MEASURE_CATEGORIES = 39
HISTORICAL_BUILDING_STRUCTURE_SAVING_GJ = 620.0


@dataclass(frozen=True)
class PublicHemDiscoverySurface:
    known_identifier_required: bool
    public_saving_type_label_available: bool
    public_saving_type_is_proven_measure_code: bool
    public_global_hem_count_available: bool
    public_measure_code_filter_proven: bool
    public_bulk_enumeration_proven: bool
    public_technical_u_available: bool
    status: str
    residual: str


@dataclass(frozen=True)
class AdminAggregationCapability:
    administrative_measure_type_available: bool
    administrative_technical_context_available: bool
    historical_measure_category_count: int
    historical_code_level_aggregation_proven: bool
    current_1103_extract_available: bool
    status: str
    residual: str


@dataclass(frozen=True)
class Ekr1103CohortCandidate:
    reference_period_current: bool
    exact_measure_code_1103: bool
    cohort_enumeration_complete_for_declared_scope: bool
    source_population_scope_declared: bool
    technical_u_coverage_declared: bool
    full_window_coverage_field_declared: bool


@dataclass(frozen=True)
class Ekr1103CohortAdmission:
    admitted: bool
    status: str
    blockers: tuple[str, ...]
    warnings: tuple[str, ...]


def public_hem_discovery_surface() -> PublicHemDiscoverySurface:
    return PublicHemDiscoverySurface(
        known_identifier_required=True,
        public_saving_type_label_available=True,
        public_saving_type_is_proven_measure_code=False,
        public_global_hem_count_available=True,
        public_measure_code_filter_proven=False,
        public_bulk_enumeration_proven=False,
        public_technical_u_available=False,
        status="QUALIFIED_IDENTIFIER_BOUND_PUBLIC_SURFACE",
        residual=PRIMARY_NEXT_RESIDUAL,
    )


def admin_aggregation_capability() -> AdminAggregationCapability:
    return AdminAggregationCapability(
        administrative_measure_type_available=True,
        administrative_technical_context_available=True,
        historical_measure_category_count=HISTORICAL_MEASURE_CATEGORIES,
        historical_code_level_aggregation_proven=True,
        current_1103_extract_available=False,
        status="QUALIFIED_ADMIN_AGGREGATION_CAPABILITY_NO_CURRENT_EXTRACT",
        residual=PRIMARY_NEXT_RESIDUAL,
    )


def admit_ekr1103_cohort(
    candidate: Ekr1103CohortCandidate,
) -> Ekr1103CohortAdmission:
    """Fail-closed admission for a future current EKR 1103 cohort extract.

    P105 does not require technical-U/full-window coverage merely to admit a
    current *counted 1103 cohort*. Those fields remain downstream performance
    and whole-dwelling gates. It does require exact code identity, current
    period, complete enumeration for a declared source scope, and explicit
    population scope.
    """

    blockers: list[str] = []
    warnings: list[str] = []

    if not candidate.reference_period_current:
        blockers.append("CURRENT_REFERENCE_PERIOD_REQUIRED")
    if not candidate.exact_measure_code_1103:
        blockers.append("EXACT_MEASURE_CODE_1103_REQUIRED")
    if not candidate.cohort_enumeration_complete_for_declared_scope:
        blockers.append("COMPLETE_1103_ENUMERATION_FOR_DECLARED_SCOPE_REQUIRED")
    if not candidate.source_population_scope_declared:
        blockers.append("SOURCE_POPULATION_SCOPE_REQUIRED")

    if not candidate.technical_u_coverage_declared:
        warnings.append("TECHNICAL_U_COVERAGE_REMAINS_REQUIRED_FOR_COMPLIANCE_DISTRIBUTION")
    if not candidate.full_window_coverage_field_declared:
        warnings.append(
            "FULL_WINDOW_COVERAGE_REMAINS_REQUIRED_FOR_WHOLE_DWELLING_PROMOTION"
        )

    if blockers:
        return Ekr1103CohortAdmission(
            admitted=False,
            status="REJECTED_FAIL_CLOSED_1103_COHORT",
            blockers=tuple(blockers),
            warnings=tuple(warnings),
        )

    return Ekr1103CohortAdmission(
        admitted=True,
        status="QUALIFIED_CURRENT_1103_COHORT_FOR_POPULATION_BINDING",
        blockers=(),
        warnings=tuple(warnings),
    )


def p105_state() -> dict[str, object]:
    public = public_hem_discovery_surface()
    admin = admin_aggregation_capability()
    return {
        "status": P105_STATUS,
        "ekr_window_action_type": EKR_WINDOW_ACTION_TYPE,
        "superseded_sub_blocker": SUPERSEDED_SUB_BLOCKER,
        "primary_residual": PRIMARY_NEXT_RESIDUAL,
        "overall_window_residual": OVERALL_WINDOW_RESIDUAL,
        "post_extract_residual": POST_EXTRACT_RESIDUAL,
        "public_surface": public.__dict__,
        "admin_capability": admin.__dict__,
        "historical_accepted_projects": HISTORICAL_ACCEPTED_PROJECTS,
        "historical_entitlements": HISTORICAL_ENTITLEMENTS,
        "historical_measure_categories": HISTORICAL_MEASURE_CATEGORIES,
        "historical_building_structure_saving_gj": (
            HISTORICAL_BUILDING_STRUCTURE_SAVING_GJ
        ),
        "current_public_1103_count_identified": False,
        "current_public_1103_technical_u_distribution_identified": False,
        "p102_structural_calibrated_retrofit_floor_lower_share": (
            P102_STRUCTURAL_CALIBRATED_RETROFIT_FLOOR
        ),
        "hp_only_share_lower": 0.0,
        "hp_only_share_upper": P102_HP_ONLY_UPPER,
        "p105_numeric_national_action_tightening": False,
        "parallel_residuals": (
            NON_EKR_RESIDUAL,
            COVERAGE_RESIDUAL,
            WALL_SECONDARY_RESIDUAL,
        ),
    }


def semantic_boundaries() -> tuple[str, ...]:
    return (
        "PUBLIC_SAVING_TYPE_IS_NOT_PROVEN_MEASURE_CODE",
        "KNOWN_HEM_ID_LOOKUP_IS_NOT_COHORT_ENUMERATION",
        "GLOBAL_HEM_COUNT_IS_NOT_EKR_1103_COUNT",
        "CEEGEX_MARKET_PRODUCT_IS_NOT_MEASURE_CODE_1103",
        "HISTORICAL_CODE_AGGREGATION_IS_NOT_CURRENT_1103_AGGREGATE",
        "ADMIN_SCHEMA_CAPABILITY_IS_NOT_PUBLIC_DATA_AVAILABILITY",
        "EKR_1103_COHORT_IS_NOT_ALL_REPLACED_WINDOW_STOCK",
    )
