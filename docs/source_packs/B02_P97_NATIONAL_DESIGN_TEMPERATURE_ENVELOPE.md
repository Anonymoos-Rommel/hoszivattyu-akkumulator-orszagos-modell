# B02-P97 — NATIONAL SET-VALUED CURRENT-STANDARD DESIGN-TEMPERATURE ENVELOPE

## Goal

Resolve the national reference-programme dependency:

`COMPLETE_LOCATION_TO_CURRENT_STANDARD_ZONE_MAPPING_REQUIRED`

without inventing an exact settlement-to-zone map that cannot be represented
on the canonical KSH population grain.

Base:

`f228e566d44de19e5bf2f644549678344bb73e89`

## Why exact settlement mapping is the wrong national requirement

P86 established:

- current standard: `MSZ 24140:2026`;
- current zone values: `-12 / -11 / -10 C`;
- 20 public city control points;
- exact project/location mapping remains fail-closed.

The canonical national WBL population grain is not a settlement coordinate
grain. It is built from:

- county;
- settlement type;
- construction period;
- other dwelling/physical dimensions.

Therefore:

`COUNTY + SETTLEMENT TYPE != EXACT SETTLEMENT COORDINATE`

An exact national settlement-zone join would create false precision even if a
copyrighted polygon map were digitized externally.

## P82 inference rule

P82 already established the project-wide national physical-input principle:

`NO FULL-POPULATION DATA != BLOCKER`

`NO DEFENSIBLE POPULATION INFERENCE == BLOCKER`

`POPULATION ESTIMATE != RECORD PASS/FAIL`

It also explicitly generalized design-outdoor-temperature evidence into a
reproducible climate/location methodology rather than a household-microdata
requirement.

P97 applies that existing rule.

## Public current-standard authority

Official MSZT authority:

`SRC-B02-MSZ-24140-2026`

confirms:

- MSZ 24140:2026 is current from 2026-04-01;
- it replaced MSZ 24140:2015;
- the revised standard contains a new design-outdoor-temperature map.

Public current technical interpretation:

`SRC-B02-BIMLINE-MSZ24140-2026`

reports the F1 map domain:

- `-12 C`
- `-11 C`
- `-10 C`

and preserves the application caveats already frozen by P86:

- baseline values reported for settlements above 30,000 population;
- baseline values reported for elevations <=300 m;
- local/project conditions can justify an explicitly authorized departure.

P97 does not remove those project-level caveats.

## National reference-programme decision

For national bounded propagation, P97 admits the full current-standard zone
set:

`theta_e in {-12, -11, -10} C`

It does not choose:

- a most-likely zone;
- a county default;
- a settlement-type default;
- a population-weighted midpoint.

Current residential service reference:

`theta_i = 20 C`

Therefore:

`Delta T = theta_i - theta_e`

gives:

- at -10 C: `30 K`
- at -11 C: `31 K`
- at -12 C: `32 K`

Hence:

`Delta T in [30,32] K`

## Physical meaning of the uncertainty

For a fixed positive heat-loss coefficient H:

`Q_design = H * Delta T`

Therefore the complete current-map location uncertainty propagates
monotonically as:

`Q_lower = H * 30`

`Q_upper = H * 32`

The location-only spread is:

`32 / 30 = 1.066666666667`

or:

**6.6666666667%**

between the warmest and coldest admitted current-map baseline design
conditions.

P97 preserves that uncertainty instead of hiding it behind a point zone.

## 14-stratum materialization

The national reference-programme design-temperature envelope is materialized
for all:

`7 WBL construction periods x 2 P21 building groups = 14 strata`

Each row carries:

- zone set `{-12,-11,-10}`;
- indoor reference `20 C`;
- `Delta T = 30..32 K`;
- location-only load spread ratio `1.066666666667`.

The same set across strata is intentional: P97 has no evidence that
construction age or P21 building group determines climate zone.

## Why this resolves the national blocker

The programme does not need a false point zone for every WBL cell to produce a
bounded national design-load response.

The full current-standard baseline zone set is finite, explicit and monotone in
the design-load equation.

Therefore, for the prospective reference-programme national model:

`COMPLETE_LOCATION_TO_CURRENT_STANDARD_ZONE_MAPPING_REQUIRED`

is superseded by:

`QUALIFIED_REFERENCE_PROGRAMME_STANDARD_ZONE_ENVELOPE`

and is no longer a national design-load blocker.

## What remains fail-closed

P86's project-level resolver is unchanged.

For a specific building or project:

`REALIZED_LOCATION_STANDARD_ZONE_VERIFICATION_REQUIRED`

remains.

The project must still establish:

- exact current-standard location/baseline;
- local altitude;
- applicability of the >30,000 / <=300 m baseline;
- any authorized urban-heat-island, sensitive-function or other local/risk
  adjustment.

P97 cannot pass a specific project.

## Frozen boundaries

`NATIONAL ZONE SET != EXACT SETTLEMENT ZONE`

`CURRENT STANDARD DOMAIN != PROJECT DESIGN AUTHORITY`

`SET-VALUED PROPAGATION != MOST-LIKELY ZONE`

`COUNTY + SETTLEMENT TYPE GRAIN != SETTLEMENT COORDINATE`

`BASELINE MAP SCOPE != AUTOMATIC PROJECT COMPLIANCE OUTSIDE SCOPE`

`NATIONAL REFERENCE PROGRAMME != REALIZED PROJECT ACCEPTANCE`

## Q-B02-004 effect

The reference-programme residual:

`COMPLETE_LOCATION_TO_CURRENT_STANDARD_ZONE_MAPPING_REQUIRED`

is removed.

The main narrowed residuals now include:

- `DEFENSIBLE_NATIONAL_SUPPLY_TEMPERATURE_INFERENCE_REQUIRED`
- `FRESH_MULTI_SOURCE_ENVELOPE_ACTION_EVIDENCE_REQUIRED`

Other independent model-contract blockers remain governed by their own
modules and are not silently resolved by P97.

## Readiness

- B02 remains **55%**
- B06 `PEAK_LOAD_EFFECT` remains **50%**
- `Q-B02-004` remains **OPEN_NARROWED**

P97 improves physical completeness but does not mint a readiness uplift by
itself.
