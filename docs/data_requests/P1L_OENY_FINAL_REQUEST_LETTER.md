# P1-L OÉNY adatigénylési levél – végleges pre-send változat

**Állapot:** VÉGLEGESÍTETT TERVEZET / NEM KÜLDÖTT

**Verzió:** 2026-08-17 / v1.0

## Címzés

**Címzett:** Lechner Tudásközpont Nonprofit Kft. – Jogi Igazgatóság, közadat felelős szervezeti egység

**Elsődleges benyújtás:** Ügyfélkapus e-Papír

**Tartalék benyújtás:** info@lechnerkozpont.hu

**Tárgy:** Közérdekű adatigénylés – OÉNY energetikai adatszótár és anonimizált, strukturált pilot

## Levéltervezet

Tisztelt Jogi Igazgatóság!

Alulírott **[IGÉNYLŐ TELJES NEVE / SZERVEZETE]**, válaszcím: **[E-MAIL VAGY POSTAI CÍM]**, a Lechner Tudásközpont kezelésében lévő, megismerhető közérdekű adatok iránt az információs önrendelkezési jogról és az információszabadságról szóló 2011. évi CXII. törvény 28. §-a alapján az alábbi, szűkített adatigényt terjesztem elő.

Az igény egy módszertani kutatás előkészítését szolgálja. Nem kérünk személyes adatot, ingatlan- vagy tanúsítvány-azonosítót, eredeti dokumentumot, fényképet, szabad szöveget, új szakmai minősítést vagy új adatbázis/elemzés létrehozását. Ha valamely kért adat nem létezik, nem adható át, vagy csak új feldolgozással lenne előállítható, elegendő ennek rövid közlése és – ha lehetséges – a legközelebbi meglévő adatforrás megnevezése.

### 1. Meglévő adatszótár és aggregált leltár

Kérem, amennyiben meglévő adatként rendelkezésre áll:

1. a mellékelt OÉNY readiness pilot schema 1.0 mezőinek adatszótárát, kódtábláit, meződefinícióit, schema/export-verzióját és változástörténetét;
2. annak közlését, hogy a mezők közül melyek léteznek normalizált háttérmezőként, melyek csak dokumentumból állapíthatók meg, és melyek nem állnak rendelkezésre;
3. mezőnként a teljes érintett rekord-/populációs darabszámot és a kitöltött, Q vagy NOT_IN_SOURCE státuszok darabszámát vagy hiányarányát, kizárólag a szolgáltató adatvédelmi közzétételi szabályai szerinti aggregált formában;
4. a durva területi, épület-, építési-időszak- és alapterület-sávok kódkönyvét, valamint az alkalmazott ritka-cellás elnyomási vagy összevonási szabály rövid leírását;
5. ha létezik ilyen meglévő dokumentáció, a mintavételi keret és a rétegzési kategóriák leírását. Súlyokat, országos reprezentativitási garanciát és új statisztikai becslést nem kérünk.

A kért mezők kizárólag:

schema_version; pilot_record_id; reference_year; coarse_geography; building_category; construction_period_band; heated_floor_area_band; heating_system_quality; heating_energy_carrier; emitter_status; emitter_types; emitter_evidence; temperature_status; supply_temperature_c; return_temperature_c; temperature_basis; demand_reduction_status; hydraulic_readiness_status; electrical_readiness_status; permit_readiness_status; evidence_pages; pii_check.

### 2. Egyszeri anonimizált strukturált pilot

Ha jogilag és technikailag lehetséges, kérem **egy egyszeri, legfeljebb 500 rekordos** anonimizált, géppel olvasható pilotminta átadását UTF-8 CSV vagy JSON formátumban, a mellékelt schema 1.0 szerint. Kisebb, az Önök megítélése szerint arányos minta is elfogadható; 500 rekordnál nagyobb minta csak új, kifejezett egyeztetés és jóváhagyás után jöhet szóba.

Lehetőség szerint kérjük a minta disclosure-safe, rétegzett kiválasztását a durva régió/településtípus, épületkategória és építési-időszak-sávok szerint. A rétegek és a kiválasztási eljárás rövid leírását kérjük, de nem kérünk személyhez vagy ingatlanhoz kapcsolható mintavételi kulcsot, súlyt vagy országos reprezentativitási garanciát.

A pilotban kizárólag a fenti 22 schema-property, a schema 1.0 szerinti technikai rekordazonosító és a szükséges státusz-/evidence-kódok szerepelhetnek. Kifejezetten nem kérünk nevet, címet, helyrajzi számot, HET-azonosítót, e-mailt, telefonszámot, koordinátát, mérő- vagy engedélyazonosítót, szabad szöveget, fényképet, PDF-et, eredeti tanúsítványt vagy visszafejtési/linkage-kulcsot.

Kérjük, hogy a ritka kombinált cellákat (különösen durva terület × épületkategória × időszak × alapterület) saját adatvédelmi és disclosure-control szabályuk szerint nyomják el vagy vonják össze. Az elnyomott vagy nem elérhető adatot nem tekintjük nullának.

### 3. Felhasználás, publikáció és átadás

A kapott adatot kizárólag belső módszertani kutatásra és reprodukálható feldolgozásra használjuk. Eredeti rekordot, eredeti dokumentumot vagy egyedi sorokat nem teszünk közzé és nem adunk tovább. Csak jogszerűen publikálható, aggregált vagy származtatott eredmény jelenhet meg, az Önök által közölt forrás-, licenc-, újrahasznosítási és adatvédelmi feltételek szerint. E levél nem tekinti automatikusan megadottnak az újrahasznosítási vagy publikációs engedélyt.

Kérjük az esetleges költség-, licenc-, titoktartási, adatfeldolgozási, retention- vagy további adatvédelmi feltételek előzetes közlését. A pilotfájl biztonságos átadási módját kérjük megjelölni; kéretlen e-mail-mellékletként nyers vagy korlátozott hozzáférésű fájlt nem kérünk.

Kifejezetten nem kérünk és nem tekintünk teljesítettnek: országos hőleadó- vagy hőfoklépcső-megoszlást, KSH/WBL közös archetípus-illesztést, S1 előtte/utána keresletcsökkentési hatást, hidraulikai/villamos/engedélyezési országos readiness-t, programjogosultságot, támogatási alkalmasságot, COP-ot, fogyasztást vagy retrofitköltséget.

Kelt: **[DÁTUM]**

Tisztelettel:

**[IGÉNYLŐ TELJES NEVE / SZERVEZETE]**

**[VÁLASZCÍM]**

## Küldési mellékletlista

1. `schemas/oeny_readiness_pilot.schema.json` – kizárólag a strukturált pilot technikai szerződése;
2. szükség esetén a requested-field manifest kivonata – belső P1J/P1K anyagokat nem csatolunk;
3. személyes adatot, belső DOCX-et vagy nyers adatot nem csatolunk.

## Pre-send korlát

Ez a dokumentum végleges pre-send változat, de **NEM KÜLDÖTT**. A címzett, a csatorna, az igénylő személye, a válaszcím, a dátum és az esetleges licenc-/retention-feltételek Joseph külön jóváhagyása nélkül nem tölthetők ki és nem továbbíthatók.
