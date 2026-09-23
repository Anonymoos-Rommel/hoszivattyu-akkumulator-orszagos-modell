# B02-P96 — PITCHED-ROOF POST-STATE U BOUND

## Goal

Resolve:

`PITCHED_ROOF_POSTSTATE_U_BOUND_REQUIRED`

for the prospective reference-programme branch without rewriting the historical
P80/P83 source state.

Base:

`e4825e2c06486e581ec3488ec6f304a7060d0ba2`

## Why the blocker existed

P80 correctly preserved the Csoknyai Table 9.1 source gap:

`TABLE_9_1_HAS_NO_EXPLICIT_PITCHED_ROOF_ROW`

and P82 generalized it to:

`PITCHED_ROOF_POSTSTATE_U_BOUND_REQUIRED`

That source-local absence remains historically true.

P96 resolves the modelling gap from an independent current legal authority.

## Current legal authority

`SRC-B06-HU-ENERGY-RULES-2023`

9/2023. (V. 25.) EKM Annex 1 section 1.1 gives the following element
requirement values:

- flat roof: `0.17 W/m2K`;
- structures enclosing heated attic space: `0.17 W/m2K`;
- ceiling below attic/crawl space: `0.17 W/m2K`.

The annex note states that for new buildings and renovations the designed
structures must also be checked for durability/building-physics protection.

P96 uses only the explicit:

`structures enclosing heated attic space = 0.17 W/m2K`

row as authority for the pitched/heated-attic reference-programme upper bound.

This is not inferred from flat roof or attic floor.

## Thermal-bridge correction

P91 independently pins the current Hungarian simplified thermal-bridge method.

For built-in attic enclosing structures:

`zeta in [0.10, 0.20]`

For the conservative reference-programme upper:

`U_R,max = U * (1 + zeta_max)`

therefore:

`U_R,max = 0.17 * 1.20 = 0.204 W/m2K`

The equivalent separate bridge increment is:

`Delta U_tb,max = 0.17 * 0.20 = 0.034 W/m2K`

Internal insulation remains outside the simplified zeta route and requires the
detailed method.

## P93 top-envelope handoff

P93 already materializes the thermal-envelope top area across all 14 strata.

The P93 quantity may represent:

- flat roof;
- pitched/heated-attic enclosing roof;
- upper ceiling below unheated attic;

depending the thermal-envelope state.

The current legal base U upper for all three relevant top-envelope classes is
0.17 W/m2K.

For a conservative type-unresolved top-envelope transmission bound, P96 uses
the largest admitted current simplified correction:

`U_R,max = 0.204 W/m2K`

This does not assert that every top envelope is a pitched roof.

## 14-stratum result

All:

`7 WBL construction periods x 2 P21 building groups = 14 strata`

receive the P96 top-envelope thermal upper.

Global P93 top-envelope area upper:

`196.392 m2/dwelling`

Therefore global conservative top-envelope transmission upper:

`H_top,max = 196.392 * 0.204`

= **40.063968 W/K/dwelling**

This is a reference-programme upper sensitivity.

It is not:

- an observed national U distribution;
- a household point value;
- proof of construction quality;
- an ex-post project acceptance value.

## Blocker effect

Previous:

`PITCHED_ROOF_POSTSTATE_U_BOUND_REQUIRED`

Current:

`RESOLVED_FOR_REFERENCE_PROGRAMME`

and the current reference-programme component-U input becomes:

`QUALIFIED_REFERENCE_PROGRAMME_COMPONENT_U_SURFACE`

because P80 already supplies:

- external wall;
- flat roof;
- attic floor;
- basement ceiling;
- window;

while P96 supplies the previously missing pitched/heated-attic enclosing
structure.

## Historical-state rule

P96 does not rewrite P80 or P83 historical evidence.

The statements:

`P80 TABLE 9.1 HAS NO EXPLICIT PITCHED ROOF ROW`

and:

`P83 PITCHED ROOF U = Q AT THAT SLICE`

remain historically correct.

P96 is a later independent-authority supersession layer.

## Realized/project boundary

For a specific building:

`REALIZED_PITCHED_ROOF_U_VERIFICATION_REQUIRED`

A project specification, as-built/commissioning evidence or equivalent
qualified evidence is required.

## Frozen boundaries

`REGULATORY U REQUIREMENT != OBSERVED REALIZED U`

`HEATED ATTIC ENCLOSURE != ALL ROOF GEOMETRY`

`PITCHED ROOF U BOUND != ROOF TYPE PREVALENCE`

`PITCHED ROOF U BOUND != REALIZED PROJECT ACCEPTANCE`

`P91 ZETA SIMPLIFIED ROUTE != DETAILED PSI/CHI ROUTE`

`P96 SUPERSEDES P80 PITCHED GAP != P80 SOURCE REWRITE`

## Remaining Q-B02-004 residuals

After P96 the narrowed reference-programme list is:

- `COMPLETE_LOCATION_TO_CURRENT_STANDARD_ZONE_MAPPING_REQUIRED`
- `DEFENSIBLE_NATIONAL_SUPPLY_TEMPERATURE_INFERENCE_REQUIRED`
- `FRESH_MULTI_SOURCE_ENVELOPE_ACTION_EVIDENCE_REQUIRED`

## Readiness

- B02 remains **55%**
- B06 `PEAK_LOAD_EFFECT` remains **50%**
- `Q-B02-004` remains **OPEN_NARROWED**

No readiness uplift is minted solely because the last envelope-U gap is closed.
