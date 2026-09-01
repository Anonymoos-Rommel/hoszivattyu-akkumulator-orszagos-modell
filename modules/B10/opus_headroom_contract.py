"""Fail-closed OPUS TITÁSZ consumption-side headroom contract.

OPUS publishes a weaker source-native schema than the MVM Démász P1 source:
station code, station name, current free capacity and five-year forecast free
capacity.  This module preserves that row identity and deliberately does not
invent voltage, N-1 capacity, peak load, aggregation or a cross-DSO assessment.
"""

from __future__ import annotations

import csv
import hashlib
import io
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from math import isfinite


class OpusHeadroomContractError(ValueError):
    """Fail-closed OPUS TITÁSZ headroom contract violation."""


OPUS_TITASZ_SOURCE_ID = "SRC-B10-OPUS-TITASZ-CONSUMPTION-HEADROOM-2026"
OPUS_TITASZ_LANDING_SOURCE_ID = "SRC-B10-OPUS-TITASZ-HEADROOM-LANDING-2026"
OPUS_TITASZ_LEGAL_SOURCE_ID = "SRC-B10-OPUS-TITASZ-LEGAL-2026"
OPUS_TITASZ_COMPANY_SOURCE_ID = "SRC-B10-OPUS-TITASZ-COMPANY-2026"
OPUS_TITASZ_SOURCE_REFS = (
    OPUS_TITASZ_SOURCE_ID,
    OPUS_TITASZ_LANDING_SOURCE_ID,
    OPUS_TITASZ_LEGAL_SOURCE_ID,
    OPUS_TITASZ_COMPANY_SOURCE_ID,
)
OPUS_TITASZ_PUBLISHER = "OPUS TITÁSZ Áramhálózati Zártkörűen Működő Részvénytársaság"
OPUS_TITASZ_SHORT_NAME = "OPUS TITÁSZ Zrt."
OPUS_TITASZ_DATASET_NAME = "Alállomások szabad kapacitásai"
OPUS_TITASZ_DATA_URL = (
    "https://www.opustitasz.hu/storage/documents/ugyfelek/halozati-szolgaltatasok/"
    "Al%C3%A1llom%C3%A1sok_szabad_kapacit%C3%A1sai.pdf"
)
OPUS_TITASZ_LANDING_URL = (
    "https://www.opustitasz.hu/ugyfelek/halozati-szolgaltatas-es-termekek/"
    "alallomasok-szabad-kapacitasai"
)
OPUS_TITASZ_LEGAL_URL = "https://www.opustitasz.hu/jogi-nyilatkozat"
OPUS_TITASZ_COMPANY_URL = "https://www.opustitasz.hu/kozszolgalati-informaciok"
OPUS_TITASZ_EFFECTIVE_DATE = "2026-07-22"
OPUS_TITASZ_SOURCE_REVISION = "EFFECTIVE_2026-07-22"
OPUS_TITASZ_SOURCE_PDF_SHA256 = "3550266167435880f2055497aa5da5d5a4d04240cbfaac4c1425c46b8f4e8e48"
REGION_SCHEME = "DSO_SUBSTATION"
SOURCE_SEMANTICS = "PUBLISHED_INDICATIVE_DSO_ESTIMATE_NOT_CONNECTION_AUTHORITY"
CONNECTION_AUTHORITY = "MGT_REQUIRED"
REUSE_CLEARED = "REUSE_CLEARED"
EXTERNAL_ONLY_REUSE_UNRESOLVED = "EXTERNAL_ONLY_REUSE_UNRESOLVED"
REUSE_RESTRICTED = "REUSE_RESTRICTED"
REUSE_UNKNOWN = "REUSE_UNKNOWN"
LICENSE_DECISIONS = {
    REUSE_CLEARED,
    EXTERNAL_ONLY_REUSE_UNRESOLVED,
    REUSE_RESTRICTED,
    REUSE_UNKNOWN,
}
VERIFIED_AGAINST_SOURCE = "VERIFIED_AGAINST_SOURCE"
UNVERIFIED_EXTRACTION = "UNVERIFIED_EXTRACTION"
EXTRACTION_VERIFICATIONS = {VERIFIED_AGAINST_SOURCE, UNVERIFIED_EXTRACTION}
SHA256_RE = re.compile(r"[0-9a-f]{64}")
NORMALIZED_HEADERS = (
    "station_code",
    "station_name",
    "free_capacity_current_mw",
    "free_capacity_5y_mw",
)
_VERIFIED_EXTRACTION_TOKEN = object()


def _source_text(value: object, field_name: str) -> str:
    if not isinstance(value, str) or not value or value != value.strip() or any(char in value for char in "\t\r\n"):
        raise OpusHeadroomContractError(f"{field_name} must be a non-empty source-native text field")
    if len(value) > 256:
        raise OpusHeadroomContractError(f"{field_name} exceeds the bounded source field length")
    return value


def _optional_nonnegative_number(value: object, field_name: str) -> float | None:
    if not isinstance(value, str):
        raise OpusHeadroomContractError(f"{field_name} must be a normalized text field")
    text = value.strip()
    if not text:
        return None
    try:
        number = float(text.replace(",", "."))
    except ValueError as exc:
        raise OpusHeadroomContractError(f"invalid numeric field: {field_name}") from exc
    if not isfinite(number) or number < 0:
        raise OpusHeadroomContractError(f"{field_name} must be finite and non-negative")
    return number


def _canonical_region_id(station_code: str, station_name: str) -> str:
    return f"OPUS_TITASZ:{station_code}:{station_name}"


@dataclass(frozen=True)
class OpusHeadroomProvenance:
    source_id: str
    publisher: str
    dataset_name: str
    source_url: str
    landing_url: str
    legal_url: str
    company_url: str
    retrieved_at: datetime
    source_effective_date: str
    source_revision: str
    license_decision: str
    raw_storage_policy: str
    extraction_verification: str
    source_pdf_sha256: str | None = None
    normalized_text_sha256: str | None = None

    def __post_init__(self) -> None:
        if self.source_id != OPUS_TITASZ_SOURCE_ID:
            raise OpusHeadroomContractError("provenance source_id must match the canonical OPUS data source")
        if self.publisher != OPUS_TITASZ_PUBLISHER or self.dataset_name != OPUS_TITASZ_DATASET_NAME:
            raise OpusHeadroomContractError("provenance source identity does not match the canonical OPUS contract")
        if self.source_url != OPUS_TITASZ_DATA_URL:
            raise OpusHeadroomContractError("source_url must be the canonical OPUS PDF")
        if self.landing_url != OPUS_TITASZ_LANDING_URL or self.legal_url != OPUS_TITASZ_LEGAL_URL or self.company_url != OPUS_TITASZ_COMPANY_URL:
            raise OpusHeadroomContractError("OPUS provenance URLs must match the canonical source family")
        if not isinstance(self.retrieved_at, datetime) or self.retrieved_at.tzinfo is None or self.retrieved_at.utcoffset() is None:
            raise OpusHeadroomContractError("retrieved_at must be timezone-aware")
        object.__setattr__(self, "retrieved_at", self.retrieved_at.astimezone(timezone.utc))
        if self.source_effective_date != OPUS_TITASZ_EFFECTIVE_DATE:
            raise OpusHeadroomContractError("source_effective_date does not match the acquired OPUS PDF")
        if self.source_revision != OPUS_TITASZ_SOURCE_REVISION:
            raise OpusHeadroomContractError("source_revision does not match the acquired OPUS PDF")
        if self.license_decision not in LICENSE_DECISIONS:
            raise OpusHeadroomContractError("invalid license_decision")
        if self.raw_storage_policy not in {"EXTERNAL_ONLY", "REPOSITORY_ALLOWED"}:
            raise OpusHeadroomContractError("invalid raw_storage_policy")
        if self.extraction_verification not in EXTRACTION_VERIFICATIONS:
            raise OpusHeadroomContractError("invalid extraction_verification")
        for field_name in ("source_pdf_sha256", "normalized_text_sha256"):
            value = getattr(self, field_name)
            if value is not None and not SHA256_RE.fullmatch(value):
                raise OpusHeadroomContractError(f"{field_name} must be lowercase SHA-256")
        if self.source_pdf_sha256 is not None and self.source_pdf_sha256 != OPUS_TITASZ_SOURCE_PDF_SHA256:
            raise OpusHeadroomContractError("source_pdf_sha256 does not match the acquired OPUS PDF revision")


@dataclass(frozen=True)
class OpusHeadroomRecord:
    station_code: str
    station_name: str
    free_capacity_current_mw: float | None
    free_capacity_5y_mw: float | None
    evidence_status: str
    source_refs: tuple[str, ...]
    provenance: OpusHeadroomProvenance | None = None
    region_scheme: str = REGION_SCHEME
    region_id: str = ""
    source_semantics: str = SOURCE_SEMANTICS
    connection_authority: str = CONNECTION_AUTHORITY
    _verification_token: object | None = field(default=None, repr=False, compare=False)

    @property
    def source_row_key(self) -> tuple[str, str]:
        return self.station_code, self.station_name

    def __post_init__(self) -> None:
        code = _source_text(self.station_code, "station_code")
        name = _source_text(self.station_name, "station_name")
        object.__setattr__(self, "station_code", code)
        object.__setattr__(self, "station_name", name)
        expected_region = _canonical_region_id(code, name)
        if self.region_scheme != REGION_SCHEME:
            raise OpusHeadroomContractError("OPUS supports only DSO_SUBSTATION grain")
        if self.region_id and self.region_id != expected_region:
            raise OpusHeadroomContractError("region_id must remain the exact OPUS source row key")
        object.__setattr__(self, "region_id", expected_region)
        if self.source_semantics != SOURCE_SEMANTICS:
            raise OpusHeadroomContractError("source semantics must preserve the indicative-estimate caveat")
        if self.connection_authority != CONNECTION_AUTHORITY:
            raise OpusHeadroomContractError("published headroom cannot replace individual MGT authority")
        if self.evidence_status not in {"DER", "Q"}:
            raise OpusHeadroomContractError("OPUS normalized evidence must be DER or Q; it is never OBS")
        if tuple(self.source_refs) != OPUS_TITASZ_SOURCE_REFS:
            raise OpusHeadroomContractError("OPUS source_refs must bind the complete canonical source family")
        values = (self.free_capacity_current_mw, self.free_capacity_5y_mw)
        for field_name, value in zip(("free_capacity_current_mw", "free_capacity_5y_mw"), values):
            if value is not None and (isinstance(value, bool) or not isinstance(value, (int, float)) or not isfinite(value) or value < 0):
                raise OpusHeadroomContractError(f"{field_name} must be finite and non-negative")
        if self.evidence_status == "DER":
            if self._verification_token is not _VERIFIED_EXTRACTION_TOKEN:
                raise OpusHeadroomContractError("DER rows must be created by the canonical verified extraction path")
            if self.provenance is None:
                raise OpusHeadroomContractError("DER rows require provenance")
            if self.provenance.license_decision != REUSE_CLEARED:
                raise OpusHeadroomContractError("DER rows require explicit reuse clearance")
            if self.provenance.extraction_verification != VERIFIED_AGAINST_SOURCE:
                raise OpusHeadroomContractError("DER rows require extraction verification against the official source")
            if self.provenance.source_pdf_sha256 != OPUS_TITASZ_SOURCE_PDF_SHA256 or self.provenance.normalized_text_sha256 is None:
                raise OpusHeadroomContractError("DER rows require the exact source-PDF revision and normalized-text checksum")
            if any(value is None for value in values):
                raise OpusHeadroomContractError("DER rows require complete source-native capacity fields")


@dataclass(frozen=True)
class OpusHeadroomBatch:
    records: tuple[OpusHeadroomRecord, ...]
    source_refs: tuple[str, ...]
    evidence_status: str
    aggregation_authority: str = "NONE_NON_ADDITIVE"

    def __post_init__(self) -> None:
        if not self.records:
            raise OpusHeadroomContractError("OPUS batch requires at least one explicit source row")
        if tuple(self.source_refs) != OPUS_TITASZ_SOURCE_REFS:
            raise OpusHeadroomContractError("OPUS batch source_refs must bind the canonical source family")
        if self.evidence_status not in {"DER", "Q"}:
            raise OpusHeadroomContractError("OPUS batch evidence_status must be DER or Q")
        if self.aggregation_authority != "NONE_NON_ADDITIVE":
            raise OpusHeadroomContractError("OPUS P2 does not authorize headroom aggregation")
        expected_status = "Q" if any(row.evidence_status == "Q" for row in self.records) else "DER"
        if self.evidence_status != expected_status:
            raise OpusHeadroomContractError("OPUS batch evidence_status must propagate row uncertainty")
        seen: set[tuple[str, str]] = set()
        for row in self.records:
            if row.source_row_key in seen:
                raise OpusHeadroomContractError(f"duplicate OPUS source row key: {row.source_row_key!r}")
            seen.add(row.source_row_key)


def parse_opus_titasz_consumption_headroom_text(
    normalized_tsv_text: str,
    *,
    provenance: OpusHeadroomProvenance,
) -> OpusHeadroomBatch:
    """Parse an external OPUS transcription without inventing absent fields."""

    if not isinstance(normalized_tsv_text, str) or not normalized_tsv_text.strip():
        raise OpusHeadroomContractError("normalized TSV text is required")
    exact_hash = hashlib.sha256(normalized_tsv_text.encode("utf-8")).hexdigest()
    if provenance.normalized_text_sha256 is not None and provenance.normalized_text_sha256 != exact_hash:
        raise OpusHeadroomContractError("normalized text does not match the declared SHA-256")
    reader = csv.DictReader(io.StringIO(normalized_tsv_text), delimiter="\t")
    if tuple(reader.fieldnames or ()) != NORMALIZED_HEADERS:
        raise OpusHeadroomContractError("normalized TSV headers do not match the canonical OPUS contract")
    can_promote = (
        provenance.license_decision == REUSE_CLEARED
        and provenance.extraction_verification == VERIFIED_AGAINST_SOURCE
        and provenance.source_pdf_sha256 == OPUS_TITASZ_SOURCE_PDF_SHA256
        and provenance.normalized_text_sha256 == exact_hash
        and provenance.source_effective_date == OPUS_TITASZ_EFFECTIVE_DATE
        and provenance.source_revision == OPUS_TITASZ_SOURCE_REVISION
    )
    records: list[OpusHeadroomRecord] = []
    for row_number, row in enumerate(reader, start=2):
        if None in row:
            raise OpusHeadroomContractError(f"row {row_number}: unexpected normalized columns")
        code = _source_text(row.get("station_code"), "station_code")
        name = _source_text(row.get("station_name"), "station_name")
        current = _optional_nonnegative_number(row.get("free_capacity_current_mw"), "free_capacity_current_mw")
        future = _optional_nonnegative_number(row.get("free_capacity_5y_mw"), "free_capacity_5y_mw")
        complete = current is not None and future is not None
        status = "DER" if can_promote and complete else "Q"
        records.append(
            OpusHeadroomRecord(
                station_code=code,
                station_name=name,
                free_capacity_current_mw=current,
                free_capacity_5y_mw=future,
                evidence_status=status,
                source_refs=OPUS_TITASZ_SOURCE_REFS,
                provenance=provenance,
                _verification_token=_VERIFIED_EXTRACTION_TOKEN if status == "DER" else None,
            )
        )
    if not records:
        raise OpusHeadroomContractError("normalized TSV contains no OPUS source rows")
    status = "Q" if any(row.evidence_status == "Q" for row in records) else "DER"
    return OpusHeadroomBatch(tuple(records), OPUS_TITASZ_SOURCE_REFS, status)
