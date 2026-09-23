"""B02-P114 empirical OFP application action-mix anchor.

This slice admits a real observed programme data point reported by the MFB's
EU Business Directorate head to Portfolio for the 2025-10-17 snapshot.

Reported programme observations:
- HUF 50.4bn applications;
- HUF 40.3bn approvals;
- HUF 18.8bn disbursements;
- 4,457 applications with disbursement;
- HUF 5.5m average application;
- insulation in 90% of applications;
- insulation + window replacement together in approximately two thirds.

The observation is useful because it is actual programme behaviour, not a
schema, planned measure list or semantic capability statement.

It is NOT promoted to the P109-P113 completed KEHOP 1103 cohort because:
- the reported action mix is application-stage, not physical completion;
- the source describes the cumulative energy-efficiency OFP programme series
  spanning the earlier RRF phase and the later KEHOP Plusz phase;
- "window replacement" is a human-readable action label, not direct readback
  of the FAIR/MEKH administrative category code 1103;
- the two-thirds wording is approximate;
- approval/disbursement does not establish completed technical performance.

Critical boundaries:
APPLICATION_ACTION_MIX != COMPLETED_ACTION_COHORT
RRF_PLUS_KEHOP_CUMULATIVE_SERIES != KEHOP_417_418_ONLY
WINDOW_REPLACEMENT_LABEL != VERIFIED_ADMIN_CODE_1103
DISBURSEMENT_CASE != PHYSICALLY_COMPLETED_PROJECT
APPROXIMATELY_TWO_THIRDS != EXACT_HARD_SHARE_BOUND
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from modules.B02.ekr_verified_window_compliance import (
    P102_HP_ONLY_UPPER,
    P102_STRUCTURAL_CALIBRATED_RETROFIT_FLOOR,
)

P114_STATUS = "ADMITTED_EMPIRICAL_OFP_APPLICATION_ACTION_MIX"

CURRENT_COMPLETION_RESIDUAL = (
    "KEHOP_417_418_PROGRAMMONITORING_1103_INCLUSION_OR_INSTITUTIONAL_EXPORT_READBACK_REQUIRED"
)
PREFERRED_RECORD_RESIDUAL = "FAIR_IH_KEHOP_1103_COMPLETION_RECORD_EXTRACT_REQUIRED"
TECHNICAL_JOIN_RESIDUAL = "KEHOP_1103_FINAL_TECHNICAL_DOCUMENT_JOIN_REQUIRED"
EKR_OVERLAP_RESIDUAL = "KEHOP_EKR1103_OVERLAP_OR_HEM_ATTRIBUTION_REQUIRED"
OVERALL_WINDOW_RESIDUAL = "CURRENT_REPLACED_WINDOW_COMPLIANCE_POPULATION_SURFACE_REQUIRED"

SNAPSHOT_DATE = "2025-10-17"
APPLICATION_VOLUME_HUF_BN = 50.4
APPROVAL_VOLUME_HUF_BN = 40.3
DISBURSEMENT_VOLUME_HUF_BN = 18.8
DISBURSEMENT_CASE_COUNT = 4457
AVERAGE_APPLICATION_HUF_M = 5.5
INSULATION_APPLICATION_SHARE = 0.90
INSULATION_PLUS_WINDOW_REPLACEMENT_REPORTED_SHARE = 2.0 / 3.0


@dataclass(frozen=True)
class ApplicationActionMixObservation:
    snapshot_date: str
    application_volume_huf_bn: float
    approval_volume_huf_bn: float
    disbursement_volume_huf_bn: float
    disbursement_case_count: int
    average_application_huf_m: float
    insulation_application_share: float
    insulation_plus_window_replacement_share: float
    combined_share_is_approximate: bool
    stage: str
    programme_series_scope: str
    source_is_mfb_official_statement: bool


@dataclass(frozen=True)
class ApplicationActionMixDecision:
    admitted: bool
    status: str
    blockers: tuple[str, ...]
    warnings: tuple[str, ...]


def _valid_date(value: str) -> bool:
    try:
        date.fromisoformat(value)
        return True
    except (TypeError, ValueError):
        return False


def assess_application_action_mix(
    candidate: ApplicationActionMixObservation,
) -> ApplicationActionMixDecision:
    blockers: list[str] = []
    warnings: list[str] = []

    if not _valid_date(candidate.snapshot_date):
        blockers.append("VALID_SNAPSHOT_DATE_REQUIRED")
    if candidate.application_volume_huf_bn <= 0:
        blockers.append("POSITIVE_APPLICATION_VOLUME_REQUIRED")
    if not 0 <= candidate.approval_volume_huf_bn <= candidate.application_volume_huf_bn:
        blockers.append("APPROVAL_VOLUME_MUST_BE_WITHIN_APPLICATION_VOLUME")
    if not 0 <= candidate.disbursement_volume_huf_bn <= candidate.approval_volume_huf_bn:
        blockers.append("DISBURSEMENT_VOLUME_MUST_BE_WITHIN_APPROVAL_VOLUME")
    if candidate.disbursement_case_count <= 0:
        blockers.append("POSITIVE_DISBURSEMENT_CASE_COUNT_REQUIRED")
    if candidate.average_application_huf_m <= 0:
        blockers.append("POSITIVE_AVERAGE_APPLICATION_REQUIRED")
    if not 0 <= candidate.insulation_application_share <= 1:
        blockers.append("VALID_INSULATION_SHARE_REQUIRED")
    if not 0 <= candidate.insulation_plus_window_replacement_share <= 1:
        blockers.append("VALID_COMBINED_ACTION_SHARE_REQUIRED")
    if (
        candidate.insulation_plus_window_replacement_share
        > candidate.insulation_application_share
    ):
        blockers.append("COMBINED_SHARE_CANNOT_EXCEED_INSULATION_SHARE")
    if candidate.stage != "APPLICATION":
        blockers.append("APPLICATION_STAGE_REQUIRED")
    if candidate.programme_series_scope != "RRF_PLUS_KEHOP_CUMULATIVE_OFP":
        blockers.append("SOURCE_NATIVE_PROGRAMME_SERIES_SCOPE_REQUIRED")
    if not candidate.source_is_mfb_official_statement:
        blockers.append("MFB_INSTITUTIONAL_OBSERVATION_REQUIRED")

    if not blockers:
        warnings.extend(
            (
                "APPLICATION_ACTION_MIX_IS_NOT_COMPLETED_ACTION_COHORT",
                "RRF_PLUS_KEHOP_CUMULATIVE_SERIES_IS_NOT_KEHOP_417_418_ONLY",
                "WINDOW_REPLACEMENT_LABEL_IS_NOT_VERIFIED_ADMIN_CODE_1103",
                "DISBURSEMENT_CASE_IS_NOT_PHYSICALLY_COMPLETED_PROJECT",
            )
        )
        if candidate.combined_share_is_approximate:
            warnings.append("APPROXIMATE_TWO_THIRDS_IS_NOT_EXACT_HARD_SHARE_BOUND")

    return ApplicationActionMixDecision(
        admitted=not blockers,
        status=(
            "ADMITTED_EMPIRICAL_APPLICATION_ACTION_MIX"
            if not blockers
            else "REJECTED_FAIL_CLOSED_APPLICATION_ACTION_MIX"
        ),
        blockers=tuple(dict.fromkeys(blockers)),
        warnings=tuple(dict.fromkeys(warnings)),
    )


def canonical_observation() -> ApplicationActionMixObservation:
    return ApplicationActionMixObservation(
        snapshot_date=SNAPSHOT_DATE,
        application_volume_huf_bn=APPLICATION_VOLUME_HUF_BN,
        approval_volume_huf_bn=APPROVAL_VOLUME_HUF_BN,
        disbursement_volume_huf_bn=DISBURSEMENT_VOLUME_HUF_BN,
        disbursement_case_count=DISBURSEMENT_CASE_COUNT,
        average_application_huf_m=AVERAGE_APPLICATION_HUF_M,
        insulation_application_share=INSULATION_APPLICATION_SHARE,
        insulation_plus_window_replacement_share=(
            INSULATION_PLUS_WINDOW_REPLACEMENT_REPORTED_SHARE
        ),
        combined_share_is_approximate=True,
        stage="APPLICATION",
        programme_series_scope="RRF_PLUS_KEHOP_CUMULATIVE_OFP",
        source_is_mfb_official_statement=True,
    )


def p114_state() -> dict[str, object]:
    return {
        "status": P114_STATUS,
        "snapshot_date": SNAPSHOT_DATE,
        "application_volume_huf_bn": APPLICATION_VOLUME_HUF_BN,
        "approval_volume_huf_bn": APPROVAL_VOLUME_HUF_BN,
        "disbursement_volume_huf_bn": DISBURSEMENT_VOLUME_HUF_BN,
        "disbursement_case_count": DISBURSEMENT_CASE_COUNT,
        "average_application_huf_m": AVERAGE_APPLICATION_HUF_M,
        "insulation_application_share": INSULATION_APPLICATION_SHARE,
        "insulation_plus_window_replacement_reported_share": (
            INSULATION_PLUS_WINDOW_REPLACEMENT_REPORTED_SHARE
        ),
        "combined_share_precision": "APPROXIMATE",
        "programme_series_scope": "RRF_PLUS_KEHOP_CUMULATIVE_OFP",
        "stage": "APPLICATION",
        "empirical_action_mix_admitted": True,
        "kehop_417_418_only_action_mix_identified": False,
        "completion_1103_cohort_identified": False,
        "current_completion_residual": CURRENT_COMPLETION_RESIDUAL,
        "preferred_record_residual": PREFERRED_RECORD_RESIDUAL,
        "technical_join_residual": TECHNICAL_JOIN_RESIDUAL,
        "ekr_overlap_residual": EKR_OVERLAP_RESIDUAL,
        "overall_window_residual": OVERALL_WINDOW_RESIDUAL,
        "p102_structural_calibrated_retrofit_floor_lower_share": (
            P102_STRUCTURAL_CALIBRATED_RETROFIT_FLOOR
        ),
        "hp_only_share_lower": 0.0,
        "hp_only_share_upper": P102_HP_ONLY_UPPER,
        "p114_numeric_national_compliance_tightening": False,
    }


def semantic_boundaries() -> tuple[str, ...]:
    return (
        "APPLICATION_ACTION_MIX_IS_NOT_COMPLETED_ACTION_COHORT",
        "RRF_PLUS_KEHOP_CUMULATIVE_SERIES_IS_NOT_KEHOP_417_418_ONLY",
        "WINDOW_REPLACEMENT_LABEL_IS_NOT_VERIFIED_ADMIN_CODE_1103",
        "DISBURSEMENT_CASE_IS_NOT_PHYSICALLY_COMPLETED_PROJECT",
        "APPROXIMATELY_TWO_THIRDS_IS_NOT_EXACT_HARD_SHARE_BOUND",
    )
