# B10-P20 — DSO / KSH service-area crosswalk tranche

Audit date: 2026-09-03
Canonical base: `d0db78f8616a0fab835e6a0596091620039795c4`

## Decision

P20 applies the public-data rule introduced by P19:

`PUBLIC FACT USE != SOURCE-DOCUMENT REPUBLICATION != BULK DATABASE RECONSTRUCTION`

and preserves the P15 spatial authority boundary:

`SETTLEMENT NAME != KSH SETTLEMENT ID != WHOLE-SETTLEMENT DSO MEMBERSHIP != PARTIAL-SETTLEMENT USAGE-LOCATION MEMBERSHIP != EXACT DSO NODE`

P20 materializes an initial attributed tranche only where two independent facts are proven:

1. the official **5 jegyű** KSH `településazonosító törzsszám` and settlement name;
2. official DSO whole-settlement service-area membership.

The national canonical crosswalk remains header-only because a bounded tranche is not a complete national mapping.

## KSH administrative identity authority

Official KSH gazetteer:

`https://www.ksh.hu/docs/hun/hnk/hnk_2019.pdf`

Section IV explicitly publishes the five-digit `településazonosító törzsszám` by settlement name. Examples used by P20 include:

- `17686` — Ágasegyháza;
- `21944` — Akasztó;
- `10719` — Bácsalmás;
- `12441` — Abádszalók;
- `27872` — Abony;
- `08776` — Ajak.

Current KSH TSZJ methodology:

`https://ksh.hu/docs/osztalyozasok/teruleti_szamjel/tsz_modszertan.pdf`

The method defines the settlement identifier as five digits: four identity digits plus a fifth CDV digit. It also states that the identifier remains unchanged from establishment until dissolution and is never reassigned after dissolution. Therefore the official 2019 five-digit identifier remains authoritative for these continuing settlements.

P20 explicitly rejects the earlier draft use of the four-digit OSAP helper code as the canonical P15 KSH identifier:

`4-DIGIT OSAP SETTLEMENT CODE != 5-DIGIT KSH TELEPÜLÉSAZONOSÍTÓ TÖRZSSZÁM`

## MVM Démász authority

Current official service-area page:

`https://mvmhalozat.hu/aram/oldalak/6454`

The page publishes whole-settlement service-area lists by county and separately identifies settlements where only part of the administrative settlement belongs to MVM Démász.

P20 materializes 10 directly bounded whole-settlement rows from this authority. None of the separately identified partial settlements is promoted to whole-settlement membership.

The partial-settlement set remains outside the tranche and requires usage-location authority:

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

The current package is effective from 2026-06-03. The M1 territorial attachment is:

`https://www.opustitasz.hu/storage/documents/tarsasagunk/szabalyzatok/uzletszabalyzat/hatalyban-levo/OPUS%20TITASZ_%C3%9Czletszab%C3%A1lyzat%20mell%C3%A9klet.pdf`

M1 explicitly enumerates territorial-jurisdiction settlements. P20 materializes 10 directly bounded whole-settlement rows from that list and binds them to official five-digit KSH identifiers.

## Registry architecture

P20 adds:

- `registry/dso_service_area_membership_crosswalk_tranche.csv`
- `registry/dso_service_area_crosswalk_authorities.csv`

The tranche contains exactly **20** observed rows:

- 10 MVM Démász;
- 10 OPUS TITÁSZ.

Every row requires:

- exact five-digit KSH settlement identifier;
- exact settlement name;
- exact DSO operator and `DSO_SERVICE_AREA` identity;
- `WHOLE_SETTLEMENT` scope;
- source lineage to both KSH and DSO authority;
- `OBS` evidence status;
- `WHOLE_SETTLEMENT_MEMBERSHIP_PROVEN` status.

`registry/dso_service_area_membership_crosswalk.csv` remains header-only by design. The tranche is evidence that the bridge can be populated correctly, not evidence of six-DSO national completeness.

## Remaining Q

P20 does not prove:

- complete national six-DSO settlement crosswalk;
- ELMŰ current 2026 M1 normalization;
- E.ON DDÁSZ current 2026 M1 normalization;
- E.ON ÉDÁSZ current 2026 M1 normalization;
- MVM Émász M1 normalization;
- usage-location resolution for partial settlements;
- exact supplying substation or feeder;
- headroom, hosting capacity or connection permission;
- limiting-node status;
- reinforcement requirement or programme CAPEX.

Therefore `Q-B01-002`, `NO_COMPLETE_KSH_DSO_MEMBERSHIP_CROSSWALK` and `PARTIAL_SETTLEMENT_USAGE_LOCATION_RESOLUTION_REQUIRED` remain open blockers.

## Readiness effect

B10 remains `IN_PROGRESS` at readiness **15**. P20 turns a real subset of the administrative-to-DSO bridge into observed attributed facts but does not satisfy the national regional-penetration/hosting acceptance gate.
