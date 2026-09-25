# B05-P39 - S2125 WEATHER TO BT16 OBSERVED-TIMESERIES ACQUISITION

Date: 2026-09-25
Canonical base: 9b6a9097759307bfd225513adc0598c37aee3ff8

## Purpose

P38 parked the complete direct-event energy package behind an acquisition
dependency and identified WEATHER_TO_NIBE_BT16_OR_OBS_TIMESERIES_REQUIRED as
the next independent physical blocker.

P39 attacks that blocker without inventing an ambient-weather formula.

The exact NIBE S2125 controller does not trigger defrost from ambient
temperature or humidity alone. It uses evaporator sensor BT16 together with
compressor/controller state. Therefore the next admissible evidence object is
a same-system observed telemetry series, not a weather-only heuristic.

## Core boundary

AMBIENT_T_RH
!=
BT16_EVAPORATOR_STATE

OUTSIDE_TEMPERATURE_FEED
!=
WEATHER_TO_BT16_MAPPING

HISTORY_GRAPH
!=
RAW_SOURCE_TIMESERIES

20S_GROUPED_GRAFANA_STATE
!=
RAW_BT16_TRANSIENT_SERIES

DIRECT_MODBUS_OR_USB_OR_RAW_INFLUX
=
QUALIFIED_ACQUISITION_ROUTE

QUALIFIED_ACQUISITION_ROUTE
!=
ACQUIRED_OBS_SERIES

## 1. Official physical target

The canonical NIBE S2125 manufacturer evidence already proves:

- when BT16 is below the configured defrost-start threshold, time is counted
  toward active defrost only for compressor-running minutes;
- direct telemetry exposes BT28 outdoor temperature;
- direct telemetry exposes BT16 evaporator temperature;
- direct telemetry exposes current compressor frequency;
- direct telemetry exposes Defrost state 0=off, 1=active, 2=passive.

Sources:
- SRC-B05-NIBE-S2125-IHB
- SRC-B05-NIBE-S2125-MODBUS-DEFROST-2026

Therefore a model trained only on outdoor temperature and RH would omit a
source-defined controller input and operating-state condition.

## 2. Exact minimum observed series

P39 narrows the previous residual to one exact data object:

S2125_RAW_BT28_BT16_COMPRESSOR_DEFROST_TIMESERIES_REQUIRED

Minimum mandatory columns/fields:

- timestamp;
- exact S2125 system identity;
- BT28 outdoor temperature, degC;
- BT16 evaporator temperature, degC;
- compressor frequency or source-native compressor running state;
- direct Defrost state with explicit 0/1/2 semantics.

Required metadata:

- source system identity and controller/module identity;
- source-native sampling cadence;
- timezone / timestamp basis;
- scaling and units;
- register/entity identity;
- explicit confirmation that the rows are not an unknown downsample or graph
  interpolation.

Relative humidity, wind and precipitation are valuable weather covariates but
are not allowed to substitute for BT16. They may be joined later by timestamp
and location once the product telemetry exists.

## 3. Public EmonCMS weather/BT16 surface probe

P39 ran a redacted hosted probe against two publicly linked MyHeatpump EmonCMS
applications.

Run:
36130996547

The public read credentials were recovered dynamically from their public links
and were neither printed nor committed.

App 1:
- feeds: 14;
- inputs: 123;
- weather/BT16/direct-state candidate feeds: one;
- candidate: metoffice / outside_temperature / feed 486660;
- BT16 / evaporator / BT28 / compressor / direct-defrost input candidates: 0.

App 2:
- feeds: 9;
- inputs: 55;
- weather/BT16/direct-state candidate feeds: one;
- candidate: metoffice / outside_temperature / feed 523113;
- BT16 / evaporator / BT28 / compressor / direct-defrost input candidates: 0.

Therefore these public standard app surfaces expose ambient weather but do not
provide the required product evaporator/controller series.

Source:
SRC-B05-P39-PUBLIC-EMONCMS-BT16-PROBE-2026.

## 4. Real S2125 Home Assistant / InfluxDB route

P37/P38 already pinned a real S2125-12 + SMO S40 field installation where the
direct defrost entity is historized in InfluxDB and queried from Grafana.

The published example query uses a 20-second grouped maximum for the direct
defrost state. This proves state-history availability, but a grouped Grafana
query is not automatically a raw BT16 time series.

A later S2125 field discussion explicitly identifies direct Defrost as the
0/1/2 entity and reports BT16 being added to Home Assistant monitoring.

Sources:
- SRC-B05-S2125-HA-INFLUX-DIRECT-STATE-FIELD-2023
- SRC-B05-S2125-HA-BT16-DEFROST-FIELD-2025

These sources prove practical acquisition feasibility. They do not publish the
raw timestamped BT28+BT16+compressor+Defrost rows required by P39.

## 5. Exact S2125 USB logging route

A documented S2125-12 + SMO S40 field installation was instructed by NIBE
support to insert a USB stick and enable logging for subsequent analysis. The
owner reports using the USB logger while investigating frequent defrosts.

This proves that source-side logging is a practical acquisition route on an
exact S2125 installation.

P39 does not assume that every possible USB profile automatically contains the
required fields. Admission still requires the actual exported header/register
set and rows.

Source:
SRC-B05-S2125-SMO-S40-USB-LOGGING-FIELD-2023.

## 6. Exact S2125 myUplink / Home Assistant API surface

A Home Assistant issue documents an exact Vølund/NIBE S2125 + SMO20 system
connected through myUplink. The installation exposed 579 entities and included
a diagnostics JSON attachment in the public issue.

The attachment link is no longer retrievable through the current GitHub public
fetch path; it redirects to an expired/restricted object URL.

Therefore P39 records only:

EXACT_S2125_MYUPLINK_DATAPOINT_SURFACE_EXISTS

and explicitly does not claim:

BT16_RAW_HISTORY_ACQUIRED

Source:
SRC-B05-HA-MYUPLINK-S2125-SMO20-SURFACE-2024.

## 7. Source-quality gate

An observed BT16 series is admissible when one of these routes supplies the
mandatory columns with explicit timing semantics:

### A. Direct Modbus

- source-native register/entity identity;
- explicit scale/unit;
- timestamped polling;
- polling cadence documented;
- no unknown aggregation.

### B. USB raw logger

- source-native file;
- actual header/register identity retained;
- timestamped rows;
- scaling/divisors documented;
- no synthetic interpolation.

### C. Raw Home Assistant / Influx history

- exact source entities bound to the same system;
- raw history query or source-native cadence;
- no unknown Grafana aggregation;
- timestamps and units retained.

The following are not sufficient on their own:

- screenshots;
- line graphs;
- a grouped `max()` state query without the underlying BT16 rows;
- ambient temperature/RH alone;
- a standard MyHeatpump outside-temperature feed;
- myUplink display/history values without proven sampling/aggregation semantics;
- BT16 observations from another product family silently transferred to S2125.

## 8. Weather mapping remains a later derivation

P39 does not mint:

BT16 = f(T_ambient, RH)

and does not fit defrost frequency.

Once the raw series exists, the model may evaluate candidate explanatory
variables such as:

- BT28/outdoor temperature;
- external ambient temperature;
- relative humidity;
- precipitation/fog;
- wind;
- compressor frequency/runtime;
- previous defrost state;
- controller configuration.

The model must preserve the distinction between source-observed BT16 and any
later statistical projection of BT16.

## 9. Blocker transition

Previous:

WEATHER_TO_NIBE_BT16_OR_OBS_TIMESERIES_REQUIRED

P39:

OPEN_NARROWED_TO_RAW_BT28_BT16_COMPRESSOR_DEFROST_SERIES

New exact residual:

S2125_RAW_BT28_BT16_COMPRESSOR_DEFROST_TIMESERIES_REQUIRED

The weather-to-BT16 mapping itself remains Q until such observed data are
acquired and a bounded model is validated.

## 10. Q-B05-003 transition

Previous:

OPEN_NARROWED_TO_COMPLETE_RAW_EVENT_PACKAGE_WEATHER_TO_BT16_AND_CROSS_PRODUCT

P39:

OPEN_NARROWED_TO_COMPLETE_RAW_EVENT_PACKAGE_RAW_BT16_SERIES_AND_CROSS_PRODUCT

Residuals:

- S2125_COMPLETE_RAW_DIRECT_EVENT_PACKAGE_REQUIRED
- S2125_RAW_BT28_BT16_COMPRESSOR_DEFROST_TIMESERIES_REQUIRED
- CROSS_PRODUCT_DEFROST_RUNTIME_COVERAGE_REQUIRED

No numeric weather-to-BT16 mapping and no defrost-frequency curve are admitted.

## 11. Readiness

- DEFROST: 20% -> 20%
- B05 overall: 64% -> 64%

P39 materially narrows the acquisition specification and source-quality gate,
but does not yet acquire the physical observed series.

## Public references

P39 EmonCMS probe:
https://github.com/Anonymoos-Rommel/hoszivattyu-akkumulator-orszagos-modell/actions/runs/36130996547

Exact S2125 direct-state InfluxDB field discussion:
https://gathering.tweakers.net/forum/list_messages/2102920/45

S2125 Home Assistant BT16/direct-defrost discussion:
https://gathering.tweakers.net/forum/list_messages/2102920/102

Exact S2125 USB logging field discussion:
https://gathering.tweakers.net/forum/list_messages/2102920/17

Exact S2125 + SMO20 myUplink Home Assistant issue:
https://github.com/home-assistant/core/issues/112588
