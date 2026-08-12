# P1-B forráscsomag: B02 KSH adat- és archetípus-szerződés

Állapot: **API- és mezőszerződés ellenőrizve; alkalmas célállomány nincs kiszámítva**

Lekérdezés napja: **2026-08-12**

## Eredmény

A KSH 2022 népszámlálási adatbázisának `V67` verziójában négy B02-re használható adatfolyamot ellenőriztünk. A vármegye × településtípus alapmodellhez a `WBL011` fűtési és a `WBL017` felszereltségi adatfolyam a kanonikus páros; a `WBL010` és `WBL016` járási kontroll.

A két fő adatfolyam közös megfigyelt magja az építési időszak, falazat, alapterület-kategória, komfortosság és lakottság. A fűtési oldal fűtési módot és fűtőanyagot, a felszereltségi oldal kombinált fűtés/fűtőanyag-kódot és hőszivattyú-ellátottságot ad. A mérték minden esetben lakások előfordulásszáma.

## Ellenőrző megfigyelések

- `OBS`: a `WBL017` országos, lakott, minden más dimenzióban összesen, `HOSZIV=1` lekérdezése 67 853 lakást adott 2022-re;
- `OBS`: a `WBL011` ugyanilyen országos alaplekérdezésében 1 788 022 lakás szerepelt kizárólag hálózati gázzal, 129 294 kizárólag villamos energiával, 619 573 kizárólag fával, 831 922 többfajta tüzelőanyaggal és 618 724 távfűtéssel.

Ezek nem adhatók össze automatikusan más hierarchiaszintekkel, és egyik érték sem jelenti a programra technikailag alkalmas lakásállományt. Különösen a többtüzelős csoport további bontást igényel a gázkiváltási potenciálhoz.

## Módszertani döntés

Az archetípus-szerződésben `CONTRACTED` lett a terület, lakottság, építési időszak, falazat, alapterület, komfortosság, fűtési mód, fűtőanyag és meglévő hőszivattyú-jelző. Az épülettípus és hőleadó rendszer `GAP`; a primerenergia-igény `MODELLED`, nem `OBS`.

Ez a szétválasztás megakadályozza, hogy egy KSH aggregált népszámlálási mezőből indokolatlan műszaki alkalmasságot vagy energetikai teljesítményt vezessünk le.

## Publikálási és licenchatár

A KSH aggregált nyilvános adataihoz a KSH szerzői jogi és felhasználási feltételeit kell alkalmazni, forrásmegjelöléssel. A repó most csak a metaadatot, a mezőszerződést és a pontos kérésmintát tartalmazza; nyers API-válasz nincs Gitben.

## Nyitott kapuk

1. épülettípus és hőleadó rendszer hiteles mezője vagy validált proxyja;
2. a KSH kísérleti primerenergia-becslés letölthető mezőinek és kulcsainak rögzítése;
3. teljes, snapshotolt vármegye × településtípus kivonat és SHA-256;
4. ritka és hiányos archetípus-cellák lefedettségi jelentése;
5. Joseph által jóváhagyott műszaki alkalmassági és retrofit-szabály.

## Kanonikus fájlok

- [`registry/datasets.csv`](../../registry/datasets.csv)
- [`registry/archetype_dimensions.csv`](../../registry/archetype_dimensions.csv)
- [`modules/B02/data_contract.md`](../../modules/B02/data_contract.md)
- [`registry/open_questions.csv`](../../registry/open_questions.csv)
