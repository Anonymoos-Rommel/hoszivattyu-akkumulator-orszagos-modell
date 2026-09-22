"""B02-P83 bounded reference-retrofit physical-state surface.

P83 materializes the first national-stratum physical-state surface that is
actually supported by the existing P79/P80 evidence. It does not claim a
complete B06 design-load surface.

The materialized branch is:
REFERENCE_ENVELOPE_RETROFIT_PLUS_AWHP

For every WBL construction-period x P21 building-group state, P83 carries:
- the complete P79 candidate-type set;
- the P79 heated-floor-area calibration envelope;
- the P80 source-native reference-retrofit U upper bounds;
- explicit action geometry and action-to-post-state model contracts.

Still Q:
- component-area geometry;
- pitched-roof post-state U;
- ventilation;
- thermal bridges;
- location-to-design-outdoor-temperature;
- national P65 supply-temperature inference;
- national action-frequency evidence.

POPULATION SURFACE != HOUSEHOLD DESIGN INPUT
REFERENCE RETROFIT U-MAX != REALIZED HOUSEHOLD U
SET-VALUED GEOMETRY != HOUSEHOLD GEOMETRY
"""

from __future__ import annotations

from dataclasses import dataclass

from modules.B02.keop23_uvalue_poststate import (
    REFERENCE_ENVELOPE_RETROFIT_PLUS_AWHP,
    reference_retrofit_constraint,
)
from modules.B02.keop23_wbl_crosswalk import candidates_for


SUPPORTED_COMPONENTS = (
    "EXTERNAL_WALL",
    "FLAT_ROOF",
    "ATTIC_FLOOR",
    "BASEMENT_CEILING",
    "WINDOW",
)

GEOMETRY_RULE = "PRESERVE_P79_SYNTHETIC_GEOMETRY_SET"
POST_STATE_RULE = "REFERENCE_RETROFIT_U_UPPER_BOUNDS_ON_P79_GEOMETRY_SET"


@dataclass(frozen=True)
class BoundedPostState:
    wbl_period_code: str
    building_group: str
    action: str
    candidate_type_ids: tuple[int, ...]
    heated_floor_area_lower_m2_per_dwelling: float
    heated_floor_area_upper_m2_per_dwelling: float
    geometry_rule: str
    post_state_rule: str
    u_upper_bounds_w_m2k: tuple[tuple[str, float], ...]
    status: str
    residuals: tuple[str, ...]


@dataclass(frozen=True)
class DesignServiceScenario:
    design_indoor_temperature_c: float
    authority_class: str = "SCN_EXPLICIT_SERVICE_CONDITION"


def explicit_design_service_scenario(
    design_indoor_temperature_c: float,
) -> DesignServiceScenario:
    """Require an explicit finite service condition; no hidden national default."""
    value = float(design_indoor_temperature_c)
    if not (-50.0 < value < 60.0):
        raise ValueError("design indoor temperature outside defensible numeric domain")
    return DesignServiceScenario(value)


def bounded_reference_retrofit_state(
    wbl_period_code: str,
    building_group: str,
) -> BoundedPostState:
    rule = candidates_for(wbl_period_code, building_group)

    u_bounds: list[tuple[str, float]] = []
    for component in SUPPORTED_COMPONENTS:
        constraint = reference_retrofit_constraint(
            component,
            action=REFERENCE_ENVELOPE_RETROFIT_PLUS_AWHP,
        )
        if constraint.upper_u_w_m2k is None or constraint.blockers:
            raise ValueError(f"unexpected unresolved P80 component: {component}")
        u_bounds.append((component, float(constraint.upper_u_w_m2k)))

    residuals = (
        "DEFENSIBLE_COMPONENT_AREA_GEOMETRY_INFERENCE_REQUIRED",
        "PITCHED_ROOF_POSTSTATE_U_BOUND_REQUIRED",
        "DEFENSIBLE_POST_RETROFIT_VENTILATION_INFERENCE_REQUIRED",
        "DEFENSIBLE_THERMAL_BRIDGE_CORRECTION_INFERENCE_REQUIRED",
        "DEFENSIBLE_LOCATION_TO_DESIGN_OUTDOOR_TEMPERATURE_MODEL_REQUIRED",
        "DEFENSIBLE_NATIONAL_SUPPLY_TEMPERATURE_INFERENCE_REQUIRED",
        "FRESH_MULTI_SOURCE_ENVELOPE_ACTION_EVIDENCE_REQUIRED",
    )

    return BoundedPostState(
        wbl_period_code=wbl_period_code,
        building_group=building_group,
        action=REFERENCE_ENVELOPE_RETROFIT_PLUS_AWHP,
        candidate_type_ids=rule.candidate_type_ids,
        heated_floor_area_lower_m2_per_dwelling=(
            rule.heated_floor_area_per_dwelling_min_m2
        ),
        heated_floor_area_upper_m2_per_dwelling=(
            rule.heated_floor_area_per_dwelling_max_m2
        ),
        geometry_rule=GEOMETRY_RULE,
        post_state_rule=POST_STATE_RULE,
        u_upper_bounds_w_m2k=tuple(u_bounds),
        status="PARTIAL_MATERIALIZED_BOUNDED_POST_STATE",
        residuals=residuals,
    )


def action_model_contract_status() -> dict[str, str]:
    """P82 scenario/model-contract residuals implemented by P83."""
    return {
        "EXPLICIT_ACTION_GEOMETRY_RULE_REQUIRED": "CONTRACTED",
        "EXPLICIT_ACTION_TO_POST_STATE_MODEL_REQUIRED": "CONTRACTED",
        "EXPLICIT_DESIGN_INDOOR_SERVICE_SCENARIO_REQUIRED": "CONTRACTED_EXPLICIT_INPUT",
    }


def record_level_boundary() -> tuple[str, ...]:
    return (
        "P83_SURFACE_CANNOT_PASS_A_SPECIFIC_BUILDING",
        "P83_U_BOUNDS_ARE_NOT_REALIZED_HOUSEHOLD_U_VALUES",
        "SPECIFIC_BUILDING_DESIGN_LOAD_STILL_REQUIRES_COMPLETE_RECORD_INPUTS",
    )
