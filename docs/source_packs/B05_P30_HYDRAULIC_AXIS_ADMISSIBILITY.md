# B05-P30 — HYDRAULIC PERFORMANCE-AXIS ADMISSIBILITY

Date: 2026-09-25  
Canonical base: `3581ca5c0d04ba022e96fabc4007e1adfea8f66c`

## Purpose

Q-B05-006 asks when return temperature or water-side delta-T may be used as a
physical dimension of the heat-pump performance surface.

P30 resolves the question as an evidence-admission contract rather than
inventing a new numeric axis.

## Core rule

```
FIXED TEST CONDITION / SENSOR / OPERATING LIMIT
!=
PERFORMANCE SENSITIVITY AXIS
```

For the current B05 supply-based performance surface:

```
delta-T = supply temperature - return temperature
```

Therefore, with supply retained, return and delta-T are alternative hydraulic
representations of the same remaining degree of freedom.  They must not be
counted as two independent additional axes.

## Current canonical snapshot

The canonical `heat_pump_performance_points.csv` at P30 contains:

- 59 rows total;
- 6 synthetic TEST-AWHP fixture rows;
- 53 real OBS/DER product rows;
- 11 distinct real equipment IDs;
- 0 populated source-native `return_temperature_C` values;
- 0 populated source-native `delta_temperature_C` values.

Therefore the current executable V1 remains:

```
outdoor temperature x supply temperature
```

No return/delta interpolation is authorized.

The snapshot is materialized in:

`data/processed/b05_p30_hydraulic_axis_snapshot.csv`

## Dimplex source-native interpretation

Current LA 2030CP manufacturer instructions provide several hydraulic facts:

- heating-water flow / return operating limits: flow up to 70 C, return from
  18 C;
- nominal EN14511 condition: `A7 / W35...30`;
- nominal heating-water flow: 2.0 m3/h;
- an installed secondary-circuit return-temperature sensor;
- heating curves published at stated water outlet temperatures and fixed
  water-flow conditions.

The exact notation `W35...30` is useful metadata: it binds a nominal test point
to outlet 35 C and return/inlet 30 C.  It does not independently vary return at
the same A7/W35 coordinate, so it cannot prove a return-temperature performance
sensitivity surface.

Likewise, a return sensor proves observability/control, not a capacity/COP
dimension.

Source:
`SRC-B05-DIMPLEX-LA2030CP-HYDRAULIC-TEST-CONDITIONS-2026`

## Mitsubishi cross-manufacturer control

Current Mitsubishi product information for PUZ-WM50VHA publishes a nominal
water flow and identifies flow/return water-temperature thermistors in system
configurations.

This independently supports the same boundary:

```
FLOW / RETURN INSTRUMENTATION
!=
RETURN-TEMPERATURE PERFORMANCE SURFACE
```

Source:
`SRC-B05-MITSUBISHI-WM50-FLOW-RETURN-INSTRUMENTATION-2026`

## Admission gate

A return-temperature axis may be admitted only when all of the following hold:

1. exact same equipment/model identity;
2. exact matching electrical-input/unit boundary;
3. explicit source-native return-temperature observations;
4. at least one matched outdoor + supply coordinate has two or more distinct
   return temperatures;
5. each such point carries admissible capacity/input/COP evidence;
6. no cross-product pooling is used to manufacture the variation.

The delta-T gate is identical except that explicit source-native delta-T is the
candidate coordinate.

A delta-T merely calculated from one supply/return pair may be stored for audit,
but it does not prove performance sensitivity.

## Executable consequence

`modules/B05/hydraulic_axis_admissibility.py` implements the gate.

It distinguishes:
- no source-native axis values;
- fixed/test/control metadata only;
- mixed-product or mixed-boundary evidence;
- inconsistent supply/return/delta coordinates;
- genuinely varied source-native hydraulic performance axes.

## Q-B05-006 closure

```
OPEN
->
RESOLVED_CONTRACT
```

This closure does **not** claim that a return/delta performance surface exists
today.  It resolves when one would be admissible.

## Readiness

- PERFORMANCE_MAP: 80% -> 80%
- B05 overall: 64% -> 64%

No readiness uplift is minted because P30 adds no new numeric physical
performance surface.
