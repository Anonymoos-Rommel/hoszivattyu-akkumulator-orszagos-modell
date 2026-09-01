"""Fail-closed baseline/incremental infrastructure attribution contract.

This is the B10-P3 authority slice.  It deliberately separates the
``WITHOUT_PROGRAM`` and ``WITH_PROGRAM`` worlds.  A project being announced or
delivered during the programme window is not, by itself, proof of programme
causality or incremental CAPEX.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from math import isfinite
from typing import Iterable


class B10BaselineInfrastructureContractError(ValueError):
    """Raised when an attribution would be ambiguous or double counted."""


WITHOUT_PROGRAM = "WITHOUT_PROGRAM"
WITH_PROGRAM = "WITH_PROGRAM"

OPERATING = "OPERATING"
UNDER_CONSTRUCTION = "UNDER_CONSTRUCTION"
CONTRACTED = "CONTRACTED"
BUDGETED_OR_ALLOCATED = "BUDGETED_OR_ALLOCATED"
OPEN_TENDER = "OPEN_TENDER"
ANNOUNCED_UNFUNDED = "ANNOUNCED_UNFUNDED"
PROGRAM_ACCELERATED_OR_UPSIZED = "PROGRAM_ACCELERATED_OR_UPSIZED"

BASELINE = "BASELINE"
PROGRAM_ACCELERATED = "PROGRAM_ACCELERATED_OR_UPSIZED"
PROGRAM_INCREMENTAL = "PROGRAM_INCREMENTAL"
UNRESOLVED = "Q"

BASELINE_STATUSES = {
    OPERATING,
    UNDER_CONSTRUCTION,
    CONTRACTED,
    BUDGETED_OR_ALLOCATED,
    OPEN_TENDER,
    ANNOUNCED_UNFUNDED,
    PROGRAM_ACCELERATED_OR_UPSIZED,
}
EVIDENCE_STATUSES = {"OBS", "DER", "ASS", "SCN", "POL", "Q"}
CAUSALITY_STATUSES = {"DER", "SCN", "Q"}
HIGH_AUTHORITY_LEVELS = {1, 2, 3, 4}


def _iso_date(value: str | None, field_name: str) -> str | None:
    if value is None or value == "":
        return None
    if not isinstance(value, str):
        raise B10BaselineInfrastructureContractError(f"{field_name} must be ISO date text")
    try:
        date.fromisoformat(value)
    except ValueError as exc:
        raise B10BaselineInfrastructureContractError(f"{field_name} must be ISO date text") from exc
    return value


def _money(value: float | None, field_name: str) -> float | None:
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not isfinite(value) or value < 0:
        raise B10BaselineInfrastructureContractError(f"{field_name} must be finite and non-negative")
    return float(value)


@dataclass(frozen=True)
class InfrastructureEvidence:
    """One auditable source assertion about a project.

    ``authority_level`` follows the B10-P3 hierarchy: 1 regulatory/authority,
    2 DSO/MAVIR plan, 3 tender/contract/funding, 4 official project notice,
    5 other.  ``OBS`` is acceptable for a source-native status assertion, but
    never for programme causality.
    """

    source_id: str
    authority_level: int
    truth_status: str
    effective_date: str | None
    revision: str | None = None
    supports: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.source_id, str) or not self.source_id.strip():
            raise B10BaselineInfrastructureContractError("evidence source_id is required")
        if self.authority_level not in {1, 2, 3, 4, 5}:
            raise B10BaselineInfrastructureContractError("authority_level must be 1..5")
        if self.truth_status not in EVIDENCE_STATUSES:
            raise B10BaselineInfrastructureContractError("invalid evidence truth status")
        if self.truth_status == "OBS" and "PROGRAM_CAUSALITY" in self.supports:
            raise B10BaselineInfrastructureContractError(
                "program causality cannot be OBS"
            )
        _iso_date(self.effective_date, "effective_date")
        if self.revision is not None and not str(self.revision).strip():
            raise B10BaselineInfrastructureContractError("revision cannot be blank")
        if isinstance(self.supports, str):
            raise B10BaselineInfrastructureContractError("supports must be a collection")


@dataclass(frozen=True)
class InfrastructureRecord:
    """Canonical project-level input for baseline classification."""

    project_id: str
    network_operator: str
    owner: str
    region_id: str
    region_grain: str
    infrastructure_type: str
    status_taxonomy: str
    status_effective_date: str | None
    source_refs: tuple[str, ...]
    evidence: tuple[InfrastructureEvidence, ...]
    evidence_status: str
    contractual_or_funding_status: str | None = None
    without_program_required: bool | None = None
    with_program_required: bool | None = None
    program_causality_status: str = "Q"
    temporal_coincidence_only: bool = False
    total_project_cost_huf: float | None = None
    baseline_cost_huf: float | None = None
    incremental_cost_huf: float | None = None
    cost_component_id: str | None = None
    incremental_scope_proven: bool = False
    incremental_capacity_proven: bool = False
    acceleration_proven: bool = False
    upsizing_proven: bool = False
    unresolved_reason: str | None = None

    def __post_init__(self) -> None:
        for field_name in (
            "project_id",
            "network_operator",
            "owner",
            "region_id",
            "region_grain",
            "infrastructure_type",
        ):
            if not isinstance(getattr(self, field_name), str) or not getattr(self, field_name).strip():
                raise B10BaselineInfrastructureContractError(f"{field_name} is required")
        if self.status_taxonomy not in BASELINE_STATUSES:
            raise B10BaselineInfrastructureContractError("invalid status_taxonomy")
        _iso_date(self.status_effective_date, "status_effective_date")
        if isinstance(self.source_refs, str) or not self.source_refs:
            raise B10BaselineInfrastructureContractError("source_refs must be non-empty")
        if isinstance(self.evidence, str) or not self.evidence:
            raise B10BaselineInfrastructureContractError("evidence must be non-empty")
        evidence_ids = {item.source_id for item in self.evidence}
        if not set(self.source_refs).issubset(evidence_ids):
            raise B10BaselineInfrastructureContractError(
                "source_refs must identify supplied evidence records"
            )
        if self.evidence_status not in EVIDENCE_STATUSES:
            raise B10BaselineInfrastructureContractError("invalid evidence_status")
        for field_name in ("without_program_required", "with_program_required"):
            value = getattr(self, field_name)
            if value is not None and not isinstance(value, bool):
                raise B10BaselineInfrastructureContractError(
                    f"{field_name} must be bool or explicit None"
                )
        if self.program_causality_status not in CAUSALITY_STATUSES:
            if self.program_causality_status == "OBS":
                raise B10BaselineInfrastructureContractError("program causality cannot be OBS")
            raise B10BaselineInfrastructureContractError(
                "program_causality_status must be DER, SCN or Q"
            )
        if self.temporal_coincidence_only and self.program_causality_status != "Q":
            raise B10BaselineInfrastructureContractError(
                "temporal coincidence cannot prove programme causality"
            )
        if self.program_causality_status == "OBS":
            raise B10BaselineInfrastructureContractError("program causality cannot be OBS")
        _money(self.total_project_cost_huf, "total_project_cost_huf")
        _money(self.baseline_cost_huf, "baseline_cost_huf")
        _money(self.incremental_cost_huf, "incremental_cost_huf")
        if self.incremental_cost_huf is not None and self.total_project_cost_huf is not None:
            if self.incremental_cost_huf > self.total_project_cost_huf:
                raise B10BaselineInfrastructureContractError(
                    "incremental cost cannot exceed total project cost"
                )
            if self.incremental_cost_huf == self.total_project_cost_huf and self.total_project_cost_huf > 0:
                raise B10BaselineInfrastructureContractError(
                    "total project cost cannot be copied as full incremental cost"
                )
        if self.cost_component_id is not None and not self.cost_component_id.strip():
            raise B10BaselineInfrastructureContractError("cost_component_id cannot be blank")

    @property
    def effective_source_refs(self) -> tuple[str, ...]:
        return tuple(dict.fromkeys(self.source_refs))

    @property
    def has_high_authority_evidence(self) -> bool:
        return any(item.authority_level in HIGH_AUTHORITY_LEVELS for item in self.evidence)

    @property
    def has_effective_revision(self) -> bool:
        return bool(self.status_effective_date) and all(
            item.effective_date is not None for item in self.evidence
        )

    @property
    def cost_is_source_supported(self) -> bool:
        return any(
            item.authority_level <= 3 and "COST" in item.supports
            for item in self.evidence
        )


@dataclass(frozen=True)
class AttributionDecision:
    project_id: str
    status_taxonomy: str
    attribution_status: str
    evidence_status: str
    source_refs: tuple[str, ...]
    counterfactual_basis: str
    baseline_cost_huf: float | None
    incremental_cost_huf: float | None
    reason: str


@dataclass(frozen=True)
class CostAttribution:
    """A cost component assigned to one and only one accounting world."""

    project_id: str
    cost_component_id: str
    baseline_full_cost_huf: float | None
    incremental_cost_huf: float | None
    attribution_status: str
    source_refs: tuple[str, ...]

    def __post_init__(self) -> None:
        if not self.project_id.strip() or not self.cost_component_id.strip():
            raise B10BaselineInfrastructureContractError("project and cost component identity are required")
        if self.attribution_status not in {BASELINE, PROGRAM_ACCELERATED, PROGRAM_INCREMENTAL, UNRESOLVED}:
            raise B10BaselineInfrastructureContractError("invalid attribution status")
        if not self.source_refs:
            raise B10BaselineInfrastructureContractError("cost attribution requires source_refs")
        _money(self.baseline_full_cost_huf, "baseline_full_cost_huf")
        _money(self.incremental_cost_huf, "incremental_cost_huf")
        if self.baseline_full_cost_huf is not None and self.incremental_cost_huf is not None:
            if self.baseline_full_cost_huf > 0 and self.incremental_cost_huf > 0:
                raise B10BaselineInfrastructureContractError(
                    "one cost component cannot be both baseline full cost and incremental cost"
                )


def _base_evidence_ok(record: InfrastructureRecord) -> bool:
    return (
        record.has_high_authority_evidence
        and record.has_effective_revision
        and set(record.source_refs).issubset({item.source_id for item in record.evidence})
    )


def classify_infrastructure(record: InfrastructureRecord) -> AttributionDecision:
    """Classify one record, returning ``Q`` whenever attribution is unproven."""

    refs = record.effective_source_refs
    if record.without_program_required is None or record.with_program_required is None:
        return AttributionDecision(
            record.project_id,
            record.status_taxonomy,
            UNRESOLVED,
            "Q",
            refs,
            f"{WITHOUT_PROGRAM}/{WITH_PROGRAM} fields are not explicit",
            None,
            None,
            "both counterfactual worlds must be explicitly represented",
        )
    if not _base_evidence_ok(record):
        return AttributionDecision(
            record.project_id,
            record.status_taxonomy,
            UNRESOLVED,
            "Q",
            refs,
            f"{WITHOUT_PROGRAM}/{WITH_PROGRAM} evidence boundary incomplete",
            None,
            None,
            "missing authoritative source, effective date/revision, or source identity",
        )

    if record.status_taxonomy in {
        OPERATING,
        UNDER_CONSTRUCTION,
        CONTRACTED,
        BUDGETED_OR_ALLOCATED,
    } and not (record.without_program_required and record.with_program_required):
        return AttributionDecision(
            record.project_id,
            record.status_taxonomy,
            UNRESOLVED,
            "Q",
            refs,
            f"{WITHOUT_PROGRAM} baseline flag is inconsistent with status",
            None,
            None,
            "an existing/contracted project must be present in both explicit worlds",
        )

    if (
        any(value is not None for value in (
            record.total_project_cost_huf,
            record.baseline_cost_huf,
            record.incremental_cost_huf,
        ))
        and not record.cost_is_source_supported
    ):
        return AttributionDecision(
            record.project_id,
            record.status_taxonomy,
            UNRESOLVED,
            "Q",
            refs,
            f"{WITHOUT_PROGRAM}/{WITH_PROGRAM} cost boundary is unresolved",
            None,
            None,
            "numeric CAPEX requires explicit contract/funding/authority evidence",
        )

    if record.temporal_coincidence_only or record.program_causality_status == "Q":
        if record.status_taxonomy in {
            OPERATING,
            UNDER_CONSTRUCTION,
            CONTRACTED,
            BUDGETED_OR_ALLOCATED,
        }:
            return AttributionDecision(
                record.project_id,
                record.status_taxonomy,
                BASELINE,
                record.evidence_status,
                refs,
                f"{WITHOUT_PROGRAM} includes the already operating/contracted/funded scope",
                record.total_project_cost_huf,
                None,
                "programme causality is not proven; existing scope is baseline",
            )
        return AttributionDecision(
            record.project_id,
            record.status_taxonomy,
            UNRESOLVED,
            "Q",
            refs,
            f"{WITHOUT_PROGRAM}/{WITH_PROGRAM} distinction is unresolved",
            None,
            None,
            "announced/open-tender status or temporal coincidence cannot establish baseline or increment",
        )

    if record.program_causality_status not in {"DER", "SCN"}:
        raise B10BaselineInfrastructureContractError("causality requires DER or SCN, or explicit Q")

    difference_proven = any(
        (
            record.incremental_scope_proven,
            record.incremental_capacity_proven,
            record.acceleration_proven,
            record.upsizing_proven,
        )
    )
    expected_incremental_flags = (
        (True, True)
        if record.status_taxonomy in {
            OPERATING,
            UNDER_CONSTRUCTION,
            CONTRACTED,
            BUDGETED_OR_ALLOCATED,
        }
        else (False, True)
    )
    if difference_proven and (record.without_program_required, record.with_program_required) != expected_incremental_flags:
        return AttributionDecision(
            record.project_id,
            record.status_taxonomy,
            UNRESOLVED,
            "Q",
            refs,
            f"{WITHOUT_PROGRAM}/{WITH_PROGRAM} flags do not show an incremental difference",
            None,
            None,
            "incremental attribution requires absent-without-program and present-with-program",
        )
    if not difference_proven:
        return AttributionDecision(
            record.project_id,
            record.status_taxonomy,
            UNRESOLVED,
            "Q",
            refs,
            f"{WITHOUT_PROGRAM} vs {WITH_PROGRAM} has no separately proven difference",
            None,
            None,
            "causality assertion lacks incremental scope, capacity, acceleration, or upsizing evidence",
        )
    if record.incremental_cost_huf is None:
        return AttributionDecision(
            record.project_id,
            record.status_taxonomy,
            PROGRAM_ACCELERATED if record.status_taxonomy != ANNOUNCED_UNFUNDED else PROGRAM_INCREMENTAL,
            "Q",
            refs,
            f"{WITHOUT_PROGRAM} vs {WITH_PROGRAM} difference is identified but cost is unquantified",
            None,
            None,
            "incremental amount remains Q; no numeric CAPEX may be invented",
        )
    if not record.cost_is_source_supported:
        return AttributionDecision(
            record.project_id,
            record.status_taxonomy,
            UNRESOLVED,
            "Q",
            refs,
            f"{WITHOUT_PROGRAM} vs {WITH_PROGRAM} difference is identified",
            None,
            None,
            "numeric cost lacks contract/funding/authority support",
        )
    status = PROGRAM_ACCELERATED if record.status_taxonomy in {
        UNDER_CONSTRUCTION,
        CONTRACTED,
        BUDGETED_OR_ALLOCATED,
        OPERATING,
    } else PROGRAM_INCREMENTAL
    return AttributionDecision(
        record.project_id,
        PROGRAM_ACCELERATED_OR_UPSIZED if status == PROGRAM_ACCELERATED else record.status_taxonomy,
        status,
        record.evidence_status if record.evidence_status != "OBS" else "DER",
        refs,
        f"explicit {WITHOUT_PROGRAM}/{WITH_PROGRAM} difference",
        record.baseline_cost_huf,
        record.incremental_cost_huf,
        "only the proven incremental component is attributable",
    )


def validate_attribution_ledger(
    records: Iterable[InfrastructureRecord],
    attributions: Iterable[CostAttribution],
) -> None:
    """Reject duplicate project/component identities and baseline double count."""

    records = tuple(records)
    attributions = tuple(attributions)
    record_map = {record.project_id: record for record in records}
    if len(record_map) != len(records):
        raise B10BaselineInfrastructureContractError("duplicate project identity")
    seen: set[tuple[str, str]] = set()
    for attribution in attributions:
        key = (attribution.project_id, attribution.cost_component_id)
        if key in seen:
            raise B10BaselineInfrastructureContractError(f"duplicate project/cost component: {key!r}")
        seen.add(key)
        record = record_map.get(attribution.project_id)
        if record is None:
            raise B10BaselineInfrastructureContractError(f"unknown project identity: {attribution.project_id!r}")
        if record.status_taxonomy == ANNOUNCED_UNFUNDED and attribution.attribution_status == BASELINE:
            raise B10BaselineInfrastructureContractError(
                "ANNOUNCED_UNFUNDED cannot be promoted to baseline"
            )
        if attribution.attribution_status == BASELINE and attribution.incremental_cost_huf:
            raise B10BaselineInfrastructureContractError("baseline record cannot carry incremental cost")
        if attribution.attribution_status in {PROGRAM_ACCELERATED, PROGRAM_INCREMENTAL}:
            if attribution.baseline_full_cost_huf and attribution.incremental_cost_huf:
                raise B10BaselineInfrastructureContractError(
                    "baseline and incremental full cost are double counted"
                )


def assert_no_full_cost_copy(record: InfrastructureRecord) -> None:
    """Explicit guard for the forbidden ``incremental_cost = total_cost`` rule."""

    if (
        record.total_project_cost_huf is not None
        and record.incremental_cost_huf is not None
        and record.total_project_cost_huf > 0
        and record.incremental_cost_huf == record.total_project_cost_huf
    ):
        raise B10BaselineInfrastructureContractError(
            "total project cost cannot be copied into incremental CAPEX"
        )


__all__ = [
    "ANNOUNCED_UNFUNDED",
    "AttributionDecision",
    "BASELINE",
    "BASELINE_STATUSES",
    "B10BaselineInfrastructureContractError",
    "BUDGETED_OR_ALLOCATED",
    "CONTRACTED",
    "CostAttribution",
    "InfrastructureEvidence",
    "InfrastructureRecord",
    "OPEN_TENDER",
    "OPERATING",
    "PROGRAM_ACCELERATED",
    "PROGRAM_ACCELERATED_OR_UPSIZED",
    "PROGRAM_INCREMENTAL",
    "UNRESOLVED",
    "UNDER_CONSTRUCTION",
    "WITH_PROGRAM",
    "WITHOUT_PROGRAM",
    "assert_no_full_cost_copy",
    "classify_infrastructure",
    "validate_attribution_ledger",
]
