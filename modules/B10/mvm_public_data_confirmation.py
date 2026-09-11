"""Fail-closed contract for the B10-P66 MVM public-data confirmation.

P66 records only that the MVM response confirms the public-data status of
DSO distribution-territory information and identifies its publication family.
It does not turn public availability into reuse permission, exact boundary
geometry, technical authority, completeness, or model admission.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
import re


class MvmPublicDataConfirmationError(ValueError):
    """Raised when the bounded MVM confirmation is overstated."""


PUBLIC_DATA_CONFIRMED = "PUBLIC_DATA_CONFIRMED"
QUALIFIED_PUBLIC_DATA_CONFIRMATION = "QUALIFIED_PUBLIC_DATA_CONFIRMATION"
PRIVATE_ARCHIVE_ONLY = "PRIVATE_ARCHIVE_ONLY"
DSO_DISTRIBUTION_TERRITORY = "DSO_DISTRIBUTION_TERRITORY"
OPERATING_LICENCE_AND_BUSINESS_RULES = "OPERATING_LICENCE_AND_BUSINESS_RULES"
INFORMATIVE = "INFORMATIVE"

EXPECTED_OPERATORS = frozenset({"MVM_EMASZ", "MVM_DEMASZ"})
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


@dataclass(frozen=True)
class MvmPublicDataConfirmation:
    confirmation_id: str
    covered_operator_ids: frozenset[str]
    issuer: str
    request_date: str
    response_date: str
    docket_id: str
    data_scope: str
    public_data_status: str
    referred_source_family: str
    publication_character: str
    private_evidence_storage: str
    private_evidence_sha256: str
    private_evidence_committed: bool = False
    raw_correspondence_committed: bool = False
    personal_data_committed: bool = False
    source_binary_committed: bool = False
    explicit_reuse_permission_claimed: bool = False
    exact_boundary_geometry_claimed: bool = False
    source_truth_authority_claimed: bool = False
    completeness_authority_claimed: bool = False
    model_admission_claimed: bool = False


def _parse_iso_date(value: str, field_name: str) -> date:
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise MvmPublicDataConfirmationError(
            f"INVALID_{field_name.upper()}"
        ) from exc


def validate_mvm_public_data_confirmation(
    confirmation: MvmPublicDataConfirmation,
) -> str:
    """Validate the narrow public-data confirmation and privacy boundary."""

    if not confirmation.confirmation_id.strip():
        raise MvmPublicDataConfirmationError("MISSING_CONFIRMATION_ID")
    if confirmation.covered_operator_ids != EXPECTED_OPERATORS:
        raise MvmPublicDataConfirmationError("OPERATOR_SCOPE_MISMATCH")
    if not confirmation.issuer.strip():
        raise MvmPublicDataConfirmationError("MISSING_ISSUER")
    if not confirmation.docket_id.strip():
        raise MvmPublicDataConfirmationError("MISSING_DOCKET_ID")

    requested = _parse_iso_date(confirmation.request_date, "request_date")
    responded = _parse_iso_date(confirmation.response_date, "response_date")
    if responded < requested:
        raise MvmPublicDataConfirmationError("RESPONSE_PRECEDES_REQUEST")

    if confirmation.data_scope != DSO_DISTRIBUTION_TERRITORY:
        raise MvmPublicDataConfirmationError("PUBLIC_DATA_SCOPE_OVERREACH")
    if confirmation.public_data_status != PUBLIC_DATA_CONFIRMED:
        raise MvmPublicDataConfirmationError("PUBLIC_DATA_STATUS_NOT_CONFIRMED")
    if confirmation.referred_source_family != OPERATING_LICENCE_AND_BUSINESS_RULES:
        raise MvmPublicDataConfirmationError("SOURCE_FAMILY_MISMATCH")
    if confirmation.publication_character != INFORMATIVE:
        raise MvmPublicDataConfirmationError("PUBLICATION_CHARACTER_MISMATCH")

    if confirmation.private_evidence_storage != PRIVATE_ARCHIVE_ONLY:
        raise MvmPublicDataConfirmationError("PRIVATE_EVIDENCE_STORAGE_NOT_PRIVATE")
    if not _SHA256_RE.fullmatch(confirmation.private_evidence_sha256):
        raise MvmPublicDataConfirmationError("INVALID_PRIVATE_EVIDENCE_SHA256")

    if confirmation.private_evidence_committed:
        raise MvmPublicDataConfirmationError("PRIVATE_EVIDENCE_MUST_NOT_BE_COMMITTED")
    if confirmation.raw_correspondence_committed:
        raise MvmPublicDataConfirmationError("RAW_CORRESPONDENCE_MUST_NOT_BE_COMMITTED")
    if confirmation.personal_data_committed:
        raise MvmPublicDataConfirmationError("PERSONAL_DATA_MUST_NOT_BE_COMMITTED")
    if confirmation.source_binary_committed:
        raise MvmPublicDataConfirmationError("PRIVATE_SOURCE_BINARY_MUST_NOT_BE_COMMITTED")

    if confirmation.explicit_reuse_permission_claimed:
        raise MvmPublicDataConfirmationError("PUBLIC_DATA_IS_NOT_EXPLICIT_REUSE_PERMISSION")
    if confirmation.exact_boundary_geometry_claimed:
        raise MvmPublicDataConfirmationError("PUBLIC_TERRITORY_DATA_IS_NOT_EXACT_BOUNDARY_GEOMETRY")
    if confirmation.source_truth_authority_claimed:
        raise MvmPublicDataConfirmationError("PUBLIC_STATUS_IS_NOT_SOURCE_TRUTH_AUTHORITY")
    if confirmation.completeness_authority_claimed:
        raise MvmPublicDataConfirmationError("PUBLIC_STATUS_IS_NOT_COMPLETENESS_AUTHORITY")
    if confirmation.model_admission_claimed:
        raise MvmPublicDataConfirmationError("PUBLIC_STATUS_IS_NOT_MODEL_ADMISSION")

    return QUALIFIED_PUBLIC_DATA_CONFIRMATION


def confirmation_grants_reuse_permission(_: MvmPublicDataConfirmation) -> bool:
    """Public-data status alone is not an explicit reuse licence."""

    return False


def confirmation_grants_exact_boundary_geometry(_: MvmPublicDataConfirmation) -> bool:
    """The informative public source family does not self-prove exact geometry."""

    return False


def confirmation_grants_model_admission(_: MvmPublicDataConfirmation) -> bool:
    """The confirmation never self-authorizes model or programme use."""

    return False
