# B10-P39 — E.ON ÉDÁSZ / KSH service-area crosswalk expansion

Status date: 2026-09-04

## Purpose

P39 is an **evidence/data slice**, not a new semantic gate.

It expands the bounded E.ON Észak-dunántúli Áramhálózati Zrt. service-area materialization from the three historical P22 rows to **45 materialized rows** by adding **42 additional** whole-settlement memberships.

The national canonical crosswalk is not promoted.

## Core fail-closed boundaries

`SETTLEMENT NAME != KSH SETTLEMENT ID`

`KSH SETTLEMENT ID != DSO SERVICE-AREA MEMBERSHIP`

`WHOLE SETTLEMENT != NAMED SUBSETTLEMENT OR SETTLEMENT PART`

`DSO SERVICE-AREA MEMBERSHIP != EXACT DSO NODE`

`DER CURRENTNESS EDGE CAPS CURRENT MEMBERSHIP AT DER`

`PRIMARY KSH LOCATOR + DERIVED MACHINE LOCATOR != DIRECT PRIMARY ROW OBSERVATION`

`EXPLICIT NAME EQUIVALENCE OVERRIDE != GENERAL FUZZY MATCHING RULE`

`PUBLIC FACT USE != SOURCE-DOCUMENT REPUBLICATION != BULK DATABASE RECONSTRUCTION`

## 1. ÉDÁSZ territorial authority

P39 reuses the P22 authority chain for:

`SRC-B10-EON-EDASZ-M1-CANDIDATE-2025`

Official E.ON-hosted M1 attachment:

`https://www.eon.hu/content/dam/eon/eon-hungary/documents/hatarozatok-szabalyzatok-aram/EED/2025/EED_elo_usz_melleklet_20241209%20%28v1%29.pdf`

The attachment is revision-dated **2024-12-09**. Its M1 section is titled:

`E.ON ÉSZAK-DUNÁNTÚLI ÁRAMHÁLÓZATI ZRT. TERÜLETI ILLETÉKESSÉGE`

P22 already established the exact current-file identity at:

`CURRENT_2026_DER_APPROVED_PACKAGE_REVISION_LINEAGE`

through the aligned EÜSZ/M1 revision, 2024-12-11 MEKH submission, H440/2025 indefinite approval with attachments, and current 2026 operator publication authority.

P39 does **not** upgrade this edge to OBS. Therefore every P39 membership remains `DER`.

## 2. Mixed-grain and explicit-equivalence boundary

The M1 territorial list cannot be treated as a clean current-KSH whole-settlement table without row-level identity checks.

P39 does not promote `Ács-Jegespuszta`, because it is not accepted as an independent whole-settlement identity.

Two M1/current-KSH spelling differences are accepted by explicit project authority rather than silently normalized:

- `Alcsutdoboz` → current KSH `Alcsútdoboz` (`15176`);
- `Alsóőrs` → current KSH `Alsóörs` (`30526`).

These two equivalences are explicit, audited exceptions and do **not** establish a general fuzzy-name or accent-normalization rule. Presence of any other non-exact name in M1 remains insufficient for automatic whole-settlement promotion.

## 3. KSH settlement identity

Primary current settlement-identity authority:

`SRC-B10-KSH-HNT-2025-SETTLEMENT-IDS`

Derived machine-readable locator:

`SRC-B10-KSH-HNT-2025-IRSZHNK-DERIVATION-2026`

The derived locator is used only to locate current five-digit KSH settlement codes and to require an unambiguous base row with empty `Településrész`.

Because the primary KSH XLSX row is not directly materialized in this workflow, the KSH identity edge is not claimed as a direct row OBS.

## 4. P39 bounded materialization

P39 adds exactly these 42 ÉDÁSZ whole-settlement rows:

| KSH code | Settlement |
|---|---|
| 04561 | Ábrahámhegy |
| 07214 | Acsád |
| 33385 | Acsalag |
| 18139 | Ácsteszér |
| 07302 | Adásztevel |
| 31307 | Adorjánháza |
| 04880 | Ágfalva |
| 29407 | Agyagosszergény |
| 06673 | Ajka |
| 06682 | Aka |
| 02644 | Alibánfa |
| 15176 | Alcsútdoboz |
| 32346 | Almásfüzitő |
| 19512 | Alsónemesapáti |
| 30526 | Alsóörs |
| 08767 | Alsószenterzsébet |
| 22549 | Alsószölnök |
| 22725 | Alsóújlak |
| 12317 | Andrásfa |
| 34227 | Annavölgy |
| 28370 | Apácatorna |
| 08873 | Apátistvánfalva |
| 32249 | Árpás |
| 26921 | Ásványráró |
| 07339 | Aszófő |
| 19363 | Bábolna |
| 21263 | Babosdöbréte |
| 15042 | Babót |
| 22327 | Badacsonytomaj |
| 03267 | Badacsonytördemic |
| 11059 | Baglad |
| 30368 | Bagod |
| 28769 | Bágyogszovát |
| 29212 | Baj |
| 17020 | Bajánsenye |
| 16744 | Bajna |
| 29355 | Bajót |
| 24244 | Bakonybánk |
| 23746 | Bakonybél |
| 08730 | Bakonycsernye |
| 28936 | Bakonygyirót |
| 29513 | Bakonyjákó |

Every P39 row is:

- `operator_id = EON_EDASZ`;
- `service_area_id = EON_EDASZ:SERVICE_AREA`;
- `coverage_scope = WHOLE_SETTLEMENT`;
- `usage_location_requirement = NONE`;
- `evidence_status = DER`;
- `status = WHOLE_SETTLEMENT_MEMBERSHIP_PROVEN`;
- bound to the ÉDÁSZ M1 source, current KSH 2025 authority, and KSH-derived locator.

For `Alcsútdoboz` and `Alsóörs`, the row note must preserve the exact M1 spelling and the explicit equivalence decision.

The three historical P22 rows remain unchanged:

- Aba `17376`;
- Abda `11882`;
- Ács `04428`.

Therefore the bounded ÉDÁSZ state becomes:

**3 historical DER + 42 P39 DER = 45 materialized rows.**

## 5. What P39 does not prove

P39 does not prove:

- complete ÉDÁSZ settlement inventory;
- complete national KSH-to-DSO service-area coverage;
- named settlement-part / usage-location membership;
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
