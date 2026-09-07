# B02-P44 — public panel radiator quantity and retrofit anchor

**State:** `PUBLIC QUANTITY EVIDENCE RECOVERED / PANEL-TAVHO SEGMENT BOUNDED / NATIONAL P42 STILL Q`

**Canonical base:** `75e2db488e376ba6a8602d36b82a5871d5aff5e2`

**Implementation date:** 2026-09-07

## 1. Purpose

P44 executes the P43 recovery intent without sending a data request.

The programme objective remains:

`HOW MANY + WHAT TYPE + KEEP/CHANGE + HOW MANY NEW UNITS -> B06`

P44 recovers already-public quantitative radiator evidence for the Hungarian panel/district-heating segment. It does not convert a convenient segment average into a national radiator stock.

Hard boundaries:

`PUBLIC RECOVERY != DATA REQUEST`

`PANEL/TAVHO SEGMENT != ALL OCCUPIED DWELLINGS`

`COST ALLOCATOR COUNT != RADIATOR COUNT UNLESS THE SOURCE BINDS THAT SEMANTIC`

`SEGMENT QUANTITY ANCHOR != NATIONAL P42 AUTHORITY`

No external source binary is committed to this public repository.

## 2. Recovered public evidence

### 2.1 BME + MaTáSzSz 2023 national district-heating survey control

Source ID:

`SRC-B02-P44-BME-MATASZ-ONEPIPE-2023`

Authority:

`https://tavho.org/uploads/hirek/Tanulma%CC%81ny%2B12.15..pdf`

Title:

`Az egycsöves átfolyós fűtési rendszerű épületek szabályozhatóvá tételének műszaki tartalma`

Prepared by BME Épületgépészeti és Gépészeti Eljárástechnika Tanszék for Magyar Távhőszolgáltatók Szakmai Szövetsége, dated 2023-09-15.

Exact locators and bounded claims:

- section 5.1, PDF page 25/108: 37 responding district-heating providers serve `499,738` dwellings, stated as `75.4%` of domestic residential district-heating payers;
- PDF pages 26-28/108: `257,085` one-pipe dwellings in the questionnaire population;
- one-pipe system split: `21%` original flow-through, `6%` converted flow-through to bypass, `73%` bypass;
- responding one-pipe scope: `56%` of heat emitters with thermostatic valves; cost allocation reported for `54%` of the covered one-pipe buildings/emitters as stated by the study.

This is a strong current stock control for the district-heating/one-pipe segment.

It is not a national radiator-unit count.

### 2.2 Árpádhídfő VIII exact dwelling-type radiator inventory

Source ID:

`SRC-B02-P44-ARPADHIDFO-PALYAZAT-17-2015`

Authority:

`https://arpadhidfo8.hu/arpad/szovetkezet/palyazatok_dok/palyazat_17.pdf`

Exact locator: page 1/3 of the public tender `2015-17` for the Róbert Károly krt. 12-18 buildings.

Source-native facts:

- building constructed in 1964;
- 12 stairwells;
- per stairwell: `16 x 61 m2` dwellings, `5 radiators/dwelling`;
- per stairwell: `20 x 40 m2` dwellings, `3 radiators/dwelling`;
- stated required cost allocators: `1,700`.

Reproducible derivation:

- 61 m2 dwellings: `16 * 12 = 192 dwellings`; `192 * 5 = 960 in-dwelling radiators`;
- 40 m2 dwellings: `20 * 12 = 240 dwellings`; `240 * 3 = 720 in-dwelling radiators`;
- total: `432 dwellings`, `1,680 in-dwelling radiators`;
- derived in-dwelling intensity: `1,680 / 432 = 3.888889 radiators/dwelling`;
- the source separately states `1,700` cost allocators; the `20` unit difference is kept as an explicit residual for other measured rooms and is not distributed across dwellings.

This is the strongest recovered public source in P44 for exact `floor-area class -> radiator units/dwelling` evidence.

### 2.3 Lehel 2021 implemented panel retrofit quantity

Source ID:

`SRC-B02-P44-LEHEL-PANEL-RETROFIT-2021`

Authority:

`https://green-brands.hu/2022/01/07/az-otthon-melege-is-lehet-kornyezetbarat/`

Exact locator: paragraph describing the Lehel group 2021 Otthon Melege works.

Observed project facts:

- `14 buildings`;
- `2,122 dwellings` modernised;
- `3,307` new Lehel Viking radiators installed to replace old Radal radiators;
- `6,709` MOM-LEHEL cost allocators installed.

Bounded derived diagnostics:

- cost-allocator intensity: `6,709 / 2,122 = 3.161640 per dwelling`;
- observed replacement-radiator intensity: `3,307 / 2,122 = 1.558435 per dwelling`;
- replacement units / allocator positions: `3,307 / 6,709 = 0.492920`.

The last ratio is a project diagnostic only. The source does not prove that every allocator position is exactly the same universe as every existing radiator position; therefore P44 does not relabel `6,709` cost allocators as `6,709 existing radiators` and does not export `49.292%` as a national replacement share.

The `3,307` replacement radiators themselves are a real implemented physical quantity.

### 2.4 Baj 2024 public 30-dwelling reference building

Source ID:

`SRC-B02-P44-BAJ-TECHEM-REFERENCE-2024`

Authority:

`https://baj.hu/wp-content/uploads/2021/09/2024.12.10-i-kozmeghallgatassal-egybekotott-jkv.pdf`

Exact locator: `1. sz melléklet`.

The public reference case states:

- five-storey two-pipe building;
- manual radiator valves;
- `30 dwellings`;
- `110` Techem FHKV radio 4 cost allocators.

Derived reference intensity:

`110 / 30 = 3.666667 cost-allocator positions/dwelling`.

The document labels it a sample/reference building, so this is `DER / REFERENCE_CASE`, not an observed municipal stock population.

### 2.5 Pécs existing RADAL case — type, count and low-temperature reuse

Source ID:

`SRC-B02-P44-PTE-EPKO-RADAL-2025`

Authority:

`https://ojs.emt.ro/EPKO/article/download/2032/2100/3148`

Exact locators: PDF pages 2-4/6.

The engineering case study documents an existing Pécs panel building with:

- room heating by one-pipe system;
- `RADAL 600` radiators;
- actual examples `RADAL 600-9`, `600-10`, `600-11`, `600-22`;
- every dwelling in the studied configuration has `3` separate flow/return paths to `3 radiators`;
- kitchen and bathroom have pipe emitters, so `3 radiators != total heat-emitter units`.

The study also recalculates the same existing radiators after envelope retrofit:

- full structural retrofit case at `55 C` supply temperature: the table evaluates each existing RADAL radiator against the reduced room heat need and concludes that central temperature reduction can closely fit the remaining load without in-dwelling emitter replacement in the studied fully-retrofitted case, subject to hydraulic conditions;
- partial structural retrofit case at `70 C`: the lowest-floor room can require additional intervention, including a larger radiator.

This directly supports P42's programme logic:

`ENVELOPE RETROFIT -> ROOM HEAT LOSS -> EXISTING RADIATOR OUTPUT AT TARGET TEMPERATURE -> KEEP/CHANGE`

It does not establish a national reuse share.

### 2.6 BME/MaTáSzSz design-reference unit counts

The 2023 BME/MaTáSzSz study also contains source-bounded design examples based on supplied building documentation.

For the A-A 10-storey example, section 6.2 / PDF pages 48-59/108 reports:

- `200` cost allocators;
- `200` thermostatic valve heads;
- `RADAL 600`;
- cost schedule with `110` standard bypass conversions and `90` reverse-flow bypass conversions, reconciling to `200` radiator positions.

Other examples publish `75`, `154`, and `35` cost-allocator/radiator-position quantities.

These are engineering layout controls. P44 does not infer a dwelling denominator when the same source table does not publish one.

## 3. Cost-allocator semantics

Supporting public service explanation:

`https://morho.hu/tavho-szolgaltatas/hasznos-tudnivalok/`

Mórhő explains that cost allocators are fitted to radiators and that correct building-level allocation aims to equip every radiator, while noting that some non-radiator emitters such as bathroom pipe emitters cannot be fitted with such devices.

Therefore P44 uses cost-allocator counts as a **heat-emitter/radiator-position quantity control only where the source context supports it**.

It never applies the false global rule:

`1 COST ALLOCATOR == 1 RADIATOR IN EVERY BUILDING`

## 4. What P44 has actually resolved

P44 materially improves the radiator branch with real public quantities:

1. a large current district-heating denominator (`499,738` dwellings, 75.4% coverage);
2. an exact current-ish one-pipe stock control (`257,085` dwellings in the 2023 survey);
3. exact panel dwelling-type radiator counts (`40 m2 -> 3`, `61 m2 -> 5`);
4. an implemented 2,122-dwelling retrofit with exact `3,307` replacement radiators;
5. a current public 30-dwelling/110-position reference;
6. an existing RADAL case with exact radiator configurations and explicit `3 radiators/dwelling`;
7. a real engineering calculation showing when existing radiators can stay after envelope retrofit and when additional emitter intervention becomes necessary.

This is not merely a recovery-route catalogue. Numeric evidence has been recovered and bound.

## 5. What remains open

The five P42 national rows remain `Q` because P44 covers a strong but bounded panel/district-heating segment and engineering references, not the complete occupied stock.

Still open nationally:

- radiator-heated dwelling count across district, central-gas, central-solid-fuel and other hydronic systems;
- installed radiator unit count outside the bounded panel controls;
- complete material/type/size distribution, especially detached houses and traditional multi-family buildings;
- national post-envelope reuse/upgrade classification;
- national replacement quantity.

Hard boundary:

`P44 PANEL QUANTITY EVIDENCE != COMPLETE NATIONAL RADIATOR INVENTORY`

## 6. Next blocker target

P44 removes the need to keep searching blindly inside the panel/távhő segment. The next search target is the **non-district central-hydronic residential segment**, especially detached houses:

- gas-boiler + radiator homes;
- solid-fuel/central-boiler + radiator homes;
- traditional multi-family central heating.

The target evidence remains physical:

`DWELLING/ARCHETYPE -> RADIATOR UNIT COUNT -> TYPE/SIZE -> POST-RETROFIT KEEP/CHANGE`

No data request is part of this route. Only already-public/recoverable evidence is admissible for the next search slice.
