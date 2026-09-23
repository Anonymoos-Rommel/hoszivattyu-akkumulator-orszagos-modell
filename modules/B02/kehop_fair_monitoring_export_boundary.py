"""B02-P112 FAIR project-level monitoring export boundary.

P111 proved a machine-readable FAIR supported-project universe route for the
KEHOP Plusz 4.1.7/4.1.8 programme family, but the exact completion-indicator
join remained unresolved.

P112 qualifies a narrower, source-native route at project/report grain.

Official FAIR/EUPR help for Szakmai and Zaro Beszamolo monitoring records
states that:
- the monitoring list contains contract-planned monitoring records;
- the list can be exported as CSV or Excel;
- the export carries monitoring-record identity/type and realized fact data;
- fact data are bound to report sequence/type, including Zaro szakmai
  beszamolo;
- editing/viewing is access-controlled.

The KEHOP 4.1.7/4.1.8 call authority already establishes that
"Energy-efficiency measure category" is a project-level professional metric
reported at physical completion using the MEKH category list.

P112 therefore proves the generic project-level report/export path needed to
materialize completion facts from an authorised project context.

It does NOT prove:
- that the exact KEHOP 1103 field is visible in an externally observed export;
- a cross-project institutional export over the complete 4.1.7/4.1.8 universe;
- anonymous/public access;
- technical U values or EKR/HEM attribution.

The remaining primary acquisition problem is therefore cross-project/bulk
cohort materialization, not existence of a project-level export mechanism.

Critical boundaries:
PROJECT_LEVEL_MONITORING_EXPORT != CROSS_PROJECT_COMPLETE_COHORT
GENERIC_MONITORING_EXPORT_CAPABILITY != OBSERVED_KEHOP_1103_EXPORT
PROFESSIONAL_METRIC_SCHEMA != PUBLIC_FIELD_AVAILABILITY
FACT_VALUE_EXPORT != TECHNICAL_U_DISTRIBUTION
1103_COMPLETION_FACT != EKR_HEM_CLASSIFICATION
"""

from __future__ import annotations

from dataclasses import dataclass

from modules.B02.ekr_verified_window_compliance import (
    P102_HP_ONLY_UPPER,
    P102_STRUCTURAL_CALIBRATED_RETROFIT_FLOOR,
)

P112_STATUS = "QUALIFIED_FAIR_PROJECT_LEVEL_MONITORING_EXPORT_BOUNDARY"

SUPERSEDED_BLOCKER = (
    "FAIR_IH_KEHOP_1103_COMPLETION_INDICATOR_JOIN_OR_SOURCE_AGGREGATE_REQUIRED"
)
PRIMARY_NEXT_RESIDUAL = (
    "FAIR_IH_CROSS_PROJECT_KEHOP_1103_MONITORING_EXPORT_OR_SOURCE_AGGREGATE_REQUIRED"
)
PARAMETERIZATION_RESIDUAL = (
    "KEHOP_417_418_1103_MONITORING_PARAMETERIZATION_READBACK_REQUIRED"
)
PREFERRED_RECORD_RESIDUAL = "FAIR_IH_KEHOP_1103_COMPLETION_RECORD_EXTRACT_REQUIRED"
TECHNICAL_JOIN_RESIDUAL = "KEHOP_1103_FINAL_TECHNICAL_DOCUMENT_JOIN_REQUIRED"
EKR_OVERLAP_RESIDUAL = "KEHOP_EKR1103_OVERLAP_OR_HEM_ATTRIBUTION_REQUIRED"
OVERALL_WINDOW_RESIDUAL = "CURRENT_REPLACED_WINDOW_COMPLIANCE_POPULATION_SURFACE_REQUIRED"


@dataclass(frozen=True)
class ProjectMonitoringExportCandidate:
    project_id: str
    programme_code: str
    monitoring_name: str
    monitoring_type: str
    fact_value: str
    report_type: str
    source_generated_export: bool
    export_bound_to_project_context: bool


@dataclass(frozen=True)
class ProjectMonitoringExportDecision:
    admitted: bool
    status: str
    blockers: tuple[str, ...]
    warnings: tuple[str, ...]


def assess_project_monitoring_export(
    candidate: ProjectMonitoringExportCandidate,
) -> ProjectMonitoringExportDecision:
    blockers: list[str] = []
    warnings: list[str] = []

    if not candidate.project_id.strip():
        blockers.append("STABLE_PROJECT_ID_REQUIRED")
    if candidate.programme_code not in (
        "KEHOP_PLUSZ_4_1_7_24",
        "KEHOP_PLUSZ_4_1_8_24",
    ):
        blockers.append("SUPPORTED_KEHOP_PROGRAMME_REQUIRED")
    if not candidate.monitoring_name.strip():
        blockers.append("MONITORING_NAME_REQUIRED")
    if not candidate.monitoring_type.strip():
        blockers.append("MONITORING_TYPE_REQUIRED")
    if not candidate.fact_value.strip():
        blockers.append("FACT_VALUE_REQUIRED")
    if candidate.report_type not in (
        "SZAKMAI_BESZAMOLO",
        "EGYEDI_SZAKMAI_BESZAMOLO",
        "ZARO_SZAKMAI_BESZAMOLO",
        "FENNTARTASI_JELENTES",
        "ZARO_FENNTARTASI_JELENTES",
    ):
        blockers.append("SUPPORTED_REPORT_TYPE_REQUIRED")
    if not candidate.source_generated_export:
        blockers.append("FAIR_SOURCE_GENERATED_EXPORT_REQUIRED")
    if not candidate.export_bound_to_project_context:
        blockers.append("PROJECT_CONTEXT_BINDING_REQUIRED")

    if not blockers:
        warnings.extend(
            (
                "SINGLE_PROJECT_EXPORT_DOES_NOT_PROVE_COMPLETE_PROGRAMME_COHORT",
                "GENERIC_EXPORT_DOES_NOT_BY_ITSELF_PROVE_1103_PARAMETERIZATION",
                "FACT_VALUE_DOES_NOT_SUPPLY_TECHNICAL_U_DISTRIBUTION",
                "1103_FACT_DOES_NOT_CLASSIFY_EKR_HEM_OVERLAP",
            )
        )

    return ProjectMonitoringExportDecision(
        admitted=not blockers,
        status=(
            "QUALIFIED_PROJECT_LEVEL_MONITORING_EXPORT"
            if not blockers
            else "REJECTED_FAIL_CLOSED_PROJECT_MONITORING_EXPORT"
        ),
        blockers=tuple(dict.fromkeys(blockers)),
        warnings=tuple(dict.fromkeys(warnings)),
    )


def p112_state() -> dict[str, object]:
    return {
        "status": P112_STATUS,
        "superseded_blocker": SUPERSEDED_BLOCKER,
        "primary_residual": PRIMARY_NEXT_RESIDUAL,
        "parameterization_residual": PARAMETERIZATION_RESIDUAL,
        "preferred_record_residual": PREFERRED_RECORD_RESIDUAL,
        "technical_join_residual": TECHNICAL_JOIN_RESIDUAL,
        "ekr_overlap_residual": EKR_OVERLAP_RESIDUAL,
        "overall_window_residual": OVERALL_WINDOW_RESIDUAL,
        "kehop_1103_professional_metric_schema_proven": True,
        "project_level_monitoring_list_export_proven": True,
        "csv_export_proven": True,
        "excel_export_proven": True,
        "fact_date_and_fact_value_export_proven": True,
        "report_sequence_and_report_type_export_proven": True,
        "closing_report_type_supported": True,
        "access_controlled_project_context_proven": True,
        "exact_kehop_1103_parameterization_readback_observed": False,
        "cross_project_complete_417_418_export_proven": False,
        "anonymous_public_1103_export_proven": False,
        "p102_structural_calibrated_retrofit_floor_lower_share": (
            P102_STRUCTURAL_CALIBRATED_RETROFIT_FLOOR
        ),
        "hp_only_share_lower": 0.0,
        "hp_only_share_upper": P102_HP_ONLY_UPPER,
        "p112_numeric_national_action_tightening": False,
    }


def semantic_boundaries() -> tuple[str, ...]:
    return (
        "PROJECT_LEVEL_MONITORING_EXPORT_IS_NOT_CROSS_PROJECT_COMPLETE_COHORT",
        "GENERIC_MONITORING_EXPORT_CAPABILITY_IS_NOT_OBSERVED_KEHOP_1103_EXPORT",
        "PROFESSIONAL_METRIC_SCHEMA_IS_NOT_PUBLIC_FIELD_AVAILABILITY",
        "FACT_VALUE_EXPORT_IS_NOT_TECHNICAL_U_DISTRIBUTION",
        "1103_COMPLETION_FACT_IS_NOT_EKR_HEM_CLASSIFICATION",
    )
