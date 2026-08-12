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

Ehhez kapcsolódik a `HOSZIV` meglévőberendezés-jelző. Az épülettípus, hőleadó rendszer és fajlagos primerenergia-igény még nem lezárt, ezért ezek `GAP`, illetve `MODELLED` státuszúak.

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
```

Ez hálózati ellenőrzés, ezért nem része az alap GitHub Actions munkafolyamatnak. A helyi registry- és egységtesztek hálózat nélkül futnak.

## Következő kapu

A B02 következő számszerű kapuja csak akkor nyitható, ha elkészül:

- a hőleadó rendszer elsődleges forrása vagy igazolt proxyja;
- a népszámlálási WBL-cellák és a két energetikai épülettípus reprodukálható kapcsolata;
- az archetípus-cellák lefedettségi és ritkasági jelentése;
- a műszaki kizárási és minimális retrofit-szabály Joseph jóváhagyásával;
- az országos/vármegyei visszaegyeztetés és bizonytalansági tartomány.

Feldolgozott energetikai csomag: [`data/processed/b02/`](../../data/processed/b02/README.md).
