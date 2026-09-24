# B05-P17 - exact same-product minimum-modulation anchors

## Purpose

B05-P17 attacks `MULTI_PRODUCT_MIN_MODULATION_COVERAGE_REQUIRED` without manufacturing a complete modulation surface.

Core boundaries:

`SAME MANUFACTURER FAMILY != SAME PRODUCT`

`PDH != MINIMUM MODULATION`

`ONE MODULATION ANCHOR != MODULATION SURFACE`

`EXACT ANCHOR != INTERPOLATION AUTHORITY`

`CYCLING STATE != NUMERIC CYCLING ENERGY CORRECTION`

P17 does not change the B05 engine energy formula.

## Vaillant exact anchor

Exact model: `VWL 85/6 A 230V S3`.

Manufacturer technical data publish A7/W35 heat output minimum/maximum **3.00..9.00 kW**. P15 already materialized the same exact product's average-climate low-temperature +7 C EN14825 row: Pdh 3.21 kW, COP 6.33, Cdh 0.950.

Qualified bounded join:

`VWL 85/6 A 230V S3 + A7/W35 + min 3.00 kW + certified Cdh(+7)`.

## Bosch exact anchor

Exact model: `CS5800iAW 4 ORE-S`.

Bosch planning data state compressor output adapts by modulation and publish A2/W35 modulation range **1.8..4.3 kW**. The current HP KEYMARK subtype separately lists the exact non-`(60°C)` model; warmer-climate low-temperature +2 C publishes Pdh 4.31 kW, COP 3.21, Cdh 0.990.

Qualified bounded join:

`CS5800iAW 4 ORE-S + A2/W35 + min 1.8 kW + certified Cdh(+2)`.

No silent equivalence to the `(60°C)` model variant is needed.

## Residual effect

`MULTI_PRODUCT_MIN_MODULATION_COVERAGE_REQUIRED`
->
`RESOLVED_FOR_TWO_SAME_PRODUCT_ANCHORS`.

This is bounded-anchor coverage only. It does not authorize a modulation floor at arbitrary temperatures.

The exact-anchor resolver requires exact model + outdoor temperature + supply temperature. Missing coordinates return:

`Q / MODULATION_FLOOR_ANCHOR_NOT_QUALIFIED`

with:

`MODULATION_FLOOR_SURFACE_OR_INTERPOLATION_CONTRACT_REQUIRED`.

No nearest-neighbour, interpolation or extrapolation is performed.

## Q-B05-004 after P17

`OPEN_NARROWED_TO_MODULATION_SURFACE_AND_NUMERIC_CYCLING_METHOD`

Residuals:

- `MODULATION_FLOOR_SURFACE_OR_INTERPOLATION_CONTRACT_REQUIRED`
- `CYCLING_DEGRADATION_NUMERIC_METHOD_AUTHORITY_REQUIRED`

B05 remains **64%**.

PART_LOAD_MODULATION remains **45%**.

## Sources

Vaillant manufacturer manual:
https://www.vaillant.pt/downloads/installation-manuals/bombas-de-calor/0020297937-02-2406576.pdf

Bosch Home Comfort technical planning document:
https://www.bosch-homecomfort.com/be/media/country_pool/knowledge/system_pointers/fr_2/pd_cs5800iaw_4_ore-s_fr.pdf

Certified Cdh/part-load identity remains bound to the existing HP KEYMARK Vaillant and Bosch sources. No source authorizes direct hourly `COP x Cdh`.
