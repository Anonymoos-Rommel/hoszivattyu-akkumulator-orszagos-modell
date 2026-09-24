# B05-P12 - EC POWER cross-manufacturer cold high-supply physical surface

## Purpose

B05-P12 resolves the P11 cross-manufacturer cold high-supply surface residual
for the P9 reference cold-stress domain without creating a market-share,
procurement or Hungary-sales claim.

Core boundaries:

`SOURCE-NATIVE CAPACITY + SOURCE-NATIVE COP -> ELECTRICAL INPUT DER`

`DER COMPLETION != SOURCE-NATIVE ELECTRICAL INPUT OBS`

`TWO-MANUFACTURER PHYSICAL SURFACE != HUNGARIAN MARKET REPRESENTATIVENESS`

`COMMON DOMAIN != COMMON PRODUCT SIZE`

`OPERATING RANGE != PERFORMANCE POINT`

`TUV-REFERENCED MANUFACTURER TABLE != SEPARATE DEFROST ACCOUNTING`

P12 does not average unlike product sizes and does not infer market weights.

## 1. EC POWER authority

The current EC POWER download surface continues to list:

`Technical Data Heat Pump PMH 6/19`.

The manufacturer technical data sheet identifies the supplier and product
models PMH 6 and PMH 19 and cites:

- TÜV-Süd Report 64.181.22.01854.01 Rev.00;
- TÜV-Süd Report 64.181.22.01853.01.

The same sheet publishes cold heating capacity and COP at:

- A-15/W35;
- A-7/W35;
- A-15/W55;
- A-7/W55.

It also states a heating operating range of -25 C to +50 C and maximum heating
water temperature of 58 C. Those limits are operating-envelope controls only.

## 2. Source-native EC POWER cold points

### PMH 6

| Coordinate | Capacity kW | COP | Electrical input |
|---|---:|---:|---|
| A-15/W35 | 3.56 | 2.42 | DER = capacity/COP |
| A-7/W35 | 4.75 | 3.04 | DER = capacity/COP |
| A-15/W55 | 2.82 | 1.37 | DER = capacity/COP |
| A-7/W55 | 3.69 | 1.77 | DER = capacity/COP |

### PMH 19

| Coordinate | Capacity kW | COP | Electrical input |
|---|---:|---:|---|
| A-15/W35 | 9.73 | 2.62 | DER = capacity/COP |
| A-7/W35 | 12.57 | 3.19 | DER = capacity/COP |
| A-15/W55 | 8.50 | 1.64 | DER = capacity/COP |
| A-7/W55 | 10.68 | 1.96 | DER = capacity/COP |

The canonical point CSV intentionally leaves the EC POWER electrical-input
field blank. B05 already requires at least two of capacity / electrical input /
COP and deterministically completes the third quantity.

Therefore:

- source-native capacity = OBS;
- source-native COP = OBS;
- completed electrical input = DER;
- exact evaluated operating triple = DER because one metric is derived.

No input value is promoted to OBS.

## 3. Cross-manufacturer physical cohort

P11 already qualified two Tekno Point ATHENA R32 maps over:

`outdoor -15..-7 C x supply 35..55 C`

using source-native capacity + published power input + COP corners.

P12 adds two EC POWER PMH maps over the same domain using source-native
capacity + COP and deterministic DER input completion.

The cross-manufacturer cohort therefore contains at least:

- Tekno Point ATHENA R32 A-0732;
- Tekno Point ATHENA R32 A-0932;
- EC POWER PMH 6;
- EC POWER PMH 19.

P12 qualifies **surface availability**, not a raw cross-size capacity average.
Different nominal product sizes remain separate equipment maps.

## 4. P9 stress consequence

The P9 project-derived empirical 10-year coldest-72h-mean stress envelope is:

`-13.331944 .. -9.644444 C`.

That full interval lies inside both manufacturers' admitted:

`-15 .. -7 C`

outdoor domain.

The reference-programme W35/W45/W55 supply anchors all lie inside:

`35 .. 55 C`.

For each admitted product the existing B05 bounded bilinear engine therefore
evaluates the P9 stress endpoints and W35/W45/W55 without extrapolation.

Tekno Point exact corners are complete OBS triples.

EC POWER exact corners are DER-completed triples because electrical input is
not source-native in the admitted table.

All interior stress/W45 values are DER.

## 5. Effect on the P11 residual

P11 residual:

`SECOND_MANUFACTURER_COLD_W45_W55_COMPLETE_SURFACE_REQUIRED_FOR_CROSS_MANUFACTURER_COHORT`

is resolved for programme physical uncertainty propagation.

This means the P9 reference cold-stress high-supply physical domain is no
longer single-manufacturer dependent.

This does **not** establish:

- Hungarian sales/distribution;
- Hungarian installed-stock share;
- procurement availability;
- manufacturer market share;
- a representative national product mix.

Those are separate market/procurement questions and are forbidden uses of P12.

## 6. Remaining conditional extreme-domain gap

P12 does not close:

`BELOW_MINUS15_W35_REQUIRED_IF_HOURLY_EXTREME_EVENT_SIMULATION_IS_IN_SCOPE`.

The EC POWER sheet gives an operating range down to -25 C, but an operating
range is not a performance point. P12 therefore does not extrapolate its
-15 C performance to -21.9 C or -25 C.

Q-B05-001 becomes `OPEN_CONDITIONAL`: the P9 reference stress surface is
resolved cross-manufacturer, while below--15 performance remains required only
if the separate hourly-extreme runtime remains in programme scope.

## 7. Independent blockers

P12 does not close:

- Q-B05-003 defrost accounting;
- Q-B05-004 modulation/cycling/part-load degradation;
- Q-B05-005 DHW priority;
- product market-share weighting.

The EC POWER product description mentions automatic self-learning defrost, but
no separable point-level defrost energy series or accounting boundary is
admitted here.

## 8. Readiness

B05 module readiness remains **64%**.

No percentage uplift is minted. P12 removes a material physical evidence
dependency, but independent runtime and national weighting gates remain.

## Sources

### SRC-B05-ECPOWER-PMH-2023

EC POWER, Technical Data PMH 6 / PMH 19, version 03.2023.

Manufacturer PDF:
https://www.ecpower.eu/files/ec-power/customer/EN/Downloads_EN/Information_Material/EC_POWER_EN_technical_data_PMH.pdf

Role:

- source-native cold capacity and COP;
- source model identity;
- operating limits;
- TÜV-Süd report references.

The PDF is referenced only and is not stored in the repository.

### SRC-B05-ECPOWER-PMH-CURRENT-2026

EC POWER current downloads/product surface:
https://www.ecpower.eu/en/downloads.html
https://www.ecpower.eu/en/product-range2.html

Role:

- confirms PMH heat pump remains on the current manufacturer public surface;
- does not prove Hungarian procurement or market presence.
