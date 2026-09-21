# B02-P77 — national transition-response coverage gates

**State:** `METHOD QUALIFIED / NATIONAL INPUT SURFACES Q / PRODUCT DOMAIN QUANTIFIED PARTIAL`

**Canonical base:** `b85b7637194adf3d37b7ed9780103c0d5c022d9e`

**Implementation date:** 2026-09-21

## 1. Purpose

P74 correctly established that the repository does **not** need an external
generic AWHP saving percentage.

The physical chain already exists:

`B06 transition state -> B06-P65 required supply temperature -> B05 capacity/COP map`.

P77 asks a different question:

> What prevents that record/project method from becoming a national
> archetype/cell response surface?

The answer is not one missing datum. It is an ordered coverage chain.

## 2. Existing executable method

B06 already provides:

- explicit envelope/design-load physics;
- independent post-state design-load calculation;
- P65 fail-closed post-retrofit emitter-temperature authority;
- a B05 design-point bridge that calls the canonical
  `PerformanceMap.evaluate()` method;
- no W35/W45/W55 snapping and no out-of-domain extrapolation.

Therefore:

`PHYSICAL RESPONSE METHOD = QUALIFIED`.

But:

`METHOD EXISTS != NATIONAL INPUT SURFACE EXISTS`.

## 3. Gate 1 — national post-retrofit design-load surface

The B06 readiness contract explicitly states that national/building-stock
physical-state input coverage remains partial.

P21/WBL supplies population/archetype structure and modelled energy context.
It does not by itself supply the complete post-retrofit physical inputs
required by B06 design-load physics.

Therefore:

`P21/WBL POPULATION WEIGHT != POST-RETROFIT DESIGN LOAD`.

Current blocker:

`NATIONAL_POST_RETROFIT_DESIGN_LOAD_SURFACE_REQUIRED`.

## 4. Gate 2 — P65 national supply-temperature surface

P65 intentionally accepts only:

- complete room-by-room post-state design;
- complete signed/sealed post-retrofit MEP design; or
- complete design-condition measurement.

Emitter type names, W35/W45/W55 labels, current boiler setpoints and national
averages cannot mint a building supply temperature.

Therefore:

`EMITTER CLASS != P65 REQUIRED SUPPLY TEMPERATURE`.

Current blocker:

`NATIONAL_P65_SUPPLY_TEMPERATURE_SURFACE_REQUIRED`.

This is population coverage, not a missing temperature formula.

## 5. Gate 3 — B05 product design-point coverage

Once Gates 1 and 2 provide an actual design point, B05 can evaluate it only
inside a source-supported product map.

P77 binds the already-materialized B05 supply-specific product-domain audit.

Reference product:

`STIEBEL-HPA-O-4-CS-PLUS-INT`.

Reference weather profile:

`B05-EXTREME-OBSERVED-72H-15310`.

### W35

Source-supported continuous weather-temperature domain:

`-15 C .. +7 C`.

Observed extreme profile:

- total: **72 h**;
- inside product domain: **35 h**;
- below domain: **37 h**;
- weather-domain coverage: **48.6111%**;
- coldest uncovered temperature: **-21.9 C**.

### W45

Source-supported continuous domain:

`-7 C .. +7 C`.

Observed extreme profile:

- inside: **9 h**;
- below domain: **63 h**;
- weather-domain coverage: **12.5%**;
- coldest uncovered: **-21.9 C**.

### W55

Only an isolated A7/W55 source-native point is admitted.

No continuous cold-side W55 surface exists.

Status:

`Q`.

## 6. Critical interpretation boundary

The percentages above are **weather-domain coverage only**.

They answer:

> for how many observed outdoor-temperature hours does this fixed supply
> surface have source-supported product-map coverage?

They do **not** answer:

- how many heating-runtime hours are covered;
- what fraction of national heat demand is covered;
- what fraction of dwellings operates at W35/W45/W55;
- seasonal COP coverage;
- national product-market coverage.

Therefore:

`WEATHER-DOMAIN COVERAGE != HEATING-RUNTIME COVERAGE`.

## 7. B05 blocker repair

Old broad blocker:

`B05_PRODUCT_OPERATING_POINT_COVERAGE_REQUIRED`.

P77 status:

`PARTIAL_QUANTIFIED_PRODUCT_DOMAIN`.

Current concrete product-domain gaps:

- `B05_COLD_W45_PRODUCT_GRID_REQUIRED`;
- `B05_CONTINUOUS_W55_PRODUCT_SURFACE_REQUIRED`;
- `B05_W35_BELOW_MINUS15_PRODUCT_GRID_REQUIRED_IF_EXTREME_IN_SCOPE`.

The first two are unconditional current-map gaps for high-supply operation.
The third matters when the observed extreme profile is part of the requested
analysis scope.

## 8. National materialization blocker repair

Old broad blocker:

`NATIONAL_TRANSITION_RESPONSE_MATERIALIZATION_BY_ARCHETYPE_REQUIRED`.

P77 replaces it with:

1. `NATIONAL_POST_RETROFIT_DESIGN_LOAD_SURFACE_REQUIRED`;
2. `NATIONAL_P65_SUPPLY_TEMPERATURE_SURFACE_REQUIRED`;
3. `B05_MATERIALIZED_DESIGN_POINT_COVERAGE_REQUIRED`.

These gates are ordered.

A product-map coverage percentage cannot compensate for missing physical
building inputs, and a building archetype cannot be snapped to a product test
temperature.

Canonical rule:

`POPULATION MATERIALIZATION = PHYSICAL INPUT SURFACE + P65 TEMPERATURE AUTHORITY + PRODUCT MAP COVERAGE`.

## 9. Non-claims

P77 does not claim:

- 48.6% or 12.5% heating-runtime coverage;
- W35/W45/W55 population shares;
- a national seasonal COP;
- the 72-hour observed event is a 1-in-10 cold spell;
- all Hungarian buildings require one of the three nominal supply labels;
- B05 product diversity is nationally representative;
- Q-B02-004 is resolved.

B02 readiness remains **55%**.
