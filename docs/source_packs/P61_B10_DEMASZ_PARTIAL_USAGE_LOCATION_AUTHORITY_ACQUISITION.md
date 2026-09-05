# B10-P61 — MVM Démász partial-settlement usage-location authority acquisition

Status date: 2026-09-05

Canonical base: `50179145dfa9e27aabd85bf50940557bea7a0e94`

## Purpose

P61 ends the P58-P60 hardening-only run and returns B10 to blocker-directed evidence acquisition.

The target is the exact 20-settlement partial population frozen by P45/P57 and the standing blocker:

`PARTIAL_SETTLEMENT_USAGE_LOCATION_RESOLUTION_REQUIRED`

P61 asks two operational questions:

1. what current counterpart DSO territorial evidence is already public for each of the 20 MVM Démász partial settlements; and
2. whether any case now has enough claim-specific authority to produce a real P15 `USAGE_LOCATION_MEMBERSHIP_PROVEN` record rather than another residual classification.

The answer to the second question is **yes for one named usage-location: `Tass üdülőterület` → ELMŰ**.

The global blocker is **not** cleared: the remaining partial-settlement population still lacks complete usage-location boundary authority.

## Current MVM Démász source precedence

P61 pins the current MEKH-approved business-rule package exposed by the MVM Démász 2026-05-26 landing and its M1 territorial-jurisdiction attachment:

- business-rule landing: `https://mvmhalozat.hu/aram/oldalak/125878`
- current M1: `https://mvmhalozat.hu/attachments/41985`
- P61 source id: `SRC-B10-MVM-DEMASZ-M1-2026`

The M1 explicitly separates the administrative settlements fully served by MVM Démász from the exact 20 settlements whose territory is served only **in part**.

The older public-service geography HTML at `https://mvmhalozat.hu/aram/oldalak/6454` remains a live official page, but on the P61 retrieval date it exposes only 15 partial labels. It therefore cannot be the canonical P61 source for the exact current 20-settlement partial population.

P61 freezes:

`CURRENT MEKH-APPROVED M1 PARTIAL POPULATION > LIVE HTML PARTIAL POPULATION WHEN THE HTML IS INCOMPLETE`

This is source precedence, not a claim that the HTML is generally invalid.

## Exact 20-settlement acquisition matrix

The matrix is stored in:

`registry/dso_service_area_membership_demasz_p61_counterpart_authority_matrix.csv`

Every P57 partial settlement appears exactly once.

P61's targeted current-M1 scan produces:

- **9** OPUS TITÁSZ administrative-unit overlaps:
  - Csabacsűd
  - Dévaványa
  - Gyomaendrőd
  - Kunszentmárton
  - Szeghalom
  - Tiszakécske
  - Tiszasas
  - Tiszaug
  - Zsadány
- **3** ELMŰ administrative-unit overlaps:
  - Dabas
  - Péteri
  - Újhartyán
- **1** DDÁSZ administrative-unit overlap:
  - Mohács
- **1** ELMŰ named territorial subset:
  - Tass → `Tass üdülőterület`
- **6** cases with no exact counterpart token found in the targeted ELMŰ / OPUS TITÁSZ / DDÁSZ current-M1 scan:
  - Baja
  - Csongrád
  - Érsekcsanád
  - Solt
  - Szentes
  - Tápiószőlős

The six no-hit rows are search outcomes only. They are **not** national negative membership claims.

## Administrative-unit overlap remains fail-closed

The 13 exact whole administrative-unit counterpart tokens are useful evidence that the current published territorial surfaces overlap at administrative-settlement name grain.

They do not identify the internal geographic line between the DSOs.

Therefore P61 does not promote any of those 13 cases to a usage-location membership.

`CURRENT CROSS-OPERATOR ADMINISTRATIVE-UNIT OVERLAP != EXACT USAGE-LOCATION BOUNDARY`

`TWO CURRENT DSO SOURCE TOKENS != DUAL WHOLE-SETTLEMENT MEMBERSHIP`

`ADMINISTRATIVE-UNIT PRESENCE != AUTHORITY TO SPLIT ADDRESSES, PARCELS OR FEEDERS`

## First exact named usage-location resolution: Tass üdülőterület

P57 correctly refused to infer a boundary from the current ELMŰ M1 token alone.

P61 adds an independent authority edge that P57 did not use: the official ELMŰ distribution operating licence, MEH decision 805/2006, annex 2. In the Dél-pesti regional territorial-jurisdiction list it names **`Tass üdülőterület`** as an ELMŰ jurisdiction unit.

The current ELMŰ M1 still contains the exact same named territorial unit: **`Tass üdülőterület`**.

Together these authorities establish:

- historical regulatory semantics: the exact label denotes an ELMŰ territorial-jurisdiction unit;
- current operator continuity: the exact named unit remains in the current ELMŰ M1;
- KSH administrative identity: `Tass = 20525`.

P61 therefore materializes exactly one usage-location row:

- settlement: `Tass`
- KSH settlement code: `20525`
- operator: `ELMU`
- service area: `ELMU:SERVICE_AREA`
- coverage scope: `PARTIAL_SETTLEMENT`
- usage-location id: `ELMU:TASS:UDULOTERULET`
- source-native label: `Tass üdülőterület`
- status: `USAGE_LOCATION_MEMBERSHIP_PROVEN`
- evidence status: `DER`

The machine-readable row is:

`registry/dso_service_area_membership_elmu_p61_usage_location.csv`

The P61 regression test also reconstructs the P15 `ServiceAreaMembershipRecord` and requires the runtime classifier to return `USAGE_LOCATION_MEMBERSHIP_PROVEN`.

## No complement inference

P61 explicitly does **not** infer what part of Tass remains MVM Démász.

`NAMED ELMŰ SUBSET != AUTHORITY TO INFER THE MVM DÉMÁSZ COMPLEMENT`

It does not infer:

- a polygon for the remainder of Tass;
- an address list for the remainder of Tass;
- parcel boundaries;
- feeder boundaries;
- a percentage split;
- whole-settlement ELMŰ membership;
- whole-settlement MVM Démász membership;
- an exact DSO node.

A programme entity can use the P61 result only after its upstream location identity is explicitly `ELMU:TASS:UDULOTERULET` or is independently resolved to that named usage-location.

`USAGE-LOCATION SERVICE-AREA MEMBERSHIP != EXACT DSO NODE`

## State impact

P61 adds:

- **1** real `USAGE_LOCATION_MEMBERSHIP_PROVEN` record;
- **0** whole-settlement membership rows;
- **0** inferred complement rows;
- **0** DSO-node assignments.

MVM Démász remains at **256** materialized whole-settlement memberships and the exact P45/P57 partial population remains **20** administrative settlements.

ELMŰ remains at **130** materialized whole-settlement identities; P61 adds a separate partial usage-location record, not a 131st whole-settlement identity.

The national canonical crosswalk remains header-only.

The standing global blockers remain active, including:

- `NO_COMPLETE_KSH_DSO_MEMBERSHIP_CROSSWALK`
- `PARTIAL_SETTLEMENT_USAGE_LOCATION_RESOLUTION_REQUIRED`
- `REGIONAL_READINESS_HEADER_ONLY`

This is intentional: **one resolved usage-location is real progress, but it is not national completion**.

B10 remains `IN_PROGRESS`; readiness remains **15%** until a later closure assessment has evidence to move an acceptance gate.

## Core frozen boundaries

`CURRENT M1 AUTHORITY != STALE/INCOMPLETE HTML ENUMERATION`

`CURRENT CROSS-OPERATOR ADMINISTRATIVE-UNIT OVERLAP != EXACT USAGE-LOCATION BOUNDARY`

`HISTORICAL REGULATORY TERRITORIAL SEMANTICS + CURRENT EXACT NAMED TERRITORIAL UNIT = BOUNDED CURRENT NAMED USAGE-LOCATION MEMBERSHIP`

`NAMED ELMŰ SUBSET != AUTHORITY TO INFER THE MVM DÉMÁSZ COMPLEMENT`

`USAGE-LOCATION SERVICE-AREA MEMBERSHIP != EXACT DSO NODE`
