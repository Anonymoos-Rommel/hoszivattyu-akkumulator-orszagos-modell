# 1. számú melléklet – Kért adatmezők és kutatási céljuk

**Kapcsolódó kérelem:** P1L-FINAL OÉNY pilot adatigénylés

**Pilot maximum:** 500 rekord

**Technikai keret:** a P1K OÉNY Pilot Acceptance Contract és az OÉNY readiness pilot schema 1.0. A hiányt vagy ismeretlent explicit Q, NOT_IN_SOURCE vagy NOT_STATED értékkel kérjük jelölni; imputálást nem kérünk.

| Mező neve | Rövid magyar megnevezés | Kutatási cél | Kívánt adattípus / formátum | Anonimizálási követelmény | Kötelező / opcionális | P1K acceptance ID |
|---|---|---|---|---|---|---|
| schema_version | Séma verziója | A pilot rekordjainak értelmezési és verzióazonossága | Szöveg, pontosan 1.0 | Csak technikai verziójelző | Kötelező | P1K-001 |
| pilot_record_id | Pilot technikai rekordazonosító | Rekordszintű technikai kezelés és deduplikáció | Szöveg, PILOT- + 16 hexadecimális karakter | Véletlen, nem visszafejthető; kulcstábla és linkage tilos | Kötelező | P1K-002 |
| reference_year | Referenciaév | Időbeli rétegzés és forrásidőszak rögzítése | Egész szám, 2000–2100 | Csak év; hónap és nap nem kérendő | Kötelező | P1K-003 |
| coarse_geography | Durva területi kategória | Területi rétegzés és torzításvizsgálat | Kódolt szöveg: durva régió és/vagy településtípus | Nincs cím, koordináta, helyrajzi szám vagy HET-ID | Kötelező | P1K-004 |
| building_category | Épületkategória | S0 épületarchetípus-rétegzés | Enum: FAMILY_HOUSE, MULTI_DWELLING, OTHER, NOT_STATED | Nincs cím vagy lakásazonosító | Kötelező | P1K-005 |
| construction_period_band | Építési időszak-sáv | S0 korszak szerinti rétegzés | Előre definiált kódolt sáv | Pontos építési év nem szükséges | Kötelező | P1K-006 |
| heated_floor_area_band | Fűtött alapterület-sáv | S0 energia- és archetípus-rétegzés | Előre definiált kódolt sáv | Pontos alapterület nem kérendő | Kötelező | P1K-007 |
| heating_system_quality | Fűtési rendszer energetikai minősége | S0 kiinduló energetikai kontextus | Enum: BAD, POOR, AVERAGE, GOOD, EXCELLENT, NOT_STATED | Csak kategória; tanúsítvány- és ingatlanazonosító nélkül | Kötelező | P1K-008 |
| heating_energy_carrier | Fűtési energiahordozó | S0 energiahordozó-rétegzés | Enum: GAS, ELECTRICITY, SOLID_FUEL, DISTRICT_HEAT, MULTIPLE, OTHER, NOT_STATED | Csak kategória; fogyasztási és mérőadat nem kérendő | Kötelező | P1K-009 |
| emitter_status | Hőleadó státusza | S2 hőleadó-adat bizonyítékalapjának jelölése | Enum: OBS, Q, NOT_IN_SOURCE | Nincs fotó, PDF vagy eredeti tanúsítvány | Kötelező | P1K-010 |
| emitter_types | Jelenlegi hőleadó típusa(i) | S2 műszaki readiness előfeltételének vizsgálata | Egyedi enumlista | Nincs szabad szöveg; javasolt korszerűsítés nem jelenlegi állapot | Kötelező | P1K-011 |
| emitter_evidence | Hőleadó bizonyítéktípusa | Az OBS állítás auditálhatósága | Enumlista: TEXT_EXPLICIT, TABLE_EXPLICIT, SCHEMATIC_EXPLICIT, PHOTO_EXPLICIT, NONE | Csak bizonyítékkód; kép vagy dokumentum nem kérendő | Kötelező | P1K-012 |
| temperature_status | Hőmérsékleti adat státusza | S2 tervezési vagy mért hőfokadat bizonyítékalapja | Enum: OBS, Q, NOT_IN_SOURCE | Referenciaérték nem jelölhető OBS-ként | Kötelező | P1K-013 |
| supply_temperature_c | Előremenő hőmérséklet | S2 hőfoklépcső vizsgálata | Szám vagy null, °C, −50…150 | Csak épületspecifikus, explicit érték; nem szintetikus 55/45 | Kötelező | P1K-014 |
| return_temperature_c | Visszatérő hőmérséklet | S2 hőfoklépcső vizsgálata | Szám vagy null, °C, −50…150 | Supply értékből nem számítható vissza | Kötelező | P1K-015 |
| temperature_basis | Hőmérsékleti adat alapja | Az adat megfigyelési/tervezési státuszának megkülönböztetése | Enum: DESIGN_EXPLICIT, CALCULATION_INPUT, OPERATING_MEASURED, REFERENCE_ASSUMPTION, NOT_STATED | Csak basis-kód; dokumentum nem kérendő | Kötelező | P1K-016 |
| demand_reduction_status | Keresletcsökkentési státusz | S1 before/after bizonyíték meglétének jelölése | Enum: OBS, Q, NOT_IN_SOURCE | Nincs háztartási vagy beavatkozási linkage-kulcs | Kötelező | P1K-017 |
| hydraulic_readiness_status | Hidraulikai readiness | S2 hidraulikai előfeltétel explicit bizonyítéka | Enum: OBS, Q, NOT_IN_SOURCE | Nincs tervrajz, cím vagy szabad szöveg | Kötelező | P1K-018 |
| electrical_readiness_status | Villamos readiness | S2 csatlakozási/mérési előfeltétel explicit bizonyítéka | Enum: OBS, Q, NOT_IN_SOURCE | Nincs mérőazonosító, ügyféladat vagy pontos hálózati pont | Kötelező | P1K-019 |
| permit_readiness_status | Engedélyezési readiness | S2 jogi/kivitelezési előfeltétel explicit bizonyítéka | Enum: OBS, Q, NOT_IN_SOURCE | Nincs engedélyszám, cím vagy dokumentum | Kötelező | P1K-020 |
| evidence_pages | Bizonyíték oldalszáma(i) | Dokumentumalapú OBS visszaellenőrizhetősége | Pozitív egész számok tömbje | Csak oldal/ref; PDF vagy kép nem kérendő | Opcionális | P1K-021 |
| pii_check | PII-ellenőrzés | A pilot intake adatvédelmi kapuja | Const: PASS | Név, cím, HET-ID, koordináta, kapcsolat, free text, fotó és linkage tilos | Kötelező | P1K-022 |

## Közös átadási feltételek

- Elsődleges formátum: UTF-8 CSV vagy JSON.
- Kérjük az adatszótárt, kódlistákat, mértékegységeket és az alkalmazott séma/verzió megjelölését.
- Ha valamely mező nem létezik strukturáltan, ezt kérjük külön jelezni; új adat vagy új elemzés létrehozását nem kérjük.
- Ritka kombinációk esetén suppression/generalizálás elfogadható és előnyben részesítendő; az elnyomott cella ismeretlen, nem nulla.
