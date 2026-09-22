"""B02-P78 national post-retrofit design-load input coverage.

P77 established that the physical response method exists but the national input
surface does not. P78 decomposes the design-load surface into the exact inputs
required by the current B06 peak-load contract and distinguishes:

- population-key coverage already materialized at the 2022 KSH WBL full-joint;
- calibrated building-type linkage already admitted by P21;
- historical/archetype calibration that can constrain a model;
- post-retrofit physical-state inputs that remain Q.

P78 intentionally does not convert annual energy to peak kW, does not turn a
floor-area band into exact heated area, and does not promote a historical
synthetic average building into a current/post-retrofit national observation.

Critical boundaries:

NATIONAL POPULATION KEY COVERAGE != PHYSICAL STATE PARAMETERIZATION
WBL FLOOR-AREA BAND != HEATED FLOOR-AREA POINT
WALL-MATERIAL CATEGORY != COMPONENT U-VALUE
SYNTHETIC AVERAGE ARCHETYPE != CURRENT NATIONAL POST-RETROFIT STATE
ANNUAL ENERGY != DESIGN PEAK
"""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
WBL_MANIFEST = ROOT / "data" / "processed" / "b02" / "ksh_wbl_joint_manifest.json"

EXPECTED_FULL_JOINT_ROWS = 116_452
EXPECTED_OCCUPIED_DWELLINGS = 4_008_541

MATERIALIZED_OBS = "MATERIALIZED_OBS"
MATERIALIZED_OBS_SET_BOUNDED = "MATERIALIZED_OBS_SET_BOUNDED"
MATERIALIZED_ASS_CALIBRATED = "MATERIALIZED_ASS_CALIBRATED"
CALIBRATION_ONLY = "CALIBRATION_ONLY"
PARTIAL_ARCHETYPE_CALIBRATION = "PARTIAL_ARCHETYPE_CALIBRATION"
PARTIAL_CURRENT_STANDARD_ZONE_DOMAIN = "PARTIAL_CURRENT_STANDARD_ZONE_DOMAIN"
PARTIAL_CURRENT_METHOD_HVENT_SURFACE = "PARTIAL_CURRENT_METHOD_HVENT_SURFACE"
PARTIAL_ACTION_CONDITIONED_AIRTIGHTNESS_RESPONSE = "PARTIAL_ACTION_CONDITIONED_AIRTIGHTNESS_RESPONSE"
PARTIAL_HUNGARIAN_FACADE_OPENING_SPLIT_PROXY = "PARTIAL_HUNGARIAN_FACADE_OPENING_SPLIT_PROXY"
PARTIAL_HUNGARIAN_FACADE_AND_TOP_GEOMETRY_PROXY = "PARTIAL_HUNGARIAN_FACADE_AND_TOP_GEOMETRY_PROXY"
QUALIFIED_REFERENCE_PROGRAMME_TARGET_SURFACE = "QUALIFIED_REFERENCE_PROGRAMME_TARGET_SURFACE"
QUALIFIED_SIMPLIFIED_THERMAL_BRIDGE_CORRECTION_SURFACE = "QUALIFIED_SIMPLIFIED_THERMAL_BRIDGE_CORRECTION_SURFACE"
CURRENT_METHOD_SERVICE_REFERENCE = "CURRENT_METHOD_SERVICE_REFERENCE"
PUBLIC_23_TYPE_BASELINE_NUMERIC_AUTHORITY = "PUBLIC_23_TYPE_BASELINE_NUMERIC_AUTHORITY"
Q = "Q"


@dataclass(frozen=True)
class PopulationSurface:
    row_count: int
    occupied_dwellings: int
    grain: str
    source_id: str
    materialization_status: str


@dataclass(frozen=True)
class InputCoverage:
    input_id: str
    status: str
    evidence_status: str
    source_refs: tuple[str, ...]
    required_for_design_load: bool
    blocker: str | None
    note: str


@dataclass(frozen=True)
class DesignLoadMaterializationDecision:
    status: str
    blockers: tuple[str, ...]


def population_surface() -> PopulationSurface:
    manifest = json.loads(WBL_MANIFEST.read_text(encoding="utf-8"))
    projection = manifest["controls"]["projections"]["WBL011_FULL_STOCK_JOINT"]
    rows = int(projection["returned_records"])
    occupied = int(projection["returned_numeric_dwelling_sum"])
    if rows != EXPECTED_FULL_JOINT_ROWS:
        raise ValueError("unexpected WBL011 full-joint row count")
    if occupied != EXPECTED_OCCUPIED_DWELLINGS:
        raise ValueError("unexpected occupied-dwelling control")
    return PopulationSurface(
        row_count=rows,
        occupied_dwellings=occupied,
        grain=str(projection["grain"]),
        source_id=str(manifest["source_id"]),
        materialization_status=str(
            manifest["controls"]["wbl011_full_stock_joint_materialization_status"]
        ),
    )


def national_design_load_input_coverage() -> tuple[InputCoverage, ...]:
    """Return the evidence status of each national B06 design-load input layer."""

    _ = population_surface()
    return (
        InputCoverage(
            "GEOGRAPHY_SETTLEMENT",
            MATERIALIZED_OBS,
            "OBS",
            ("SRC-B02-KSH-CENSUS-API-2022",),
            False,
            None,
            "County and settlement type are present on the canonical WBL cell grain.",
        ),
        InputCoverage(
            "CONSTRUCTION_PERIOD",
            MATERIALIZED_OBS,
            "OBS",
            ("SRC-B02-KSH-CENSUS-API-2022",),
            False,
            None,
            "Construction-period code is directly present on the canonical WBL cell grain.",
        ),
        InputCoverage(
            "WALL_MATERIAL_CATEGORY",
            MATERIALIZED_OBS,
            "OBS",
            ("SRC-B02-KSH-CENSUS-API-2022",),
            False,
            None,
            "WBL wall-material category is observed; it does not determine a U-value.",
        ),
        InputCoverage(
            "DWELLING_FLOOR_AREA_BAND",
            MATERIALIZED_OBS_SET_BOUNDED,
            "OBS",
            ("SRC-B02-KSH-CENSUS-API-2022",),
            False,
            None,
            "Eight WBL floor-area bands are observed; the open >=120 m2 class forbids an arbitrary midpoint.",
        ),
        InputCoverage(
            "BUILDING_TYPE",
            MATERIALIZED_ASS_CALIBRATED,
            "ASS",
            ("B02-P21",),
            False,
            None,
            "P21 attaches FAMILY_HOUSE/MULTI_DWELLING probabilities to exact WBL cells with explicit uncertainty.",
        ),
        InputCoverage(
            "HEATED_FLOOR_AREA_OR_DIRECT_GEOMETRY",
            Q,
            "Q",
            (
                "SRC-B02-KSH-CENSUS-API-2022",
                "SRC-B02-HU-CSOKNYAI-HOUSING-STOCK-DISSERTATION-2022",
                "SRC-B02-BME-RBSM-2026",
            ),
            True,
            "HEATED_AREA_OR_DIRECT_GEOMETRY_SURFACE_REQUIRED",
            "Dwelling area is banded and is not the complete heated-envelope geometry required by B06.",
        ),
        InputCoverage(
            "POST_RETROFIT_ENVELOPE_GEOMETRY",
            PARTIAL_HUNGARIAN_FACADE_AND_TOP_GEOMETRY_PROXY,
            "DER/SCN_PROXY",
            (
                "SRC-B02-HU-CSOKNYAI-HOUSING-STOCK-DISSERTATION-2022",
                "SRC-B02-BME-RBSM-2026",
                "SRC-B02-HU-EPISCOPE-AVERAGE-BUILDING-METHOD",
                "SRC-B02-HU-EPISCOPE-BUDAORS-AVERAGE-2015",
                "SRC-B02-EU-TABULA-DATABASE-EVALUATION-2015",
                "B02-P85",
                "B02-P92",
                "B02-P93",
            ),
            True,
            "POST_RETROFIT_ENVELOPE_GEOMETRY_SURFACE_REQUIRED",
            "B02-P85 materializes gross synthetic geometry proxies, B02-P92 adds a Hungarian wall-versus-aggregate-opening split, and B02-P93 adds a Hungarian class-average top-envelope-area calibration across all 14 reference-programme strata. The facade magnitude remains conditional on BBOX_RECTANGULARIZATION_VALIDATION_REQUIRED and the bottom heat-loss plane remains unresolved. Therefore the overall post-retrofit envelope-geometry surface is still partial and fail-closed.",
        ),
        InputCoverage(
            "BASELINE_COMPONENT_U_VALUE_CALIBRATION",
            PUBLIC_23_TYPE_BASELINE_NUMERIC_AUTHORITY,
            "DER",
            (
                "SRC-B02-HU-CSOKNYAI-HOUSING-STOCK-DISSERTATION-2022",
                "SRC-B02-BME-RBSM-2026",
            ),
            False,
            None,
            "The 2022 dissertation publishes 23-type survey-derived baseline component U-value tables and the 2026 RBSM confirms the synthetic-average lineage. This is baseline/calibration authority, not an action-conditioned post-retrofit surface.",
        ),
        InputCoverage(
            "POST_RETROFIT_COMPONENT_U_VALUES",
            Q,
            "Q",
            (
                "SRC-B06-HU-ENERGY-RULES-2023",
                "SRC-B02-BME-RBSM-2026",
            ),
            True,
            "POST_RETROFIT_COMPONENT_U_VALUE_SURFACE_REQUIRED",
            "Current regulation can constrain retrofit outcomes, but the action-specific resulting U-values are not yet bound across the population surface.",
        ),
        InputCoverage(
            "POST_RETROFIT_VENTILATION",
            QUALIFIED_REFERENCE_PROGRAMME_TARGET_SURFACE,
            "POL/OBS/DER/SCN",
            (
                "SRC-B06-HU-ENERGY-RULES-2023",
                "SRC-B06-HU-ENERGY-METHOD-2023",
                "SRC-B02-BME-RBSM-2026",
                "SRC-B06-HU-EKR-18-2025",
                "SRC-B02-EU-ECODESIGN-VENTILATION-1253-2014",
                "SRC-B02-HU-PTE-AIRTIGHTNESS-2014",
                "SRC-B02-UK-RFTF-AIRTIGHTNESS-2013",
                "SRC-B02-US-WINDOW-AIRTIGHTNESS-2026",
                "SRC-B02-UK-AIRTIGHTNESS-DURABILITY-2025",
                "SRC-B06-HU-OFP-KEHOP-2026",
                "B02-P85",
                "B02-P87",
                "B02-P88",
                "B02-P89",
                "B02-P90",
            ),
            True,
            None,
            "B02-P90 explicitly adopts the current-method good-airtightness 0.03..0.06 1/h cases as a prospective reference-programme target surface. This closes the national reference-scenario ventilation input without claiming observed or guaranteed future performance. Realized/ex-post claims remain record-level gated by REALIZED_AIRTIGHTNESS_VERIFICATION_REQUIRED.",
        ),
        InputCoverage(
            "POST_RETROFIT_THERMAL_BRIDGE_H",
            QUALIFIED_SIMPLIFIED_THERMAL_BRIDGE_CORRECTION_SURFACE,
            "POL/DER/SCN",
            (
                "SRC-B06-HU-ENERGY-METHOD-2023",
                "SRC-B02-HU-CSOKNYAI-HOUSING-STOCK-DISSERTATION-2022",
                "SRC-B02-BME-RBSM-2026",
                "B02-P80",
                "B02-P85",
                "B02-P91",
            ),
            True,
            None,
            "B02-P91 uses the current Hungarian simplified thermal-bridge route U_R=U*(1+zeta) and expresses the equivalent separate B06 bridge term as A*U*zeta. This closes the independent reference-programme correction-factor input without inventing psi-length prevalence. Component area geometry and pitched-roof U remain separately tracked blockers; internal insulation and realized detailed project claims require the detailed route.",
        ),
        InputCoverage(
            "DESIGN_OUTDOOR_TEMPERATURE",
            PARTIAL_CURRENT_STANDARD_ZONE_DOMAIN,
            "DER",
            (
                "SRC-B02-MSZ-24140-2026",
                "SRC-B02-BIMLINE-MSZ24140-2026",
            ),
            True,
            "COMPLETE_LOCATION_TO_CURRENT_STANDARD_ZONE_MAPPING_REQUIRED",
            "B02-P86 materializes the current MSZ 24140:2026 zone domain (-12/-11/-10 C) and 20 public city anchors. Exact national settlement-to-zone geometry and out-of-baseline-scope local authority remain Q.",
        ),
        InputCoverage(
            "DESIGN_INDOOR_TEMPERATURE",
            CURRENT_METHOD_SERVICE_REFERENCE,
            "POL",
            ("SRC-B06-HU-ENERGY-METHOD-2023",),
            True,
            None,
            "The current residential calculation method supplies 20 C as an explicit service/reference condition. It is not an observed household setpoint and may be overridden by project authority.",
        ),
        InputCoverage(
            "ACTION_TO_POST_STATE_PHYSICS",
            Q,
            "Q",
            ("B06-P63",),
            True,
            "ACTION_TO_POST_STATE_PHYSICAL_MAPPING_REQUIRED",
            "P63 calculates from explicit before/after states but does not itself assign after-state geometry/U/ventilation/thermal-bridge values to every national cell.",
        ),
    )


def current_design_load_blockers() -> tuple[str, ...]:
    blockers: list[str] = []
    for item in national_design_load_input_coverage():
        if item.required_for_design_load and item.blocker and item.blocker not in blockers:
            blockers.append(item.blocker)
    return tuple(blockers)


def assess_national_post_retrofit_design_load_surface(
    supplied_inputs: set[str] | frozenset[str] = frozenset(),
) -> DesignLoadMaterializationDecision:
    """Fail closed until all current physical input blockers are satisfied."""

    residual = tuple(
        blocker for blocker in current_design_load_blockers()
        if blocker not in supplied_inputs
    )
    if residual:
        return DesignLoadMaterializationDecision(
            "PARTIAL_RESOLVED_INPUT_COVERAGE_DECOMPOSED",
            residual,
        )
    return DesignLoadMaterializationDecision(
        "QUALIFIED_FOR_B06_DESIGN_LOAD_MATERIALIZATION",
        (),
    )


def archetype_calibration_boundary() -> dict[str, object]:
    """Machine-readable non-promotion boundary for external archetype evidence."""

    return {
        "keop_survey_buildings": 2029,
        "synthetic_average_building_types": 23,
        "single_family_types": 12,
        "multi_family_types": 11,
        "type5_heated_floor_area_m2": 103.4,
        "allowed_use": "PUBLIC_23_TYPE_BASELINE_CALIBRATION_AND_CROSSWALK_INPUT",
        "forbidden_promotions": (
            "TYPE5_TO_ALL_HUNGARY",
            "2015_SYNTHETIC_AVERAGE_TO_2026_POST_RETROFIT_OBSERVATION",
            "ANNUAL_ENERGY_TO_DESIGN_PEAK",
        ),
    }
