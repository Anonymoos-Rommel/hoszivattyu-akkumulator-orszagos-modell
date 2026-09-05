# B02-P11 — WBL017 code-set and gap-cause authority

Állapot: **AUDITED / FAIL-CLOSED**

Kapcsolódó kérdések: `Q-B02-001`, `Q-B02-002`, `Q-B02-004`

Ellenőrzés napja: **2026-09-05**

## Cél

A P10-ben gépileg rögzített WBL017 lefedettségi különbségek után különválasztani:

1. azt, hogy a kiválasztott `FUTMODAG_V3` kódok source-native kódok-e;
2. azt, hogy a kiválasztott kódkészlet bizonyítottan teljes és diszjunkt source-native leaf-partíció-e;
3. azt, hogy a 88 977 és 6 294 lakásos különbség konkrét oka bizonyított-e.

P11 nem módosítja a P1-H extractor kódkészletét, nem tölti fel a hiányzó cellákat és nem nevez meg feltételezett gap-okot bizonyított okként.

## Kanonikus határok

`SOURCE CODE EXISTS != SELECTED CODESET IS EXHAUSTIVE`

`PINNED STRUCTURE != PROVEN SOURCE-NATIVE LEAF PARTITION`

`SELECTED CODES != DISJOINT ANALYTICAL PARTITION`

`COUNT GAP OBSERVED != GAP MECHANISM PROVEN`

`UNRESOLVED GAP != OMITTED CODE != API SUPPRESSION != STRUCTURAL INVALIDITY`

## Mit bizonyít a jelenlegi P1-H extractor?

A `tools/extract_b02_ksh_wbl_joint_cells.py` a pinned `WBL017/V67` struktúrát olvassa, ellenőrzi a dimenziósorrendet, és minden projekciónál ellenőrzi, hogy a kiválasztott kódok szerepelnek-e a source codelistben. A jelenlegi `FUTMODAG_V3` kiválasztás 13 kódot tartalmaz:

`01; 02; 03; 04-05; 06-12; 13; 14; 15; 16-17; 18; 19; 20-24; 25`

Ez fontos source-native existence control, de a jelenlegi kód nem bizonyítja külön, hogy:

- ezek pontosan az összes source-native leaf kód;
- nincs más source-native kód, amely a lakottlakás-univerzum egy részét hordozza;
- a kiválasztás kategóriaértelemben diszjunkt és teljes;
- a kiválasztott készlet minden `DW_OC` rekordot lefed.

A P1-H materializált eredménye maga is azt mutatja, hogy a kiválasztás nem egyezik vissza a teljes lakottlakás-kontrollra: 3 919 564 versus 4 008 541.

## Miért fontos a WBL011 precedens?

A WBL011 `FUTES_TOH` esetén a repó explicit forrásanomáliát dokumentál: a publikált parent pointer és az API-viselkedés miatt a `NHEAT21` duplikálja a `NHEAT` rekordokat. Emiatt a repó explicit diszjunkt analitikai partíciót rögzített:

`HEAT111 + HEAT112 + HEAT12 + NHEAT`

és ezt exact módon visszaegyeztette a 4 008 541 lakásos univerzumra.

A WBL017 `FUTMODAG_V3` kiválasztásnál jelenleg nincs ugyanilyen, source-native leaf-partíciót és teljes population reconciliationt bizonyító authority. P11 ezért nem viszi át automatikusan a WBL011 precedens státuszát WBL017-re.

## A két gap jelenlegi státusza

### Population coverage

- WBL011 lakottlakás-kontroll: **4 008 541**;
- WBL017 leaf-projekció: **3 919 564**;
- exact gap: **88 977**.

A gap darabszáma reprodukálható `DER`, de a gap mechanizmusa továbbra is `Q / UNRESOLVED_CAUSE`.

### `HOSZIV=1`

- source-native országos TOTAL kontroll: **67 853 OBS**;
- leaf-projekció `HOSZIV=1` részösszeg: **61 559**;
- exact gap: **6 294**.

Ez a különbség szintén reprodukálható `DER`; a mechanizmus nincs bizonyítva.

## Executable authority gate

A `modules/B02/wbl017_codeset_authority.py` két külön döntést ad.

### 1. Code-set authority

`QUALIFIED` csak akkor lehetséges, ha mind igaz:

- a source structure pinned;
- a kiválasztott kódok source-native kódok;
- a source-native leaf-partíció explicit bizonyított;
- a kiválasztás teljes;
- a kiválasztás diszjunkt;
- a leaf-projekció exact visszaegyezik a megfelelő TOTAL kontrollra.

A jelenlegi WBL017 kódkészlet ezért `Q`.

### 2. Gap-cause authority

Konkrét mechanizmus csak akkor `QUALIFIED`, ha:

- source-native ok explicit azonosított;
- az ok bizonyítéka `OBS` vagy `DER`;
- az ok exact módon visszaegyezteti a teljes gapet.

Jelenleg mind a 88 977-es, mind a 6 294-es ok `Q`.

## Tiltott következtetések

- A 13 kiválasztott `FUTMODAG_V3` kód puszta létezése nem bizonyít teljes leaf-partíciót.
- Az API által nem visszaadott kombinációk nem bizonyított nullák.
- A 88 977 lakás nem minősíthető automatikusan kihagyott kódnak, adatvédelmi elnyomásnak, strukturálisan érvénytelen kombinációnak vagy `HOSZIV=0` állománynak.
- A 6 294 `HOSZIV=1` különbség nem osztható szét alcsoportokra.
- A gap okának lezárása sem ad önmagában WBL011↔WBL017 cell-level joint authorityt.
- Ez a slice nem ad technikai eligibilityt és nem ad OÉNY-küldési jóváhagyást.

## Closure path

A kódkészlet- és gap-ok lezárásához source-native audit szükséges, amely legalább:

1. archiválja vagy reprodukálhatóan levezeti a `FUTMODAG_V3` teljes codelistet és parent/leaf viszonyt;
2. explicit rögzíti a kiválasztott teljes diszjunkt partíciót;
3. source-native TOTAL kontrollokkal visszaegyezteti a population és `HOSZIV` bontásokat;
4. ha gap marad, azt API-válaszokkal vagy KSH módszertani authorityvel konkrét mechanizmushoz köti;
5. missing/unreturned értéket addig `Q`-ként tart, amíg source-native státusz nem bizonyított.

## Hatás a B02 állapotára

- `Q-B02-001`: **OPEN**;
- `Q-B02-002`: **OPEN**;
- `Q-B02-004`: **OPEN**;
- national technical/final eligible count: **blank/Q**;
- OÉNY adatkérés: **nem került elküldésre és P11 nem ad küldési jóváhagyást**;
- B02 readiness változatlanul **55%**.

P11 nem readiness-uplift; a WBL017 code-set és gap-cause authorityt teszi explicit fail-closed szerződéssé.
