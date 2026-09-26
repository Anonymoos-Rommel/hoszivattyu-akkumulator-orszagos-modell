# B05-P41 — EXACT S2125 MULTI-TIMESTAMP PUBLIC HISTORY ACQUISITION AUDIT

Date: 2026-09-25
Expanded public-history audit: 2026-09-26
Canonical base: `c48cbadf5a5d0ea9199a965e48d7b4bd0cd40fcf`

## Purpose

P40 acquired the first public machine-readable exact S2125 same-response
snapshot containing BT28, BT16, current compressor frequency and direct
Defrost.

P41 continues the acquisition attack for the still-open physical residual:

`S2125_MULTI_TIMESTAMP_BT28_BT16_COMPRESSOR_DEFROST_SERIES_REQUIRED`

The goal is not another telemetry-route proof. The goal is a public raw
multi-timestamp row set.

## Core boundary

```
EXACT_S2125_MULTI_TIMESTAMP_HISTORY_EXISTS
!=
PUBLIC_RAW_FOUR_SIGNAL_SERIES_ACQUIRED

PUBLIC_GRAPH_OR_QUERY
!=
RAW_SOURCE_ROWS

CSV_EXPORT_CAPABILITY
!=
PUBLIC_CSV_ACQUIRED

READ_ONLY_VIEWER_OFFER
!=
PUBLIC_DATA_ACCESS

PUBLIC_RAW_OTHER_CHANNEL_S2125_TIMESERIES
!=
PUBLIC_RAW_TARGET_FOUR_SIGNAL_SERIES

OWNER_SIDE_COMPLETE_FOUR_SIGNAL_HISTORY
!=
PUBLIC_RAW_FOUR_SIGNAL_SERIES_ACQUIRED

BOUNDED_PUBLIC_TARGET_EXPORT_SEARCH_EXHAUSTED
!=
GLOBAL_SOURCE_ABSENCE
```

P41 does not claim global source absence. It records the bounded result of the
audited public field systems and repositories.

## 1. SvenPausH — S2125-12 + VVM/VVMS320

P40 already acquired one exact four-signal API snapshot from this owner.

The owner's public field discussion additionally states that data are read from
the VVM320 Modbus interface, written to InfluxDB and visualized in Grafana.
The same defrost discussion analyses BT16 / evaporator temperature and the
defrost process over time.

The pinned NibeAPI implementation can refresh the local REST API every 10
seconds and write input registers to InfluxDB.

Repository history was audited through the public Git history:
- the 2026-05-13 S2125 JSON is the only committed field snapshot;
- earlier export/compare commits contain code only;
- SQL dumps contain schema but no nibe_datenpunkte_log observation rows;
- no Influx debug/history dump is committed;
- no public NibeAPI fork publishes another field export.

Result:

`OWNER_LOCAL_MULTITIMESTAMP_HISTORY = PROVEN`

`PUBLIC_RAW_FOUR_SIGNAL_SERIES = NOT_ACQUIRED`

Sources:
- SRC-B05-P40-SVENPAUSH-S2125-SYSTEM-IDENTITY-2026
- SRC-B05-P40-SVENPAUSH-S2125-REST-SNAPSHOT-FCE467-2026
- SRC-B05-P40-NIBEAPI-INFLUX-SEMANTICS-FCE467-2026
- SRC-B05-P41-SVENPAUSH-S2125-INFLUX-HISTORY-2025

## 2. Borisvkr / martius — S2125-12 + SMO S40

A public field discussion identifies an exact S2125-12 + SMO S40 system and
publishes a Grafana/Influx query for the direct defrost entity:

`defrosting_eb101_31806`

The discussion explicitly confirms that the direct-state data exist in
InfluxDB.

The published query is a grouped Grafana query using `max(value)` over 20 s.
It is evidence that history exists; it is not the underlying raw row export.

P41 found no public owner CSV, Influx dump, recorder DB export or raw Grafana
data export containing the complete BT28+BT16+compressor+Defrost row set.

Source:
- SRC-B05-S2125-HA-INFLUX-DIRECT-STATE-FIELD-2023

## 3. Havisoft — S2125-12 + VVM S320

The exact owner's 2024 Home Assistant history-graph configuration already
places BT28, direct Defrost and current compressor frequency on the same
history surface. In the same exact S2125-12 + VVM S320 system, a later
2025 field update explicitly adds BT16 to Home Assistant monitoring while
retaining the direct Defrost 0/1/2 entity.

Therefore P41 can now state the stronger bounded result:

`OWNER_SIDE_COMPLETE_FOUR_SIGNAL_HISTORY = PROVEN`

for one exact same-system monitoring environment containing:
- BT28;
- BT16;
- current compressor frequency;
- direct Defrost.

This is not promoted to public raw data. The audited public posts expose
history configuration, graphs and the later BT16 monitoring update, but no
source-native Home Assistant recorder export, Influx dump or CSV row set
containing the four channels together.

Therefore:

`PUBLIC_RAW_FOUR_SIGNAL_SERIES = NOT_ACQUIRED`

Sources:
- SRC-B05-S2125-HA-MULTISIGNAL-HISTORYGRAPH-2024
- SRC-B05-S2125-HA-BT16-DEFROST-FIELD-2025

## 4. WPNutzer — S2125-8 + VVM S320

The exact owner publicly states that myUplink diagram data are exported to CSV.
The discussion describes timestamp handling and confirms that the CSV contains
timestamped history values.

The same owner uses such CSV timestamps when analysing S2125 operation and
defrost-related behaviour.

P41 does not infer that the owner's CSV includes direct Defrost 0/1/2, BT16,
BT28 and compressor frequency in one export. The actual CSV is not publicly
attached in the audited thread.

Therefore:

`MYUPLINK_TIMESTAMPED_CSV_EXPORT = PROVEN`

but:

`PUBLIC_RAW_FOUR_SIGNAL_CSV = NOT_ACQUIRED`

Source:
- SRC-B05-P41-WPNUTZER-S2125-MYUPLINK-CSV-2024

## 5. mlinzner — S2125-12 field system

In a public OpenEnergyMonitor discussion, the exact S2125-12 owner offers
read-only myUplink viewer access. Another participant explains that such viewer
access can be logged with existing scripts and plotted.

The thread does not publish a viewer link, credential, CSV or logged dataset.

P41 neither requests nor attempts non-public access.

Therefore:

`READ_ONLY_HISTORY_ACCESS_ROUTE = OFFERED`

but:

`PUBLIC_MACHINE_READABLE_HISTORY = NOT_ACQUIRED`

Source:
- SRC-B05-P41-OEM-S2125-READONLY-VIEWER-OFFER-2025

## 6. Silkeborg / jkjaer — S2125 + S320

P35-P38 already established:
- exact S2125/S320 owner system identity;
- public co-timed electric/thermal EmonCMS history;
- private Home Assistant direct-defrost history feasibility;
- absence of direct Defrost and BT16 on the bounded public EmonCMS app/input
  surfaces.

P41 does not reclassify the private HA history as public.

A fresh 2026-09-26 read-only rerun of the existing P37 public-surface probes
recovered the same published EmonCMS read route without storing or printing
the public read key. The live result remains unchanged:
- public feeds: 13;
- direct-state candidate count: 1;
- the only candidate remains Operation Mode 501344;
- public inputs: 7;
- input names remain OutdoorTemp, FlowRate, TargetSupplyTemp, OperationMode,
  ReturnTemp, SupplyTemp and CurPwr;
- no public BT16 input;
- no public direct Defrost input.

The owner's later Home Assistant direct-defrost history therefore has not been
promoted onto the audited public EmonCMS surface as of 2026-09-26.

Sources:
- SRC-B05-OEM-S2125-MODBUS-TCP-FIELD-2024
- SRC-B05-OEM-S2125-PUBLIC-EMONCMS-APP-2024
- SRC-B05-P36-SILKEBORG-EMONCMS-METER-PROBE-2026
- SRC-B05-P37-SILKEBORG-PUBLIC-FEED-CANDIDATE-PROBE-2026
- SRC-B05-P37-SILKEBORG-PUBLIC-INPUT-INVENTORY-2026

## 7. hans1966 / hansij66 — S2125-12 + SMO S40

The exact field owner reports an S2125 + SMO S40 installation with a Kamstrup
Multical 303 and states that all measured data are routed through:

`MBUS/MODBUS -> MQTT -> InfluxDB -> Grafana`

The owner's public signature identifies the heat pump as S2125-12. The linked
public `hansij66/nibe2mqtt` implementation, pinned at
`e3922c535b2f4d23053429935dd0e898738569a7`, contains the exact target S2125
register catalogue entries for BT28/1621, BT16/1622, current compressor
frequency/1803 and direct Defrost/1805. Its parser adds a source-side timestamp
to each published value set and maintains a defrost counter using direct 1805
state, with an InfluxDB history route documented in the project.

This proves a second independent exact field system with a concrete
machine-readable multi-timestamp history pipeline whose implementation covers
all four target channels.

It does not prove that the owner's underlying Influx rows are public. Repository
history and public field posts expose implementation, graphs and operating
discussion, but no source-native four-signal raw history dump was acquired.

Therefore:

`OWNER_LOCAL_MULTITIMESTAMP_HISTORY = PROVEN`

`PUBLIC_RAW_FOUR_SIGNAL_SERIES = NOT_ACQUIRED`

Sources:
- SRC-B05-P41-HANS1966-S2125-INFLUX-HISTORY-2023
- SRC-B05-NIBE2MQTT-S2125-DIRECT-STATE-E3922C-2023

## 8. LasseCB — S2125-12 + VVM 500

The exact owner identifies an S2125-12 + VVM 500 installation and reports
reading pump data into Home Assistant. Based on values supplied by the heat
pump, the owner's history calculation can report the fraction of a day spent in
active defrost, including an observed case around 20 percent under humid
near-freezing conditions.

That result requires owner-side time history of the direct active-defrost
condition and is useful independent confirmation that exact S2125 controller
state is historized outside the previously audited Dutch/Austrian systems.

The public forum attachments are images. No Home Assistant recorder export,
CSV, database dump or source-native row set containing BT28 + BT16 + compressor
+ direct Defrost together is published in the audited thread.

Therefore:

`OWNER_LOCAL_DIRECT_DEFROST_HISTORY = PROVEN`

`PUBLIC_RAW_FOUR_SIGNAL_SERIES = NOT_ACQUIRED`

Source:
- SRC-B05-P41-LASSECB-S2125-HA-DEFROST-HISTORY-2025

## 9. schingeldi — S2125-8 + SMO S40 + EMK 500

This exact owner publicly identifies an S2125-8 controlled by an SMO S40 and
publishes source-native multi-timestamp rows from an actual export.

The posted export sample contains source-native UTC-offset timestamps, EB101-BT12
supply temperature in degC, BT25 external supply temperature in degC, and BF1
volume flow in l/min. The visible sample spans
2024-05-15T09:35:54+00:00 through 2024-05-15T09:38:45+00:00. The owner states
that exported values can arrive every 2-3 seconds.

This materially changes the bounded acquisition statement:

`PUBLIC_RAW_S2125_MULTITIMESTAMP_ROWS_ACQUIRED = TRUE`

but the published sample does not contain BT28, BT16, current compressor
frequency or direct Defrost. Targeted follow-up searches over the same owner and
thread did not locate a public export containing that four-signal target set.

Therefore:

`PUBLIC_RAW_TARGET_FOUR_SIGNAL_SERIES_ACQUIRED = FALSE`

and:

`PUBLIC_RAW_OTHER_CHANNEL_S2125_TIMESERIES != TARGET_FOUR_SIGNAL_SERIES`

The physical residual is not closed by substituting BT12/BT25/BF1 for the
required variables.

Source:
- SRC-B05-P41-SCHINGELDI-S2125-RAW-MULTITIMESTAMP-2024

## 10. Repository and fingerprint audit

P41 also checked public code/data surfaces for:
- S2125 CSV/LOG datasets;
- NIBE S2125 Influx/Grafana dumps;
- Home Assistant recorder exports;
- entity fingerprints for direct defrost and BT16;
- NibeAPI forks and repository history;
- exact four-register combinations around BT28/BT16/compressor/Defrost.

The public matches were:
- register catalogues;
- logger implementations;
- Home Assistant configurations;
- owner discussions and graphs;
- one P40 current snapshot;
- one public exact-S2125 raw multi-timestamp export sample on non-target BT12/BT25/BF1 channels.

No public raw multi-timestamp same-system four-signal row set was acquired.

The expanded public acquisition attack also covered owner-specific post
histories, GitHub repositories/issues/attachments, CSV/XLSX/TXT/JSON
fingerprints, Home Assistant recorder/history surfaces, Influx/Grafana
queries, public file-sharing links and fresh 2026 S2125 monitoring routes.
One exact-S2125 raw multi-timestamp sample was acquired on non-target
BT12/BT25/BF1 channels, while Havisoft now proves all four target signals
exist owner-side in one exact Home Assistant history environment.

Within this explicitly audited public scope:

`BOUNDED_PUBLIC_TARGET_EXPORT_SEARCH_EXHAUSTED = TRUE`

and:

`PUBLIC_RAW_TARGET_FOUR_SIGNAL_SERIES_ACQUIRED = FALSE`

This bounded result is recorded as:

`AUDITED_PUBLIC_S2125_HISTORY_SURFACES_NO_RAW_FOUR_SIGNAL_EXPORT_FOUND`

It is not:

`NO_SUCH_DATA_EXISTS`

and it is not:

`OWNER_SIDE_TARGET_HISTORY_ABSENT`

## 11. Physical residual

P41 does not rename away the physical requirement.

It remains exactly:

`S2125_MULTI_TIMESTAMP_BT28_BT16_COMPRESSOR_DEFROST_SERIES_REQUIRED`

Admissible closure still requires:
- one exact S2125 system;
- multiple source-native timestamps;
- BT28;
- BT16;
- compressor state/frequency;
- direct Defrost 0/1/2;
- common timebase;
- explicit units/scaling;
- known aggregation/cadence semantics;
- enough operating variation for a bounded weather/operating-state analysis.

A complete OFF -> ACTIVE/PASSIVE -> OFF interval is preferred because it can
also advance the separate event-package residual.

## 12. Q-B05-003

State remains:

`OPEN_NARROWED_TO_COMPLETE_RAW_EVENT_PACKAGE_MULTI_TIMESTAMP_BT16_SERIES_AND_CROSS_PRODUCT`

Residuals remain:
- S2125_COMPLETE_RAW_DIRECT_EVENT_PACKAGE_REQUIRED
- S2125_MULTI_TIMESTAMP_BT28_BT16_COMPRESSOR_DEFROST_SERIES_REQUIRED
- CROSS_PRODUCT_DEFROST_RUNTIME_COVERAGE_REQUIRED

No weather-to-BT16 model, defrost-frequency curve or event kWh is admitted.

## 13. Readiness

- DEFROST: 20% -> 20%
- B05 overall: 64% -> 64%

The acquisition uncertainty is reduced from "does exact S2125 history exist?"
to "obtain an admissible raw export from one of the proven owner-local history
surfaces." That is progress, not physical closure.

## 14. Next admissible acquisition route

The bounded public-web acquisition route is now exhausted for the target
four-signal row set without weakening the evidence gate.

The next admissible step is a targeted primary-data request to an exact S2125
owner that already has the required history. Preferred acquisition targets are:

1. Havisoft — complete BT28 + BT16 + compressor + direct Defrost history is
   proven in one exact S2125-12 + VVM S320 Home Assistant environment.
2. SvenPausH — one exact four-signal public snapshot already exists and the
   same system has owner-local InfluxDB/Grafana history.
3. Other exact owner-local history surfaces audited above if either route is
   unavailable.

The requested artifact must remain source-native and machine-readable. It must
preserve original timestamps, all four target signals, units/scaling, cadence
or sampling semantics, and preferably a complete OFF -> ACTIVE/PASSIVE -> OFF
defrost interval.

A graph, minute-bucket aggregation, screenshot, derived daily percentage or
manually transcribed values does not satisfy this residual.

No owner is contacted and no non-public access is attempted by P41.

## Public references

SvenPausH S2125/VVMS320 Influx/Grafana defrost history:
https://www.energiesparhaus.at/forum-nibe-s2125-vvms320-enteisung-2025/84233

WPNutzer exact S2125-8 + VVM S320 myUplink CSV:
https://www.energiesparhaus.at/forum-myuplink-daten-in-csv-datei-nicht-korrekt/81009

Exact S2125-12 + SMO S40 direct Defrost in InfluxDB:
https://gathering.tweakers.net/forum/list_messages/2102920/45

Havisoft exact S2125 history graph with BT28, Defrost and compressor:
https://gathering.tweakers.net/forum/list_messages/2102920/56

Havisoft later BT16 monitoring update on the same exact system:
https://gathering.tweakers.net/forum/list_messages/2102920/102

Exact S2125-12 read-only myUplink viewer offer:
https://community.openenergymonitor.org/t/nibe-s2125-12-best-heatpump-settings-for-extended-absence-during-cold-weather/27710

hans1966 exact S2125-12 + SMO S40 field history route:
https://gathering.tweakers.net/forum/list_messages/2102920/24

hansij66 pinned S2125 Modbus/MQTT/Influx implementation:
https://github.com/hansij66/nibe2mqtt/tree/e3922c535b2f4d23053429935dd0e898738569a7

LasseCB exact S2125-12 + VVM 500 Home Assistant active-defrost history:
https://www.varmepumpsforum.com/vpforum/index.php?topic=86084.msg871021

schingeldi exact S2125-8 + SMO S40 public raw multi-timestamp export sample:
https://www.haustechnikdialog.de/Forum/t/277733/Waermemenge-in-kWh-aus-NIBE-SMO-S40-EMK500-auslesen
