# B08-P3 — canonical seasonal reporting and national-load layer

## Purpose

P3 closes the B08 seasonal/calendar methodology gap and separates the national Hungarian control-area baseline from regional DSO/county claims.

Core rules:

`NATIONAL CONTROL-AREA BASELINE != REGIONAL DSO/COUNTY BASELINE`

`SEASON WINDOW != WEATHER EVENT`

`NATIONAL PEAK != SUM OF REGIONAL PEAKS`

`PUBLIC REPOSITORY MATERIALIZATION != MODEL-USE AUTHORITY`

## Canonical reporting policy

The reporting calendar is a project methodology contract with evidence status `POL`.

### Calendar year

For reporting year Y:

`[Y-01-01 00:00, (Y+1)-01-01 00:00)`

in `Europe/Budapest` local time.

### Winter

The canonical winter labelled Y is:

`[(Y-1)-12-01 00:00, Y-03-01 00:00)`

in `Europe/Budapest` local time.

This is a reporting convention. It is not a claim that every extreme-weather event occurs inside that window and it does not replace the separate B05 extreme-weather stress scenarios.

All source alignment is performed after conversion to UTC. Half-open interval semantics are explicit.

## Seasonal peak contract

A seasonal peak may be emitted only when:

- the entire reporting window is covered;
- the panel has no time gaps or overlaps;
- no value is missing;
- no admitted input row has evidence status `Q`;
- the source grain remains Hungarian control area for the national path.

Tied peak timestamps are retained.

No interpolation, resampling, gap filling or hidden annualization is allowed.

## National versus regional baseline

B08-P2 already established the source-native Hungarian ENTSO-E Actual Total Load semantics:

- document type A65;
- process A16;
- business type A04;
- Hungarian area `10YHU-MAVIR----U`;
- source-native PT15M/PT30M/PT60M intervals;
- UTC intake/provenance contract.

P3 clarifies that this source grain can support a **national Hungarian control-area baseline** without first producing a DSO/county panel.

Therefore:

`NO DSO/COUNTY LOAD PANEL != NATIONAL BASELINE BLOCKED`

For a real numeric national baseline, the following still remain mandatory:

- real acquired numeric load panel;
- source-specific model-use authority;
- complete acquisition provenance/checksum lineage.

The current repository does not yet contain such a real numeric panel, so the national numeric baseline remains Q.

## Regional claim boundary

The national control-area series cannot be relabelled or mechanically downscaled to:

- DSO service area;
- county;
- settlement;
- substation.

A regional claim requires either:

- source-native regional load evidence; or
- an explicit calibrated mapping contract with uncertainty.

Q-B01-002 remains a separate geography/orchestration question.

## Source permission boundary

Public-repository raw redistribution and model-use authority are separate controls.

P3 does not grant reuse permission and does not materialize ENTSO-E A65 raw values.

The lack of public-repository materialization permission does not create a requirement for regional data.

## Open-question effect

### Q-B08-002

`RESOLVED_CONTRACT`

Calendar-year definition, winter definition, timezone, half-open boundaries and peak extraction semantics are now executable.

### Q-B08-001

`OPEN_NARROWED`

The canonical source product, source grain, time basis and provenance contract are already established by P2. P3 removes regional mapping as a prerequisite for the national baseline.

Remaining national blockers are:

- real numeric source acquisition;
- model-use authority for that acquisition;
- complete acquisition provenance.

Regional DSO/county load remains a separate claim layer.

## Readiness

B08 module readiness remains **45%**.

The seasonal reporting contract is now executable, but no real national numeric snapshot has been admitted, so no arbitrary module-level readiness uplift is applied.
