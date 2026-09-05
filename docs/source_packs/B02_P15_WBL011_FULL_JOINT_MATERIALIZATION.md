# B02-P15 — WBL011 complete stock-joint repository materialization

Állapot: **REPOSITORY MATERIALIZED / CURRENT STOCK ARCHETYPE Q**

Dátum: **2026-09-05**

Kapcsolódó kérdések: `Q-B02-001`, `Q-B02-002`, `Q-B02-004`

## Cél

P14 bizonyította, hogy a pinned `WBL011/V67` teljes stock-jointja source-native formában elérhető. P15 ugyanazt a jointot a meglévő canonical `tools/extract_b02_ksh_wbl_joint_cells.py` útvonalon determinisztikusan materializálja a repositoryba.

Kanonikus határ:

`SOURCE-NATIVE COMPLETE WBL011 JOINT -> REPOSITORY-MATERIALIZED COMPLETE WBL011 JOINT`

de továbbra is:

`REPOSITORY-MATERIALIZED COMPLETE WBL011 JOINT != POPULATED CURRENT-STOCK ARCHETYPE != TECHNICAL READINESS ARCHETYPE`

## Exact materialization

- source flow: `WBL011/V67`;
- projection: `WBL011_FULL_STOCK_JOINT`;
- county/Budapest queries: **20**;
- materializált full-joint sor: **116 452**;
- lakásszám: **4 008 541**;
- teljes combined WBL artifact: **164 412** sor;
- combined output SHA-256: `f4df16e4f53947e33a2d4477d9806faee903b999d26143b3bdc92d747d3c800f`;
- full-projection semantic SHA-256: `ffe8e08cd6555eb1d2dbf001b640d8ece614f1b818d09b82499d129bdf8f4876`.

Csak ténylegesen visszaadott API-observation kerül a fájlba. Nem visszaadott kombináció nem lesz nullává alakítva.

## P14 -> P15 lineage audit

A P14 acquisition ledger és a P15 újralekérdezés összevetése:

- county rekordszám egyezés: **20/20**;
- response byte-hossz egyezés: **20/20**;
- raw SHA-256 egyezés: **3/20**;
- raw SHA-256 eltérés: **17/20**.

Ezért kanonikus:

`RAW RESPONSE SHA-256 = RETRIEVAL-INSTANCE LINEAGE != IMMUTABLE DATASET FINGERPRINT`

A raw hash eltérés önmagában nem jelent observation-driftet, ha a source query, rekordszám, byte-hossz és materializált semantic controls változatlanok. A repository artifact rendezett, normalizált sorokból készül és saját output hash-t kap.

## Admission impact

P15 lezárja a jelenlegi P9 sub-blockert:

`NO_MATERIALIZED_COMPLETE_WBL_JOINT` -> **CLOSED**

A `CURRENT_STOCK_ARCHETYPE_ASSIGNMENT` azonban továbbra is `Q`, mert hiányzik:

- `NO_CURRENT_BUILDING_TYPE_LINK_AUTHORITY`;
- `NO_PRIMARY_ENERGY_TO_WBL_LINK_AUTHORITY`.

A `TECHNICAL_READINESS_ARCHETYPE` ezen felül továbbra is blokkolt:

- `NO_CURRENT_HEAT_EMITTER_EVIDENCE`;
- `NO_CURRENT_DESIGN_TEMPERATURE_EVIDENCE`.

## Tiltott következtetések

- A direct WBL011 full joint nem ad building-type authorityt.
- A KSH MODELLED primary-energy panel nem válik WBL-jointtá.
- Heating mode/fuel nem imputál heat-emittert vagy design temperature-t.
- A külön envelope és heating/fuel projekciókat nem kell és nem szabad synthetic módon cross-joinolni; a direct full-joint projection használandó.
- Missing/Q nem nulla.

## Q-impact és readiness

- `Q-B02-001`: **OPEN**;
- `Q-B02-002`: **OPEN**, de a WBL011 repository-materialization sub-blocker lezárt;
- `Q-B02-004`: **OPEN**;
- national technical/final eligible count: **blank / Q**;
- B02 readiness: **55%**;
- **no readiness uplift**;
- OÉNY request: **nem lett elküldve**.
