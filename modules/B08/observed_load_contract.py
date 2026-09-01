"""Canonical intake contract for source-native Hungarian observed load data.

This contract deliberately stops at the grain supplied by the source. The
ENTSO-E candidate is a Hungarian control-area / national series, not a DSO or
county series, and it must not be converted into one.
"""

from __future__ import annotations

import hashlib
import re
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from math import isfinite
from typing import Iterable
from urllib.parse import parse_qs, urlparse


class ObservedLoadContractError(ValueError):
    """Fail-closed observed-load intake violation."""


EVIDENCE_STATUSES = {"OBS", "DER", "SCN", "Q"}
TRUTH_CONTEXTS = {"REAL", "SCN"}
ENTSOE_ACTUAL_TOTAL_LOAD = "A65"
ENTSOE_REALISED = "A16"
ENTSOE_CONSUMPTION = "A04"
HUNGARY_EIC = "10YHU-MAVIR----U"
HUNGARY_CONTROL_AREA = "HUNGARY_CONTROL_AREA"
CONTROL_AREA_SCHEME = "ENTSOE_CONTROL_AREA"
ALLOWED_RESOLUTIONS = {"PT15M": 0.25, "PT30M": 0.5, "PT60M": 1.0}
SHA256_RE = re.compile(r"[0-9a-f]{64}")
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
SOURCE_REVISION_NOT_PROVIDED = "NOT_PROVIDED_BY_SOURCE"
ENTSOE_SOURCE_ID = "SRC-B08-ENTSOE-ACTUAL-TOTAL-LOAD-2026"
ENTSOE_PUBLISHER = "ENTSO-E"
ENTSOE_DATASET_NAME = "Actual Total Load [6.1.A]"
ENTSOE_API_HOST = "web-api.tp.entsoe.eu"
ENTSOE_API_PATH = "/api"
REQUIRED_REQUEST_VALUES = {
    "documentType": ENTSOE_ACTUAL_TOTAL_LOAD,
    "processType": ENTSOE_REALISED,
    "businessType": ENTSOE_CONSUMPTION,
    "outBiddingZone_Domain": HUNGARY_EIC,
}
REQUIRED_REQUEST_KEYS = frozenset((*REQUIRED_REQUEST_VALUES, "periodStart", "periodEnd"))
_OBS_VERIFICATION_TOKEN = object()


def _local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def _children(element: ET.Element, name: str) -> list[ET.Element]:
    return [child for child in element.iter() if _local_name(child.tag) == name]


def _text(element: ET.Element | None, name: str) -> str | None:
    if element is None:
        return None
    for child in element.iter():
        if _local_name(child.tag) == name:
            return (child.text or "").strip()
    return None


def _required_text(element: ET.Element | None, name: str) -> str:
    value = _text(element, name)
    if not value:
        raise ObservedLoadContractError(f"missing XML field: {name}")
    return value


def _parse_timestamp(value: str, field: str) -> datetime:
    try:
        timestamp = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ObservedLoadContractError(f"invalid {field}") from exc
    if timestamp.tzinfo is None or timestamp.utcoffset() is None:
        raise ObservedLoadContractError(f"{field} must be timezone-aware")
    return timestamp.astimezone(timezone.utc)


def _parse_request_timestamp(value: str, field: str) -> datetime:
    if not isinstance(value, str) or not re.fullmatch(r"\d{12}", value):
        raise ObservedLoadContractError(f"{field} must use yyyyMMddHHmm UTC")
    try:
        return datetime.strptime(value, "%Y%m%d%H%M").replace(tzinfo=timezone.utc)
    except ValueError as exc:
        raise ObservedLoadContractError(f"invalid {field}") from exc


def _validated_request_window(request_url: str) -> tuple[datetime, datetime]:
    parsed = urlparse(request_url)
    if (
        parsed.scheme != "https"
        or parsed.hostname != ENTSOE_API_HOST
        or parsed.path != ENTSOE_API_PATH
        or parsed.params
        or parsed.fragment
        or not parsed.query
    ):
        raise ObservedLoadContractError("provenance request_url must be the canonical ENTSO-E HTTPS API URL")
    query = parse_qs(parsed.query, keep_blank_values=True, strict_parsing=True)
    if set(query) != REQUIRED_REQUEST_KEYS:
        raise ObservedLoadContractError("provenance request_url must contain exactly the canonical non-secret query fields")
    for key in REQUIRED_REQUEST_KEYS:
        values = query.get(key, [])
        if len(values) != 1 or not values[0]:
            raise ObservedLoadContractError(f"provenance request query field {key} must occur exactly once")
    for key, expected in REQUIRED_REQUEST_VALUES.items():
        if query[key][0] != expected:
            raise ObservedLoadContractError(f"provenance request query field {key} has the wrong canonical value")
    start = _parse_request_timestamp(query["periodStart"][0], "periodStart")
    end = _parse_request_timestamp(query["periodEnd"][0], "periodEnd")
    if end <= start:
        raise ObservedLoadContractError("periodEnd must be after periodStart")
    return start, end


def _finite_nonnegative(value: float | None, field: str) -> float:
    if value is None or isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ObservedLoadContractError(f"{field} must be finite and non-negative")
    if not isfinite(value) or value < 0:
        raise ObservedLoadContractError(f"{field} must be finite and non-negative")
    return float(value)


@dataclass(frozen=True)
class SourceProvenance:
    source_id: str
    publisher: str
    dataset_name: str
    request_url: str
    retrieved_at: datetime
    license_decision: str
    raw_storage_policy: str
    source_sha256: str | None = None
    source_revision: str = SOURCE_REVISION_NOT_PROVIDED

    def __post_init__(self) -> None:
        for name in ("source_id", "publisher", "dataset_name", "request_url", "license_decision", "raw_storage_policy"):
            value = getattr(self, name)
            if not isinstance(value, str) or not value.strip():
                raise ObservedLoadContractError(f"provenance {name} is required")
        if self.source_id != ENTSOE_SOURCE_ID or self.publisher != ENTSOE_PUBLISHER or self.dataset_name != ENTSOE_DATASET_NAME:
            raise ObservedLoadContractError("provenance source identity must match the canonical ENTSO-E Actual Total Load contract")
        _validated_request_window(self.request_url)
        if self.license_decision not in LICENSE_DECISIONS:
            raise ObservedLoadContractError("invalid license_decision")
        if not isinstance(self.retrieved_at, datetime) or self.retrieved_at.tzinfo is None or self.retrieved_at.utcoffset() is None:
            raise ObservedLoadContractError("provenance retrieved_at must be timezone-aware")
        object.__setattr__(self, "retrieved_at", self.retrieved_at.astimezone(timezone.utc))
        if self.raw_storage_policy not in {"EXTERNAL_ONLY", "REPOSITORY_ALLOWED"}:
            raise ObservedLoadContractError("invalid raw_storage_policy")
        if not isinstance(self.source_revision, str) or not self.source_revision.strip():
            raise ObservedLoadContractError("provenance source_revision is required or must be NOT_PROVIDED_BY_SOURCE")
        if self.source_sha256 is not None and not SHA256_RE.fullmatch(self.source_sha256):
            raise ObservedLoadContractError("source_sha256 must be lowercase SHA-256")


@dataclass(frozen=True)
class ObservedLoadRecord:
    """One source-native load power value at the source's supported grain."""

    source_series_id: str
    timestamp_utc: datetime
    interval_end_utc: datetime
    timestep_hours: float
    power_mw: float | None
    region_id: str
    region_scheme: str
    source_time_basis: str
    interval_convention: str
    truth_context: str
    evidence_status: str
    source_refs: tuple[str, ...]
    source_revision: str | None = None
    provenance: SourceProvenance | None = None
    _obs_verification_token: object | None = field(default=None, repr=False, compare=False)

    def __post_init__(self) -> None:
        if self.timestamp_utc.tzinfo is None or self.timestamp_utc.utcoffset() is None:
            raise ObservedLoadContractError("timestamp_utc must be timezone-aware")
        if self.interval_end_utc.tzinfo is None or self.interval_end_utc.utcoffset() is None:
            raise ObservedLoadContractError("interval_end_utc must be timezone-aware")
        start = self.timestamp_utc.astimezone(timezone.utc)
        end = self.interval_end_utc.astimezone(timezone.utc)
        object.__setattr__(self, "timestamp_utc", start)
        object.__setattr__(self, "interval_end_utc", end)
        if end <= start:
            raise ObservedLoadContractError("interval end must be after interval start")
        if not isinstance(self.timestep_hours, (int, float)) or isinstance(self.timestep_hours, bool) or not isfinite(self.timestep_hours) or self.timestep_hours <= 0:
            raise ObservedLoadContractError("timestep_hours must be finite and positive")
        expected_end = start + timedelta(hours=float(self.timestep_hours))
        if end != expected_end:
            raise ObservedLoadContractError("interval endpoints do not match timestep_hours")
        if not isinstance(self.source_series_id, str) or not self.source_series_id.strip():
            raise ObservedLoadContractError("source_series_id is required")
        if self.region_id != HUNGARY_CONTROL_AREA or self.region_scheme != CONTROL_AREA_SCHEME:
            raise ObservedLoadContractError("observed source grain must remain Hungarian control area")
        if not isinstance(self.source_time_basis, str) or not self.source_time_basis.strip():
            raise ObservedLoadContractError("source_time_basis is required")
        if self.interval_convention != "INTERVAL_START":
            raise ObservedLoadContractError("only explicit interval-start convention is supported")
        if self.truth_context not in TRUTH_CONTEXTS:
            raise ObservedLoadContractError("truth_context must be REAL or SCN")
        allowed = {"SCN", "Q"} if self.truth_context == "SCN" else {"OBS", "DER", "Q"}
        if self.evidence_status not in allowed:
            raise ObservedLoadContractError("evidence status is incompatible with truth context")
        if self.provenance is not None and not isinstance(self.provenance, SourceProvenance):
            raise ObservedLoadContractError("provenance must be SourceProvenance")
        if self.evidence_status == "OBS":
            if self._obs_verification_token is not _OBS_VERIFICATION_TOKEN:
                raise ObservedLoadContractError("OBS records must be created by the canonical verified parser path")
            if self.provenance is None:
                raise ObservedLoadContractError("OBS records require complete source provenance")
            if self.provenance.license_decision != REUSE_CLEARED or self.provenance.source_sha256 is None:
                raise ObservedLoadContractError("OBS records require cleared reuse and verified payload checksum")
            if self.source_revision != self.provenance.source_revision:
                raise ObservedLoadContractError("OBS record source_revision must match provenance")
            if self.source_refs != (self.provenance.source_id,):
                raise ObservedLoadContractError("OBS record source_refs must match provenance")
        if isinstance(self.source_refs, str) or not self.source_refs or any(not isinstance(ref, str) or not ref.strip() for ref in self.source_refs):
            raise ObservedLoadContractError("source_refs must be a non-empty collection")
        if self.power_mw is not None:
            _finite_nonnegative(self.power_mw, "power_mw")
        elif self.evidence_status != "Q":
            raise ObservedLoadContractError("missing power remains Q; it cannot become zero")


def derive_energy_mwh(records: Iterable[ObservedLoadRecord]) -> tuple[float | None, ...]:
    """Derive MWh explicitly from MW and each record's explicit duration."""
    result: list[float | None] = []
    for record in records:
        result.append(None if record.power_mw is None else record.power_mw * record.timestep_hours)
    return tuple(result)


def _header_value(root: ET.Element, name: str) -> str | None:
    for element in root.iter():
        if _local_name(element.tag) == name:
            value = (element.text or "").strip()
            if value:
                return value
    return None


def parse_entsoe_actual_total_load(
    xml_text: str,
    *,
    provenance: SourceProvenance,
    truth_context: str = "REAL",
    source_time_basis: str = "UTC",
) -> tuple[ObservedLoadRecord, ...]:
    """Parse an ENTSO-E A65/A16/A04 payload without resampling or relabelling."""
    if not isinstance(xml_text, str) or not xml_text.strip():
        raise ObservedLoadContractError("XML payload is required")
    exact_payload_sha256 = hashlib.sha256(xml_text.encode("utf-8")).hexdigest()
    if provenance.source_sha256 is not None and provenance.source_sha256 != exact_payload_sha256:
        raise ObservedLoadContractError("source_sha256 does not match exact UTF-8 payload")
    if truth_context not in TRUTH_CONTEXTS:
        raise ObservedLoadContractError("truth_context must be REAL or SCN")
    request_start, request_end = _validated_request_window(provenance.request_url)
    observed_eligible = (
        truth_context == "REAL"
        and provenance.source_sha256 is not None
        and provenance.license_decision == REUSE_CLEARED
    )
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError as exc:
        raise ObservedLoadContractError("invalid ENTSO-E XML") from exc
    if _header_value(root, "documentType") != ENTSOE_ACTUAL_TOTAL_LOAD:
        raise ObservedLoadContractError("payload is not Actual Total Load A65")
    records: list[ObservedLoadRecord] = []
    for series in _children(root, "TimeSeries"):
        if _required_text(series, "processType") != ENTSOE_REALISED:
            raise ObservedLoadContractError("forecast/modelled process cannot become OBS")
        if _required_text(series, "businessType") != ENTSOE_CONSUMPTION:
            raise ObservedLoadContractError("payload is not load consumption")
        domain = _required_text(series, "outBiddingZone_Domain.mRID")
        if domain != HUNGARY_EIC:
            raise ObservedLoadContractError("payload is not the Hungarian ENTSO-E area")
        series_id = _required_text(series, "mRID")
        period = next((item for item in series.iter() if _local_name(item.tag) == "Period"), None)
        if period is None:
            raise ObservedLoadContractError("missing load Period")
        start = _parse_timestamp(_required_text(period, "start"), "period start")
        end = _parse_timestamp(_required_text(period, "end"), "period end")
        if end <= start:
            raise ObservedLoadContractError("load Period end must be after start")
        if start < request_start or end > request_end:
            raise ObservedLoadContractError("payload period lies outside the canonical request window")
        resolution = _required_text(period, "resolution")
        if resolution not in ALLOWED_RESOLUTIONS:
            raise ObservedLoadContractError("unsupported or implicit resolution")
        timestep = ALLOWED_RESOLUTIONS[resolution]
        points = [item for item in period.iter() if _local_name(item.tag) == "Point"]
        if not points:
            raise ObservedLoadContractError("load Period requires explicit points")
        for point in points:
            try:
                position = int(_required_text(point, "position"))
            except ValueError as exc:
                raise ObservedLoadContractError("point position must be an integer") from exc
            if position < 1:
                raise ObservedLoadContractError("point position must be positive")
            timestamp = start + timedelta(hours=timestep * (position - 1))
            interval_end = timestamp + timedelta(hours=timestep)
            if interval_end > end:
                raise ObservedLoadContractError("point lies outside declared period")
            quantity_text = _text(point, "quantity")
            if quantity_text in {None, ""}:
                quantity = None
            else:
                try:
                    quantity = float(quantity_text)
                except ValueError as exc:
                    raise ObservedLoadContractError("point quantity must be numeric") from exc
            status = "OBS" if quantity is not None and observed_eligible else "Q"
            records.append(ObservedLoadRecord(
                source_series_id=series_id,
                timestamp_utc=timestamp,
                interval_end_utc=interval_end,
                timestep_hours=timestep,
                power_mw=quantity,
                region_id=HUNGARY_CONTROL_AREA,
                region_scheme=CONTROL_AREA_SCHEME,
                source_time_basis=source_time_basis,
                interval_convention="INTERVAL_START",
                truth_context=truth_context,
                evidence_status=status if truth_context == "REAL" else ("SCN" if quantity is not None else "Q"),
                source_refs=(provenance.source_id,),
                source_revision=provenance.source_revision,
                provenance=provenance,
                _obs_verification_token=_OBS_VERIFICATION_TOKEN if status == "OBS" else None,
            ))
    if not records:
        raise ObservedLoadContractError("payload requires at least one Hungarian load series")
    keys: set[tuple[str, datetime]] = set()
    for record in records:
        key = (record.source_series_id, record.timestamp_utc)
        if key in keys:
            raise ObservedLoadContractError("duplicate canonical source series timestamp")
        keys.add(key)
    return tuple(sorted(records, key=lambda item: (item.source_series_id, item.timestamp_utc)))


def validate_record_panel(records: Iterable[ObservedLoadRecord]) -> None:
    """Validate only duplicate identity; gaps remain explicit, never filled."""
    values = tuple(records)
    if not values:
        raise ObservedLoadContractError("at least one observed load record is required")
    keys = [(row.source_series_id, row.timestamp_utc) for row in values]
    if len(keys) != len(set(keys)):
        raise ObservedLoadContractError("duplicate canonical source series timestamp")
    if len({row.timestep_hours for row in values}) != 1:
        raise ObservedLoadContractError("mixed timestep requires separate source panels")
