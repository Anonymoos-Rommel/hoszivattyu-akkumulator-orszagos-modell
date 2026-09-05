# B02-P10 — WBL017 coverage reconciliation

Állapot: **AUDITED / FAIL-CLOSED**

Kapcsolódó kérdések: `Q-B02-001`, `Q-B02-002`, `Q-B02-004`

Ellenőrzés napja: **2026-09-05**

## Cél

A P1-H óta explicit nyitva maradt WBL017 lefedettségi különbséget gépileg szétválasztani a teljes lakottlakás-univerzumtól, a source-native országos `HOSZIV=1` kontrolltól és minden későbbi archetípus- vagy alkalmassági állítástól.

A P10 nem magyarázza meg feltételezéssel a különbséget, nem tölt fel hiányzó cellát és nem változtat meg KSH-kódot.

## Kanonikus határok

`RETURNED WBL017 LEAF PROJECTION != COMPLETE OCCUPIED-DWELLING UNIVERSE`

`WBL017 NATIONAL HOSZIV TOTAL != WBL017 LEAF-PROJECTION HOSZIV SUBTOTAL`

`COUNT RECONCILIATION != CELL-LEVEL JOINT AUTHORITY != TECHNICAL ELIGIBILITY`

`MISSING / UNRETURNED != ZERO != HOSZIV=0 != EXCLUDED`

## Reprodukálható jelenlegi számok

A P1-H már materializálta a három elkülönített KSH V67 projekciót. A két WBL011 nézet egyaránt visszaegyezik a szerződött lakott hagyományos lakás-univerzumra:

- WBL011 `DW_OC` referencia: **4 008 541** lakás;
- WBL017 `HEAT_PUMP_BASELINE` leaf-projekció: **3 919 564** lakás;
- exact különbség: **88 977** lakás.

A hőszivattyú-jelenlét külön kontrollja:

- országos, minden más releváns dimenzión `TOTAL`, `HOSZIV=1`: **67 853** lakás (`OBS`);
- WBL017 leaf-projekcióban `HOSZIV=1`: **61 559** lakás;
- exact különbség: **6 294** lakás.

A 61 559-es leaf-részösszeg a leaf-projekcióból levezetett érték; nem írhatja felül a 67 853-as source-native országos TOTAL megfigyelést.

## Forrás- és kódhatár

A kanonikus forrás továbbra is a KSH Népszámlálás 2022 V67 adatbázisa és a már rögzített `SRC-B02-KSH-CENSUS-API-2022` provenance. A P1-H manifest rögzíti a WBL017 structure URL-t és SHA-256 lenyomatot, továbbá a projekció lekérdezéseit.

A jelenlegi extractor a `FUTMODAG_V3` kombinált fűtési mód / fűtőanyag dimenzió szerződött kódhalmazát és a `HOSZIV={1,0,9}` kódokat használja. A P10 **nem állítja**, hogy a 88 977-es vagy 6 294-es különbség bizonyítottan egyetlen kihagyott kód, adatvédelmi elnyomás, strukturálisan érvénytelen kombináció vagy más konkrét mechanizmus eredménye. Ehhez külön source-native kód-/API-válasz audit szükséges.

Hivatalos KSH navigáció:

- Népszámlálás 2022 adatbázis: `https://nepszamlalas2022.ksh.hu/adatbazis/`
- felhasználási feltételek: `https://nepszamlalas2022.ksh.hu/felhasznalasi-feltetelek`

A KSH adatbázis külön lakásdimenzióként publikálja a „Fűtési mód, fűtőanyag” és a „Hőszivattyús fűtőberendezés, eszköz ellátottság” nézeteket. A honlap tartalma CC BY 4.0 alatt használható forrásmegjelöléssel.

## Executable gate

A `modules/B02/wbl017_coverage_reconciliation.py` csak count-reconciliationt végez.

Bemenet:

- referencia-darabszám;
- projekció-darabszám;
- referencia evidence-status;
- projekció evidence-status.

Szabályok:

1. darabszám csak nemnegatív egész lehet;
2. referencia és projekció csak `OBS`/`DER` lineage-dzsel tekinthető valós count-evidence-nek;
3. ha a projekció kisebb a referenciánál: `Q / INCOMPLETE_POPULATION_COVERAGE`;
4. ha a projekció nagyobb a referenciánál: `Q / PROJECTION_EXCEEDS_REFERENCE`;
5. exact egyenlőség esetén `RECONCILED`, de ez **csak count equality**;
6. `RECONCILED` nem bizonyít kategória-teljességet, cella-jointot, WBL011↔WBL017 joinabilityt vagy technikai alkalmasságot.

A jelenlegi két gépi claim a `registry/b02_wbl017_coverage_reconciliation.csv` fájlban egyaránt `Q`.

## Tiltott következtetések

- A **88 977** lakás nem sorolható automatikusan `HOSZIV=0` alá.
- A **88 977** nem tekinthető automatikusan nullának vagy programon kívüli állománynak.
- A **6 294** `HOSZIV=1` különbség nem osztható szét építési időszak, településtípus vagy `FUTMODAG_V3` cellák között feltételezéssel.
- A **61 559** leaf-részösszeg nem helyettesítheti a **67 853** országos source-native kontrollt.
- A WBL017 baseline továbbra sem műszaki hőszivattyú-alkalmasság.
- A count-gap lezárása önmagában nem zárná a P9 `NO_COMPLETE_WBL_JOINT` blockerét sem; ahhoz a szükséges együtt megfigyelt/jóváhagyott join authority külön bizonyítandó.

## Hatás a B02 állapotára

- `Q-B02-001`: **OPEN**;
- `Q-B02-002`: **OPEN**;
- `Q-B02-004`: **OPEN**;
- national technical/final eligible count: **blank/Q**;
- OÉNY adatkérés: **nem került elküldésre és P10 nem ad küldési jóváhagyást**;
- B02 readiness változatlanul **55%**.

P10 ezért nem readiness-uplift, hanem a WBL017 population-control szemantikai és gépi lezárása fail-closed formában.
