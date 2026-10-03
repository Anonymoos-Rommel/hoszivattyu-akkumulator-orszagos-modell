# B05-P22 - extended Mitsubishi minimum-point grid

## Current-use qualification — 2026-10-02

The original account below is retained as historical claim lineage. Its WM50
exact cycling-ready co-location conclusion is superseded for current use by
`registry/b05_cycling_source_admission_manifest.json` and
`docs/checkpoints/V1_035_CYCLING_SOURCE_ADMISSION.md` .

The presently readable standalone KEYMARK `PUZ-WM50VHA(-BS)`, Units Outdoor,
registration `037-0032-20 / rev.2`, certification date `19.12.2023`, reports
warmer +7 C Cdh low/medium **0.980/0.980** and average **0.950/0.960**. The prior
P20 warmer 0.950 attribution lacks current corroboration. Original September 24
bytes were not retained; historical cause is unresolved. No old transcription
error or publisher revision is asserted.

The source-native manufacturer minimum Q/input/COP pairs remain qualified at
their fixed water coordinates. Published Cdh remains an observation at its own
climate/application/bin scope. CALCM:01 issue 1.2 Appendix D / Table D1 (page 62)
distinguishes fixed and variable test-water branches; an application label does
not identify the selected branch. P20/P22 exact fixed-W35 joining therefore
remains Q pending source-bound test conditions or a named permissible transfer
rule. Neither branch is assumed for WM50. Swapping 0.950 for 0.980 cannot close
this gap.

P18 arithmetic remains valid conditionally. `evaluate_conditional_cycling_point`
returns `CONDITIONAL_STANDARD_METHOD_CALCULATION`; the existing source-qualified
entry point returns Q and null COP/input while authority is absent. No actual
hourly electricity/SPF or national policy follows. Manufacturer grids,
interpolation and independent evidence gates are unchanged. The original P59
eight-point exact execution gate is now unresolved for both product families;
current total readiness is Q/null with 67 supported points and 8 unresolved
weight. Historical 75 and independent B05 module 64 remain explicit.


## Purpose

P21 established the first bounded PUZ-WM50VHA modulation-floor rectangle.
P22 replaces that narrow current evidence surface with the manufacturer Data
Book's explicit **Min** performance table for the same current-certified base
model:

`PUZ-WM50VHA(-BS)`.

P22 also retains the minimum-point COP paired with every materialized minimum
capacity. This matters because P18 requires COP at the cycling/minimum capacity,
not nominal COP.

## 1. Official Data Book authority

Mitsubishi Electric Data Book Vol.5.3 publishes separate Max, Nominal, Mid and
Min heating-performance tables for PUZ-WM50VHA(-BS).

The Min table provides source-native:

- minimum heating capacity;
- COP at that same Min operating point;
- outdoor temperature;
- water outlet temperature.

P22 materializes 40 exact capacity/COP pairs.

The official PDF is large enough that the browser PDF renderer cannot reliably
render its pages, but the Mitsubishi document library search index exposes the
full table structure and exact fields. No graph is digitized.

## 2. Piecewise source-native domain

### Core complete grid

Outdoor nodes:

`-10, -7, 2, 7, 12, 15, 20 C`

Supply nodes:

`35, 40, 45, 50, 55 C`

Every combination is source-native.

This produces:

`6 outdoor intervals x 4 supply intervals = 24 complete cells`.

Qualified bounded core:

`A-10..A20 x W35..W55`.

### Cold shoulder

At A-15 the Data Book publishes Min values at:

- W35;
- W40;
- W45.

Together with A-10 this adds two complete cells:

`A-15..A-10 x W35..W45`.

### Extreme shoulder

At A-20 the Min table publishes:

- W35;
- W40.

Together with A-15 this adds one complete cell:

`A-20..A-15 x W35..W40`.

Total:

- 40 exact OBS points;
- 27 complete bounded cells.

Blank Data Book cells are not filled.

## 3. P21 consistency

The P21 rectangle is reproduced exactly by the Data Book:

| point | P21 | P22 Data Book |
|---|---:|---:|
| A2/W35 | 2.50 kW | 2.50 kW |
| A2/W45 | 2.50 kW | 2.50 kW |
| A7/W35 | 1.80 kW | 1.80 kW |
| A7/W45 | 1.30 kW | 1.30 kW |

P22 therefore supersedes the narrow P21 evidence surface for current use without
invalidating its historical result.

## 4. Minimum-point COP surface

Each P22 Data Book point keeps the source-native COP from the same **Min** row.

Exact point:

`minimum capacity + minimum-point COP = OBS`.

Inside a complete cell, the existing B05 project interpolation rule is applied
separately to minimum capacity and minimum-point COP:

`complete source-native rectangle -> bounded bilinear DER`.

The corresponding minimum-point electrical input is DER:

`minimum_capacity / minimum_COP`.

This is not nominal performance and is not a market-weighted product curve.

## 5. P9 stress consequence

Canonical P9 mean-stress envelope:

`-13.331944 .. -9.644444 C`.

### W35

Fully inside P22 complete cells.

Status:

`RESOLVED_FULL_ENVELOPE`.

### W45

Also fully inside the A-15..A-10 cold shoulder and the warmer core.

Status:

`RESOLVED_FULL_ENVELOPE`.

### W55

Source-native floor exists from A-10 upward, but the A-15/W55 Min cell is
blank.

Therefore only the warmer P9 segment is qualified.

The colder segment remains Q.

P22 does not decide whether a blank cold/high-supply Data Book cell means:

- unsupported operating combination; or
- unpublished minimum-performance point.

That requires explicit operating-domain classification.

## 6. Exact same-product Cdh bins

Mitsubishi's official ERP technical documentation for PUZ-WM50VHA(-BS),
low-temperature application, average climate, publishes:

| Tj | Cdh |
|---|---:|
| -7 C | 0.99 |
| +2 C | 0.98 |
| +7 C | 0.95 |
| +12 C | 0.93 |

The document explicitly states that 0.9 is the fallback only when Cdh was not
determined by measurement.

P22 joins these exact Tj bins to the Data Book's exact W35 Min capacity/COP
points for the same product.

Therefore four exact W35 bins are fully cycling-ready under the P18 method.

P22 does **not** interpolate Cdh between these temperatures and does not assign
the W35 Cdh set to W45/W55.

## 7. Q-B05-004 transition

Historical P21 residual:

`MODULATION_FLOOR_COVERAGE_OUTSIDE_MITSUBISHI_A2_A7_W35_W45_REQUIRED`

becomes:

`SUPERSEDED_BY_EXTENDED_DATABOOK_GRID`.

Current Q-B05-004:

`OPEN_NARROWED_TO_COLD_HIGH_SUPPLY_CDH_MAPPING_AND_SECOND_SURFACE`.

Residuals:

1. `MITSUBISHI_COLD_HIGH_SUPPLY_DOMAIN_CLASSIFICATION_REQUIRED`;
2. `CDH_HOURLY_TEMPERATURE_MAPPING_REQUIRED`;
3. `SECOND_MANUFACTURER_MODULATION_FLOOR_SURFACE_REQUIRED`.

## 8. Readiness

PART_LOAD_MODULATION remains **45%**.

B05 remains **64%**.

P22 is substantial evidence progress, but no readiness uplift is minted because:

- one manufacturer's broad surface is not a national product cohort;
- cold/high-supply blank cells remain unclassified;
- four exact Cdh bins do not yet define arbitrary-hour Cdh.

## Sources

Mitsubishi Electric Data Book Vol.5.3 R32:
https://library.mitsubishielectric.co.uk/pdf/download_full/4099

Mitsubishi Electric ERP technical documentation:
https://erp.mitsubishielectric.eu/files/library/files/erpdocs/lot1/wm050xx_001_001.pdf
