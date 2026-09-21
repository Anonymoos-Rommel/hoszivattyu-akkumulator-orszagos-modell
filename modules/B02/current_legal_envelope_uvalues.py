"""B02-P81 current Hungarian legal envelope U-value authority.

Authority:
9/2023. (V. 25.) ÉKM decree, current consolidated text.

Section 3(3) requires the structures of an existing building that are affected
by an energy-saving renovation to comply with Annex 1 sections 1 and 2.
Annex 1 section 1.1 publishes component U-value requirements.

P81 binds those current legal requirements to the B02 post-state model only
when the component is actually affected by an energy-saving envelope
renovation and no applicable legal exception/transitional regime supersedes
the current requirement.

Critical boundaries:

CURRENT LEGAL U REQUIREMENT != CURRENT STOCK U OBSERVATION
LEGAL REQUIREMENT FOR AFFECTED COMPONENT != REQUIREMENT FOR UNTOUCHED COMPONENT
LEGAL U-MAX != REALIZED POST-RETROFIT U POINT
CURRENT EKM RULE != LEGACY TNM-SUPPORTED-PROGRAM REQUIREMENT
LEGAL COMPLIANCE AUTHORITY != NATIONAL ACTION ASSIGNMENT
"""

from __future__ import annotations

from dataclasses import dataclass

from modules.B02.keop23_uvalue_poststate import (
    AIR_TO_WATER_HP_ONLY,
    REFERENCE_ENVELOPE_RETROFIT,
    REFERENCE_ENVELOPE_RETROFIT_PLUS_AWHP,
)

SOURCE_ID = "SRC-B02-HU-ENERGY-RULES-2023"

QUALIFIED_CURRENT_LEGAL_U_REQUIREMENT = "QUALIFIED_CURRENT_LEGAL_U_REQUIREMENT"
NOT_APPLICABLE_UNTOUCHED_COMPONENT = "NOT_APPLICABLE_UNTOUCHED_COMPONENT"
Q = "Q"

NO_APPLICABLE_EXEMPTION = "NO_APPLICABLE_EXEMPTION"
APPLICABLE_PROTECTION_EXEMPTION = "APPLICABLE_PROTECTION_EXEMPTION"
EXEMPTION_STATUS_UNKNOWN = "EXEMPTION_STATUS_UNKNOWN"

CURRENT_EKM_REGIME = "CURRENT_EKM_REGIME"
LEGACY_TNM_PROGRAM_REGIME = "LEGACY_TNM_PROGRAM_REGIME"
LEGAL_REGIME_UNKNOWN = "LEGAL_REGIME_UNKNOWN"

CURRENT_LEGAL_U_MAX = {
    "EXTERNAL_WALL": 0.24,
    "FLAT_ROOF": 0.17,
    "PITCHED_ROOF": 0.17,
    "ATTIC_FLOOR": 0.17,
    "BASEMENT_CEILING": 0.26,
    "WINDOW": 1.10,
}

COMPONENT_SOURCE_LABEL = {
    "EXTERNAL_WALL": "Homlokzati fal",
    "FLAT_ROOF": "Laposteto",
    "PITCHED_ROOF": "Futott tetoteret hatarolo szerkezetek",
    "ATTIC_FLOOR": "Padlas es buvoter alatti fodem",
    "BASEMENT_CEILING": "Also zarofodem futetlen terek felett",
    "WINDOW": "Fa vagy PVC keretszerkezetu homlokzati uvegezett nyilaszaro >0.5m2",
}


@dataclass(frozen=True)
class LegalUValueConstraint:
    component: str
    upper_u_w_m2k: float | None
    status: str
    source_id: str
    blockers: tuple[str, ...]
    applicability: str


@dataclass(frozen=True)
class LegalPostStateDecision:
    status: str
    blockers: tuple[str, ...]


def current_legal_u_requirement(
    component: str,
    *,
    affected_by_energy_saving_renovation: bool,
    protection_exemption_status: str = NO_APPLICABLE_EXEMPTION,
    legal_regime: str = CURRENT_EKM_REGIME,
) -> LegalUValueConstraint:
    """Return the current legal U requirement only inside its actual scope."""

    if component not in CURRENT_LEGAL_U_MAX:
        return LegalUValueConstraint(
            component=component,
            upper_u_w_m2k=None,
            status=Q,
            source_id=SOURCE_ID,
            blockers=("COMPONENT_NOT_MAPPED_TO_EKM_ANNEX_1_1_1",),
            applicability="UNRESOLVED",
        )

    if not affected_by_energy_saving_renovation:
        return LegalUValueConstraint(
            component=component,
            upper_u_w_m2k=None,
            status=NOT_APPLICABLE_UNTOUCHED_COMPONENT,
            source_id=SOURCE_ID,
            blockers=(),
            applicability="UNAFFECTED_COMPONENT",
        )

    blockers: list[str] = []
    if protection_exemption_status == APPLICABLE_PROTECTION_EXEMPTION:
        blockers.append("HERITAGE_OR_LOCAL_PROTECTION_EXCEPTION_APPLIES")
    elif protection_exemption_status == EXEMPTION_STATUS_UNKNOWN:
        blockers.append("PROTECTION_EXCEPTION_STATUS_REQUIRED")
    elif protection_exemption_status != NO_APPLICABLE_EXEMPTION:
        blockers.append("INVALID_PROTECTION_EXCEPTION_STATUS")

    if legal_regime == LEGACY_TNM_PROGRAM_REGIME:
        blockers.append("LEGACY_TNM_SUPPORTED_PROGRAM_REQUIREMENT_APPLIES")
    elif legal_regime == LEGAL_REGIME_UNKNOWN:
        blockers.append("APPLICABLE_LEGAL_REGIME_REQUIRED")
    elif legal_regime != CURRENT_EKM_REGIME:
        blockers.append("INVALID_LEGAL_REGIME")

    if blockers:
        return LegalUValueConstraint(
            component=component,
            upper_u_w_m2k=None,
            status=Q,
            source_id=SOURCE_ID,
            blockers=tuple(blockers),
            applicability="EXCEPTION_OR_TRANSITION_UNRESOLVED",
        )

    return LegalUValueConstraint(
        component=component,
        upper_u_w_m2k=CURRENT_LEGAL_U_MAX[component],
        status=QUALIFIED_CURRENT_LEGAL_U_REQUIREMENT,
        source_id=SOURCE_ID,
        blockers=(),
        applicability="ENERGY_SAVING_RENOVATION_AFFECTED_COMPONENT",
    )


def assess_action_legal_envelope_mapping(
    *,
    action: str,
    envelope_component_is_affected: bool,
    protection_exemption_status: str = NO_APPLICABLE_EXEMPTION,
    legal_regime: str = CURRENT_EKM_REGIME,
) -> LegalPostStateDecision:
    """Separate action semantics from legal component requirements."""

    if action == AIR_TO_WATER_HP_ONLY:
        if envelope_component_is_affected:
            return LegalPostStateDecision(
                Q,
                ("HP_ONLY_ACTION_CONFLICTS_WITH_ENVELOPE_COMPONENT_AFFECTED_FLAG",),
            )
        return LegalPostStateDecision(
            "NO_ENVELOPE_LEGAL_U_TRIGGER_FROM_HP_ONLY_ACTION",
            (),
        )

    if action in {
        REFERENCE_ENVELOPE_RETROFIT,
        REFERENCE_ENVELOPE_RETROFIT_PLUS_AWHP,
    }:
        if not envelope_component_is_affected:
            return LegalPostStateDecision(
                Q,
                ("REFERENCE_ENVELOPE_ACTION_REQUIRES_EXPLICIT_AFFECTED_COMPONENT_SET",),
            )

        probe = current_legal_u_requirement(
            "EXTERNAL_WALL",
            affected_by_energy_saving_renovation=True,
            protection_exemption_status=protection_exemption_status,
            legal_regime=legal_regime,
        )
        if probe.status != QUALIFIED_CURRENT_LEGAL_U_REQUIREMENT:
            return LegalPostStateDecision(Q, probe.blockers)
        return LegalPostStateDecision(
            "QUALIFIED_ACTION_TO_CURRENT_LEGAL_ENVELOPE_REQUIREMENT",
            (),
        )

    return LegalPostStateDecision(
        Q,
        ("ACTION_TO_ENVELOPE_LEGAL_SCOPE_MAPPING_REQUIRED",),
    )


def assess_national_current_legal_u_surface(
    *,
    national_affected_component_assignment_materialized: bool,
    legal_exception_regime_materialized: bool,
    current_no_action_baseline_materialized: bool,
    component_area_surface_materialized: bool,
) -> LegalPostStateDecision:
    blockers: list[str] = []
    if not national_affected_component_assignment_materialized:
        blockers.append("NATIONAL_AFFECTED_ENVELOPE_COMPONENT_ASSIGNMENT_REQUIRED")
    if not legal_exception_regime_materialized:
        blockers.append("NATIONAL_LEGAL_ENVELOPE_EXCEPTION_REGIME_REQUIRED")
    if not current_no_action_baseline_materialized:
        blockers.append("CURRENT_NO_ACTION_BASELINE_U_SURFACE_REQUIRED")
    if not component_area_surface_materialized:
        blockers.append("COMPONENT_AREA_GEOMETRY_SURFACE_REQUIRED")

    if blockers:
        return LegalPostStateDecision(Q, tuple(blockers))

    return LegalPostStateDecision(
        "QUALIFIED_CURRENT_LEGAL_ACTION_CONDITIONED_U_SURFACE",
        (),
    )
