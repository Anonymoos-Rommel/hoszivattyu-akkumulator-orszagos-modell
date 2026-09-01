# B10 — Hálózatfejlesztés

Állapot: **IN PROGRESS — P1 bounded DSO consumption-headroom contract**

B10 feladata a regionális hálózati readiness, a program nélküli baseline
infrastruktúra és a programhoz rendelhető inkrementális hálózati beavatkozás
szétválasztása. A modul nem gyárthat hálózati kapacitást B08 vagy B09 országos
/control-area adataiból.

## B10-P1 scope

A P1 első source-native authority családja az MVM DÉMÁSZ hivatalos,
fogyasztási célú alállomási szabadkapacitás-publikációja és annak módszertani
magyarázata.

A runtime szerződés kizárólag az alábbi szemcsét fogadja:

- hálózati engedélyes: `MVM DEMASZ`;
- régióséma: `DSO_SUBSTATION`;
- állomás + source-native állomáskód + feszültségszint;
- külön `CURRENT` és `FIVE_YEAR` horizont;
- N-1 transzformátorkapacitás MW;
- téli esti csúcsterhelés MW;
- publikált elvi szabad kapacitás MW.

A két horizont nem mosható össze és az alállomási headroom **nem összeadható**
országos vagy DSO-szintű headroommá. A topológiai átfedés, párhuzamos táplálás,
középfeszültségű korlát, zárlati szint, feszültségminőség és csatlakozási
műszaki feltételek miatt ilyen aggregációhoz külön authority szükséges.

## Truth és provenance

A P1 nem közvetlen PDF-parser. Az input egy külső acquisition lépésben előállított,
normalizált TSV-transzkripció. Emiatt a runtime rekord **soha nem `OBS`**:

- `DER`: csak explicit reuse clearance, source-PDF SHA-256, normalized-text
  SHA-256 és `VERIFIED_AGAINST_SOURCE` mellett;
- `Q`: minden más esetben, beleértve az ismeretlen/restricted reuse-t,
  ellenőrizetlen extractiont vagy hiányzó checksumot.

A publikált DSO-szabadkapacitás maga is tájékoztató / számított hálózati érték.
A source semantics ezért kötelezően:
`PUBLISHED_INDICATIVE_DSO_ESTIMATE_NOT_CONNECTION_AUTHORITY`.

## MGT authority

A publikált szabad kapacitás nem csatlakozási engedély. A runtime minden
headroom-rekordhoz és assessmenthez `MGT_REQUIRED` authority-jelölést tart fenn.
Egyedi csatlakoztathatóságot a P1 nem állít.

## B08/B09 kapcsolat

`assess_incremental_demand()` csak akkor hasonlíthat össze terhelésnövekményt a
publikált headroommal, ha az upstream demand már **pontosan ugyanarra a
`DSO_SUBSTATION` region_id-ra** van bizonyítottan leképezve. A függvény nem készít:

- ENTSO-E control-area → DSO alállomás mappinget;
- vármegye → DSO/alállomás mappinget;
- B01 state vagy háztartásszám alapú proxy-szétosztást;
- B08 vagy B09 országos/nemzeti scalinget.

Ezért a jelenlegi B08/B09 control-area evidence önmagában nem használható
B10 állomási assessmentre.

## Out of scope P1

- baseline infrastruktúra státuszledger feltöltése;
- inkrementális CAPEX-attribúció;
- hálózatfejlesztési projektköltség;
- közép- és kisfeszültségű topológiai power-flow;
- reinforcement-optimalizáció;
- county↔DSO crosswalk;
- országos headroom;
- MGT vagy csatlakozási döntés;
- további DSO-k adapterei.

`registry/regional_readiness.csv`, `registry/baseline_infrastructure.csv` és
`registry/incremental_capex_attribution.csv` P1-ben szándékosan nem kap kézzel
átírt numerikus sort.

## Nyitott kapuk

- Q-B01-002: kanonikus területi megfeleltetés továbbra is OPEN;
- Q-B10-001: baseline vs program-inkrementális infrastruktúra/CAPEX OPEN;
- Q-B10-002: baseline státuszok teljesülési valószínűsége/időzítése OPEN;
- országos DSO coverage és géppel reprodukálható source acquisition külön későbbi kapu.
