# B02-P94 — HUNGARIAN BOTTOM-ENVELOPE AREA CALIBRATION

## Goal

Resolve:

`ACTUAL_BOTTOM_HEAT_LOSS_PLANE_AREA_INFERENCE_REQUIRED`

for the prospective reference-programme branch without treating mean floorplate,
bbox plan or dwelling floor area as the actual lower thermal-envelope area.

Base:

`cbba591f4b29539dec51125dc46484da0d1a025a`

## Source authority

`SRC-B02-EU-TABULA-DATABASE-EVALUATION-2015`

The TABULA/EPISCOPE database evaluation defines:

`A_Floor = A_Floor_1 + A_Floor_2`

The two source fields are thermal-envelope floor element areas measured with
external dimensions.

P94 therefore models:

`BOTTOM_ENVELOPE_AREA`

not:

- universal ground-contact floor area;
- universal basement-ceiling area;
- a boundary-type-specific U-value state.

The same report states that envelope-area indicators may serve as a preliminary
basis for synthetic average buildings where deeper empirical stock geometry is
not available.

## Hungarian published class-average ratios

Table 4 publishes the following Hungarian values.

### SFH

`A_Floor / A_C_Ref = 0.80 m2/m2`

### MFH

`A_Floor / A_C_Ref = 0.33 m2/m2`

### AB

`A_Floor / A_C_Ref = 0.20 m2/m2`

Hungarian TH is absent.

These are source-native published class-average indicators, averaged over
construction-year classes.

## Mapping to project groups

### FAMILY_HOUSE

Uses:

`0.80`

as the available Hungarian SFH class-average reference calibration.

This is not evidence of zero household variance.

### MULTI_DWELLING

P21 does not identify MFH versus AB.

P94 therefore preserves:

`0.20 .. 0.33`

No class mixture or midpoint is invented.

## Scaling to canonical heated-floor area

P94 does not transplant absolute TABULA example-building floor areas.

For canonical P85 heated-floor-area interval:

`A_C = [A_C,lo, A_C,hi]`

and bottom-envelope ratio:

`r = [r_lo, r_hi]`

the positive interval is:

`A_bottom = [A_C,lo*r_lo, A_C,hi*r_hi]`

## 14-stratum result

All:

`7 WBL construction periods x 2 P21 building groups = 14 strata`

receive an explicit bottom-envelope-area proxy.

Global descriptive range:

**10.96777777778 .. 187.04 m2/dwelling**

This is a reference-programme synthetic geometry proxy.

It is not:

- a household min/max;
- a measured national distribution;
- an age-specific floor-area ratio;
- a realized project measurement.

## Boundary-type separation

P94 resolves geometry only.

`KNOWN BOTTOM ENVELOPE AREA != KNOWN BOTTOM BOUNDARY TYPE`

and:

`KNOWN BOTTOM ENVELOPE AREA != KNOWN BOTTOM COMPONENT U`

The source aggregate A_Floor does not justify assigning every square metre to
ground contact or every square metre to basement ceiling.

Any such physical classification remains an independent modelling/evidence
decision.

## Blocker effect

Previous:

`ACTUAL_BOTTOM_HEAT_LOSS_PLANE_AREA_INFERENCE_REQUIRED`

Current:

`RESOLVED_FOR_REFERENCE_PROGRAMME_BOTTOM_ENVELOPE_PROXY`

The remaining geometry chain is now reduced to:

- `BBOX_RECTANGULARIZATION_VALIDATION_REQUIRED`
- `PITCHED_ROOF_POSTSTATE_U_BOUND_REQUIRED`

Other independent residuals remain:

- `COMPLETE_LOCATION_TO_CURRENT_STANDARD_ZONE_MAPPING_REQUIRED`
- `DEFENSIBLE_NATIONAL_SUPPLY_TEMPERATURE_INFERENCE_REQUIRED`
- `FRESH_MULTI_SOURCE_ENVELOPE_ACTION_EVIDENCE_REQUIRED`

## Realized/project boundary

For a specific building:

`REALIZED_BOTTOM_ENVELOPE_GEOMETRY_VERIFICATION_REQUIRED`

Survey, BIM/as-built geometry or equivalent qualified project evidence is
required.

## Frozen boundaries

`A_FLOOR = THERMAL-ENVELOPE BOTTOM AREA`

`BOTTOM AREA != GROUND-FLOOR-ONLY`

`BOTTOM AREA != BASEMENT-CEILING-ONLY`

`HU CLASS-AVERAGE RATIO != HOUSEHOLD RATIO`

`HU CLASS-AVERAGE RATIO != AGE-SPECIFIC RATIO`

`BOTTOM-AREA CALIBRATION != BOUNDARY-TYPE OR U RESOLUTION`

## Readiness

- B02 remains **55%**
- B06 `PEAK_LOAD_EFFECT` remains **50%**
- `Q-B02-004` remains **OPEN_NARROWED**

No readiness uplift is minted solely because this geometry residual is retired.
