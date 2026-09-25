# B05-P34 - NIBE DEFROST EVENT-ENERGY ADMISSION

Date: 2026-09-25
Canonical base: b13e7c685a69bf3bb64a6c8e904d63a051084c7d

## Purpose

P33 qualified exact NIBE S2125 defrost state and direct telemetry.

P34 tests the next residual:

NIBE_DEFROST_EVENT_HEAT_ELECTRIC_ENERGY_REQUIRED

The result is an executable admission route, not a numeric event-energy
closure.

## Core boundary

EVENT SHAPE != EVENT IDENTITY != EVENT ENERGY

A dashboard trace that resembles a defrost is not sufficient. Direct event
state and electrical/thermal measurements must be joined on the same system and
the same time intervals.

## 1. Manufacturer measurement path exists

Current NIBE S-Series Modbus documentation provides the S2125/F2120 slave-1
direct state channel already admitted by P33:

- Defrost register 1805;
- 0 = off;
- 1 = active;
- 2 = passive.

The same current NIBE document publishes common measurement channels including:

- pulse energy meter BE7/BF3: register 396, kWh, factor 100;
- pulse energy meter BE6/BF2: register 398, kWh, factor 100;
- flow measurement hot water, compressor including addition: 1575, kWh,
  factor 10;
- flow measurement, compressor including addition: 1577, kWh, factor 10;
- flow measurement hot water, compressor only: 1583, kWh, factor 10;
- flow measurement heat, compressor only: 1585, kWh, factor 10;
- instantaneous used power: 2166, W, factor 10, described as used power with
  compressor and addition.

This proves that a same-system measurement route is technically available.

It does not prove that any particular public logger currently captures all of
these channels at sufficient temporal resolution.

Source:
SRC-B05-NIBE-S2125-MODBUS-DEFROST-2026.

## 2. Public S2125 field-monitor candidate

Public HeatpumpMonitor system 252 identifies a 7.6 kW S2125 R290 system in
Silkeborg, Denmark.

The associated OpenEnergyMonitor owner discussion identifies the installation
as NIBE S2125 + S320, describes normal and tank-defrost behaviour, links public
monitoring, and states that Home Assistant logs defrosting state / last-defrost
information.

These sources establish a real product-family field-monitor target and an event
logging route.

They do not provide, in the material admitted by P34, one raw canonical table
that contains timestamp + direct NIBE Defrost state + electrical measurement +
thermal measurement for the same complete defrost event.

Sources:

- SRC-B05-HEATPUMPMONITOR-S2125-SILKEBORG-252-2026;
- SRC-B05-OEM-S2125-SILKEBORG-DEFROST-2026.

## 3. HeatpumpMonitor API route

HeatpumpMonitor publishes a public API helper documenting:

- system metadata retrieval;
- available-feed discovery;
- timestamped timeseries retrieval.

This qualifies an acquisition route.

It does not prove that system 252 exposes the exact NIBE direct Defrost
register as a public feed. Therefore:

PUBLIC TIMESERIES API != COTIMED DIRECT-STATE EVENT SERIES

Source:
SRC-B05-HEATPUMPMONITOR-API-2026.

## 4. Numeric admission contract

modules/B05/defrost_event_energy_admission.py admits numeric event energy only
when all of the following are true:

1. every row carries one explicit event identity and one explicit system identity;
2. the complete event is independently bounded by direct OFF -> ACTIVE/PASSIVE -> OFF state transitions;
3. state, electrical and thermal streams are all OBS;
4. every event interval has direct ACTIVE or direct PASSIVE defrost state;
5. one event contains one directly identified state class;
6. intervals arrive in source order and are positive-duration and exactly contiguous;
7. power values are interval means, not isolated instantaneous point samples;
8. electrical and thermal meter boundaries are explicit and invariant;
9. state, electrical and thermal source identities are explicit;
10. thermal sign convention is explicit;
11. no electrical/thermal interval value is missing or non-finite.

When admitted, P34 may derive:

- event electrical kWh;
- net thermal energy to the building;
- heat removed during negative thermal intervals.

The output evidence class is DER_FROM_COMPLETE_COTIMED_OBS_INTERVAL_MEANS.

## 5. Why instantaneous power alone is not integrated

The NIBE register 2166 is explicitly instantaneous used power.

A sequence of isolated instantaneous values is not silently treated as exact
interval energy. P34 requires the logger/materializer to establish
INTERVAL_MEAN semantics, or a future separately qualified integration method.

Therefore:

PARTIAL EVENT WINDOW != COMPLETE EVENT ENERGY

INSTANTANEOUS POINT SAMPLE != INTERVAL ENERGY

## 6. Why cumulative kWh registers are not silently differenced

NIBE exposes cumulative kWh/flow-energy channels, but P34 does not assume that
every such register represents signed building heat removal during reverse-cycle
defrost.

A future cumulative-delta route must explicitly establish:

- meter meaning;
- event start/end boundary readings;
- resolution;
- wrap/reset behaviour;
- whether negative/reverse heat is represented and how.

Until then those channels prove measurement availability only.

## 7. Public evidence inventory

P34 stores only bounded metadata in:

data/processed/b05_p34_public_nibe_defrost_evidence_inventory.csv

No third-party raw monitoring timeseries or copyrighted document is committed.

## 8. Blocker transition

NIBE_DEFROST_EVENT_HEAT_ELECTRIC_ENERGY_REQUIRED
->
OPEN_NARROWED_TO_COTIMED_DIRECT_STATE_AND_ENERGY_SERIES

Exact new residual:

NIBE_S2125_COTIMED_DEFROST_STATE_HEAT_ELECTRIC_SERIES_REQUIRED

Q-B05-003 current state:

OPEN_NARROWED_TO_COTIMED_EVENT_ENERGY_SERIES_WEATHER_TO_BT16_AND_CROSS_PRODUCT

Other residuals remain:

- WEATHER_TO_NIBE_BT16_OR_OBS_TIMESERIES_REQUIRED;
- CROSS_PRODUCT_DEFROST_RUNTIME_COVERAGE_REQUIRED.

## 9. Readiness

- DEFROST: 20% -> 20%
- B05 overall: 64% -> 64%

No uplift is justified because P34 qualifies the measurement/admission route
but does not yet supply a real admitted event-energy observation.

## Sources

NIBE Technical Information - Modbus S-Series:
https://www.nibe.eu/download/18.42a6470a1963dded290bb1/1746538843623/Technical%20information%20Modbus%20S-Series.pdf

HeatpumpMonitor API helper:
https://heatpumpmonitor.org/api-helper

HeatpumpMonitor system 252:
https://heatpumpmonitor.org/dashboard?id=252

OpenEnergyMonitor field discussion:
https://community.openenergymonitor.org/t/nibe-ashp-and-tank-defrosts/29553
