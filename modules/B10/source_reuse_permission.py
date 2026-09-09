"""Fail-closed contract for third-party source reuse permissions.

B10-P61 records permission metadata without publishing private correspondence.
The permission decision is intentionally separate from source truth, currentness,
coverage, and model-admission authority.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
import re


class SourceReusePermissionError(ValueError):
    """Raised when a source-reuse permission record overstates its authority."""


USE_ALLOWED = "USE_ALLOWED"
QUALIFIED_SOURCE_REUSE_PERMISSION = "QUALIFIED_SOURCE_REUSE_PERMISSION"
PRIVATE_ARCHIVE_ONLY = "PRIVATE_ARCHIVE_ONLY"
OPERATING_LICENCE_GEOGRAPHIC_DATA = "OPERATING_LICENCE_GEOGRAPHIC_DATA"

_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


@dataclass(frozen=True)
class SourceReusePermission:
    permission_id: str
    operator_id: str
    issuer: str
    represented_entity: str
    request_date: str
    response_date: str
    docket_id: str
    permission_scope: str
    permission_decision: str
    private_evidence_storage: str
    private_evidence_sha256: str
    private_evidence_committed: bool = False
    raw_correspondence_committed: bool = False
    personal_data_committed: bool = False
    source_binary_committed: bool = False
    scope_expansion_allowed: bool = False


def _parse_iso_date(value: str, field_name: str) -> date:
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise SourceReusePermissionError(f"INVALID_{field_name.upper()}") from exc


def validate_source_reuse_permission(permission: SourceReusePermission) -> str:
    """Validate the narrow permission and private-evidence boundary.

    A successful result proves only that a bounded reuse permission is recorded.
    It does not prove that the referenced public data are correct, complete,
    current, representative, or sufficient for any B10 model claim.
    """

    if not permission.permission_id.strip():
        raise SourceReusePermissionError("MISSING_PERMISSION_ID")
    if not permission.operator_id.strip():
        raise SourceReusePermissionError("MISSING_OPERATOR_ID")
    if not permission.issuer.strip():
        raise SourceReusePermissionError("MISSING_ISSUER")
    if not permission.represented_entity.strip():
        raise SourceReusePermissionError("MISSING_REPRESENTED_ENTITY")
    if not permission.docket_id.strip():
        raise SourceReusePermissionError("MISSING_DOCKET_ID")

    requested = _parse_iso_date(permission.request_date, "request_date")
    responded = _parse_iso_date(permission.response_date, "response_date")
    if responded < requested:
        raise SourceReusePermissionError("RESPONSE_PRECEDES_REQUEST")

    if permission.permission_scope != OPERATING_LICENCE_GEOGRAPHIC_DATA:
        raise SourceReusePermissionError("PERMISSION_SCOPE_OVERREACH")
    if permission.permission_decision != USE_ALLOWED:
        raise SourceReusePermissionError("PERMISSION_NOT_ALLOWED")
    if permission.private_evidence_storage != PRIVATE_ARCHIVE_ONLY:
        raise SourceReusePermissionError("PRIVATE_EVIDENCE_STORAGE_NOT_PRIVATE")
    if not _SHA256_RE.fullmatch(permission.private_evidence_sha256):
        raise SourceReusePermissionError("INVALID_PRIVATE_EVIDENCE_SHA256")

    if permission.private_evidence_committed:
        raise SourceReusePermissionError("PRIVATE_EVIDENCE_MUST_NOT_BE_COMMITTED")
    if permission.raw_correspondence_committed:
        raise SourceReusePermissionError("RAW_CORRESPONDENCE_MUST_NOT_BE_COMMITTED")
    if permission.personal_data_committed:
        raise SourceReusePermissionError("PERSONAL_DATA_MUST_NOT_BE_COMMITTED")
    if permission.source_binary_committed:
        raise SourceReusePermissionError("PRIVATE_SOURCE_BINARY_MUST_NOT_BE_COMMITTED")
    if permission.scope_expansion_allowed:
        raise SourceReusePermissionError("PERMISSION_SCOPE_EXPANSION_FORBIDDEN")

    return QUALIFIED_SOURCE_REUSE_PERMISSION


def permission_grants_source_truth_authority(_: SourceReusePermission) -> bool:
    """A reuse permission never self-authorizes the factual source claim."""

    return False


def permission_grants_model_admission(_: SourceReusePermission) -> bool:
    """A reuse permission never self-authorizes model or programme use."""

    return False
