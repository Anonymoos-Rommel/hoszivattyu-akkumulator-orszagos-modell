# B10 — Hálózatfejlesztés

Állapot: **IN PROGRESS — P1 bounded DSO consumption-headroom contract**

B10 feladata a regionális hálózati readiness, a program nélküli baseline
infrastruktúra és a programhoz rendelhető inkrementális hálózati beavatkozás
szétválasztása. A modul nem gyárthat hálózati kapacitást B08 vagy B09 országos
/control-area adataiból.

## B10-P1 scope

A P1 első source-native authority családja az **MVM Démász Áramhálózati Kft.** hivatalos,
fogyasztási célú alállomási szabadkapacitás-publikációja és annak módszertani
magyarázata.

A runtime szerződés kizárólag az alábbi szemcsét fogadja:

- hivatalos publisher: `MVM Démász Áramhálózati Kft.`;
- source-native hálózati engedélyes mező: `MVM DEMASZ`;
- régióséma: `DSO_SUBSTATION`;
- állomás + source-native, négybetűs állomáskód + feszültségszint;
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

## B10-P2 — OPUS TITÁSZ second-DSO evidence

A P2 külön, source-native OPUS TITÁSZ contractot vezet be. Az OPUS publication
nem tartalmaz külön voltage, N-1 transformer-capacity vagy winter-evening-peak
mezőt, ezért ezek nem kerülnek a parserbe és nem vezethetők le az állomásnévből.

A source snapshot audit alapján a station code nem fix hosszúságú: 4 és 5
karakteres kódok egyaránt szerepelnek, a `DEBR` kód pedig kétszer jelenik meg.
Az exact source-row identity ezért a változatlan `(station_code, station_name)`
pár. Az OPUS region ID `OPUS_TITASZ:<station_code>:<station_name>` és nem
azonosítható az MVM Démász voltage-grain kulcsával.

Az OPUS normalized record soha nem `OBS`: teljes, külön synthetic clearance
esetén `DER`, egyébként `Q`. A parser nem ad assessment handoffot; az MVM
`assess_incremental_demand()` explicit módon elutasítja az OPUS rekordot, így
nem jön létre cross-DSO vagy B08/B09 control-area → alállomás mapping.

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

## B10-P3 — baseline infrastructure authority

The canonical contract is implemented in
[`baseline_infrastructure_contract.py`](baseline_infrastructure_contract.py).
Every project is evaluated against two explicit worlds: `WITHOUT_PROGRAM` and
`WITH_PROGRAM`. `OPERATING`, `UNDER_CONSTRUCTION`, `CONTRACTED` and
`BUDGETED_OR_ALLOCATED` are baseline candidates only when project identity,
effective date and authoritative evidence are complete. `OPEN_TENDER` and
`ANNOUNCED_UNFUNDED` are not baseline by announcement alone.

Authority level alone is insufficient: every baseline candidate must have a
referenced, high-authority evidence item explicitly supporting its status
claim (`OPERATING`, `UNDER_CONSTRUCTION`, `CONTRACTED` or
`FUNDED_OR_ALLOCATED`). Announcement, tender, plan, funding, construction and
operation remain separate claims; only evidence named by `source_refs` may
satisfy a gate, and record truth cannot outrank that referenced evidence.

Only a separately evidenced incremental scope, capacity, acceleration, upsizing
or cost component can be attributed to the programme. Temporal coincidence is
not causality, and program causality can never be `OBS`. Numeric CAPEX is
source-supported only; missing is not zero. `validate_attribution_ledger()`
rejects duplicate project/component identities and baseline/incremental
double-counting.

The B10-P3 official-source audit covers MEKH, MAVIR, MVM and OPUS publication
areas. None of those public landing pages, by themselves, supplies a complete
project-level contract/funding ledger for this programme. Therefore
`baseline_infrastructure.csv` and `incremental_capex_attribution.csv` remain
header-only, Q-B10-001 remains `OPEN / PARTIALLY_BOUNDED`, and B10 readiness
remains 15.

## B10-P4 — observed baseline RRF projects

B10-P4 applies the P3 classifier to exactly two completed, official RRF
projects: MVM Démász `RRF-6.1.1-21-2022-00006` and OPUS TITÁSZ
`RRF-6.1.1-21-2022-00001`. Their realised scope is `WITHOUT_PROGRAM` baseline
with `OPERATING` evidence effective 2026-06-15. The rows use the umbrella
`DSO_SERVICE_AREA` project grain and are deliberately excluded from the
`DSO_SUBSTATION` consumption-headroom assessment path.

The MVM grant and 50% rate do not mint an OBS total project cost; its cost field
stays blank. OPUS's directly stated 41,489,280,000 HUF total is source-supported.
Neither row receives a numeric programme-incremental cost. Renewable-generation
integration figures remain separate source semantics, not consumption headroom,
MGT permission, B08 load capacity or national headroom. Q-B10-001 remains
`OPEN / PARTIALLY_BOUNDED`, Q-B10-002 remains `OPEN`, and readiness remains 15.

Explicit exclusions: national DSO coverage, county↔DSO crosswalk,
ENTSO-E→substation mapping, national headroom/CAPEX, power-flow, reinforcement
optimisation, household allocation, connection approval, MGT replacement and
Q-B10-002 closure.
