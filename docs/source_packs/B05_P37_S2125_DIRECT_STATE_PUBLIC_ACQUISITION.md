# B05-P37 - S2125 DIRECT DEFROST STATE PUBLIC ACQUISITION BOUNDARY

Date: 2026-09-25
Canonical base: f9bbe06fb5a5ec5156518b7340966e00b44de63d

## Purpose

P36 resolved the exact Silkeborg S2125 co-timed electrical/thermal export and a
bounded cumulative-kWh delta route. The remaining exact-system event-energy
artifact is direct controller event identity.

P37 audits the remaining public acquisition surface and separates:

1. public Silkeborg EmonCMS data actually exposed today;
2. private Home Assistant direct-state context documented by the owner;
3. independent real S2125 direct-state logging implementations;
4. the exact artifact still required for an admitted event.

## Core boundary

OPERATION_PRIORITISATION_10_20_30
!=
DIRECT_DEFROST_STATE_0_1_2

PUBLIC_EMONCMS_SURFACE_AUDIT
!=
PRIVATE_HOME_ASSISTANT_HISTORY_ABSENCE

CROSS_SYSTEM_S2125_DIRECT_STATE_LOGGING
!=
EXACT_SILKEBORG_RAW_EVENT

TECHNICAL_ACQUISITION_FEASIBILITY
!=
ACQUIRED_EXACT_EVENT_SERIES

## 1. Official direct-state authority remains explicit

Current NIBE S-Series Modbus authority exposes a read-only Defrost state for the
S2125/F2120 family with explicit state semantics:

- direct Defrost register identity: 1805 in the checked S2125 register mapping;
- type: input register / u8;
- 0 = off;
- 1 = active;
- 2 = passive.

The project already pins this authority as:

SRC-B05-NIBE-S2125-MODBUS-DEFROST-2026.

This is the semantic target. A different field with different value semantics
cannot substitute for it.

## 2. Exact Silkeborg public feed candidate audit

A temporary hosted probe dynamically recovered the owner's public read-only
EmonCMS route without storing or printing the credential.

Run:
36127929853

Result:

- public feed list readable: YES;
- total feeds reported: 13;
- targeted direct-state candidate search terms:
  defrost, 1805, 31806, EB101, last-defrost, mode, avfrost;
- candidates returned: 1;
- candidate:
  - feed id: 501344
  - tag: S2125
  - name: Operation Mode
  - engine: 5.

This is a targeted candidate search, not a claim that every possible private or
differently named signal is globally absent.

Source:
SRC-B05-P37-SILKEBORG-PUBLIC-FEED-CANDIDATE-PROBE-2026.

## 3. Operation Mode is not Defrost

A second hosted probe joined feed 501344 to the exact Silkeborg thermal feed
501342 over the same P36 24-hour window.

Run:
36127985794

Observed:

- common timestamps: 8297;
- Operation Mode values: 10, 20, 30;
- counts:
  - 10: 13
  - 20: 687
  - 30: 7597
- negative-heat points by Operation Mode:
  - 10: 0
  - 20: 40
  - 30: 556
- negative-heat runs detected: 19.

Across the inspected defrost-shaped negative-heat transitions, Operation Mode
can remain 30 before and throughout the negative-heat interval.

NIBE source semantics identify this 10/20/30 family as operating
prioritisation, not direct Defrost 0/1/2 state.

Therefore:

OPERATION_MODE_501344
!=
DIRECT_NIBE_DEFROST_STATE

Source:
SRC-B05-P37-SILKEBORG-OPMODE-SEMANTICS-PROBE-2026.

## 4. Exact public EmonCMS input audit

The public read route also permits input/list.json readback.

Probe run:
36128067191

Result:

- input list returned as a list;
- input rows: 7;
- targeted direct-state candidate count: 0.

A separate bounded input-name inventory was run:

36128115477

The exact seven public inputs were:

- OutdoorTemp
- FlowRate
- TargetSupplyTemp
- OperationMode
- ReturnTemp
- SupplyTemp
- CurPwr

No public input in this exact seven-input set is a direct Defrost state.

This is a statement about the audited public EmonCMS input surface only.
It is not evidence that the owner's private Home Assistant recorder lacks the
state.

Sources:
- SRC-B05-P37-SILKEBORG-PUBLIC-INPUT-PROBE-2026
- SRC-B05-P37-SILKEBORG-PUBLIC-INPUT-INVENTORY-2026

## 5. Owner private Home Assistant context remains important

The exact Silkeborg owner has separately documented Home Assistant
"defrosting mode" and "last defrost" logging for the same S2125/S320 field
system.

P37 therefore does not conclude:

DIRECT_STATE_ABSENT

It concludes only:

DIRECT_STATE_RAW_HISTORY_NOT_ACQUIRED_FROM_AUDITED_PUBLIC_EMONCMS_SURFACE

The likely existing route is the owner's private Home Assistant history /
recorder rather than the public EmonCMS app surface.

Source:
SRC-B05-OEM-S2125-SILKEBORG-DEFROST-2026.

## 6. Independent real S2125 logging proves acquisition feasibility

### 6.1 nibe2mqtt

Exact public repository commit:

e3922c535b2f4d23053429935dd0e898738569a7

The S2125 register data includes:

Defrosting (EB101) -> MODBUS_INPUT_REGISTER 1805

The parser explicitly handles the 1805 defrost state, maintains previous
defrost status and increments a defrost counter on a 0 -> 1 transition.
The same project documents MQTT-to-InfluxDB storage.

This proves a concrete S2125 Modbus -> MQTT -> history-database acquisition
architecture for the direct state.

It does not provide the Silkeborg owner's private raw history.

Source:
SRC-B05-NIBE2MQTT-S2125-DIRECT-STATE-E3922C-2023.

### 6.2 Home Assistant / InfluxDB field evidence

A separate real NIBE S2125 + SMO S40 field discussion documents the direct
defrost entity being enabled in Home Assistant and queried from InfluxDB /
Grafana. The published query groups the direct defrost entity on a 20-second
timebase.

This independently demonstrates that S2125 direct defrost state is practically
historized in real Home Assistant / InfluxDB operation.

The source-native Home Assistant entity suffix is retained as published and is
not numerically equated to the official NIBE register ID by P37.

Source:
SRC-B05-S2125-HA-INFLUX-DIRECT-STATE-FIELD-2023.

## 7. Acquisition conclusion

The remaining blocker is no longer:

"find whether S2125 exposes a direct state"

and it is no longer:

"find whether direct state can be historized".

Both are proven.

The exact remaining artifact is:

SILKEBORG_S2125_PRIVATE_HA_HISTORY_OR_1805_LOGGER_EXPORT_REQUIRED

Two admissible routes now exist.

### Route A - private history export

Obtain from the exact Silkeborg installation a raw timestamped Home Assistant /
InfluxDB history export containing direct Defrost state for a complete event
window.

Required minimum columns:

- timestamp;
- exact entity/register identity;
- state value 0/1/2.

The event must contain a complete:

OFF -> ACTIVE/PASSIVE -> OFF

boundary.

### Route B - new direct logger

If historical private export cannot be obtained, log the exact S2125 direct
Defrost register on the exact Silkeborg system prospectively, preserving raw
timestamps and state values.

Once one complete raw direct-state event exists, P36 already supplies the
qualified same-system cumulative electric/thermal energy route needed to join
event start/end boundaries.

## 8. Executable contract

modules/B05/direct_defrost_state_acquisition.py enforces:

- Operation Mode 10/20/30 cannot satisfy direct Defrost identity;
- public EmonCMS input/feed audit cannot be generalized into private HA absence;
- independent S2125 historical logging proves feasibility only;
- only an exact-system raw timestamped 0/1/2 series can close event identity.

## 9. Blocker transition

Previous:

SILKEBORG_S2125_OWNER_RAW_DIRECT_STATE_EXPORT_REQUIRED

P37:

OPEN_NARROWED_TO_PRIVATE_HA_HISTORY_OR_NEW_1805_LOGGER_EXPORT

New exact residual:

SILKEBORG_S2125_PRIVATE_HA_HISTORY_OR_1805_LOGGER_EXPORT_REQUIRED

Q-B05-003 current state becomes:

OPEN_NARROWED_TO_PRIVATE_DIRECT_STATE_EXPORT_WEATHER_TO_BT16_AND_CROSS_PRODUCT

Other residual families remain:

- WEATHER_TO_NIBE_BT16_OR_OBS_TIMESERIES_REQUIRED
- CROSS_PRODUCT_DEFROST_RUNTIME_COVERAGE_REQUIRED

No numeric event kWh is admitted.

## 10. Readiness

- DEFROST: 20% -> 20%
- B05 overall: 64% -> 64%

P37 materially narrows the acquisition route but does not yet acquire the one
raw direct-state event required to increase evidence readiness.

## Public references

P37 feed-candidate probe:
https://github.com/Anonymoos-Rommel/hoszivattyu-akkumulator-orszagos-modell/actions/runs/36127929853

P37 Operation Mode probe:
https://github.com/Anonymoos-Rommel/hoszivattyu-akkumulator-orszagos-modell/actions/runs/36127985794

P37 public-input probe:
https://github.com/Anonymoos-Rommel/hoszivattyu-akkumulator-orszagos-modell/actions/runs/36128067191

P37 public-input inventory:
https://github.com/Anonymoos-Rommel/hoszivattyu-akkumulator-orszagos-modell/actions/runs/36128115477

nibe2mqtt exact commit:
https://github.com/hansij66/nibe2mqtt/tree/e3922c535b2f4d23053429935dd0e898738569a7

Independent S2125 HA/Influx field discussion:
https://gathering.tweakers.net/forum/list_messages/2102920/45
