"""B10-P28 fail-closed REAL managed-peak network-study input admission.

Core rules:

    REAL PROGRAMME NODE PANEL != MANAGED PEAK STUDY INPUT
    P10 MANAGED NODE LOAD != NETWORK STUDY INPUT
    NUMERIC PEAK MATCH != STUDY-CASE BINDING
    STUDY INPUT != NETWORK SURVIVABILITY RESULT
    STUDY INPUT != LIMITING NODE
    MISSING STUDY NODE != NON_LIMITING NODE

P27 proves that the supplied REAL entity x timestamp demand panel is the exact
authoritative programme cohort/window. P10 can then derive a managed exact-node
load only from exact flex lineage. P28 adds the missing study-case admission gate:
claim-specific authoritative evidence must explicitly bind those exact managed
node peaks to one exact network study/case/horizon before downstream survivability
or limiting-node reasoning can consume them as study inputs.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from .incremental_reinforcement_contract import HORIZONS
from .managed_flex_survivability_contract import (
    B10ManagedFlexSurvivabilityError,
    MANAGED_NODE_LOAD_PROVEN,
    FlexDispatchSnapshot,
    ManagedNodeLoadResult,
    build_managed_node_load,
)
from .programme_node_demand_contract import ProgrammeDemandSnapshot
from .real_programme_node_panel_contract import (
    REAL_PROGRAMME_NODE_PANEL_PROVEN,
    RealProgrammeCohortManifest,
    certify_real_programme_node_panel,
)


class B10ManagedPeakStudyInputError(ValueError):
    """Raised when managed-peak network-study input authority is overstated."""


MANAGED_PEAK_STUDY_INPUT = "MANAGED_PEAK_STUDY_INPUT"
REAL_MANAGED_PEAK_STUDY_INPUT_PROVEN = "REAL_MANAGED_PEAK_STUDY_INPUT_PROVEN"
Q_REAL_MANAGED_PEAK_STUDY_INPUT_UNRESOLVED = "Q_REAL_MANAGED_PEAK_STUDY_INPUT_UNRESOLVED"

REAL = "REAL"
EVIDENCE_STATUSES = {"OBS", "DER", "Q"}
DSO_SUBSTATION = "DSO_SUBSTATION"

STUDY_INPUT_ID_PREFIX = "STUDY_INPUT_ID:"
NETWORK_OPERATOR_PREFIX = "NETWORK_OPERATOR:"
NETWORK_STUDY_ID_PREFIX = "NETWORK_STUDY_ID:"
STUDY_CASE_ID_PREFIX = "STUDY_CASE_ID:"
PANEL_ID_PREFIX = "PANEL_ID:"
PROGRAMME_ID_PREFIX = "PROGRAMME_ID:"
COHORT_ID_PREFIX = "COHORT_ID:"
SCOPE_ID_PREFIX = "SCOPE_ID:"
HORIZON_PREFIX = "HORIZON:"
TRUTH_CONTEXT_PREFIX = "TRUTH_CONTEXT:"
EXPECTED_NODE_COUNT_PREFIX = "EXPECTED_NODE_COUNT:"
STUDY_NODE_PREFIX = "STUDY_NODE:"
MANAGED_PEAK_MW_PREFIX = "MANAGED_PEAK_MW:"
NODE_REGION_GRAIN_BINDING = "NODE_REGION_GRAIN:DSO_SUBSTATION"

_STUDY_INPUT_AUTHORITY_MAX_LEVEL = 2


def _text(value: str, name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise B10ManagedPeakStudyInputError(f"{name} is required")
    return value


def _peak_token(node_id: str, peak_mw: float) -> str:
    return f"{MANAGED_PEAK_MW_PREFIX}{node_id}:{peak_mw}"


@dataclass(frozen=True)
class ManagedPeakStudyInputEvidence:
    source_id: str
    authority_level: int
    truth_status: str
    supports: tuple[str, ...]

    def __post_init__(self) -> None:
        _text(self.source_id, "source_id")
        if self.authority_level not in {1, 2, 3, 4, 5}:
            raise B10ManagedPeakStudyInputError("authority_level must be 1..5")
        if self.truth_status not in EVIDENCE_STATUSES:
            raise B10ManagedPeakStudyInputError("truth_status must be OBS, DER or Q")
        if isinstance(self.supports, str):
            raise B10ManagedPeakStudyInputError("supports must be a collection")
        if any(not isinstance(item, str) or not item.strip() for item in self.supports):
            raise B10ManagedPeakStudyInputError("supports cannot contain blanks")


@dataclass(frozen=True)
class ManagedPeakStudyInputRecord:
    study_input_id: str
    network_operator: str
    network_study_id: str
    study_case_id: str
    panel_id: str
    programme_id: str
    cohort_id: str
    scope_id: str
    horizon: str
    source_refs: tuple[str, ...]
    evidence: tuple[ManagedPeakStudyInputEvidence, ...]
    truth_context: str = REAL
    node_region_scheme: str = DSO_SUBSTATION

    def __post_init__(self) -> None:
        for name in (
            "study_input_id",
            "network_operator",
            "network_study_id",
            "study_case_id",
            "panel_id",
            "programme_id",
            "cohort_id",
            "scope_id",
        ):
            _text(getattr(self, name), name)
        if self.horizon not in HORIZONS:
            raise B10ManagedPeakStudyInputError("horizon must be CURRENT or FIVE_YEAR")
        if self.truth_context != REAL:
            raise B10ManagedPeakStudyInputError("P28 admits REAL managed-peak study inputs only")
        if self.node_region_scheme != DSO_SUBSTATION:
            raise B10ManagedPeakStudyInputError("study input must remain at DSO_SUBSTATION grain")
        if isinstance(self.source_refs, str) or not self.source_refs:
            raise B10ManagedPeakStudyInputError("source_refs must be non-empty")
        if any(not isinstance(ref, str) or not ref.strip() for ref in self.source_refs):
            raise B10ManagedPeakStudyInputError("source_refs cannot contain blanks")
        if isinstance(self.evidence, str) or not self.evidence:
            raise B10ManagedPeakStudyInputError("evidence must be non-empty")
        evidence_ids = {item.source_id for item in self.evidence}
        if not set(self.source_refs).issubset(evidence_ids):
            raise B10ManagedPeakStudyInputError("source_refs must identify supplied evidence")

    @property
    def referenced_evidence(self) -> tuple[ManagedPeakStudyInputEvidence, ...]:
        refs = set(self.source_refs)
        return tuple(item for item in self.evidence if item.source_id in refs)


@dataclass(frozen=True)
class ManagedPeakStudyNode:
    node_region_id: str
    assessed_managed_peak_mw: float
    evidence_status: str

    def __post_init__(self) -> None:
        _text(self.node_region_id, "node_region_id")
        if isinstance(self.assessed_managed_peak_mw, bool) or not isinstance(
            self.assessed_managed_peak_mw, (int, float)
        ):
            raise B10ManagedPeakStudyInputError("assessed_managed_peak_mw must be numeric")
        value = float(self.assessed_managed_peak_mw)
        if value < 0:
            raise B10ManagedPeakStudyInputError("assessed_managed_peak_mw must be non-negative")
        object.__setattr__(self, "assessed_managed_peak_mw", value)
        if self.evidence_status not in {"OBS", "DER"}:
            raise B10ManagedPeakStudyInputError("study-node evidence_status must be OBS or DER")


@dataclass(frozen=True)
class ManagedPeakStudyInputDecision:
    study_input_id: str
    network_operator: str
    network_study_id: str
    study_case_id: str
    panel_id: str
    programme_id: str
    cohort_id: str
    scope_id: str
    horizon: str
    truth_context: str
    status: str
    evidence_status: str
    nodes: tuple[ManagedPeakStudyNode, ...]
    managed_load_result: ManagedNodeLoadResult | None
    source_refs: tuple[str, ...]
    reason: str

    def __post_init__(self) -> None:
        if self.status not in {
            REAL_MANAGED_PEAK_STUDY_INPUT_PROVEN,
            Q_REAL_MANAGED_PEAK_STUDY_INPUT_UNRESOLVED,
        }:
            raise B10ManagedPeakStudyInputError("invalid managed-peak study-input status")
        if self.status == REAL_MANAGED_PEAK_STUDY_INPUT_PROVEN:
            if self.evidence_status not in {"OBS", "DER"}:
                raise B10ManagedPeakStudyInputError("proven study input requires OBS/DER evidence")
            if not self.nodes or self.managed_load_result is None:
                raise B10ManagedPeakStudyInputError("proven study input requires nodes and managed load")
            if self.managed_load_result.status != MANAGED_NODE_LOAD_PROVEN:
                raise B10ManagedPeakStudyInputError("proven study input requires MANAGED_NODE_LOAD_PROVEN")
            if self.managed_load_result.truth_context != REAL:
                raise B10ManagedPeakStudyInputError("proven study input must preserve REAL truth context")
        else:
            if self.evidence_status != "Q":
                raise B10ManagedPeakStudyInputError("Q study input must preserve Q evidence status")
            if self.nodes or self.managed_load_result is not None:
                raise B10ManagedPeakStudyInputError("Q study input must withhold numeric managed peaks")


def _general_binding(record: ManagedPeakStudyInputRecord, node_count: int) -> set[str]:
    return {
        MANAGED_PEAK_STUDY_INPUT,
        f"{STUDY_INPUT_ID_PREFIX}{record.study_input_id}",
        f"{NETWORK_OPERATOR_PREFIX}{record.network_operator}",
        f"{NETWORK_STUDY_ID_PREFIX}{record.network_study_id}",
        f"{STUDY_CASE_ID_PREFIX}{record.study_case_id}",
        f"{PANEL_ID_PREFIX}{record.panel_id}",
        f"{PROGRAMME_ID_PREFIX}{record.programme_id}",
        f"{COHORT_ID_PREFIX}{record.cohort_id}",
        f"{SCOPE_ID_PREFIX}{record.scope_id}",
        f"{HORIZON_PREFIX}{record.horizon}",
        f"{TRUTH_CONTEXT_PREFIX}{record.truth_context}",
        NODE_REGION_GRAIN_BINDING,
        f"{EXPECTED_NODE_COUNT_PREFIX}{node_count}",
    }


def _qualifying_evidence(record: ManagedPeakStudyInputRecord) -> tuple[ManagedPeakStudyInputEvidence, ...]:
    return tuple(
        item
        for item in record.referenced_evidence
        if item.authority_level <= _STUDY_INPUT_AUTHORITY_MAX_LEVEL
        and item.truth_status in {"OBS", "DER"}
    )


def certify_real_managed_peak_study_input(
    record: ManagedPeakStudyInputRecord,
    *,
    cohort_manifest: RealProgrammeCohortManifest,
    programme_snapshots: Iterable[ProgrammeDemandSnapshot],
    flex_snapshots: Iterable[FlexDispatchSnapshot],
) -> ManagedPeakStudyInputDecision:
    """Admit only exact P27/P10 REAL managed peaks into an exact study case."""

    if not isinstance(record, ManagedPeakStudyInputRecord):
        raise B10ManagedPeakStudyInputError("record must be ManagedPeakStudyInputRecord")
    if not isinstance(cohort_manifest, RealProgrammeCohortManifest):
        raise B10ManagedPeakStudyInputError("cohort_manifest must be RealProgrammeCohortManifest")

    demand_values = tuple(programme_snapshots)
    flex_values = tuple(flex_snapshots)
    refs = tuple(
        sorted(
            set(record.source_refs)
            | set(cohort_manifest.source_refs)
            | {ref for item in demand_values for ref in item.source_refs}
            | {ref for item in demand_values for ref in item.spatial_authority.source_refs}
            | {ref for item in flex_values for ref in item.source_refs}
        )
    )

    def q(reason: str) -> ManagedPeakStudyInputDecision:
        return ManagedPeakStudyInputDecision(
            record.study_input_id,
            record.network_operator,
            record.network_study_id,
            record.study_case_id,
            record.panel_id,
            record.programme_id,
            record.cohort_id,
            record.scope_id,
            record.horizon,
            record.truth_context,
            Q_REAL_MANAGED_PEAK_STUDY_INPUT_UNRESOLVED,
            "Q",
            (),
            None,
            refs,
            reason,
        )

    identity_pairs = (
        (record.panel_id, cohort_manifest.panel_id, "panel_id"),
        (record.programme_id, cohort_manifest.programme_id, "programme_id"),
        (record.cohort_id, cohort_manifest.cohort_id, "cohort_id"),
        (record.scope_id, cohort_manifest.scope_id, "scope_id"),
    )
    for record_value, manifest_value, name in identity_pairs:
        if record_value != manifest_value:
            return q(f"study input {name} does not match the authoritative P27 cohort manifest")

    panel = certify_real_programme_node_panel(cohort_manifest, demand_values)
    if panel.status != REAL_PROGRAMME_NODE_PANEL_PROVEN or panel.node_demand_result is None:
        return q("P27 REAL programme node panel is not proven; bounded P9 rows cannot enter the study")

    try:
        managed = build_managed_node_load(demand_values, flex_values)
    except B10ManagedFlexSurvivabilityError as exc:
        return q(f"P10 managed-load gate failed: {exc}")
    if managed.status != MANAGED_NODE_LOAD_PROVEN or managed.truth_context != REAL or not managed.rows:
        return q("P10 REAL managed node load is unresolved; no numeric study input may be admitted")
    if managed.scope_id != record.scope_id:
        return q("P10 managed-load scope does not match the exact study input scope")
    if managed.unmanaged != panel.node_demand_result:
        return q("P10 managed load is not derived from the exact P27-certified programme node panel")

    peaks = tuple(managed.peak_managed_import_mw_by_node)
    if not peaks:
        return q("P10 managed-load result contains no exact-node managed peaks")

    qualifying = _qualifying_evidence(record)
    general = _general_binding(record, len(peaks))
    if not any(general.issubset(set(item.supports)) for item in qualifying):
        return q("no referenced authoritative evidence binds the exact REAL programme panel to this network study case")

    node_statuses: list[str] = []
    for node_id, peak_mw in peaks:
        node_required = general | {
            f"{STUDY_NODE_PREFIX}{node_id}",
            _peak_token(node_id, peak_mw),
        }
        matches = tuple(item for item in qualifying if node_required.issubset(set(item.supports)))
        if not matches:
            return q(
                "one or more exact managed node peaks lack claim-specific binding to the network study case"
            )
        node_statuses.append("OBS" if all(item.truth_status == "OBS" for item in matches) else "DER")

    managed_statuses = {row.evidence_status for row in managed.rows}
    study_status = "OBS" if all(item.truth_status == "OBS" for item in qualifying) else "DER"
    evidence_status = (
        "OBS"
        if panel.evidence_status == "OBS"
        and managed_statuses == {"OBS"}
        and study_status == "OBS"
        and set(node_statuses) == {"OBS"}
        else "DER"
    )
    nodes = tuple(
        ManagedPeakStudyNode(node_id, peak_mw, evidence_status)
        for node_id, peak_mw in peaks
    )
    return ManagedPeakStudyInputDecision(
        record.study_input_id,
        record.network_operator,
        record.network_study_id,
        record.study_case_id,
        record.panel_id,
        record.programme_id,
        record.cohort_id,
        record.scope_id,
        record.horizon,
        REAL,
        REAL_MANAGED_PEAK_STUDY_INPUT_PROVEN,
        evidence_status,
        nodes,
        managed,
        refs,
        (
            "the exact P27-certified REAL cohort/window and exact P10 managed node peaks are explicitly "
            "bound by authoritative evidence to the declared network study/case/horizon"
        ),
    )


def require_real_managed_peak_study_input(
    decision: ManagedPeakStudyInputDecision,
) -> ManagedNodeLoadResult:
    if not isinstance(decision, ManagedPeakStudyInputDecision):
        raise B10ManagedPeakStudyInputError("decision must be ManagedPeakStudyInputDecision")
    if (
        decision.status != REAL_MANAGED_PEAK_STUDY_INPUT_PROVEN
        or decision.managed_load_result is None
    ):
        raise B10ManagedPeakStudyInputError("proven REAL managed-peak study input is required")
    return decision.managed_load_result


def require_study_node_peak(
    decision: ManagedPeakStudyInputDecision,
    node_region_id: str,
) -> float:
    """Return a numeric peak only when that exact node is proven as study input."""

    _text(node_region_id, "node_region_id")
    require_real_managed_peak_study_input(decision)
    matches = [item for item in decision.nodes if item.node_region_id == node_region_id]
    if len(matches) != 1:
        raise B10ManagedPeakStudyInputError("exact node is not uniquely proven in the managed-peak study input")
    return matches[0].assessed_managed_peak_mw


__all__ = [
    "B10ManagedPeakStudyInputError",
    "MANAGED_PEAK_STUDY_INPUT",
    "ManagedPeakStudyInputDecision",
    "ManagedPeakStudyInputEvidence",
    "ManagedPeakStudyInputRecord",
    "ManagedPeakStudyNode",
    "Q_REAL_MANAGED_PEAK_STUDY_INPUT_UNRESOLVED",
    "REAL_MANAGED_PEAK_STUDY_INPUT_PROVEN",
    "certify_real_managed_peak_study_input",
    "require_real_managed_peak_study_input",
    "require_study_node_peak",
]
