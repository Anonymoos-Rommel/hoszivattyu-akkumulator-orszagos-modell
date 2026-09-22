# B02-P92 — HUNGARIAN FACADE / OPENING SPLIT PROXY

## Goal

Resolve the P85 facade split residual for the prospective
`REFERENCE_ENVELOPE_RETROFIT_PLUS_AWHP` branch without inventing a universal
window-to-wall ratio.

Base:
`de294488c2b56eea76c16943eec34b617a551e52`

Previous residual:

`NET_EXTERNAL_WALL_AND_WINDOW_AREA_SPLIT_INFERENCE_REQUIRED`

P92 uses Hungarian TABULA/EPISCOPE class-average envelope geometry as a
reference-programme calibration and preserves all source-native limitations.

## Source authority

`SRC-B02-EU-TABULA-DATABASE-EVALUATION-2015`

The December-2015 TABULA/EPISCOPE database evaluation uses the April-2015
database version. Hungarian BME contributors are listed among the project
partners.

The report defines:

- `A_Wall = A_Wall_1 + A_Wall_2 + A_Wall_3`
- `A_Window = A_Window_1 + A_Window_2 + A_Door_1`

Therefore:

`TABULA A_Window != WINDOW-ONLY AREA`

P92 calls the aggregate quantity:

`OPENING_AREA`

to preserve the source semantics.

The same report states that envelope-area indicators from example buildings may
serve as a preliminary basis for synthetic average buildings when deeper
empirical building-stock geometry is unavailable.

This permits a **reference-programme calibration**.

It does not establish a household-level or age-specific observed distribution.

## Hungarian class-average geometry

Table 4 gives the following Hungarian values, averaged across construction-year
classes within each available building-size class.

### SFH

- conditioned floor area: 112 m2
- wall area: 128 m2
- aggregate opening area: 16 m2

Gross facade:

`128 + 16 = 144 m2`

Opening share:

`16 / 144 = 0.111111111111`

### MFH

- conditioned floor area: 644 m2
- wall area: 668 m2
- aggregate opening area: 97 m2

Gross facade:

`668 + 97 = 765 m2`

Opening share:

`97 / 765 = 0.126797385621`

### AB

- conditioned floor area: 1702 m2
- wall area: 1197 m2
- aggregate opening area: 359 m2

Gross facade:

`1197 + 359 = 1556 m2`

Opening share:

`359 / 1556 = 0.230719794344`

Hungarian TH values are absent from the evaluated table.

## Mapping to the project building groups

### FAMILY_HOUSE

P92 uses the available Hungarian SFH class-average calibration:

`opening_share = 0.111111111111`

The equal lower/upper values mean:

**one available Hungarian class-average reference point**

and do **not** mean zero population variance.

### MULTI_DWELLING

P21 does not point-identify the national stratum as TABULA MFH versus AB.

P92 therefore preserves both Hungarian class-average states:

`opening_share = 0.126797385621 .. 0.230719794344`

No MFH/AB population mixture or midpoint is invented.

## P85 gross-facade dependency

P85 provides:

`bbox_rectangular_facade_proxy`

not source-native facade area.

P92 therefore applies the Hungarian opening-share calibration to the P85 proxy
conditionally.

For gross facade interval:

`G = [G_lo, G_hi]`

and opening share:

`s = [s_lo, s_hi]`

P92 computes the outer interval:

`A_opening = [G_lo*s_lo, G_hi*s_hi]`

`A_wall,net = [G_lo*(1-s_hi), G_hi*(1-s_lo)]`

This resolves the **partition rule**.

It does not prove that the rectangularized P85 facade magnitude equals the
actual thermally exposed facade.

Canonical boundary:

`FACADE SPLIT CALIBRATION != BBOX VALIDATION`

## 14-stratum result

P92 materializes all:

`7 WBL construction periods x 2 P21 building groups = 14 strata`

Global descriptive proxy extrema:

- aggregate opening area:
  **4.414150670801 .. 36.48 m2/dwelling**
- net external wall area:
  **26.780668380503 .. 291.84 m2/dwelling**

These are set-valued **synthetic reference-programme proxies**.

They are not household bounds or statistical national confidence intervals.

## Aggregate opening transmission upper route

B06 does not require a component to be named specifically WINDOW. It requires
explicit component U and A inputs.

Current Hungarian element limits include:

- wood/PVC glazed facade opening >0.5 m2:
  **1.10 W/m2K**
- ordinary facade / heated-to-unheated external door:
  **1.40 W/m2K**

Because the TABULA aggregate opening area contains windows plus a door, P92
uses:

`U_opening,upper = 1.40 W/m2K`

only as a **conservative aggregate opening upper sensitivity**.

This avoids inventing a window/door area split for the upper design-load route.

It does not claim:

- every window has U=1.40;
- every door has U=1.40;
- realized project opening U-values are known.

Using P91:

`U_wall,R,upper = 0.336 W/m2K`

the correlated facade-only conservative upper is:

`H_facade,upper = G_hi * ((1-s_hi)*0.336 + s_hi*1.40)`

Across the 14 current proxy strata:

**55.194637943445 .. 149.13024 W/K per dwelling**

This remains facade-only and BBOX-dependent.

## Blocker effect

Previous:

`NET_EXTERNAL_WALL_AND_WINDOW_AREA_SPLIT_INFERENCE_REQUIRED`

Current reference-programme status:

`RESOLVED_FOR_REFERENCE_PROGRAMME_OPENING_SPLIT`

Current residual from this branch:

`BBOX_RECTANGULARIZATION_VALIDATION_REQUIRED`

The window/door sub-split is not required for a conservative aggregate
transmission upper, because the source-native aggregate opening definition is
preserved and a conservative aggregate U upper is available.

A window-only or door-only point estimate would still require a separate split.

## Remaining geometry chain

Still open:

- `ACTUAL_TOP_HEAT_LOSS_PLANE_AREA_INFERENCE_REQUIRED`
- `ACTUAL_BOTTOM_HEAT_LOSS_PLANE_AREA_INFERENCE_REQUIRED`
- `BBOX_RECTANGULARIZATION_VALIDATION_REQUIRED`
- `PITCHED_ROOF_POSTSTATE_U_BOUND_REQUIRED`

Independent later residuals include:

- `COMPLETE_LOCATION_TO_CURRENT_STANDARD_ZONE_MAPPING_REQUIRED`
- `DEFENSIBLE_NATIONAL_SUPPLY_TEMPERATURE_INFERENCE_REQUIRED`
- `FRESH_MULTI_SOURCE_ENVELOPE_ACTION_EVIDENCE_REQUIRED`

## Realized/project boundary

For an actual dwelling:

`REALIZED_FACADE_GEOMETRY_VERIFICATION_REQUIRED`

Project geometry, survey, BIM/as-built data or equivalent qualified evidence is
required.

## Frozen boundaries

`TABULA A_WINDOW INCLUDES DOOR`

`OPENING AREA != WINDOW-ONLY AREA`

`HU CLASS AVERAGE != HOUSEHOLD AREA SHARE`

`HU CLASS AVERAGE != AGE-SPECIFIC OPENING SHARE`

`P85 BBOX FACADE PROXY != SOURCE-NATIVE TABULA FACADE`

`FACADE SPLIT CALIBRATION != BBOX VALIDATION`

`NO UNIVERSAL 20% WINDOW DEFAULT`

## Readiness

- B02 remains **55%**
- B06 `PEAK_LOAD_EFFECT` remains **50%**
- `Q-B02-004` remains **OPEN_NARROWED**

P92 removes one geometry partition blocker, but the full B06 geometry surface
is not yet qualified.
