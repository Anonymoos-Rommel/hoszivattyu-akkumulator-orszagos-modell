# B10-P37 — ELMŰ / KSH service-area crosswalk expansion

Canonical base: `fdf90e53e020867e6cda4c7ffff39b81f724a7b3`

## Scope

P37 is an **evidence/data slice**. It expands the bounded ELMŰ whole-settlement service-area tranche while preserving the P22 current-M1 authority decision and the existing P15/P20/P21/P22 crosswalk semantics.

It introduces no new semantic contract, does not claim a complete ELMŰ inventory, and does not change B10 readiness.

## Core boundaries

`SETTLEMENT NAME != KSH SETTLEMENT ID`

`KSH SETTLEMENT ID != DSO SERVICE-AREA MEMBERSHIP`

`WHOLE SETTLEMENT != NAMED SUBSETTLEMENT OR SETTLEMENT PART`

`DSO SERVICE-AREA MEMBERSHIP != EXACT DSO NODE`

`DER CURRENTNESS EDGE CAPS CURRENT MEMBERSHIP AT DER`

`PRIMARY KSH LOCATOR + DERIVED MACHINE LOCATOR != DIRECT PRIMARY ROW OBSERVATION`

`PUBLIC FACT USE != SOURCE-DOCUMENT REPUBLICATION != BULK DATABASE RECONSTRUCTION`

These boundaries are fail-closed.

## Authority chain

### ELMŰ membership authority

Existing source ID:

`SRC-B10-ELMU-M1-CANDIDATE-2025`

Direct official E.ON-hosted M1 attachment:

`https://www.eon.hu/content/dam/eon/eon-hungary/documents/pest-megyei-halozat/tarsasagunkrol/%C3%BCzletszab%C3%A1lyzatok/2025/0617/ELMu_elo_usz_melleklet_20250410.pdf`

The attachment is dated **2025-04-10**. Its M1 section, page 7, is titled **“ELMŰ HÁLÓZATI KFT. TERÜLETI ILLETÉKESSÉGE”** and directly lists the service-area names used by P37.

P22 already proved current 2026 use of this exact attachment at:

`CURRENT_2026_DER_APPROVED_PACKAGE_REVISION_LINEAGE`

through the approved-package revision lineage. P37 does not reopen that currentness decision and does not upgrade it to OBS. The direct M1 list can be observed, but the current-file identity edge remains DER; therefore the current service-area membership rows remain **DER**.

### KSH identity authority and machine locator

Primary authority locator:

`SRC-B10-KSH-HNT-2025-SETTLEMENT-IDS`

`https://www.ksh.hu/docs/helysegnevtar/hnt_letoltes_2025.xlsx`

Reproducible machine-readable derivation helper:

`SRC-B10-KSH-HNT-2025-IRSZHNK-DERIVATION-2026`

`https://github.com/ferenci-tamas/IrszHnk/blob/master/IrszHnk.csv`

The derived CSV is used only to locate exact name/code pairs whose `Településrész` field is empty. It is not promoted to primary statistical authority. Because the primary KSH XLSX rows are not directly materialized in this workflow, every new P37 row remains **DER**.

## P37 bounded materialization

P37 adds **40 additional** ELMŰ whole-settlement rows:

| KSH code | Settlement |
|---|---|
| `10108` | Áporka |
| `18777` | Bernecebaráti |
| `08891` | Biatorbágy |
| `03407` | Budajenő |
| `23463` | Budakalász |
| `12052` | Budakeszi |
| `23278` | Budaörs |
| `32027` | Bugyi |
| `06822` | Csobánka |
| `33118` | Csomád |
| `22804` | Csömör |
| `34333` | Csörög |
| `26985` | Csővár |
| `09247` | Dabas |
| `09973` | Délegyháza |
| `24013` | Diósd |
| `29647` | Dömsöd |
| `25362` | Dunabogdány |
| `09584` | Dunaharaszti |
| `18616` | Dunakeszi |
| `20534` | Dunavarsány |
| `24518` | Ecser |
| `30988` | Érd |
| `13480` | Erdőkertes |
| `06035` | Felsőpakony |
| `32610` | Fót |
| `13295` | Galgagyörk |
| `27128` | Galgamácsa |
| `32559` | Gödöllő |
| `25627` | Gyál |
| `29735` | Gyömrő |
| `09690` | Halásztelek |
| `33552` | Herceghalom |
| `32106` | Inárcs |
| `28097` | Ipolydamásd |
| `04978` | Ipolytölgyes |
| `07807` | Isaszeg |
| `32230` | Kakucs |
| `22345` | Kemence |
| `34166` | Kerepes |

For every new row:

- `operator_id = ELMU`;
- `service_area_id = ELMU:SERVICE_AREA`;
- `coverage_scope = WHOLE_SETTLEMENT`;
- `usage_location_requirement = NONE`;
- `evidence_status = DER`;
- `status = WHOLE_SETTLEMENT_MEMBERSHIP_PROVEN`;
- source chain = ELMŰ M1 + primary KSH locator + reproducible KSH-derived locator.

The three historical P22 ELMŰ rows remain unchanged DER observations from the earlier source chain:

- Acsa `18573`;
- Alsónémedi `23199`;
- Apaj `33561`.

Therefore the bounded ELMŰ tranche state after P37 is **43 materialized rows = 3 historical P22 DER + 40 P37 DER**. This is a bounded state, not a completeness claim or permanent registry-size invariant.

## Fail-closed exclusions

The ELMŰ M1 mixes whole settlements with names that cannot be promoted automatically to a KSH whole-settlement record. Examples include:

- `Bankháza (Kiskunlacháza)`;
- `Domonyvölgy (Domony)`;
- `Tass üdülőterület`.

P37 also rejects an M1 name when the KSH-derived locator does not expose one unambiguous empty-`Településrész` row. In particular:

- `Budapest` is represented through KSH district records rather than one whole-settlement row in the machine locator;
- `Göd` is represented there through `Alsógöd` and `Felsőgöd` rows, without an empty-`Településrész` row.

P37 therefore does not manufacture whole-settlement identities for those names.

## Completeness boundary

The canonical national registry:

`registry/dso_service_area_membership_crosswalk.csv`

remains **header-only**.

P37 does not prove:

- a complete normalized ELMŰ settlement inventory;
- a complete national KSH-to-DSO membership crosswalk;
- usage-location resolution for named or partial settlements;
- exact DSO node identity;
- node topology or feeder/substation assignment;
- published headroom for programme entities;
- limiting-node status;
- reinforcement requirement;
- reinforcement cost;
- programme-incremental CAPEX.

The blockers remain active, including:

- `NO_COMPLETE_KSH_DSO_MEMBERSHIP_CROSSWALK`;
- `PARTIAL_SETTLEMENT_USAGE_LOCATION_RESOLUTION_REQUIRED`;
- `NO_COMPLETE_NATIONAL_DSO_NODE_INVENTORY`;
- `NO_REAL_PROGRAMME_NODE_PANEL`;
- `INCREMENTAL_CAPEX_ATTRIBUTION_HEADER_ONLY`.

B10 remains `IN_PROGRESS`; readiness remains **15%**.
