"""B02-P59 site legal / delivery gate for heat-pump installation.

Permit / notification / siting clearance is not a building-physics property and
must not be treated as a B02 current-stock technical-readiness field.

The correct decision grain is the actual site + proposed installation:
national building rules + local townscape rules + property/condominium/heritage
constraints + noise/siting/water-disposal requirements.

NO CURRENT PERMIT DATA != TECHNICALLY INELIGIBLE
SITE CLEARANCE UNKNOWN != PASS
SITE CLEARANCE PENDING != FAIL
FINAL REFUSAL WITH NO ADMITTED ALTERNATIVE -> BLOCKED
"""

from __future__ import annotations

from dataclasses import dataclass


Q = "Q"
QUALIFIED = "QUALIFIED"
BLOCKED = "BLOCKED"

NOT_REQUIRED = "NOT_REQUIRED"
APPROVED = "APPROVED"
PENDING = "PENDING"
REFUSED = "REFUSED"
CLEARANCE_STATUSES = frozenset({NOT_REQUIRED, APPROVED, PENDING, REFUSED})


@dataclass(frozen=True)
class SiteLegalDeliveryCandidate:
    record_id: str
    national_building_rule_checked: bool
    local_townscape_rule_checked: bool
    local_clearance_status: str
    heritage_or_protected_status_checked: bool
    property_or_condominium_consent_status: str
    outdoor_unit_siting_documented: bool
    noise_compliance_basis_documented: bool
    condensate_or_water_disposal_documented: bool
    alternative_compliant_design_available: bool
    evidence_refs_present: bool
    reproducible_repository_binding: bool


@dataclass(frozen=True)
class SiteLegalDeliveryDecision:
    status: str
    reasons: tuple[str, ...]


def assess_site_legal_delivery(
    candidate: SiteLegalDeliveryCandidate,
) -> SiteLegalDeliveryDecision:
    reasons: list[str] = []

    if not candidate.record_id.strip():
        reasons.append("RECORD_ID_MISSING")

    if not candidate.national_building_rule_checked:
        reasons.append("NATIONAL_BUILDING_RULE_NOT_CHECKED")

    if not candidate.local_townscape_rule_checked:
        reasons.append("LOCAL_TOWNSCAPE_RULE_NOT_CHECKED")

    if candidate.local_clearance_status not in CLEARANCE_STATUSES:
        reasons.append("LOCAL_CLEARANCE_STATUS_UNKNOWN")
    elif candidate.local_clearance_status == PENDING:
        reasons.append("LOCAL_CLEARANCE_PENDING")
    elif candidate.local_clearance_status == REFUSED:
        if not candidate.alternative_compliant_design_available:
            return SiteLegalDeliveryDecision(
                BLOCKED, ("LOCAL_CLEARANCE_REFUSED_NO_ALTERNATIVE",)
            )
        reasons.append("ALTERNATIVE_DESIGN_REQUIRES_NEW_CLEARANCE")

    if not candidate.heritage_or_protected_status_checked:
        reasons.append("HERITAGE_OR_PROTECTED_STATUS_NOT_CHECKED")

    if candidate.property_or_condominium_consent_status not in CLEARANCE_STATUSES:
        reasons.append("PROPERTY_OR_CONDOMINIUM_CONSENT_STATUS_UNKNOWN")
    elif candidate.property_or_condominium_consent_status == PENDING:
        reasons.append("PROPERTY_OR_CONDOMINIUM_CONSENT_PENDING")
    elif candidate.property_or_condominium_consent_status == REFUSED:
        if not candidate.alternative_compliant_design_available:
            return SiteLegalDeliveryDecision(
                BLOCKED, ("PROPERTY_OR_CONDOMINIUM_CONSENT_REFUSED_NO_ALTERNATIVE",)
            )
        reasons.append("ALTERNATIVE_DESIGN_REQUIRES_NEW_PROPERTY_CONSENT")

    if not candidate.outdoor_unit_siting_documented:
        reasons.append("OUTDOOR_UNIT_SITING_MISSING")

    if not candidate.noise_compliance_basis_documented:
        reasons.append("NOISE_COMPLIANCE_BASIS_MISSING")

    if not candidate.condensate_or_water_disposal_documented:
        reasons.append("CONDENSATE_OR_WATER_DISPOSAL_MISSING")

    if not candidate.evidence_refs_present:
        reasons.append("EVIDENCE_REFS_MISSING")

    if not candidate.reproducible_repository_binding:
        reasons.append("NO_REPRODUCIBLE_REPOSITORY_BINDING")

    if reasons:
        return SiteLegalDeliveryDecision(Q, tuple(reasons))

    return SiteLegalDeliveryDecision(QUALIFIED, ())
