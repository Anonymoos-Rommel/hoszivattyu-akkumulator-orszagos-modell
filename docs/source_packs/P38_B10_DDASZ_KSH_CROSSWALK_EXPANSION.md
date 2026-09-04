# B10-P38 — E.ON DDÁSZ / KSH service-area crosswalk expansion

Status date: 2026-09-04

## Purpose

P38 is an **evidence/data slice**, not a new semantic gate.

It expands the bounded E.ON Dél-dunántúli Áramhálózati Zrt. service-area materialization from the three historical P22 rows to **43 materialized rows** by adding **40 additional** unambiguous whole-settlement memberships.

The national canonical crosswalk is not promoted.

## Core fail-closed boundaries

`SETTLEMENT NAME != KSH SETTLEMENT ID`

`KSH SETTLEMENT ID != DSO SERVICE-AREA MEMBERSHIP`

`WHOLE SETTLEMENT != NAMED SUBSETTLEMENT OR SETTLEMENT PART`

`DSO SERVICE-AREA MEMBERSHIP != EXACT DSO NODE`

`DER CURRENTNESS EDGE CAPS CURRENT MEMBERSHIP AT DER`

`PRIMARY KSH LOCATOR + DERIVED MACHINE LOCATOR != DIRECT PRIMARY ROW OBSERVATION`

`PUBLIC FACT USE != SOURCE-DOCUMENT REPUBLICATION != BULK DATABASE RECONSTRUCTION`

## 1. DDÁSZ territorial authority

P38 reuses the P22 authority chain for:

`SRC-B10-EON-DDASZ-M1-CANDIDATE-2025`

Official E.ON-hosted M1 attachment:

`https://www.eon.hu/content/dam/eon/eon-hungary/documents/hatarozatok-szabalyzatok-aram/EDE/2025/EDE_elo_usz_melleklet_20241209%20%28v1%29.pdf`

The attachment is revision-dated **2024-12-09**. Its M1 section is titled:

`E.ON DÉL-DUNÁNTÚLI ÁRAMHÁLÓZATI ZRT. TERÜLETI ILLETÉKESSÉGE`

P22 already established the exact current-file identity at:

`CURRENT_2026_DER_APPROVED_PACKAGE_REVISION_LINEAGE`

through the aligned EÜSZ/M1 revision, 2024-12-11 MEKH submission, H442/2025 indefinite approval with attachments, and current 2026 operator publication authority.

P38 does **not** upgrade this edge to OBS. Therefore every P38 membership remains `DER`.

## 2. Mixed-grain M1 list

The M1 territorial list mixes whole settlements with named settlement parts / localities.

Examples that are **not** promoted as whole settlements include:

- `Ágostonpuszta`;
- `Alsóbélatelep`;
- `Alsófakos`;
- `Alsóhetény`;
- `Alsóhídvég`;
- `Alsókölked`;
- `Alsókövesd`;
- `Alsópél`;
- `Alsótekeres`;
- `Andormajor`;
- `Antalfalu`;
- `Antalszállás`;
- `Bagola`;
- `Bajcsa`;
- `Balatonaliga`;
- `Balatonbozsok`;
- `Balatonkiliti`;
- `Balatonmária`;
- `Balatonszabadi - Sóstó`.

Presence of a name in M1 alone is insufficient for whole-settlement promotion.

## 3. KSH settlement identity

Primary current settlement-identity authority:

`SRC-B10-KSH-HNT-2025-SETTLEMENT-IDS`

Derived machine-readable locator:

`SRC-B10-KSH-HNT-2025-IRSZHNK-DERIVATION-2026`

The derived locator is used only to locate exact current five-digit KSH settlement codes and to require an unambiguous base row with empty `Településrész`.

Because the primary KSH XLSX row is not directly materialized in this workflow, the KSH identity edge is not claimed as a direct row OBS.

## 4. P38 bounded materialization

P38 adds exactly these 40 DDÁSZ whole-settlement rows:

| KSH code | Settlement |
|---|---|
| 06868 | Adorjás |
| 25812 | Ág |
| 26824 | Alap |
| 13329 | Almamellék |
| 23384 | Almásháza |
| 20376 | Almáskeresztúr |
| 34184 | Alsóbogát |
| 17385 | Alsómocsolád |
| 29665 | Alsónána |
| 11563 | Alsónyék |
| 32081 | Alsópáhok |
| 18829 | Alsórajk |
| 25283 | Alsószentiván |
| 33279 | Alsószentmárton |
| 28714 | Andocs |
| 26125 | Aparhant |
| 27298 | Apátvarasd |
| 06886 | Aranyosgadány |
| 28583 | Áta |
| 32735 | Attala |
| 05403 | Babarc |
| 09663 | Babarcszőlős |
| 30474 | Babócsa |
| 28316 | Bábonymegyer |
| 04738 | Bak |
| 14395 | Bakháza |
| 22275 | Bakóca |
| 08299 | Bakonya |
| 03975 | Baksa |
| 15097 | Baktüttös |
| 27377 | Balatonberény |
| 33853 | Balatonboglár |
| 19460 | Balatonendréd |
| 20729 | Balatonfenyves |
| 07117 | Balatonföldvár |
| 17002 | Balatongyörök |
| 07375 | Balatonkeresztúr |
| 33862 | Balatonlelle |
| 26462 | Balatonmagyaród |
| 16601 | Balatonszabadi |

Every P38 row is:

- `operator_id = EON_DDASZ`;
- `service_area_id = EON_DDASZ:SERVICE_AREA`;
- `coverage_scope = WHOLE_SETTLEMENT`;
- `usage_location_requirement = NONE`;
- `evidence_status = DER`;
- `status = WHOLE_SETTLEMENT_MEMBERSHIP_PROVEN`;
- bound to the DDÁSZ M1 source, current KSH 2025 authority, and KSH-derived locator.

The three historical P22 rows remain unchanged:

- Abaliget `12548`;
- Ádánd `06080`;
- Adony `08925`.

Therefore the bounded DDÁSZ state becomes:

**3 historical DER + 40 P38 DER = 43 materialized rows.**

## 5. What P38 does not prove

P38 does not prove:

- complete DDÁSZ settlement inventory;
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
