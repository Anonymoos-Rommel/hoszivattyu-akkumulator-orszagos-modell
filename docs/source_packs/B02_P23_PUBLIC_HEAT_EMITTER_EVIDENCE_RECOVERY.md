# B02-P23 — PUBLIC HEAT-EMITTER EVIDENCE RECOVERY

**Audit date:** 2026-09-06 09:48–10:00 Europe/Budapest  
**Canonical base:** `cf9e8c2ea1ba8604cb17a6805cfd2c8424aa5219`  
**Purpose:** exhaust the strongest currently public emitter-relevant evidence routes before waiting for the OÉNY response or introducing any new calibrated emitter model.

## Canonical boundary

`TECHNICAL BUILDING SYSTEM DATA != CURRENT HEAT-EMITTER ASSIGNMENT`

`HEATING TOPOLOGY != RADIATOR / SURFACE-HEATING / CONVECTOR / STOVE TYPE`

`EQUIPMENT COUNT != DWELLING COUNT != WBL CELL ASSIGNMENT`

`SURVEY QUESTIONNAIRE TAXONOMY != PUBLISHED SURVEY DISTRIBUTION`

P23 does **not** alter the P18 direct-authority contract and does **not** promote any public source to stock-level current-emitter authority.

## 1. EU Building Stock Observatory — June 2026

Official European Commission page:

`https://energy.ec.europa.eu/topics/energy-efficiency/energy-performance-buildings/eu-building-stock-observatory_en`

Database:

`https://building-stock-observatory.energy.ec.europa.eu/database/`

The Commission states that the BSO:

- covers installed technical building systems;
- can be queried by topic, year and country;
- was updated with new data in June 2026;
- exposes a full XLSX dataset download route.

This is useful source discovery, but the P23 audit did **not** verify a Hungary-specific public indicator that provides a current residential distribution of the canonical emitter types (`RADIATOR`, `FLOOR_HEATING`, `WALL_HEATING`, `CEILING_HEATING`, `FAN_COIL`, `AIR_HEATING`, `DIRECT_ELECTRIC`, etc.).

Therefore:

`BSO TECHNICAL-SYSTEM COVERAGE != VERIFIED HUNGARY EMITTER DISTRIBUTION`

BSO remains a possible future source route, not current emitter authority.

## 2. KSH 2022 Household Budget and Living Conditions Survey questionnaire

Official questionnaire:

`https://www.ksh.hu/docs/hun/info/02osap/onk/2154/k222154.pdf`

Survey year: **2022**  
Reference year: **2021**

The questionnaire explicitly collects emitter-relevant subtypes.

### One-dwelling central heating (`EGYLAK`)

- gas boiler;
- mixed-fuel boiler / water-jacket fireplace;
- heat pump;
- **electric floor or wall heating**;
- electric boiler.

### Individual fixed room heating (`EGYEDI`)

- **gas convector**;
- **stove / fireplace / tile stove / cooking stove**;
- **electric storage heater**;
- **air conditioner**.

This is stronger than the Census topology because it proves that KSH has an explicit survey taxonomy for several emitter/device classes.

However the public questionnaire contains **category definitions, not national subtype counts**, and the survey is not the complete 2022 occupied dwelling stock.

Therefore:

`PUBLIC KSH EMITTER TAXONOMY != PUBLIC NUMERIC EMITTER DISTRIBUTION != COMPLETE CURRENT-STOCK ASSIGNMENT`

The row is `QUALIFIED_TAXONOMY_ONLY`.

## 3. KSH Statistical Yearbook 2022 — table 3.2.6

Official publication:

`https://www.ksh.hu/docs/hun/xftp/idoszaki/evkonyv/evkonyv_2022.pdf`

Table: **3.2.6. Data on housing by income quintiles, 2021+**.

Published national totals for the primary heating system:

- district heating: **16.0%**;
- central heating with boilers heating several apartments: **6.3%**;
- central heating for one dwelling: **48.4%**;
- individual fixed heating system: **28.9%**;
- electric or heat-pump heating systems: **2.6%**.

The table's own notes state that:

- one-dwelling central heating includes examples such as radiator, floor and wall heating;
- individual fixed heating includes examples such as convector, stove and fireplace.

Consequently the published percentages are useful as a **survey topology control**, but the categories collapse multiple emitter types.

`48.4% ONE-DWELLING CENTRAL != 48.4% RADIATOR`

`28.9% INDIVIDUAL FIXED != 28.9% GAS CONVECTOR`

The row is `QUALIFIED_CONTROL_ONLY` and cannot satisfy P18.

## 4. KSH Census 2022 / WBL011

Official database description:

`https://nepszamlalas2022.ksh.hu/en/database/`

The Census provides heating mode and heating fuel together with the WBL dimensions. P22 already materializes this source-native joint at:

- **116,452** complete WBL rows;
- **4,008,541** occupied dwellings;
- exact `cell_id` binding.

P22 proves current heating-system topology, but the Census does not split central heating into radiator/floor/wall emitters and does not split room-by-room heating into convector/stove/etc. at the WBL grain.

The row remains `QUALIFIED_SYSTEM_ONLY`.

## 5. MEHI equipment-count context

Public MEHI article:

`https://mehi.hu/lejart-a-varakozasi-idonk-nem-halogathatjuk-tovabb-az-epuleteink-felujitasat/`

MEHI states that estimates indicate approximately:

- **3 million outdated gas convectors**;
- more than **800,000 old gas boilers**

in Hungarian residential buildings.

This is useful scale context only. The statement is explicitly estimate-based and concerns **equipment counts**, not occupied-dwelling counts or a WBL-linked emitter distribution.

It must not be transformed into a stock assignment.

`3,000,000 CONVECTOR DEVICES != 3,000,000 CONVECTOR-HEATED DWELLINGS`

## P23 result

The public route is materially narrowed but the direct blocker is **not closed**.

What is now proven publicly:

1. complete current Census heating-system topology at WBL cell grain (P22);
2. KSH explicitly surveys several emitter/device subtypes;
3. public KSH result tables collapse those subtypes before publication;
4. public context confirms large legacy convector stock, but only as equipment-count estimate;
5. no verified public source in this audit provides a complete current occupied-stock emitter assignment or WBL-compatible direct binding.

Therefore canonical current state remains:

`CURRENT_HEAT_EMITTER_EVIDENCE = Q`

`NO_CURRENT_HEAT_EMITTER_EVIDENCE = OPEN`

and independently:

`NO_CURRENT_DESIGN_TEMPERATURE_EVIDENCE = OPEN`

## Next evidence route

The best next public-data investigation is **design-temperature / low-temperature-system authority**, because P23 has now demonstrated that the public emitter route reaches explicit taxonomy and topology controls but not a complete current-stock emitter distribution.

The already-sent OÉNY pilot request remains the preferred route for stronger direct emitter evidence if/when a response arrives.
