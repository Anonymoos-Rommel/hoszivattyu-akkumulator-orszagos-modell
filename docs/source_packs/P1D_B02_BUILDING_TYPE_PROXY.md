# P1-D forráscsomag: B02 WBL épülettípus-proxy és hőleadó adatgap

Állapot: **reprodukálható épülettípus-proxy elkészült (`ASS`); országos hőleadó-adat nem azonosítható**

Lekérdezés napja: **2026-08-12**

## Döntési eredmény

A 2022-es népszámlálási `WBL011` és `WBL017` adatfolyamok nem tartalmaznak épülettípus- vagy hőleadó-dimenziót. Ezért közvetlen, megfigyelt WBL-cellajoin nem készíthető.

A KSH *Miben élünk?* 2015-ös, 20 000 címes rétegzett lakásfelmérése ugyanakkor településtípus szerint közli az 1–3 és 4 vagy több lakásos épületekben lévő lakások becsült számát. Ez hivatalos, de hét évvel korábbi és részben eltérő településkategóriájú forrás, ezért csak `ASS` proxyként használható.

## Források

1. [KSH, *Miben élünk? – A 2015. évi lakásfelmérés főbb eredményei*](https://www.ksh.hu/docs/hun/xftp/idoszaki/pdf/miben_elunk15.pdf), 1. tábla, nyomtatott 6. oldal: 1–3, 4–12, 13–24, 25–50 és 50-nél több lakásos épület; Budapest, megyeszékhely, város és község; teljes és lakott lakásállomány.
2. [KSH Népszámlálás 2022 adatbázis](https://nepszamlalas2022.ksh.hu/adatbazis/), `WBL011/V67`: lakott hagyományos lakások (`DW_OC`) `FV`, `MJV`, `EV`, `K` levélkódok szerint.
3. [Hosszú Távú Felújítási Stratégia](https://energy.ec.europa.eu/system/files/2021-08/hu_2020_ltrs_en_0.pdf), 30. oldal: a korszerű hőleadó alacsonyabb fűtőközeg-hőmérsékleten is megfelelő komfortot biztosíthat, de a stratégia nem közöl országos hőleadó-állományt.

## Reprodukálható transzformáció

Kategóriatérkép:

- `1–3` lakás az épületben → `FAMILY_HOUSE`;
- `4–12`, `13–24`, `25–50`, `50-nél több` → `MULTI_DWELLING`.

Településtípusonként:

`proxy_count(type, s) = round_half_up(WBL_2022_DW_OC(s) × KSH_2015_occupied_share(type, s))`

A családi házas ág kerekített, a többlakásos ág a településtípus WBL-összegének maradéka. Így nincs darabszámvesztés.

| WBL településtípus | WBL lakott lakás (`OBS`) | Családi ház proxy (`ASS`) | Többlakásos proxy (`ASS`) |
| --- | ---: | ---: | ---: |
| Budapest (`FV`) | 800 338 | 144 423 | 655 915 |
| Megyei jogú város (`MJV`) | 867 129 | 307 566 | 559 563 |
| Egyéb város (`EV`) | 1 243 229 | 888 698 | 354 531 |
| Község (`K`) | 1 097 845 | 1 082 449 | 15 396 |
| **Összesen** | **4 008 541** | **2 423 136** | **1 585 405** |

A proxy országos aránya 60,4493% családi ház és 39,5507% többlakásos épület. Ez a lakott WBL-univerzum becslése, ezért nem hasonlítható közvetlenül a teljes lakásállomány energetikai modelljének arányához.

## Minőségi kontrollok

- PDF: 52 oldal, kötelező szöveges kontrollok és SHA-256 lenyomat;
- KSH 2015 1. tábla: 40 megőrzött forrássor;
- a kerekített lakott épületnagyság-sorok összege 3 860 700, a közölt országos összesen 3 860 600: maradék `-100` lakás;
- `WBL011` levélkódok: 4 008 541 lakás;
- proxy-visszaegyeztetés: 4 008 541, maradék `0`;
- minden proxyrekord `ASS` státuszú;
- determinisztikus újrageneráláskor a három kimenet byte-azonos.

## Kategória- és időbeli korlátok

- Budapest ↔ `FV` és község ↔ `K` pontos kategóriakapcsolat;
- `Megyeszékhely` ↔ `MJV` és `Város` ↔ `EV` csak közelítő kapcsolat;
- a 2015-ös arány nem tükrözi automatikusan a 2015–2022 közötti állományváltozást;
- a proxy nem változik vármegye, építési időszak, falazat, alapterület, komfortosság, fűtési mód vagy tüzelőanyag szerint;
- ezért a proxy csak országos és településtípusos baseline/szenzitivitási számításban használható.

## Hőleadó: igazolt hiány

A vizsgált hivatalos források műszaki jelentőségét alátámasztják, de országos előfordulási arányt nem adnak a következőkre:

- radiátor és annak méretezési hőmérséklete;
- padló-, fal- vagy mennyezetfűtés;
- fan-coil;
- egy- vagy kétcsöves hidraulika;
- helyiségenkénti szabályozhatóság;
- beépített hőleadó-kapacitás.

Fűtési mód, fűtőanyag, komfortfokozat vagy építési kor alapján ezek nem imputálhatók `OBS` vagy `DER` státusszal.

## Beszerzési terv

Első választás: az országos épületenergetikai vagy építésügyi nyilvántartások anonimizált, aggregált mezőauditja, amennyiben a hőleadó és tervezési hőmérséklet ténylegesen tárolt mező.

Második választás: rétegzett országos műszaki felmérés legalább az alábbi rétegekkel:

`épülettípus × építési időszak × településtípus × fűtési mód`

Kötelező mérési mezők: hőleadótípus, előremenő/visszatérő tervezési hőmérséklet, helyiséghőterhelés, beépített hőleadó-teljesítmény, hidraulikai topológia, beszabályozottság és szabályozhatóság.

## Nem következik ebből

- nincs új technikailag alkalmas lakásszám;
- nincs hőszivattyú-COP vagy méretezési eredmény;
- nincs radiátorcsere- vagy retrofitköltség;
- nincs vármegyei épülettípus-eloszlás;
- nincs automatikus programjogosultság.
