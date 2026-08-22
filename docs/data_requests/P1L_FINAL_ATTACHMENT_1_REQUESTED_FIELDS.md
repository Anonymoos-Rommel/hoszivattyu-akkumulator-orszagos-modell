# 1. számú melléklet – Kért forrásnatív adatok és P1K célmezők

**Kapcsolódó kérelem:** P1L-FINAL-R1 OÉNY pilot adatigénylés
**Pilot maximum:** 500 rekord
**P1K célmezők:** 22 (a canonical contract változatlan)
**Lechner felé kért interfész:** kizárólag az OÉNY-ben ténylegesen meglévő, strukturált forrásnatív adat és meglévő adatszótár/kódlista.

## Értelmezési szabály

A táblázat elsődleges oszlopa kutatási fogalmat nevez meg, nem kötelező OÉNY-mezőnevet. Amennyiben az OÉNY-ben azonos vagy tartalmilag megfelelő adat más mezőnéven, kódolással vagy granularitással szerepel, az eredeti forrásmezőt és annak adatszótárát/kódlistáját kérjük. Nem kérünk új kategorizálást, minősítést, összekapcsolást vagy származtatott adat előállítását.

## 1. SOURCE-NATIVE REQUEST FIELDS

| Kutatási fogalom | Kért forrásnatív adat | Elfogadható forrás-grain | P1K célmező(k) | Adatvédelmi korlát |
|---|---|---|---|---|
| Időbeli referencia | Az OÉNY rekordhoz tartozó meglévő tanúsítási/nyilvántartási évkód | Rekord- vagy meglévő időszak-grain; hónap/nap nem szükséges | `reference_year` (P1K-003) | Csak év vagy meglévő, kellően durva időszak; nincs dátum/időbélyeg |
| Durva földrajzi réteg | OÉNY-ben meglévő régió-, megye-, településtípus- vagy más durva földrajzi kód | Durva régió vagy településtípus; cím- és koordináta-grain kizárva | `coarse_geography` (P1K-004) | Nincs cím, helyrajzi szám, koordináta, HET-ID vagy ritka kis területi kód |
| Épület/használati típus | OÉNY-ben meglévő épület-, rendeltetés- vagy lakóépület-típus kódja | Meglévő kategória- vagy rekord-grain | `building_category` (P1K-005) | Nincs lakás-, tulajdonos- vagy ingatlanazonosító |
| Építési kor | Meglévő építési év, építési időszak-kód vagy hasonló forrásnatív érték | Év vagy OÉNY saját időszak-kódja; nem kérünk P1K-sávos átkódolást | `construction_period_band` (P1K-006) | Pontos év helyett meglévő sáv elfogadható; cím/linkage nincs |
| Fűtött alapterület | Meglévő fűtött alapterületérték, intervallum vagy OÉNY-saját kód | Rekord-grain, szám vagy meglévő intervallum | `heated_floor_area_band` (P1K-007) | P1K-sávos átkódolást nem kérünk; pontos érték csak akkor, ha meglévő és disclosure-safe |
| Fűtési rendszer és energiahordozó | Meglévő fűtési rendszer-, energiahordozó-, energiaosztály- vagy hatásossági kód(ok) | OÉNY saját kódlista szerinti rekord-grain | `heating_system_quality`, `heating_energy_carrier` (P1K-008–009) | Nem kérünk BAD/POOR/... saját enumot, fogyasztási adatot vagy mérőazonosítót |
| Hőleadó / hőleadási mód | Ha létezik, meglévő hőleadó-, hőleadási mód- vagy kapcsolódó műszaki kód | OÉNY saját mező- és kódlista szerinti rekord-grain | `emitter_types` (P1K-011) | Nem kérünk fotót, PDF-et, szabad szöveget vagy szakértői minősítést |
| Hőmérsékleti számértékek | Ha létezik, meglévő előremenő- és visszatérőérték, egységgel és az OÉNY meglévő eredet-/mérési metaadatával | Épület-/rendszer-rekord-grain; °C vagy meglévő kód | `supply_temperature_c`, `return_temperature_c` (P1K-014–015) | Nem kérünk referenciaértéket épületspecifikus adatként, és nem kérünk 55/45 szintetikus értéket |

## 2. INTERNAL P1K DERIVED FIELDS – NEM KÉRJÜK A LECHNERTŐL

Az alábbi mezőket a pilot ingest során mi hozzuk létre a beérkező source-native adatokból, vagy a hiányt explicit módon jelöljük. Ezek nem OÉNY-forrásmezőként és nem adatigényként szerepelnek:

| Belső P1K mező | Kezelés |
|---|---|
| `schema_version` | Ingest-séma technikai verziója; mi állítjuk be. |
| `pilot_record_id` | Véletlen, nem visszafejthető pilot-azonosító; mi generáljuk. |
| `coarse_geography`, `building_category` | A forrásnatív földrajzi/épülettípus-kód P1K szerinti belső kategorizálása. |
| `construction_period_band`, `heated_floor_area_band`, `heating_system_quality`, `heating_energy_carrier` | P1K-kategorizálás a forrásnatív értékből; saját enum szerinti átkódolást nem kérünk. |
| `emitter_status`, `emitter_evidence` | Forrásbizonyíték-státusz és QA-kód; mi kódoljuk `OBS`/`Q`/`NOT_IN_SOURCE` szerint. |
| `emitter_types` | A meglévő natív hőleadó-adat P1K enumjára történő belső normalizálása, ha bizonyíték támogatja. |
| `temperature_status`, `temperature_basis` | A natív hőmérsékleti érték epistemikus státusza; referenciaérték nem lehet `OBS`. |
| `demand_reduction_status` | Belső, fail-closed S1 státusz; új before/after adatot vagy számítást nem kérünk. |
| `hydraulic_readiness_status`, `electrical_readiness_status`, `permit_readiness_status` | Belső, fail-closed readiness-státusz; Lechner-minősítést nem kérünk. |
| `evidence_pages` | Belső QA/provenance-mező; PDF-et, fotót vagy eredeti tanúsítványt nem kérünk. |
| `pii_check` | Intake QA-kapu; mi ellenőrizzük, és eltérés esetén elutasítjuk a rekordot. |

A `reference_year`, `supply_temperature_c` és `return_temperature_c` P1K-célmezőkbe a kapott forrásnatív értékeket csak technikai ingest-normalizálás után írjuk; a Lechnertől nem kérjük a P1K-mezőnevek vagy P1K-kódolás alkalmazását.

## Közös átadási feltételek

- Elsődleges formátum: UTF-8 CSV vagy JSON.
- Kérjük a meglévő adatszótárt, kódlistákat, mértékegységeket és séma-/exportverziót.
- Ha valamely forrásnatív adat nem létezik strukturáltan, ezt kérjük külön jelezni; új adat vagy új elemzés létrehozását nem kérjük.
- A nem elérhető belső P1K célmezőt mi `Q` vagy `NOT_IN_SOURCE` értékkel kezeljük; imputálást nem végzünk.
- Ritka kombinációk esetén suppression/generalizálás elfogadható és előnyben részesítendő; az elnyomott cella ismeretlen, nem nulla.
