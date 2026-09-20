"""B06-P64 realized retrofit completion gate.

This gate separates physical completion evidence from energy-outcome evidence.

FINAL INVOICE != ENERGY OUTCOME
FINAL HET != COMPLETION SCOPE
PLANNED POST != REALIZED POST
S1 READY = REALIZED COMPLETION + LINKED OUTCOME
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date


Q = "Q"
QUALIFIED = "QUALIFIED"
BLOCKED = "BLOCKED"
OBS = "OBS"


@dataclass(frozen=True)
class RealizedCompletionEvidence:
    record_id: str
    intervention_id: str
    project_id: str
    site_link_id: str

    completion_evidence_status: str
    physical_completion_date: str
    final_het_date: str

    contract_scope_ids: tuple[str, ...]
    realized_scope_ids: tuple[str, ...]
    scope_amendment_approved: bool = False
    scope_amendment_refs: tuple[str, ...] = ()

    final_invoice_refs: tuple[str, ...] = ()
    performance_confirmation_refs: tuple[str, ...] = ()
    final_het_refs: tuple[str, ...] = ()
    final_energy_calculation_refs: tuple[str, ...] = ()

    verifier_id: str = ""
    final_het_record_link: str = ""
    final_het_site_link: str = ""

    physical_completion_declared: bool = False
    reproducible_repository_binding: bool = False


@dataclass(frozen=True)
class RealizedCompletionDecision:
    status: str
    evidence_status: str
    reasons: tuple[str, ...]


def _refs_ok(refs: tuple[str, ...]) -> bool:
    return bool(refs) and all(isinstance(ref, str) and ref.strip() for ref in refs)


def _parse_iso_date(value: str, name: str, reasons: list[str]) -> date | None:
    if not value.strip():
        reasons.append(f"{name}_MISSING")
        return None
    try:
        return date.fromisoformat(value)
    except ValueError:
        reasons.append(f"{name}_INVALID")
        return None


def assess_realized_completion(
    evidence: RealizedCompletionEvidence,
) -> RealizedCompletionDecision:
    reasons: list[str] = []

    if not evidence.record_id.strip():
        reasons.append("RECORD_ID_MISSING")
    if not evidence.intervention_id.strip():
        reasons.append("INTERVENTION_ID_MISSING")
    if not evidence.project_id.strip():
        reasons.append("PROJECT_ID_MISSING")
    if not evidence.site_link_id.strip():
        reasons.append("SITE_LINK_ID_MISSING")

    if evidence.completion_evidence_status != OBS:
        reasons.append("COMPLETION_EVIDENCE_MUST_BE_OBS")

    completion_date = _parse_iso_date(
        evidence.physical_completion_date,
        "PHYSICAL_COMPLETION_DATE",
        reasons,
    )
    het_date = _parse_iso_date(evidence.final_het_date, "FINAL_HET_DATE", reasons)

    if completion_date is not None and het_date is not None and het_date < completion_date:
        reasons.append("FINAL_HET_PRECEDES_PHYSICAL_COMPLETION")

    if not evidence.contract_scope_ids:
        reasons.append("CONTRACT_SCOPE_MISSING")
    if not evidence.realized_scope_ids:
        reasons.append("REALIZED_SCOPE_MISSING")

    contract_scope = set(evidence.contract_scope_ids)
    realized_scope = set(evidence.realized_scope_ids)
    if contract_scope != realized_scope:
        if not evidence.scope_amendment_approved:
            return RealizedCompletionDecision(
                BLOCKED,
                evidence.completion_evidence_status,
                ("UNAPPROVED_SCOPE_DEVIATION",),
            )
        if not _refs_ok(evidence.scope_amendment_refs):
            reasons.append("SCOPE_AMENDMENT_REFS_MISSING")

    if not _refs_ok(evidence.final_invoice_refs):
        reasons.append("FINAL_INVOICE_REFS_MISSING")
    if not _refs_ok(evidence.performance_confirmation_refs):
        reasons.append("PERFORMANCE_CONFIRMATION_REFS_MISSING")
    if not _refs_ok(evidence.final_het_refs):
        reasons.append("FINAL_HET_REFS_MISSING")
    if not _refs_ok(evidence.final_energy_calculation_refs):
        reasons.append("FINAL_ENERGY_CALCULATION_REFS_MISSING")

    if not evidence.verifier_id.strip():
        reasons.append("VERIFIER_ID_MISSING")
    if evidence.final_het_record_link != evidence.record_id:
        reasons.append("FINAL_HET_RECORD_LINK_MISMATCH")
    if evidence.final_het_site_link != evidence.site_link_id:
        reasons.append("FINAL_HET_SITE_LINK_MISMATCH")

    if not evidence.physical_completion_declared:
        reasons.append("PHYSICAL_COMPLETION_NOT_DECLARED")
    if not evidence.reproducible_repository_binding:
        reasons.append("NO_REPRODUCIBLE_REPOSITORY_BINDING")

    if reasons:
        return RealizedCompletionDecision(
            Q,
            evidence.completion_evidence_status,
            tuple(reasons),
        )

    return RealizedCompletionDecision(
        QUALIFIED,
        evidence.completion_evidence_status,
        (),
    )
