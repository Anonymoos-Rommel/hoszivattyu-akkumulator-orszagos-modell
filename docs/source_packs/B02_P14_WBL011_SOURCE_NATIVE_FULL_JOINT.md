# B02-P14 — WBL011 source-native complete-joint authority

Állapot: **SOURCE-NATIVE FULL JOINT QUALIFIED / REPOSITORY MATERIALIZATION PENDING**

Kapcsolódó kérdések: `Q-B02-001`, `Q-B02-002`, `Q-B02-004`

## Cél

P14 azt a P9-ben nyitva maradt kérdést vizsgálja, hogy a pinned KSH Népszámlálás 2022 `WBL011/V67` forrás ténylegesen publikálja-e egyetlen source-native observation grainen a B02 stock-dimenziók közös eloszlását, vagy csak külön margók érhetők el.

A kanonikus határ:

`SOURCE-NATIVE COMPLETE WBL011 JOINT != REPOSITORY-MATERIALIZED COMPLETE WBL011 JOINT != POPULATED CURRENT-STOCK ARCHETYPE`

és változatlanul:

`SOURCE-NATIVE JOINT != SYNTHETIC CROSS-JOIN`

## Lekérdezett source-native grain

A live source-acquisition probe a `WBL011/V67` dataflowban egyszerre választotta ki a következő nem-`TOTAL` dimenziókat:

- `TERUL_GEO3`: a 20 vármegye/Budapest kód;
- `TERUL_TELTIP2`: `FV`, `MJV`, `EV`, `K`;
- `LAKAS_OCS`: `DW_OC`;
- `EPEV_POC1`: hét szerződött építési időszak;
- `FALA_V`: öt falazati kategória;
- `LAT_V`: nyolc alapterület-kategória;
- `KOMF`: öt komfortkategória;
- `FUTES_TOH`: `HEAT111`, `HEAT112`, `HEAT12`, `NHEAT`;
- `FUTAGOK`: `FUEL11`, `FUEL12`, `FUEL13`, `FUEL14`, `FUEL21`, `FUEL22`, `FUEL23`, `FUEL3`.

Minden vármegyére/Budapestre külön, ugyanezen source-flowból független `TOTAL` kontroll is le lett kérve.

## Bizonyított eredmény

A teljes országos source surface:

- **20/20** területi válasz exact `delta = 0`;
- source-native full-joint visszaadott rekordok: **116 452**;
- full-joint lakásszám összege: **4 008 541**;
- független county `TOTAL` kontrollok összege: **4 008 541**;
- országos eltérés: **0**;
- a 20 full-joint response összes nyers mérete: **27 375 751 byte**.

A 20 full-joint és 20 független `TOTAL` válasz exact SHA-256 lenyomata a `registry/b02_wbl011_source_native_full_joint.csv` fájlban van rögzítve. A NATIONAL sor összegezett kontroll, ezért nem állít egy nem lekért, egyetlen országos payloadhoz tartozó SHA-t.

Ez bizonyítja, hogy:

> a WBL011 szükséges stock-dimenziói source-native módon együtt megfigyeltek, és a lekérdezett non-TOTAL partíció exact módon lefedi a 4 008 541 lakott lakásos WBL011 univerzumot.

A korábbi P1-H külön `WBL011_ENVELOPE` és `WBL011_HEATING_FUEL` materializációja tehát **nem a KSH source korlátja**, hanem a jelenlegi repository-materializáció korlátja.

## Ami ettől még nincs materializálva

P14 nem commitolja a 116 452 full-joint observation sort a repositoryba. A meglévő feldolgozott adat továbbra is a P1-H külön projekcióit tartalmazza.

Ezért:

- a source-native full joint: **QUALIFIED**;
- a full-joint repository artifact: **NOT MATERIALIZED**;
- a külön P1-H projekciók cellaszintű cross-joinja továbbra is **tiltott**;
- a P9 admission gate nem tekintheti a source elérhetőségét materializált current-stock panelnek.

A korábbi túl tág blocker ezért pontosítandó:

`NO_COMPLETE_WBL_JOINT` → `NO_MATERIALIZED_COMPLETE_WBL_JOINT`

## Ami P14-ből nem következik

A WBL011 source-native full joint nem tartalmaz és nem bizonyít:

- current `FAMILY_HOUSE` / `MULTI_DWELLING` stock assignment authorityt;
- primary-energy-to-WBL link authorityt;
- current heat-emitter evidence-et;
- current design-temperature evidence-et;
- hidraulikai readiness-t;
- technikai alkalmassági vagy programjogosultsági lakásszámot.

Különösen:

`COMPLETE WBL011 STOCK JOINT != COMPLETE B02 ARCHETYPE`

mert a building-type és primary-energy kapcsolatok továbbra is külön authority-problémák.

## P9 és Q-hatás

P14 valódi blocker reductiont ad: a **source-native WBL011 joint existence/completeness kérdés lezárható**. A current-stock archetype azonban `Q`, mert:

1. a 116 452 full-joint sor még nincs determinisztikusan repository-artifactként materializálva;
2. current building-type link authority továbbra sincs;
3. primary-energy-to-WBL link authority továbbra sincs.

A technical-readiness archetype ezen felül current heat-emitter és design-temperature evidence nélkül szintén `Q`.

Ezért:

- `Q-B02-001`: **OPEN**;
- `Q-B02-002`: **OPEN**;
- `Q-B02-004`: **OPEN**;
- national technical/final eligible count: blank / `Q`;
- B02 readiness: **55%**;
- **no readiness uplift**;
- OÉNY request: **nem lett elküldve**.

## Következő tiszta adatlépés

A WBL011 teljes stock-joint tényleges használatához külön determinisztikus materializáció szükséges, amely:

- ugyanazt a pinned `WBL011/V67` source grain-t használja;
- a 20 területi válasz lineage-ét megőrzi;
- csak ténylegesen visszaadott observationöket materializál;
- exact **116 452** rekord- és **4 008 541** population-controlt reprodukál;
- hash-manifestet készít;
- nem kapcsol hozzá building type, primary energy, emitter vagy temperature dimenziót bizonyíték nélkül.
