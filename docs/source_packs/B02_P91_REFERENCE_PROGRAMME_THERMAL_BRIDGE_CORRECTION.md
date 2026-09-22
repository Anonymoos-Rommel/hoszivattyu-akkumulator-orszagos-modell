# B02-P91 — REFERENCE-PROGRAMME THERMAL-BRIDGE CORRECTION

## Goal

Close the independent thermal-bridge correction blocker for the prospective
`REFERENCE_ENVELOPE_RETROFIT_PLUS_AWHP` branch without fabricating a national
inventory of line-bridge lengths or psi-values.

Base:
`51f4303d391a35c49930f918ed8a1fc288404c48`

## Current Hungarian method authority

`SRC-B06-HU-ENERGY-METHOD-2023`

Appendix 1 section 6.1.2 defines two valid routes.

### Detailed route

`H_tr,D = sum(A_i*U_i) + sum(l_k*psi_k) + sum(chi_j)`

The detailed route may use thermal-bridge catalogues or numerical modelling
under MSZ EN ISO 10211.

### Simplified route

`H_tr = sum(A_i*U_R,i)`

with

`U_R = U*(1+zeta)`

P91 uses this simplified route for the prospective reference-programme model.

The equivalent bridge-only term needed by the current B06 interface is:

`H_tb = A*U*zeta`

because:

`A*U*(1+zeta) = A*U + A*U*zeta`

Therefore the B06 separate thermal-bridge term can remain explicit while being
exactly equivalent to the current simplified method.

## Applicability gate

The current method states that the zeta correction factor cannot be used for
structures insulated on the **internal side**.

Therefore P91 contracts:

- non-internal-insulation reference-programme route -> simplified zeta method;
- internal insulation -> `DETAILED_THERMAL_BRIDGE_MODEL_REQUIRED`.

This is fail-closed.

P91 does not claim that internal insulation is absent from the observed
Hungarian stock. It defines the prospective reference-programme calculation
route.

## Current-method zeta envelopes

### External walls

Current table 6.1:

For uninterrupted external-side or within-structure insulation:

- weak thermal bridging: 0.15
- medium: 0.20
- strong: 0.30

For other external walls:

- weak: 0.25
- medium: 0.30
- strong: 0.40

Because national insulation position and bridge class are not point-identified,
P91 preserves the full eligible method envelope:

**zeta = 0.15 .. 0.40**

No midpoint or prevalence weighting is introduced.

### Flat roofs

**zeta = 0.10 .. 0.20**

### Attic floors

**zeta = 0.10**

### Basement ceilings

- within-structure insulation: 0.20
- lower-side insulation: 0.10

P91 preserves:

**zeta = 0.10 .. 0.20**

### Pitched-roof / built-in-attic enclosing structures

**zeta = 0.10 .. 0.20**

The correction-factor method is known, but P80/P85 still lacks the explicit
pitched-roof post-retrofit U bound. Therefore complete pitched-roof heat loss
remains separately Q.

## Reference-retrofit corrected U upper sensitivities

Using the existing P80 reference-retrofit U upper bounds:

| Component | U max | zeta upper | U_R upper |
| --- | ---: | ---: | ---: |
| External wall | 0.24 | 0.40 | **0.336 W/m2K** |
| Flat roof | 0.17 | 0.20 | **0.204 W/m2K** |
| Attic floor | 0.17 | 0.10 | **0.187 W/m2K** |
| Basement ceiling | 0.26 | 0.20 | **0.312 W/m2K** |

These are conservative method-consistent upper sensitivities.

They are not realized point U-values.

## Windows and double counting

P91 does not apply another generic zeta correction directly to the P80 window
U-value.

The current method requires that bridge effects already included in a
component's average U-value must not be counted again in the transmission sum.

For the external-wall simplified classification, window perimeters are already
among the geometry terms used to determine thermal-bridge class.

Canonical boundary:

`BRIDGE EFFECT ALREADY IN U != ADD AGAIN`

## 14-stratum surface

The P91 data surface is materialized across the same 14:

`7 WBL construction periods x 2 P21 building groups`

The zeta envelope itself is method-defined, while each row remains joined to
the P80/P85 reference-retrofit component U bounds.

This means the thermal-bridge correction factor is no longer an independent
unknown.

Actual `H_tb` still depends on component area:

`H_tb = A*U*zeta`

but component-area geometry is already a separately tracked blocker. P91 does
not duplicate that blocker under another name.

## Blocker effect

Previous:

`POST_RETROFIT_THERMAL_BRIDGE_SURFACE_REQUIRED`

Current reference-programme state:

`RESOLVED_FOR_REFERENCE_PROGRAMME_SIMPLIFIED_ROUTE`

The independent thermal-bridge correction-factor blocker is retired.

Still independent:

- `NET_EXTERNAL_WALL_AND_WINDOW_AREA_SPLIT_INFERENCE_REQUIRED`
- `ACTUAL_TOP_HEAT_LOSS_PLANE_AREA_INFERENCE_REQUIRED`
- `ACTUAL_BOTTOM_HEAT_LOSS_PLANE_AREA_INFERENCE_REQUIRED`
- `BBOX_RECTANGULARIZATION_VALIDATION_REQUIRED`
- `PITCHED_ROOF_POSTSTATE_U_BOUND_REQUIRED`

## Realized/project boundary

For project-specific detailed claims:

`REALIZED_THERMAL_BRIDGE_VERIFICATION_REQUIRED`

Acceptable detailed routes include:

- project-specific thermal-bridge catalogue;
- numerical modelling;
- other qualified line/point bridge evidence compatible with the current
  method.

Internal insulation automatically falls into the detailed route.

## Frozen boundaries

`SIMPLIFIED ZETA ROUTE != DETAILED PSI/CHI ROUTE`

`REFERENCE PROGRAMME ZETA != OBSERVED THERMAL-BRIDGE DISTRIBUTION`

`INTERNAL INSULATION != ZETA-ELIGIBLE`

`THERMAL-BRIDGE FACTOR != COMPONENT-AREA GEOMETRY`

`KNOWN PITCHED-ROOF ZETA != RESOLVED PITCHED-ROOF U`

`REFERENCE PROGRAMME CORRECTION != REALIZED PROJECT PERFORMANCE`

## Readiness

- B02 remains **55%**
- B06 `PEAK_LOAD_EFFECT` remains **50%**
- `Q-B02-004` remains **OPEN_NARROWED**

No readiness uplift is minted solely because one independent input blocker was
removed.
