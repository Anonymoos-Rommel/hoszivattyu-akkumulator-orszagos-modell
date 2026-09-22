"""B10-P67 national network-impact inference layer.

P67 applies the project-wide population-inference policy to network modelling
without weakening exact DSO-node, MGT, network-study or project-CAPEX claims.

NO COMPLETE NATIONAL NODE INVENTORY != NATIONAL MODEL BLOCKED
NO DEFENSIBLE NETWORK POPULATION INFERENCE == NATIONAL MODEL BLOCKED
NATIONAL NETWORK ESTIMATE != SPECIFIC NODE PASS/FAIL
PUBLIC REPOSITORY MATERIALIZATION != MODEL USABILITY

The national/programme layer may use representative/calibrated DSO-node and
reinforcement evidence with explicit uncertainty. Specific node, reinforcement
and CAPEX claims remain fail-closed and exact.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
P64_COVERAGE = ROOT / "registry" / "dso_service_area_membership_p64_operational_coverage.csv"
NODE_SOURCES = ROOT / "registry" / "dso_node_inventory_sources.csv"
BASELINE_INFRA = ROOT / "registry" / "baseline_infrastructure.csv"

NATIONAL_NETWORK_INFERENCE = "NATIONAL_NETWORK_INFERENCE"
EXACT_NODE_AUTHORITY = "EXACT_NODE_AUTHORITY"
SOURCE_ACCESS_AND_PROVENANCE = "SOURCE_ACCESS_AND_PROVENANCE"

QUALIFIED_SPATIAL_SURFACE = "QUALIFIED_OPERATIONAL_SPATIAL_SURFACE"
QUALIFIED_SOURCE_COVERAGE = "QUALIFIED_ALL_DSO_NODE_SOURCE_COVERAGE"
CALIBRATION_ONLY_PROJECT_COHORT = "CALIBRATION_ONLY_SMALL_BASELINE_PROJECT_COHORT"
Q_NATIONAL_NETWORK_INFERENCE = "Q_NATIONAL_NETWORK_INFERENCE"
QUALIFIED_NATIONAL_BOUNDED_NETWORK_INFERENCE = (
    "QUALIFIED_NATIONAL_BOUNDED_NETWORK_INFERENCE"
)

PREFERRED_INDEPENDENT_STRATA = 3
MINIMUM_INDEPENDENT_STRATA = 2


@dataclass(frozen=True)
class BlockerRepair:
    legacy_blocker: str
    replacement: str
    plane: str
    status: str
    exact_claim_boundary: str


@dataclass(frozen=True)
class CurrentEvidenceSurface:
    resolved_spatial_share_pct: float
    unresolved_spatial_share_pct: float
    canonical_dso_count: int
    bounded_node_source_dso_count: int
    baseline_project_count: int
    baseline_project_operator_count: int
    spatial_status: str
    node_source_status: str
    baseline_project_status: str


@dataclass(frozen=True)
class NationalNetworkInferenceAdmission:
    status: str
    blockers: tuple[str, ...]
    warnings: tuple[str, ...]


_REPAIRS = (
    BlockerRepair(
        "NO_COMPLETE_KSH_DSO_MEMBERSHIP_CROSSWALK",
        "DISCLOSED_RESIDUAL_SPATIAL_UNCERTAINTY_REQUIRED",
        NATIONAL_NETWORK_INFERENCE,
        "RETIRED_AS_NATIONAL_MODELLING_BLOCKER",
        "EXACT_UNRESOLVED_LOCATION_STILL_REQUIRES_EXACT_DSO_MEMBERSHIP",
    ),
    BlockerRepair(
        "PARTIAL_SETTLEMENT_USAGE_LOCATION_RESOLUTION_REQUIRED",
        "DISCLOSED_RESIDUAL_SPATIAL_UNCERTAINTY_REQUIRED",
        NATIONAL_NETWORK_INFERENCE,
        "RETIRED_AS_NATIONAL_MODELLING_BLOCKER",
        "EXACT_PARTIAL_SETTLEMENT_CLAIM_REQUIRES_USAGE_LOCATION_AUTHORITY",
    ),
    BlockerRepair(
        "NO_COMPLETE_NATIONAL_DSO_NODE_INVENTORY",
        "DEFENSIBLE_REPRESENTATIVE_NODE_COHORT_REQUIRED",
        NATIONAL_NETWORK_INFERENCE,
        "RETIRED_AS_NATIONAL_EXPECTED_IMPACT_BLOCKER",
        "EXHAUSTIVE_LIMITING_NODE_CLAIM_REQUIRES_COMPLETE_RELEVANT_NODE_AUTHORITY",
    ),
    BlockerRepair(
        "HEADROOM_NODE_SET_NOT_INVENTORY_COMPLETENESS",
        "REPRESENTATIVE_HEADROOM_SAMPLE_WITH_SCOPE_AND_UNCERTAINTY_REQUIRED",
        NATIONAL_NETWORK_INFERENCE,
        "REFRAMED_AS_INFERENCE_REQUIREMENT",
        "PUBLISHED_HEADROOM_ROW_STILL_CANNOT_MINT_UNPUBLISHED_NODE_OR_TOPOLOGY",
    ),
    BlockerRepair(
        "PUBLISHED_NODE_SET_REPOSITORY_MATERIALIZATION_BLOCKED",
        "SOURCE_ACCESS_PROVENANCE_AND_RUNTIME_USE_AUTHORITY_REQUIRED",
        SOURCE_ACCESS_AND_PROVENANCE,
        "RETIRED_AS_PUBLIC_REPOSITORY_PREREQUISITE",
        "RAW_REPUBLICATION_STILL_REQUIRES_REUSE_PERMISSION",
    ),
    BlockerRepair(
        "NO_REAL_PROGRAMME_NODE_PANEL",
        "DEFENSIBLE_PROGRAMME_DEMAND_DISTRIBUTION_BY_DSO_STRATUM_REQUIRED",
        NATIONAL_NETWORK_INFERENCE,
        "REFRAMED_AS_POPULATION_INFERENCE_REQUIREMENT",
        "SPECIFIC_NODE_DEMAND_CLAIM_REQUIRES_EXACT_ENTITY_TO_NODE_MAPPING",
    ),
    BlockerRepair(
        "NO_REAL_MANAGED_PEAK_SURVIVABILITY_STUDY",
        "DEFENSIBLE_MANAGED_PEAK_SURVIVABILITY_INFERENCE_REQUIRED",
        NATIONAL_NETWORK_INFERENCE,
        "REFRAMED_AS_POPULATION_INFERENCE_REQUIREMENT",
        "SPECIFIC_NODE_SURVIVABILITY_CLAIM_REQUIRES_CLAIM_SPECIFIC_NETWORK_STUDY",
    ),
    BlockerRepair(
        "INCREMENTAL_CAPEX_ATTRIBUTION_HEADER_ONLY",
        "REPRESENTATIVE_REINFORCEMENT_COHORT_AND_INCREMENTAL_CAPEX_DISTRIBUTION_REQUIRED",
        NATIONAL_NETWORK_INFERENCE,
        "REFRAMED_AS_POPULATION_INFERENCE_REQUIREMENT",
        "SPECIFIC_PROJECT_PROGRAMME_CAPEX_REQUIRES_EXACT_P3_P5_P31_P32_LINEAGE",
    ),
    BlockerRepair(
        "NO_REAL_TIMED_PROGRAMME_CAPEX",
        "DEFENSIBLE_REINFORCEMENT_DELIVERY_TIMING_DISTRIBUTION_REQUIRED",
        NATIONAL_NETWORK_INFERENCE,
        "REFRAMED_AS_POPULATION_INFERENCE_REQUIREMENT",
        "SPECIFIC_PROJECT_TIMED_CAPEX_REQUIRES_EXACT_P11_P32_P33_LINEAGE",
    ),
)


def blocker_repairs() -> tuple[BlockerRepair, ...]:
    return _REPAIRS


def repaired_requirement(legacy_blocker: str) -> BlockerRepair:
    for repair in _REPAIRS:
        if repair.legacy_blocker == legacy_blocker:
            return repair
    raise KeyError(legacy_blocker)


def current_evidence_surface() -> CurrentEvidenceSurface:
    with P64_COVERAGE.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    if len(rows) != 1 or rows[0]["scope"] != "NATIONAL":
        raise ValueError("P64 national operational coverage row is missing")
    p64 = rows[0]

    with NODE_SOURCES.open(encoding="utf-8", newline="") as handle:
        node_sources = list(csv.DictReader(handle))
    operator_ids = {row["operator_id"] for row in node_sources}
    bounded = {
        row["operator_id"]
        for row in node_sources
        if row["node_source_status"] == "NODE_BEARING_SOURCE_BOUNDED"
    }

    with BASELINE_INFRA.open(encoding="utf-8", newline="") as handle:
        projects = list(csv.DictReader(handle))
    baseline = [row for row in projects if row["status"] == "BASELINE"]

    return CurrentEvidenceSurface(
        resolved_spatial_share_pct=float(p64["any_effective_resolution_share_pct"]),
        unresolved_spatial_share_pct=float(p64["no_effective_resolution_share_pct"]),
        canonical_dso_count=len(operator_ids),
        bounded_node_source_dso_count=len(bounded),
        baseline_project_count=len(baseline),
        baseline_project_operator_count=len({row["network_operator"] for row in baseline}),
        spatial_status=QUALIFIED_SPATIAL_SURFACE,
        node_source_status=(
            QUALIFIED_SOURCE_COVERAGE
            if operator_ids and bounded == operator_ids
            else "PARTIAL_DSO_NODE_SOURCE_COVERAGE"
        ),
        baseline_project_status=CALIBRATION_ONLY_PROJECT_COHORT,
    )


def assess_national_network_inference(
    *,
    independent_dso_strata: int,
    programme_demand_distribution: bool,
    representative_headroom_cohort: bool,
    reinforcement_project_cohort: bool,
    programme_incremental_capex_attribution: bool,
    delivery_timing_distribution: bool,
    managed_peak_survivability_model: bool,
    population_calibration: bool,
    uncertainty_explicit: bool,
) -> NationalNetworkInferenceAdmission:
    """Assess national bounded inference, never a specific-node/project claim."""

    if independent_dso_strata < 0:
        raise ValueError("independent_dso_strata cannot be negative")

    blockers: list[str] = []
    warnings: list[str] = []

    if independent_dso_strata < MINIMUM_INDEPENDENT_STRATA:
        blockers.append("AT_LEAST_TWO_INDEPENDENT_DSO_STRATA_REQUIRED")
    elif independent_dso_strata < PREFERRED_INDEPENDENT_STRATA:
        warnings.append("FEWER_THAN_PREFERRED_THREE_INDEPENDENT_DSO_STRATA")

    if not programme_demand_distribution:
        blockers.append("DEFENSIBLE_PROGRAMME_DEMAND_DISTRIBUTION_BY_DSO_STRATUM_REQUIRED")
    if not representative_headroom_cohort:
        blockers.append("REPRESENTATIVE_HEADROOM_SAMPLE_WITH_SCOPE_AND_UNCERTAINTY_REQUIRED")
    if not reinforcement_project_cohort:
        blockers.append("REPRESENTATIVE_REINFORCEMENT_PROJECT_COHORT_REQUIRED")
    if not programme_incremental_capex_attribution:
        blockers.append(
            "REPRESENTATIVE_REINFORCEMENT_COHORT_AND_INCREMENTAL_CAPEX_DISTRIBUTION_REQUIRED"
        )
    if not delivery_timing_distribution:
        blockers.append("DEFENSIBLE_REINFORCEMENT_DELIVERY_TIMING_DISTRIBUTION_REQUIRED")
    if not managed_peak_survivability_model:
        blockers.append("DEFENSIBLE_MANAGED_PEAK_SURVIVABILITY_INFERENCE_REQUIRED")
    if not population_calibration:
        blockers.append("NETWORK_POPULATION_CALIBRATION_REQUIRED")
    if not uncertainty_explicit:
        blockers.append("NETWORK_INFERENCE_UNCERTAINTY_REQUIRED")

    status = (
        QUALIFIED_NATIONAL_BOUNDED_NETWORK_INFERENCE
        if not blockers
        else Q_NATIONAL_NETWORK_INFERENCE
    )
    return NationalNetworkInferenceAdmission(status, tuple(blockers), tuple(warnings))


def exact_claim_boundary() -> tuple[str, ...]:
    return (
        "NATIONAL_NETWORK_ESTIMATE_CANNOT_PASS_A_SPECIFIC_NODE",
        "SPECIFIC_NODE_DEMAND_REQUIRES_EXACT_ENTITY_TO_NODE_MAPPING",
        "SPECIFIC_REINFORCEMENT_REQUIRES_AUTHORITATIVE_DSO_MGT_OR_NETWORK_STUDY",
        "SPECIFIC_PROGRAMME_INCREMENTAL_CAPEX_REQUIRES_EXACT_ATTRIBUTION_LINEAGE",
        "SPECIFIC_TIMED_CAPEX_REQUIRES_EXACT_PROJECT_COMPONENT_SCHEDULE_LINEAGE",
    )
