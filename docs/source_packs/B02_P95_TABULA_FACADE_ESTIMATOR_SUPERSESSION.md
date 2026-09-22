# B02-P95 — TABULA FACADE ESTIMATOR SUPERSESSION OF P85 BBOX ROUTE

## Goal

Resolve the remaining facade-geometry dependency:

`BBOX_RECTANGULARIZATION_VALIDATION_REQUIRED`

without falsely declaring the P85 rectangularized facade proxy validated.

Base:

`336fbbdc5ae44b7197666c2e3e9215efca54e296`

## Independent validation authority

`SRC-B02-EU-TABULA-DATABASE-EVALUATION-2015`

The official TABULA/EPISCOPE evaluation defines a simplified thermal-envelope
estimation procedure for plausibility control and rough assessment of large
housing portfolios.

For facade area:

`A_facade = b + 0.7 * A_C_Ref`

with:

- 0 attached neighbours: `b = 50 m2`
- 1 attached neighbour: `b = 25 m2`
- 2 attached neighbours: `b = 5 m2`

The source defines facade as the total surface of:

- walls;
- windows;
- doors.

The procedure was tested against the extended TABULA database.

For **total envelope area** the report states:

- 40% of building datasets lie within +/-0.1 of the estimate;
- 80% lie within +/-0.3;
- no relevant systematic deviation was found;
- the procedure is considered appropriate for plausibility controls and
  estimating envelope area for larger stock subsets.

P95 preserves the source scope.

It does **not** turn the total-envelope +/-0.3 statement into a facade-specific
error bound.

## Reference-area semantics

`SRC-B02-EU-TABULA-REFERENCE-AREA-WEB`

TABULA defines `A_C_Ref` as conditioned reference floor area based on internal
dimensions.

The KEOP23 synthetic geometry provides:

- heated floor area;
- total floor area.

Exact semantic identity between the KEOP field and TABULA `A_C_Ref` is not
proven.

P95 therefore refuses:

`A_C_Ref = heated_floor_area`

as an exact identity.

For the reference-programme estimator it preserves:

`A_C_Ref_proxy in [A_heated, A_total]`

This interval is a modelling proxy:

- lower: explicitly heated floor area;
- upper: total floor area, which may include unheated parts.

The upper value is conservative and is not promoted to observed conditioned
area.

## Attached-neighbour uncertainty

The KEOP23 type surface contains no attached-neighbour field.

Several FAMILY_HOUSE source notes also use family/row-house wording.

Therefore P95 does not assume:

`FAMILY_HOUSE = DETACHED`

The admitted TABULA neighbour set is:

`N_attached in {0, 1, 2}`

No prevalence or midpoint is invented.

## P85 bbox validation result

P85 facade proxy:

`A_bbox = 2 * (bbox_x + bbox_y) * ceiling_height * storeys / dwellings`

This remains reproducible synthetic arithmetic.

P95 evaluates it independently against TABULA.

### Narrow audit

Use KEOP heated floor area as the closest single `A_C_Ref` proxy and preserve
all 0/1/2 neighbour classes.

Result:

**2 / 23 types overlap**

the TABULA facade-estimator interval.

### Widened area-semantic audit

Preserve:

`A_C_Ref_proxy in [heated_floor_area, total_floor_area]`

and all neighbour classes.

Result:

**11 / 23 types overlap**

the widened TABULA estimator interval.

This is still insufficient to certify the bbox facade proxy as the canonical
reference-programme facade geometry.

## Decision

P95 does **not** mark:

`BBOX_RECTANGULARIZATION_VALIDATION_REQUIRED = PASS`

Instead:

`BBOX_RECTANGULARIZATION_VALIDATION_REQUIRED`

becomes:

`SUPERSEDED_BY_TABULA_FACADE_ESTIMATOR`

The historical P85 bbox values remain in the repository for:

- provenance;
- diagnostics;
- regression history;
- model comparison.

They are removed from the canonical prospective reference-programme facade
path.

## Canonical P95 facade estimator

For each KEOP23 candidate type:

Lower bound:

`A_facade,lo = [5 + 0.7 * A_heated] / dwellings`

Upper bound:

`A_facade,hi = [50 + 0.7 * A_total] / dwellings`

This combines:

- attached-neighbour uncertainty;
- reference-area semantic uncertainty.

For each WBL-period x P21-building-group stratum P95 takes the min/max over the
full P79 candidate-type set.

No type weights are invented.

## P92 opening split handoff

P92 already established Hungarian class-average aggregate-opening shares:

- FAMILY_HOUSE: HU SFH = 11.111111%
- MULTI_DWELLING: HU MFH/AB set = 12.679739% .. 23.071979%

P95 applies those unchanged shares to the new TABULA facade interval.

The source-native P92 boundary remains:

`OPENING_AREA != WINDOW_ONLY_AREA`

because the TABULA opening aggregate includes a door component.

## 14-stratum canonical facade result

All 14 reference-programme strata now have bbox-independent facade geometry.

Global descriptive proxy extrema:

- gross facade:
  **38.526111111111 .. 238.58 m2/dwelling**
- aggregate openings:
  **4.88501016703 .. 26.508888888889 m2/dwelling**
- net external wall:
  **29.637374678663 .. 212.071111111111 m2/dwelling**

Using the existing conservative P91/P92 thermal inputs, facade-only conservative
transmission upper:

**47.700254335904 .. 108.368337777778 W/K per dwelling**

These are synthetic reference-programme proxy bounds.

They are not household confidence intervals or realized project geometry.

## Geometry state after P95

The prospective reference-programme envelope geometry now has:

- facade magnitude: P95 TABULA estimator set;
- wall/opening split: P92 Hungarian class-average calibration;
- top envelope area: P93;
- bottom envelope area: P94.

Therefore:

`POST_RETROFIT_ENVELOPE_GEOMETRY_SURFACE_REQUIRED`

becomes:

`RESOLVED_FOR_REFERENCE_PROGRAMME_ENVELOPE_GEOMETRY_PROXY`

Realized/project use still requires:

`REALIZED_ENVELOPE_GEOMETRY_VERIFICATION_REQUIRED`

## Frozen boundaries

`BBOX AUDIT FAILURE != DATA DELETION`

`BBOX PROXY != CANONICAL REFERENCE-PROGRAMME FACADE AFTER P95`

`TABULA ESTIMATOR != OBSERVED FACADE AREA`

`HEATED FLOOR AREA != EXACT TABULA A_C_REF`

`TOTAL FLOOR AREA != EXACT TABULA A_C_REF`

`UNKNOWN NEIGHBOUR COUNT != DETACHED DEFAULT`

`TOTAL-ENVELOPE +/-30% != FACADE-SPECIFIC ERROR BOUND`

`REFERENCE-PROGRAMME PROXY != REALIZED PROJECT GEOMETRY`

## Remaining Q-B02-004 residuals

After P95 the current narrowed list is:

- `PITCHED_ROOF_POSTSTATE_U_BOUND_REQUIRED`
- `COMPLETE_LOCATION_TO_CURRENT_STANDARD_ZONE_MAPPING_REQUIRED`
- `DEFENSIBLE_NATIONAL_SUPPLY_TEMPERATURE_INFERENCE_REQUIRED`
- `FRESH_MULTI_SOURCE_ENVELOPE_ACTION_EVIDENCE_REQUIRED`

## Readiness

- B02 remains **55%**
- B06 `PEAK_LOAD_EFFECT` remains **50%**
- `Q-B02-004` remains **OPEN_NARROWED**

P95 removes a geometry blocker by replacing a failed route, not by weakening
the validation rule.
