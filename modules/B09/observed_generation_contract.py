"""Source-native ENTSO-E observed-generation intake for B09.

The contract is intentionally bounded to Hungary's ENTSO-E control-area / bidding-
zone grain. It does not create county or DSO generation, dispatch storage, infer
missing production types, or turn source consumption into negative generation.
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

from modules.B08.observed_load_contract import CONTROL_AREA_SCHEME, HUNGARY_CONTROL_AREA, HUNGARY_EIC
from modules.B09.engine import SupplyRecord


class ObservedGenerationContractError(ValueError):
    """Fail-closed B09 observed-generation intake violation."""


ENTSOE_ACTUAL_GENERATION_PER_TYPE = "A75"
ENTSOE_REALISED = "A16"
ENTSOE_RESOURCE_TYPE_AGGREGATION = "A08"
ENTSOE_PRODUCTION_BUSINESS_TYPES = {"A01", "A93", "A94"}
ENTSOE_MEGAWATT_UNIT = "MAW"
ALLOWED_RESOLUTIONS = {"PT15M": 0.25, "PT30M": 0.5, "PT60M": 1.0}
SHA256_RE = re.compile(r"[0-9a-f]{64}")
PSR_TYPE_RE = re.compile(r"B[0-9]{2}")

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
SOURCE_SEMANTICS = "ENTSOE_PUBLISHED_ACTUAL_MAY_INCLUDE_PROVIDER_ESTIMATES"

ENTSOE_SOURCE_ID = "SRC-B09-ENTSOE-ACTUAL-GENERATION-TYPE-2026"
ENTSOE_PUBLISHER = "ENTSO-E"
ENTSOE_DATASET_NAME = "Actual Generation per Production Type [16.1.B&C]"
ENTSOE_API_HOST = "web-api.tp.entsoe.eu"
ENTSOE_API_PATH = "/api"
REQUIRED_REQUEST_VALUES = {
    "documentType": ENTSOE_ACTUAL_GENERATION_PER_TYPE,
    "processType": ENTSOE_REALISED,
    "in_Domain": HUNGARY_EIC,
}
REQUIRED_REQUEST_KEYS = frozenset((*REQUIRED_REQUEST_VALUES, "periodStart", "periodEnd"))
_OBS_VERIFICATION_TOKEN = object()


def _local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def _elements(element: ET.Element, name: str) -> list[ET.Element]:
    return [child for child in element.iter() if _local_name(child.tag) == name]


def _text(element: ET.Element | None, *names: str) -> str | None:
    if element is None:
        return None
    wanted = set(names)
    for child in element.iter():
        if _local_name(child.tag) in wanted:
            value = (child.text or "").strip()
            if value:
                return value
    return None


def _required_text(element: ET.Element | None, *names: str) -> str:
    value = _text(element, *names)
    if not value:
        raise ObservedGenerationContractError(f"missing XML field: {'/'.join(names)}")
    return value


def _utc_timestamp(value: str, field_name: str) -> datetime:
    try:
        timestamp = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ObservedGenerationContractError(f"invalid {field_name}") from exc
    if timestamp.tzinfo is None or timestamp.utcoffset() is None:
        raise ObservedGenerationContractError(f"{field_name} must be timezone-aware")
    return timestamp.astimezone(timezone.utc)


def _request_timestamp(value: str, field_name: str) -> datetime:
    if not isinstance(value, str) or not re.fullmatch(r"\d{12}", value):
        raise ObservedGenerationContractError(f"{field_name} must use yyyyMMddHHmm UTC")
    try:
        return datetime.strptime(value, "%Y%m%d%H%M").replace(tzinfo=timezone.utc)
    except ValueError as exc:
        raise ObservedGenerationContractError(f"invalid {field_name}") from exc


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
        raise ObservedGenerationContractError("request_url must use the canonical ENTSO-E HTTPS API endpoint")
    try:
        query = parse_qs(parsed.query, keep_blank_values=True, strict_parsing=True)
    except ValueError as exc:
        raise ObservedGenerationContractError("invalid request query") from exc
    if set(query) != REQUIRED_REQUEST_KEYS:
        raise ObservedGenerationContractError("request_url must contain exactly the canonical non-secret query fields")
    for key in REQUIRED_REQUEST_KEYS:
        values = query.get(key, [])
        if len(values) != 1 or not values[0]:
            raise ObservedGenerationContractError(f"request query field {key} must occur exactly once")
    for key, expected in REQUIRED_REQUEST_VALUES.items():
        if query[key][0] != expected:
            raise ObservedGenerationContractError(f"request query field {key} has the wrong canonical value")
    start = _request_timestamp(query["periodStart"][0], "periodStart")
    end = _request_timestamp(query["periodEnd"][0], "periodEnd")
    if end <= start:
        raise ObservedGenerationContractError("periodEnd must be after periodStart")
    return start, end


def _finite_nonnegative(value: float | None, field_name: str) -> float:
    if value is None or isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ObservedGenerationContractError(f"{field_name} must be finite and non-negative")
    if not isfinite(value) or value < 0:
        raise ObservedGenerationContractError(f"{field_name} must be finite and non-negative")
    return float(value)


@dataclass(frozen=True)
class GenerationSourceProvenance:
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
                raise ObservedGenerationContractError(f"provenance {name} is required")
        if self.source_id != ENTSOE_SOURCE_ID or self.publisher != ENTSOE_PUBLISHER or self.dataset_name != ENTSOE_DATASET_NAME:
            raise ObservedGenerationContractError("provenance source identity must match the canonical ENTSO-E generation contract")
        _validated_request_window(self.request_url)
        if self.license_decision not in LICENSE_DECISIONS:
            raise ObservedGenerationContractError("invalid license_decision")
        if not isinstance(self.retrieved_at, datetime) or self.retrieved_at.tzinfo is None or self.retrieved_at.utcoffset() is None:
            raise ObservedGenerationContractError("provenance retrieved_at must be timezone-aware")
        object.__setattr__(self, "retrieved_at", self.retrieved_at.astimezone(timezone.utc))
        if self.raw_storage_policy not in {"EXTERNAL_ONLY", "REPOSITORY_ALLOWED"}:
            raise ObservedGenerationContractError("invalid raw_storage_policy")
        if not isinstance(self.source_revision, str) or not self.source_revision.strip():
            raise ObservedGenerationContractError("source_revision is required or must be NOT_PROVIDED_BY_SOURCE")
        if self.source_sha256 is not None and not SHA256_RE.fullmatch(self.source_sha256):
            raise ObservedGenerationContractError("source_sha256 must be lowercase SHA-256")


@dataclass(frozen=True)
class ObservedGenerationRecord:
    source_series_id: str
    timestamp_utc: datetime
    interval_end_utc: datetime
    timestep_hours: float
    power_mw: float | None
    production_type_code: str
    business_type: str
    region_id: str
    region_scheme: str
    evidence_status: str
    source_refs: tuple[str, ...]
    source_semantics: str = SOURCE_SEMANTICS
    source_revision: str | None = None
    provenance: GenerationSourceProvenance | None = None
    _obs_verification_token: object | None = field(default=None, repr=False, compare=False)

    def __post_init__(self) -> None:
        if self.timestamp_utc.tzinfo is None or self.timestamp_utc.utcoffset() is None:
            raise ObservedGenerationContractError("timestamp_utc must be timezone-aware")
        if self.interval_end_utc.tzinfo is None or self.interval_end_utc.utcoffset() is None:
            raise ObservedGenerationContractError("interval_end_utc must be timezone-aware")
        start = self.timestamp_utc.astimezone(timezone.utc)
        end = self.interval_end_utc.astimezone(timezone.utc)
        object.__setattr__(self, "timestamp_utc", start)
        object.__setattr__(self, "interval_end_utc", end)
        if end <= start:
            raise ObservedGenerationContractError("interval end must be after interval start")
        if not isinstance(self.timestep_hours, (int, float)) or isinstance(self.timestep_hours, bool) or not isfinite(self.timestep_hours) or self.timestep_hours <= 0:
            raise ObservedGenerationContractError("timestep_hours must be finite and positive")
        if end != start + timedelta(hours=float(self.timestep_hours)):
            raise ObservedGenerationContractError("interval endpoints do not match timestep_hours")
        if not isinstance(self.source_series_id, str) or not self.source_series_id.strip():
            raise ObservedGenerationContractError("source_series_id is required")
        if not isinstance(self.production_type_code, str) or not PSR_TYPE_RE.fullmatch(self.production_type_code):
            raise ObservedGenerationContractError("production_type_code must be a source-native ENTSO-E Bxx code")
        if self.business_type not in ENTSOE_PRODUCTION_BUSINESS_TYPES:
            raise ObservedGenerationContractError("unsupported production business type")
        if self.region_id != HUNGARY_CONTROL_AREA or self.region_scheme != CONTROL_AREA_SCHEME:
            raise ObservedGenerationContractError("observed generation grain must remain the Hungarian ENTSO-E control area")
        if self.evidence_status not in {"OBS", "Q"}:
            raise ObservedGenerationContractError("source-native observed generation status must be OBS or Q")
        if self.source_semantics != SOURCE_SEMANTICS:
            raise ObservedGenerationContractError("source semantics must preserve the provider-estimate caveat")
        if self.provenance is not None and not isinstance(self.provenance, GenerationSourceProvenance):
            raise ObservedGenerationContractError("provenance must be GenerationSourceProvenance")
        if self.evidence_status == "OBS":
            if self._obs_verification_token is not _OBS_VERIFICATION_TOKEN:
                raise ObservedGenerationContractError("OBS records must be created by the canonical verified parser path")
            if self.provenance is None:
                raise ObservedGenerationContractError("OBS records require complete provenance")
            if self.provenance.license_decision != REUSE_CLEARED or self.provenance.source_sha256 is None:
                raise ObservedGenerationContractError("OBS records require cleared reuse and verified payload checksum")
            if self.source_revision != self.provenance.source_revision:
                raise ObservedGenerationContractError("OBS source_revision must match provenance")
            if self.source_refs != (self.provenance.source_id,):
                raise ObservedGenerationContractError("OBS source_refs must match provenance")
        if isinstance(self.source_refs, str) or not self.source_refs or any(not isinstance(ref, str) or not ref.strip() for ref in self.source_refs):
            raise ObservedGenerationContractError("source_refs must be a non-empty collection")
        if self.power_mw is not None:
            _finite_nonnegative(self.power_mw, "power_mw")
        elif self.evidence_status != "Q":
            raise ObservedGenerationContractError("missing generation remains Q; it cannot become zero")


@dataclass(frozen=True)
class ObservedGenerationBatch:
    records: tuple[ObservedGenerationRecord, ...]
    request_start_utc: datetime
    request_end_utc: datetime
    excluded_consumption_series_count: int
    source_refs: tuple[str, ...]

    def __post_init__(self) -> None:
        if not self.records:
            raise ObservedGenerationContractError("generation batch requires at least one production record")
        if self.request_start_utc.tzinfo is None or self.request_end_utc.tzinfo is None:
            raise ObservedGenerationContractError("request window must be timezone-aware")
        if self.request_end_utc <= self.request_start_utc:
            raise ObservedGenerationContractError("request window end must be after start")
        if not isinstance(self.excluded_consumption_series_count, int) or isinstance(self.excluded_consumption_series_count, bool) or self.excluded_consumption_series_count < 0:
            raise ObservedGenerationContractError("excluded_consumption_series_count must be a non-negative integer")


def parse_entsoe_actual_generation_per_type(
    xml_text: str,
    *,
    provenance: GenerationSourceProvenance,
) -> ObservedGenerationBatch:
    """Parse source-native A75 generation, excluding consumption-direction series."""
    if not isinstance(xml_text, str) or not xml_text.strip():
        raise ObservedGenerationContractError("XML payload is required")
    exact_sha = hashlib.sha256(xml_text.encode("utf-8")).hexdigest()
    if provenance.source_sha256 is not None and provenance.source_sha256 != exact_sha:
        raise ObservedGenerationContractError("source_sha256 does not match exact UTF-8 payload")
    request_start, request_end = _validated_request_window(provenance.request_url)
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError as exc:
        raise ObservedGenerationContractError("invalid ENTSO-E XML") from exc
    if _required_text(root, "documentType") != ENTSOE_ACTUAL_GENERATION_PER_TYPE:
        raise ObservedGenerationContractError("payload is not A75 Actual Generation per Production Type")
    if _required_text(root, "process.processType", "processType") != ENTSOE_REALISED:
        raise ObservedGenerationContractError("payload is not realised A16 generation")

    observed_eligible = provenance.source_sha256 is not None and provenance.license_decision == REUSE_CLEARED
    records: list[ObservedGenerationRecord] = []
    excluded_consumption = 0

    for series in _elements(root, "TimeSeries"):
        in_domain = _text(series, "inBiddingZone_Domain.mRID", "in_Domain.mRID")
        out_domain = _text(series, "outBiddingZone_Domain.mRID", "out_Domain.mRID")
        if not in_domain and out_domain:
            if out_domain != HUNGARY_EIC:
                raise ObservedGenerationContractError("consumption-direction series is not the Hungarian ENTSO-E area")
            excluded_consumption += 1
            continue
        if in_domain != HUNGARY_EIC:
            raise ObservedGenerationContractError("generation series is not the Hungarian ENTSO-E area")
        if out_domain:
            raise ObservedGenerationContractError("a production series cannot also carry a consumption/out-domain direction")

        business_type = _required_text(series, "businessType")
        if business_type not in ENTSOE_PRODUCTION_BUSINESS_TYPES:
            raise ObservedGenerationContractError("unsupported generation business type")
        if _required_text(series, "objectAggregation") != ENTSOE_RESOURCE_TYPE_AGGREGATION:
            raise ObservedGenerationContractError("generation series must use A08 resource-type aggregation")
        measure_unit = _required_text(series, "quantity_Measure_Unit.name", "measurement_Unit.name", "measure_Unit.name")
        if measure_unit != ENTSOE_MEGAWATT_UNIT:
            raise ObservedGenerationContractError("generation quantity must use source-native MW/MAW")
        production_type = _required_text(series, "MktPSRType.psrType", "mktPSRType.psrType", "psrType")
        if not PSR_TYPE_RE.fullmatch(production_type):
            raise ObservedGenerationContractError("invalid source-native production type code")
        series_id = _required_text(series, "mRID")
        periods = _elements(series, "Period")
        if len(periods) != 1:
            raise ObservedGenerationContractError("each generation TimeSeries must contain exactly one Period")
        period = periods[0]
        start = _utc_timestamp(_required_text(period, "start"), "period start")
        end = _utc_timestamp(_required_text(period, "end"), "period end")
        if end <= start:
            raise ObservedGenerationContractError("generation Period end must be after start")
        if start < request_start or end > request_end:
            raise ObservedGenerationContractError("payload period lies outside the canonical request window")
        resolution = _required_text(period, "resolution")
        if resolution not in ALLOWED_RESOLUTIONS:
            raise ObservedGenerationContractError("unsupported or implicit generation resolution")
        timestep = ALLOWED_RESOLUTIONS[resolution]
        points = _elements(period, "Point")
        if not points:
            raise ObservedGenerationContractError("generation Period requires explicit points")
        for point in points:
            try:
                position = int(_required_text(point, "position"))
            except ValueError as exc:
                raise ObservedGenerationContractError("generation point position must be an integer") from exc
            if position < 1:
                raise ObservedGenerationContractError("generation point position must be positive")
            timestamp = start + timedelta(hours=timestep * (position - 1))
            interval_end = timestamp + timedelta(hours=timestep)
            if interval_end > end:
                raise ObservedGenerationContractError("generation point lies outside declared period")
            quantity_text = _text(point, "quantity")
            if quantity_text in {None, ""}:
                quantity = None
            else:
                try:
                    quantity = float(quantity_text)
                except ValueError as exc:
                    raise ObservedGenerationContractError("generation point quantity must be numeric") from exc
            status = "OBS" if quantity is not None and observed_eligible else "Q"
            records.append(ObservedGenerationRecord(
                source_series_id=series_id,
                timestamp_utc=timestamp,
                interval_end_utc=interval_end,
                timestep_hours=timestep,
                power_mw=quantity,
                production_type_code=production_type,
                business_type=business_type,
                region_id=HUNGARY_CONTROL_AREA,
                region_scheme=CONTROL_AREA_SCHEME,
                evidence_status=status,
                source_refs=(provenance.source_id,),
                source_revision=provenance.source_revision,
                provenance=provenance,
                _obs_verification_token=_OBS_VERIFICATION_TOKEN if status == "OBS" else None,
            ))

    keys: set[tuple[str, datetime]] = set()
    for record in records:
        key = (record.production_type_code, record.timestamp_utc)
        if key in keys:
            raise ObservedGenerationContractError("duplicate production-type/timestamp source key")
        keys.add(key)
    if not records:
        raise ObservedGenerationContractError("payload contains no Hungarian production-direction generation records")
    return ObservedGenerationBatch(
        records=tuple(sorted(records, key=lambda row: (row.production_type_code, row.timestamp_utc))),
        request_start_utc=request_start,
        request_end_utc=request_end,
        excluded_consumption_series_count=excluded_consumption,
        source_refs=(provenance.source_id,),
    )


def to_b09_supply_records(
    batch: ObservedGenerationBatch,
    *,
    expected_production_types: Iterable[str],
) -> tuple[SupplyRecord, ...]:
    """Convert a complete source-native MW panel to canonical B09 kW DER rows.

    The expected production-type set is explicit because ENTSO-E does not require a
    platform configuration declaring every production type expected for an area.
    Absence is therefore never inferred to mean zero.
    """
    expected_types = tuple(sorted(set(expected_production_types)))
    if not expected_types or any(not isinstance(code, str) or not PSR_TYPE_RE.fullmatch(code) for code in expected_types):
        raise ObservedGenerationContractError("expected_production_types must be a non-empty set of source-native Bxx codes")
    actual_types = tuple(sorted({row.production_type_code for row in batch.records}))
    if actual_types != expected_types:
        raise ObservedGenerationContractError("observed production types do not match the explicit acquisition manifest")
    timesteps = {row.timestep_hours for row in batch.records}
    if len(timesteps) != 1:
        raise ObservedGenerationContractError("mixed generation timestep cannot enter one B09 supply panel")
    timestep = next(iter(timesteps))
    expected_timestamps: list[datetime] = []
    cursor = batch.request_start_utc
    while cursor < batch.request_end_utc:
        expected_timestamps.append(cursor)
        cursor += timedelta(hours=timestep)
    if cursor != batch.request_end_utc:
        raise ObservedGenerationContractError("request window is not divisible by the source timestep")
    actual_keys = {(row.production_type_code, row.timestamp_utc) for row in batch.records}
    expected_keys = {(code, timestamp) for code in expected_types for timestamp in expected_timestamps}
    if actual_keys != expected_keys:
        raise ObservedGenerationContractError("generation panel is incomplete; missing is not zero")
    if any(row.power_mw is None for row in batch.records):
        raise ObservedGenerationContractError("missing generation quantity blocks B09 handoff; it cannot become zero")

    result: list[SupplyRecord] = []
    for row in batch.records:
        power_mw = _finite_nonnegative(row.power_mw, "power_mw")
        result.append(SupplyRecord(
            timestamp=row.timestamp_utc,
            timestep_hours=row.timestep_hours,
            source_component_id=f"ENTSOE_PSR_{row.production_type_code}",
            region_id=row.region_id,
            region_scheme=row.region_scheme,
            truth_context="REAL",
            evidence_status="DER" if row.evidence_status == "OBS" else "Q",
            source_refs=row.source_refs,
            delivered_generation_kw=power_mw * 1000.0,
        ))
    return tuple(result)
