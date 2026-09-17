# B02-P52 — residential radiator schedule recovery

**State:** `EXACT RESIDENTIAL TYPE-SIZE-QUANTITY SCHEDULE MATERIALIZED / DESIGN-PROCUREMENT EVIDENCE ONLY / NATIONAL P42 STILL Q`

**Canonical base:** `e16fcc27461a2eb9b9ad40f5f8be74298659dc40`

**Implementation date:** 2026-09-17

## 1. Purpose

P52 continues the P50-P51 radiator branch by recovering a genuinely filled residential mechanical schedule rather than another schema-only requirement or isolated listing.

The recovered public SZOVA procurement/design documents describe an eight-dwelling residential development at:

`9700 Szombathely, Szőllősi sétány, hrsz. 8665/1`

They publish exact source-native radiator type/size/count rows for the first four dwellings as one aggregate schedule and for dwellings 5-8 individually.

P52 materializes these rows as bounded design/procurement evidence only.

Hard boundary:

`FILLED RESIDENTIAL RADIATOR SCHEDULE != CURRENT INSTALLED-STOCK CENSUS`

`NEW-BUILD DESIGN QUANTITY != PRE-RETROFIT STOCK QUANTITY`

`8-DWELLING COHORT != NATIONAL P42 AUTHORITY`

`BOUNDED 53/8 RATIO != NATIONAL RADIATORS-PER-DWELLING WEIGHT`

## 2. Source identity and residential scope

Primary public procurement page:

`https://www.szova.hu/KoZBESZERZeS/Kozbeszerzesi_eljarasok.html`

The SZOVA procurement publication identifies the project as residential development at the Szőllősi sétány 8665/1 parcel.

Recovered mechanical schedules are dated `2017-06-22` and identify the project as `4+4 lakásos társasház`.

### First stage — dwellings 1-4

Mechanical schedule:

`https://www.szova.hu/editor_up/3_%20Gepesz%20kvt%20-%201%20uetem.pdf`

Exact radiator schedule locator: PDF central-heating section, items `2.6-2.16`.

Technical description:

`https://www.szova.hu/editor_up/Muleiras%20utcai%20epuelet.pdf`

The technical description states that the building has one radiators/floor-heating circuit; floor heating is present only in dwelling 2 and not everywhere in that dwelling. The radiator circuit design temperature is `70/50 °C`; the floor-heating circuit is `38/32 °C`. It identifies the panel emitters as VOGEL&NOOT VONOVA and towel radiators as VOGEL&NOOT DELLA.

### Second stage — dwellings 5-8

Dwelling 5:

`https://www.szova.hu/editor_up/3_1%20%20Gepesz%20%205_sz_%20lakas%202%20uetem.pdf`

Exact radiator schedule locator: PDF p5, items `2.3-2.7`.

Dwelling 6:

`https://www.szova.hu/editor_up/3_2%20%20Gepesz%20%206_sz_%20lakas%202%20uetem.pdf`

Exact radiator schedule locator: PDF p4, items `2.3-2.8`.

Dwelling 7:

`https://www.szova.hu/editor_up/3_3%20%20Gepesz%207_sz_%20lakas%202%20uetem.pdf`

Exact radiator schedule locator: PDF p5, items `2.3-2.7`.

Dwelling 8:

`https://szova.hu/editor_up/3_4%20%20Gepesz%20%208_sz%20lakas%202%20uetem%281%29.pdf`

Exact radiator schedule locator: central-heating table, items `2.3-2.8`.

Second-stage technical description:

`https://szova.hu/editor_up/Muleiras%20udvari%20epuelet.pdf`

It states that every second-stage dwelling has a radiator/floor-heating circuit, that floor heating is present in every courtyard dwelling, and that the radiator circuit design temperature is `70/50 °C`, with `38/32 °C` for floor heating. It also identifies VONOVA panel radiators and DELLA towel radiators.

Therefore the complete eight-dwelling cohort is classified as:

`HYBRID_RADIATOR_FLOOR`

This classification is deliberately conservative: stage 1 is radiator-dominant and only dwelling 2 contains floor heating, while stage 2 contains floor heating in all four dwellings.

## 3. Exact recovered radiator schedule

### Dwellings 1-4 aggregate

| Type-size token | Quantity |
|---|---:|
| 11KV-600-400 | 6 |
| 11KV-600-520 | 3 |
| 11KV-600-600 | 3 |
| 22KV-600-600 | 1 |
| 22KV-600-720 | 5 |
| 22KV-600-800 | 1 |
| 22KV-600-920 | 2 |
| 22KV-600-1200 | 1 |
| 22KV-600-1400 | 1 |
| 33KV-900-520 | 1 |
| DELLA-1100x600 | 4 |

Total: `28` radiators = `24` panel + `4` towel.

### Dwelling 5

- 22KV-600-800: 1
- 22KV-600-920: 1
- 22KV-600-1000: 1
- 22KV-600-1120: 1
- DELLA-1100x600: 1

Total: `5` radiators.

### Dwelling 6

- 11KV-600-400: 1
- 22KV-600-520: 1
- 22KV-600-600: 1
- 22KV-600-920: 1
- 22KV-600-1120: 1
- DELLA-1100x600: 1

Total: `6` radiators.

### Dwelling 7

- 11KV-600-400: 1
- 22KV-600-800: 2
- 22KV-600-920: 1
- 22KV-600-1000: 2
- DELLA-1100x600: 2

Total: `8` radiators.

### Dwelling 8

- 22KV-600-520: 1
- 22KV-600-720: 1
- 22KV-600-800: 1
- 22KV-600-1000: 1
- 22KV-600-1120: 1
- DELLA-1100x600: 1

Total: `6` radiators.

## 4. Eight-dwelling bounded cohort totals

Exact recovered total:

`28 + 5 + 6 + 8 + 6 = 53 radiators`

Composition:

- panel steel: `44`
- towel radiators: `9`

Panel configuration counts:

- `11KV`: `14`
- `22KV`: `29`
- `33KV`: `1`

Exact type-size counts:

| Type-size token | Quantity |
|---|---:|
| 11KV-600-400 | 8 |
| 11KV-600-520 | 3 |
| 11KV-600-600 | 3 |
| 22KV-600-520 | 2 |
| 22KV-600-600 | 2 |
| 22KV-600-720 | 6 |
| 22KV-600-800 | 5 |
| 22KV-600-920 | 5 |
| 22KV-600-1000 | 4 |
| 22KV-600-1120 | 3 |
| 22KV-600-1200 | 1 |
| 22KV-600-1400 | 1 |
| 33KV-900-520 | 1 |
| DELLA-1100x600 | 9 |

The bounded arithmetic ratio is:

`53 / 8 = 6.625 radiators per dwelling`

P52 permits this ratio only as a cohort diagnostic. It is not a stock weight and cannot be applied to Hungarian dwelling counts.

## 5. Why this is useful

P52 materially improves the type/size side of the radiator model because it provides a complete filled schedule with:

- residential building scope;
- eight known dwellings;
- exact manufacturer/product family;
- panel configuration token;
- source-native height and length encoded in the type-size token;
- exact quantities;
- explicit radiator design temperature (`70/50 °C`);
- disclosed coexistence of floor heating.

This is stronger than a property advertisement or single-house anecdote for validating type-size parsers, configuration classes, product mapping and bounded quantity logic.

It can support later engineering work such as:

`TYPE/SIZE TOKEN -> PRODUCT PERFORMANCE TABLE -> OUTPUT AT TARGET WATER TEMPERATURE`

But it does not answer:

`WHAT IS CURRENTLY INSTALLED NATIONALLY?`

and it does not create a pre-retrofit KEEP/UPSIZE/CHANGE result because these are planned new-installation schedules.

## 6. Executable fail-closed contract

`modules/B02/residential_radiator_schedule_recovery.py` provides:

- `ResidentialRadiatorScheduleRow`;
- `ResidentialRadiatorScheduleSummary`;
- `validate_residential_radiator_schedule_row()`;
- `summarize_residential_radiator_schedule()`;
- explicit current-stock and national-P42 non-authority helpers.

The gate rejects:

- non-residential rows;
- non-design installation status;
- undisclosed hybrid heating scope;
- non-positive counts;
- missing type-size/product/source identity;
- current-installed-stock promotion;
- pre-retrofit-stock promotion;
- national P42 authority promotion;
- self-authorized programme use;
- cross-cohort pooling;
- duplicate evidence rows;
- inconsistent coverage denominators.

## 7. P42 effect

All five P42 national claims remain:

`Q / programme_use_allowed=NO`

P52 does **not** resolve:

- national radiator-heated dwelling count;
- national installed radiator unit count;
- representative current national type/size distribution;
- stock-level KEEP/UPSIZE/CHANGE share;
- national replacement quantity.

What it resolves is narrower and real:

`PUBLICLY RECOVERED FILLED RESIDENTIAL TYPE-SIZE-QUANTITY SCHEDULE = YES`

That is evidence progress, not a governance-only slice.

No source binary is committed to the repository.
