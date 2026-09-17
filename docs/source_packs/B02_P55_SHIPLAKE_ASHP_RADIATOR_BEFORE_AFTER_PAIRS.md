# B02-P55 — CHO-612 Shiplake Lock residential ASHP radiator before/after pairs

**State:** `ROOM-GRAIN CURRENT->PROPOSED ASHP RADIATOR PAIRS RECOVERED / SOURCE-NATIVE FLOW+MWT / EXACT-DERIVED RETURN / DESIGN AUTHORITY ONLY / NOT COMMISSIONED / NOT HUNGARIAN STOCK AUTHORITY`

**Canonical base:** `e107b4ca8e550147462328b6f0843ea397199545`

**Implementation date:** 2026-09-17

## 1. Purpose

P55 closes the heat-pump-specific evidence gap left explicit by P54:

`DISTRICT-HEATING RETROFIT DESIGN != HEAT-PUMP RETROFIT EVIDENCE`.

P55 uses the CHO-612 — Shiplake Lock Heat Engineer / RetrofitWorks residential design report published as a UK Contracts Finder attachment.

Primary source:

`https://www.contractsfinder.service.gov.uk/Notice/Attachment/5d92f026-b38f-4ca0-ac01-38c3a143a288`

The report is a single residential ASHP design package containing:

- `Heating Type: ASHP`;
- whole-building heat-source requirement: `9.85 kW`;
- design external temperature: `-1.8 °C`;
- heat-pump output at design conditions: `10 kW`;
- maximum designed flow temperature: `50 °C`;
- room-by-room heat loss;
- Appendix L — `Current Radiators` with room, type, height, length and output;
- Appendix O — `New Radiators` with the same room grain, room heat loss, new radiator type/dimensions and output;
- explicit `Mean (Flow/Return) Water Temperature`: `46.5 °C`.

## 2. Temperature provenance contract

The source explicitly publishes:

`FLOW_TEMP = 50 °C — SOURCE_NATIVE`

and:

`MWT = 46.5 °C — SOURCE_NATIVE`.

The source does **not** print a separate return-temperature field in the recovered schedule.

Because the source explicitly defines MWT as the mean of flow and return:

`MWT = (FLOW + RETURN) / 2`

therefore:

`RETURN = 2 * 46.5 - 50 = 43 °C`.

P55 freezes the provenance as:

`RETURN_TEMP = 43 °C — EXACT_DERIVED_FROM_SOURCE_NATIVE_FLOW_AND_MWT`.

Hard boundary:

`EXACT DERIVATION FROM TWO SOURCE-NATIVE INPUTS != SOURCE-NATIVE RETURN FIELD`.

The validator therefore rejects any claim that the 43 °C return value was literally printed by the source.

## 3. Exact room-grain current -> proposed pairs

P55 materializes ten exact room-grain pairs from the dwelling.

| Room | Current radiator | Room heat loss | Proposed radiator(s) | Output @ 46.5 °C MWT |
|---|---|---:|---|---:|
| Boot Room / Rear Lobby | K1 600x700 | 816.72 W | K3 700x700 | 913 W |
| Lounge | P+ 600x1280 | 1275.03 W | P+ 600x2100 | 1269 W |
| Lounge part 2 | P+ 600x1280 | 1150.04 W | P+ 600x2000 | 1208 W |
| Kitchen | K2 600x800 | 1256.48 W | K2 600x800 + K2 600x400 + K2 600x500 | 1441 W |
| Entrance Hall | P+ 600x700 | 582.46 W | P+ 750x700 | 593 W |
| Toilet 1 | K1 600x410 | 226.24 W | K1 600x500 | 231 W |
| Bathroom 1 | Double panel no fins 590x480 | 599.92 W | P+ 450x1400 | 626 W |
| Bedroom 1 | Double panel no fins 590x1350 | 1017.73 W | retained 590x1350 + P+ 500x600 | 1031 W |
| Bedroom 2 | P1 600x1280 | 825.29 W | P+ 600x1200 | 838 W |
| Bedroom 3 | P1 600x1280 | 776.18 W | retained P1 600x1280 + P1 600x1100 | 790 W |

These rows demonstrate multiple ASHP emitter outcomes at one common low-temperature design basis:

- type change;
- dimensional upsize;
- retained emitter plus additional emitter;
- multi-emitter room design;
- same-type resize.

## 4. Fail-closed room-level adequacy rule

P55 does **not** infer compliance from an aggregate positive margin.

Nine of the ten materialized room rows meet or exceed the source-native room heat loss at the source-native 46.5 °C MWT.

The Lounge row does not:

- source-native room heat loss: `1275.03 W`;
- source-native proposed radiator output: `1269 W`;
- exact difference: `-6.03 W`.

This row is intentionally preserved without rounding, normalization or silent promotion.

Hard boundary:

`AGGREGATE DWELLING OUTPUT MARGIN > 0 != EVERY ROOM MEETS DESIGN HEAT LOSS`.

and:

`1269 W < 1275.03 W -> ROOM-LEVEL DEFICIT RETAINED`.

P55 therefore supports an explicit room-level fail-closed adequacy gate.

## 5. Bounded quantitative result

Inside the ten-row materialized cohort:

- dwellings represented: **1**;
- exact room pairs: **10**;
- rooms meeting/exceeding heat loss: **9**;
- rooms below heat loss: **1**;
- summed room heat loss: **8526.09 W**;
- summed proposed output at 46.5 °C MWT: **8940 W**;
- aggregate margin: **+413.91 W**;
- maximum designed flow temperature: **50 °C**;
- custom MWT: **46.5 °C**;
- exact-derived return temperature: **43 °C**.

These figures are valid only for this dwelling and these ten rows.

## 6. Authority gained by P55

P55 is materially stronger than P54 on one axis:

`P54 LOWER-TEMPERATURE RESIDENTIAL DESIGN PRECEDENT`

`-> P55 RESIDENTIAL ASHP DESIGN PRECEDENT`.

P55 therefore qualifies as bounded **ASHP DESIGN authority** for the documented dwelling and room pairs.

It does not qualify as:

- implementation authority;
- commissioning authority;
- post-install measured performance authority;
- Hungarian housing-stock authority;
- national emitter-replacement fraction authority;
- national P42 programme-use authority.

Canonical boundaries:

`UK RESIDENTIAL ASHP DESIGN != HUNGARIAN RESIDENTIAL STOCK`

`ONE DWELLING != REPRESENTATIVE POPULATION SAMPLE`

`DESIGN REPORT != INSTALLED / COMMISSIONED OUTCOME`

`ASHP DESIGN PAIRS != NATIONAL REPLACEMENT FRACTION`

`BOUNDED ENGINEERING PRECEDENT != PROGRAMME POPULATION WEIGHT`.

All national P42 radiator claims therefore remain fail-closed unless separately supported by population evidence.

## 7. Why this matters to the original programme

P55 supplies the strongest recovered evidence so far for the per-dwelling emitter decision engine shape:

`ROOM HEAT LOSS`

`+ CURRENT EMITTER TYPE/SIZE`

`+ ASHP TARGET WATER-TEMPERATURE BASIS`

`-> KEEP / UPSIZE / CHANGE / ADD`

`-> PROPOSED ROOM EMITTER OUTPUT`

`-> ROOM-LEVEL ADEQUACY CHECK`.

This is directly relevant to the original national programme architecture because it demonstrates the data and validation path required before a dwelling can be classified as hydraulically/emitter-ready for an ASHP transition.

It still does not provide Hungarian prevalence or national scaling weights.

## 8. Repository contract

`modules/B02/ashp_radiator_before_after_pairs.py` provides:

- `AshpRadiatorBeforeAfterPair`;
- `AshpRadiatorPairSummary`;
- `validate_ashp_radiator_before_after_pair()`;
- `summarize_ashp_radiator_before_after_pairs()`;
- explicit authority helpers that grant only bounded ASHP design authority and reject implementation, commissioning, Hungarian-stock and national-P42 promotion.

`registry/b02_p55_shiplake_ashp_radiator_before_after_pairs.csv` materializes exactly ten room pairs.

No external source binary is committed.
