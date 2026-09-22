# B02-P82 — national physical-input evidence-plane repair

**Canonical base:** `f4062b6d54bec3286c838fea657e0b0cec23620e`

## Purpose

P82 applies the project-wide population inference policy to the remaining B02 national physical-state blockers.

Canonical rules:

`NO FULL-POPULATION DATA != BLOCKER`

`NO DEFENSIBLE POPULATION INFERENCE == BLOCKER`

`POPULATION ESTIMATE != RECORD PASS/FAIL`

P82 does not create missing evidence. It repairs the grain of the requirements.

## Population-plane repairs

The following legacy blockers no longer mean that every Hungarian dwelling needs an exact technical record:

- `WITHIN_TYPE_GEOMETRY_DISTRIBUTION_REQUIRED`
  -> `DEFENSIBLE_WITHIN_ARCHETYPE_GEOMETRY_INFERENCE_REQUIRED`
- `COMPONENT_AREA_GEOMETRY_SURFACE_REQUIRED`
  -> `DEFENSIBLE_COMPONENT_AREA_GEOMETRY_INFERENCE_REQUIRED`
- `CURRENT_NO_ACTION_BASELINE_U_SURFACE_REQUIRED`
  -> `DEFENSIBLE_CURRENT_BASELINE_U_INFERENCE_REQUIRED`
- `POST_RETROFIT_VENTILATION_SURFACE_REQUIRED`
  -> `DEFENSIBLE_POST_RETROFIT_VENTILATION_INFERENCE_REQUIRED`
- `POST_RETROFIT_THERMAL_BRIDGE_SURFACE_REQUIRED`
  -> `DEFENSIBLE_THERMAL_BRIDGE_CORRECTION_INFERENCE_REQUIRED`
- `NATIONAL_P65_SUPPLY_TEMPERATURE_SURFACE_REQUIRED`
  -> `DEFENSIBLE_NATIONAL_SUPPLY_TEMPERATURE_INFERENCE_REQUIRED`

Admissible national evidence remains limited to the canonical population classes: exhaustive administrative/census evidence, representative observed samples, or calibrated multi-source inference with provenance, explicit target population, period/grain, reproducibility and uncertainty.

A calibrated multi-source inference requires multiple independent source families and population-control calibration. Three independent sources remain preferred where available, but fewer than three do not automatically make defensible inference impossible.

## Scenario/model-contract repairs

These are not empirical population-prevalence questions:

- `GEOMETRY_INVARIANCE_BY_ACTION_REQUIRED`
  -> `EXPLICIT_ACTION_GEOMETRY_RULE_REQUIRED`
- `DESIGN_INDOOR_SERVICE_CONDITION_REQUIRED`
  -> `EXPLICIT_DESIGN_INDOOR_SERVICE_SCENARIO_REQUIRED`
- `ACTION_TO_POST_STATE_PHYSICAL_MAPPING_REQUIRED`
  -> `EXPLICIT_ACTION_TO_POST_STATE_MODEL_REQUIRED`

They still must be explicit before a calculation that depends on them runs. The repair only removes the false requirement to discover a national observed prevalence for a model/service choice.

## Source/method requirements

Two requirements remain evidence/method gaps, but are generalized away from a single exact source artifact:

- `TABLE_9_1_HAS_NO_EXPLICIT_PITCHED_ROOF_ROW`
  -> `PITCHED_ROOF_POSTSTATE_U_BOUND_REQUIRED`
- `DESIGN_OUTDOOR_TEMPERATURE_MAPPING_REQUIRED`
  -> `DEFENSIBLE_LOCATION_TO_DESIGN_OUTDOOR_TEMPERATURE_MODEL_REQUIRED`

The first may be satisfied by another authoritative engineering source or admitted bounded method. The second needs a reproducible climate/location methodology; it is not a household microdata requirement.

## P81 continuity

`FRESH_MULTI_SOURCE_ENVELOPE_ACTION_EVIDENCE_REQUIRED` remains unchanged. P81 already repaired the exact national action-assignment error.

## Record-level boundary

P82 explicitly does not weaken:

- specific-building design-load inputs;
- specific-building P65 supply-temperature evidence;
- record/project transition PASS/FAIL;
- legal, tariff or network-node gates.

`NATIONAL PHYSICAL INPUT != HOUSEHOLD POINT PHYSICAL INPUT`

A national inference cannot pass a specific dwelling.

## Blocker effect

P82 changes the *form* of the remaining B02 physical blockers, not their evidence state.

No new U-value, geometry, ventilation, thermal-bridge, design-temperature or supply-temperature number is minted.

Q-B02-004 remains OPEN.
B02 readiness remains 55%.

B05 product-domain, CAPEX and remaining emitter/room-action residuals are deliberately untouched in this slice.
