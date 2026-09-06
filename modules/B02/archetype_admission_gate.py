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

B02-P32 repairs the applicability semantics identified by P31. Hydronic current
systems continue to require separately admitted design/calculation temperature
evidence. A non-hydronic system may use NOT_APPLICABLE only when the
non-hydronic applicability claim itself is separately QUALIFIED. Unknown,
missing and not-applicable remain distinct states.

B02-P40 repairs one remaining admission asymmetry. Heat-emitter readiness may
now be supported either by the existing P18 direct OBS/DER authority path or by
a separately QUALIFIED calibrated-emitter authority. The calibrated path is
fail-closed: generic P12 model approval is necessary but not sufficient. The
model output must also cover the complete occupied-dwelling stock emitter
assignment at WBL-compatible grain with a reproducible repository binding.
A one-category marginal such as the approved P39 gas-convector linkage cannot
self-authorize the complete heat-emitter readiness claim.

B02-P41 adds a transition-path-specific thermal route. A current non-hydronic
emitter that is not reused by the programme does not need a fictional current
hydronic design-temperature pair. This is not a free bypass: the replacement
route must itself be separately QUALIFIED from an admitted current-emitter
category authority and explicit non-hydronic semantics. P41 initially admits
only the already-qualified P39 gas-convector category. It does not generalize
that treatment to other emitter classes and does not close the remaining
full-stock emitter or hydronic design-temperature blockers.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import isfinite


Q = "Q"
QUALIFIED = "QUALIFIED"
CONTRACTED = "CONTRACTED"
NOT_APPLICABLE = "NOT_APPLICABLE"
APPROVED_CALIBRATED_MODEL = "APPROVED_CALIBRATED_MODEL"
REUSE_EXISTING_DISTRIBUTION = "REUSE_EXISTING_DISTRIBUTION"
REPLACE_EXISTING_DISTRIBUTION = "REPLACE_EXISTING_DISTRIBUTION"
NON_HYDRONIC_ROOM_HEATING = "NON_HYDRONIC_ROOM_HEATING"
GAS_CONVECTOR = "GAS_CONVECTOR"

REAL_EVIDENCE = frozenset({"OBS", "DER"})
BUILDING_TYPE_LINK_OK = frozenset({"OBS", "DER", APPROVED_CALIBRATED_MODEL})
ENERGY_LINK_OK = frozenset({"OBS", "DER", "MODELLED_LINKED"})
HEAT_EMITTER_LINK_OK = frozenset({"OBS", "DER", APPROVED_CALIBRATED_MODEL})
DESIGN_TEMPERATURE_APPLICABILITY = frozenset({"APPLICABLE", NOT_APPLICABLE})
MODEL_OUTPUT_EVIDENCE = frozenset({"ASS", "MODELLED"})
THERMAL_TRANSITION_PATHS = frozenset(
    {REUSE_EXISTING_DISTRIBUTION, REPLACE_EXISTING_DISTRIBUTION}
)

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
class CalibratedHeatEmitterAuthorityCandidate:
    """Complete-stock authority wrapper around an already-admitted model.

    P12 calibrated-model admission proves model quality/governance. This P40
    wrapper proves that the admitted model output is sufficient for the
    *complete current heat-emitter assignment* consumed by technical readiness.
    A model of one emitter category or one stock subset is therefore not enough.
    """

    model_id: str
    model_admission_status: str
    output_evidence_status: str
    source_universe: str
    source_grain: str
    current_state_explicit: bool
    publishes_complete_assignment: bool
    wbl_compatible_join_key: bool
    reproducible_repository_binding: bool


@dataclass(frozen=True)
class CalibratedHeatEmitterAuthorityDecision:
    status: str
    reasons: tuple[str, ...]


def assess_calibrated_heat_emitter_authority(
    candidate: CalibratedHeatEmitterAuthorityCandidate,
) -> CalibratedHeatEmitterAuthorityDecision:
    """Admit a calibrated emitter assignment only when it covers the full stock."""

    reasons: list[str] = []
    if not candidate.model_id.strip():
        reasons.append("NO_MODEL_ID")
    if candidate.model_admission_status != QUALIFIED:
        reasons.append("CALIBRATED_HEAT_EMITTER_MODEL_NOT_ADMITTED")
    if candidate.output_evidence_status not in MODEL_OUTPUT_EVIDENCE:
        reasons.append("CALIBRATED_HEAT_EMITTER_OUTPUT_EVIDENCE_INVALID")
    if candidate.source_universe != REQUIRED_STOCK_UNIVERSE:
        reasons.append("NOT_OCCUPIED_DWELLING_STOCK")
    if candidate.source_grain not in DIRECT_WBL_GRAINS:
        reasons.append("GRAIN_NOT_DIRECT_WBL_LINK")
    if not candidate.current_state_explicit:
        reasons.append("CURRENT_EMITTER_STATE_NOT_EXPLICIT")
    if not candidate.publishes_complete_assignment:
        reasons.append("NO_COMPLETE_HEAT_EMITTER_ASSIGNMENT")
    if not candidate.wbl_compatible_join_key:
        reasons.append("NO_WBL_COMPATIBLE_JOIN_KEY")
    if not candidate.reproducible_repository_binding:
        reasons.append("NO_REPRODUCIBLE_REPOSITORY_BINDING")

    if reasons:
        return CalibratedHeatEmitterAuthorityDecision(Q, tuple(reasons))
    return CalibratedHeatEmitterAuthorityDecision(QUALIFIED, ())


@dataclass(frozen=True)
class ThermalTransitionPathCandidate:
    """Category-scoped current-to-programme thermal transition authority.

    P41 intentionally starts with one proven class only: GAS_CONVECTOR. The
    category may use this route only after its current-stock calibrated linkage
    is already QUALIFIED. The route says that the current non-hydronic thermal
    distribution is not reused and therefore has no current hydronic design
    temperature to prove. It does not prove the design or readiness of the new
    replacement system.
    """

    current_emitter_type: str
    emitter_category_authority_status: str
    current_state_explicit: bool
    current_distribution_topology: str
    design_temperature_applicability: str
    transition_path: str
    replacement_required: bool


@dataclass(frozen=True)
class ThermalTransitionPathDecision:
    status: str
    reasons: tuple[str, ...]


def assess_thermal_transition_path(
    candidate: ThermalTransitionPathCandidate,
) -> ThermalTransitionPathDecision:
    """Admit the P41 gas-convector replacement path without inventing hydronic data."""

    reasons: list[str] = []
    if candidate.current_emitter_type != GAS_CONVECTOR:
        reasons.append("P41_EMITTER_CLASS_NOT_ADMITTED")
    if candidate.emitter_category_authority_status != QUALIFIED:
        reasons.append("CURRENT_EMITTER_CATEGORY_NOT_ADMITTED")
    if not candidate.current_state_explicit:
        reasons.append("CURRENT_EMITTER_STATE_NOT_EXPLICIT")
    if candidate.current_distribution_topology != NON_HYDRONIC_ROOM_HEATING:
        reasons.append("CURRENT_DISTRIBUTION_NOT_NON_HYDRONIC_ROOM_HEATING")
    if candidate.design_temperature_applicability != NOT_APPLICABLE:
        reasons.append("CURRENT_HYDRONIC_TEMPERATURE_NOT_NOT_APPLICABLE")
    if candidate.transition_path != REPLACE_EXISTING_DISTRIBUTION:
        reasons.append("GAS_CONVECTOR_MUST_USE_REPLACEMENT_PATH")
    if not candidate.replacement_required:
        reasons.append("REPLACEMENT_REQUIREMENT_NOT_EXPLICIT")

    if reasons:
        return ThermalTransitionPathDecision(Q, tuple(reasons))
    return ThermalTransitionPathDecision(QUALIFIED, ())


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
        inputs.building_type_link_status == APPROVED_CALIBRATED_MODEL
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
    heat_emitter_calibrated_authority_status: str = Q,
    design_temperature_direct_authority_status: str = Q,
    design_temperature_applicability: str = "APPLICABLE",
    design_temperature_applicability_authority_status: str = Q,
    thermal_transition_path: str = REUSE_EXISTING_DISTRIBUTION,
    thermal_transition_path_authority_status: str = Q,
) -> AdmissionDecision:
    """Assess thermal readiness according to the actual transition path.

    The default REUSE_EXISTING_DISTRIBUTION route preserves P18/P32/P40 exactly:
    current emitter authority and, where hydronic, current design-temperature
    authority are required.

    P41 adds REPLACE_EXISTING_DISTRIBUTION for an already-admitted current
    non-hydronic category. That route does not require a fictional current
    hydronic temperature pair, but only when a separate transition-path
    authority is QUALIFIED. The path authority itself is produced by
    assess_thermal_transition_path(); a route token cannot self-authorize.
    """

    stock = assess_stock_archetype(stock_inputs)
    blockers = list(stock.blockers)

    if thermal_transition_path not in THERMAL_TRANSITION_PATHS:
        blockers.append("THERMAL_TRANSITION_PATH_UNKNOWN")
    elif thermal_transition_path == REPLACE_EXISTING_DISTRIBUTION:
        if thermal_transition_path_authority_status != QUALIFIED:
            blockers.append("THERMAL_REPLACEMENT_PATH_NOT_ADMITTED")
    else:
        if heat_emitter_status not in HEAT_EMITTER_LINK_OK:
            blockers.append("NO_CURRENT_HEAT_EMITTER_EVIDENCE")
        elif heat_emitter_status in REAL_EVIDENCE:
            if heat_emitter_direct_authority_status != QUALIFIED:
                blockers.append("HEAT_EMITTER_DIRECT_EVIDENCE_NOT_ADMITTED")
        elif heat_emitter_calibrated_authority_status != QUALIFIED:
            blockers.append("CALIBRATED_HEAT_EMITTER_MODEL_NOT_ADMITTED")

        if design_temperature_applicability not in DESIGN_TEMPERATURE_APPLICABILITY:
            blockers.append("DESIGN_TEMPERATURE_APPLICABILITY_UNKNOWN")
        elif design_temperature_applicability == NOT_APPLICABLE:
            if design_temperature_applicability_authority_status != QUALIFIED:
                blockers.append("DESIGN_TEMPERATURE_APPLICABILITY_NOT_ADMITTED")
            elif design_temperature_status != NOT_APPLICABLE:
                blockers.append("NON_HYDRONIC_TEMPERATURE_STATUS_NOT_NOT_APPLICABLE")
        else:
            if design_temperature_status not in REAL_EVIDENCE:
                blockers.append("NO_CURRENT_DESIGN_TEMPERATURE_EVIDENCE")
            elif design_temperature_direct_authority_status != QUALIFIED:
                blockers.append("DESIGN_TEMPERATURE_DIRECT_EVIDENCE_NOT_ADMITTED")

    if blockers:
        return AdmissionDecision(Q, tuple(blockers))
    return AdmissionDecision(QUALIFIED, ())
