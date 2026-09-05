# B02-P9 — Archetype admission gate

Állapot: **FAIL-CLOSED CONTRACTED / CURRENT STOCK ARCHETYPE Q**

Kapcsolódó kérdések: `Q-B02-001`, `Q-B02-002`, `Q-B02-004`

## Cél

B02-P9 különválasztja a szerződött dimenziós sémát, a populated current-stock archetype-ot és a technical-readiness archetype-ot.

`CONTRACTED DIMENSION SCHEMA != POPULATED CURRENT-STOCK ARCHETYPE != TECHNICAL READINESS ARCHETYPE`

## Current evidence state

### 1. WBL011 stock joint

P14 a pinned `WBL011/V67` teljes source-native stock-jointját QUALIFIED-ra emelte. P15 ugyanazt a grain-t a canonical extractorban repository-artifactként materializálta: **116 452** direct observation sor, exact **4 008 541** lakott lakás.

`SOURCE-NATIVE COMPLETE WBL011 JOINT != REPOSITORY-MATERIALIZED COMPLETE WBL011 JOINT != CURRENT-STOCK ARCHETYPE`

A materializációs oldal most teljesült. A külön `WBL011_ENVELOPE` és `WBL011_HEATING_FUEL` margók synthetic cross-joinja továbbra is tiltott; a direct `WBL011_FULL_STOCK_JOINT` projection használandó.

### 2. Building-type assignment

A `FAMILY_HOUSE` / `MULTI_DWELLING` taxonomy szerződött, de a 2022 WBL állományra alkalmazott kapcsolat továbbra is a 2015-ös településtípusos `ASS` proxy.

`CONTRACTED BUILDING-TYPE TAXONOMY != CURRENT BUILDING-TYPE STOCK ASSIGNMENT`

P16 kimutatta, hogy a KSH 2025 experimental-statistics módszertana current 2022 census analytical surface-en ténylegesen külön kezeli a családi házakat és társasházi lakásokat, és a census adatbázisban lakottsági információ is rendelkezésre áll. Ez azonban nem publikált occupied-stock building-type joint és nem ad repo-szinten reprodukálható WBL join kulcsot.

`CURRENT CLASSIFICATION EXISTS != PUBLIC OCCUPIED-STOCK DISTRIBUTION != DIRECT WBL LINK AUTHORITY`

P16 ezen felül hardeninget vezet be: közvetlen `OBS`/`DER` building-type link csak `WBL_FULL_JOINT` vagy determinisztikusan kapcsolható `DWELLING_RECORD` grainből fogadható el. `SETTLEMENT_TYPE` vagy `COUNTY_X_SETTLEMENT_TYPE` building-type margó nem direct link; ilyen kontroll csak a P12 calibrated-linkage út inputja lehet.

P17 a P16 direct-authority gate eredményét explicit módon beköti a P9 admissionbe: nyers `OBS` vagy `DER` building-type státusz többé nem elég, külön `building_type_direct_authority_status = QUALIFIED` szükséges.

### 3. Primary-energy linkage

A KSH 2025 energetikai panel building type × construction period × primary-energy bin grainen `MODELLED`, és nincs explicit WBL-link authority.

`MODELLED ENERGY PANEL != PRIMARY-ENERGY-TO-WBL LINK AUTHORITY`

P17 pontosítja a legerősebb current evidence-et. A KSH módszertan szerint a final random-forest modell a teljes 2022 census housing stockra futott, és több WBL-kompatibilis lakásjellemzőt használ. Ez hivatalos, erős model evidence, de a public anyag nem ad ki reprodukálható dwelling-level predikciókat, fitted RF artifactot vagy WBL-compatible record keyt.

`PRIMARY-ENERGY MODEL EXISTS != REPRODUCIBLE WBL LINK AUTHORITY`

`PUBLIC AGGREGATE MODEL OUTPUT != RECORD-LEVEL WBL BINDING`

A 279 020 internálisan census rekordhoz kapcsolt energiatanúsítvány `OBS` sample evidence, nem complete occupied-stock assignment. A full-stock random-forest output `MODELLED`, nem direct `OBS`/`DER` WBL joint.

P17 ezért két authority utat tart külön:

1. direct primary-energy link: csak külön direct gate `QUALIFIED` eredménnyel;
2. modelled primary-energy link: csak P12 `QUALIFIED` calibrated-model admissionnel.

`RAW OBS/DER LINK TOKEN != DIRECT-LINK ADMISSION`

A KSH random forest P17 után explicit P12 candidate (`KSH-RF-2022-PRIMARY-ENERGY`), de `NOT_APPROVED / Q`.

## Executable admission contract

A current-stock archetype `QUALIFIED` csak akkor lehet, ha egyszerre:

1. schema = `CONTRACTED`;
2. WBL joint repositoryban determinisztikusan materializált és complete;
3. current building-type link = separately admitted direct `OBS`/`DER` authority vagy külön admitted calibrated model;
4. primary-energy link = separately admitted direct `OBS`/`DER` WBL authority vagy külön admitted calibrated model.

A direct building-type authority P16 után csak akkor tekinthető valódi linknek, ha a building type ugyanazon WBL stock jointban van jelen, vagy dwelling-record szinten determinisztikusan kapcsolható. Coarse building-type marginból tilos implicit subcell allocationt készíteni.

A direct primary-energy authority P17 után ugyanezt a fail-closed logikát követi: occupied-stock WBL full joint vagy reprodukálható dwelling-record binding kell. Egy aggregate/modelled energy panel nem direct authority.

P17 után a canonical current state:

- schema: `CONTRACTED`;
- WBL011 source-native full joint: `QUALIFIED`;
- WBL011 repository full-joint materialization: `MATERIALIZED`;
- current KSH building-type classification existence: `OBS` methodological fact;
- public occupied-WBL building-type direct link: `Q`;
- building type used by current archetype: `ASS`;
- official KSH full-stock primary-energy model existence: documented;
- public reproducible primary-energy-to-WBL direct link: `Q`;
- KSH primary-energy model P12 candidate: `NOT_APPROVED / Q`;
- primary energy used by current archetype: `MODELLED_UNLINKED`.

Kimenet: `Q`.

A current blockers:

- `NO_CURRENT_BUILDING_TYPE_LINK_AUTHORITY`;
- `NO_PRIMARY_ENERGY_TO_WBL_LINK_AUTHORITY`.

A technical-readiness archetype ezek mellett current heat-emitter és design-temperature `OBS`/`DER` evidence-et is igényel. Mindkettő jelenleg `Q`.

## Machine-readable state

- `registry/b02_archetype_admission_gate.csv`;
- `registry/b02_current_building_type_authority_audit.csv` — P8/P16 current building-type authority audit;
- `registry/b02_primary_energy_authority_audit.csv` — P17 direct/model candidate audit;
- `registry/b02_calibrated_linkage_admission.csv` — P12/P17 calibrated-model admission state;
- `registry/b02_wbl011_source_native_full_joint.csv` — P14 retrieval evidence;
- `registry/b02_wbl011_full_joint_materialization.csv` — P15 repository materialization evidence.

## Q-impact

- `Q-B02-002` OPEN: a WBL materialization lezárt, current KSH classification/model existence bizonyított, de public occupied-WBL building-type direct link és reproducible/admitted primary-energy linkage nincs.
- `Q-B02-001` OPEN: current technical-readiness archetype és national technical eligible count nincs.
- `Q-B02-004` OPEN: current heat-emitter és design-temperature evidence nincs.

## Tiltott következtetések

- `CONTRACTED` schema nem evidence promotion.
- Direct WBL011 full joint nem building-type vagy primary-energy authority.
- `ASS` building-type proxy nem current stock authority.
- Coarse building-type margin nem direct WBL subcell link.
- KSH internal/current classification existence nem publikált occupied-stock assignment.
- `MODELLED` primary-energy panel vagy full-stock prediction nem direct WBL assignment authority.
- 279 020 linked certificate nem complete occupied-stock primary-energy joint.
- Raw `OBS`/`DER` token nem helyettesíti a direct-link gate-et.
- Model-status token nem helyettesíti P12 approval/admissiont.
- Heating mode/fuel nem imputál heat emittert vagy design temperature-t.
- Missing/Q nem nulla.

## Readiness

B02 readiness változatlanul **55%**. P17 a primary-energy authority frontot és a P9 token-admissiont hardeníti, de current-stock archetype-ot vagy technical/final eligible countot még nem engedélyez.
