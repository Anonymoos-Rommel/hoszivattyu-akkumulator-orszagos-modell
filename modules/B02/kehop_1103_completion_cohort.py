"""B02-P109 KEHOP completed-window technical cohort schema.

P108 resolved the generic component-specific record bridge and left:
KEHOP_COMPLETED_WINDOW_PROJECT_TECHNICAL_COHORT_REQUIRED.

P109 proves that the current KEHOP Plusz 4.1.7-24 and 4.1.8-24 calls already
require a project-level physical-completion indicator:

    Energiahatékonysági intézkedés kategória

reported from the MEKH category list.

Under the current 18/2025 EM taxonomy:

    1103 = Épületszerkezetek - Felújítás - Nyílászáró cseréje

Therefore completed KEHOP window projects are administratively enumerable from
completion indicators by exact measure category 1103, provided an extract is
available.

This does NOT itself provide component U values. Technical performance still
requires the P108 same-project join to final HET/final energy calculation or the
installed-product DoP route.

This also does NOT prove EKR/HEM participation. The KEHOP call permits HEM
compensation through an optional written HEM-generation agreement. Therefore:

MEKH_MEASURE_CATEGORY_1103 != REGISTERED_HEM_1103

Explicit HEM agreement/HEM-ID binding is required to classify EKR overlap.

Critical boundaries:

COMPLETION_INDICATOR_1103 != TECHNICAL_U_DISTRIBUTION
RCO18_HOUSEHOLD_COUNT != WINDOW_1103_COHORT
MEKH_CATEGORY_1103 != REGISTERED_HEM_1103
PUBLIC_PROGRAMME_STATUS != COMPLETED_PROJECT_ENUMERATION
ADMINISTRATIVELY_ENUMERABLE != PUBLICLY_AVAILABLE
CONVENIENCE_SAMPLE != COMPLETE_DECLARED_SCOPE_COHORT
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from modules.B02.ekr_verified_window_compliance import (
    P102_HP_ONLY_UPPER,
    P102_STRUCTURAL_CALIBRATED_RETROFIT_FLOOR,
)


P109_STATUS = "QUALIFIED_KEHOP_COMPLETION_INDICATOR_1103_COHORT_SCHEMA"

PROGRAMMES = (
    "KEHOP_PLUSZ_4_1_7_24",
    "KEHOP_PLUSZ_4_1_8_24",
)
WINDOW_MEASURE_CATEGORY = "1103"

SUPERSEDED_BLOCKER = "KEHOP_COMPLETED_WINDOW_PROJECT_TECHNICAL_COHORT_REQUIRED"
PRIMARY_NEXT_RESIDUAL = "MFB_KEHOP_COMPLETION_INDICATOR_1103_EXTRACT_REQUIRED"
TECHNICAL_JOIN_RESIDUAL = "KEHOP_1103_FINAL_TECHNICAL_DOCUMENT_JOIN_REQUIRED"
EKR_OVERLAP_RESIDUAL = "KEHOP_EKR1103_OVERLAP_OR_HEM_ATTRIBUTION_REQUIRED"
OVERALL_WINDOW_RESIDUAL = "CURRENT_REPLACED_WINDOW_COMPLIANCE_POPULATION_SURFACE_REQUIRED"
DIRECT_OBS_RESIDUAL = "REPRESENTATIVE_HUNGARIAN_REPLACED_WINDOW_UW_DISTRIBUTION_REQUIRED"
MEKH_EKR_RESIDUAL = "MEKH_EKR_1103_ADMIN_EXTRACT_OR_PUBLISHED_AGGREGATE_REQUIRED"
WALL_SECONDARY_RESIDUAL = "MISSING_HISTORICAL_RENOVATED_WALL_U_TIGHTENING_REQUIRED"


@dataclass(frozen=True)
class KehopCompletionIndicatorRecord:
    project_id: str
    programme_code: str
    physical_completion_date: str
    measure_category_codes: tuple[str, ...]
    final_het_ref: str = ""
    final_energy_calculation_ref: str = ""
    installed_product_or_dop_refs: tuple[str, ...] = ()
    hem_generation_agreement_ref: str = ""
    hem_id: str = ""


@dataclass(frozen=True)
class CompletionIndicatorDecision:
    admitted_to_1103_cohort: bool
    status: str
    blockers: tuple[str, ...]
    warnings: tuple[str, ...]


@dataclass(frozen=True)
class Kehop1103ExtractCandidate:
    records: tuple[KehopCompletionIndicatorRecord, ...]
    declared_programmes: tuple[str, ...]
    reference_cutoff_date: str
    enumeration_complete_for_declared_scope: bool
    source_scope_description: str


@dataclass(frozen=True)
class Kehop1103ExtractDecision:
    admitted: bool
    status: str
    unique_project_count: int
    blockers: tuple[str, ...]
    warnings: tuple[str, ...]


def _valid_iso_date(value: str) -> bool:
    try:
        date.fromisoformat(value)
        return True
    except (ValueError, TypeError):
        return False


def assess_completion_indicator_record(
    record: KehopCompletionIndicatorRecord,
) -> CompletionIndicatorDecision:
    blockers: list[str] = []
    warnings: list[str] = []

    if not record.project_id.strip():
        blockers.append("PROJECT_ID_REQUIRED")
    if record.programme_code not in PROGRAMMES:
        blockers.append("SUPPORTED_KEHOP_PROGRAMME_REQUIRED")
    if not _valid_iso_date(record.physical_completion_date):
        blockers.append("VALID_PHYSICAL_COMPLETION_DATE_REQUIRED")
    if WINDOW_MEASURE_CATEGORY not in set(record.measure_category_codes):
        blockers.append("MEKH_MEASURE_CATEGORY_1103_REQUIRED")

    if not record.final_het_ref.strip():
        warnings.append("FINAL_HET_JOIN_REMAINS_REQUIRED_FOR_TECHNICAL_COHORT")
    if (
        not record.final_energy_calculation_ref.strip()
        and not record.installed_product_or_dop_refs
    ):
        warnings.append("P108_COMPONENT_PERFORMANCE_JOIN_REMAINS_REQUIRED")

    hem_bound = bool(
        record.hem_generation_agreement_ref.strip()
        or record.hem_id.strip()
    )
    if not hem_bound:
        warnings.append("EKR_HEM_OVERLAP_UNCLASSIFIED")

    if blockers:
        return CompletionIndicatorDecision(
            admitted_to_1103_cohort=False,
            status="REJECTED_FAIL_CLOSED_COMPLETION_INDICATOR_RECORD",
            blockers=tuple(blockers),
            warnings=tuple(warnings),
        )

    return CompletionIndicatorDecision(
        admitted_to_1103_cohort=True,
        status="QUALIFIED_COMPLETED_KEHOP_1103_PROJECT_RECORD",
        blockers=(),
        warnings=tuple(warnings),
    )


def assess_kehop_1103_extract(
    candidate: Kehop1103ExtractCandidate,
) -> Kehop1103ExtractDecision:
    blockers: list[str] = []
    warnings: list[str] = []

    if not candidate.declared_programmes:
        blockers.append("DECLARED_PROGRAMME_SCOPE_REQUIRED")
    elif any(p not in PROGRAMMES for p in candidate.declared_programmes):
        blockers.append("UNSUPPORTED_PROGRAMME_IN_DECLARED_SCOPE")

    if not _valid_iso_date(candidate.reference_cutoff_date):
        blockers.append("VALID_REFERENCE_CUTOFF_DATE_REQUIRED")
    if not candidate.source_scope_description.strip():
        blockers.append("SOURCE_SCOPE_DESCRIPTION_REQUIRED")
    if not candidate.enumeration_complete_for_declared_scope:
        blockers.append("COMPLETE_ENUMERATION_FOR_DECLARED_SCOPE_REQUIRED")

    project_ids: list[str] = []
    for record in candidate.records:
        decision = assess_completion_indicator_record(record)
        if not decision.admitted_to_1103_cohort:
            blockers.append(f"INVALID_RECORD:{record.project_id or '<missing>'}")
        if record.programme_code not in set(candidate.declared_programmes):
            blockers.append(
                f"RECORD_OUTSIDE_DECLARED_PROGRAMME_SCOPE:{record.project_id}"
            )
        if record.project_id.strip():
            project_ids.append(record.project_id.strip())

    duplicates = sorted(
        project_id
        for project_id in set(project_ids)
        if project_ids.count(project_id) > 1
    )
    if duplicates:
        blockers.append("DUPLICATE_PROJECT_IDS_IN_EXTRACT")

    if not candidate.records:
        warnings.append("ZERO_1103_RECORDS_IN_DECLARED_SCOPE")

    if blockers:
        return Kehop1103ExtractDecision(
            admitted=False,
            status="REJECTED_FAIL_CLOSED_KEHOP_1103_EXTRACT",
            unique_project_count=len(set(project_ids)),
            blockers=tuple(dict.fromkeys(blockers)),
            warnings=tuple(dict.fromkeys(warnings)),
        )

    return Kehop1103ExtractDecision(
        admitted=True,
        status="QUALIFIED_COMPLETE_KEHOP_1103_COMPLETION_INDICATOR_EXTRACT",
        unique_project_count=len(set(project_ids)),
        blockers=(),
        warnings=tuple(dict.fromkeys(warnings)),
    )


def classify_ekr_overlap(
    record: KehopCompletionIndicatorRecord,
) -> str:
    """Classify only explicit project-level HEM/EKR binding.

    Measure category 1103 is insufficient because it is an intervention
    taxonomy also used by KEHOP completion reporting.
    """

    if record.hem_id.strip():
        return "EXPLICIT_HEM_ID_BOUND"
    if record.hem_generation_agreement_ref.strip():
        return "HEM_GENERATION_AGREEMENT_PRESENT_PENDING_HEM_ID"
    return "EKR_HEM_OVERLAP_UNCLASSIFIED"


def p109_state() -> dict[str, object]:
    return {
        "status": P109_STATUS,
        "superseded_blocker": SUPERSEDED_BLOCKER,
        "primary_residual": PRIMARY_NEXT_RESIDUAL,
        "technical_join_residual": TECHNICAL_JOIN_RESIDUAL,
        "ekr_overlap_residual": EKR_OVERLAP_RESIDUAL,
        "overall_window_residual": OVERALL_WINDOW_RESIDUAL,
        "programmes": PROGRAMMES,
        "window_measure_category": WINDOW_MEASURE_CATEGORY,
        "completion_indicator_1103_admin_field_proven": True,
        "nationwide_programme_geography_covered_by_417_plus_418": True,
        "public_1103_completion_extract_identified": False,
        "public_completed_window_technical_cohort_identified": False,
        "measure_category_1103_proves_registered_hem": False,
        "p102_structural_calibrated_retrofit_floor_lower_share": (
            P102_STRUCTURAL_CALIBRATED_RETROFIT_FLOOR
        ),
        "hp_only_share_lower": 0.0,
        "hp_only_share_upper": P102_HP_ONLY_UPPER,
        "p109_numeric_national_action_tightening": False,
        "parallel_residuals": (
            DIRECT_OBS_RESIDUAL,
            MEKH_EKR_RESIDUAL,
            WALL_SECONDARY_RESIDUAL,
        ),
    }


def semantic_boundaries() -> tuple[str, ...]:
    return (
        "COMPLETION_INDICATOR_1103_IS_NOT_TECHNICAL_U_DISTRIBUTION",
        "RCO18_HOUSEHOLD_COUNT_IS_NOT_WINDOW_1103_COHORT",
        "MEKH_CATEGORY_1103_IS_NOT_REGISTERED_HEM_1103",
        "PUBLIC_PROGRAMME_STATUS_IS_NOT_COMPLETED_PROJECT_ENUMERATION",
        "ADMINISTRATIVELY_ENUMERABLE_IS_NOT_PUBLICLY_AVAILABLE",
        "CONVENIENCE_SAMPLE_IS_NOT_COMPLETE_DECLARED_SCOPE_COHORT",
    )
