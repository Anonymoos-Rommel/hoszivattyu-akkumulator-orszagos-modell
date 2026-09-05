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

### 1. WBL joint incompleteness

P1-H három külön source-native KSH projekciót materializált:

- `WBL011_ENVELOPE`;
- `WBL011_HEATING_FUEL`;
- `WBL017_HEAT_PUMP_BASELINE`.

A két WBL011 projekció ugyanazon 4 008 541 lakott lakásos univerzumra egyezik vissza, de külön API-projekciók. Ezért:

`MATCHING MARGINAL TOTALS != CELL-LEVEL JOINT AUTHORITY`

A külön envelope és heating/fuel cellák összekapcsolása továbbra is tiltott.

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
2. létezik complete WBL joint a szükséges stock dimenziókra;
3. a building-type kapcsolat `OBS`, `DER` vagy külön jóváhagyott kalibrált modell;
4. a primary-energy kapcsolat explicit WBL-link authorityt hordoz.

A jelenlegi canonical state:

- schema: `CONTRACTED`;
- WBL joint: incomplete;
- building type: `ASS`;
- primary energy: `MODELLED_UNLINKED`.

Kimenet: `Q`.

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

## Q-impact

- `Q-B02-002` **nem zárható** pusztán azért, mert a dimenzió- és kategóriaséma szerződött. A nyitott rész a current stock assignment authority és a WBL-kompatibilis building-type kapcsolat.
- `Q-B02-001` nyitott, mert nincs current technical-readiness archetype és nincs országos technical eligible count.
- `Q-B02-004` nyitott, mert current heat-emitter és design-temperature evidence továbbra sincs.

## Tiltott következtetések

- `CONTRACTED` schema nem evidence promotion.
- Külön WBL projekciók nem cross-joinolhatók azért, mert az aggregált összegük egyezik.
- `ASS` building-type proxy nem current stock authority.
- `MODELLED` primary-energy panel nem WBL assignment authority.
- Heating mode vagy heating fuel nem imputálhat heat emittert vagy design temperature-t.
- Missing/Q nem nulla.

## Readiness

B02 readiness változatlanul **55%**. P9 sem eligible-stock számot, sem új megfigyelt jointot nem hoz létre; kizárólag a claim-admission határt teszi végrehajthatóvá.
