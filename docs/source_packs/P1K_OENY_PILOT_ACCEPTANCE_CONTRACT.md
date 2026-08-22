# P1-K OÉNY Pilot Acceptance Contract

**Állapot:** `CONTRACTED / NO EXTERNAL REQUEST`

**Verzió:** 2026-08-17 / v1.0

**Readiness-döntés az adatigénylési tervezetre:** `GO_FOR_REQUEST`

Ez a döntés kizárólag technikai és módszertani készenlétet jelent a P1-F tervezet Joseph általi végső engedélyezésére. Nem jelent automatikus küldést, jogi jóváhagyást, költség- vagy licencvállalást, és külső adatbekérés nem történt.

## 1. Hatály és elsőbbségi szabály

Ez a szerződés a következő két kanonikus artefaktum mezőire épül:

- [S0–S2 Evidence Gap Matrix](../../registry/b02_s0_s2_evidence_gap_matrix.csv)
- [OÉNY readiness pilot schema](../../schemas/oeny_readiness_pilot.schema.json)

Az adatbekérési tervezet a [P1-F OÉNY adatigénylési tervezet](../data_requests/P1F_OENY_DATA_REQUEST_DRAFT.md). A P1-K gépi acceptance-regisztere: [oeny_pilot_acceptance_contract.csv](../../registry/oeny_pilot_acceptance_contract.csv).

Eltérés esetén a JSON Schema gépi mező- és enum-szerződése, a gap matrix bizonyítékállapota, majd ez a P1-K elfogadási értelmezés az irányadó. A P1-K nem bővíti a pilot-sémát, és nem ír át hiányzó adatot.

## 2. Elfogadási egység és grain

A pilot elsődleges egysége egy anonimizált `pilot_record_id`-vel azonosított, durva területi, épület- és időszak-sávokkal jellemzett rekord. Ez nem jelent háztartás-azonosítást, nem jelent KSH/WBL-kulcsot, és nem teszi lehetővé ugyanazon rendeltetési egység későbbi felismerését.

A readiness-grain állapotonként eltér:

- **S0:** rekord × durva régió/településtípus × épületkategória × építési-időszak- és alapterület-sáv;
- **S1:** azonos definíciójú beavatkozás előtti/utáni rekord × fázis — a pilot ezt várhatóan nem fedi le;
- **S2:** rekord × explicit műszaki bizonyíték (hőleadó, hőmérséklet, hidraulika, villamos és engedélyezési státusz).

A margók és külön dimenziók nem keresztszorozhatók. A `Q` és `NOT_IN_SOURCE` értékek ismeretlent jelentenek, nem nullát és nem negatív bizonyítékot.

## 3. Mezőszintű acceptance-szerződés

Az alábbi táblázat a gépi regiszter rövid, auditálható kivonata. A teljes, mezőazonosítókkal kezelt szerződés a [CSV-ben](../../registry/oeny_pilot_acceptance_contract.csv) van.

| Mező | Readiness-cél / grain | Minimum minőség és hiánytűrés | Success / failure | Siker esetén is tiltott következtetés |
|---|---|---|---|---|
| `schema_version` | Szerződésverzió / minden rekord | Pontosan `1.0`; hiány 0% | 100% valid / eltérő vagy hiányzó | Tartalmi teljesség vagy reprezentativitás |
| `pilot_record_id` | Nem visszafejthető technikai ID / pilot | Pattern-valid, egyedi; hiány és duplikáció 0% | Minden ID egyedi / újrahasznált vagy dekódolható | Háztartás- vagy KSH/WBL-link |
| `reference_year` | Időbeli kontroll / rekord × év | Egész év 2000–2100; hiány nem imputálható | Valid, forrásévvel egyező / ellentmondó vagy kitalált | Országos trend vagy idősor |
| `coarse_geography` | Területi rétegzés / régió × településtípus | Durva, kódkönyvezett; cím/koordináta tilos | Kategóriák visszaolvashatók / túlfinomított vagy imputált | Országos regionális readiness vagy reprezentativitás |
| `building_category` | S0 épülettípus / rekord × kategória | Csak a séma enumja; ismeretlen `NOT_STATED` | Enum és forrásalap / szabad szöveg vagy feltételezés | Közös KSH/WBL archetípus-illesztés |
| `construction_period_band` | S0 építési kor / rekord × sáv | Előre rögzített durva sáv; ismeretlen explicit | Kódkönyv szerinti / ad hoc vagy imputált | Országos korstruktúra vagy energiaigény |
| `heated_floor_area_band` | S0 alapterület / rekord × sáv | Durva sáv; pontos érték alapértelmezésben nem kérendő | Forrásalapú sáv / üres vagy rejtetten kerekített | Fogyasztás vagy támogatási szükséglet |
| `heating_system_quality` | S0 OÉNY-minőség / rekord × tanúsítvány | Csak az ötfokú enum; `NOT_STATED` megengedett | Explicit OÉNY-érték / emitterből levezetett | S2 readiness, emitter, COP vagy alkalmasság |
| `heating_energy_carrier` | S0 energiahordozó / rekord × kategória | Enum; fogyasztás és szabad szöveg tilos | Explicit kategória / imputált vagy fogyasztásnak álcázott | Villamos headroom vagy műszaki alkalmasság |
| `emitter_status` | S2 hőleadó-bizonyíték / tanúsítvány-dokumentum | `OBS` csak explicit evidence-dzsel; különben `Q`/`NOT_IN_SOURCE` | Nincs inferált OBS / fűtési kategóriából levezetett OBS | Országos emitter-eloszlás vagy S2 alkalmasság |
| `emitter_types` | S2 jelenlegi hőleadó / dokumentum | Egyedi enumlista; több explicit típus külön elem | OBS-hez evidence és ref / OCR- vagy szakértői feltételezés | Prevalencia, COP, költség vagy hőszivattyú-kompatibilitás |
| `emitter_evidence` | Audit trail / dokumentum | Evidence enum; `NONE` csak Q/NOT_IN_SOURCE mellett | OBS-hez nem-NONE / bizonyíték nélküli állítás | Bizonyíték országos lefedettsége vagy minősége |
| `temperature_status` | S2 hőfokadat / dokumentum × basis | OBS csak explicit design/calculation/operating; referencia nem OBS | Basis-hez kötött / 55/45 referencia OBS-ként | Országos hőfoklépcső vagy alacsony-hőmérsékletű alkalmasság |
| `supply_temperature_c` | S2 előremenő / rekord × hőfok-basis | °C, párban, −50…150; hiány csak explicit Q/NOT_IN_SOURCE | Returnnel azonos basis / kitalált vagy egyoldalú pár | Eloszlás, COP, fogyasztás vagy költség |
| `return_temperature_c` | S2 visszatérő / rekord × hőfok-basis | °C, supply-val azonos basis; nem visszaszámítható | Párban valid / szintetikus vagy basis nélküli | Országos readiness vagy műszaki megfelelés |
| `temperature_basis` | A számérték epistemikus alapja / rekord | Enum; minden nem-null értékhez basis | Reference nem OBS / hiányzó vagy ellentmondó basis | Üzemi működés, COP vagy megtakarítás |
| `demand_reduction_status` | S1 before/after / rekord × fázis | OBS csak linked bizonyítékkal; Q/NOT_IN_SOURCE várt | Explicit before/after / S0-ból levezetett OBS | Programhatás vagy országos keresletcsökkenés |
| `hydraulic_readiness_status` | S2 hidraulika / épület × műszaki evidence | OBS csak explicit műszaki forrásból | Forrásolt OBS vagy explicit hiány / emitterből inferált | Országos hidraulikai alkalmasság vagy költség |
| `electrical_readiness_status` | S2 villamos readiness / épület × régió | OBS csak explicit mérés/csatlakozásból | Forrásolt OBS vagy explicit hiány / energiahordozóból inferált | DSO-kapacitás, headroom vagy országos readiness |
| `permit_readiness_status` | S2 jogi/kivitelezési előfeltétel / épület × fázis | OBS csak explicit jogi evidence-ből | Forrásolt OBS vagy explicit hiány / tanúsítványból inferált | Jogi eligibility vagy kivitelezési kapacitás |
| `evidence_pages` | OBS auditálhatósága / rekord × forrásoldal | Pozitív egész oldalszám; OBS-hez szükség esetén ref | Visszaellenőrizhető / OBS bizonyíték nélkül | A pilot országos bizonyító ereje |
| `pii_check` | Intake adatvédelmi kapu / minden rekord | Pontosan `PASS`; PII-scan kötelező | 100% PASS / bármely PII vagy tisztázatlan találat | Bármilyen háztartási, országos vagy jogi állítás |

## 4. Pilot-szintű kapuk

1. **G0 – Request readiness:** a P1-F tervezet a JSON-sémára és a P1-K-ra hivatkozik; nincs külső küldés.
2. **G1 – Structured intake:** csak UTF-8 CSV/JSON, anonimizált rekordok, séma-validáció és PII-ellenőrzés után.
3. **G2 – Completeness:** nincs üres, jelentés nélküli cella; az ismeretlen `Q` vagy `NOT_IN_SOURCE`. A hiányt nem szabad nullának vagy negatív bizonyítéknak venni.
4. **G3 – Evidence:** minden `OBS` állapot explicit forrásra, szükség esetén oldalra és basisre mutat. Referenciafeltétel nem observed adat.
5. **G4 – Sample:** a P1-F 500–1000 rekordot `SCN` tervezési tartományként ad meg. 500 alatti minta alkalmas lehet séma-/kinyerési smoke testre, de országos vagy reprezentatív állításra nem, ezért ilyen felhasználásra `REVISE_REQUEST`.
6. **G5 – Representativeness:** a pilotból csak akkor lehet kalibrációs input, ha a mintavételi keret, rétegzés, kiválasztási valószínűség és súlyozás külön bizonyított. A darabszám önmagában nem reprezentativitás.
7. **G6 – Final acceptance:** a teljesítési jegyzőkönyvnek tartalmaznia kell schema-verziót, rekord- és mezőszámokat, hiányarányokat, `OBS/Q/NOT_IN_SOURCE` bontást, PII-ellenőrzést, evidence/basis coverage-t és az ismert torzításokat.

Ha később PDF- vagy fotó-pilot merül fel, az nem része ennek az elfogadásnak: új jóváhagyás, a [P1-F feldolgozási protokoll](../protocols/P1F_OENY_SAMPLE_PROCESSING_PROTOCOL.md) kapui, biztonságos átadás és külön annotációs acceptance szükséges.

## 5. Tiltott következtetések sikeres pilot után is

Sikeres P1K-elfogadás esetén is tiltott:

- országos hőleadó-, hőfoklépcső-, hidraulikai-, villamos- vagy engedélyezési readiness-eloszlást közölni;
- a pilotot KSH/WBL-lel közös archetípus-illesztésként, országosan reprezentatív mintaként vagy súlyozás nélkül kalibrációként használni;
- `HOSZIV=1`, `heating_system_quality`, energiahordozó vagy tanúsítvány megléte alapján S2/S3 állapotot, jogi eligibilityt, COP-ot, fogyasztást, CAPEX-et, támogatási igényt vagy programhatást levezetni;
- S1 before/after hatást vagy ok-okozati megtakarítást állítani, ha nincs azonos definíciójú fázisadat;
- a `Q`/`NOT_IN_SOURCE` állapotokat nullának, sikertelennek vagy hiányzó rekordnak átminősíteni;
- külső adatbekérést, licencelfogadást, adatátvételt vagy valós adat tárolását ebből a dokumentumból automatikusan végrehajtani.

## 6. Readiness-döntés a P1-F adatigénylési tervezetre

**Döntés: `GO_FOR_REQUEST` – Joseph végső engedélyére előkészítve.**

Indok:

- a P1-F szakaszolja az adatigényt: először adatszótár és aggregált leltár, utána strukturált anonimizált pilot, végül külön kapu a PDF-pilot lehetőségére;
- a kért pilotmezők és státuszok most már mezőszinten elfogadási kritériumhoz kötöttek;
- a tervezet kifejezetten kizárja a nem bizonyított országos readiness-, S1-hatás-, KSH/WBL-illesztési és jogosultsági következtetéseket;
- a 500–1000 rekord `SCN` tervezési tartomány, nem reprezentativitási garancia;
- az adatbekérés továbbra sem történt meg, és a levél küldésre nem jóváhagyott tervezet marad mindaddig, amíg Joseph az igénylőt, csatornát, jogi/licenc- és adatvédelmi feltételeket külön jóvá nem hagyja.

**Visszaminősítési szabály:** sémaeltérés, PII-találat, bizonyíték nélküli `OBS`, nem dokumentált mintavétel vagy új következtetési igény esetén a P1-F státusza `REVISE_REQUEST`; küldés/átvétel csak új Joseph-döntés után. `NO_GO` akkor, ha az adatátadás jogszerűsége, anonimizálása vagy a kérés teljesíthetősége nem igazolható.
