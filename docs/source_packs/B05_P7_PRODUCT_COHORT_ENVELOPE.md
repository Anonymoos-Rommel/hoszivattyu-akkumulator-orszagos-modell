# B05-P7 — representative observed product-cohort performance envelope

## Purpose

B05-P7 applies the project-wide population-inference policy to heat-pump product performance without weakening exact product sizing.

Core boundaries:

`PRODUCT-COHORT ENVELOPE != PRODUCT-SPECIFIC PERFORMANCE MAP`

`CROSS-MANUFACTURER COMMON POINT != NATIONAL MARKET SHARE`

`MISSING COMMON POINT != LICENSE TO EXTRAPOLATE`

`OPERATING LIMIT != PERFORMANCE POINT`

The national/programme model does not require a single reference heat-pump model to provide every W35/W45/W55 operating point. It may use a bounded cohort envelope where several observed products share the exact same operating coordinate.

## Existing evidence reused

P7 does not add manufacturer claims. It reuses the canonical B05 source-native operating points already stored in:

`data/processed/heat_pump_performance_points.csv`

The current evidence contains 33 OBS product operating points across Vaillant and STIEBEL ELTRON product families.

## Materialized cohort surface

P7 groups complete OBS capacity/input/COP triples only at identical:

`outdoor_temperature x supply_temperature`

coordinates.

The materialized output is:

`data/processed/b05_product_cohort_performance_envelope.csv`

Eight coordinates contain at least two observed equipment records.

Five coordinates have observations from both manufacturers and therefore receive:

`QUALIFIED_CROSS_MANUFACTURER_COHORT_ENVELOPE`

- A-7/W35
- A2/W35
- A7/W35
- A7/W45
- A7/W55

For these coordinates P7 materializes min/max:

- thermal capacity;
- total-unit electrical input;
- COP.

No simple average or centre estimate is produced.

## Cold-side calibration-only coordinates

Three exact coordinates remain single-manufacturer cohort evidence:

- A-15/W35;
- A-7/W45;
- A2/W45.

They remain:

`CALIBRATION_ONLY_SINGLE_MANUFACTURER_COHORT`

They cannot be promoted to cross-manufacturer national envelopes.

## Consequence for national modelling

The old implicit architecture:

`ONE REFERENCE PRODUCT MUST COVER THE WHOLE NATIONAL DOMAIN`

is not required.

The current national route is:

`MULTI-PRODUCT OBSERVED COMMON COORDINATES -> BOUNDED COHORT ENVELOPE -> PROGRAMME UNCERTAINTY PROPAGATION`

This does not imply market representativeness. Product counts are not market-share weights.

## Remaining product-domain gaps

P7 does not close:

- cold W45 cross-manufacturer coverage;
- continuous W55 cross-manufacturer coverage;
- below -15 C W35 if that extreme-weather domain remains in programme scope;
- defrost accounting;
- cycling/part-load degradation;
- DHW priority;
- return-temperature/delta-T sensitivity.

These remain separate gates.

## Product-specific boundary

Any claim that a particular heat pump can serve a particular building at a particular design point still requires that specific product's own source-supported performance map.

A cohort envelope cannot authorize a specific product.

## State

Q-B05-001 remains OPEN_NARROWED.

B05 module readiness remains 64%. P7 does not invent a percentage uplift from semantic improvement alone.
