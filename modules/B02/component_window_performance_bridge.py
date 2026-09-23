"""B02-P108 component-specific window replacement performance bridge.

P107 resolved the numeric Invert extract but rejected whole-building renovation
generation as a proxy for component-specific window replacement. The exact
residual became:

    COMPONENT_SPECIFIC_WINDOW_REPLACEMENT_PERFORMANCE_BRIDGE_REQUIRED

P108 qualifies a Hungarian record-level bridge through the current KEHOP Plusz
Otthonfelujitasi Program completion chain already admitted by B06-P64.

A qualified completed project can bind:

    realized window-replacement scope
    + final invoice / performance confirmation
    + final HET
    + final detailed energy calculation

to the same record, intervention, project and site.

Two component-performance paths are admitted:

1. the final energy calculation contains explicit post-state U values that are
   explicitly linked to the replaced-window scope; or
2. exact installed window-product references are linked to the final invoice
   and realized window scope, and the linked performance declaration supplies
   the window U value.

This resolves the generic record-level bridge. It does not create a public
completed-project technical cohort, national population share, EKR/non-EKR
split, or whole-dwelling window compliance without coverage evidence.

Critical boundaries:

PROGRAMME_WINDOW_ELIGIBILITY != REALIZED_WINDOW_REPLACEMENT
FINAL_HET_ONLY != REALIZED_WINDOW_SCOPE
PRODUCT_CATALOGUE_ENTRY != INSTALLED_PRODUCT
SAME_PROJECT_DOCUMENT_SET != AUTOMATIC_COMPONENT_LINK
REPLACED_OPENING_COMPLIANCE != WHOLE_DWELLING_WINDOW_COMPLIANCE
KEHOP_COMPLETED_PROJECT != NON_EKR_PROJECT
RECORD_LEVEL_BRIDGE != NATIONAL_POPULATION_SURFACE
"""

from __future__ import annotations

from dataclasses import dataclass
from math import isfinite

from modules.B02.current_replaced_window_u_quality import (
    CURRENT_REFERENCE_WINDOW_U_MAX_W_M2K,
    P102_HP_ONLY_UPPER,
    P102_STRUCTURAL_CALIBRATED_RETROFIT_FLOOR,
)
from modules.B06.realized_completion_gate import (
    QUALIFIED,
    RealizedCompletionEvidence,
    assess_realized_completion,
)


P108_STATUS = "QUALIFIED_KEHOP_COMPONENT_SPECIFIC_WINDOW_RECORD_BRIDGE"

RESOLVED_BLOCKER = "COMPONENT_SPECIFIC_WINDOW_REPLACEMENT_PERFORMANCE_BRIDGE_REQUIRED"
PRIMARY_NEXT_RESIDUAL = "KEHOP_COMPLETED_WINDOW_PROJECT_TECHNICAL_COHORT_REQUIRED"
EKR_OVERLAP_RESIDUAL = "KEHOP_EKR1103_OVERLAP_OR_HEM_ATTRIBUTION_REQUIRED"
COVERAGE_RESIDUAL = "FULL_DWELLING_WINDOW_COVERAGE_OR_REMAINING_STATE_REQUIRED"
DIRECT_OBS_RESIDUAL = "REPRESENTATIVE_HUNGARIAN_REPLACED_WINDOW_UW_DISTRIBUTION_REQUIRED"
MEKH_RESIDUAL = "MEKH_EKR_1103_ADMIN_EXTRACT_OR_PUBLISHED_AGGREGATE_REQUIRED"
OVERALL_WINDOW_RESIDUAL = "CURRENT_REPLACED_WINDOW_COMPLIANCE_POPULATION_SURFACE_REQUIRED"
WALL_SECONDARY_RESIDUAL = "MISSING_HISTORICAL_RENOVATED_WALL_U_TIGHTENING_REQUIRED"

AFFECTED_OPENING_REFERENCE_SATISFIED = (
    "AFFECTED_OPENING_REFERENCE_SATISFIED_VERIFIED_KEHOP"
)
AFFECTED_OPENING_REFERENCE_DEFICIT = (
    "AFFECTED_OPENING_REFERENCE_DEFICIT_VERIFIED_KEHOP"
)
AFFECTED_OPENING_UNRESOLVED = "AFFECTED_OPENING_UNRESOLVED"
WHOLE_DWELLING_WINDOW_REFERENCE_SATISFIED = (
    "WHOLE_DWELLING_WINDOW_REFERENCE_SATISFIED"
)
WHOLE_DWELLING_WINDOW_UNRESOLVED = "WHOLE_DWELLING_WINDOW_UNRESOLVED"

FINAL_CALC_PATH = "FINAL_ENERGY_CALCULATION_REPLACED_WINDOW_U"
PRODUCT_DOP_PATH = "INSTALLED_PRODUCT_PERFORMANCE_DECLARATION"


@dataclass(frozen=True)
class KehopWindowPerformanceCandidate:
    completion: RealizedCompletionEvidence
    window_scope_ids: tuple[str, ...]

    final_calc_replaced_window_u_values_w_m2k: tuple[float, ...] = ()
    final_calc_values_explicitly_linked_to_window_scope: bool = False

    installed_product_refs: tuple[str, ...] = ()
    installed_product_u_values_w_m2k: tuple[float, ...] = ()
    installed_product_refs_linked_to_final_invoice_and_window_scope: bool = False

    full_dwelling_window_coverage: bool | None = None
    remaining_windows_reference_satisfied: bool | None = None


@dataclass(frozen=True)
class KehopWindowPerformanceAssessment:
    status: str
    evidence_status: str
    performance_path: str | None
    admitted_u_values_w_m2k: tuple[float, ...]
    affected_opening_state: str
    dwelling_window_state: str
    blockers: tuple[str, ...]
    warnings: tuple[str, ...]


def _validate_u_values(values: tuple[float, ...], name: str) -> tuple[float, ...]:
    checked: list[float] = []
    for raw in values:
        value = float(raw)
        if not isfinite(value) or value <= 0.0:
            raise ValueError(f"{name} values must be finite and positive")
        checked.append(value)
    return tuple(checked)


def _refs_ok(refs: tuple[str, ...]) -> bool:
    return bool(refs) and all(isinstance(ref, str) and ref.strip() for ref in refs)


def assess_kehop_window_performance(
    candidate: KehopWindowPerformanceCandidate,
) -> KehopWindowPerformanceAssessment:
    blockers: list[str] = []
    warnings: list[str] = []

    completion = assess_realized_completion(candidate.completion)
    if completion.status != QUALIFIED:
        blockers.append("QUALIFIED_REALIZED_COMPLETION_REQUIRED")
        blockers.extend(f"COMPLETION:{reason}" for reason in completion.reasons)

    if not candidate.window_scope_ids:
        blockers.append("WINDOW_SCOPE_IDS_REQUIRED")
    else:
        realized_scope = set(candidate.completion.realized_scope_ids)
        missing = [scope for scope in candidate.window_scope_ids if scope not in realized_scope]
        if missing:
            blockers.append("WINDOW_SCOPE_NOT_PRESENT_IN_REALIZED_SCOPE")

    final_values = _validate_u_values(
        candidate.final_calc_replaced_window_u_values_w_m2k,
        "final_calc_replaced_window_u_values_w_m2k",
    )
    product_values = _validate_u_values(
        candidate.installed_product_u_values_w_m2k,
        "installed_product_u_values_w_m2k",
    )

    performance_path: str | None = None
    admitted_values: tuple[float, ...] = ()

    if (
        final_values
        and candidate.final_calc_values_explicitly_linked_to_window_scope
    ):
        performance_path = FINAL_CALC_PATH
        admitted_values = final_values
    elif (
        product_values
        and _refs_ok(candidate.installed_product_refs)
        and len(candidate.installed_product_refs) == len(product_values)
        and candidate.installed_product_refs_linked_to_final_invoice_and_window_scope
    ):
        performance_path = PRODUCT_DOP_PATH
        admitted_values = product_values
    else:
        if final_values and not candidate.final_calc_values_explicitly_linked_to_window_scope:
            blockers.append("FINAL_CALC_U_VALUES_NOT_LINKED_TO_REPLACED_WINDOW_SCOPE")
        if product_values:
            if not _refs_ok(candidate.installed_product_refs):
                blockers.append("INSTALLED_PRODUCT_REFS_REQUIRED")
            elif len(candidate.installed_product_refs) != len(product_values):
                blockers.append("INSTALLED_PRODUCT_REF_U_VALUE_CARDINALITY_MISMATCH")
            if not candidate.installed_product_refs_linked_to_final_invoice_and_window_scope:
                blockers.append("INSTALLED_PRODUCT_NOT_LINKED_TO_FINAL_INVOICE_AND_WINDOW_SCOPE")
        if not final_values and not product_values:
            blockers.append("COMPONENT_SPECIFIC_WINDOW_PERFORMANCE_EVIDENCE_REQUIRED")

    if blockers:
        affected = AFFECTED_OPENING_UNRESOLVED
    elif all(
        value <= CURRENT_REFERENCE_WINDOW_U_MAX_W_M2K
        for value in admitted_values
    ):
        affected = AFFECTED_OPENING_REFERENCE_SATISFIED
    else:
        affected = AFFECTED_OPENING_REFERENCE_DEFICIT

    dwelling = WHOLE_DWELLING_WINDOW_UNRESOLVED
    if affected == AFFECTED_OPENING_REFERENCE_SATISFIED:
        if candidate.full_dwelling_window_coverage is True:
            dwelling = WHOLE_DWELLING_WINDOW_REFERENCE_SATISFIED
        elif candidate.remaining_windows_reference_satisfied is True:
            dwelling = WHOLE_DWELLING_WINDOW_REFERENCE_SATISFIED
        else:
            blockers.append(COVERAGE_RESIDUAL)
            warnings.append(
                "VERIFIED_REPLACED_OPENINGS_ARE_NOT_WHOLE_DWELLING_WINDOW_COMPLIANCE"
            )

    if blockers:
        return KehopWindowPerformanceAssessment(
            status="Q_COMPONENT_SPECIFIC_WINDOW_RECORD",
            evidence_status="OBS/DER",
            performance_path=performance_path,
            admitted_u_values_w_m2k=admitted_values,
            affected_opening_state=affected,
            dwelling_window_state=dwelling,
            blockers=tuple(dict.fromkeys(blockers)),
            warnings=tuple(dict.fromkeys(warnings)),
        )

    return KehopWindowPerformanceAssessment(
        status="QUALIFIED_COMPONENT_SPECIFIC_WINDOW_RECORD",
        evidence_status="OBS/DER",
        performance_path=performance_path,
        admitted_u_values_w_m2k=admitted_values,
        affected_opening_state=affected,
        dwelling_window_state=dwelling,
        blockers=(),
        warnings=tuple(dict.fromkeys(warnings)),
    )


def p108_state() -> dict[str, object]:
    return {
        "status": P108_STATUS,
        "resolved_blocker": RESOLVED_BLOCKER,
        "primary_residual": PRIMARY_NEXT_RESIDUAL,
        "overall_window_residual": OVERALL_WINDOW_RESIDUAL,
        "qualified_record_level_paths": (
            FINAL_CALC_PATH,
            PRODUCT_DOP_PATH,
        ),
        "kehop_completed_project_microdata_publicly_identified": False,
        "kehop_completed_window_technical_cohort_identified": False,
        "kehop_ekr_overlap_identified": False,
        "national_replaced_window_compliance_share_identified": False,
        "p102_structural_calibrated_retrofit_floor_lower_share": (
            P102_STRUCTURAL_CALIBRATED_RETROFIT_FLOOR
        ),
        "hp_only_share_lower": 0.0,
        "hp_only_share_upper": P102_HP_ONLY_UPPER,
        "p108_numeric_national_action_tightening": False,
        "residuals": (
            PRIMARY_NEXT_RESIDUAL,
            EKR_OVERLAP_RESIDUAL,
            COVERAGE_RESIDUAL,
            DIRECT_OBS_RESIDUAL,
            MEKH_RESIDUAL,
            WALL_SECONDARY_RESIDUAL,
        ),
    }


def semantic_boundaries() -> tuple[str, ...]:
    return (
        "PROGRAMME_WINDOW_ELIGIBILITY_IS_NOT_REALIZED_WINDOW_REPLACEMENT",
        "FINAL_HET_ONLY_IS_NOT_REALIZED_WINDOW_SCOPE",
        "PRODUCT_CATALOGUE_ENTRY_IS_NOT_INSTALLED_PRODUCT",
        "SAME_PROJECT_DOCUMENT_SET_IS_NOT_AUTOMATIC_COMPONENT_LINK",
        "REPLACED_OPENING_COMPLIANCE_IS_NOT_WHOLE_DWELLING_WINDOW_COMPLIANCE",
        "KEHOP_COMPLETED_PROJECT_IS_NOT_NON_EKR_PROJECT",
        "RECORD_LEVEL_BRIDGE_IS_NOT_NATIONAL_POPULATION_SURFACE",
    )
