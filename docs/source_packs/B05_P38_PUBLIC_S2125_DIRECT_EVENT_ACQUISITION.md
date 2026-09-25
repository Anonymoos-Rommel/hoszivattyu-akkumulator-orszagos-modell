# B05-P38 - PUBLIC S2125 DIRECT EVENT ACQUISITION AUDIT

Date: 2026-09-25
Canonical base: 49f1693ffaf49ff9ad8c85b6b1a3883e0a2c3eb7

## Purpose

P37 proved that direct NIBE S2125 defrost state is technically observable and
historisable, but the exact Silkeborg public EmonCMS surface did not expose the
raw direct state.

P38 performs one last public-acquisition attack before parking the event-energy
residual. The target is not another proxy. The target is one machine-readable
S2125 event package containing, on one exact system and one common timebase:

- direct Defrost state 0/1/2;
- a complete OFF -> ACTIVE/PASSIVE -> OFF event boundary;
- electrical energy or qualified cumulative electrical energy;
- thermal energy or qualified cumulative thermal energy.

## Core boundary

PUBLIC_FLEET_SCAN_WITH_ZERO_DIRECT_FEEDS
!=
GLOBAL_SOURCE_ABSENCE

FORUM_HISTORY_GRAPH
!=
RAW_MACHINE_READABLE_EXPORT

DIRECT_STATE_HISTORY_EXISTS
!=
COMPLETE_EVENT_ENERGY_PACKAGE_EXISTS

COMPLETE_EVENT_PACKAGE
=
SAME_SYSTEM
+
RAW_DIRECT_STATE
+
COMMON_TIMEBASE
+
ELECTRIC_ENERGY
+
THERMAL_ENERGY

## 1. HeatpumpMonitor API surface

The public HeatpumpMonitor API documents:

- /system/list/public.json for the public system inventory;
- /timeseries/available?id=SYSTEM_ID for the timeseries keys exposed for each
  public system;
- /timeseries/data for machine-readable timeseries retrieval.

Source:
SRC-B05-HEATPUMPMONITOR-API-2026.

## 2. Fleet-wide S2125 public scan

Hosted probe:

36130170945

The probe read the public system list and then queried
/timeseries/available for every public system whose hp_model contains S2125.

Point-in-time result on 2026-09-25:

- total public systems: 809;
- public S2125 systems: 4.

Exact S2125 systems:

### HPM 252 - Silkeborg, Denmark

- model: S2125;
- output: 7.6 kW;
- electric meter: Heat pump integration;
- heat meter: Heat pump integration;
- available keys: 11;
- direct-state candidates matching defrost / 1805 / 31805 / 31806 / EB101:
  0.

Available keys:
- heatpump_ch
- heatpump_dhw
- heatpump_elec
- heatpump_elec_kwh
- heatpump_flowT
- heatpump_flowrate
- heatpump_heat
- heatpump_heat_kwh
- heatpump_outsideT
- heatpump_returnT
- heatpump_targetT

### HPM 448 - Bristol

- model: S2125;
- output: 12 kW;
- MID metering: yes;
- electric meter: SDM120 Modbus/MBUS Single Phase, class 1;
- heat meter: Axioma Qalcosonic, class 2;
- available keys: 9;
- direct-state candidates: 0.

Available keys:
- heatpump_elec
- heatpump_elec_kwh
- heatpump_flowT
- heatpump_flowrate
- heatpump_heat
- heatpump_heat_kwh
- heatpump_outsideT
- heatpump_returnT
- heatpump_roomT

### HPM 660 - Farnham

- model: S2125;
- output: 12 kW;
- MID metering: yes;
- electric meter: SDM120 Modbus/MBUS Single Phase, class 1;
- heat meter: Axioma Qalcosonic, class 2;
- available keys: 9;
- direct-state candidates: 0.

The exposed keys are the same nine standard heat-pump meter/temperature keys as
HPM 448.

### HPM 729 - Molesey, Surrey

- model: S2125;
- output: 12 kW;
- MID metering: yes;
- electric meter: SDM120 Modbus/MBUS Single Phase, class 1;
- heat meter: Axioma Qalcosonic, class 2;
- available keys: 8;
- direct-state candidates: 0.

Available keys:
- heatpump_elec
- heatpump_elec_kwh
- heatpump_flowT
- heatpump_flowrate
- heatpump_heat
- heatpump_heat_kwh
- heatpump_outsideT
- heatpump_returnT

Source:
SRC-B05-P38-HPM-S2125-FLEET-SCAN-2026.

## 3. Underlying public-route audit

P38 did not assume that /timeseries/available exhausts every possible owner
feed. It therefore audited the HeatpumpMonitor metadata and public heatpump
routes for the three non-Silkeborg systems.

Hosted probes:

- 36130234218
- 36130296098
- 36130357980

Results:

- HPM 448, 660 and 729 expose heatpump_url;
- each heatpump_url resolves to heatpumpmonitor.org/heatpump/view?id=...;
- none is a direct public EmonCMS app URL;
- none of the three public heatpump pages contains a linked emoncms.org/app/view
  route that can be used to enumerate an underlying owner feed set.

HPM 252 has no heatpump_url in the public system metadata; its separate
public-owner EmonCMS route was already audited in P36/P37.

Therefore the current HeatpumpMonitor public surfaces do not expose a direct
state route for any of the four public S2125 systems.

This remains a bounded statement about the audited public surfaces, not an
assertion that owner-private histories do not exist.

Source:
SRC-B05-P38-HPM-S2125-PUBLIC-ROUTE-SCAN-2026.

## 4. Real S2125 direct-state histories still exist outside those public APIs

Independent field evidence remains important because it prevents a false
absence conclusion.

### Home Assistant / InfluxDB direct state

Real S2125 users document the Home Assistant entity for direct defrost state
and an InfluxDB/Grafana query over that state. One field report states that the
data became available after the direct entity was enabled / after a manual
defrost and was present in InfluxDB.

Source:
SRC-B05-S2125-HA-INFLUX-DIRECT-STATE-FIELD-2023.

### Same history graph can contain direct state and operating signals

Another published S2125 Home Assistant history configuration places these
signals together in a 24-hour history graph:

- direct defrost state;
- compressor frequency;
- BF1 flow;
- EB101 power;
- supply and return temperatures;
- outdoor temperature.

This proves that a useful same-system event join is practical in an owner
history database.

The forum publication is configuration/visual evidence only. It does not expose
a raw machine-readable event export, cumulative electric event energy or
cumulative thermal event energy.

Source:
SRC-B05-S2125-HA-MULTISIGNAL-HISTORYGRAPH-2024.

## 5. No admissible public complete event found

P38 found no current public source satisfying all mandatory parts at once:

1. exact S2125 system identity;
2. raw timestamped direct Defrost state;
3. complete OFF -> ACTIVE/PASSIVE -> OFF event;
4. same-system electric energy;
5. same-system thermal energy;
6. common event timebase;
7. machine-readable observations.

Therefore:

PUBLIC_COMPLETE_S2125_DIRECT_EVENT_PACKAGE
=
NOT_ACQUIRED

This is not:

PUBLIC_COMPLETE_S2125_DIRECT_EVENT_PACKAGE
=
PROVEN_NOT_TO_EXIST

## 6. Residual consolidation

P37 retained the exact Silkeborg route:

SILKEBORG_S2125_PRIVATE_HA_HISTORY_OR_1805_LOGGER_EXPORT_REQUIRED

P38 adds the product-level umbrella:

S2125_COMPLETE_RAW_DIRECT_EVENT_PACKAGE_REQUIRED

This umbrella can be resolved by either:

### Route A - Silkeborg

Acquire the private direct-state history or create a new exact-system 1805
logger export, then join the direct event boundary to the already-qualified P36
Silkeborg cumulative electric/thermal feeds.

### Route B - another exact S2125 system

Acquire a raw direct-state event plus same-system electric and thermal energy
from another S2125 installation.

Cross-system mixing is forbidden:

STATE_FROM_SYSTEM_A
+
ENERGY_FROM_SYSTEM_B
!=
ADMISSIBLE_EVENT_ENERGY

## 7. Decision after the public-acquisition attack

Repeated public searching is no longer the highest-value next step.

The event-energy residual remains real and explicit, but it is parked behind
an acquisition dependency:

S2125_COMPLETE_RAW_DIRECT_EVENT_PACKAGE_REQUIRED

The next independent physical residual to attack is:

WEATHER_TO_NIBE_BT16_OR_OBS_TIMESERIES_REQUIRED

This follows the original national-model objective. Even after one event energy
is eventually acquired, annual Hungarian defrost impact still requires a
weather-to-evaporator-state / event-frequency relationship.

## 8. Executable contract

modules/B05/public_s2125_direct_event_acquisition.py encodes:

- a fleet-wide zero-candidate scan is bounded evidence, not global absence;
- field screenshots/configuration do not substitute for raw event rows;
- a complete event package requires same-system state + electric + thermal
  observations;
- the current P38 evidence leaves event energy Q and hands the next research
  priority to weather -> BT16 / observed timeseries.

## 9. Q-B05-003 transition

Previous P37 state:

OPEN_NARROWED_TO_PRIVATE_DIRECT_STATE_EXPORT_WEATHER_TO_BT16_AND_CROSS_PRODUCT

P38 state:

OPEN_NARROWED_TO_COMPLETE_RAW_EVENT_PACKAGE_WEATHER_TO_BT16_AND_CROSS_PRODUCT

Residuals:

- S2125_COMPLETE_RAW_DIRECT_EVENT_PACKAGE_REQUIRED
- WEATHER_TO_NIBE_BT16_OR_OBS_TIMESERIES_REQUIRED
- CROSS_PRODUCT_DEFROST_RUNTIME_COVERAGE_REQUIRED

The Silkeborg private-history residual remains a valid route under the first
umbrella.

No numeric event kWh is admitted.

## 10. Readiness

- DEFROST: 20% -> 20%
- B05 overall: 64% -> 64%

P38 exhausts a bounded current public acquisition route but does not add the
missing physical observation.

## Public references

HeatpumpMonitor API:
https://heatpumpmonitor.org/api-helper

P38 fleet scan:
https://github.com/Anonymoos-Rommel/hoszivattyu-akkumulator-orszagos-modell/actions/runs/36130170945

P38 S2125 metadata scan:
https://github.com/Anonymoos-Rommel/hoszivattyu-akkumulator-orszagos-modell/actions/runs/36130234218

P38 heatpump-url route scan:
https://github.com/Anonymoos-Rommel/hoszivattyu-akkumulator-orszagos-modell/actions/runs/36130296098

P38 linked-app scan:
https://github.com/Anonymoos-Rommel/hoszivattyu-akkumulator-orszagos-modell/actions/runs/36130357980

S2125 HA/Influx direct-state field evidence:
https://gathering.tweakers.net/forum/list_messages/2102920/45

S2125 multi-signal HA history configuration:
https://gathering.tweakers.net/forum/list_messages/2102920/56
