"""Fail-closed B10 consumption-side DSO headroom contract.

This slice is deliberately narrow. It normalizes an externally acquired and
independently verified transcription of the official MVM DEMASZ consumption-side
free-capacity publication. It does not parse or redistribute the source PDF,
aggregate substations, map counties to DSO nodes, infer a B08/B09 nodal handoff,
replace an individual MGT, or create reinforcement/CAPEX authority.

Because the official publication is itself a DSO calculation/estimate and this
runtime consumes a normalized transcription rather than source-native PDF bytes,
verified rows are DER, never OBS. Unverified or reuse-uncleared rows remain Q.
"""

from __future__ import annotations

import csv
import hashlib
import io
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from math import isfinite
from typing import Iterable


class B10HeadroomContractError(ValueError):
    """Fail-closed B10 DSO-headroom contract violation."""


MVM_DEMASZ_SOURCE_ID = "SRC-B10-MVM-DEMASZ-CONSUMPTION-HEADROOM-2026"
MVM_DEMASZ_METHOD_SOURCE_ID = "SRC-B10-MVM-DEMASZ-HEADROOM-METHOD-2026"
MVM_DEMASZ_PUBLISHER = "MVM DEMASZ Aramhalozati Kft."
MVM_DEMASZ_DATASET_NAME = "MVM DEMASZ consumption-purpose free capacities"
MVM_DEMASZ_DATA_URL = "https://mvmhalozat.hu/attachments/41914"
MVM_DEMASZ_METHOD_URL = "https://mvmhalozat.hu/attachments/41913"
MVM_DEMASZ_OPERATOR = "DEMASZ"
REGION_SCHEME = "DSO_SUBSTATION"
SOURCE_SEMANTICS = "PUBLISHED_INDICATIVE_DSO_ESTIMATE_NOT_CONNECTION_AUTHORITY"
CONNECTION_AUTHORITY = "MGT_REQUIRED"

CURRENT = "CURRENT"
FIVE_YEAR = "FIVE_YEAR"
HORIZONS = {CURRENT, FIVE_YEAR}

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
SOURCE_REVISION_NOT_PROVIDED = "NOT_PROVIDED_BY_SOURCE"
SHA256_RE = re.compile(r"[0-9a-f]{64}")
STATION_CODE_RE = re.compile(r"[A-Z0-9]{4}")

NORMALIZED_HEADERS = (
    "network_operator",
    "station_name",
    "station_code",
    "n1_capacity_current_mw",
    "n1_capacity_5y_mw",
    "voltage_kv",
    "winter_evening_load_current_mw",
    "free_capacity_current_mw",
    "winter_evening_load_5y_mw",
    "free_capacity_5y_mw",
)

_VERIFIED_EXTRACTION_TOKEN = object()


def _finite_nonnegative(value: float, field_name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not isfinite(value) or value < 0:
        raise B10HeadroomContractError(f"{field_name} must be finite and non-negative")
    return float(value)


def _parse_number(value: str, field_name: str) -> float:
    if not isinstance(value, str) or not value.strip():
        raise B10HeadroomContractError(f"missing normalized field: {field_name}")
    try:
        number = float(value.strip())
    except ValueError as exc:
        raise B10HeadroomContractError(f"invalid numeric field: {field_name}") from exc
    return _finite_nonnegative(number, field_name)


def _canonical_region_id(station_code: str, voltage_kv: float) -> str:
    voltage = int(voltage_kv) if float(voltage_kv).is_integer() else voltage_kv
    return f"MVM_DEMASZ:{station_code}:{voltage}KV"


@dataclass(frozen=True)
class DsoHeadroomProvenance:
    source_id: str
    publisher: str
    dataset_name: str
    source_url: str
    methodology_source_id: str
    methodology_url: str
    retrieved_at: datetime
    license_decision: str
    raw_storage_policy: str
    extraction_verification: str
    source_pdf_sha256: str | None = None
    normalized_text_sha256: str | None = None
    source_revision: str = SOURCE_REVISION_NOT_PROVIDED

    def __post_init__(self) -> None:
        if self.source_id != MVM_DEMASZ_SOURCE_ID:
            raise B10HeadroomContractError("provenance source_id must match the canonical MVM DEMASZ data source")
        if self.publisher != MVM_DEMASZ_PUBLISHER or self.dataset_name != MVM_DEMASZ_DATASET_NAME:
            raise B10HeadroomContractError("provenance source identity does not match the canonical MVM DEMASZ contract")
        if self.source_url != MVM_DEMASZ_DATA_URL:
            raise B10HeadroomContractError("source_url must be the canonical MVM DEMASZ capacity publication")
        if self.methodology_source_id != MVM_DEMASZ_METHOD_SOURCE_ID or self.methodology_url != MVM_DEMASZ_METHOD_URL:
            raise B10HeadroomContractError("methodology provenance must match the canonical MVM DEMASZ method source")
        if not isinstance(self.retrieved_at, datetime) or self.retrieved_at.tzinfo is None or self.retrieved_at.utcoffset() is None:
            raise B10HeadroomContractError("retrieved_at must be timezone-aware")
        object.__setattr__(self, "retrieved_at", self.retrieved_at.astimezone(timezone.utc))
        if self.license_decision not in LICENSE_DECISIONS:
            raise B10HeadroomContractError("invalid license_decision")
        if self.raw_storage_policy not in {"EXTERNAL_ONLY", "REPOSITORY_ALLOWED"}:
            raise B10HeadroomContractError("invalid raw_storage_policy")
        if self.extraction_verification not in EXTRACTION_VERIFICATIONS:
            raise B10HeadroomContractError("invalid extraction_verification")
        if not isinstance(self.source_revision, str) or not self.source_revision.strip():
            raise B10HeadroomContractError("source_revision is required or must be NOT_PROVIDED_BY_SOURCE")
        for field_name in ("source_pdf_sha256", "normalized_text_sha256"):
            value = getattr(self, field_name)
            if value is not None and not SHA256_RE.fullmatch(value):
                raise B10HeadroomContractError(f"{field_name} must be lowercase SHA-256")


@dataclass(frozen=True)
class DsoHeadroomRecord:
    station_name: str
    station_code: str
    voltage_kv: float
    horizon: str
    n_minus_1_capacity_mw: float | None
    winter_evening_peak_load_mw: float | None
    theoretical_free_capacity_mw: float | None
    evidence_status: str
    source_refs: tuple[str, ...]
    provenance: DsoHeadroomProvenance | None = None
    region_scheme: str = REGION_SCHEME
    region_id: str = ""
    source_semantics: str = SOURCE_SEMANTICS
    connection_authority: str = CONNECTION_AUTHORITY
    _verification_token: object | None = field(default=None, repr=False, compare=False)

    def __post_init__(self) -> None:
        if not isinstance(self.station_name, str) or not self.station_name.strip():
            raise B10HeadroomContractError("station_name is required")
        if not isinstance(self.station_code, str) or not STATION_CODE_RE.fullmatch(self.station_code):
            raise B10HeadroomContractError("station_code must be a four-character source station code")
        voltage = _finite_nonnegative(self.voltage_kv, "voltage_kv")
        if voltage <= 0:
            raise B10HeadroomContractError("voltage_kv must be positive")
        object.__setattr__(self, "voltage_kv", voltage)
        if self.horizon not in HORIZONS:
            raise B10HeadroomContractError("horizon must be CURRENT or FIVE_YEAR")
        if self.region_scheme != REGION_SCHEME:
            raise B10HeadroomContractError("B10-P1 supports only DSO_SUBSTATION grain")
        canonical_region = _canonical_region_id(self.station_code, voltage)
        if self.region_id and self.region_id != canonical_region:
            raise B10HeadroomContractError("region_id must remain the canonical DSO substation/voltage key")
        object.__setattr__(self, "region_id", canonical_region)
        if self.source_semantics != SOURCE_SEMANTICS:
            raise B10HeadroomContractError("source semantics must preserve the indicative-estimate caveat")
        if self.connection_authority != CONNECTION_AUTHORITY:
            raise B10HeadroomContractError("published headroom cannot replace individual MGT authority")
        if self.evidence_status not in {"DER", "Q"}:
            raise B10HeadroomContractError("normalized B10 headroom evidence must be DER or Q; it is never OBS")
        if isinstance(self.source_refs, str) or not self.source_refs or any(not isinstance(ref, str) or not ref.strip() for ref in self.source_refs):
            raise B10HeadroomContractError("source_refs must be a non-empty collection")
        values = (
            self.n_minus_1_capacity_mw,
            self.winter_evening_peak_load_mw,
            self.theoretical_free_capacity_mw,
        )
        for field_name, value in zip(
            ("n_minus_1_capacity_mw", "winter_evening_peak_load_mw", "theoretical_free_capacity_mw"),
            values,
        ):
            if value is not None:
                _finite_nonnegative(value, field_name)
        if self.evidence_status == "DER":
            if self._verification_token is not _VERIFIED_EXTRACTION_TOKEN:
                raise B10HeadroomContractError("DER rows must be created by the canonical verified extraction path")
            if self.provenance is None:
                raise B10HeadroomContractError("DER rows require provenance")
            if self.provenance.license_decision != REUSE_CLEARED:
                raise B10HeadroomContractError("DER rows require explicit reuse clearance")
            if self.provenance.extraction_verification != VERIFIED_AGAINST_SOURCE:
                raise B10HeadroomContractError("DER rows require extraction verification against the official source")
            if self.provenance.source_pdf_sha256 is None or self.provenance.normalized_text_sha256 is None:
                raise B10HeadroomContractError("DER rows require source-PDF and normalized-text checksums")
            if any(value is None for value in values):
                raise B10HeadroomContractError("DER rows require complete published numeric fields")
            if tuple(self.source_refs) != (MVM_DEMASZ_SOURCE_ID, MVM_DEMASZ_METHOD_SOURCE_ID):
                raise B10HeadroomContractError("DER source_refs must bind the data and methodology sources")
        elif all(value is None for value in values):
            pass


@dataclass(frozen=True)
class DsoHeadroomBatch:
    records: tuple[DsoHeadroomRecord, ...]
    source_refs: tuple[str, ...]
    evidence_status: str
    aggregation_authority: str = "NONE_NON_ADDITIVE"

    def __post_init__(self) -> None:
        if not self.records:
            raise B10HeadroomContractError("headroom batch requires at least one explicit station record")
        if self.evidence_status not in {"DER", "Q"}:
            raise B10HeadroomContractError("batch evidence_status must be DER or Q")
        if self.aggregation_authority != "NONE_NON_ADDITIVE":
            raise B10HeadroomContractError("B10-P1 does not authorize summing substation headroom")
        expected = "Q" if any(row.evidence_status == "Q" for row in self.records) else "DER"
        if self.evidence_status != expected:
            raise B10HeadroomContractError("batch evidence_status must propagate row uncertainty")
        seen: set[tuple[str, float, str]] = set()
        for row in self.records:
            key = (row.station_code, row.voltage_kv, row.horizon)
            if key in seen:
                raise B10HeadroomContractError(f"duplicate station/voltage/horizon key: {key!r}")
            seen.add(key)


@dataclass(frozen=True)
class HeadroomAssessment:
    region_id: str
    region_scheme: str
    horizon: str
    incremental_demand_mw: float
    published_headroom_mw: float | None
    remaining_headroom_mw: float | None
    overload_mw: float | None
    evidence_status: str
    source_refs: tuple[str, ...]
    connection_authority: str = CONNECTION_AUTHORITY


def parse_mvm_demasz_consumption_headroom_text(
    normalized_tsv_text: str,
    *,
    provenance: DsoHeadroomProvenance,
) -> DsoHeadroomBatch:
    """Parse a normalized external transcription of the official MVM DEMASZ table.

    The input is not the source PDF. It is a tab-separated acquisition artifact with
    the exact ``NORMALIZED_HEADERS`` contract. Therefore successful, verified rows
    are DER rather than OBS. The raw/source PDF remains external unless its reuse
    terms are separately cleared.
    """
    if not isinstance(normalized_tsv_text, str) or not normalized_tsv_text.strip():
        raise B10HeadroomContractError("normalized TSV text is required")
    exact_text_hash = hashlib.sha256(normalized_tsv_text.encode("utf-8")).hexdigest()
    if provenance.normalized_text_sha256 is not None and provenance.normalized_text_sha256 != exact_text_hash:
        raise B10HeadroomContractError("normalized text does not match the declared SHA-256")

    reader = csv.DictReader(io.StringIO(normalized_tsv_text), delimiter="\t")
    if tuple(reader.fieldnames or ()) != NORMALIZED_HEADERS:
        raise B10HeadroomContractError("normalized TSV headers do not match the canonical B10-P1 contract")

    can_promote = (
        provenance.license_decision == REUSE_CLEARED
        and provenance.extraction_verification == VERIFIED_AGAINST_SOURCE
        and provenance.source_pdf_sha256 is not None
        and provenance.normalized_text_sha256 == exact_text_hash
    )
    status = "DER" if can_promote else "Q"
    token = _VERIFIED_EXTRACTION_TOKEN if can_promote else None
    refs = (MVM_DEMASZ_SOURCE_ID, MVM_DEMASZ_METHOD_SOURCE_ID)
    records: list[DsoHeadroomRecord] = []

    for row_number, row in enumerate(reader, start=2):
        operator = (row.get("network_operator") or "").strip().upper().replace("É", "E")
        if operator != MVM_DEMASZ_OPERATOR:
            raise B10HeadroomContractError(f"row {row_number}: unsupported network operator")
        station_name = (row.get("station_name") or "").strip()
        station_code = (row.get("station_code") or "").strip().upper()
        if not station_name:
            raise B10HeadroomContractError(f"row {row_number}: station_name is required")
        if not STATION_CODE_RE.fullmatch(station_code):
            raise B10HeadroomContractError(f"row {row_number}: invalid station_code")

        voltage = _parse_number(row["voltage_kv"], "voltage_kv")
        current_values = (
            _parse_number(row["n1_capacity_current_mw"], "n1_capacity_current_mw"),
            _parse_number(row["winter_evening_load_current_mw"], "winter_evening_load_current_mw"),
            _parse_number(row["free_capacity_current_mw"], "free_capacity_current_mw"),
        )
        future_values = (
            _parse_number(row["n1_capacity_5y_mw"], "n1_capacity_5y_mw"),
            _parse_number(row["winter_evening_load_5y_mw"], "winter_evening_load_5y_mw"),
            _parse_number(row["free_capacity_5y_mw"], "free_capacity_5y_mw"),
        )
        for horizon, values in ((CURRENT, current_values), (FIVE_YEAR, future_values)):
            records.append(
                DsoHeadroomRecord(
                    station_name=station_name,
                    station_code=station_code,
                    voltage_kv=voltage,
                    horizon=horizon,
                    n_minus_1_capacity_mw=values[0],
                    winter_evening_peak_load_mw=values[1],
                    theoretical_free_capacity_mw=values[2],
                    evidence_status=status,
                    source_refs=refs,
                    provenance=provenance,
                    _verification_token=token,
                )
            )

    if not records:
        raise B10HeadroomContractError("normalized TSV contains no station records")
    return DsoHeadroomBatch(tuple(records), refs, status)


def assess_incremental_demand(
    record: DsoHeadroomRecord,
    *,
    incremental_demand_mw: float,
    demand_region_id: str,
    demand_region_scheme: str,
    demand_evidence_status: str,
    demand_source_refs: Iterable[str],
) -> HeadroomAssessment:
    """Assess one explicitly mapped load increment against one substation row.

    No spatial mapping is inferred. A B08 control-area or county demand cannot enter
    this function unless an upstream contract has already produced the exact same
    DSO-substation key. The result is not a connection permission; MGT remains the
    individual authority.
    """
    if not isinstance(record, DsoHeadroomRecord):
        raise B10HeadroomContractError("record must be DsoHeadroomRecord")
    demand = _finite_nonnegative(incremental_demand_mw, "incremental_demand_mw")
    if demand_region_scheme != REGION_SCHEME or demand_region_id != record.region_id:
        raise B10HeadroomContractError("demand grain must exactly match the DSO substation/voltage record")
    if demand_evidence_status not in {"OBS", "DER", "SCN", "Q"}:
        raise B10HeadroomContractError("unsupported demand evidence status")
    if isinstance(demand_source_refs, str):
        raise B10HeadroomContractError("demand_source_refs must be an explicit collection")
    demand_refs = tuple(demand_source_refs)
    if not demand_refs or any(not isinstance(ref, str) or not ref.strip() for ref in demand_refs):
        raise B10HeadroomContractError("demand_source_refs are required")
    refs = tuple(sorted(set(record.source_refs + demand_refs)))

    if record.evidence_status == "Q" or demand_evidence_status == "Q" or record.theoretical_free_capacity_mw is None:
        return HeadroomAssessment(
            region_id=record.region_id,
            region_scheme=REGION_SCHEME,
            horizon=record.horizon,
            incremental_demand_mw=demand,
            published_headroom_mw=None,
            remaining_headroom_mw=None,
            overload_mw=None,
            evidence_status="Q",
            source_refs=refs,
        )

    headroom = record.theoretical_free_capacity_mw
    remaining = max(0.0, headroom - demand)
    overload = max(0.0, demand - headroom)
    result_status = "SCN" if demand_evidence_status == "SCN" else "DER"
    return HeadroomAssessment(
        region_id=record.region_id,
        region_scheme=REGION_SCHEME,
        horizon=record.horizon,
        incremental_demand_mw=demand,
        published_headroom_mw=headroom,
        remaining_headroom_mw=remaining,
        overload_mw=overload,
        evidence_status=result_status,
        source_refs=refs,
    )
