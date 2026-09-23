"""B02-P111 FAIR project-universe export bridge.

P110 identified the KEHOP implementation / FAIR administrative layer as the
exact locus of the project-level completion indicator carrying MEKH measure
category 1103.

P111 qualifies a concrete machine-readable acquisition route for the project
universe itself:

- the official FAIR Supported Project Search is populated from development
  programme systems including EUPR;
- the supported-project data are refreshed daily;
- authenticated users can export search results as CSV;
- for Szechenyi Terv Plusz the documented CSV export has no result-row limit.

The documented public/search export field set is project metadata. It does not
establish exposure of the professional physical-completion indicator or an
exact MEKH 1103 selector.

Therefore P111 resolves the generic machine-readable project-universe problem
but does not resolve the 1103 cohort. The remaining exact join is:

    FAIR project_id / project universe
        +
    FAIR/IH physical-completion indicator containing 1103

or an equivalent source-generated complete 1103 aggregate.

Critical boundaries:
FAIR_PROJECT_CSV != COMPLETION_INDICATOR_EXPORT
PROJECT_METADATA != MEASURE_CATEGORY_1103
LOGIN_GATED_SEARCH_EXPORT != INTERNAL_INDICATOR_EXPORT
NEARLY_10000_EXPECTED_HOMES != COMPLETED_PROJECT_COUNT
PROJECT_UNIVERSE_ROUTE != TECHNICAL_U_DISTRIBUTION
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from modules.B02.ekr_verified_window_compliance import (
    P102_HP_ONLY_UPPER,
    P102_STRUCTURAL_CALIBRATED_RETROFIT_FLOOR,
)

P111_STATUS = "QUALIFIED_FAIR_PROJECT_UNIVERSE_EXPORT_BRIDGE"

SUPERSEDED_BLOCKER = "FAIR_IH_KEHOP_1103_COMPLETION_EXPORT_OR_AGGREGATE_REQUIRED"
PRIMARY_NEXT_RESIDUAL = (
    "FAIR_IH_KEHOP_1103_COMPLETION_INDICATOR_JOIN_OR_SOURCE_AGGREGATE_REQUIRED"
)
PREFERRED_RECORD_RESIDUAL = "FAIR_IH_KEHOP_1103_COMPLETION_RECORD_EXTRACT_REQUIRED"
TECHNICAL_JOIN_RESIDUAL = "KEHOP_1103_FINAL_TECHNICAL_DOCUMENT_JOIN_REQUIRED"
EKR_OVERLAP_RESIDUAL = "KEHOP_EKR1103_OVERLAP_OR_HEM_ATTRIBUTION_REQUIRED"
OVERALL_WINDOW_RESIDUAL = "CURRENT_REPLACED_WINDOW_COMPLIANCE_POPULATION_SURFACE_REQUIRED"

PROGRAMMES = ("KEHOP_PLUSZ_4_1_7_24", "KEHOP_PLUSZ_4_1_8_24")


@dataclass(frozen=True)
class FairProjectUniverseCandidate:
    declared_programmes: tuple[str, ...]
    extract_refresh_date: str
    project_ids: tuple[str, ...]
    source_generated_csv: bool
    enumeration_complete_for_declared_scope: bool
    source_scope_description: str


@dataclass(frozen=True)
class FairProjectUniverseDecision:
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


def assess_fair_project_universe(
    candidate: FairProjectUniverseCandidate,
) -> FairProjectUniverseDecision:
    blockers: list[str] = []
    warnings: list[str] = []

    if not candidate.declared_programmes:
        blockers.append("DECLARED_PROGRAMME_SCOPE_REQUIRED")
    elif any(p not in PROGRAMMES for p in candidate.declared_programmes):
        blockers.append("UNSUPPORTED_PROGRAMME_IN_DECLARED_SCOPE")

    if not _date_ok(candidate.extract_refresh_date):
        blockers.append("VALID_EXTRACT_REFRESH_DATE_REQUIRED")

    if not candidate.source_generated_csv:
        blockers.append("FAIR_SOURCE_GENERATED_CSV_REQUIRED")

    if not candidate.enumeration_complete_for_declared_scope:
        blockers.append("COMPLETE_ENUMERATION_FOR_DECLARED_SCOPE_REQUIRED")

    if not candidate.project_ids:
        blockers.append("NONEMPTY_PROJECT_ID_UNIVERSE_REQUIRED")
    elif any(not p.strip() for p in candidate.project_ids):
        blockers.append("NONEMPTY_PROJECT_IDS_REQUIRED")
    elif len(set(candidate.project_ids)) != len(candidate.project_ids):
        blockers.append("UNIQUE_PROJECT_IDS_REQUIRED")

    if not candidate.source_scope_description.strip():
        blockers.append("SOURCE_SCOPE_DESCRIPTION_REQUIRED")

    if not blockers:
        warnings.extend(
            (
                "PROJECT_UNIVERSE_DOES_NOT_CLASSIFY_1103",
                "PROJECT_UNIVERSE_DOES_NOT_SUPPLY_TECHNICAL_U_DISTRIBUTION",
                "PROJECT_UNIVERSE_DOES_NOT_CLASSIFY_EKR_OVERLAP",
            )
        )

    return FairProjectUniverseDecision(
        admitted=not blockers,
        status=(
            "QUALIFIED_FAIR_KEHOP_PROJECT_UNIVERSE"
            if not blockers
            else "REJECTED_FAIL_CLOSED_FAIR_PROJECT_UNIVERSE"
        ),
        blockers=tuple(dict.fromkeys(blockers)),
        warnings=tuple(dict.fromkeys(warnings)),
    )


def p111_state() -> dict[str, object]:
    return {
        "status": P111_STATUS,
        "superseded_blocker": SUPERSEDED_BLOCKER,
        "primary_residual": PRIMARY_NEXT_RESIDUAL,
        "preferred_record_residual": PREFERRED_RECORD_RESIDUAL,
        "technical_join_residual": TECHNICAL_JOIN_RESIDUAL,
        "ekr_overlap_residual": EKR_OVERLAP_RESIDUAL,
        "overall_window_residual": OVERALL_WINDOW_RESIDUAL,
        "fair_supported_project_search_proven": True,
        "fair_daily_refresh_proven": True,
        "authenticated_csv_export_proven": True,
        "szechenyi_terv_plusz_export_row_limit": None,
        "machine_readable_project_universe_route_proven": True,
        "documented_project_metadata_export_fields_proven": True,
        "physical_completion_indicator_in_search_export_proven": False,
        "exact_1103_selector_in_search_export_proven": False,
        "mfb_programme_scale_control_is_approximate": True,
        "p102_structural_calibrated_retrofit_floor_lower_share": (
            P102_STRUCTURAL_CALIBRATED_RETROFIT_FLOOR
        ),
        "hp_only_share_lower": 0.0,
        "hp_only_share_upper": P102_HP_ONLY_UPPER,
        "p111_numeric_national_action_tightening": False,
    }


def semantic_boundaries() -> tuple[str, ...]:
    return (
        "FAIR_PROJECT_CSV_IS_NOT_COMPLETION_INDICATOR_EXPORT",
        "PROJECT_METADATA_IS_NOT_MEASURE_CATEGORY_1103",
        "LOGIN_GATED_SEARCH_EXPORT_IS_NOT_INTERNAL_INDICATOR_EXPORT",
        "NEARLY_10000_EXPECTED_HOMES_IS_NOT_COMPLETED_PROJECT_COUNT",
        "PROJECT_UNIVERSE_ROUTE_IS_NOT_TECHNICAL_U_DISTRIBUTION",
    )
