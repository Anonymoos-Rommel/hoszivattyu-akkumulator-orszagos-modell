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

### 3. Primary-energy linkage

A KSH 2025 energetikai panel building type × construction period × primary-energy bin grainen `MODELLED`, és nincs explicit WBL-link authority.

`MODELLED ENERGY PANEL != PRIMARY-ENERGY-TO-WBL LINK AUTHORITY`

## Executable admission contract

A current-stock archetype `QUALIFIED` csak akkor lehet, ha egyszerre:

1. schema = `CONTRACTED`;
2. WBL joint repositoryban determinisztikusan materializált és complete;
3. current building-type link = `OBS`, `DER` vagy külön admitted calibrated model;
4. primary-energy link explicit WBL authorityt hordoz.

P15 után a canonical current state:

- schema: `CONTRACTED`;
- WBL011 source-native full joint: `QUALIFIED`;
- WBL011 repository full-joint materialization: `MATERIALIZED`;
- building type: `ASS`;
- primary energy: `MODELLED_UNLINKED`.

Kimenet: `Q`.

A current blockers:

- `NO_CURRENT_BUILDING_TYPE_LINK_AUTHORITY`;
- `NO_PRIMARY_ENERGY_TO_WBL_LINK_AUTHORITY`.

A technical-readiness archetype ezek mellett current heat-emitter és design-temperature `OBS`/`DER` evidence-et is igényel. Mindkettő jelenleg `Q`.

## Machine-readable state

- `registry/b02_archetype_admission_gate.csv`;
- `registry/b02_wbl011_source_native_full_joint.csv` — P14 retrieval evidence;
- `registry/b02_wbl011_full_joint_materialization.csv` — P15 repository materialization evidence.

## Q-impact

- `Q-B02-002` OPEN: a materialization sub-blocker lezárt, de current building-type authority és primary-energy linkage nincs.
- `Q-B02-001` OPEN: current technical-readiness archetype és national technical eligible count nincs.
- `Q-B02-004` OPEN: current heat-emitter és design-temperature evidence nincs.

## Tiltott következtetések

- `CONTRACTED` schema nem evidence promotion.
- Direct WBL011 full joint nem building-type vagy primary-energy authority.
- `ASS` building-type proxy nem current stock authority.
- `MODELLED` primary-energy panel nem WBL assignment authority.
- Heating mode/fuel nem imputál heat emittert vagy design temperature-t.
- Missing/Q nem nulla.

## Readiness

B02 readiness változatlanul **55%**. P15 valódi blocker reductiont és repository materializationt hoz, de current-stock archetype-ot vagy technical/final eligible countot még nem engedélyez.
