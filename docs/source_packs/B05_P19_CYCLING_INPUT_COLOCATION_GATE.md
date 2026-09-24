# B05-P19 - cycling input co-location gate

## Purpose

P18 left:

`MINIMUM_CAPACITY_COP_INPUT_REQUIRED`

and

`MODULATION_FLOOR_SURFACE_OR_INTERPOLATION_CONTRACT_REQUIRED`.

P19 asks a narrower question: is minimum-capacity COP absent from public product
evidence altogether, or are the required fields available but not explicitly
paired at the same operating point?

## Existing qualified products

### Vaillant VWL 85/6 A 230V S3

A7/W35:
- exact minimum modulation = 3.00 kW;
- certified non-default Cdh(+7) = 0.950;
- certified COP 6.33 belongs to Pdh 3.21 kW, not 3.00 kW.

Result:

`Q / POINT_PAIRED_MINIMUM_CAPACITY_COP_REQUIRED`.

### Bosch CS5800iAW 4 ORE-S

A2/W35:
- exact minimum modulation = 1.80 kW;
- certified non-default Cdh(+2) = 0.990;
- certified COP 3.21 belongs to Pdh 4.31 kW, not 1.80 kW.

Result:

`Q / POINT_PAIRED_MINIMUM_CAPACITY_COP_REQUIRED`.

## Third exact certified product discovery

Current public distributor technical data for:

`PAVH-06V1FXC`

publish at A7/W35:

- heating capacity min/max: 3.4..6.5 kW;
- electrical heating input min/max: 0.74..1.5 kW;
- COP min/max: 4.26..4.6.

This proves that all three field families can be published together for one
exact product and one operating condition.

It does **not** prove that:

`3.4 kW <-> 0.74 kW <-> COP 4.6`

or any other endpoint combination is an explicitly measured point.

Therefore:

`RANGE CO-PUBLICATION != POINT PAIRING`

and B05 does not divide range endpoints to manufacture COPd.

The evidence source is also distributor-tier, so it is discovery evidence and
not promoted into a canonical manufacturer modulation surface.

## Amitime current certification control

The current HP KEYMARK subtype identifies exact model PAVH-06V1FXC under
registration 041-K027-01/01, BRE certification and TÜV SÜD Guangzhou testing.

Its EN14825 average-climate Cdh fields are exactly 0.900 across low/medium
temperature bins.

P15 already established:

`PUBLISHED 0.900 != PROVEN MEASUREMENT-DETERMINED CDH`

because 0.900 is also the standard fallback when Cdh is not determined by
measurement.

So Amitime does not solve the runtime co-location gate either.

## Executable gate

P19 requires, on the same product and operating coordinate:

1. exact modulation floor;
2. explicit point-paired COPd at that minimum/cycling capacity;
3. qualified measurement-determined product Cdh.

Cross-product assembly is forbidden.

Range endpoint division is forbidden unless the source explicitly states that
the capacity and input endpoints form the same operating point.

## Residual transition

`MINIMUM_CAPACITY_COP_INPUT_REQUIRED`

becomes:

`NARROWED_TO_POINT_PAIRED_MINIMUM_CAPACITY_COP_REQUIRED`.

Q-B05-004 becomes:

`OPEN_NARROWED_TO_MODULATION_SURFACE_AND_POINT_PAIRED_MIN_CAPACITY_COP`.

Residuals:

- `MODULATION_FLOOR_SURFACE_OR_INTERPOLATION_CONTRACT_REQUIRED`;
- `POINT_PAIRED_MINIMUM_CAPACITY_COP_REQUIRED`.

## Readiness

PART_LOAD_MODULATION remains **45%**.

B05 remains **64%**.

No uplift is minted because P19 improves the exact blocker definition but does
not yet create a product-ready cycling runtime point.

## Sources

Hemeltron current AMITIME heatLITE technical page:
https://en.hemeltron.ee/amitime-heatlite

Heat Pump KEYMARK current Amitime subtype:
https://www.heatpumpkeymark.com/en/nc/ps-keymark/certificate-holders/?cHash=828ac1e95e4348d03bdfd53fa712afe2&tx_pskeymark_frontend%5Baction%5D=showSubtype&tx_pskeymark_frontend%5Bcontroller%5D=Frontend&tx_pskeymark_frontend%5Bsubtype%5D=3221
