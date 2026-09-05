# B02-P9 — Archetype admission gate

Állapot: **FAIL-CLOSED CONTRACTED / CURRENT STOCK ARCHETYPE Q**

Kapcsolódó kérdések: `Q-B02-001`, `Q-B02-002`, `Q-B02-004`

## Cél

B02-P9 különválasztja a már szerződött archetípus-dimenziókat attól az állítástól, hogy a 2022-es magyar lakott lakásállomány teljes közös archetípus-jointja ténylegesen materializálható.

Kanonikus határ:

`CONTRACTED DIMENSION SCHEMA != POPULATED CURRENT-STOCK ARCHETYPE != TECHNICAL READINESS ARCHETYPE`

A schema repository-architektúra. Nem evidence-status, nem lakásszám, és nem jogosít fel külön margók összekapcsolására.

## Current evidence state

A jelenlegi B02 evidence surface három külön problémát tart nyitva.

### 1. WBL source-native joint bizonyított, repository materialization hiányzik

P1-H három külön source-native KSH projekciót materializált:

- `WBL011_ENVELOPE`;
- `WBL011_HEATING_FUEL`;
- `WBL017_HEAT_PUMP_BASELINE`.

B02-P14 később közvetlenül lekérte a pinned `WBL011/V67` teljes stock-joint surface-t. Ugyanazon response grainen egyszerre szerepelt non-`TOTAL` értéken a terület, településtípus, építési időszak, falazat, alapterület, komfort, fűtési mód és tüzelőanyag. A 20 vármegye/Budapest válasz **116 452** rekordja exact **4 008 541** lakott lakásra egyezik vissza, és mind a 20 független county `TOTAL` kontrollhoz `delta = 0`.

Ezért a korábbi source-availability kérdés lezárt. Az új kanonikus határ:

`SOURCE-NATIVE COMPLETE WBL011 JOINT != REPOSITORY-MATERIALIZED COMPLETE WBL011 JOINT != CURRENT-STOCK ARCHETYPE`

A 116 452 full-joint observation sor azonban P14-ben nincs repository-artifactként materializálva. A P1-H külön envelope és heating/fuel projekcióinak cellaszintű összekapcsolása ezért továbbra is tiltott:

`SEPARATE MATERIALIZED PROJECTIONS != MATERIALIZED FULL JOINT`

### 2. Building-type assignment

A kanonikus `FAMILY_HOUSE` / `MULTI_DWELLING` kategóriapár szerződött. A 2022 WBL állományra alkalmazott building-type kapcsolat azonban továbbra is a 2015-ös településtípusos proxyból származó `ASS`.

B02-P6 történeti 2016 KSH kontrollt adott; B02-P8 current KSH source-family auditot adott. Egyik sem bizonyított 2022-es WBL-kompatibilis building-type joint authorityt.

Ezért:

`CONTRACTED BUILDING-TYPE TAXONOMY != CURRENT BUILDING-TYPE STOCK ASSIGNMENT`

### 3. Primary-energy linkage

A KSH 2025 energetikai panel building type × construction period × primary-energy bin grainen `MODELLED`. B02-P7 a 2011+ construction-period harmonizációt exact darabszám-összegzéssel elvégzi, de ettől az energetikai panel nem válik WBL-jointtá.

Ezért:

`MODELLED ENERGY PANEL != PRIMARY-ENERGY-TO-WBL LINK AUTHORITY`

## Executable admission contract

`modules/B02/archetype_admission_gate.py` két külön claimet kezel.

### Current stock archetype assignment

`QUALIFIED` csak akkor lehet, ha egyszerre:

1. a schema `CONTRACTED`;
2. a szükséges WBL joint repositoryban determinisztikusan materializált és complete;
3. a building-type kapcsolat `OBS`, `DER` vagy külön jóváhagyott kalibrált modell;
4. a primary-energy kapcsolat explicit WBL-link authorityt hordoz.

A jelenlegi canonical state:

- schema: `CONTRACTED`;
- WBL011 source-native full joint: `QUALIFIED` P14 evidence alapján;
- WBL011 full-joint repository materialization: **incomplete / not materialized**;
- building type: `ASS`;
- primary energy: `MODELLED_UNLINKED`.

Kimenet: `Q`.

A runtime input ezért `wbl_joint_materialized_complete`, nem pusztán source-availability flag. A current blocker:

`NO_MATERIALIZED_COMPLETE_WBL_JOINT`

### Technical readiness archetype

Ehhez a fenti current-stock archetype mellett külön current heat-emitter és design-temperature evidence is kell `OBS`/`DER` státuszban.

A jelenlegi canonical state mindkettőre `Q`, ezért technical-readiness archetype sem materializálható.

## Machine-readable state

A canonical audit:

`registry/b02_archetype_admission_gate.csv`

Három claimet tart külön:

1. `ARCHETYPE_DIMENSION_SCHEMA = CONTRACTED`;
2. `CURRENT_STOCK_ARCHETYPE_ASSIGNMENT = Q`;
3. `TECHNICAL_READINESS_ARCHETYPE = Q`.

A P14 source-native full-joint evidence külön gépi auditja:

`registry/b02_wbl011_source_native_full_joint.csv`

## Q-impact

- `Q-B02-002` **nem zárható** pusztán azért, mert a WBL011 source-native joint bizonyított. A nyitott rész a repository-materializált current stock assignment authority, a WBL-kompatibilis building-type kapcsolat és a primary-energy linkage.
- `Q-B02-001` nyitott, mert nincs current technical-readiness archetype és nincs országos technical eligible count.
- `Q-B02-004` nyitott, mert current heat-emitter és design-temperature evidence továbbra sincs.

## Tiltott következtetések

- `CONTRACTED` schema nem evidence promotion.
- Source-native full-joint availability nem azonos a repositoryban materializált full-joint artifacttal.
- A külön P1-H WBL projekciók nem cross-joinolhatók azért, mert az aggregált összegük egyezik.
- `ASS` building-type proxy nem current stock authority.
- `MODELLED` primary-energy panel nem WBL assignment authority.
- Heating mode vagy heating fuel nem imputálhat heat emittert vagy design temperature-t.
- Missing/Q nem nulla.

## Readiness

B02 readiness változatlanul **55%**. P14 valódi source-evidence blocker reductiont hoz, de sem current-stock archetype-ot, sem eligible-stock számot nem materializál. A current-stock és technical-readiness claim ezért továbbra is `Q`.
