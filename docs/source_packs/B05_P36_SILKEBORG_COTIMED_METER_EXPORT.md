# B05-P36 - SILKEBORG S2125 CO-TIMED METER AND CUMULATIVE-ENERGY ROUTE

Date: 2026-09-25
Canonical base: 812010e2705661817a64687f1a0c7b4b50491c28

## Purpose

P35 separated two missing artifacts for the exact Silkeborg NIBE S2125 field system:

- SILKEBORG_S2125_OWNER_RAW_DIRECT_STATE_EXPORT_REQUIRED
- SILKEBORG_S2125_COTIMED_ELECTRIC_THERMAL_EXPORT_REQUIRED

P36 attacks the meter side directly and then tests whether the exact public
cumulative-energy feeds provide a qualified alternative to integrating sampled
power.

## Core boundary

COTIMED_METER_SERIES_EXISTS
!=
DIRECT_DEFROST_EVENT_EXISTS
!=
EVENT_ENERGY_IS_ADMISSIBLE

and:

PHPFINA_FIXED_INTERVAL_NO_AVERAGING
!=
INTERVAL_MEAN_POWER

while:

SOURCE_DEFINED_CUMULATIVE_KWH
+
EXACT_SYSTEM_FEED_BINDING
+
SIGNED_FIELD_DELTA_BEHAVIOUR
->
QUALIFIED_CUMULATIVE_DELTA_ROUTE

still does not create a defrost event boundary without direct controller state.

## 1. Exact public owner app route

The Silkeborg owner publicly linked an EmonCMS app named NIBE_S2125 in an
OpenEnergyMonitor community discussion dated 2024-05-23.

The public post contains a read-only access route. P36 does not store, copy or
publish the read-only credential in the repository. Hosted probes recover the
route dynamically from the public owner post and print no credential value.

Source:
SRC-B05-OEM-S2125-PUBLIC-EMONCMS-APP-2024.

## 2. Exact public app meter readback

Hosted probe run 36125366409 recovered the exact app configuration.

The probe returned:

- PUBLIC_FORUM_LINK_RECOVERED=YES
- READKEY_REDACTED=YES
- GETCONFIGMETA_OK=YES
- metadata SHA-256:
  0b7f79b4ac01d9584a7e92eea5a006113c0814a577bead91770b287dc0363aa6

The exact public app configuration exposed:

- heatpump_elec: feed 501345, W, native interval 10 s
- heatpump_elec_kwh: feed 501346, kWh, native interval 10 s
- heatpump_heat: feed 501342, W, native interval 10 s
- heatpump_heat_kwh: feed 501343, kWh, native interval 10 s
- heatpump_flowT: feed 501339, degC, native interval 10 s
- heatpump_returnT: feed 501338, degC, native interval 10 s
- heatpump_flowrate: feed 501341, l/m, native interval 10 s
- heatpump_outsideT: feed 501336, degC, native interval 10 s

P36 does not infer controller-state semantics from any of these standard app
feed keys.

Source:
SRC-B05-P36-SILKEBORG-EMONCMS-METER-PROBE-2026.

## 3. Exact co-timed power export

The first probe read electric and thermal power over the same public
HeatpumpMonitor-linked 24-hour window:

- local window: 2025-12-30 00:00 to 2025-12-31 00:00 Europe/Copenhagen
- UTC window: 2025-12-29T23:00:00Z to 2025-12-30T23:00:00Z

Electric power response:

- raw response SHA-256:
  4d3a766c1d983186be5ac6ac70ef8d7fdedf91220c5362b14aa6c0ca0d896f97
- returned points: 8641
- non-null points: 8297

Thermal power response:

- raw response SHA-256:
  4461464bba911eb5c6934fc9a606ddf338333992141f42c7ffddb5ba2b23f30a
- returned points: 8641
- non-null points: 8297

Exact timestamp join:

- common non-null timestamps: 8297
- first common timestamp: 1767049210000 ms
- last common timestamp: 1767135590000 ms
- common timestamps with negative measured heatpump_heat: 596
- first negative-heat common timestamp: 1767050380000 ms
- last negative-heat common timestamp: 1767133880000 ms

No third-party raw timeseries payload is committed. P36 stores only bounded
metadata, counts, timestamps and cryptographic digests.

This resolves:

SILKEBORG_S2125_COTIMED_ELECTRIC_THERMAL_EXPORT_REQUIRED

for the exact public app/system and audited window.

## 4. Negative heat remains a proxy, not event identity

P35 established from exact HeatpumpMonitor code that "defrosts and other heat
lost" is based on negative heat output not classified as cooling.

P36 proves that negative heat exists in the raw co-timed Silkeborg meter
series.

That still does not establish which intervals are direct NIBE Defrost=1
(active) or Defrost=2 (passive).

Therefore:

NEGATIVE_HEAT_COMMON_POINT
!=
DIRECT_NIBE_DEFROST_STATE

The event-identity artifact remains:

SILKEBORG_S2125_OWNER_RAW_DIRECT_STATE_EXPORT_REQUIRED

## 5. Direct power integration remains blocked

Official EmonCMS PHPFina source is pinned at:

669aca74038f271e24b23238eec639d1fa185114

The implementation explicitly identifies PHPFina as:

Fixed Interval No Averaging

A 10-second native interval therefore proves fixed sample spacing but not that a
stored W value is the mean power over the complete interval.

P34 requires interval-mean semantics for its direct power-integration route.
P36 does not relax that rule.

Source:
SRC-B05-EMONCMS-PHPFINA-NOAVG-669ACA-2025.

## 6. MyHeatpump defines an explicit cumulative-kWh route

The exact MyHeatpump app source is pinned at:

52ff3d9ace5e81e38833be501c5290e5fdb08c16

Its configuration defines:

- heatpump_elec_kwh as "Cumulative electric use kWh"
- heatpump_heat_kwh as "Cumulative heat output in kWh"

Its processing path uses get_cumulative_kwh(), which bounds the requested
window to feed availability, reads a start value and an end value, and returns:

kWh_end - kWh_start

This establishes an explicit application-level cumulative-delta contract.

Source:
SRC-B05-EMONCMS-MYHEATPUMP-KWH-52FF3D-2026.

## 7. Exact field-system cumulative behaviour

A second redacted hosted probe was run:

36126579113

It queried the exact Silkeborg electric power, thermal power, cumulative
electric kWh and cumulative thermal kWh feeds over:

- 1767050300000 to 1767051000000 ms
- 2025-12-29T23:18:20Z to 2025-12-29T23:30:00Z

Raw-response SHA-256 digests:

- heatpump_elec:
  2bf8eb4a1ee968f27e796ab510bbc14aa1f6b84a44b86f3adfc85d9ae70c8b28
- heatpump_heat:
  7ebc4a99f92c1a772e9ba9680685f4e8589f207dd3054ad6cdd4a6c66fa6c79c
- heatpump_elec_kwh:
  79d9d87cb5c654d1b39316db1229d4b28db8c34a47cab22e31333982574c6fe9
- heatpump_heat_kwh:
  8f99bf3dd1624df36f5be9324d8576efb10712fa4bf0c9268afe96b4e9796e78

Observed bounded results:

- electric power non-null points: 68
- thermal power non-null points: 68
- electric kWh non-null points: 71
- thermal kWh non-null points: 71
- four-feed common timestamps: 68
- evaluated common delta steps: 67
- reset-like delta steps greater than 1 kWh: 0 on both energy feeds
- negative thermal-power common points: 42
- negative thermal-power points whose corresponding heat-kWh delta is negative:
  42 / 42

Electric cumulative delta versus W x dt:

- mean absolute error using current point: 0.00039828850538971804 kWh
- maximum absolute error using current point: 0.003772135416666666 kWh

Thermal cumulative delta versus W x dt:

- mean absolute error using current point: 0.0018767015270530485 kWh
- maximum absolute error using current point: 0.02731871202256944 kWh

These comparisons are consistency checks, not a promotion of sampled W to
interval-mean power.

The decisive result is that the exact owner app binds source-defined cumulative
kWh feeds, the app source defines end-minus-start semantics, and the exact
field-system thermal cumulative feed moves negatively on every audited negative
thermal-power step.

Therefore the cumulative route is qualified in bounded exact-system scope:

SILKEBORG_S2125_INTERVAL_MEAN_OR_QUALIFIED_CUMULATIVE_DELTA_REQUIRED
->
RESOLVED_QUALIFIED_CUMULATIVE_DELTA_ROUTE

Event-specific reset/continuity remains an event-window admission check when the
direct state boundary is finally available; it is not a separate generic source
blocker.

Source:
SRC-B05-P36-SILKEBORG-KWH-SEMANTICS-PROBE-2026.

## 8. Executable contract

modules/B05/defrost_meter_export_contract.py separately qualifies:

1. exact co-timed meter export;
2. the cumulative-delta energy route;
3. direct controller event identity.

The exact P36 state is:

- meter export: ADMITTED
- cumulative-delta route: ADMITTED
- direct raw controller state: NOT ADMITTED

Therefore numeric event-energy handoff remains blocked by the event-identity
side only.

A future direct-state series must still provide:

- exact same system identity;
- raw timestamped Defrost state;
- explicit 0=off / 1=active / 2=passive semantics;
- a complete OFF -> ACTIVE/PASSIVE -> OFF event boundary;
- event-window cumulative start/end readings with no reset/discontinuity inside
  that event.

## 9. Blocker transition

Previous:

OPEN_NARROWED_TO_OWNER_DIRECT_STATE_EXPORT_AND_COTIMED_METER_JOIN

P36 final:

OPEN_NARROWED_TO_OWNER_RAW_DIRECT_STATE_EXPORT

Resolved:

- SILKEBORG_S2125_COTIMED_ELECTRIC_THERMAL_EXPORT_REQUIRED
- SILKEBORG_S2125_INTERVAL_MEAN_OR_QUALIFIED_CUMULATIVE_DELTA_REQUIRED

Remaining exact same-system event-energy residual:

- SILKEBORG_S2125_OWNER_RAW_DIRECT_STATE_EXPORT_REQUIRED

Q-B05-003 remains open because the separate families also remain:

- WEATHER_TO_NIBE_BT16_OR_OBS_TIMESERIES_REQUIRED
- CROSS_PRODUCT_DEFROST_RUNTIME_COVERAGE_REQUIRED

No numeric event kWh is admitted.

## 10. Readiness

- DEFROST: 20% -> 20%
- B05 overall: 64% -> 64%

P36 closes two real acquisition/energy-route residuals but still lacks the raw
direct event identity required for one admitted defrost event.

## Sources

Owner public EmonCMS-app discussion:
https://community.openenergymonitor.org/t/questions-to-nibe-ashp-control-settings/26181

P36 meter-series probe:
https://github.com/Anonymoos-Rommel/hoszivattyu-akkumulator-orszagos-modell/actions/runs/36125366409

P36 cumulative-kWh semantics probe:
https://github.com/Anonymoos-Rommel/hoszivattyu-akkumulator-orszagos-modell/actions/runs/36126579113

EmonCMS PHPFina exact source:
https://github.com/emoncms/emoncms/blob/669aca74038f271e24b23238eec639d1fa185114/Modules/feed/engine/PHPFina.php

MyHeatpump exact cumulative-feed source:
https://github.com/emoncms/app/blob/52ff3d9ace5e81e38833be501c5290e5fdb08c16/apps/OpenEnergyMonitor/myheatpump/myheatpump.js

MyHeatpump exact cumulative-delta processor:
https://github.com/emoncms/app/blob/52ff3d9ace5e81e38833be501c5290e5fdb08c16/apps/OpenEnergyMonitor/myheatpump/myheatpump_process.php
