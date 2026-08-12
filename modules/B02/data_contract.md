# B02 adat- és archetípus-szerződés

Állapot: **CONTRACTED részhalmaz, alkalmassági modell még nyitott**

API-verzió: **KSH V67**

Ellenőrzés napja: **2026-08-12**

## Határ

Ez a szerződés a 2022-es KSH népszámlálási adatbázisból reprodukálhatóan lekérhető, aggregált lakásjellemzőket rögzíti. Nem állítja, hogy a teljes lakásállomány vagy bármely tüzelőanyag-kategória hőszivattyúra alkalmas. A műszaki alkalmasság későbbi, szabályozott `DER` kimenet lesz.

## Kanonikus adatfolyamok

- `WBL011`: fűtési mód és fűtőanyag vármegye × településtípus bontásban;
- `WBL017`: felszereltség, köztük hőszivattyús fűtőberendezés, ugyanebben a területi bontásban;
- `WBL010` és `WBL016`: járási kontrollnézetek, nem az első modell-grain.

A géppel olvasható metaadat a [`registry/datasets.csv`](../../registry/datasets.csv), az archetípus-dimenziók szerződése a [`registry/archetype_dimensions.csv`](../../registry/archetype_dimensions.csv) fájlban van.

## Univerzum és kulcs

Az elsődleges lakásuniverzum a `LAKAS_OCS=DW_OC`, vagyis a lakott hagyományos lakások köre. A `TOTAL` és `DW_NOC` értékek kontrollként maradnak meg, de nem keverhetők a programalappal.

A kanonikus területi kulcs:

`TERUL_GEO3 × TERUL_TELTIP2`

Az archetípus első megfigyelt magja:

`EPEV_POC1 × FALA_V × LAT_V × KOMF × fűtési mód × fűtőanyag`

Ehhez kapcsolódik a `HOSZIV` meglévőberendezés-jelző. Az épülettípus kanonikus kategóriái szerződöttek, a WBL-kapcsolat azonban csak `ASS` proxy. A hőleadó rendszer `GAP`, a fajlagos primerenergia-igény `MODELLED`.

## Mérték és kódhierarchia

Mind a négy adatfolyam mértéke `OBS_VALUE`, jelentése előfordulások száma, kanonikus egysége `dwelling`.

A KSH kódlisták hierarchikusak. `TOTAL`, részösszeg és gyermek kód együttes összeadása tilos. Például a `FUEL2` többfajta tüzelőanyag részösszeg nem adható hozzá ismét a saját gyermekeihez. Minden aggregáció előtt levélkód-készletet kell választani és dokumentálni.

## Hiányzó és ismeretlen értékek

- `HOSZIV=9` jelentése nincs információ; nem azonos a `HOSZIV=0` értékkel.
- `WALL6`, egyéb tüzelőanyag vagy többtüzelős kategória nem bontható fel feltételezéssel.
- hiányzó épülettípus vagy hőleadó rendszer nem alakítható automatikusan alkalmas rekorddá;
- nyitott alapterület-sávhoz csak külön dokumentált `ASS` vagy `DER` pontbecslés rendelhető.

## Megfigyelt kontra becsült

A népszámlálási `OBS_VALUE` aggregált megfigyelés. A KSH kísérleti primerenergia-igény viszont modellbecslés; ezt `MODELLED` mezőként, módszertani verzióval és bizonytalansággal kell továbbadni B05 és B06 felé. Az egyik nem örökölheti a másik `OBS` státuszát.

## Energetikai modellkapcsolat

A KSH 2025-ös kísérleti statisztikája külön random-forest modellt és publikált eredményt ad családi házakra és többlakásos épületekre. Ez alapján a B02 kanonikus épülettípus-kódjai:

- `FAMILY_HOUSE`;
- `MULTI_DWELLING`.

A publikált HTML-ből determinisztikusan kinyert adatok 16 épülettípus × építési időszak átlagot és 944 energiaigény-eloszlási cellát tartalmaznak. A binekben 4 575 790 lakás szerepel; a módszertani 4 580 538 lakásos univerzumhoz képest a levezetett maradék 4 748 lakás, a publikált-bin lefedettség 0,9989634405390808.

Ez nem jelenti azt, hogy a teljes állomány energetikai tanúsítvánnyal rendelkezik. A módszertan 279 020 kapcsolt tanúsítványt és kerekítve 6,1%-os kapcsolási arányt közöl. Az egész állományra kiterjesztett energiaigény `MODELLED`, a lefedettségi arány pedig `DER`.

A népszámlálási `Y_GE2011` kategória és az energetikai publikáció `2011–2015`, illetve `2016–2022` kategóriái nem azonosak. Összevonásuk csak a publikált cellaszámokkal súlyozott, külön képlettel dokumentált transzformáció lehet.

## WBL épülettípus-proxy

A `WBL011` V67 struktúrájában nincs épülettípus-dimenzió. A KSH 2015-ös, 20 000 címes lakásfelmérésének 1. táblája viszont településtípusonként közli az 1–3, illetve 4 vagy több lakásos épületekben lévő lakott lakásokat. A szerződött proxy:

1. `1–3` lakás az épületben → `FAMILY_HOUSE`;
2. `4–12`, `13–24`, `25–50`, `50-nél több` → `MULTI_DWELLING`;
3. településtípusonként a 2015-ös lakottlakás-arány vetítése a 2022-es `WBL011`, `DW_OC` összegre;
4. `ROUND_HALF_UP` kerekítés a családi házas ágon, a többlakásos ág pedig maradék.

Az eredmény 4 008 541 lakott lakásból 2 423 136 `FAMILY_HOUSE` és 1 585 405 `MULTI_DWELLING`. Mindkettő `ASS`. Budapest és község kategóriája pontosan illeszkedik; a 2015-ös `Megyeszékhely`–2022-es `MJV`, valamint `Város`–`EV` kapcsolat közelítő. A proxy nem vihető át automatikusan vármegye, építési időszak, falazat, alapterület, komfortosság vagy fűtési rendszer szerinti WBL alcellákra.

A KSH táblájának kerekített épületnagyság-sorai 3 860 700 lakott lakást adnak, miközben a közölt országos összesen 3 860 600. A 100 lakásos kerekítési maradvány megmarad, nem kerül rejtett korrekcióra.

## OÉNY hőleadó- és hőmérsékletmező-audit

A teljes Hosszú Távú Felújítási Stratégia rögzíti, hogy a korszerű hőleadók alacsonyabb fűtőközeg-hőmérsékleten is megfelelő komfortot adhatnak. A dokumentum azonban nem közöl országos radiátor-, felületfűtés- vagy fan-coil-megoszlást és tervezési előremenő hőmérsékletet. Emiatt fűtési mód vagy tüzelőanyag alapján hőleadó nem imputálható.

A P1-E audit igazolta, hogy a 176/2008. (VI. 30.) Korm. rendelet alátámasztó munkarésze kezeli a hőfoklépcsőt, az OÉNY pedig JSON/XML forrásfájlt és kötelező számítási PDF-et tárol. A `v3.0.14801` feltöltési sémában ugyanakkor nincs dedikált mező a jelenlegi hőleadótípusra vagy a tervezési előremenő/visszatérő hőmérsékletre. A hőfoklépcső dokumentumba ágyazott adatjelölt; a kötelező hőleadófotó képi bizonyíték. A javaslati blokk `HeatExchangers` és `FanCoilUnits` elemei nem a jelenlegi állapot megfigyelései.

A gap lezárásának első lépése ezért anonimizált OÉNY-adatszótár és strukturált pilotminta beszerzése, mezőhiány- és kinyerhetőségi próbával. PDF-minta csak akkor kérhető, ha normalizált mező nincs, az adatgazda az átadást jogszerűnek ítéli, a személyes adatok eltávolíthatók, a biztonságos csatorna rögzített és Joseph külön jóváhagyta a második kaput. Ha ez nem ad reprodukálható hőleadótípust és hőfoklépcsőt, épülettípus × kor × településtípus × fűtési mód szerint rétegzett reprezentatív műszaki felmérés szükséges. Minimális mezők: hőleadótípus, tervezési előremenő/visszatérő hőmérséklet, helyiséghőterhelés, beépített hőleadó-kapacitás, hidraulikai topológia és szabályozhatóság.

Az OÉNY tanúsítványállomány tranzakciós és szabályozási okból szelektált. Teljes hozzáférés esetén is tilos közvetlen országos megoszlásként kezelni; KSH-állományhoz kalibrált rétegzés, duplikációkezelés és dokumentált mintasúly szükséges.

### P1-F beszerzési és annotációs szerződés

A küldésre előkészített, de még nem jóváhagyott adatigénylési szöveg: [`docs/data_requests/P1F_OENY_DATA_REQUEST_DRAFT.md`](../../docs/data_requests/P1F_OENY_DATA_REQUEST_DRAFT.md). A kérés terhelés- és adatminimalizáló sorrendje:

1. meglévő adatszótár, verziótörténet, rekordszám és mezőkitöltöttség;
2. anonimizált strukturált pilotminta;
3. csak külön megállapodással és jóváhagyással redaktált számítási-PDF-pilot.

A valós fájlok nem kerülhetnek Gitbe. Feldolgozásukhoz kötelező a [`P1F OÉNY mintafeldolgozási protokoll`](../../docs/protocols/P1F_OENY_SAMPLE_PROCESSING_PROTOCOL.md), két független annotátor, eltéréskor harmadik adjudikátor, valamint a gépi [`oeny_heat_emitter_annotation.schema.json`](../../schemas/oeny_heat_emitter_annotation.schema.json) szerződés. A referencia-hőfoklépcső nem válhat `OBS` épületadattá, és következtetett hőleadótípus sem emelhető megfigyeléssé.

### P1-G archetípus-lefedettség és joinability

A P1-G gépi leltár 16 pozitív épülettípus × építési időszak energetikai cellát, 944 energiaigény-bint – ebből 864 pozitív és 80 nulla lakásszámút – valamint 8 településtípus × épülettípus proxycellát rögzít. A 4 575 790 lakásos energetikai binösszeg `DER` a KSH `MODELLED` eloszlásából; a 4 008 541 lakásos épülettípus-proxy továbbra is `ASS`.

A [`b02_archetype_joinability_2022.csv`](../../data/processed/b02/b02_archetype_joinability_2022.csv) fail-closed szerződése szerint a WBL011/WBL017, az energetikai modell, az épülettípus-proxy és a leendő OÉNY-hőleadó minta eltérő grain. A külön margók keresztbeszorzása nem képezhet `OBS` vagy `DER` teljes archetípust. Ilyen összekapcsolás csak új közös adat vagy Joseph által jóváhagyott, kalibrált statisztikai modell alapján készülhet.

## Reprodukálható lekérdezés

Az API a dimenziókat a struktúrában megadott sorrendben, `/d/` útvonalon fogadja. Példa az országos, lakott, hőszivattyúval rendelkező lakások kontroll-lekérdezésére:

```text
https://nepszamlalas2022.ksh.hu/api/dataflows/WBL017/V67/d/TIME_PERIOD22:2022,TERUL_GEO3:HU,TERUL_TELTIP2:HU,LAKAS_OCS:DW_OC,EPEV_POC1:TOTAL,FALA_V:TOTAL,LAT_V:TOTAL,KOMF:TOTAL,FUTMODAG_V3:TOTAL,INTERNET:TOTAL,LEGKONDI:TOTAL,HOSZIV:1,NAPELEM:TOTAL,NAPKOLL:TOTAL
```

Az ellenőrzéskor a válasz `OBS_VALUE=67853` volt (`OBS`, 2022). Ez kizárólag baseline sanity check: nem a technikailag alkalmas célállomány.

## Snapshot-szabály

Minden modellfuttatáshoz rögzíteni kell:

1. a `V67` vagy későbbi, explicit API-verziót;
2. a teljes kérés-URL-t;
3. a válasz nyers bájtjainak SHA-256 értékét;
4. a lekérési időpontot és a KSH felhasználási feltételeit;
5. a struktúra- és adatválasz párosát ugyanazon API-verzióból.

A `data/raw/` nincs Gitben. Nyers snapshot publikálása előtt külön licenc- és méretellenőrzés szükséges.

Az élő, rögzített szerkezet és a kontrollmegfigyelés ellenőrzése:

```powershell
python tools/validate_b02_ksh_api.py
python tools/build_b02_building_type_proxy.py --output-dir data/processed/b02 --retrieved-at 2026-08-12
```

Ez hálózati ellenőrzés, ezért nem része az alap GitHub Actions munkafolyamatnak. A helyi registry- és egységtesztek hálózat nélkül futnak.

## Következő kapu

A B02 következő számszerű kapuja csak akkor nyitható, ha elkészül:

- az OÉNY üzemeltetőjétől kapott adatszótár és anonimizált mintakivonat alapján a hőleadó/hőfoklépcső kinyerhetőségének bizonyítása, vagy reprezentatív műszaki felmérés;
- a településtípusos épülettípus-proxy friss forrással vagy adminisztratív adattal történő validálása és az alcella-kapcsolat bizonyítása;
- az archetípus-cellák lefedettségi és ritkasági jelentése;
- a műszaki kizárási és minimális retrofit-szabály Joseph jóváhagyásával;
- az országos/vármegyei visszaegyeztetés és bizonytalansági tartomány.

Feldolgozott energetikai csomag: [`data/processed/b02/`](../../data/processed/b02/README.md).
