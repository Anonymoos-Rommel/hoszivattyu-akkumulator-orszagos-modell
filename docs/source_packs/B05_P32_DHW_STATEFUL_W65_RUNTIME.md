# B05-P32 — STATEFUL DHW RUNTIME + EXACT W65 PERFORMANCE

Date: 2026-09-25  
Canonical base: `a8c8d839ecd81dc6d15994b5de1facde6092088d`

## Purpose

P29 established controller-bound DHW dispatch but intentionally left two
residuals:

- `STATEFUL_DHW_CONTROLLER_RUNTIME_REQUIRED`;
- `DHW_HIGH_TEMP_PRODUCT_PERFORMANCE_REQUIRED`.

P32 resolves both in **bounded exact Dimplex scope** for:

`LA 2030CP + WPM Touch`.

It does not create a generic DHW policy.

## Core boundary

```
CONTROLLER STATE
+
EXACT PRODUCT PERFORMANCE
=
BOUNDED RUNTIME-READY PERFORMANCE POINT
```

but:

```
OPERATING LIMIT != PERFORMANCE POINT
```

and:

```
SOURCE GRAPH != DIGITIZED NUMERIC GRID
```

## 1. Stateful WPM Touch DHW request

The WPM Touch manual states that:

- the DHW set temperature is configurable;
- the controller calculates the current maximum DHW temperature attainable by
  heat-pump operation ("HP maximum") from the current heat-source temperature;
- if the requested set temperature exceeds that HP maximum, heat-pump DHW
  preparation terminates when HP maximum is reached;
- if flange-heater reheating is enabled, heat above HP maximum is supplied by
  the auxiliary heater;
- DHW hysteresis defines the request threshold below the set temperature;
- a request is recognised below target minus hysteresis and remains pending
  through the hysteresis band until the target is reached;
- when a DHW request occurs during heating, WPM Touch switches circulation from
  space heating to DHW.

P32 therefore requires the **current controller HP-maximum value** as runtime
state.  It does not invent the source-temperature -> HP-maximum function.

The executable state rule uses:

```
effective HP target = min(DHW setpoint, current HP maximum)
request-on threshold = effective target - hysteresis
```

A prior active request remains active inside the deadband until the effective
target is reached.

Source:
`SRC-B05-DIMPLEX-WPMTOUCH-DHW-CONTROL-2026`.

## 2. Exact LA 2030CP W65 performance

The current Dimplex System C planning manual, Version 03/2026, technical
product information for LA 2030CP section 3.10.4 publishes an exact
**Heating water outlet W65** table.

The table contains source-native:

- Qh minimum;
- Qh maximum;
- Pel minimum;
- Pel maximum;
- COP at Qh minimum;
- COP at Qh maximum.

Exact admitted outdoor temperatures are:

```
-15, -10, -7, 2, 7, 12, 20, 30, 40 C
```

The A-22/W65 row is blank and stays Q.

P32 materialises 18 observations:

```
9 exact outdoor temperatures x MIN/MAX
```

in:

`data/processed/b05_p32_dimplex_w65_performance.csv`.

The numeric source is the exact table, **not** visual digitisation of the
separate W65 heating-curve graph.

Source:
`SRC-B05-DIMPLEX-LA2030CP-W65-PERFORMANCE-2026`.

## 3. Exact W65 values

| outdoor C | level | Qh kW | Pel kW | COP |
|---:|---|---:|---:|---:|
| -15 | MIN | 8.72 | 5.77 | 1.51 |
| -15 | MAX | 17.60 | 12.39 | 1.42 |
| -10 | MIN | 8.32 | 4.80 | 1.73 |
| -10 | MAX | 20.05 | 12.43 | 1.61 |
| -7 | MIN | 7.84 | 4.30 | 1.82 |
| -7 | MAX | 21.60 | 12.36 | 1.75 |
| 2 | MIN | 5.70 | 2.69 | 2.12 |
| 2 | MAX | 17.37 | 8.19 | 2.12 |
| 7 | MIN | 6.41 | 2.60 | 2.47 |
| 7 | MAX | 16.75 | 6.54 | 2.56 |
| 12 | MIN | 7.18 | 2.58 | 2.78 |
| 12 | MAX | 18.65 | 6.53 | 2.86 |
| 20 | MIN | 8.41 | 2.60 | 3.23 |
| 20 | MAX | 20.58 | 6.55 | 3.14 |
| 30 | MIN | 10.47 | 2.56 | 4.09 |
| 30 | MAX | 24.95 | 6.48 | 3.85 |
| 40 | MIN | 12.79 | 2.49 | 5.14 |
| 40 | MAX | 29.57 | 6.37 | 4.64 |

No interpolation is introduced in P32.

## 4. Runtime admission

`modules/B05/dhw_stateful_high_temp.py` joins:

1. the Dimplex stateful DHW request;
2. the P29 exact dispatch policy;
3. the P32 exact W65 performance point.

A unique high-temperature point is returned only when:

- DHW request is active;
- effective heat-pump target is exactly 65 C;
- outdoor temperature exactly matches one source-table row;
- runtime performance level is explicitly MIN or MAX.

Otherwise the runtime fails closed.

## 5. Auxiliary reheating

If:

```
DHW setpoint > HP maximum
```

and flange-heater reheating is enabled, P32 separates the heat-pump segment
from auxiliary reheating.

The W65 heat-pump COP is never applied to resistance-heater energy.

## 6. What remains open

P32 does not infer the inverter operating level from demand.

Residual:

`DIMPLEX_W65_RUNTIME_PERFORMANCE_LEVEL_REQUIRED`.

Performance outside the exact W65 grid also remains Q:

`DHW_HIGH_TEMP_PERFORMANCE_OUTSIDE_DIMPLEX_W65_EXACT_GRID_REQUIRED`.

Mitsubishi controller state and current high-temperature performance remain a
separate product-specific residual:

`MITSUBISHI_STATEFUL_DISPATCH_AND_CURRENT_HIGH_TEMP_PERFORMANCE_REQUIRED`.

## 7. Q-B05-005 transition

```
OPEN_NARROWED_TO_STATEFUL_CONTROLLER_RUNTIME_AND_DHW_HIGH_TEMP_PERFORMANCE
->
OPEN_NARROWED_TO_RUNTIME_LEVEL_AND_CROSS_PRODUCT_COVERAGE
```

Bounded transitions:

```
STATEFUL_DHW_CONTROLLER_RUNTIME_REQUIRED
->
RESOLVED_FOR_DIMPLEX_WPM_TOUCH_HYSTERESIS_STATE
```

and:

```
DHW_HIGH_TEMP_PRODUCT_PERFORMANCE_REQUIRED
->
RESOLVED_FOR_DIMPLEX_W65_EXACT_SOURCE_GRID
```

## 8. Readiness

- DHW_MODE: 45% -> 60%
- B05 overall: 64% -> 64%

The uplift is based on a source-bound executable controller-state +
high-temperature-performance chain, not on a generic policy assumption.

## Sources

WPM Touch operating instructions:
https://www.dimplex.eu/sites/g/files/emiian586/files/media_import/medias/docus/15/Dimplex_WPMTouch_Bedienungsanleitung_fd0302_en.pdf

System C planning manual v03/2026:
https://www.dimplex.eu/sites/g/files/emiian586/files/2026-05/Projektierungshandbuch%20System%20C%C2%AE-v15-20260319_150009__EN_V2_final.pdf

Current LA2030CP installation manual (separate W65 graph and 70 C operating
envelope; numeric P32 data are **not** digitised from this graph):
https://www.dimplex.eu/sites/g/files/emiian586/files/2026-05/Dimplex_LA2030CP_Montageanweisung_FD0605_en.pdf
