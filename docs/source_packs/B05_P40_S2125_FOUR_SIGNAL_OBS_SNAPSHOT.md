# B05-P40 — EXACT S2125 FOUR-SIGNAL OBS SNAPSHOT ACQUISITION

Date: 2026-09-25
Canonical base: `a73d15d133ab270d6e396b6eeebbd47427600472`

## Purpose

P39 reduced the weather-to-evaporator problem to one exact observed data
object: a same-system BT28 + BT16 + compressor + direct-Defrost time series.

P40 acquires the first public machine-readable **same-system observation
snapshot** containing all four mandatory channels from an identified field
S2125 system.

It does not pretend that one snapshot is a time series.

## Core boundary

```
FOUR_SIGNAL_SAME_SYSTEM_OBS_SNAPSHOT_ACQUIRED
!=
RAW_TIMESERIES_ACQUIRED
!=
WEATHER_TO_BT16_MODEL
```

## 1. Exact field-system identity

The upstream owner publicly describes their installation as:

- NIBE S2125-12;
- VVM S320 / VVMS320;
- S135 exhaust-air unit.

The same owner publishes the NibeAPI tool and explicitly publishes an export
for comparison with other systems.

Source:
`SRC-B05-P40-SVENPAUSH-S2125-SYSTEM-IDENTITY-2026`.

## 2. Pinned public snapshot

Upstream repository:

`SvenPausH/NibeAPI`

Pinned upstream commit:

`fce46704475930c786db730fadc056340702664e`

Published source file:

`2026-5-13 20-36-13_device0_vvms320_S2125.json`

Git blob SHA:

`1d673572dbaeb399f8a701971da70dfe65e75315`

The JSON metadata states:

- application: NibeAPI;
- version: 1.1;
- exported_at: `2026-05-13 20:36:13`;
- deviceId: 0;
- datapoint count: 789.

The source does not state a timezone for `exported_at`. P40 therefore records
the timestamp exactly as source-native text and does not convert it to UTC.

The raw third-party JSON is **not copied into this repository**.

Source:
`SRC-B05-P40-SVENPAUSH-S2125-REST-SNAPSHOT-FCE467-2026`.

## 3. Four mandatory channels in one source response

The exact source response contains:

| Channel | API ID | Modbus ID | Raw | Divisor | Published value |
|---|---:|---:|---:|---:|---:|
| Outdoor temperature EB101-BT28 | 2766 | 1621 | 83 | 10 | 8.3 °C |
| Evaporator EB101-BT16 | 2767 | 1622 | 49 | 10 | 4.9 °C |
| Current compressor frequency EB101 | 3096 | 1803 | 200 | 10 | 20 Hz |
| Defrost EB101 | 3098 | 1805 | 0 | 1 | 0 |

The same response also contains:

- Time to defrost EB101, Modbus 407;
- Defrost Requested EB101;
- power and energy datapoints;
- source-native register type, unit, divisor and raw value metadata.

P40 uses only the bounded four-signal subset required by P39.

The observed direct Defrost state is `0`, so this snapshot is **not a defrost
event**.

## 4. Why this is OBS

This is not a register catalogue or a hypothetical acquisition route.

The file is a machine-readable export of the owner's real field system and
contains actual raw values for the four required channels in one exported API
response.

Therefore:

```
S2125_FOUR_SIGNAL_SAME_RESPONSE_SNAPSHOT = OBS
```

in bounded snapshot scope.

It does **not** establish:

- sample-to-sample cadence;
- event transition sequence;
- weather-to-BT16 response surface;
- defrost probability or frequency;
- event energy.

## 5. NibeAPI acquisition semantics

The upstream NibeAPI implementation provides a concrete path from this snapshot
to a time series.

The README states that the API is refreshed every 10 seconds by default.

The code:

- fetches all datapoints in one REST API operation;
- can write filtered input-register datapoints to InfluxDB;
- creates Influx line protocol with timestamp;
- scales raw values by each datapoint divisor;
- supports an `INFLUX_INPUT` filter;
- the distributed sample configuration sets `INFLUX_INPUT` to `all`.

The owner also publicly reports extending the tool with InfluxDB and using the
result with Grafana.

This proves acquisition capability, not publication of the missing historical
rows.

Source:
`SRC-B05-P40-NIBEAPI-INFLUX-SEMANTICS-FCE467-2026`.

## 6. Residual transition

P39 residual:

`S2125_RAW_BT28_BT16_COMPRESSOR_DEFROST_TIMESERIES_REQUIRED`

P40 establishes:

`S2125_FOUR_SIGNAL_SAME_RESPONSE_SNAPSHOT_ACQUIRED`

but leaves the P39 time-series residual open.

The exact remaining observation requirement is:

`S2125_MULTI_TIMESTAMP_BT28_BT16_COMPRESSOR_DEFROST_SERIES_REQUIRED`

Required closure must contain multiple source-native timestamps, including
enough changing operating conditions to support a weather/operating-state
mapping and, ideally, at least one direct Defrost transition.

One current snapshot cannot be duplicated or interpolated into a time series.

## 7. Model admission remains closed

P40 does not admit:

```
BT16 = f(weather)
```

and does not admit a defrost-frequency function.

Those require:

1. multi-timestamp same-system observations;
2. joined weather covariates where justified;
3. a defined validation/holdout design;
4. preservation of direct observed BT16 separately from any modeled BT16.

## 8. Q-B05-003

State:

`OPEN_NARROWED_TO_COMPLETE_RAW_EVENT_PACKAGE_MULTI_TIMESTAMP_BT16_SERIES_AND_CROSS_PRODUCT`

Residual families:

- `S2125_COMPLETE_RAW_DIRECT_EVENT_PACKAGE_REQUIRED`
- `S2125_MULTI_TIMESTAMP_BT28_BT16_COMPRESSOR_DEFROST_SERIES_REQUIRED`
- `CROSS_PRODUCT_DEFROST_RUNTIME_COVERAGE_REQUIRED`

No numeric defrost frequency or event kWh is admitted.

## 9. Readiness

- DEFROST: 20% -> 20%
- B05 overall: 64% -> 64%

The observation boundary improves materially, but one non-defrost snapshot
does not justify a readiness uplift.

## Public references

Field-system identity and owner's export statement:
https://www.energiesparhaus.at/forum-nibe-s2125-vvm-moduliert-nicht-richtig/85271

Pinned upstream snapshot:
https://github.com/SvenPausH/NibeAPI/blob/fce46704475930c786db730fadc056340702664e/2026-5-13%2020-36-13_device0_vvms320_S2125.json

Pinned NibeAPI repository:
https://github.com/SvenPausH/NibeAPI/tree/fce46704475930c786db730fadc056340702664e

Owner report of NibeAPI + InfluxDB use:
https://www.energiesparhaus.at/forum/84604
