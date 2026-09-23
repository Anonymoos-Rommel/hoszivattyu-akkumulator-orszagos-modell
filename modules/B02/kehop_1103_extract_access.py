"""B02-P110 KEHOP 1103 extract-access contract.

P109 proved that completed KEHOP Plusz 4.1.7/4.1.8 projects carry a
project-level professional completion indicator using the MEKH measure
category list, with exact code 1103 for window replacement.

P110 audits where that completion-indicator data lives and which public
surfaces can expose it.

Current official governance shows that the KEHOP Plusz implementation
administration:
- tracks physical indicators,
- aggregates/analyzes the data acquired in its remit,
- participates in FAIR development and information-content definition,
- provides programme-progress data.

Thus the exact administrative data surface is the KEHOP implementation /
FAIR layer, not the public programme page.

No current public project-level 1103 completion export or filterable public
surface was identified.

P110 therefore narrows:
    MFB_KEHOP_COMPLETION_INDICATOR_1103_EXTRACT_REQUIRED
to:
    FAIR_IH_KEHOP_1103_COMPLETION_EXPORT_OR_AGGREGATE_REQUIRED

Two closure products are distinguished:
1. aggregate 1103 count for a declared complete programme/cutoff scope;
2. preferred record extract carrying stable project IDs and technical join keys.

An aggregate may support action-frequency/count questions but cannot support
window-U distributions or EKR de-duplication unless additional fields are
provided.

Critical boundaries:
PUBLIC_PROJECT_SEARCH != COMPLETION_INDICATOR_EXPORT
PROGRAMME_INDICATORS != COMPONENT_ACTION_COHORT
ADMIN_DATA_EXISTS != PUBLIC_DATA_AVAILABLE
1103_AGGREGATE != TECHNICAL_U_DISTRIBUTION
1103_COUNT != NON_EKR_1103_COUNT
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from modules.B02.ekr_verified_window_compliance import (
    P102_HP_ONLY_UPPER,
    P102_STRUCTURAL_CALIBRATED_RETROFIT_FLOOR,
)


P110_STATUS = "QUALIFIED_FAIR_IH_KEHOP_1103_ACCESS_BOUNDARY"

SUPERSEDED_BLOCKER = "MFB_KEHOP_COMPLETION_INDICATOR_1103_EXTRACT_REQUIRED"
PRIMARY_NEXT_RESIDUAL = "FAIR_IH_KEHOP_1103_COMPLETION_EXPORT_OR_AGGREGATE_REQUIRED"
PREFERRED_RECORD_RESIDUAL = "FAIR_IH_KEHOP_1103_COMPLETION_RECORD_EXTRACT_REQUIRED"
TECHNICAL_JOIN_RESIDUAL = "KEHOP_1103_FINAL_TECHNICAL_DOCUMENT_JOIN_REQUIRED"
EKR_OVERLAP_RESIDUAL = "KEHOP_EKR1103_OVERLAP_OR_HEM_ATTRIBUTION_REQUIRED"
OVERALL_WINDOW_RESIDUAL = "CURRENT_REPLACED_WINDOW_COMPLIANCE_POPULATION_SURFACE_REQUIRED"

PROGRAMMES = ("KEHOP_PLUSZ_4_1_7_24", "KEHOP_PLUSZ_4_1_8_24")
WINDOW_MEASURE_CATEGORY = "1103"


@dataclass(frozen=True)
class Kehop1103AggregateCandidate:
    declared_programmes: tuple[str, ...]
    cutoff_date: str
    completed_project_count_all_measures: int
    completed_project_count_1103: int
    enumeration_complete_for_declared_scope: bool
    source_scope_description: str


@dataclass(frozen=True)
class Kehop1103AggregateDecision:
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


def assess_kehop_1103_aggregate(
    candidate: Kehop1103AggregateCandidate,
) -> Kehop1103AggregateDecision:
    blockers: list[str] = []
    warnings: list[str] = []

    if not candidate.declared_programmes:
        blockers.append("DECLARED_PROGRAMME_SCOPE_REQUIRED")
    elif any(p not in PROGRAMMES for p in candidate.declared_programmes):
        blockers.append("UNSUPPORTED_PROGRAMME_IN_DECLARED_SCOPE")

    if not _date_ok(candidate.cutoff_date):
        blockers.append("VALID_CUTOFF_DATE_REQUIRED")

    if candidate.completed_project_count_all_measures < 0:
        blockers.append("NONNEGATIVE_COMPLETED_PROJECT_COUNT_REQUIRED")
    if candidate.completed_project_count_1103 < 0:
        blockers.append("NONNEGATIVE_1103_COUNT_REQUIRED")
    if candidate.completed_project_count_1103 > candidate.completed_project_count_all_measures:
        blockers.append("1103_COUNT_CANNOT_EXCEED_ALL_COMPLETED_PROJECTS")

    if not candidate.enumeration_complete_for_declared_scope:
        blockers.append("COMPLETE_ENUMERATION_FOR_DECLARED_SCOPE_REQUIRED")
    if not candidate.source_scope_description.strip():
        blockers.append("SOURCE_SCOPE_DESCRIPTION_REQUIRED")

    if not blockers:
        warnings.extend(
            (
                "AGGREGATE_1103_COUNT_DOES_NOT_SUPPLY_TECHNICAL_U_DISTRIBUTION",
                "AGGREGATE_1103_COUNT_DOES_NOT_CLASSIFY_EKR_OVERLAP",
            )
        )

    return Kehop1103AggregateDecision(
        admitted=not blockers,
        status=(
            "QUALIFIED_KEHOP_1103_COMPLETION_AGGREGATE"
            if not blockers
            else "REJECTED_FAIL_CLOSED_KEHOP_1103_AGGREGATE"
        ),
        blockers=tuple(dict.fromkeys(blockers)),
        warnings=tuple(dict.fromkeys(warnings)),
    )


def p110_state() -> dict[str, object]:
    return {
        "status": P110_STATUS,
        "superseded_blocker": SUPERSEDED_BLOCKER,
        "primary_residual": PRIMARY_NEXT_RESIDUAL,
        "preferred_record_residual": PREFERRED_RECORD_RESIDUAL,
        "technical_join_residual": TECHNICAL_JOIN_RESIDUAL,
        "ekr_overlap_residual": EKR_OVERLAP_RESIDUAL,
        "overall_window_residual": OVERALL_WINDOW_RESIDUAL,
        "admin_surface": "KEHOP_IMPLEMENTATION_AUTHORITY_PLUS_FAIR",
        "completion_indicator_1103_schema_proven": True,
        "admin_indicator_monitoring_and_aggregation_proven": True,
        "fair_information_content_governance_proven": True,
        "current_public_project_level_1103_export_identified": False,
        "current_public_filterable_1103_surface_identified": False,
        "aggregate_route_admissible": True,
        "record_extract_route_preferred_for_technical_join": True,
        "p102_structural_calibrated_retrofit_floor_lower_share": (
            P102_STRUCTURAL_CALIBRATED_RETROFIT_FLOOR
        ),
        "hp_only_share_lower": 0.0,
        "hp_only_share_upper": P102_HP_ONLY_UPPER,
        "p110_numeric_national_action_tightening": False,
    }


def semantic_boundaries() -> tuple[str, ...]:
    return (
        "PUBLIC_PROJECT_SEARCH_IS_NOT_COMPLETION_INDICATOR_EXPORT",
        "PROGRAMME_INDICATORS_ARE_NOT_COMPONENT_ACTION_COHORT",
        "ADMIN_DATA_EXISTS_IS_NOT_PUBLIC_DATA_AVAILABLE",
        "1103_AGGREGATE_IS_NOT_TECHNICAL_U_DISTRIBUTION",
        "1103_COUNT_IS_NOT_NON_EKR_1103_COUNT",
    )
