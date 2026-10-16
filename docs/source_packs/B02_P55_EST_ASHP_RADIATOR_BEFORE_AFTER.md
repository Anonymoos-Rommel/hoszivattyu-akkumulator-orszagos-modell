# B02-P55 — EST / EA Technology ASHP radiator before/after pairs

**State:** `CONTROLLED RESIDENTIAL TEST-HOUSE ASHP IMPLEMENTATION + EXACT ROOM-GRAIN ORIGINAL->UPGRADED RADIATOR PAIRS + EXPLICIT 45/35 C OPERATING BASIS / NOT OCCUPIED-HOUSEHOLD SAMPLE / NOT HUNGARIAN STOCK AUTHORITY`

**Canonical base:** `e107b4ca8e550147462328b6f0843ea397199545`

**Implementation date:** 2026-09-17

## 1. Purpose

P55 closes the heat-pump-specific evidence target left open by P54:

`RESIDENTIAL + ASHP + SAME ROOM + EXISTING RADIATOR TYPE/SIZE + UPGRADED RADIATOR TYPE/SIZE + EXPLICIT FLOW/RETURN + OUTPUT`.

Primary source:

`https://assets.publishing.service.gov.uk/media/5a78de7840f0b62b22cbd718/3531-effect-radiator-valves-heat-pump-perf.pdf`

EA Technology Consulting / Energy Saving Trust, Report No. 6507, **The effect of Thermostatic Radiator Valves on heat pump performance**, June 2011.

## 2. Source status

The report states that a typical fixed-speed **air source heat pump** was installed in one of EA Technology's thermally matched Test Houses. The selected building is described as a detached, four-bedroom, two-storey test house built to a mid-1990s residential specification. The report publishes:

- whole-house design heat loss: **4.4 kW** at -1 C external / 21 C internal;
- installed ASHP nominal capacity: **6 kW**;
- original radiator schedule by room;
- upgraded radiator schedule by the same room names;
- explicit low-temperature operating condition **45/35/20 C** used to assess the original radiator system;
- target ASHP flow range of 40-50 C and target redesign flow of 50 C;
- measured flow and return temperatures in the installed system;
- a selected return-temperature set-point of **40 C** for the cycling tests.

P55 uses **45/35 C** as the exact low-temperature radiator comparison basis because the report explicitly states that operating condition when explaining why the original radiator system was inadequate and why the upgraded schedule was required.

## 3. Original radiator schedule

The original system was specified by British Gas for a 9 kW condensing gas boiler with a stated boiler flow temperature of **82 C** in cold design conditions. The source does not publish an exact original return temperature for the original schedule.

Therefore P55 stores the original output basis as:

`SOURCE_ORIGINAL_BOILER_SCHEDULE_82C_FLOW_RETURN_UNSPECIFIED`.

This prevents an unsupported old-output temperature normalization.

The source-native original rows are:

| Room | Original type | Size mm | Original schedule output W |
|---|---|---:|---:|
| Lounge | Stelrad Elite P1 | 1400 x 600 | 1225 |
| Dining | Stelrad Elite P1 | 900 x 600 | 814 |
| Kitchen | Stelrad Elite P1 | 700 x 600 | 920 |
| Utility | Stelrad Elite P1 | 400 x 450 | 297 |
| Hall | Stelrad Elite P1 | 700 x 450 | 499 |
| Landing | Stelrad Elite P1 | 400 x 450 | 297 |
| Bathroom | Stelrad Elite P1 | 500 x 600 | 472 |
| Bedroom 1 | Stelrad Elite P1 | 500 x 600 | 472 |
| En-suite | Stelrad Elite P1 | 400 x 600 | 384 |
| Bedroom 2 | Stelrad Elite P1 | 400 x 600 | 384 |
| Bedroom 3 | Stelrad Elite P1 | 400 x 600 | 384 |
| Bedroom 4 | Stelrad Elite P1 | 400 x 450 | 297 |

Source total: **6.445 kW**.

The report separately states that at **45/35/20 C** the original radiator system would deliver only **1.6 kW**, materially below the house requirement.

## 4. Upgraded low-temperature radiator schedule

The report states that the radiators were upgraded while retaining the original plumbing, using larger sizes and K2 radiators where required.

| Room | Upgraded type | Size mm | Output W | Room design C |
|---|---|---:|---:|---:|
| Lounge | Myson Select Standard K2 | 1600 x 700 | 993 | 21 |
| Dining | Myson Select Standard K2 | 1200 x 700 | 745 | 21 |
| Kitchen | Stelrad Elite P1 | 400 x 700 | 194 | 18 |
| Utility | Myson Select Standard K2 | 800 x 700 | 496 | 18 |
| Hall | Myson Select Standard K2 | 1200 x 700 | 745 | 18 |
| Landing | Stelrad Elite P1 | 400 x 450 | 57 | 18 |
| Bathroom | Stelrad Elite P1 | 500 x 600 | 57 | 22 |
| Bedroom 1 | Myson Select Standard K2 | 1400 x 600 | 765 | 18 |
| En-suite | Stelrad Elite P1 | 400 x 600 | 74 | 22 |
| Bedroom 2 | Myson Select Standard K2 | 1400 x 600 | 765 | 18 |
| Bedroom 3 | Myson Select Standard K2 | 1400 x 600 | 765 | 18 |
| Bedroom 4 | Myson Select Standard K2 | 1400 x 600 | 765 | 18 |

Source total: **6.421 kW**.

The source identifies K2 as double-panel, double-finned and notes that some Stelrad Elite P1 radiators were not changed.

## 5. Exact pair result

The two source tables join exactly on room name. P55 therefore materializes **12 room-grain old->new pairs**.

Within this bounded test-house cohort:

- 12 paired room positions;
- **9** rooms change type and/or physical dimensions;
- **3** retain the same physical type/dimensions;
- original schedule total = **6.445 kW** on its legacy source basis;
- original system output at **45/35/20 C** = **1.6 kW** aggregate;
- upgraded schedule total = **6.421 kW** on the low-temperature redesign basis;
- whole-house design heat loss = **4.4 kW**;
- installed ASHP nominal capacity = **6 kW**.

This is direct heat-pump-specific evidence for the programme chain:

`EXISTING ROOM RADIATOR -> LOW-TEMPERATURE ASHP CHECK -> KEEP / RESIZE / CHANGE`.

## 6. Critical boundaries

P55 deliberately freezes these non-equivalences:

`CONTROLLED RESIDENTIAL TEST HOUSE != OCCUPIED HOUSEHOLD SAMPLE`

`UK ASHP ENGINEERING PRECEDENT != HUNGARIAN RADIATOR STOCK WEIGHT`

`TWELVE ROOM PAIRS != NATIONAL REPLACEMENT FRACTION`

`ORIGINAL SCHEDULE OUTPUT AT LEGACY BOILER BASIS != ORIGINAL OUTPUT AT 45/35 C`

`AGGREGATE ORIGINAL 1.6 KW @45/35/20 != ROOM-BY-ROOM ORIGINAL LOW-TEMP OUTPUT TABLE`

`IMPLEMENTED TEST-HOUSE ASHP PRECEDENT != REPRESENTATIVE MARKET INSTALLATION SAMPLE`.

All five P42 national radiator claims remain `Q / programme_use_allowed=NO`.

## 7. Why P55 is stronger than P54 for the ASHP question

P54 recovered a clean residential room-level existing->proposed emitter mapping under lower-temperature district heating.

P55 adds the missing heat-pump-specific bridge:

- ASHP is actually installed;
- original and upgraded radiator schedules are both published;
- room names join exactly;
- type and dimensions are explicit on both sides;
- the low-temperature flow/return basis is explicit;
- system flow and return are instrumented in the test programme.

Thus P54 + P55 jointly support the engineering transformation shape while neither is allowed to create Hungarian population weights.

## 8. Reserve findings retained

### Reserve A — Octopus Energy, 24 Waterloo Crescent, Leeds

`https://docs.planning.org.uk/20240530/205/SDEUIAJBJOE00/zbfw54mb3i8m1b5y.pdf`

Very strong occupied-household ASHP design evidence. The room-level schedule publishes room heat loss, exact current radiator type/size, exact proposed radiator type/size and output, with a 50 C design flow temperature. It was not promoted as the primary P55 source because the document does **not** publish an explicit design return temperature.

### Reserve B — Jaga Surrey residential home

`https://jaga.com/uk/project/residential-home-surrey/`

Implemented homeowner ASHP case with an explicit change from **75/65 C** to **45/40 C** and replacement of old steel-panel radiators by Jaga Strada Hybrid emitters. It is useful implementation corroboration but does not publish exact old/new room-by-room dimensions.

### Reserve C — Energy Saving Trust / EA Technology source itself as measured-system evidence

The same primary report contains instrumented flow/return measurements and whole-house operation tests. P55 does not convert those time-series graphs into additional numeric room-level claims because the paired schedule already supplies the needed source-native evidence without digitizing graphs.

## 9. Repository contract

`modules/B02/ashp_radiator_before_after_testhouse.py` provides:

- `AshpRadiatorPair`;
- `AshpRadiatorPairSummary`;
- `validate_ashp_radiator_pair()`;
- `summarize_ashp_radiator_pairs()`;
- explicit non-promotion gates for occupied-household, Hungarian-stock and national-P42 authority.

`registry/b02_p55_est_ashp_radiator_before_after.csv` materializes exactly the twelve room pairs.

No external source binary is committed.
