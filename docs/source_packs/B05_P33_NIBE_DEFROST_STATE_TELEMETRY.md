# B05-P33 — NIBE S2125 DEFROST STATE + TELEMETRY

Date: 2026-09-25  
Canonical base: `9002ed5cbcedefac2655998f56c983fc1d3c31d3`

## Purpose

P14 resolved the EN 14511 point-accounting boundary but left the actual
weather-driven runtime model open.

P33 asks a narrower physical question:

> Can a real product's defrost event state be identified without inventing a
> universal percentage penalty or an ambient-temperature/humidity trigger?

For the NIBE S2125 product family the answer is **yes, in bounded state scope**.

The answer remains **no** for event heat/electric energy and for a generic
ambient-weather-only frequency model.

## Core boundary

```
EXACT DEFROST STATE
!=
WEATHER-ONLY EVENT FREQUENCY
!=
EVENT HEAT / ELECTRIC ENERGY
```

P33 therefore adds state observability, not a kWh penalty.

## 1. Exact NIBE S2125 controller semantics

The official S2125 installer manual states that when evaporator sensor BT16 is
below the configured start temperature, S2125 counts time toward active
defrost for each minute the compressor is running, thereby creating a defrost
requirement.

The controller exposes **time until active defrost** in minutes, and defrost
starts when this value is zero.

P33 does **not** reconstruct the timer initialization/reset algorithm from
ambient weather.  The controller timer is an explicit runtime input or the
event is observed directly through telemetry.

Source:
`SRC-B05-NIBE-S2125-IHB`.

## 2. Active versus passive defrost

The same manufacturer manual states:

- passive defrost can start when compressor demand has been fulfilled;
- a defrost requirement must exist;
- BT28 outdoor temperature must be above the configured passive-defrost
  cut-out;
- factory default passive cut-out is 4 C, but the setting is configurable;
- active defrost operates with compressor on and fan off;
- passive defrost operates with compressor off and fan on.

Because the cut-out is configurable, P33 runtime requires the **actual
configured value** rather than silently injecting the 4 C factory default.

## 3. Active-defrost termination

The source lists several termination paths for active defrost:

1. evaporator sensor reaches its stop value;
2. defrost has continued for **longer than 15 minutes**;
3. return sensor BT3 falls below 10 C;
4. BP8 falls below its permitted minimum.

The executable contract therefore uses `elapsed_minutes > 15`, not
`>= 15`.

This is controller-state evidence.  It is not an event-energy measurement.

## 4. Direct Modbus observational path

Current official NIBE S-Series Modbus technical information exposes, for the
S2125/F2120 family, source-native channels including:

- outdoor temperature BT28;
- evaporator-in temperature BT16;
- current compressor frequency;
- Defrost status:
  - 0 = off
  - 1 = active
  - 2 = passive.

For auditability, P33 materializes the exact **slave-1** register map in:

`data/processed/b05_p33_nibe_s2125_modbus_channels.csv`.

Register IDs are slave-specific and are not generalized to other slave
addresses.

Source:
`SRC-B05-NIBE-S2125-MODBUS-DEFROST-2026`.

## 5. Why Hungarian T + RH is still insufficient

B05 already preserves source-native hourly outdoor temperature and relative
humidity from HungaroMet.

The NIBE controller, however, depends on **BT16 evaporator temperature** plus
compressor/controller state.  P33 has no qualified product-specific mapping:

```
ambient temperature + RH + operating point -> BT16
```

Therefore:

```
HUNGAROMET T + RH != NIBE DEFROST EVENT
```

unless future evidence supplies either:

- observed S2125 BT16/BT28/Defrost telemetry time series; or
- a qualified product-specific weather/operating-state -> BT16 model.

## 6. Why event energy remains Q

The manufacturer sources say that:

- active defrost keeps the compressor running and stops the fan;
- passive defrost stops the compressor and runs the fan at high speed.

They do **not** provide source-native:

- heat removed per event;
- electrical kWh per active event;
- fan kWh per passive event;
- a complete event-energy surface by weather/operating state.

Therefore P33 returns:

```
heat_penalty_kwh = None
electricity_penalty_kwh = None
```

for both derived and directly observed event states.

Component state is not converted into energy.

## 7. Runtime contract

`modules/B05/defrost_runtime_state.py` provides:

- bounded requirement-accumulation classification;
- active/passive due-state classification using explicit controller timer and
  configuration;
- exact active-defrost termination checks;
- direct Modbus Defrost status decoding;
- explicit Q residuals for event energy and weather -> BT16 mapping.

No change is made to the generic engine energy formula.

## 8. P14 accounting boundary remains intact

P33 does not add a second penalty to EN 14511 points.

The P14 rule remains:

```
EN14511_RATED_POINT -> NO_EXTRA_UNIVERSAL_DEFROST_PENALTY
```

and NIBE P10 continuous capacity curves remain explicitly defrost-excluded.

## 9. Q-B05-003 transition

```
OPEN_NARROWED_TO_WEATHER_DRIVEN_RUNTIME_MODEL
->
OPEN_NARROWED_TO_EVENT_ENERGY_AND_WEATHER_TO_EVAPORATOR_STATE
```

Bounded blocker transition:

```
PRODUCT_SPECIFIC_WEATHER_DRIVEN_DEFROST_MODEL_REQUIRED
->
PARTIAL_RESOLVED_TO_EXACT_CONTROLLER_STATE_AND_TELEMETRY
```

Residuals:

- `NIBE_DEFROST_EVENT_HEAT_ELECTRIC_ENERGY_REQUIRED`;
- `WEATHER_TO_NIBE_BT16_OR_OBS_TIMESERIES_REQUIRED`;
- `CROSS_PRODUCT_DEFROST_RUNTIME_COVERAGE_REQUIRED`.

## 10. Readiness

- DEFROST: 5% -> 20%
- B05 overall: 64% -> 64%

The uplift reflects real product-specific controller-state and telemetry
evidence.  It does not claim a complete defrost energy model.

## Sources

NIBE S2125 official installer manual:

https://installer.nibe.eu/download/18.69d23679185eaf109d92e22/1676544183097/S2125-IHB-631676-1.pdf

NIBE S-Series Modbus technical information:

https://www.nibe.eu/download/18.42a6470a1963dded290bb1/1746538843623/Technical%20information%20Modbus%20S-Series.pdf
