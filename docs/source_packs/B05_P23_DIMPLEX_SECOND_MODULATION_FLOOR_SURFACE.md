# B05-P23 - Dimplex second-manufacturer modulation-floor surface

## Purpose

P22 left:

`SECOND_MANUFACTURER_MODULATION_FLOOR_SURFACE_REQUIRED`.

P23 resolves that residual with a second independent manufacturer while keeping
all source-native gaps fail-closed.

Exact product:

`Dimplex LA 2030CP`.

## Manufacturer minimum-output surface

The current Dimplex planning handbook technical page publishes a min/max
heating-output table.

P23 materializes exact minimum outputs:

| outdoor | W35 | W45 | W55 |
|---:|---:|---:|---:|
| -22 C | 8.0 | 8.0 | 7.8 |
| -15 C | 9.1 | 9.2 | 9.5 |
| -7 C | 8.8 | 8.4 | 9.5 |
| +2 C | 6.8 | 5.9 | 6.0 |
| +7 C | 9.8 | 7.1 | 7.5 |

All values are kW and remain OBS.

## A-10 source gap

The manufacturer table does not provide a usable minimum-output row at A-10
across the W35/W45/W55 surface used here.

This is not silently treated as:

- zero output;
- unsupported operation;
- equal to a neighbouring floor;
- permission to interpolate from A-15 to A-7.

P23 explicitly inserts A-10 as an interpolation barrier.

Therefore the source-native floor grid produces:

- 2 qualified cold cells over A-22..A-15;
- 4 qualified warm cells over A-7..A7;
- 0 cells crossing A-10.

Total: **6 complete bounded cells**.

## Why this still resolves the second-surface blocker

A second-manufacturer surface does not require every outdoor temperature to be
known. It requires a genuine two-dimensional source-native floor surface with
bounded interpolation semantics.

Dimplex provides that independently of Mitsubishi.

The project now has:

1. Mitsubishi PUZ-WM50VHA(-BS): broad 40-point / 27-cell piecewise surface;
2. Dimplex LA 2030CP: 15-point / 6-cell barrier-aware piecewise surface.

No value transfers between manufacturers.

## Current certification and Cdh

Current HP KEYMARK subtype:

- model: LA 2030CP;
- registration: 40060852;
- certification date: 29 August 2025;
- outdoor air/water;
- R290.

Average-climate low-temperature Cdh:

| Tj | Cdh |
|---:|---:|
| -7 C | 0.990 |
| +2 C | 0.970 |
| +7 C | 0.953 |
| +12 C | 0.912 |

All are non-default.

## Exact second-manufacturer cycling-ready bins

The Dimplex manufacturer min/max table also publishes COP in the **min** column
at W35 for:

| point | minimum capacity | minimum-point COP | Cdh |
|---|---:|---:|---:|
| A-7/W35 | 8.8 kW | 3.6 | 0.990 |
| A2/W35 | 6.8 kW | 4.7 | 0.970 |
| A7/W35 | 9.8 kW | 5.3 | 0.953 |

These three exact points independently reproduce the Mitsubishi P18-P22
cycling chain on a second manufacturer.

The +12 C HP KEYMARK Cdh remains Cdh-only because this P23 manufacturer surface
does not publish an A12/W35 minimum point.

## P9 stress limitation

Canonical P9 mean-stress envelope:

`-13.331944 .. -9.644444 C`.

This interval straddles the explicit A-10 source barrier.

Therefore P23 **does not** claim continuous Dimplex modulation-floor coverage
for the P9 stress envelope.

That is intentional.

## Residual transition

`SECOND_MANUFACTURER_MODULATION_FLOOR_SURFACE_REQUIRED`
->
`RESOLVED_FOR_DIMPLEX_LA2030CP_PIECEWISE_SURFACE`.

Q-B05-004 becomes:

`OPEN_NARROWED_TO_DOMAIN_GAPS_AND_CDH_MAPPING`.

Remaining residuals:

1. `MITSUBISHI_COLD_HIGH_SUPPLY_DOMAIN_CLASSIFICATION_REQUIRED`;
2. `DIMPLEX_A_MINUS10_MINIMUM_ROW_CLASSIFICATION_REQUIRED`;
3. `CDH_HOURLY_TEMPERATURE_MAPPING_REQUIRED`.

## Readiness

PART_LOAD_MODULATION remains **45%**.

B05 remains **64%**.

No readiness uplift is minted. Two manufacturer surfaces now exist, but the
remaining domain gaps and continuous-hour Cdh mapping are directly relevant to
the national hourly model.

## Sources

Dimplex LA 2030CP manufacturer planning handbook page:
https://dimplex.atlassian.net/wiki/spaces/PRO/pages/3902636350/Technische+Produktinformationen+LA+2030CP

Current Heat Pump KEYMARK subtype:
https://www.heatpumpkeymark.com/en/?cHash=345ece1d2c6cfa3f7606958b884b4b37&tx_pskeymark_frontend%5Baction%5D=showSubtype&tx_pskeymark_frontend%5Bcontroller%5D=Frontend&tx_pskeymark_frontend%5Bsubtype%5D=6778&type=109126
