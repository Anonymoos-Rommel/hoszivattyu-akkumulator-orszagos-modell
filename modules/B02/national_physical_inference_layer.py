"""B02-P82 national physical-input evidence-plane repair.

NO FULL-POPULATION DATA != BLOCKER
NO DEFENSIBLE POPULATION INFERENCE == BLOCKER
POPULATION ESTIMATE != RECORD PASS/FAIL
NATIONAL PHYSICAL INPUT != HOUSEHOLD POINT PHYSICAL INPUT
SCENARIO SERVICE CONDITION != POPULATION PREVALENCE EVIDENCE
"""

from __future__ import annotations
from dataclasses import dataclass

POPULATION_INFERENCE = "POPULATION_INFERENCE"
SCENARIO_MODEL_CONTRACT = "SCENARIO_MODEL_CONTRACT"
SOURCE_METHOD_EVIDENCE = "SOURCE_METHOD_EVIDENCE"

EXHAUSTIVE_ADMIN_CENSUS = "EXHAUSTIVE_ADMIN_CENSUS"
REPRESENTATIVE_OBSERVED_SAMPLE = "REPRESENTATIVE_OBSERVED_SAMPLE"
CALIBRATED_MULTI_SOURCE_INFERENCE = "CALIBRATED_MULTI_SOURCE_INFERENCE"
ADMISSIBLE_POPULATION_CLASSES = {
    EXHAUSTIVE_ADMIN_CENSUS,
    REPRESENTATIVE_OBSERVED_SAMPLE,
    CALIBRATED_MULTI_SOURCE_INFERENCE,
}


@dataclass(frozen=True)
class BlockerRepair:
    legacy_blocker: str
    current_requirement: str
    plane: str
    record_level_exactness_preserved: bool = True


@dataclass(frozen=True)
class PopulationPhysicalEvidence:
    evidence_class: str
    target_population_explicit: bool
    grain_and_period_explicit: bool
    provenance_explicit: bool
    uncertainty_explicit: bool
    reproducible: bool
    calibrated_to_population_controls: bool = False
    independent_source_count: int = 1


@dataclass(frozen=True)
class PopulationPhysicalAdmission:
    status: str
    blockers: tuple[str, ...]
    warnings: tuple[str, ...]


_REPAIRS = (
    BlockerRepair("WITHIN_TYPE_GEOMETRY_DISTRIBUTION_REQUIRED",
                  "DEFENSIBLE_WITHIN_ARCHETYPE_GEOMETRY_INFERENCE_REQUIRED",
                  POPULATION_INFERENCE),
    BlockerRepair("COMPONENT_AREA_GEOMETRY_SURFACE_REQUIRED",
                  "DEFENSIBLE_COMPONENT_AREA_GEOMETRY_INFERENCE_REQUIRED",
                  POPULATION_INFERENCE),
    BlockerRepair("GEOMETRY_INVARIANCE_BY_ACTION_REQUIRED",
                  "EXPLICIT_ACTION_GEOMETRY_RULE_REQUIRED",
                  SCENARIO_MODEL_CONTRACT),
    BlockerRepair("CURRENT_NO_ACTION_BASELINE_U_SURFACE_REQUIRED",
                  "DEFENSIBLE_CURRENT_BASELINE_U_INFERENCE_REQUIRED",
                  POPULATION_INFERENCE),
    BlockerRepair("TABLE_9_1_HAS_NO_EXPLICIT_PITCHED_ROOF_ROW",
                  "PITCHED_ROOF_POSTSTATE_U_BOUND_REQUIRED",
                  SOURCE_METHOD_EVIDENCE),
    BlockerRepair("POST_RETROFIT_VENTILATION_SURFACE_REQUIRED",
                  "DEFENSIBLE_POST_RETROFIT_VENTILATION_INFERENCE_REQUIRED",
                  POPULATION_INFERENCE),
    BlockerRepair("POST_RETROFIT_THERMAL_BRIDGE_SURFACE_REQUIRED",
                  "DEFENSIBLE_THERMAL_BRIDGE_CORRECTION_INFERENCE_REQUIRED",
                  POPULATION_INFERENCE),
    BlockerRepair("DESIGN_OUTDOOR_TEMPERATURE_MAPPING_REQUIRED",
                  "DEFENSIBLE_LOCATION_TO_DESIGN_OUTDOOR_TEMPERATURE_MODEL_REQUIRED",
                  SOURCE_METHOD_EVIDENCE),
    BlockerRepair("DESIGN_INDOOR_SERVICE_CONDITION_REQUIRED",
                  "EXPLICIT_DESIGN_INDOOR_SERVICE_SCENARIO_REQUIRED",
                  SCENARIO_MODEL_CONTRACT),
    BlockerRepair("ACTION_TO_POST_STATE_PHYSICAL_MAPPING_REQUIRED",
                  "EXPLICIT_ACTION_TO_POST_STATE_MODEL_REQUIRED",
                  SCENARIO_MODEL_CONTRACT),
    BlockerRepair("NATIONAL_P65_SUPPLY_TEMPERATURE_SURFACE_REQUIRED",
                  "DEFENSIBLE_NATIONAL_SUPPLY_TEMPERATURE_INFERENCE_REQUIRED",
                  POPULATION_INFERENCE),
)


def blocker_repairs() -> tuple[BlockerRepair, ...]:
    return _REPAIRS


def repaired_requirement(legacy_blocker: str) -> BlockerRepair:
    rows = [x for x in _REPAIRS if x.legacy_blocker == legacy_blocker]
    if len(rows) != 1:
        raise KeyError(f"legacy blocker not uniquely mapped: {legacy_blocker}")
    return rows[0]


def current_requirements(plane: str) -> tuple[str, ...]:
    return tuple(x.current_requirement for x in _REPAIRS if x.plane == plane)


def assess_population_physical_evidence(
    evidence: PopulationPhysicalEvidence,
    *,
    preferred_independent_sources: int = 3,
) -> PopulationPhysicalAdmission:
    """National/regional inference gate; never authorizes a specific building."""
    blockers: list[str] = []
    warnings: list[str] = []

    if evidence.evidence_class not in ADMISSIBLE_POPULATION_CLASSES:
        blockers.append("ADMISSIBLE_POPULATION_EVIDENCE_CLASS_REQUIRED")
    if not evidence.target_population_explicit:
        blockers.append("TARGET_POPULATION_REQUIRED")
    if not evidence.grain_and_period_explicit:
        blockers.append("GRAIN_AND_REFERENCE_PERIOD_REQUIRED")
    if not evidence.provenance_explicit:
        blockers.append("PROVENANCE_REQUIRED")
    if not evidence.uncertainty_explicit:
        blockers.append("UNCERTAINTY_REQUIRED")
    if not evidence.reproducible:
        blockers.append("REPRODUCIBLE_INFERENCE_REQUIRED")

    if evidence.evidence_class == CALIBRATED_MULTI_SOURCE_INFERENCE:
        if evidence.independent_source_count < 2:
            blockers.append("MULTI_SOURCE_INFERENCE_REQUIRES_MULTIPLE_INDEPENDENT_SOURCES")
        if not evidence.calibrated_to_population_controls:
            blockers.append("POPULATION_CONTROL_CALIBRATION_REQUIRED")
        if 2 <= evidence.independent_source_count < preferred_independent_sources:
            warnings.append("FEWER_THAN_PREFERRED_INDEPENDENT_SOURCES")

    if blockers:
        return PopulationPhysicalAdmission("Q", tuple(dict.fromkeys(blockers)),
                                           tuple(dict.fromkeys(warnings)))
    return PopulationPhysicalAdmission(
        "QUALIFIED_FOR_NATIONAL_BOUNDED_PHYSICAL_INFERENCE",
        (),
        tuple(dict.fromkeys(warnings)),
    )


def record_level_boundary() -> tuple[str, ...]:
    return (
        "SPECIFIC_BUILDING_DESIGN_LOAD_REQUIRES_RECORD_LEVEL_INPUTS",
        "SPECIFIC_BUILDING_P65_SUPPLY_TEMPERATURE_REQUIRES_RECORD_LEVEL_EVIDENCE",
        "POPULATION_INFERENCE_CANNOT_PASS_A_SPECIFIC_BUILDING",
    )
