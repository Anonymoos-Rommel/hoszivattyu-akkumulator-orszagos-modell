# P1-H forráscsomag: B02 KSH WBL közös cellák

Állapot: **MATERIALIZED részprojekciók; teljes archetípus-joint továbbra is `Q`**

Issue: [#36](https://github.com/Anonymoos-Rommel/hoszivattyu-akkumulator-orszagos-modell/issues/36)

Kapcsolódó kérdések: `Q-B02-001`, `Q-B02-002`, `Q-B02-004`

Ellenőrzés napja: **2026-08-12**

> **Current-state supersession — B02-P15 / 2026-09-05:** P1-H eredetileg három részprojekciót materializált. P15 ugyanebben a canonical extractorban hozzáadta a direct `WBL011_FULL_STOCK_JOINT` projekciót: 116 452 OBS sor / 4 008 541 lakás. A lentebbi, három projekcióra és 60 kérésre vonatkozó számok a történeti P1-H snapshotot írják le; a current state-et a P15 source pack és a current manifest adja. A separate envelope/heating margók synthetic cellajoinja továbbra is tiltott; combined WBL011 elemzéshez a direct full joint használandó.

## Eredmény

A KSH 2022. évi népszámlálási adatbázisának rögzített `V67` verziójából három, egymástól elkülönített közös megfigyelési projekció készült. Egy sor minden esetben egyetlen KSH API-válasz `OBS_VALUE` rekordja; külön margók keresztbeszorzása vagy projekciók közötti cellajoin nem történt.

| Projekció | Együtt megfigyelt grain | Visszaadott cella | Visszaadott lakásszám összege | Státusz |
|---|---|---:|---:|---|
| `WBL011_ENVELOPE` | vármegye × településtípus × építési időszak × falazat × alapterület × komfort | 32 655 | 4 008 541 | cellák `OBS`, leltár `DER` |
| `WBL011_HEATING_FUEL` | vármegye × településtípus × építési időszak × fűtési mód × tüzelőanyag | 7 682 | 4 008 541 | cellák `OBS`, leltár `DER` |
| `WBL017_HEAT_PUMP_BASELINE` | vármegye × településtípus × építési időszak × kombinált fűtés/tüzelőanyag × meglévő hőszivattyú-jelenlét | 7 623 | 3 919 564 | cellák `OBS`, leltár `DER` |

Az első két, külön-külön lekérdezett WBL011-projekció pontosan visszaadja a szerződött 4 008 541 lakott hagyományos lakásos univerzumot. A két nézet mind a 406 közös vármegye × településtípus × építési időszak csoportban azonos összegre egyezik. Ez nem jogosítja fel a modellt arra, hogy az épületburok- és a fűtés–tüzelőanyag-projekciót cellaszinten összekapcsolja.

## Lekérdezési határ

Minden projekció a húsz `TERUL_GEO3` vármegye/Budapest leaf kódra külön kérésként futott, összesen 60 API-kéréssel. A változó dimenziókban explicit kódhalmaz szerepel; a nem vizsgált dimenziókat `TOTAL` tartja fixen. Az univerzum mindenhol `2022` és `LAKAS_OCS=DW_OC`.

- struktúrák: [`WBL011/V67`](https://nepszamlalas2022.ksh.hu/api/structure/WBL011/V67), [`WBL017/V67`](https://nepszamlalas2022.ksh.hu/api/structure/WBL017/V67);
- adatbázis: [KSH Népszámlálás 2022 adatbázis](https://nepszamlalas2022.ksh.hu/adatbazis/);
- felhasználási feltételek: [KSH Népszámlálás 2022](https://nepszamlalas2022.ksh.hu/felhasznalasi-feltetelek).

Forrás: Központi Statisztikai Hivatal (KSH).

A manifest minden kérés teljes URL-jét, visszaadott rekordszámát, byte-méretét és SHA-256 lenyomatát tárolja. A nyers válaszfájlok a nyilvános repóba nem kerültek be.

## Kódhierarchia-kontroll

A változó dimenziókban általában a hierarchia leaf kódjai szerepelnek. A `FUTES_TOH` kivétel: a publikált kódlistában a `NHEAT21` szülőmutatója ellentmondásos, és az API-ban a `NHEAT21` rekordjai pontosan megismétlik a `NHEAT` rekordokat. A kettős számlálás elkerülésére a diszjunkt analitikai partíció:

`HEAT111 + HEAT112 + HEAT12 + NHEAT`

Ez a tüzelőanyag-leaf kódokkal együtt pontosan 4 008 541 lakásra egyezik vissza. A kivétel a kinyerőben és a manifestben is explicit; nem általános leaf-szabály módosítása.

## Ritkaság és nem visszaadott kombinációk

Az API a vizsgált kérésekben csak pozitív, legalább 1 lakásos rekordokat adott vissza. A leltár emiatt külön kezeli:

- a visszaadott pontos lakásszámot és annak leíró gyakorisági sávját;
- a teljes kartéziánus jelölt rácsot;
- a nem visszaadott kombinációk számát.

| Projekció | Jelölt kombináció | Visszaadott | Nem visszaadott | 1 lakásos | 2–4 lakásos | 5–9 lakásos |
|---|---:|---:|---:|---:|---:|---:|
| `WBL011_ENVELOPE` | 112 000 | 32 655 | 79 345 | 5 890 | 6 994 | 4 499 |
| `WBL011_HEATING_FUEL` | 17 920 | 7 682 | 10 238 | 478 | 710 | 646 |
| `WBL017_HEAT_PUMP_BASELINE` | 21 840 | 7 623 | 14 217 | 913 | 1 074 | 790 |

A nem visszaadott kombináció **nem bizonyított nulla**. Lehet szerkezetileg értelmetlen, tényleges nulla, adatvédelmi okból nem közölt vagy másként nem elérhető. A gyakorisági sávok csak leíró leltárak; nem állítják, hogy a KSH adatvédelmi küszöbei vagy statisztikai megbízhatósági kategóriái lennének.

## Hőszivattyú-baseline

A WBL017 részprojekcióban a visszaadott összeg:

- `HOSZIV=1`: 61 559 lakás;
- `HOSZIV=0`: 3 855 849 lakás;
- `HOSZIV=9`: 2 156 lakás;
- összesen: 3 919 564 lakás.

Ez 88 977 lakással kisebb a WBL011 lakottlakás-univerzumnál, a `HOSZIV=1` érték pedig 6 294-gyel kisebb a minden fűtési dimenzióban `TOTAL` országos 67 853-as kontrollnál. A különbség a kiválasztott kombinált fűtés/tüzelőanyag leaf-projekció lefedetlensége; nem kerül nullának, „nincs hőszivattyú” kategóriának vagy más kódnak imputálásra.

A `HOSZIV=1` meglévő berendezés megfigyelése, **nem műszaki alkalmasság**. Nem bizonyít megfelelő hőleadót, hőfoklépcsőt, épületburkot, villamos csatlakozást vagy gazdaságosságot.

## Tiltott következtetések

- Az épületburok- és fűtésprojekció **nem kapcsolható össze cellaszinten**.
- A WBL017 hőszivattyú-baseline nem kapcsolható cellaszinten a WBL011 buroktáblához.
- Az `ASS` épülettípus-proxy és a `MODELLED` primerenergia-eloszlás nem örökölhet `OBS` státuszt.
- A nem visszaadott kombináció nem alakítható automatikusan nulla vagy kizárt lakássá.
- A teljes WBL × épülettípus × primerenergia × hőleadó × hőmérséklet archetípus továbbra is `Q`.

## Reprodukció

```powershell
python tools/extract_b02_ksh_wbl_joint_cells.py --output-dir data/processed/b02 --retrieved-at 2026-08-12
python tools/build_b02_archetype_coverage.py --data-dir data/processed/b02 --retrieved-at 2026-08-12
python -m unittest discover -s tests -v
```

Az első parancs hálózati művelet, ezért az offline GitHub Actions teszt nem futtatja újra. A commitolt CSV-ket és a manifest hashkontrolljait a tesztek hálózat nélkül ellenőrzik.

## Következő B02 kapu

1. a WBL017 leaf-projekció 88 977 lakásos lefedetlenségének külön KSH-kód- és aggregációs auditja;
2. országos és vármegyei kontrollösszegek automatikus összevetése minden projekcióra;
3. a teljes többdimenziós joint csak explicit, méret- és adatvédelmi tervvel materializálható;
4. az OÉNY-adatkérés továbbra is Joseph külön jóváhagyási kapuja;
5. műszaki alkalmassági vagy retrofit-szabály csak külön, jóváhagyott B02 döntéssel készülhet.
