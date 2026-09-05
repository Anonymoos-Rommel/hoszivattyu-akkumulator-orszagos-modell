# B02-P13 — WBL017 source-native hierarchy and residual reconciliation

Állapot: **SOURCE EVIDENCE ACQUIRED / PARTIAL BLOCKER CLOSURE**

Ellenőrzés napja: **2026-09-05**

Kapcsolódó kérdések: `Q-B02-001`, `Q-B02-002`, `Q-B02-004`

## Cél

A P10–P11 után nyitva maradt két WBL017 eltérés tényleges source-native vizsgálata:

- occupied `TOTAL` **4 008 541** vs non-`TOTAL` projection **3 919 564** → **88 977**;
- national `HOSZIV=1` `TOTAL` **67 853** vs non-`TOTAL` projection **61 559** → **6 294**.

P13 nem újabb hipotézis-gate. A KSH Népszámlálás 2022 pinned `WBL017/V67` struktúráját és országos API-kontrolljait ténylegesen lekérte, majd a bizonyított hierarchiát és count-reconciliationt materializálta.

## Source-native FUTMODAG_V3 hierarchia

A V67 struktúrában a `TOTAL` alatt pontosan három felső non-`TOTAL` ág található:

1. `01-12` — Helyiségenként konvektorral, kályhával vagy más eszközzel;
2. `13-24` — Egy vagy több lakást fűtő központi, cirkó kazánnal vagy más eszközzel;
3. `25` — Távfűtéssel.

A teljes parent/child kódhierarchia a
`data/processed/b02/ksh_wbl017_futmodag_hierarchy_2022.csv`
fájlban van rögzítve.

A P1-H extractor 13 kódos választása a bottom-level non-`TOTAL` ágakat fedi le:

`01, 02, 03, 04-05, 06-12, 13, 14, 15, 16-17, 18, 19, 20-24, 25`

A P13 API-probe bizonyította, hogy **nincs további non-`TOTAL` FUTMODAG_V3 kód**, amelyet a projection kihagyott volna.

## Parent-child országos kontrollok

A visszaadott országos OBS sorok exact hierarchikus egyezést adnak:

- `01` 515 369 + `02` 70 482 + `03` 342 507 = `01-05` **928 358**;
- `01-05` 928 358 + `06-12` 233 645 = `01-12` **1 162 003**;
- `13` 1 272 653 + `14` 58 812 + `15` 277 066 = `13-17` **1 608 531**;
- `18` 119 227 + `19` 411 079 = `18-24` **530 306**;
- `13-17` 1 608 531 + `18-24` 530 306 = `13-24` **2 138 837**.

Az `04-05`, `16-17` és `20-24` kódokra a multi-code kérés nem adott külön sort. P13 ezeket **nem írja át explicit OBS nullára**. A parent-child visszaegyezésből csak az következik, hogy a visszaadott testvérágak már exact módon kimerítik a megfelelő parent országos countját.

## A 88 977-es residual mechanizmusa

A három felső non-`TOTAL` ág összege:

`1 162 003 + 2 138 837 + 618 724 = 3 919 564`.

A source-native `TOTAL` occupied control:

`4 008 541`.

Ezért:

`4 008 541 - 3 919 564 = 88 977`.

Mivel a V67 struktúrában nincs további non-`TOTAL` `FUTMODAG_V3` ág, P13 bizonyítja:

**88 977 occupied dwelling benne van a `TOTAL` kontrollban, de egyik non-`TOTAL` `FUTMODAG_V3` kategóriában sincs jelen.**

Ez **DER source-native classification residual**. Nem „kihagyott kód”.

P13 külön ellenőrizte a WBL011 `FUTES_TOH=NHEAT` országos controlt is. Az érték **1 173 639**, ezért a `88 977 = NHEAT` hipotézis hamis és elvetett.

A 88 977-re továbbra sem szabad külön bizonyíték nélkül azt mondani, hogy:

- nincs fűtése;
- `HOSZIV=0`;
- suppression;
- invalid record;
- programon kívüli lakás.

## A 6 294-es HOSZIV=1 residual mechanizmusa

A három felső non-`TOTAL` ág `HOSZIV=1` countja:

- `01-12`: **7 561**;
- `13-24`: **51 615**;
- `25`: **2 383**.

Összesen:

`7 561 + 51 615 + 2 383 = 61 559`.

A source-native national `TOTAL`, `HOSZIV=1` control **67 853**.

Ezért:

`67 853 - 61 559 = 6 294`.

P13 bizonyítja:

**6 294 `HOSZIV=1` dwelling benne van a national TOTAL heat-pump controlban, de egyik non-`TOTAL` `FUTMODAG_V3` ágban sincs jelen.**

Ez a classification residual exact mechanizmusa. A 6 294 nem osztható szét vármegye, településtípus, építési időszak vagy más cella szerint külön source-native evidence nélkül.

## Canonical változás P11-hez képest

P11 helyesen hagyta Q-ban a claim-eket, mert akkor még nem volt meg a source-native hierarchy proof.

P13 ezt új bizonyítékkal felülírja:

- `WBL017_FUTMODAG_V3_CODESET_AUTHORITY` → **QUALIFIED**;
- `WBL017_POPULATION_GAP_CAUSE` → **QUALIFIED** a classification-residual mechanizmusra;
- `WBL017_HOSZIV1_GAP_CAUSE` → **QUALIFIED** a classification-residual mechanizmusra.

Fontos különbség:

`COMPLETE NON-TOTAL CODESET != COMPLETE POPULATION CLASSIFICATION`

A code-set most bizonyítottan teljes, miközben a non-`TOTAL` population coverage továbbra sem teljes.

## Mi nem zárult le

P13 nem hoz létre:

- WBL011↔WBL017 cell-level joint authorityt;
- current building-type link authorityt;
- primary-energy-to-WBL link authorityt;
- heat-emitter vagy design-temperature evidence-t;
- technical eligibility countot.

Ezért:

- `Q-B02-001`: **OPEN**;
- `Q-B02-002`: **OPEN**;
- `Q-B02-004`: **OPEN**;
- current-stock archetype: **Q**;
- technical-readiness archetype: **Q**;
- national technical/final eligible count: **blank/Q**;
- B02 readiness: **55%**.

A 55% változatlan, mert P13 valódi adatminőségi blockert zár, de még nem zárja a P9 current-stock archetype admission egyik fő upstream authority-hiányát sem.

Az OÉNY adatkérés P13 miatt sem került elküldésre, és P13 nem ad küldési jóváhagyást.
