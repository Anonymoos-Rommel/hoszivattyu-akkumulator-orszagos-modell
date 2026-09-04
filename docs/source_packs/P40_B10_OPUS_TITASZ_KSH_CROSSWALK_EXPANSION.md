# B10-P40 — OPUS TITÁSZ / KSH service-area crosswalk expansion

Status date: 2026-09-04

## Purpose

P40 is an **evidence/data slice**, not a new semantic gate.

It expands the bounded OPUS TITÁSZ Áramhálózati Zrt. service-area materialization from the ten historical P20 rows to **50 materialized rows** by adding the next **40 whole-settlement memberships** from the current official M1 territorial-jurisdiction list.

The national canonical crosswalk is not promoted.

## Core fail-closed boundaries

`SETTLEMENT NAME != KSH SETTLEMENT ID`

`KSH SETTLEMENT ID != DSO SERVICE-AREA MEMBERSHIP`

`WHOLE SETTLEMENT != PARTIAL SETTLEMENT OR USAGE-LOCATION MEMBERSHIP`

`DSO SERVICE-AREA MEMBERSHIP != EXACT DSO NODE`

`BOUNDED CURRENT M1 ROWS != COMPLETE OPERATOR CROSSWALK`

`PUBLIC FACT USE != SOURCE-DOCUMENT REPUBLICATION != BULK DATABASE RECONSTRUCTION`

## 1. OPUS TITÁSZ current territorial authority

P40 reuses the current authority already registered by P20:

`SRC-B10-OPUS-TITASZ-M1-2026`

Official OPUS TITÁSZ M1 attachment:

`https://www.opustitasz.hu/storage/documents/tarsasagunk/szabalyzatok/uzletszabalyzat/hatalyban-levo/OPUS%20TITASZ_%C3%9Czletszab%C3%A1lyzat%20mell%C3%A9klet.pdf`

The attachment identifies itself as the 2026 OPUS TITÁSZ distribution business-rule annex package. M1 is titled:

`1. AZ OPUS TITÁSZ ZRT. TERÜLETI ILLETÉKESSÉGE`

and enumerates settlements by serial number, settlement name and county.

P20 materialized M1 serials **1–10**. P40 extends the bounded materialization with serials **11–50** exactly as published.

No name normalization, fuzzy matching or inferred settlement identity is needed for this tranche.

## 2. KSH settlement identity

P40 reuses the P20 KSH authority:

`SRC-B10-KSH-HNK-2019-SETTLEMENT-IDS`

Official KSH gazetteer:

`https://www.ksh.hu/docs/hun/hnk/hnk_2019.pdf`

Section IV publishes the five-digit `településazonosító törzsszám` by settlement name.

P20 already established the identity rule used here: the official five-digit KSH settlement identifier remains unchanged for a continuing settlement and is not reassigned after dissolution. For all 40 P40 rows, the current OPUS M1 settlement name has an exact corresponding KSH 2019 settlement-name entry with the materialized five-digit identifier.

Because both required facts are directly published by official sources — current OPUS whole-settlement membership and official KSH five-digit settlement identity — the P40 rows remain `OBS`, consistent with the P20 OPUS tranche.

## 3. P40 bounded materialization

P40 adds exactly M1 serials 11–50:

| M1 serial | KSH code | Settlement |
|---:|---|---|
| 11 | 15167 | Bakonszeg |
| 12 | 02325 | Baktalórántháza |
| 13 | 26958 | Balkány |
| 14 | 02918 | Balmazújváros |
| 15 | 15963 | Balsa |
| 16 | 26480 | Barabás |
| 17 | 26693 | Báránd |
| 18 | 02990 | Bátorliget |
| 19 | 33446 | Bedő |
| 20 | 25441 | Benk |
| 21 | 28246 | Beregdaróc |
| 22 | 20677 | Beregsurány |
| 23 | 18467 | Berekböszörmény |
| 24 | 34005 | Berekfürdő |
| 25 | 12788 | Berettyóújfalu |
| 26 | 07472 | Berkesz |
| 27 | 13639 | Besenyőd |
| 28 | 11305 | Besenyszög |
| 29 | 21227 | Beszterec |
| 30 | 02680 | Békésszentandrás |
| 31 | 25256 | Bihardancsháza |
| 32 | 19956 | Biharkeresztes |
| 33 | 24828 | Biharnagybajom |
| 34 | 29887 | Bihartorda |
| 35 | 29610 | Biharugra |
| 36 | 02945 | Biri |
| 37 | 34102 | Bocskaikert |
| 38 | 14137 | Bojt |
| 39 | 22239 | Botpalád |
| 40 | 11299 | Bököny |
| 41 | 13471 | Bucsa |
| 42 | 19707 | Buj |
| 43 | 09681 | Cégénydányád |
| 44 | 22938 | Cibakháza |
| 45 | 31334 | Csabacsűd |
| 46 | 34175 | Csataszög |
| 47 | 12928 | Csaholc |
| 48 | 29416 | Csaroda |
| 49 | 09715 | Császló |
| 50 | 26107 | Csegöld |

Every P40 row is:

- `operator_id = OPUS_TITASZ`;
- `service_area_id = OPUS_TITASZ:SERVICE_AREA`;
- `coverage_scope = WHOLE_SETTLEMENT`;
- `usage_location_requirement = NONE`;
- `source_ids = SRC-B10-OPUS-TITASZ-M1-2026;SRC-B10-KSH-HNK-2019-SETTLEMENT-IDS`;
- `evidence_status = OBS`;
- `status = WHOLE_SETTLEMENT_MEMBERSHIP_PROVEN`.

The ten historical P20 OPUS rows remain unchanged:

1. Abádszalók `12441`;
2. Abony `27872`;
3. Ajak `08776`;
4. Alattyán `25265`;
5. Anarcs `29975`;
6. Apagy `20303`;
7. Aranyosapáti `09353`;
8. Álmosd `27641`;
9. Ártánd `03319`;
10. Bagamér `20011`.

Therefore the bounded OPUS TITÁSZ state becomes:

**10 historical P20 OBS + 40 P40 OBS = 50 materialized rows.**

## 4. What P40 does not prove

P40 does not prove:

- complete OPUS TITÁSZ settlement inventory materialization;
- complete national KSH-to-DSO service-area coverage;
- any partial-settlement / usage-location membership;
- exact programme entity-to-node mapping;
- complete DSO node inventory;
- topology or limiting nodes;
- headroom sufficiency;
- reinforcement need;
- reinforcement cost;
- programme-incremental CAPEX.

The canonical national file:

`registry/dso_service_area_membership_crosswalk.csv`

remains header-only.

The following blockers remain active:

- `NO_COMPLETE_KSH_DSO_MEMBERSHIP_CROSSWALK`;
- `PARTIAL_SETTLEMENT_USAGE_LOCATION_RESOLUTION_REQUIRED`.

B10 remains `IN_PROGRESS`; readiness remains **15%**.
