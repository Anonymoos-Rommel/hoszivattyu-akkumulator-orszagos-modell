"""B02-P113 KEHOP program-monitoring 1103 aggregate boundary.

P112 proved that FAIR/EUPR can export project/report monitoring facts at
authorised project grain, while complete cross-project materialisation remained
open.

P113 qualifies the cross-project aggregation layer itself.

Official FAIR/EUPR terminology defines Programmonitoring as the activity that
aggregates the results of projects implemented under a programme and compares
those aggregated results with programme target values.

This proves:
- a programme-level cross-project aggregation concept is native to FAIR/EUPR;
- cross-project aggregation is distinct from a beneficiary's single-project
  monitoring export;
- a source-generated aggregate is a legitimate native product class.

P113 does NOT prove that the KEHOP professional metric
"Energy-efficiency measure category" is included in current program-monitoring
aggregation, nor that category 1103 is exposed in any current institutional or
public report.

Therefore the exact remaining acquisition is narrowed to:
- direct readback that the KEHOP 4.1.7/4.1.8 measure-category metric is included
  in program-monitoring aggregation; or
- an institutional complete cross-project export/source-generated aggregate
  that explicitly reports 1103 for a declared programme/cutoff scope.

Critical boundaries:
PROGRAMMONITORING_AGGREGATES_PROJECT_RESULTS != ALL_PROJECT_FIELDS_ARE_AGGREGATED
PROGRAMMONITORING_LAYER_EXISTS != 1103_INCLUDED
SOURCE_GENERATED_AGGREGATE_CLASS_EXISTS != CURRENT_1103_AGGREGATE_OBSERVED
PROGRAMME_AGGREGATE != TECHNICAL_U_DISTRIBUTION
PROGRAMME_1103_COUNT != NON_EKR_1103_COUNT
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from modules.B02.ekr_verified_window_compliance import (
    P102_HP_ONLY_UPPER,
    P102_STRUCTURAL_CALIBRATED_RETROFIT_FLOOR,
)

P113_STATUS = "QUALIFIED_KEHOP_PROGRAMMONITORING_AGGREGATION_BOUNDARY"

SUPERSEDED_BLOCKER = (
    "FAIR_IH_CROSS_PROJECT_KEHOP_1103_MONITORING_EXPORT_OR_SOURCE_AGGREGATE_REQUIRED"
)
PRIMARY_NEXT_RESIDUAL = (
    "KEHOP_417_418_PROGRAMMONITORING_1103_INCLUSION_OR_INSTITUTIONAL_EXPORT_READBACK_REQUIRED"
)
PARAMETERIZATION_RESIDUAL = (
    "KEHOP_417_418_1103_MONITORING_PARAMETERIZATION_READBACK_REQUIRED"
)
PREFERRED_RECORD_RESIDUAL = "FAIR_IH_KEHOP_1103_COMPLETION_RECORD_EXTRACT_REQUIRED"
TECHNICAL_JOIN_RESIDUAL = "KEHOP_1103_FINAL_TECHNICAL_DOCUMENT_JOIN_REQUIRED"
EKR_OVERLAP_RESIDUAL = "KEHOP_EKR1103_OVERLAP_OR_HEM_ATTRIBUTION_REQUIRED"
OVERALL_WINDOW_RESIDUAL = "CURRENT_REPLACED_WINDOW_COMPLIANCE_POPULATION_SURFACE_REQUIRED"

PROGRAMMES = ("KEHOP_PLUSZ_4_1_7_24", "KEHOP_PLUSZ_4_1_8_24")


@dataclass(frozen=True)
class ProgramMonitoringAggregateCandidate:
    declared_programmes: tuple[str, ...]
    cutoff_date: str
    metric_name: str
    measure_category_code: str
    completed_project_count_all_measures: int
    completed_project_count_1103: int
    source_generated: bool
    complete_for_declared_scope: bool
    aggregation_basis_description: str


@dataclass(frozen=True)
class ProgramMonitoringAggregateDecision:
    admitted: bool
    status: str
    blockers: tuple[str, ...]
    warnings: tuple[str, ...]


def _date_ok(value: str) -> bool:
    try:
        date.fromisoformat(value)
        return True
    except (ValueError, TypeError):
        return False


def assess_program_monitoring_aggregate(
    candidate: ProgramMonitoringAggregateCandidate,
) -> ProgramMonitoringAggregateDecision:
    blockers: list[str] = []
    warnings: list[str] = []

    if not candidate.declared_programmes:
        blockers.append("DECLARED_PROGRAMME_SCOPE_REQUIRED")
    elif any(p not in PROGRAMMES for p in candidate.declared_programmes):
        blockers.append("UNSUPPORTED_PROGRAMME_IN_DECLARED_SCOPE")

    if not _date_ok(candidate.cutoff_date):
        blockers.append("VALID_CUTOFF_DATE_REQUIRED")

    if candidate.metric_name.strip() != "Energiahatékonysági intézkedés kategória":
        blockers.append("EXACT_KEHOP_MEASURE_CATEGORY_METRIC_REQUIRED")

    if candidate.measure_category_code.strip() != "1103":
        blockers.append("EXACT_MEASURE_CATEGORY_1103_REQUIRED")

    if candidate.completed_project_count_all_measures < 0:
        blockers.append("NONNEGATIVE_COMPLETED_PROJECT_COUNT_REQUIRED")
    if candidate.completed_project_count_1103 < 0:
        blockers.append("NONNEGATIVE_1103_COUNT_REQUIRED")
    if candidate.completed_project_count_1103 > candidate.completed_project_count_all_measures:
        blockers.append("1103_COUNT_CANNOT_EXCEED_ALL_COMPLETED_PROJECTS")

    if not candidate.source_generated:
        blockers.append("SOURCE_GENERATED_PROGRAMMONITORING_OUTPUT_REQUIRED")
    if not candidate.complete_for_declared_scope:
        blockers.append("COMPLETE_DECLARED_SCOPE_REQUIRED")
    if not candidate.aggregation_basis_description.strip():
        blockers.append("AGGREGATION_BASIS_DESCRIPTION_REQUIRED")

    if not blockers:
        warnings.extend(
            (
                "1103_PROGRAMME_AGGREGATE_DOES_NOT_SUPPLY_TECHNICAL_U_DISTRIBUTION",
                "1103_PROGRAMME_AGGREGATE_DOES_NOT_CLASSIFY_EKR_OVERLAP",
                "PROGRAMME_AGGREGATE_DOES_NOT_REPLACE_PREFERRED_RECORD_EXTRACT",
            )
        )

    return ProgramMonitoringAggregateDecision(
        admitted=not blockers,
        status=(
            "QUALIFIED_KEHOP_1103_PROGRAMMONITORING_AGGREGATE"
            if not blockers
            else "REJECTED_FAIL_CLOSED_PROGRAMMONITORING_AGGREGATE"
        ),
        blockers=tuple(dict.fromkeys(blockers)),
        warnings=tuple(dict.fromkeys(warnings)),
    )


def p113_state() -> dict[str, object]:
    return {
        "status": P113_STATUS,
        "superseded_blocker": SUPERSEDED_BLOCKER,
        "primary_residual": PRIMARY_NEXT_RESIDUAL,
        "parameterization_residual": PARAMETERIZATION_RESIDUAL,
        "preferred_record_residual": PREFERRED_RECORD_RESIDUAL,
        "technical_join_residual": TECHNICAL_JOIN_RESIDUAL,
        "ekr_overlap_residual": EKR_OVERLAP_RESIDUAL,
        "overall_window_residual": OVERALL_WINDOW_RESIDUAL,
        "programmonitoring_cross_project_aggregation_semantics_proven": True,
        "project_results_aggregation_native_to_programmonitoring": True,
        "source_generated_aggregate_product_class_qualified": True,
        "kehop_1103_in_programmonitoring_inclusion_proven": False,
        "current_institutional_1103_aggregate_observed": False,
        "current_public_1103_aggregate_observed": False,
        "p102_structural_calibrated_retrofit_floor_lower_share": (
            P102_STRUCTURAL_CALIBRATED_RETROFIT_FLOOR
        ),
        "hp_only_share_lower": 0.0,
        "hp_only_share_upper": P102_HP_ONLY_UPPER,
        "p113_numeric_national_action_tightening": False,
    }


def semantic_boundaries() -> tuple[str, ...]:
    return (
        "PROGRAMMONITORING_AGGREGATES_PROJECT_RESULTS_IS_NOT_ALL_FIELDS_AGGREGATED",
        "PROGRAMMONITORING_LAYER_EXISTS_IS_NOT_1103_INCLUDED",
        "SOURCE_GENERATED_AGGREGATE_CLASS_EXISTS_IS_NOT_CURRENT_1103_AGGREGATE_OBSERVED",
        "PROGRAMME_AGGREGATE_IS_NOT_TECHNICAL_U_DISTRIBUTION",
        "PROGRAMME_1103_COUNT_IS_NOT_NON_EKR_1103_COUNT",
    )
