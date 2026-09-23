"""B02-P104 EKR verified window-compliance route.

P103 narrowed the public-data problem to:
CURRENT_REPLACED_WINDOW_REALIZED_UW_DISTRIBUTION_REQUIRED.

P104 shows that a direct national realized-Uw distribution is not the only
admissible closure route.

Current EKR window measures 1.2 / 1.4 / 1.6 (action type 1103) require the
affected opening to satisfy the current 9/2023 EKM U-value requirement. The
catalogue also records or requires documentary evidence for the new opening
type and U-value, while HEM verification establishes actual action
implementation and method compliance.

Therefore an EKR technical record can provide a record-level verified
specification/compliance route for affected openings.

However the public HEM registry exposes only generic registry fields and
aggregate all-HEM totals. It does not expose action type 1103, technical
parameters or an aggregate window-action cohort. P104 therefore does not mint
a national share.

Critical boundaries:

GENERIC_LEGAL_REQUIREMENT != VERIFIED_EKR_ACTION
VERIFIED_EKR_AFFECTED_OPENING != WHOLE_DWELLING_WINDOW_COMPLIANCE
PUBLIC_TOTAL_HEM_COUNT != EKR_1103_WINDOW_COUNT
ADMINISTRATIVE_TECHNICAL_FIELD != PUBLIC_POPULATION_SURFACE
EKR_WINDOW_ACTION != ALL_REPLACED_WINDOWS
EKR_COHORT != NON_EKR_REPLACED_WINDOW_STOCK
"""

from __future__ import annotations

from dataclasses import dataclass
from math import isfinite

from modules.B02.current_replaced_window_u_quality import (
    CURRENT_REFERENCE_WINDOW_U_MAX_W_M2K,
    P102_HP_ONLY_UPPER,
    P102_STRUCTURAL_CALIBRATED_RETROFIT_FLOOR,
)


EKR_WINDOW_MEASURE_CODES = ("1.2", "1.4", "1.6")
EKR_WINDOW_ACTION_TYPE = "1103"

P104_STATUS = "QUALIFIED_MULTI_ROUTE_WINDOW_COMPLIANCE_CONTRACT"

AFFECTED_OPENING_REFERENCE_SATISFIED = (
    "AFFECTED_OPENING_REFERENCE_SATISFIED_VERIFIED_EKR"
)
AFFECTED_OPENING_REFERENCE_DEFICIT = (
    "AFFECTED_OPENING_REFERENCE_DEFICIT_VERIFIED_EKR"
)
AFFECTED_OPENING_UNRESOLVED = "AFFECTED_OPENING_UNRESOLVED"
WHOLE_DWELLING_WINDOW_REFERENCE_SATISFIED = (
    "WHOLE_DWELLING_WINDOW_REFERENCE_SATISFIED"
)
WHOLE_DWELLING_WINDOW_UNRESOLVED = "WHOLE_DWELLING_WINDOW_UNRESOLVED"

PRIMARY_NEXT_RESIDUAL = "CURRENT_REPLACED_WINDOW_COMPLIANCE_POPULATION_SURFACE_REQUIRED"
EKR_COHORT_RESIDUAL = "EKR_1103_TECHNICAL_COHORT_AGGREGATE_REQUIRED"
NON_EKR_RESIDUAL = "NON_EKR_REPLACED_WINDOW_UW_DISTRIBUTION_REQUIRED"
COVERAGE_RESIDUAL = "FULL_DWELLING_WINDOW_COVERAGE_OR_REMAINING_STATE_REQUIRED"
WALL_SECONDARY_RESIDUAL = "MISSING_HISTORICAL_RENOVATED_WALL_U_TIGHTENING_REQUIRED"


@dataclass(frozen=True)
class EkrWindowActionAssessment:
    measure_code: str
    action_type: str
    hem_verified: bool
    technical_record_available: bool
    new_window_u_w_m2k: float | None
    affected_opening_state: str
    full_dwelling_window_coverage: bool | None
    remaining_windows_reference_satisfied: bool | None
    dwelling_window_state: str
    evidence_status: str
    blockers: tuple[str, ...]
    warnings: tuple[str, ...]


@dataclass(frozen=True)
class PublicHemSurface:
    public_generic_lookup_available: bool
    public_total_count_available: bool
    public_measure_type_available: bool
    public_technical_u_available: bool
    administrative_measure_type_available: bool
    administrative_technical_u_route_available: bool
    national_1103_count_identified: bool
    status: str
    residual: str


def assess_ekr_window_action(
    *,
    measure_code: str,
    hem_verified: bool,
    technical_record_available: bool,
    new_window_u_w_m2k: float | None,
    full_dwelling_window_coverage: bool | None = None,
    remaining_windows_reference_satisfied: bool | None = None,
    evidence_status: str = "POL/DER",
) -> EkrWindowActionAssessment:
    """Assess one current EKR window action against the P103 window target.

    An EKR label alone is not enough. The route requires:
    - a recognised current window measure;
    - HEM verification;
    - the technical record;
    - explicit new-opening U evidence for comparison with the programme target.

    Whole-dwelling window satisfaction additionally requires either full opening
    coverage or independently verified satisfaction of all remaining openings.
    """

    if measure_code not in EKR_WINDOW_MEASURE_CODES:
        raise ValueError(f"unsupported EKR window measure {measure_code}")

    blockers: list[str] = []
    warnings: list[str] = []

    if not hem_verified:
        blockers.append("HEM_VERIFICATION_REQUIRED")
    if not technical_record_available:
        blockers.append("EKR_TECHNICAL_RECORD_REQUIRED")

    value: float | None = None
    if new_window_u_w_m2k is not None:
        value = float(new_window_u_w_m2k)
        if not isfinite(value) or value <= 0.0:
            raise ValueError("new_window_u_w_m2k must be finite and positive")
    else:
        blockers.append("NEW_WINDOW_U_VALUE_REQUIRED_FROM_TECHNICAL_RECORD")

    if blockers:
        affected = AFFECTED_OPENING_UNRESOLVED
    elif value is not None and value <= CURRENT_REFERENCE_WINDOW_U_MAX_W_M2K:
        affected = AFFECTED_OPENING_REFERENCE_SATISFIED
    else:
        affected = AFFECTED_OPENING_REFERENCE_DEFICIT

    dwelling = WHOLE_DWELLING_WINDOW_UNRESOLVED

    if affected == AFFECTED_OPENING_REFERENCE_SATISFIED:
        if full_dwelling_window_coverage is True:
            dwelling = WHOLE_DWELLING_WINDOW_REFERENCE_SATISFIED
        elif remaining_windows_reference_satisfied is True:
            dwelling = WHOLE_DWELLING_WINDOW_REFERENCE_SATISFIED
        else:
            blockers.append(COVERAGE_RESIDUAL)
            warnings.append(
                "VERIFIED_EKR_AFFECTED_OPENING_IS_NOT_WHOLE_DWELLING_WINDOW_COMPLIANCE"
            )
    elif affected == AFFECTED_OPENING_REFERENCE_DEFICIT:
        warnings.append(
            "VERIFIED_EKR_ACTION_CAN_STILL_BE_ABOVE_PROGRAMME_1_10_TARGET_FOR_SOME_OPENING_CLASSES"
        )

    return EkrWindowActionAssessment(
        measure_code=measure_code,
        action_type=EKR_WINDOW_ACTION_TYPE,
        hem_verified=hem_verified,
        technical_record_available=technical_record_available,
        new_window_u_w_m2k=value,
        affected_opening_state=affected,
        full_dwelling_window_coverage=full_dwelling_window_coverage,
        remaining_windows_reference_satisfied=remaining_windows_reference_satisfied,
        dwelling_window_state=dwelling,
        evidence_status=evidence_status,
        blockers=tuple(dict.fromkeys(blockers)),
        warnings=tuple(dict.fromkeys(warnings)),
    )


def public_hem_surface() -> PublicHemSurface:
    return PublicHemSurface(
        public_generic_lookup_available=True,
        public_total_count_available=True,
        public_measure_type_available=False,
        public_technical_u_available=False,
        administrative_measure_type_available=True,
        administrative_technical_u_route_available=True,
        national_1103_count_identified=False,
        status="QUALIFIED_PUBLICATION_BOUNDARY_WITH_ADMINISTRATIVE_ROUTE",
        residual=EKR_COHORT_RESIDUAL,
    )


def p104_state() -> dict[str, object]:
    surface = public_hem_surface()
    return {
        "status": P104_STATUS,
        "superseded_primary_residual": (
            "CURRENT_REPLACED_WINDOW_REALIZED_UW_DISTRIBUTION_REQUIRED"
        ),
        "primary_residual": PRIMARY_NEXT_RESIDUAL,
        "admissible_closure_routes": (
            "DIRECT_REPRESENTATIVE_OR_CALIBRATED_REPLACED_WINDOW_UW",
            "EKR_1103_VERIFIED_TECHNICAL_RECORD_COHORT",
        ),
        "ekr_window_measure_codes": EKR_WINDOW_MEASURE_CODES,
        "ekr_window_action_type": EKR_WINDOW_ACTION_TYPE,
        "public_hem_surface": surface.__dict__,
        "ekr_record_level_affected_opening_route_qualified": True,
        "ekr_whole_dwelling_route_requires_coverage": True,
        "public_national_ekr_1103_technical_cohort_identified": False,
        "non_ekr_replaced_window_population_surface_identified": False,
        "national_replaced_window_compliance_share_identified": False,
        "p102_structural_calibrated_retrofit_floor_lower_share": (
            P102_STRUCTURAL_CALIBRATED_RETROFIT_FLOOR
        ),
        "hp_only_share_lower": 0.0,
        "hp_only_share_upper": P102_HP_ONLY_UPPER,
        "p104_numeric_national_action_tightening": False,
        "sub_residuals": (
            EKR_COHORT_RESIDUAL,
            NON_EKR_RESIDUAL,
            COVERAGE_RESIDUAL,
            WALL_SECONDARY_RESIDUAL,
        ),
    }


def semantic_boundaries() -> tuple[str, ...]:
    return (
        "GENERIC_LEGAL_REQUIREMENT_IS_NOT_VERIFIED_EKR_ACTION",
        "VERIFIED_EKR_AFFECTED_OPENING_IS_NOT_WHOLE_DWELLING_WINDOW_COMPLIANCE",
        "PUBLIC_TOTAL_HEM_COUNT_IS_NOT_EKR_1103_WINDOW_COUNT",
        "ADMINISTRATIVE_TECHNICAL_FIELD_IS_NOT_PUBLIC_POPULATION_SURFACE",
        "EKR_WINDOW_ACTION_IS_NOT_ALL_REPLACED_WINDOWS",
        "EKR_COHORT_IS_NOT_NON_EKR_REPLACED_WINDOW_STOCK",
    )
