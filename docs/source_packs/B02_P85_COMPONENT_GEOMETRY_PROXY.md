# B02-P85 — bounded component-geometry proxy surface

**State:** `NUMERIC SYNTHETIC GEOMETRY PROXY MATERIALIZED / COMPONENT-AREA BLOCKER NARROWED / Q-B02-004 OPEN_NARROWED`

## 1. Purpose

P83 materialized the first 14-stratum reference-retrofit physical-state surface, but B06 design-load execution still lacked component geometry.

P85 exhausts the already-canonical KEOP23 Table 14.7 geometry before searching for new data.

It uses only:

- `data/processed/b02/keop23_synthetic_geometry.csv`;
- `registry/b02_p79_wbl_keop23_crosswalk.csv`;
- the P83 bounded reference-retrofit surface.

No household geometry is invented.

## 2. Canonical boundaries

`KEOP23 SYNTHETIC GEOMETRY != HOUSEHOLD GEOMETRY`

`BOUNDING RECTANGLE FACADE PROXY != NET EXTERNAL WALL AREA`

`BOUNDING PLAN AREA != ROOF OR GROUND CONTACT AREA`

`MAX USABLE ROOF AREA != TOTAL ROOF HEAT-LOSS AREA`

`CANDIDATE-TYPE MIN/MAX != WITHIN-TYPE CONFIDENCE INTERVAL`

## 3. 23-type derived geometry proxy

P85 materializes:

`data/processed/b02/p85_keop23_component_geometry_proxy.csv`

For each of the 23 canonical KEOP23 synthetic types:

### 3.1 Heated volume per dwelling

Derived as:

`heated_floor_area * ceiling_height / model_dwelling_count`

Synthetic-type global descriptive range:

**145.323055556 .. 631.26 m3/dwelling**

Allowed use:

- ventilation-geometry calibration;
- bounded archetype sensitivity.

Forbidden:

- household volume bound;
- current population observation.

### 3.2 Mean storey floorplate per dwelling

Derived as:

`total_floor_area / storeys / model_dwelling_count`

Synthetic-type global descriptive range:

**9.916611842 .. 187.1 m2/dwelling**

This is a mean storey plate.

It is not automatically:

- top heat-loss area;
- ground-contact area;
- roof area.

### 3.3 Bounding plan area

Derived as:

`bbox_x * bbox_y / model_dwelling_count`

Synthetic-type descriptive range:

**9.926315789 .. 220.15 m2/dwelling**

This is an explicit rectangularization proxy only.

### 3.4 Bounding rectangular facade proxy

Derived as:

`2 * (bbox_x + bbox_y) * ceiling_height * storeys / model_dwelling_count`

Synthetic-type descriptive range:

**34.812631579 .. 328.32 m2/dwelling**

This is not source-native net external wall area.

It is especially not allowed to infer a window/wall split.

### 3.5 Maximum usable roof area per dwelling

Source field divided by model dwelling count.

Synthetic-type descriptive range:

**0.545454545 .. 18 m2/dwelling**

Usable roof area is not the total thermally exposed roof area.

## 4. 14-stratum set-valued envelope

P85 materializes:

`data/processed/b02/p85_component_geometry_stratum_envelope.csv`

Grain:

`7 WBL construction periods x 2 P21 building groups = 14 strata`

For every stratum the complete P79 candidate set is retained.

Each numeric interval is:

`min(candidate synthetic-type proxy) .. max(candidate synthetic-type proxy)`

It is therefore a set-valued synthetic calibration envelope.

It is not:

- a within-type statistical confidence interval;
- a household min/max;
- a national probability interval.

## 5. Combined current reference-retrofit input surface

P85 also materializes:

`data/processed/b02/p85_reference_retrofit_physical_input_surface.csv`

This joins, on the exact same 14-stratum candidate sets:

- P83 heated-floor-area set;
- P85 heated-volume proxy;
- P85 mean floorplate proxy;
- P85 bounding plan proxy;
- P85 rectangularized facade proxy;
- P85 usable-roof-area proxy;
- P80/P83 reference-retrofit U upper bounds:
  - external wall <= 0.24 W/m2K;
  - flat roof <= 0.17;
  - attic floor <= 0.17;
  - basement ceiling <= 0.26;
  - timber/PVC window <= 1.15.

Status:

`PARTIAL_REFERENCE_RETROFIT_PHYSICAL_INPUT_SURFACE`

## 6. Blocker effect

The old broad requirement:

`DEFENSIBLE_COMPONENT_AREA_GEOMETRY_INFERENCE_REQUIRED`

becomes:

`PARTIAL_RESOLVED_SYNTHETIC_PROXY`

The source-acquisition question is now materially narrower.

Remaining exact geometry residuals:

1. `NET_EXTERNAL_WALL_AND_WINDOW_AREA_SPLIT_INFERENCE_REQUIRED`
2. `ACTUAL_TOP_HEAT_LOSS_PLANE_AREA_INFERENCE_REQUIRED`
3. `ACTUAL_BOTTOM_HEAT_LOSS_PLANE_AREA_INFERENCE_REQUIRED`
4. `BBOX_RECTANGULARIZATION_VALIDATION_REQUIRED`

And the already-known independent physical residuals remain:

- `PITCHED_ROOF_POSTSTATE_U_BOUND_REQUIRED`;
- `DEFENSIBLE_POST_RETROFIT_VENTILATION_INFERENCE_REQUIRED`;
- `DEFENSIBLE_THERMAL_BRIDGE_CORRECTION_INFERENCE_REQUIRED`;
- `DEFENSIBLE_LOCATION_TO_DESIGN_OUTDOOR_TEMPERATURE_MODEL_REQUIRED`;
- `DEFENSIBLE_NATIONAL_SUPPLY_TEMPERATURE_INFERENCE_REQUIRED`;
- `FRESH_MULTI_SOURCE_ENVELOPE_ACTION_EVIDENCE_REQUIRED`.

## 7. Why P85 does not feed B06 design load as a finished input

B06 transmission heat loss requires actual thermal component areas.

A rectangularized gross facade proxy cannot be silently decomposed into:

- net wall area;
- window area.

Likewise:

- mean storey floorplate cannot silently become roof or ground-contact area;
- usable roof area cannot silently become thermal roof area.

P85 therefore improves the physical surface without bypassing the remaining geometry evidence problem.

## 8. Record-level boundary

P85 cannot pass a specific building.

Specific-building design-load calculation still requires record/project geometry evidence.

Population inference and record qualification remain separate.

## 9. Q-B02-004

Q-B02-004 remains:

`OPEN_NARROWED`

P85 adds real numeric physical-state materialization, but does not mint:

- national point design load;
- national point supply temperature;
- national COP;
- household pass/fail;
- national retrofit action frequency.

## 10. Readiness

B02 overall readiness remains **55%**.

Reason:

P85 materially narrows one geometry blocker, but the complete national design-load and P65/B05 response chain is still not executable over the full population surface.

No arbitrary readiness uplift is applied.
