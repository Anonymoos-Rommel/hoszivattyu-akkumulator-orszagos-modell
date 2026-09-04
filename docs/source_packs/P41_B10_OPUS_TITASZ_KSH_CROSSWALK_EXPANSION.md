# B10-P41 — OPUS TITÁSZ / KSH service-area crosswalk expansion II

## Scope

B10-P41 is an evidence/data slice. It introduces no new semantic gate.

It preserves the historical OPUS TITÁSZ rows materialized by P20 (M1 serials 1–10) and P40 (M1 serials 11–50), and adds exactly the next 40 current official M1 whole-settlement rows, serials **51–90**.

The bounded OPUS TITÁSZ materialization therefore becomes:

- P20: 10 OBS rows, M1 serials 1–10;
- P40: +40 OBS rows, M1 serials 11–50;
- P41: +40 OBS rows, M1 serials 51–90;
- current bounded total: **90 materialized rows**.

P41 deliberately stops at serial **90, Géberjén**. M1 serial **91, Gégény**, is not materialized by this slice.

## Authorities

### OPUS TITÁSZ

- operator: `OPUS_TITASZ`
- source id: `SRC-B10-OPUS-TITASZ-M1-2026`
- source kind: `OFFICIAL_CURRENT_M1_ATTACHMENT`
- currentness: `CURRENT_2026`
- membership semantics: `M1_SETTLEMENT_LIST`
- official source: `https://www.opustitasz.hu/storage/documents/tarsasagunk/szabalyzatok/uzletszabalyzat/hatalyban-levo/OPUS%20TITASZ_%C3%9Czletszab%C3%A1lyzat%20mell%C3%A9klet.pdf`

The current M1 directly lists the settlement names in the service area. P41 uses only the bounded serial 51–90 range.

### KSH settlement identity

- source id: `SRC-B10-KSH-HNK-2019-SETTLEMENT-IDS`
- official source: `https://www.ksh.hu/docs/hun/hnk/hnk_2019.pdf`

Each P41 row binds the exact OPUS M1 settlement name to the directly published official five-digit KSH settlement identifier. No fuzzy matching, accent normalization, similar-name inference, or identity override is used in P41.

## Core boundaries

- `SETTLEMENT NAME != KSH SETTLEMENT ID`
- `KSH SETTLEMENT ID != DSO SERVICE-AREA MEMBERSHIP`
- `WHOLE SETTLEMENT != PARTIAL SETTLEMENT OR USAGE-LOCATION MEMBERSHIP`
- `DSO SERVICE-AREA MEMBERSHIP != EXACT DSO NODE`
- `BOUNDED CURRENT M1 ROWS != COMPLETE OPERATOR CROSSWALK`
- `PUBLIC FACT USE != SOURCE-DOCUMENT REPUBLICATION != BULK DATABASE RECONSTRUCTION`

The new rows have:

- `coverage_scope = WHOLE_SETTLEMENT`
- `usage_location_requirement = NONE`
- `evidence_status = OBS`
- `status = WHOLE_SETTLEMENT_MEMBERSHIP_PROVEN`

`OBS` is supported here because both the current OPUS M1 membership fact and the official KSH identifier are directly published and bound at the exact settlement identity used by the row.

## Exact P41 tranche

| M1 serial | KSH code | Settlement |
|---:|:---:|---|
| 51 | 30641 | Csenger |
| 52 | 24095 | Csengersima |
| 53 | 26851 | Csengerújfalu |
| 54 | 05795 | Cserkeszőlő |
| 55 | 13170 | Csépa |
| 56 | 12450 | Csökmő |
| 57 | 18795 | Darnó |
| 58 | 14678 | Darvas |
| 59 | 15130 | Debrecen |
| 60 | 17756 | Demecser |
| 61 | 05573 | Derecske |
| 62 | 24819 | Dévaványa |
| 63 | 14508 | Dombrád |
| 64 | 03647 | Döge |
| 65 | 14614 | Ebes |
| 66 | 09432 | Ecsegfalva |
| 67 | 15741 | Egyek |
| 68 | 32328 | Encsencs |
| 69 | 18528 | Eperjeske |
| 70 | 25469 | Esztár |
| 71 | 10852 | Érpatak |
| 72 | 23250 | Fábiánháza |
| 73 | 16647 | Fegyvernek |
| 74 | 18971 | Fehérgyarmat |
| 75 | 22415 | Fényeslitke |
| 76 | 34014 | Folyás |
| 77 | 03258 | Földes |
| 78 | 16993 | Furta |
| 79 | 10791 | Fülesd |
| 80 | 22150 | Fülöp |
| 81 | 14377 | Fülpösdaróc |
| 82 | 12256 | Füzesgyarmat |
| 83 | 13727 | Gacsály |
| 84 | 04996 | Garbolc |
| 85 | 18175 | Gáborján |
| 86 | 05801 | Gávavencsellő |
| 87 | 04613 | Gelénes |
| 88 | 13000 | Gemzse |
| 89 | 28893 | Geszteréd |
| 90 | 03629 | Géberjén |

## What P41 does not prove

The 90 bounded OPUS rows are not a complete OPUS TITÁSZ settlement inventory materialization and do not clear national crosswalk completeness.

Service-area membership does not establish:

- exact programme entity-to-node mapping;
- exact DSO substation identity;
- headroom sufficiency;
- limiting-node status;
- reinforcement need;
- reinforcement project cost;
- programme-incremental CAPEX.

No numeric or categorical downstream network result is inferred from these rows.

## Canonical state and blockers

`registry/dso_service_area_membership_crosswalk.csv` remains header-only.

The following blockers remain active:

- `NO_COMPLETE_KSH_DSO_MEMBERSHIP_CROSSWALK`
- `PARTIAL_SETTLEMENT_USAGE_LOCATION_RESOLUTION_REQUIRED`

B10 remains `IN_PROGRESS`; readiness remains **15%**.

P41 therefore improves bounded evidence coverage only. It does not authorize closure of B10 or promotion of the canonical national service-area crosswalk.
