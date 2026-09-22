# B07-P3 — bounded household-battery product cohort

## Purpose

B07-P3 materializes the programme-level quantities that are semantically comparable across the existing canonical VARTA and sonnen product evidence.

Core boundaries:

`PRODUCT COHORT != PRODUCT-SPECIFIC RUNTIME`

`WARRANTY RETENTION != DEGRADATION LAW`

`MANUFACTURING LOCATION != CELL OR SUPPLY-CHAIN ORIGIN`

`BATTERY-ONLY EFFICIENCY != WHOLE-SYSTEM EFFICIENCY`

`MISSING PRODUCT FIELD != LICENSE TO IMPUTE`

## Materialized cohort

The canonical evidence currently contains two products from two manufacturers and two chemistries.

P3 materializes:

- nominal capacity: **6.5–11 kWh**
- maximum charge power: **2.5–7 kW**
- maximum discharge power: **2.3–7 kW**
- warranty term: **10 years**
- warranty cycle envelope: **4,000–10,000 cycles**
- warranty retention: **80%**

These are bounded programme/product-sensitivity inputs only. They are not market-share weighted and do not select a product for a specific dwelling.

## Lifecycle boundary

Both canonical products carry a 10-year / 80% retention warranty statement.

This supports a contractual lifecycle scenario bound.

It does **not** support:

- linear annual degradation;
- calendar-aging law;
- throughput-aging law;
- cycle-to-year conversion;
- interpolation between commissioning and warranty horizon.

Q-B07-004 therefore remains open for runtime aging.

## Efficiency boundary

The existing efficiency evidence remains semantically incompatible:

- VARTA: 97.8% battery-only efficiency;
- sonnen: 75–80% whole-system example.

P3 does not pool, average, square-root split or convert these into one-way AC/grid efficiencies.

Q-B07-003 remains open.

## Supply-chain boundary

Both products have German manufacturing/assembly evidence.

That does not establish:

- cell origin;
- inverter origin;
- upstream material origin;
- supply-chain concentration.

Q-B07-002 remains open for procurement/supply-chain claims, but the missing upstream origin does not block the physical SOC model.

## Temperature boundary

Only VARTA currently has a materialized operating-temperature range. P3 does not invent a second-product temperature envelope or a cohort derating curve.

## State

B07 remains IN_PROGRESS.

Module readiness remains **58%**. No readiness uplift is minted from bounded cohort materialization alone.
