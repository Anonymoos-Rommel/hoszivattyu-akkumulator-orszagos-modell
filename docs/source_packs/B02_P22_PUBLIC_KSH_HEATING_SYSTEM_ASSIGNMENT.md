# B02-P22 — Public KSH current heating-system assignment

**Status:** `SOURCE-NATIVE HEATING SYSTEM QUALIFIED / EMITTER AND DESIGN TEMPERATURE STILL Q`

**Base:** B02-P21 merged main `e80743e81472ae1c8f780852a37f066b816d91f0`

**Audit date:** 2026-09-06

## Purpose

P21 qualified the populated current-stock archetype without promoting model output to observation. P22 uses the already-materialized 2022 KSH Census WBL011 full occupied-stock joint to recover the current heating-system topology at the same exact `cell_id` grain.

Canonical boundary:

`CURRENT HEATING SYSTEM TOPOLOGY != CURRENT HEAT EMITTER != CURRENT DESIGN TEMPERATURE != HYDRAULIC READINESS`

P22 does not infer radiators, surface heating, convectors, stoves, supply temperature, return temperature or technical eligibility.

## Source

Canonical source remains:

- `SRC-B02-KSH-CENSUS-API-2022`;
- WBL011 / V67;
- reference year 2022;
- universe `LAKAS_OCS=DW_OC`;
- materialized projection `WBL011_FULL_STOCK_JOINT`;
- exact 116,452 returned positive OBS rows;
- exact 4,008,541 occupied dwellings.

Official KSH Census 2022 definitions distinguish:

- district heating;
- central heating in a multi-dwelling building;
- central heating per dwelling;
- room-by-room heating, which includes heating by convector, stove or other device and also dwellings where heating equipment/conditions were absent at enumeration.

Public definition page:
`https://nepszamlalas2022.ksh.hu/fogalmak`

The public Census preliminary publication independently shows the same four heating-mode concepts by settlement type. This is a semantic/control surface, not a replacement for the pinned WBL011 rows:
`https://nepszamlalas2022.ksh.hu/eredmenyek/elozetes-adatok-2/kiadvany/assets/nepszamlalas2022-elozetesadatok-2.pdf`

## Executable assignment

`modules/B02/heating_system_assignment.py`

The runtime consumes only the committed WBL011 full-joint rows and preserves their source-native heating-mode and heating-fuel fields.

For the present claim it uses the minimum semantic partition:

- `HEAT111`, `HEAT112` -> `CENTRAL_HEATING`;
- `HEAT12` -> `DISTRICT_HEATING`;
- `NHEAT` -> `ROOM_BY_ROOM_OR_NO_HEAT`.

`HEAT12` is already canonical in B01 as district heating. P22 intentionally keeps `HEAT111` and `HEAT112` together because a finer distinction is unnecessary for the emitter-readiness question and would add no new evidence.

Every output row remains bound to the original WBL `cell_id`, dwelling count, heating-mode code/name and heating-fuel code/name.

The deterministic topology transform is `DER`.

## Why this is useful

Before P22, the two remaining readiness blockers were discussed as if all 4,008,541 occupied dwellings had equally unknown heating context.

P22 proves that this is too coarse. The public Census already partitions the complete occupied stock by heating topology at exact WBL grain. Downstream investigation can therefore be targeted separately at:

- central-heating cells;
- district-heating cells;
- room-by-room/no-heat cells.

This materially narrows the emitter evidence problem without inventing an emitter.

## Why the heat-emitter blocker remains open

The Census heating-mode categories do not identify a complete current emitter inventory.

In particular:

- central heating does not prove radiator versus floor/wall/other heat emitter;
- district heating does not prove the in-dwelling emitter;
- room-by-room heating explicitly covers convector, stove or other devices and also the no-heating-equipment case;
- heating fuel does not uniquely identify the emitter.

Therefore:

`FUTES_TOH OBS + FUTAGOK OBS -> HEATING SYSTEM DER`

but not:

`-> CURRENT HEAT EMITTER OBS/DER`

P18 direct-authority requirements remain unchanged and `NO_CURRENT_HEAT_EMITTER_EVIDENCE` stays open.

## Why design temperature remains open

No WBL011 field provides current design supply/return temperature. P22 therefore makes no temperature assignment and does not use the 55/45 C reference assumption as current-building evidence.

`NO_CURRENT_DESIGN_TEMPERATURE_EVIDENCE` stays open.

## External survey control

KSH STADAT 14.8.2.2 publishes a 2022 household-survey heating-mode distribution by region and settlement type with finer fuel distinctions such as gas/other central heating and gas/electric/other room heating:
`https://www.ksh.hu/stadat_files/jov/hu/jov0048.html`

P22 does **not** use those survey percentages to overwrite or allocate the Census WBL cells. They remain an optional external plausibility/control surface only because their survey universe and grain differ from the complete Census occupied-stock joint.

## Current state after P22

- `CURRENT_STOCK_ARCHETYPE_ASSIGNMENT = QUALIFIED` from P21;
- `CURRENT_HEATING_SYSTEM_ASSIGNMENT = QUALIFIED_SYSTEM_ONLY`;
- `heat_emitter_status = Q`;
- `design_temperature_status = Q`;
- `TECHNICAL_READINESS_ARCHETYPE = Q`;
- blockers remain exactly:
  - `NO_CURRENT_HEAT_EMITTER_EVIDENCE`;
  - `NO_CURRENT_DESIGN_TEMPERATURE_EVIDENCE`.

OÉNY remains `SENT_2026-08-22 / AWAITING_RESPONSE`. The KSH custom building-type request remains `SENT_2026-09-06 / AWAITING_RESPONSE`; neither response is required for this P22 public-data assignment.

No readiness percentage uplift is inferred merely from this topology layer.
