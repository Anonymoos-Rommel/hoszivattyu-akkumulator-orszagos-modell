# B02-P83 — bounded national reference-retrofit physical-state surface

## Result

P83 materializes the first national-stratum B02 physical-state surface that is supported by the existing P79/P80 evidence without inventing missing inputs.

Materialized branch:

`REFERENCE_ENVELOPE_RETROFIT_PLUS_AWHP`

Canonical grain:

`7 WBL construction periods x 2 P21 building groups = 14 strata`

For every stratum, P83 carries:

- complete P79 KEOP23 candidate-type set;
- P79 heated-floor-area-per-dwelling min/max calibration envelope;
- explicit geometry-preservation model rule;
- P80 source-native reference-retrofit U upper bounds:
  - external wall: 0.24 W/m2K;
  - flat roof: 0.17 W/m2K;
  - attic floor: 0.17 W/m2K;
  - basement ceiling: 0.26 W/m2K;
  - window: 1.15 W/m2K.

The materialized data is:

`data/processed/b02/p83_bounded_reference_retrofit_surface.csv`

## P82 model-contract closure

P83 implements three P82 requirements:

- `EXPLICIT_ACTION_GEOMETRY_RULE_REQUIRED -> CONTRACTED`
- `EXPLICIT_ACTION_TO_POST_STATE_MODEL_REQUIRED -> CONTRACTED`
- `EXPLICIT_DESIGN_INDOOR_SERVICE_SCENARIO_REQUIRED -> CONTRACTED_EXPLICIT_INPUT`

The indoor design service condition has no hidden default. A caller must provide it explicitly.

## What P83 does not claim

`POPULATION SURFACE != HOUSEHOLD DESIGN INPUT`

`REFERENCE RETROFIT U-MAX != REALIZED HOUSEHOLD U`

`SET-VALUED GEOMETRY != HOUSEHOLD GEOMETRY`

P83 does not promote the historical KEOP23 calibration to current-2026 observed stock truth.

The HP-only branch still requires a defensible current baseline U inference.

## Remaining physical gaps

The reference-retrofit branch is still incomplete for B06 design-load materialization because the following remain unresolved:

- `DEFENSIBLE_COMPONENT_AREA_GEOMETRY_INFERENCE_REQUIRED`
- `PITCHED_ROOF_POSTSTATE_U_BOUND_REQUIRED`
- `DEFENSIBLE_POST_RETROFIT_VENTILATION_INFERENCE_REQUIRED`
- `DEFENSIBLE_THERMAL_BRIDGE_CORRECTION_INFERENCE_REQUIRED`
- `DEFENSIBLE_LOCATION_TO_DESIGN_OUTDOOR_TEMPERATURE_MODEL_REQUIRED`

Downstream programme response additionally still requires:

- `DEFENSIBLE_NATIONAL_SUPPLY_TEMPERATURE_INFERENCE_REQUIRED`
- `FRESH_MULTI_SOURCE_ENVELOPE_ACTION_EVIDENCE_REQUIRED`
- the already-known B05 operating-point gaps.

## State

Q-B02-004 remains OPEN, but is narrowed by actual materialization rather than another semantic-only repair.

B02 readiness remains 55%; no arbitrary readiness uplift is minted.
