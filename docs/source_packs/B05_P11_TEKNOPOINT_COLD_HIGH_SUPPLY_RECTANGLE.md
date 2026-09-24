# B05-P11 — Tekno Point ATHENA R32 cold high-supply complete performance rectangle

## Purpose

B05-P11 narrows Q-B05-001 by adding a current manufacturer product family with
source-native cold heating points that provide all three operating quantities:

- thermal capacity;
- published electrical power input;
- COP.

For two ATHENA R32 product sizes, the manufacturer table exposes the four exact
corners needed for the B05 rectangular interpolation contract:

- A-15/W35;
- A-15/W55;
- A-7/W35;
- A-7/W55.

Core boundaries:

`SOURCE-NATIVE CORNERS -> BOUNDED BILINEAR DERIVATION`

`W45 DERIVATION INSIDE W35..W55 != SOURCE-NATIVE W45 OBSERVATION`

`PRODUCT-FAMILY PERFORMANCE SURFACE != NATIONAL MARKET SHARE`

`OPERATING LIMIT != PERFORMANCE POINT`

`PUBLISHED POWER INPUT != PROOF OF SEPARATE DEFROST ENERGY ACCOUNTING`

P11 does not extrapolate below -15 C, does not invent a market weight and does
not close the separate defrost or part-load/cycling questions.

## 1. Manufacturer authority

The Tekno Point 2025 hydronic-system catalogue identifies the ATHENA R32
air-to-water heat-pump family and publishes heating capacity, absorbed/power
input and COP at cold operating coordinates.

The current Tekno Point product surface continues to list ATHENA R32 and states
that the family produces heating water up to 55 C at outdoor temperature down
to -20 C.

The -20 C statement is treated only as an operating-limit/current-product
control. It is not converted into a performance point.

## 2. Canonical exact points

P11 materializes two source-native equipment maps.

### ATHENA R32 A-0732

| Coordinate | Capacity kW | Power input kW | COP |
|---|---:|---:|---:|
| A-15/W35 | 4.75 | 1.52 | 3.13 |
| A-15/W55 | 3.90 | 2.00 | 1.95 |
| A-7/W35 | 5.03 | 1.57 | 3.20 |
| A-7/W55 | 4.35 | 2.05 | 2.12 |

### ATHENA R32 A-0932

| Coordinate | Capacity kW | Power input kW | COP |
|---|---:|---:|---:|
| A-15/W35 | 6.30 | 1.93 | 3.26 |
| A-15/W55 | 4.98 | 2.50 | 1.99 |
| A-7/W35 | 6.53 | 1.98 | 3.30 |
| A-7/W55 | 5.58 | 2.58 | 2.16 |

The published triples are internally consistent within the existing B05
manufacturer-rounding tolerance.

The repository maps the manufacturer field `P assorb. / Power` to the B05
`total_unit_input` product-unit boundary. This means the published heat-pump
unit electrical input used in the source performance table. P11 does not infer
external system electricity, backup-heater electricity or a separable defrost
energy term from that field.

## 3. P9 stress-domain consequence

P9 materialized:

`-13.331944 .. -9.644444 C`

as the five-station project-derived empirical 10-year coldest-72h-mean stress
envelope.

That entire interval lies inside the P11 source-native outdoor-temperature
rectangle:

`-15 .. -7 C`.

The reference-programme supply-temperature set remains bounded to <=55 C.
W45 lies inside the source-native supply rectangle:

`35 .. 55 C`.

Therefore, for the two admitted Tekno Point equipment maps, B05 can evaluate:

- W35 across the full P9 stress interval;
- W45 across the full P9 stress interval;
- W55 across the full P9 stress interval;

with the existing deterministic bounded bilinear interpolation and without
out-of-domain extrapolation.

Exact manufacturer coordinates remain OBS. Interpolated W45/stress-coordinate
values are DER.

## 4. Effect on P10 residuals

For a bounded current product-family surface P11 resolves:

- `SECOND_MANUFACTURER_COLD_W35_COMPLETE_TRIPLE_REQUIRED`;
- `COLD_W45_TOTAL_INPUT_COP_SURFACE_REQUIRED`;
- `COLD_W55_TOTAL_INPUT_COP_SURFACE_REQUIRED`.

This does not create a cross-manufacturer cold W45/W55 cohort envelope. The
new narrower cohort residual is:

`SECOND_MANUFACTURER_COLD_W45_W55_COMPLETE_SURFACE_REQUIRED_FOR_CROSS_MANUFACTURER_COHORT`.

The conditional hourly-extreme residual remains:

`BELOW_MINUS15_W35_REQUIRED_IF_HOURLY_EXTREME_EVENT_SIMULATION_IS_IN_SCOPE`.

The source states operation down to -20 C, but P11 has no complete performance
rectangle below -15 C, so the engine must still fail closed there.

## 5. Independent runtime blockers

P11 does not close:

- Q-B05-003 defrost accounting;
- Q-B05-004 modulation/cycling/part-load degradation;
- Q-B05-005 DHW priority;
- national market-share or procurement weighting.

The performance table does not establish a separable point-level defrost energy
series, so no hidden defrost penalty is applied.

## 6. Readiness

B05 module readiness remains **64%**.

P11 materially strengthens the cold performance surface but does not mint an
overall readiness uplift because independent runtime and national weighting
questions remain.

Component percentages are intentionally unchanged. Their notes are updated to
record the stronger evidence.

## Sources

### SRC-B05-TEKNOPOINT-ATHENA-R32-2025

Tekno Point hydronic-system catalogue, manufacturer-hosted PDF:

https://teknopoint.com/pdf/catalogo_sistema_idronico_ITA_EN_2025.pdf

Role: source-native ATHENA R32 cold capacity / power-input / COP triples.

### SRC-B05-TEKNOPOINT-ATHENA-R32-CURRENT-2026

Current Tekno Point ATHENA R32 product page:

https://teknopoint.com/fr/pompes-a-chaleur/athena-r32

Role: current-product and operating-limit control only; not a substitute for
the source-native performance table.
