"""B10-P27 fail-closed real programme node-panel admission contract.

Core rules:

    P9 INTERNAL PANEL COMPLETENESS != PROGRAMME COHORT COMPLETENESS
    SUPPLIED ENTITY SET != AUTHORITATIVE PROGRAMME COHORT
    EXACT NODE MAPPING != COHORT COMPLETENESS
    REAL PROGRAMME NODE PANEL != NATIONAL PROGRAMME TOTAL UNLESS SCOPE AUTHORITY SAYS SO
    MISSING ENTITY/TIMESTAMP != ZERO

P9 correctly proves whether the rows it receives form a complete entity x timestamp
panel at exact DSO-substation mappings. P27 adds the missing outer admission gate:
whether that supplied entity set and timestamp window are exactly the authoritative
REAL programme cohort/window for the declared scope.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Iterable

from .programme_node_demand_contract import (
    B10ProgrammeNodeDemandError,
    NODE_DEMAND_PROVEN,
    ProgrammeDemandSnapshot,
    ProgrammeNodeDemandResult,
    aggregate_programme_node_demand,
)


class B10RealProgrammeNodePanelError(ValueError):
    """Raised when real programme panel completeness or authority is overstated."""


PROGRAMME_COHORT_MANIFEST = "PROGRAMME_COHORT_MANIFEST"
PROGRAMME_ENTITY_MEMBERSHIP = "PROGRAMME_ENTITY_MEMBERSHIP"
PROGRAMME_PANEL_TIMESTAMP = "PROGRAMME_PANEL_TIMESTAMP"

REAL_PROGRAMME_NODE_PANEL_PROVEN = "REAL_PROGRAMME_NODE_PANEL_PROVEN"
Q_REAL_PROGRAMME_NODE_PANEL_UNRESOLVED = "Q_REAL_PROGRAMME_NODE_PANEL_UNRESOLVED"

REAL = "REAL"
EVIDENCE_STATUSES = {"OBS", "DER", "Q"}

PANEL_ID_PREFIX = "PANEL_ID:"
PROGRAMME_ID_PREFIX = "PROGRAMME_ID:"
COHORT_ID_PREFIX = "COHORT_ID:"
SCOPE_ID_PREFIX = "SCOPE_ID:"
ENTITY_ID_PREFIX = "ENTITY_ID:"
TIMESTAMP_PREFIX = "TIMESTAMP:"
EXPECTED_ENTITY_COUNT_PREFIX = "EXPECTED_ENTITY_COUNT:"
EXPECTED_TIMESTAMP_COUNT_PREFIX = "EXPECTED_TIMESTAMP_COUNT:"

_COHORT_AUTHORITY_MAX_LEVEL = 3


def _text(value: str, name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise B10RealProgrammeNodePanelError(f"{name} is required")
    return value


def _aware_utc(value: datetime, name: str) -> datetime:
    if not isinstance(value, datetime) or value.tzinfo is None or value.utcoffset() is None:
        raise B10RealProgrammeNodePanelError(f"{name} must be timezone-aware")
    return value.astimezone(timezone.utc)


@dataclass(frozen=True)
class ProgrammeCohortEvidence:
    source_id: str
    authority_level: int
    truth_status: str
    supports: tuple[str, ...]

    def __post_init__(self) -> None:
        _text(self.source_id, "source_id")
        if self.authority_level not in {1, 2, 3, 4, 5}:
            raise B10RealProgrammeNodePanelError("authority_level must be 1..5")
        if self.truth_status not in EVIDENCE_STATUSES:
            raise B10RealProgrammeNodePanelError("truth_status must be OBS, DER or Q")
        if isinstance(self.supports, str):
            raise B10RealProgrammeNodePanelError("supports must be a collection")
        if any(not isinstance(item, str) or not item.strip() for item in self.supports):
            raise B10RealProgrammeNodePanelError("supports cannot contain blanks")


@dataclass(frozen=True)
class RealProgrammeCohortManifest:
    panel_id: str
    programme_id: str
    cohort_id: str
    scope_id: str
    expected_entity_ids: tuple[str, ...]
    expected_timestamps: tuple[datetime, ...]
    source_refs: tuple[str, ...]
    evidence: tuple[ProgrammeCohortEvidence, ...]
    truth_context: str = REAL

    def __post_init__(self) -> None:
        for name in ("panel_id", "programme_id", "cohort_id", "scope_id"):
            _text(getattr(self, name), name)
        if self.truth_context != REAL:
            raise B10RealProgrammeNodePanelError("P27 admits REAL programme cohorts only")
        if isinstance(self.expected_entity_ids, str) or not self.expected_entity_ids:
            raise B10RealProgrammeNodePanelError("expected_entity_ids must be non-empty")
        if any(not isinstance(item, str) or not item.strip() for item in self.expected_entity_ids):
            raise B10RealProgrammeNodePanelError("expected_entity_ids cannot contain blanks")
        if len(set(self.expected_entity_ids)) != len(self.expected_entity_ids):
            raise B10RealProgrammeNodePanelError("expected_entity_ids must be unique")
        if isinstance(self.expected_timestamps, datetime) or not self.expected_timestamps:
            raise B10RealProgrammeNodePanelError("expected_timestamps must be non-empty")
        normalized = tuple(_aware_utc(item, "expected timestamp") for item in self.expected_timestamps)
        if len(set(normalized)) != len(normalized):
            raise B10RealProgrammeNodePanelError("expected_timestamps must be unique")
        object.__setattr__(self, "expected_timestamps", normalized)
        if isinstance(self.source_refs, str) or not self.source_refs:
            raise B10RealProgrammeNodePanelError("source_refs must be non-empty")
        if any(not isinstance(item, str) or not item.strip() for item in self.source_refs):
            raise B10RealProgrammeNodePanelError("source_refs cannot contain blanks")
        if isinstance(self.evidence, str) or not self.evidence:
            raise B10RealProgrammeNodePanelError("evidence must be non-empty")
        evidence_ids = {item.source_id for item in self.evidence}
        if not set(self.source_refs).issubset(evidence_ids):
            raise B10RealProgrammeNodePanelError("source_refs must identify supplied evidence")

    @property
    def referenced_evidence(self) -> tuple[ProgrammeCohortEvidence, ...]:
        refs = set(self.source_refs)
        return tuple(item for item in self.evidence if item.source_id in refs)


@dataclass(frozen=True)
class RealProgrammeNodePanelDecision:
    panel_id: str
    programme_id: str
    cohort_id: str
    scope_id: str
    truth_context: str
    status: str
    evidence_status: str
    expected_entity_count: int
    actual_entity_count: int
    expected_timestamp_count: int
    actual_timestamp_count: int
    node_demand_result: ProgrammeNodeDemandResult | None
    unresolved_entity_ids: tuple[str, ...]
    missing_entity_ids: tuple[str, ...]
    extra_entity_ids: tuple[str, ...]
    missing_timestamps: tuple[datetime, ...]
    extra_timestamps: tuple[datetime, ...]
    source_refs: tuple[str, ...]
    reason: str

    def __post_init__(self) -> None:
        if self.status not in {
            REAL_PROGRAMME_NODE_PANEL_PROVEN,
            Q_REAL_PROGRAMME_NODE_PANEL_UNRESOLVED,
        }:
            raise B10RealProgrammeNodePanelError("invalid real programme node-panel status")
        if self.status == REAL_PROGRAMME_NODE_PANEL_PROVEN:
            if self.evidence_status == "Q" or self.node_demand_result is None:
                raise B10RealProgrammeNodePanelError("proven real panel requires non-Q P9 result")
            if self.node_demand_result.status != NODE_DEMAND_PROVEN:
                raise B10RealProgrammeNodePanelError("proven real panel requires NODE_DEMAND_PROVEN")
            if any(
                (
                    self.unresolved_entity_ids,
                    self.missing_entity_ids,
                    self.extra_entity_ids,
                    self.missing_timestamps,
                    self.extra_timestamps,
                )
            ):
                raise B10RealProgrammeNodePanelError("proven real panel cannot carry completeness gaps")
        elif self.node_demand_result is not None:
            raise B10RealProgrammeNodePanelError("Q real panel must withhold numeric P9 node result")


def _manifest_required_claims(manifest: RealProgrammeCohortManifest) -> set[str]:
    return {
        PROGRAMME_COHORT_MANIFEST,
        f"{PANEL_ID_PREFIX}{manifest.panel_id}",
        f"{PROGRAMME_ID_PREFIX}{manifest.programme_id}",
        f"{COHORT_ID_PREFIX}{manifest.cohort_id}",
        f"{SCOPE_ID_PREFIX}{manifest.scope_id}",
        f"{EXPECTED_ENTITY_COUNT_PREFIX}{len(manifest.expected_entity_ids)}",
        f"{EXPECTED_TIMESTAMP_COUNT_PREFIX}{len(manifest.expected_timestamps)}",
        *(f"{PROGRAMME_ENTITY_MEMBERSHIP}:{entity_id}" for entity_id in manifest.expected_entity_ids),
        *(f"{PROGRAMME_PANEL_TIMESTAMP}:{timestamp.isoformat()}" for timestamp in manifest.expected_timestamps),
    }


def _manifest_authority(manifest: RealProgrammeCohortManifest) -> tuple[bool, str]:
    required = _manifest_required_claims(manifest)
    qualifying = tuple(
        item
        for item in manifest.referenced_evidence
        if item.authority_level <= _COHORT_AUTHORITY_MAX_LEVEL
        and item.truth_status in {"OBS", "DER"}
        and required.issubset(set(item.supports))
    )
    if not qualifying:
        return False, "Q"
    status = "OBS" if all(item.truth_status == "OBS" for item in qualifying) else "DER"
    return True, status


def certify_real_programme_node_panel(
    manifest: RealProgrammeCohortManifest,
    snapshots: Iterable[ProgrammeDemandSnapshot],
) -> RealProgrammeNodePanelDecision:
    """Certify one REAL programme cohort panel without inferring absent rows.

    The cohort manifest must authoritatively identify the exact expected entity set
    and timestamp set. P9 then proves the supplied panel internally and aggregates it
    at exact P8 DSO-substation mappings. Any mismatch returns Q and withholds all P9
    numeric node rows/peaks from this stronger P27 decision.
    """

    if not isinstance(manifest, RealProgrammeCohortManifest):
        raise B10RealProgrammeNodePanelError("manifest must be RealProgrammeCohortManifest")
    values = tuple(snapshots)
    if any(not isinstance(item, ProgrammeDemandSnapshot) for item in values):
        raise B10RealProgrammeNodePanelError("all snapshots must be ProgrammeDemandSnapshot")

    expected_entities = set(manifest.expected_entity_ids)
    expected_timestamps = set(manifest.expected_timestamps)
    actual_entities = {item.source_entity_id for item in values}
    actual_timestamps = {item.timestamp for item in values}

    missing_entities = tuple(sorted(expected_entities - actual_entities))
    extra_entities = tuple(sorted(actual_entities - expected_entities))
    missing_timestamps = tuple(sorted(expected_timestamps - actual_timestamps))
    extra_timestamps = tuple(sorted(actual_timestamps - expected_timestamps))

    manifest_ok, manifest_status = _manifest_authority(manifest)
    refs = tuple(
        sorted(
            set(manifest.source_refs)
            | {ref for item in values for ref in item.source_refs}
            | {ref for item in values for ref in item.spatial_authority.source_refs}
        )
    )

    def q(reason: str, unresolved: tuple[str, ...] = ()) -> RealProgrammeNodePanelDecision:
        return RealProgrammeNodePanelDecision(
            panel_id=manifest.panel_id,
            programme_id=manifest.programme_id,
            cohort_id=manifest.cohort_id,
            scope_id=manifest.scope_id,
            truth_context=manifest.truth_context,
            status=Q_REAL_PROGRAMME_NODE_PANEL_UNRESOLVED,
            evidence_status="Q",
            expected_entity_count=len(expected_entities),
            actual_entity_count=len(actual_entities),
            expected_timestamp_count=len(expected_timestamps),
            actual_timestamp_count=len(actual_timestamps),
            node_demand_result=None,
            unresolved_entity_ids=tuple(sorted(set(unresolved))),
            missing_entity_ids=missing_entities,
            extra_entity_ids=extra_entities,
            missing_timestamps=missing_timestamps,
            extra_timestamps=extra_timestamps,
            source_refs=refs,
            reason=reason,
        )

    if not manifest_ok:
        return q("no referenced authority proves the exact REAL programme cohort and timestamp manifest")
    if not values:
        return q("authoritative cohort manifest exists but no real programme demand rows were supplied")
    if any(item.truth_context != REAL for item in values):
        return q("P27 real programme admission rejects SCN or mixed truth-context rows")
    if any(item.scope_id != manifest.scope_id for item in values):
        return q("one or more demand rows do not match the authoritative programme scope")
    if missing_entities or extra_entities:
        return q("supplied entity set does not exactly equal the authoritative programme cohort")
    if missing_timestamps or extra_timestamps:
        return q("supplied timestamp set does not exactly equal the authoritative panel window")

    try:
        p9 = aggregate_programme_node_demand(values)
    except B10ProgrammeNodeDemandError as exc:
        return q(f"P9 internal entity/timestamp panel gate failed: {exc}")
    if p9.status != NODE_DEMAND_PROVEN or not p9.rows:
        return q(
            "P9 exact-node programme demand remains unresolved; P27 cannot certify the real panel",
            p9.unresolved_entity_ids,
        )
    if p9.scope_id != manifest.scope_id or p9.truth_context != REAL:
        return q("P9 result does not preserve the manifest scope and REAL truth context")

    p9_entities = {item.source_entity_id for item in values}
    if p9_entities != expected_entities:
        return q("post-P9 entity set does not preserve the authoritative cohort")

    p9_statuses = {row.evidence_status for row in p9.rows}
    evidence_status = "OBS" if manifest_status == "OBS" and p9_statuses == {"OBS"} else "DER"
    return RealProgrammeNodePanelDecision(
        panel_id=manifest.panel_id,
        programme_id=manifest.programme_id,
        cohort_id=manifest.cohort_id,
        scope_id=manifest.scope_id,
        truth_context=REAL,
        status=REAL_PROGRAMME_NODE_PANEL_PROVEN,
        evidence_status=evidence_status,
        expected_entity_count=len(expected_entities),
        actual_entity_count=len(actual_entities),
        expected_timestamp_count=len(expected_timestamps),
        actual_timestamp_count=len(actual_timestamps),
        node_demand_result=p9,
        unresolved_entity_ids=(),
        missing_entity_ids=(),
        extra_entity_ids=(),
        missing_timestamps=(),
        extra_timestamps=(),
        source_refs=refs,
        reason=(
            "authoritative REAL cohort/window exactly matches the supplied entity x timestamp panel; "
            "P9 proves complete exact-node aggregation without treating missing rows as zero"
        ),
    )


def require_real_programme_node_panel(
    decision: RealProgrammeNodePanelDecision,
) -> ProgrammeNodeDemandResult:
    if not isinstance(decision, RealProgrammeNodePanelDecision):
        raise B10RealProgrammeNodePanelError("decision must be RealProgrammeNodePanelDecision")
    if (
        decision.status != REAL_PROGRAMME_NODE_PANEL_PROVEN
        or decision.node_demand_result is None
    ):
        raise B10RealProgrammeNodePanelError("proven REAL programme node panel is required")
    return decision.node_demand_result


__all__ = [
    "B10RealProgrammeNodePanelError",
    "PROGRAMME_COHORT_MANIFEST",
    "PROGRAMME_ENTITY_MEMBERSHIP",
    "PROGRAMME_PANEL_TIMESTAMP",
    "ProgrammeCohortEvidence",
    "Q_REAL_PROGRAMME_NODE_PANEL_UNRESOLVED",
    "REAL_PROGRAMME_NODE_PANEL_PROVEN",
    "RealProgrammeCohortManifest",
    "RealProgrammeNodePanelDecision",
    "certify_real_programme_node_panel",
    "require_real_programme_node_panel",
]
