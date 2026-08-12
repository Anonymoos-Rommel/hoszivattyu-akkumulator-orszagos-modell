# P1-F OÉNY anonimizált mintafeldolgozási protokoll

Állapot: **PROPOSED_POL – végrehajtás előtt Joseph jóváhagyása szükséges**

Verzió: **1.0 / 2026-08-12**

## Cél és határ

A protokoll a Lechner/OÉNY által esetlegesen átadott anonimizált strukturált minta és – csak külön második kapuban – számítási PDF-ek feldolgozását szabályozza. Nem jogosít fel adatigénylés elküldésére, szerződés vagy licenc elfogadására, nyers fájl Gitbe töltésére, illetve országos becslés készítésére.

Alapelv: **ha a személyesadat-mentesség, a felhasználási jog vagy a forrás eredete nem bizonyítható, a fájl karanténban marad és nem annotálható.**

## Adatosztályok

| Osztály | Példa | Git | Hozzáférés | Megjegyzés |
| --- | --- | --- | --- | --- |
| `PUBLIC_METHOD` | protokoll, üres séma, tesztadat | megengedett | nyilvános | Nem tartalmaz valós OÉNY-rekordot. |
| `RESTRICTED_SOURCE` | kapott CSV/JSON/PDF/kép | tilos | kijelölt feldolgozók | Változatlan eredeti, írásvédett logikai másolat. |
| `RESTRICTED_DERIVED` | kitakart PDF, oldalkép, OCR-szöveg | tilos | kijelölt feldolgozók | Az anonimizálás igazolásáig karantén. |
| `PUBLIC_AGGREGATE` | jóváhagyott cellaszám vagy minőségi mutató | csak külön kapu után | nyilvános | Licenc-, cellaelnyomási és reprezentativitási ellenőrzés kell. |

A repó a `data/quarantine/` és `data/restricted/` útvonalat kizárja. Ez nem teszi biztonságossá a repón belüli tárolást: a valós állományt hozzáférés-szabályozott, a nyilvános munkafán kívüli tárolóban kell tartani.

## Kapuk

### G0 – Átvételi jogosultság

Az átvétel előtt írásban rögzítendő:

- az adatgazda és az átadó csatorna;
- az átadási és újrahasznosítási feltételek;
- a megengedett feldolgozók és cél;
- a megőrzési vagy törlési határidő;
- a publikálható aggregáció és a szolgáltató által előírt minimumcellás vagy elnyomási szabály.

Hiány esetén: `BLOCKED`, nincs letöltés vagy feldolgozás.

### G1 – Beérkeztetés

1. Fogadás kizárólag az adatgazda által jóváhagyott csatornán.
2. Az eredeti fájl SHA-256 lenyomatának, bájtméretének, formátumának, átvételi idejének és átadói csomagazonosítójának rögzítése nem nyilvános naplóban.
3. Kártevővizsgálat és fájltípus-ellenőrzés.
4. Az eredeti fájl tartalmi módosításának tilalma; feldolgozás csak munkapéldányon.
5. Sikertelen vizsgálat vagy váratlan fájltípus esetén karantén és `BLOCKED`.

### G2 – Adatminimalizálás és anonimitás

A feldolgozó munkapéldány nem tartalmazhat nevet, címet, pontos koordinátát, helyrajzi számot, HET- vagy más tanúsítványazonosítót, e-mailt, telefonszámot, tanúsítói/megrendelői/tulajdonosi azonosítót, szabad szöveget, fájl-metaadatból visszamaradt személyes adatot vagy eredeti fényképet.

- A szolgáltatói anonimizálás az elsődleges védelem; a helyi ellenőrzés nem helyettesíti.
- A közvetlen azonosítókat nem egyszerű hash-sel, hanem nem nyilvános kulcsú HMAC-SHA-256 leképezéssel vagy véletlen megfeleltetési táblával kell leválasztani.
- A kulcs és a megfeleltetési tábla nem kerülhet Gitbe, annotátorhoz vagy publikált kimenetbe.
- Területi és időadat csak az adatgazda által engedélyezett durvaságban maradhat.
- Egyetlen PII-jelzés is `BLOCKED`; a rekord nem adható annotátornak.

### G3 – Redakciós kétkulcsos ellenőrzés

Egy feldolgozó elkészíti a kitakart dokumentumot, egy másik személy pedig az eredetihez képest ellenőrzi. Az annotátorok csak a `PASS` redakciós állapotú példányt és annak új SHA-256 lenyomatát kapják. Az eredeti és a redakció közötti megfeleltetés elkülönített, korlátozott naplóban marad.

### G4 – Kettős vak annotáció

Minden dokumentumot két, egymástól független annotátor (`ANNOTATOR_A`, `ANNOTATOR_B`) kap meg.

- Mindketten ugyanazt a redaktált bájtsorozatot látják.
- Nem látják egymás címkéjét, indoklását vagy automatikus kinyerési eredményét.
- Nem kapnak országos súlyt, programalkalmassági eredményt vagy elvárt címkét.
- Automatikus OCR vagy modell használható dokumentum-előkészítésre, de nem lehet ground truth; minden `OBS` címkéhez explicit oldalbizonyíték kell.
- A referencia-rendszer 55/45 °C értéke csak `REFERENCE_ASSUMPTION`; nem minősíthető a vizsgált épület megfigyelt hőfoklépcsőjének.
- Következtetett hőleadótípus nem `OBS`. Ha a dokumentum nem mondja ki vagy nem mutatja egyértelműen, `Q` és `NOT_STATED`/`UNREADABLE` a helyes kimenet.

A gépi rekord szerződése: [`schemas/oeny_heat_emitter_annotation.schema.json`](../../schemas/oeny_heat_emitter_annotation.schema.json).

### G5 – Eltérés és adjudikáció

A két elsődleges címke lényegi aláírása a következőkből áll:

- hőleadó-státusz és rendezett hőleadótípusok;
- hőmérséklet-státusz, előremenő/visszatérő érték és értékalap.

Egyezéskor nincs harmadik döntés. Eltéréskor egy harmadik, az első két címke eredetétől vak adjudikátor (`ADJUDICATOR`) újra megvizsgálja ugyanazt a redaktált forrást, és a két annotation ID-ra hivatkozó végső rekordot készít. Automatikus többségi vagy modellalapú felülírás tilos.

### G6 – Minőségkapu

Minden pilotnál közlendő:

- dokumentum- és rétegszám;
- PII-karanténba került fájlok száma, tartalom nélkül;
- hőleadó és hőmérséklet kitöltöttsége;
- nyers egyezési arány és Cohen-kappa a hőleadó-kategóriákra;
- hőmérsékletpárok abszolút eltérése;
- adjudikációs arány;
- olvashatatlan és nem közölt értékek aránya.

Javasolt, még nem jóváhagyott projektküszöbök (`PROPOSED_POL`): nulla PII-kiszivárgás; legalább 90% nyers hőleadó-egyezés; legalább 0,80 kappa; a közösen megtalált hőmérsékletpárok legalább 95%-án legfeljebb 1 °C annotátori eltérés. Ezek nem empirikus eredmények és az első batch előtt Josephnek kell jóváhagynia vagy módosítania őket; utólagos eredményhez igazításuk tilos.

### G7 – Országos felhasználhatóság

Az annotációs pontosság önmagában nem reprezentativitás. Országos becslés előtt külön szükséges:

- OÉNY-minta és KSH-lakásállomány összevetése;
- épülettípus × építési időszak × településtípus × fűtési mód rétegzés;
- tanúsítási ok, duplikált és megújított tanúsítványok kezelése;
- dokumentált mintasúly vagy kalibráció;
- a nem megfigyelt cellák és bizonytalanság közlése;
- Joseph jóváhagyása a publikálható aggregációra.

E kapu előtt nincs új országos radiátorarány, hőmérséklet-eloszlás, COP, retrofitköltség vagy alkalmaslakás-becslés.

## Annotációs kódkönyv

### Hőleadótípus

- `RADIATOR`
- `FLOOR_HEATING`
- `WALL_HEATING`
- `CEILING_HEATING`
- `FAN_COIL`
- `AIR_HEATING`
- `DIRECT_ELECTRIC`
- `OTHER`
- `NOT_STATED`
- `UNREADABLE`

Több explicit rendszer több elemként rögzítendő. A `NOT_STATED` és `UNREADABLE` nem keverhető más típussal. `OTHER` esetén `OTHER_NEEDS_CODEBOOK` review flag szükséges.

### Bizonyítékalap

- `TEXT_EXPLICIT`
- `TABLE_EXPLICIT`
- `SCHEMATIC_EXPLICIT`
- `PHOTO_EXPLICIT`
- `NONE`

Az `OBS` státuszhoz legalább egy explicit alap és oldalszám kell. `NONE` csak `Q` státusszal használható.

### Hőmérsékletalap

- `DESIGN_EXPLICIT`
- `CALCULATION_INPUT`
- `OPERATING_MEASURED`
- `REFERENCE_ASSUMPTION`
- `NOT_STATED`

Csak a dokumentumban az adott épülethez explicit megadott tervezési, számítási vagy mért pár lehet `OBS`. A referenciafeltételezés és a nem közölt érték `Q`.

## Gépi ellenőrzés

Végleges JSONL batch:

```powershell
python tools/validate_oeny_annotations.py annotations.jsonl
```

Egyedi, még pár nélküli rekord szerkezeti ellenőrzése:

```powershell
python tools/validate_oeny_annotations.py --records-only annotation.jsonl
```

A validátor szerkezeti és kereszt-rekord konzisztenciát vizsgál. Nem bizonyítja a jogszerű átadást, a tényleges anonimizálást, a dokumentumbeli címke helyességét vagy a reprezentativitást.
