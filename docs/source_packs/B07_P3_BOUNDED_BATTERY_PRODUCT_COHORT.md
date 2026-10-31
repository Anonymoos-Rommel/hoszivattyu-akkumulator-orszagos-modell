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

Both canonical products now have a materialized operating-temperature range. The stable product ID `SONNEN-BATTERY-10-PERFORMANCE` is bound to **10p/11**, the **May 2024** datasheet and performance module article **3000364**, not all configurations marketed under the family name.

Source `SRC-B07-SONNEN-10P11-DATASHEET-2024` gives **11 kWh nominal**, **10 kWh usable (OBS)** and **7/7 kW rated inverter charge/discharge power** for 10p/11, retained as the existing catalog AC power-cap values without claiming the source labels them maximum. The 9.9 kW figures of larger variants are not imported. `capacity_boundary=NOMINAL` continues to identify the nominal-capacity field; it does not relabel usable capacity or substitute it into the unchanged cohort nominal-capacity envelope.

The operating range is **−5..45 °C**; **5..35 °C** is a separate optimal range, recorded as a note rather than substituted for operating limits. Power reduction below 5 °C or above 35 °C is possible but unquantified. **No full-power guarantee across the operating range** is inferred. A validated temperature-dependent power/efficiency/aging response is still required; no derating curve is invented.

Maximum inverter efficiency in this datasheet is not product-specific one-way AC/grid or round-trip efficiency. All existing efficiency Q fields, lifecycle/degradation limits, PARTIAL status and readiness percentages remain unchanged. No runtime input, engine, schema, product choice or market-share inference is introduced.

The source gives only May 2024, not a publication day: `published_at=undated` preserves the existing exact-day schema without inventing precision; the month is retained in the title, reference period and notes. The exact source URL, retrieval date and SHA256 are recorded in `registry/sources.csv` and `registry/battery_sources.csv`; the original PDF is preserved in the authorized project archive, not copied into the repository (`EXTERNAL_ONLY`).

## State

B07 remains IN_PROGRESS.

Module readiness remains **58%**. No readiness uplift is minted from bounded cohort materialization alone.
