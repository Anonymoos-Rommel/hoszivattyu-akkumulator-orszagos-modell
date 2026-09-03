# B10-P20 — DSO / KSH service-area crosswalk tranche

Audit date: 2026-09-03
Canonical base: `d0db78f8616a0fab835e6a0596091620039795c4`

## Decision

P20 applies the corrected public-data rule introduced by P19:

`PUBLIC FACT USE != SOURCE-DOCUMENT REPUBLICATION != BULK DATABASE RECONSTRUCTION`

and preserves the spatial authority boundary from P15:

`SETTLEMENT NAME != KSH SETTLEMENT ID != WHOLE-SETTLEMENT DSO MEMBERSHIP != PARTIAL-SETTLEMENT USAGE-LOCATION MEMBERSHIP != EXACT DSO NODE`

P20 therefore materializes attributed administrative-to-DSO membership facts only where two independent authorities are available:

1. an official KSH settlement code/name pair; and
2. an official DSO whole-settlement service-area statement.

## KSH administrative authority

Official KSH source:

`https://www.ksh.hu/docs/hun/info/02osap/2024/segedlet/s241405.pdf`

The published list binds settlement names to official KSH settlement identifiers. P20 uses this only for administrative identity normalization. The KSH code does not prove DSO membership.

## MVM Démász authority

Official current service-area page:

`https://mvmhalozat.hu/aram/oldalak/6454`

The page publishes whole-settlement service-area lists by county and separately enumerates settlements where only part of the administrative settlement belongs to the MVM Démász area.

P20 materializes a first KSH-normalized whole-settlement tranche from the explicit whole-settlement lists. None of the separately listed partial settlements is promoted to `WHOLE_SETTLEMENT_MEMBERSHIP_PROVEN`.

The following partial settlements remain outside the tranche and require usage-location authority before a concrete programme entity can be assigned automatically:

- Baja
- Csongrád
- Érsekcsanád
- Gyomaendrőd
- Kunszentmárton
- Mohács
- Solt
- Szeghalom
- Szentes
- Tápiószőlős
- Tass
- Tiszakécske
- Tiszasas
- Tiszaug
- Újhartyán
- Zsadány

## OPUS TITÁSZ authority

Current business-rule landing:

`https://www.opustitasz.hu/tarsasagunk/szabalyzatok/uzletszabalyzat`

The page identifies the business-rule package effective from 2026-06-03. The current M1 territorial attachment is:

`https://www.opustitasz.hu/storage/documents/tarsasagunk/szabalyzatok/uzletszabalyzat/hatalyban-levo/OPUS%20TITASZ_%C3%9Czletszab%C3%A1lyzat%20mell%C3%A9klet.pdf`

M1 explicitly enumerates OPUS TITÁSZ territorial-jurisdiction settlements. P20 materializes an initial KSH-normalized tranche from these published whole-settlement facts.

## Registry architecture

P20 adds:

- `registry/dso_service_area_membership_crosswalk_tranche.csv`
- `registry/dso_service_area_crosswalk_authorities.csv`

The tranche contains only rows satisfying:

- exact official KSH settlement identifier;
- exact official settlement name;
- exact DSO operator/service-area identity;
- `WHOLE_SETTLEMENT` scope;
- source lineage to both administrative and DSO authorities;
- `OBS` evidence status;
- `WHOLE_SETTLEMENT_MEMBERSHIP_PROVEN` status.

The national canonical registry:

`registry/dso_service_area_membership_crosswalk.csv`

remains header-only by design. A bounded two-operator tranche is not promoted to a complete six-DSO national crosswalk.

## What P20 does not claim

P20 does not prove:

- a complete national six-DSO settlement crosswalk;
- ELMŰ current 2026 M1 normalization;
- E.ON DDÁSZ current 2026 M1 normalization;
- E.ON ÉDÁSZ current 2026 M1 normalization;
- MVM Émász M1 normalization;
- usage-location resolution for partial settlements;
- exact supplying substation or feeder;
- headroom, connection permission or hosting capacity;
- limiting-node status;
- reinforcement requirement or programme CAPEX.

`Q-B01-002`, `NO_COMPLETE_KSH_DSO_MEMBERSHIP_CROSSWALK` and `PARTIAL_SETTLEMENT_USAGE_LOCATION_RESOLUTION_REQUIRED` therefore remain open blockers.

## Readiness effect

B10 remains `IN_PROGRESS` at readiness **15**. P20 converts a real subset of the spatial bridge from Q to observed attributed facts, but does not yet satisfy the national regional-penetration/hosting acceptance gate.
