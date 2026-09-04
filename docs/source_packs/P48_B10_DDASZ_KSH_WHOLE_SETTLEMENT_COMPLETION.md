# B10-P48 — E.ON DDÁSZ / KSH WHOLE-SETTLEMENT COMPLETION

## Purpose

P48 is a completion-first evidence/data slice for the E.ON Dél-dunántúli Áramhálózati Zrt. service-area membership surface.

It does not create a new semantic gate and it does not continue the historical arbitrary 40-row tranche pattern. The target is the complete current M1 population that can be defended as exact whole-settlement identity under the already established B10/P15 boundary.

## Authorities

Primary DSO authority:

- `SRC-B10-EON-DDASZ-M1-CANDIDATE-2025`
- current approved-package M1 attachment, revision `20241209`
- currentness remains the P22 approved-package / MEKH revision-lineage conclusion

Identity authorities:

- `SRC-B10-KSH-HNT-2025-SETTLEMENT-IDS`
- `SRC-B10-KSH-HNT-2025-IRSZHNK-DERIVATION-2026`
- `SRC-B10-KSH-HNK-2019-SETTLEMENT-IDS` only for the two exact direct-KSH exception rows described below

## Complete current source accounting

The current DDÁSZ M1 contains **1116 unique source tokens**.

P38/history already materialized **43** DDÁSZ whole-settlement identities. Every one of those 43 historical identities is present in the current M1 source population.

The initial exact-name candidate pass produced 779 new rows, but the global cross-DSO uniqueness gate exposed two current M1 tokens that collide with already-proven MVM Démász whole-settlement memberships: `Dusnok` (`04109`) and `Mélykút` (`16018`). Because the DDÁSZ M1 source semantics are `ADMINISTRATIVE_UNITS_IN_M1`, exact name presence alone cannot override a separately proven whole-settlement operator membership.

P48 therefore admits **777** new exact DER whole-settlement identities.

Therefore:

`43 historical + 777 P48 = 820 materialized current provable whole-settlement identities`

The remaining:

`1116 - 820 = 296`

source tokens remain fail-closed.

Those 296 are not treated as zero, absent, or outside the DDÁSZ service area. They are merely not admitted to the exact whole-settlement materialization surface by P48.

## Normal path

The normal P48 path requires:

1. a current DDÁSZ M1 source token;
2. an exact whole-settlement name identity in the KSH-derived locator;
3. a unique five-digit KSH settlement code;
4. no named settlement-part / special-grain indication;
5. no identity equivalence inference;
6. no collision with an already-proven whole-settlement membership of another DSO.

Rows admitted through this path remain `DER`, not `OBS`.

## PDF extraction artifact corrections

Exactly three parser-only extraction artifacts are corrected before exact identity matching:

| Extracted token | Source identity retained | KSH code |
| --- | --- | ---: |
| `E.ON Dél-dunántúli Áramhálózati Zrt. - Elosztói Üzletszabályzat Husztót` | `Husztót` | `31431` |
| `E.ON Dél-dunántúli Áramhálózati Zrt. - Elosztói Üzletszabályzat Pogányszentpéter` | `Pogányszentpéter` | `27553` |
| `S zaporca` | `Szaporca` | `34032` |

The first two remove a page-header string attached by PDF text extraction. The third removes an extraction-inserted internal space from the source word.

`PDF EXTRACTION ARTIFACT CORRECTION != FUZZY IDENTITY MATCH`

These repairs do not authorize accent folding, edit-distance matching, arbitrary whitespace repair, token splitting, or any generalized name-normalization rule.

## Direct official KSH 2019 exceptions

The reproducible derived locator does not directly materialize two source-exact whole-locality rows. Exact official KSH 2019 locality identity supplies them instead:

- `33233 Gödre`
- `10348 Zalakomár`

For both rows the DDÁSZ M1 name and the official KSH 2019 locality name are exact. No spelling equivalence is inferred.

## Cross-DSO whole-settlement conflicts remain fail-closed

Two DDÁSZ M1 tokens are exact KSH locality-name matches but cannot be admitted as DDÁSZ whole-settlement memberships because the same KSH identity is already separately proven as MVM Démász whole-settlement membership:

| DDÁSZ M1 token | KSH code | Existing proven whole-settlement operator |
| --- | ---: | --- |
| `Dusnok` | `04109` | MVM Démász |
| `Mélykút` | `16018` | MVM Démász |

Dusnok is already present on the historical MVM Démász materialization surface. Mélykút is present on the P45 MVM Démász completion surface. The MVM Démász authority explicitly separates whole-settlement from partial-settlement coverage, while the DDÁSZ M1 authority is an administrative-unit list.

Therefore P48 does not mint a second whole-settlement DSO membership from name equality alone.

`EXACT ADMINISTRATIVE-UNIT NAME MATCH != SECOND WHOLE-SETTLEMENT DSO MEMBERSHIP`

Both conflicts are recorded in `registry/dso_service_area_membership_ddasz_p48_exceptions.csv` as `CROSS_DSO_WHOLE_CONFLICT_EXCLUDED` and are absent from the P48 pair surface.

## Fourteen spelling-equivalence edges remain fail-closed

P48 deliberately does **not** authorize the following source-name to current KSH-name equivalences:

| DDÁSZ M1 source spelling | KSH diagnostic candidate | KSH code |
| --- | --- | ---: |
| `Balatonöszöd` | `Balatonőszöd` | `11916` |
| `Baranyahidvég` | `Baranyahídvég` | `20464` |
| `Csikóstöttös` | `Csikóstőttős` | `30094` |
| `Cun` | `Cún` | `11086` |
| `Füzvölgy` | `Fűzvölgy` | `16531` |
| `Kallosd` | `Kallósd` | `05537` |
| `Kálóz` | `Káloz` | `16683` |
| `Kazsók` | `Kazsok` | `26888` |
| `Köröshegy` | `Kőröshegy` | `15510` |
| `Kövágótöttös` | `Kővágótöttös` | `06992` |
| `Öcsény` | `Őcsény` | `08961` |
| `Szabadhidvég` | `Szabadhídvég` | `18740` |
| `Turony` | `Túrony` | `18582` |
| `Vókány` | `Vokány` | `05892` |

These candidates are useful diagnostics only.

`SOURCE SPELLING DIFFERENCE != AUTHORIZED IDENTITY EQUIVALENCE`

No generalized fuzzy-name or accent-normalization authority is minted by P48.

## Remaining special-grain population

Beyond the fourteen spelling edges and the two cross-DSO conflicts, the unresolved population is dominated by named settlement parts and other M1 special/mixed administrative grains.

P48 does not promote those records to whole-settlement membership.

Accordingly the operator extraction state deliberately remains:

`PARTIAL_TRANCHE_MATERIALIZED`

and not a complete operator membership crosswalk claim.

## Normalized storage

Because P48 adds 777 records, the repeated operator/source/status fields are stored once in a manifest and the exact identity surface is stored as a two-column pair file:

- `registry/dso_service_area_membership_ddasz_p48_pairs.csv`
- `registry/dso_service_area_membership_ddasz_p48_manifest.csv`
- `registry/dso_service_area_membership_ddasz_p48_exceptions.csv`

The manifest reconstructs the same row-level semantics for every admitted normal P48 identity. The exception file separately records parser/direct-KSH admission paths and the two excluded cross-DSO conflicts.

`NORMALIZED STORAGE != WEAKER ROW-LEVEL EVIDENCE`

## Completion boundary

P48 closes the complete **currently provable whole-settlement materialization** for DDÁSZ under the stated authority paths and cross-DSO conflict gate; it does not close all DDÁSZ M1 grains.

`COMPLETE PROVABLE WHOLE-SETTLEMENT MATERIALIZATION != COMPLETE OPERATOR MEMBERSHIP CROSSWALK`

The national canonical crosswalk therefore remains header-only.

P48 does not prove or infer:

- exact programme entity to DSO-node mapping;
- exact node identity;
- node headroom or sufficiency;
- limiting node;
- reinforcement requirement;
- reinforcement scope or cost;
- programme-incremental CAPEX;
- timed programme-incremental CAPEX.

## B10 state

The standing closure blockers remain in force, including:

- `NO_COMPLETE_KSH_DSO_MEMBERSHIP_CROSSWALK`
- `PARTIAL_SETTLEMENT_USAGE_LOCATION_RESOLUTION_REQUIRED`

B10 remains `IN_PROGRESS` and readiness remains **15%**.
