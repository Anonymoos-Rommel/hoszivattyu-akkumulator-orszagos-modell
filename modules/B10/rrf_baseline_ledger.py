"""B10-P4 observed baseline applications for the two bounded RRF projects.

This module materialises exactly two project-level records through the
canonical B10-P3 contract. It does not introduce another classifier, a
headroom path, a national aggregate, or programme-incremental CAPEX model.

Field-specific provenance is explicit: completion publications prove OBS
OPERATING status, while exact financial values are accepted only from the
referenced source that actually publishes that precision.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from .baseline_infrastructure_contract import (
    BASELINE,
    B10BaselineInfrastructureContractError,
    InfrastructureEvidence,
    InfrastructureRecord,
    OPERATING,
    classify_infrastructure,
)


MVM_DEMASZ_RRF_PROJECT_ID = "RRF-6.1.1-21-2022-00006"
OPUS_TITASZ_RRF_PROJECT_ID = "RRF-6.1.1-21-2022-00001"
MVM_DEMASZ_RRF_BASELINE_ID = f"B10-BASE-MVM-DEMASZ-{MVM_DEMASZ_RRF_PROJECT_ID}"
OPUS_TITASZ_RRF_BASELINE_ID = f"B10-BASE-OPUS-TITASZ-{OPUS_TITASZ_RRF_PROJECT_ID}"
RRF_ASSET_TYPE = "MULTI_ASSET_DSO_NETWORK_DEVELOPMENT_PROGRAM"
DSO_SERVICE_AREA = "DSO_SERVICE_AREA"
MVM_DEMASZ_SERVICE_AREA = "MVM_DEMASZ:SERVICE_AREA"
OPUS_TITASZ_SERVICE_AREA = "OPUS_TITASZ:SERVICE_AREA"
RRF_COMPLETION_DATE = "2026-06-15"

MVM_DEMASZ_RRF_PROJECT_SOURCE_ID = "SRC-B10-MVM-DEMASZ-RRF-PROJECT-2026"
MVM_DEMASZ_RRF_COMPLETION_SOURCE_ID = "SRC-B10-MVM-DEMASZ-RRF-COMPLETION-2026"
OPUS_TITASZ_RRF_PROJECT_SOURCE_ID = "SRC-B10-OPUS-TITASZ-RRF-PROJECT-2026"
OPUS_TITASZ_RRF_COMPLETION_SOURCE_ID = "SRC-B10-OPUS-TITASZ-RRF-COMPLETION-2026"


@dataclass(frozen=True)
class _RrfProjectSpec:
    baseline_id: str
    project_id: str
    network_operator: str
    owner: str
    region_id: str
    scope_description: str
    counterfactual_cost_huf: int | None
    project_source_id: str
    completion_source_id: str
    project_supports_exact_cost: bool


_SPECS = (
    _RrfProjectSpec(
        baseline_id=MVM_DEMASZ_RRF_BASELINE_ID,
        project_id=MVM_DEMASZ_RRF_PROJECT_ID,
        network_operator="MVM DEMASZ",
        owner="MVM Démász Áramhálózati Kft.",
        region_id=MVM_DEMASZ_SERVICE_AREA,
        scope_description=(
            "Completed umbrella DSO service-area RRF network-development project: "
            "substations, MV/LV and digital network upgrades."
        ),
        counterfactual_cost_huf=None,
        project_source_id=MVM_DEMASZ_RRF_PROJECT_SOURCE_ID,
        completion_source_id=MVM_DEMASZ_RRF_COMPLETION_SOURCE_ID,
        project_supports_exact_cost=False,
    ),
    _RrfProjectSpec(
        baseline_id=OPUS_TITASZ_RRF_BASELINE_ID,
        project_id=OPUS_TITASZ_RRF_PROJECT_ID,
        network_operator="OPUS TITÁSZ",
        owner="OPUS TITÁSZ Zrt.",
        region_id=OPUS_TITASZ_SERVICE_AREA,
        scope_description=(
            "Completed umbrella DSO service-area RRF network-development project: "
            "HV/MV/LV, substation, reliability and digital upgrades."
        ),
        counterfactual_cost_huf=41_489_280_000,
        project_source_id=OPUS_TITASZ_RRF_PROJECT_SOURCE_ID,
        completion_source_id=OPUS_TITASZ_RRF_COMPLETION_SOURCE_ID,
        project_supports_exact_cost=True,
    ),
)


def _record(spec: _RrfProjectSpec) -> InfrastructureRecord:
    # The official project pages bind exact project/funding facts. For OPUS the
    # project page explicitly publishes the exact total project cost, therefore
    # it is represented as level-3 funding/cost evidence. It does NOT prove
    # OPERATING status; that remains completion-source authority only.
    project_supports = ["PROJECT_ID", "OPERATOR", "PROJECT_SCOPE"]
    project_authority_level = 4
    if spec.project_supports_exact_cost:
        project_supports.extend(("FUNDED_OR_ALLOCATED", "COST"))
        project_authority_level = 3
    project_evidence = InfrastructureEvidence(
        source_id=spec.project_source_id,
        authority_level=project_authority_level,
        truth_status="OBS",
        effective_date=RRF_COMPLETION_DATE,
        revision="PROJECT_PAGE_CURRENT_2026",
        supports=tuple(project_supports),
    )

    completion_evidence = InfrastructureEvidence(
        source_id=spec.completion_source_id,
        authority_level=3,
        truth_status="OBS",
        effective_date=RRF_COMPLETION_DATE,
        revision="COMPLETION_2026-06-15",
        supports=(
            "PROJECT_ID",
            "OPERATOR",
            "OPERATING",
            "FUNDED_OR_ALLOCATED",
            "REALISED_RENEWABLE_GENERATION_INTEGRATION_CAPABILITY_MW",
        ),
    )

    # Reference every source required by published machine claims. MVM keeps
    # both project and completion sources for project/grant context + status;
    # OPUS additionally requires its project source for the exact cost value.
    source_refs = (spec.project_source_id, spec.completion_source_id)

    return InfrastructureRecord(
        project_id=spec.project_id,
        network_operator=spec.network_operator,
        owner=spec.owner,
        region_id=spec.region_id,
        region_grain=DSO_SERVICE_AREA,
        infrastructure_type=RRF_ASSET_TYPE,
        status_taxonomy=OPERATING,
        status_effective_date=RRF_COMPLETION_DATE,
        source_refs=source_refs,
        evidence=(project_evidence, completion_evidence),
        evidence_status="OBS",
        contractual_or_funding_status="FUNDED_OR_ALLOCATED",
        without_program_required=True,
        with_program_required=True,
        program_causality_status="Q",
        total_project_cost_huf=spec.counterfactual_cost_huf,
    )


RRF_BASELINE_RECORDS = tuple(_record(spec) for spec in _SPECS)


def validate_observed_baseline_record(record: InfrastructureRecord) -> None:
    """Validate P4 identity, grain and field-specific provenance."""

    spec = next((item for item in _SPECS if item.project_id == record.project_id), None)
    if spec is None:
        raise B10BaselineInfrastructureContractError(
            f"unsupported B10-P4 project identity: {record.project_id!r}"
        )
    if record.region_grain != DSO_SERVICE_AREA or record.region_id != spec.region_id:
        raise B10BaselineInfrastructureContractError(
            "B10-P4 records must remain at DSO_SERVICE_AREA project grain"
        )
    if record.infrastructure_type != RRF_ASSET_TYPE:
        raise B10BaselineInfrastructureContractError(
            "B10-P4 records must use the bounded multi-asset DSO project type"
        )
    if record.status_taxonomy != OPERATING or record.status_effective_date != RRF_COMPLETION_DATE:
        raise B10BaselineInfrastructureContractError(
            "B10-P4 records require the official 2026-06-15 OPERATING completion date"
        )

    referenced = {item.source_id for item in record.referenced_evidence}
    if spec.completion_source_id not in referenced:
        raise B10BaselineInfrastructureContractError(
            "B10-P4 records must reference the exact project completion source"
        )
    if not any(
        item.source_id == spec.completion_source_id
        and "OPERATING" in item.supports
        and item.truth_status == "OBS"
        for item in record.referenced_evidence
    ):
        raise B10BaselineInfrastructureContractError(
            "B10-P4 completion source must explicitly support OBS OPERATING"
        )

    if record.total_project_cost_huf is not None:
        if not spec.project_supports_exact_cost:
            raise B10BaselineInfrastructureContractError(
                "B10-P4 exact project cost is not source-authorised for this project"
            )
        if spec.project_source_id not in referenced:
            raise B10BaselineInfrastructureContractError(
                "B10-P4 exact project cost requires the exact project/funding source"
            )
        if not any(
            item.source_id == spec.project_source_id
            and item.authority_level <= 3
            and "COST" in item.supports
            and item.truth_status == "OBS"
            for item in record.referenced_evidence
        ):
            raise B10BaselineInfrastructureContractError(
                "B10-P4 project/funding source must explicitly support exact OBS COST"
            )


def classify_observed_baseline_projects(
    records: Iterable[InfrastructureRecord] = RRF_BASELINE_RECORDS,
):
    """Classify the bounded P4 records through the canonical P3 classifier."""

    output = []
    for record in records:
        validate_observed_baseline_record(record)
        decision = classify_infrastructure(record)
        if decision.attribution_status != BASELINE or decision.evidence_status != "OBS":
            raise B10BaselineInfrastructureContractError(
                f"B10-P4 observed baseline did not classify as OBS BASELINE: {record.project_id}"
            )
        output.append(decision)
    return tuple(output)


__all__ = [
    "DSO_SERVICE_AREA",
    "MVM_DEMASZ_RRF_BASELINE_ID",
    "MVM_DEMASZ_RRF_COMPLETION_SOURCE_ID",
    "MVM_DEMASZ_RRF_PROJECT_ID",
    "MVM_DEMASZ_RRF_PROJECT_SOURCE_ID",
    "MVM_DEMASZ_SERVICE_AREA",
    "OPUS_TITASZ_RRF_BASELINE_ID",
    "OPUS_TITASZ_RRF_COMPLETION_SOURCE_ID",
    "OPUS_TITASZ_RRF_PROJECT_ID",
    "OPUS_TITASZ_RRF_PROJECT_SOURCE_ID",
    "OPUS_TITASZ_SERVICE_AREA",
    "RRF_ASSET_TYPE",
    "RRF_BASELINE_RECORDS",
    "RRF_COMPLETION_DATE",
    "classify_observed_baseline_projects",
    "validate_observed_baseline_record",
]
