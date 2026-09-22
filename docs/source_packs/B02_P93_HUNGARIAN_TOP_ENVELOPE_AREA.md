# B02-P93 — HUNGARIAN TOP-ENVELOPE AREA CALIBRATION

## Goal

Resolve:

`ACTUAL_TOP_HEAT_LOSS_PLANE_AREA_INFERENCE_REQUIRED`

for the prospective reference-programme branch without converting a mean storey
floorplate or bbox plan into a roof area.

Base:

`5daee8571b09281dee16bb8a8f37693b50dc0e79`

## Source authority

`SRC-B02-EU-TABULA-DATABASE-EVALUATION-2015`

The TABULA/EPISCOPE database evaluation defines:

`A_Roof = A_Roof_1 + A_Roof_2`

The source roof/attic fields show that the thermal-envelope top element may be:

- tilted roof;
- flat roof;
- upper floor ceiling below an unheated attic;

depending on the example-building attic state.

Therefore P93 models:

`TOP_ENVELOPE_AREA`

not:

`UNIVERSAL_PITCHED_ROOF_AREA`

The same report states that envelope-area indicators may serve as a preliminary
basis for synthetic average buildings where no deeper empirical stock geometry
is available.

This is the exact modelling role used here.

## Hungarian published class-average ratios

Table 4 publishes average thermal-envelope area ratios, averaged over
construction-year classes and differentiated by size class.

### SFH

`A_Roof / A_C_Ref = 0.84 m2/m2`

### MFH

`A_Roof / A_C_Ref = 0.35 m2/m2`

### AB

`A_Roof / A_C_Ref = 0.20 m2/m2`

Hungarian TH is absent.

These published ratios are used directly.

P93 deliberately does **not** recompute them as:

`average(A_Roof) / average(A_C_Ref)`

because the published ratio row is the source-native aggregated indicator.

## Mapping to project groups

### FAMILY_HOUSE

Uses the available HU SFH class-average ratio:

`0.84`

This is a single synthetic-average calibration point.

It is not evidence of zero population variance.

### MULTI_DWELLING

P21 does not identify MFH versus AB.

Therefore P93 preserves:

`0.20 .. 0.35`

No MFH/AB prevalence or midpoint is invented.

## Scaling to canonical heated-floor area

P93 does not transplant the absolute TABULA example-house roof area into every
national stratum.

Instead, for canonical P85 heated-floor-area interval:

`A_C = [A_C,lo, A_C,hi]`

and admitted top-area ratio:

`r = [r_lo, r_hi]`

the positive interval is:

`A_top = [A_C,lo*r_lo, A_C,hi*r_hi]`

This preserves building-size scaling.

## 14-stratum result

All:

`7 WBL construction periods x 2 P21 building groups = 14 strata`

receive an explicit top-envelope-area proxy.

Global descriptive range:

**10.96777777778 .. 196.392 m2/dwelling**

This is a reference-programme synthetic geometry proxy.

It is not:

- a household min/max;
- an observed national distribution;
- an age-specific roof-area distribution;
- a realized project measurement.

## Important independence from pitched-roof U

P93 resolves geometry only.

`KNOWN TOP ENVELOPE AREA != KNOWN PITCHED-ROOF U`

The current P80/P85 state still has:

`PITCHED_ROOF_POSTSTATE_U_BOUND_REQUIRED`

Therefore P93 does not use the top-area proxy to manufacture a complete
transmission term where the component thermal type/U is unresolved.

This separation is intentional.

## Blocker effect

Previous:

`ACTUAL_TOP_HEAT_LOSS_PLANE_AREA_INFERENCE_REQUIRED`

Current:

`RESOLVED_FOR_REFERENCE_PROGRAMME_TOP_ENVELOPE_PROXY`

Still open in the geometry chain:

- `ACTUAL_BOTTOM_HEAT_LOSS_PLANE_AREA_INFERENCE_REQUIRED`
- `BBOX_RECTANGULARIZATION_VALIDATION_REQUIRED`
- `PITCHED_ROOF_POSTSTATE_U_BOUND_REQUIRED`

Other independent residuals remain:

- `COMPLETE_LOCATION_TO_CURRENT_STANDARD_ZONE_MAPPING_REQUIRED`
- `DEFENSIBLE_NATIONAL_SUPPLY_TEMPERATURE_INFERENCE_REQUIRED`
- `FRESH_MULTI_SOURCE_ENVELOPE_ACTION_EVIDENCE_REQUIRED`

## Realized/project boundary

For a specific building:

`REALIZED_TOP_ENVELOPE_GEOMETRY_VERIFICATION_REQUIRED`

A survey, BIM/as-built geometry or equivalent qualified project evidence is
required.

## Frozen boundaries

`A_ROOF = THERMAL-ENVELOPE TOP AREA`

`A_ROOF MAY BE ROOF OR UPPER CEILING DEPENDING ATTIC STATE`

`HU CLASS-AVERAGE RATIO != HOUSEHOLD RATIO`

`HU CLASS-AVERAGE RATIO != AGE-SPECIFIC RATIO`

`TOP-AREA CALIBRATION != PITCHED-ROOF U RESOLUTION`

`TOP-AREA CALIBRATION != BBOX PLAN AREA`

## Readiness

- B02 remains **55%**
- B06 `PEAK_LOAD_EFFECT` remains **50%**
- `Q-B02-004` remains **OPEN_NARROWED**

No readiness uplift is minted solely because this geometry residual is retired.
