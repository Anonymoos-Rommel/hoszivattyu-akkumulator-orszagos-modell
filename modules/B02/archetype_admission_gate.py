"""Fail-closed admission gates for B02 archetype claims.

B02-P9 separates three things that must not be conflated:

1. a contracted archetype dimension schema;
2. a populated current-stock archetype assignment;
3. technical-readiness enrichment of that stock assignment.

A contracted schema is repository architecture, not evidence that the required
joint population exists. B02-P14 proves that source-native WBL011 full-joint
availability is not the same as repository materialization. B02-P15 now
materializes that complete WBL011 stock joint, so the current stock claim
remains Q only because building-type linkage and primary-energy linkage are
still not authoritative.

B02-P12 additionally requires an independently QUALIFIED calibrated-linkage
admission before model-status tokens may satisfy the building-type or
primary-energy link gates. A status string cannot self-authorize a model.

B02-P16 defines the direct building-type authority boundary. B02-P17 wires
that direct-authority result into this P9 gate and defines the symmetric direct
primary-energy boundary: raw OBS/DER tokens are not sufficient unless a
separate direct-link admission is QUALIFIED.

B02-P18 applies the same rule to technical-readiness enrichment. A raw OBS/DER
heat-emitter or temperature token is evidence status, not stock-level direct
authority. Current-state emitter evidence and current-system design-temperature
evidence require separate direct admission at the same WBL stock grain or a
reproducible dwelling-record binding. Reference or operating temperatures do
not self-authorize the design-temperature gate.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import isfinite


Q = "Q"
QUALIFIED = "QUALIFIED"
CONTRACTED = "CONTRACTED"

REAL_EVIDENCE = frozenset({"OBS", "DER"})
BUILDING_TYPE_LINK_OK = frozenset({"OBS", "DER", "APPROVED_CALIBRATED_MODEL"})
ENERGY_LINK_OK = frozenset({"OBS", "DER", "MODELLED_LINKED"})

DIRECT_WBL_GRAINS = frozenset({"WBL_FULL_JOINT", "DWELLING_RECORD"})
PRIMARY_ENERGY_METRICS = frozenset(
    {"SPECIFIC_PRIMARY_ENERGY_KWH_M2_YEAR", "PRIMARY_ENERGY_BIN"}
)
EMITTER_EVIDENCE_TYPES = frozenset(
    {"TEXT_EXPLICIT", "TABLE_EXPLICIT", "SCHEMATIC_EXPLICIT", "PHOTO_EXPLICIT"}
)
DESIGN_TEMPERATURE_BASES = frozenset({"DESIGN_EXPLICIT", "CALCULATION_INPUT"})
REQUIRED_STOCK_UNIVERSE = "OCCUPIED_DWELLING_STOCK"


@dataclass(frozen=True)
class AdmissionDecision:
    status: str
    blockers: tuple[str, ...]


@dataclass(frozen=True)
class PrimaryEnergyAuthorityCandidate:
    source_id: str
    reference_year: int
    source_universe: str
    source_grain: str
    evidence_status: str
    primary_energy_metric: str
    publishes_complete_assignment: bool
    wbl_compatible_join_key: bool
    reproducible_repository_binding: bool


@dataclass(frozen=True)
class PrimaryEnergyAuthorityDecision:
    status: str
    reasons: tuple[str, ...]


def assess_direct_primary_energy_authority(
    candidate: PrimaryEnergyAuthorityCandidate,
) -> PrimaryEnergyAuthorityDecision:
    """Admit only a reproducible direct current-stock primary-energy link.

    Direct OBS/DER authority requires occupied-stock scope and either the
    primary-energy metric to be published in the complete WBL joint or a
    reproducible dwelling-record binding to that stock. MODELLED assignments
    are not direct evidence and must use the separate P12 calibrated-model path.
    """

    reasons: list[str] = []
    if candidate.reference_year < 2022:
        reasons.append("REFERENCE_YEAR_BEFORE_2022")
    if candidate.source_universe != REQUIRED_STOCK_UNIVERSE:
        reasons.append("NOT_OCCUPIED_DWELLING_STOCK")
    if candidate.source_grain not in DIRECT_WBL_GRAINS:
        reasons.append("GRAIN_NOT_DIRECT_WBL_LINK")
    if candidate.evidence_status not in REAL_EVIDENCE:
        reasons.append("EVIDENCE_NOT_OBS_OR_DER")
    if candidate.primary_energy_metric not in PRIMARY_ENERGY_METRICS:
        reasons.append("PRIMARY_ENERGY_METRIC_NOT_COMPATIBLE")
    if not candidate.publishes_complete_assignment:
        reasons.append("NO_COMPLETE_PRIMARY_ENERGY_ASSIGNMENT")
    if not candidate.wbl_compatible_join_key:
        reasons.append("NO_WBL_COMPATIBLE_JOIN_KEY")
    if not candidate.reproducible_repository_binding:
        reasons.append("NO_REPRODUCIBLE_REPOSITORY_BINDING")

    if reasons:
        return PrimaryEnergyAuthorityDecision(Q, tuple(reasons))
    return PrimaryEnergyAuthorityDecision(QUALIFIED, ())


@dataclass(frozen=True)
class HeatEmitterAuthorityCandidate:
    source_id: str
    reference_year: int
    source_universe: str
    source_grain: str
    evidence_status: str
    current_state_explicit: bool
    emitter_evidence_type: str
    evidence_locator_present: bool
    publishes_complete_assignment: bool
    wbl_compatible_join_key: bool
    reproducible_repository_binding: bool


@dataclass(frozen=True)
class HeatEmitterAuthorityDecision:
    status: str
    reasons: tuple[str, ...]


def assess_direct_heat_emitter_authority(
    candidate: HeatEmitterAuthorityCandidate,
) -> HeatEmitterAuthorityDecision:
    """Admit only explicit current-emitter evidence bound to the stock claim."""

    reasons: list[str] = []
    if candidate.reference_year < 2022:
        reasons.append("REFERENCE_YEAR_BEFORE_2022")
    if candidate.source_universe != REQUIRED_STOCK_UNIVERSE:
        reasons.append("NOT_OCCUPIED_DWELLING_STOCK")
    if candidate.source_grain not in DIRECT_WBL_GRAINS:
        reasons.append("GRAIN_NOT_DIRECT_WBL_LINK")
    if candidate.evidence_status not in REAL_EVIDENCE:
        reasons.append("EVIDENCE_NOT_OBS_OR_DER")
    if not candidate.current_state_explicit:
        reasons.append("CURRENT_EMITTER_STATE_NOT_EXPLICIT")
    if candidate.emitter_evidence_type not in EMITTER_EVIDENCE_TYPES:
        reasons.append("EMITTER_EVIDENCE_NOT_EXPLICIT")
    if not candidate.evidence_locator_present:
        reasons.append("NO_EMITTER_EVIDENCE_LOCATOR")
    if not candidate.publishes_complete_assignment:
        reasons.append("NO_COMPLETE_HEAT_EMITTER_ASSIGNMENT")
    if not candidate.wbl_compatible_join_key:
        reasons.append("NO_WBL_COMPATIBLE_JOIN_KEY")
    if not candidate.reproducible_repository_binding:
        reasons.append("NO_REPRODUCIBLE_REPOSITORY_BINDING")

    if reasons:
        return HeatEmitterAuthorityDecision(Q, tuple(reasons))
    return HeatEmitterAuthorityDecision(QUALIFIED, ())


@dataclass(frozen=True)
class DesignTemperatureAuthorityCandidate:
    source_id: str
    reference_year: int
    source_universe: str
    source_grain: str
    evidence_status: str
    current_state_explicit: bool
    temperature_basis: str
    supply_temperature_c: float | None
    return_temperature_c: float | None
    evidence_locator_present: bool
    publishes_complete_assignment: bool
    wbl_compatible_join_key: bool
    reproducible_repository_binding: bool


@dataclass(frozen=True)
class DesignTemperatureAuthorityDecision:
    status: str
    reasons: tuple[str, ...]


def assess_direct_design_temperature_authority(
    candidate: DesignTemperatureAuthorityCandidate,
) -> DesignTemperatureAuthorityDecision:
    """Admit only current-system design/calculation temperature evidence.

    P1K permits OPERATING_MEASURED as observed temperature evidence, but the P9
    blocker is specifically current design-temperature evidence. Operating
    measurements and REFERENCE_ASSUMPTION values therefore remain useful
    evidence/context but cannot satisfy this narrower direct authority gate.
    """

    reasons: list[str] = []
    if candidate.reference_year < 2022:
        reasons.append("REFERENCE_YEAR_BEFORE_2022")
    if candidate.source_universe != REQUIRED_STOCK_UNIVERSE:
        reasons.append("NOT_OCCUPIED_DWELLING_STOCK")
    if candidate.source_grain not in DIRECT_WBL_GRAINS:
        reasons.append("GRAIN_NOT_DIRECT_WBL_LINK")
    if candidate.evidence_status not in REAL_EVIDENCE:
        reasons.append("EVIDENCE_NOT_OBS_OR_DER")
    if not candidate.current_state_explicit:
        reasons.append("CURRENT_SYSTEM_STATE_NOT_EXPLICIT")
    if candidate.temperature_basis not in DESIGN_TEMPERATURE_BASES:
        reasons.append("TEMPERATURE_BASIS_NOT_DESIGN_AUTHORITY")

    supply = candidate.supply_temperature_c
    ret = candidate.return_temperature_c
    if supply is None or ret is None:
        reasons.append("DESIGN_TEMPERATURE_PAIR_INCOMPLETE")
    elif (
        not isfinite(supply)
        or not isfinite(ret)
        or supply < -50
        or supply > 150
        or ret < -50
        or ret > 150
        or supply <= ret
    ):
        reasons.append("DESIGN_TEMPERATURE_PAIR_INVALID")

    if not candidate.evidence_locator_present:
        reasons.append("NO_TEMPERATURE_EVIDENCE_LOCATOR")
    if not candidate.publishes_complete_assignment:
        reasons.append("NO_COMPLETE_DESIGN_TEMPERATURE_ASSIGNMENT")
    if not candidate.wbl_compatible_join_key:
        reasons.append("NO_WBL_COMPATIBLE_JOIN_KEY")
    if not candidate.reproducible_repository_binding:
        reasons.append("NO_REPRODUCIBLE_REPOSITORY_BINDING")

    if reasons:
        return DesignTemperatureAuthorityDecision(Q, tuple(reasons))
    return DesignTemperatureAuthorityDecision(QUALIFIED, ())


@dataclass(frozen=True)
class StockArchetypeInputs:
    schema_status: str
    wbl_joint_materialized_complete: bool
    building_type_link_status: str
    primary_energy_link_status: str
    building_type_model_admission_status: str = Q
    primary_energy_model_admission_status: str = Q
    building_type_direct_authority_status: str = Q
    primary_energy_direct_authority_status: str = Q


def assess_stock_archetype(inputs: StockArchetypeInputs) -> AdmissionDecision:
    """Assess whether a populated current-stock archetype is authoritative."""

    blockers: list[str] = []
    if inputs.schema_status != CONTRACTED:
        blockers.append("SCHEMA_NOT_CONTRACTED")
    if not inputs.wbl_joint_materialized_complete:
        blockers.append("NO_MATERIALIZED_COMPLETE_WBL_JOINT")

    if inputs.building_type_link_status not in BUILDING_TYPE_LINK_OK:
        blockers.append("NO_CURRENT_BUILDING_TYPE_LINK_AUTHORITY")
    elif (
        inputs.building_type_link_status in REAL_EVIDENCE
        and inputs.building_type_direct_authority_status != QUALIFIED
    ):
        blockers.append("BUILDING_TYPE_DIRECT_LINK_NOT_ADMITTED")
    elif (
        inputs.building_type_link_status == "APPROVED_CALIBRATED_MODEL"
        and inputs.building_type_model_admission_status != QUALIFIED
    ):
        blockers.append("CALIBRATED_BUILDING_TYPE_MODEL_NOT_ADMITTED")

    if inputs.primary_energy_link_status not in ENERGY_LINK_OK:
        blockers.append("NO_PRIMARY_ENERGY_TO_WBL_LINK_AUTHORITY")
    elif (
        inputs.primary_energy_link_status in REAL_EVIDENCE
        and inputs.primary_energy_direct_authority_status != QUALIFIED
    ):
        blockers.append("PRIMARY_ENERGY_DIRECT_LINK_NOT_ADMITTED")
    elif (
        inputs.primary_energy_link_status == "MODELLED_LINKED"
        and inputs.primary_energy_model_admission_status != QUALIFIED
    ):
        blockers.append("CALIBRATED_PRIMARY_ENERGY_MODEL_NOT_ADMITTED")

    if blockers:
        return AdmissionDecision(Q, tuple(blockers))
    return AdmissionDecision(QUALIFIED, ())


def assess_technical_readiness_enrichment(
    stock_inputs: StockArchetypeInputs,
    *,
    heat_emitter_status: str,
    design_temperature_status: str,
    heat_emitter_direct_authority_status: str = Q,
    design_temperature_direct_authority_status: str = Q,
) -> AdmissionDecision:
    """Require separately admitted current evidence for readiness enrichment."""

    stock = assess_stock_archetype(stock_inputs)
    blockers = list(stock.blockers)
    if heat_emitter_status not in REAL_EVIDENCE:
        blockers.append("NO_CURRENT_HEAT_EMITTER_EVIDENCE")
    elif heat_emitter_direct_authority_status != QUALIFIED:
        blockers.append("HEAT_EMITTER_DIRECT_EVIDENCE_NOT_ADMITTED")

    if design_temperature_status not in REAL_EVIDENCE:
        blockers.append("NO_CURRENT_DESIGN_TEMPERATURE_EVIDENCE")
    elif design_temperature_direct_authority_status != QUALIFIED:
        blockers.append("DESIGN_TEMPERATURE_DIRECT_EVIDENCE_NOT_ADMITTED")

    if blockers:
        return AdmissionDecision(Q, tuple(blockers))
    return AdmissionDecision(QUALIFIED, ())
