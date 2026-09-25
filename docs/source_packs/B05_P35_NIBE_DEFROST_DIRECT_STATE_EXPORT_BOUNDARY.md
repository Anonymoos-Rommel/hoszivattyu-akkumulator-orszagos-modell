# B05-P35 - NIBE DEFROST DIRECT-STATE EXPORT BOUNDARY

Date: 2026-09-25
Canonical base: 8cff8805c10606739d4a95eb5d9776c177b4ec2c

## Purpose

P34 established the numeric event-energy admission gate and left one exact
acquisition residual:

NIBE_S2125_COTIMED_DEFROST_STATE_HEAT_ELECTRIC_SERIES_REQUIRED

P35 determines whether the public HeatpumpMonitor / OpenEnergyMonitor material
already satisfies the direct-event-identity side of that gate.

It does not.

The useful result is a narrower and now source-separated acquisition target.

## Core boundary

NEGATIVE_HEAT_PROXY
!=
DIRECT_NIBE_DEFROST_STATE
!=
RAW_TIMESTAMPED_DIRECT_STATE_EXPORT

and:

TECHNICAL_ACQUISITION_PATH_EXISTS
!=
ACQUIRED_JOINED_SERIES

## 1. Exact HeatpumpMonitor dashboard semantics

HeatpumpMonitor source code is pinned at:

a68fdc026bdfc74afe557d952f0d4d96ce76eba5

In:

www/Modules/dashboard/myheatpump_process.js

the function process_defrosts() iterates heatpump_heat. When heat is negative
and the same interval is not classified as cooling, the code accumulates:

total_defrost_and_loss_kwh += -1 * heat * interval

The public UI therefore means exactly what its label says:

"defrosts and other heat lost"

This is valuable measured heat-loss information. It is not a direct controller
state flag.

Canonical rule:

HEATPUMPMONITOR_DEFROST_AND_LOSS
=
NEGATIVE_HEAT_PROXY

not:

HEATPUMPMONITOR_DEFROST_AND_LOSS
=
DIRECT_NIBE_DEFROST_STATE

Source:
SRC-B05-HEATPUMPMONITOR-CODE-A68FDC-2026.

## 2. Public HeatpumpMonitor API exposure boundary

At the same exact code commit,
www/Modules/timeseries/timeseries_controller.php shows:

- timeseries/available loads the system MyHeatpump app configuration;
- server, API key and feed IDs are removed before return;
- timeseries/data only maps requested keys that are already present in
  config->feeds.

Therefore a custom owner EmonCMS or Home Assistant state feed is not assumed
public simply because the owner logs it locally.

Canonical rule:

PUBLIC_APP_CONFIG_FEED
!=
OWNER_CUSTOM_MODBUS_FEED

P35 repository code search found no standard heatpump_defrost key in the
current HeatpumpMonitor default-branch code. This supports the separation but
is not interpreted as proof that the owner has no private/custom state feed.

Sources:

- SRC-B05-HEATPUMPMONITOR-CODE-A68FDC-2026
- SRC-B05-HEATPUMPMONITOR-API-2026

## 3. Exact Silkeborg owner field path

The owner identifies the field installation as NIBE VVM S320 + NIBE S2125 and
states that the monitored heat-pump sensors are internal heat-pump sensors
acquired through Modbus/TCP over Wi-Fi into EmonCMS on a Raspberry Pi.

A later owner discussion of the same S2125/S320 installation shows/logs
defrosting mode and last-defrost information in Home Assistant while linking
the public HeatpumpMonitor system.

These two owner records prove:

1. an exact-product Modbus/TCP telemetry path exists in the field system;
2. direct defrost-state information is observed/logged by the owner.

They do not provide an admitted raw table containing the direct state,
timestamps and source/register/feed binding.

Therefore:

OWNER_DIRECT_STATE_LOG_EXISTS
!=
OWNER_RAW_DIRECT_STATE_EXPORT

Sources:

- SRC-B05-OEM-S2125-MODBUS-TCP-FIELD-2024
- SRC-B05-OEM-S2125-SILKEBORG-DEFROST-2026

## 4. Public owner emonhub fork does not recover the missing site config

The current public fork is pinned at:

jkjaer/emonhub
5b231d1d13b215cea891ff0abfb62a8376f2c0d3

Fresh GitHub comparison against current upstream shows:

- fork ahead of upstream: 0 commits;
- fork tip is an upstream-authored commit;
- the public fork does not expose the exact owner site register/feed
  configuration needed to bind NIBE Defrost state into the public monitoring
  system.

This is not evidence that no local/private config exists. The field forum
material already indicates that local configuration did exist.

Canonical rule:

PUBLIC_FORK_CONFIG_NOT_FOUND
!=
PRIVATE_CONFIG_ABSENT

Source:
SRC-B05-JKJAER-EMONHUB-FORK-5B231D-2024.

## 5. External API probe result

A temporary isolated GitHub Actions probe attempted:

https://heatpumpmonitor.org/system/get.json?id=252

The remote server returned HTTP 403 before metadata retrieval.

Run:
36121168021

The temporary probe commit was removed from the P35 feature-branch tip before
the canonical implementation was built.

This result means only:

REMOTE_ACCESS_BLOCKED_403

It does not mean:

SYSTEM_DOES_NOT_EXIST
FEED_DOES_NOT_EXIST
DATA_DOES_NOT_EXIST

Canonical rule:

REMOTE_HTTP_403 != SOURCE_ABSENCE

Source:
SRC-B05-P35-HPM252-REMOTE-PROBE-2026.

## 6. Executable identity-source contract

modules/B05/defrost_identity_source_contract.py explicitly separates:

- DIRECT_CONTROLLER_RAW;
- NEGATIVE_HEAT_PROXY;
- OWNER_VISUAL_LOG;
- PUBLIC_APP_FEED;
- REMOTE_ACCESS_RESULT.

DIRECT_CONTROLLER_RAW, or a PUBLIC_APP_FEED with an explicit proven binding to
the direct controller state, may become DIRECT_STATE_ADMITTED, and only when
it is:

- exact-system bound;
- raw and timestamped;
- explicitly tied to controller-state semantics;
- explicit about state values.

Negative heat remains PROXY_ONLY.
Owner visual/log evidence remains CONTEXT_ONLY.
HTTP access results remain CONTEXT_ONLY.
An unbound public app feed remains Q. A future explicitly bound public raw
controller-state feed is admissible on the same evidence requirements as an
owner raw export.

A second gate then requires:

- admitted direct raw state;
- raw OBS electric series;
- raw OBS thermal series;
- same system;
- common timebase;
- explicit meter boundaries.

Only then is the source package READY_FOR_P34_EVENT_ENERGY_GATE.

P34 must still validate the complete OFF -> event -> OFF event window.

## 7. Exact blocker transition

Previous:

NIBE_S2125_COTIMED_DEFROST_STATE_HEAT_ELECTRIC_SERIES_REQUIRED

Current:

OPEN_NARROWED_TO_OWNER_DIRECT_STATE_EXPORT_AND_COTIMED_METER_JOIN

New exact residuals:

- SILKEBORG_S2125_OWNER_RAW_DIRECT_STATE_EXPORT_REQUIRED
- SILKEBORG_S2125_COTIMED_ELECTRIC_THERMAL_EXPORT_REQUIRED

Q-B05-003 current state:

OPEN_NARROWED_TO_OWNER_EXPORT_WEATHER_TO_BT16_AND_CROSS_PRODUCT

The separate residuals remain:

- WEATHER_TO_NIBE_BT16_OR_OBS_TIMESERIES_REQUIRED
- CROSS_PRODUCT_DEFROST_RUNTIME_COVERAGE_REQUIRED

## 8. Readiness

- DEFROST: 20% -> 20%
- B05 overall: 64% -> 64%

P35 resolves source semantics and acquisition targeting. It does not add one
real event-energy measurement, so no readiness uplift is justified.

## Sources

HeatpumpMonitor exact code commit:
https://github.com/openenergymonitor/heatpumpmonitor.org/tree/a68fdc026bdfc74afe557d952f0d4d96ce76eba5

HeatpumpMonitor public API:
https://heatpumpmonitor.org/api-helper

Silkeborg S2125 public monitor:
https://heatpumpmonitor.org/dashboard?id=252

Owner S2125/S320 defrost discussion:
https://community.openenergymonitor.org/t/nibe-ashp-and-tank-defrosts/29553

Owner S2125/S320 Modbus-TCP integration discussion:
https://community.openenergymonitor.org/t/making-a-modbus-tcp-heat-pump-work-with-emonhub/26151

Owner public emonhub fork:
https://github.com/jkjaer/emonhub/tree/5b231d1d13b215cea891ff0abfb62a8376f2c0d3

P35 hosted access probe:
https://github.com/Anonymoos-Rommel/hoszivattyu-akkumulator-orszagos-modell/actions/runs/36121168021
