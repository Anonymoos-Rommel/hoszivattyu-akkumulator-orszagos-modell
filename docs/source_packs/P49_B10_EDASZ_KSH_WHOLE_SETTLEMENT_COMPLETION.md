# B10-P49 — E.ON ÉDÁSZ / KSH WHOLE-SETTLEMENT COMPLETION

## Purpose

P49 is a completion-first evidence/data slice for the E.ON Észak-dunántúli Áramhálózati Zrt. service-area membership surface.

It does not create a new semantic gate and it does not continue the historical arbitrary 40-row tranche pattern. The target is the complete current M1 population that can be defended as whole-settlement identity under the already established B10/P15 fail-closed boundary.

## Authorities

Primary DSO authority:

- `SRC-B10-EON-EDASZ-M1-CANDIDATE-2025`
- official approved-package M1 attachment, revision `20241209`
- currentness remains the P22 approved-package / MEKH revision-lineage conclusion

Identity authorities:

- `SRC-B10-KSH-HNT-2025-SETTLEMENT-IDS`
- `SRC-B10-KSH-HNT-2025-IRSZHNK-DERIVATION-2026`
- `SRC-B10-KSH-HNK-2019-SETTLEMENT-IDS` only for the exact Jánossomorja direct-KSH exception described below

## Complete current source accounting

The current ÉDÁSZ M1 extraction contains **874 source-token occurrences** and **873 unique source tokens**. The difference is the source-native duplicate `Séska`, which occurs twice but does not create two locality identities.

P39/history already materialized **45** ÉDÁSZ whole-settlement identities. Forty-three are exact current-M1/KSH identities. The other two remain the already-audited P39 identity-specific equivalence paths:

- `Alcsutdoboz` → `15176 Alcsútdoboz`
- `Alsóőrs` → `30526 Alsóörs`

P49 does not broaden those two historical permissions into a general accent, spelling, or fuzzy-name rule.

After exact KSH locator matching, one exact KSH-2019 fallback, and exactly two parser-only extraction corrections, the candidate pass produced **775 new** whole-settlement identities. The global cross-DSO uniqueness gate then excluded six identities already proven as whole-settlement memberships of another DSO.

P49 therefore admits **769 new DER whole-settlement identities**.

Therefore:

`45 historical + 769 P49 = 814 materialized current provable whole-settlement identities`

On the unique-token denominator:

`873 unique source tokens - 814 represented whole-settlement identities = 59 unresolved unique tokens`

Because unresolved `Séska` occurs twice in the source, the unresolved occurrence count is **60**.

Those unresolved tokens are not treated as zero, absent, or outside the ÉDÁSZ service area. They are simply not admitted to the exact whole-settlement materialization surface by P49.

## Normal path

The normal P49 path requires:

1. a current ÉDÁSZ M1 source token;
2. an exact whole-settlement name identity in the KSH-derived locator;
3. a unique five-digit KSH settlement code;
4. no named settlement-part / special-grain indication;
5. no identity-equivalence inference;
6. no collision with an already-proven whole-settlement membership of another DSO.

Rows admitted through this path remain `DER`, not `OBS`.

## Parser-only extraction corrections

Exactly two extraction artifacts are corrected before exact identity matching:

| Extracted token | Official M1 identity retained | KSH code |
| --- | --- | ---: |
| `P ázmándfalu` | `Pázmándfalu` | `12715` |
| `Zsira 9` | `Zsira` | `04622` |

The official M1 renders `Pázmándfalu` without the inserted internal space, and `Zsira` is the final M1 locality before the following page/M2 boundary. These are parser-boundary repairs only.

`PDF EXTRACTION ARTIFACT CORRECTION != FUZZY IDENTITY MATCH`

They do not authorize accent folding, edit-distance matching, arbitrary whitespace repair, suffix stripping, token splitting, or generalized name normalization.

## Exact direct official KSH 2019 exception

The reproducible derived locator does not directly materialize one source-exact whole-locality row. Exact official KSH 2019 locality identity supplies it instead:

- `29221 Jánossomorja`

The ÉDÁSZ M1 name and the official KSH 2019 locality name are exact. No spelling equivalence is inferred.

## Six cross-DSO whole-settlement conflicts remain fail-closed

Six exact ÉDÁSZ M1/KSH locality matches cannot be admitted as ÉDÁSZ whole-settlement memberships because the same KSH identity is already separately proven as a whole-settlement membership of another DSO:

| ÉDÁSZ M1 token | KSH code | Existing proven whole-settlement operator |
| --- | ---: | --- |
| `Bodorfa` | `04321` | E.ON DDÁSZ |
| `Szentgál` | `07922` | E.ON DDÁSZ |
| `Bocfölde` | `17543` | E.ON DDÁSZ |
| `Pilisszentkereszt` | `18731` | ELMŰ |
| `Nagykapornak` | `20589` | E.ON DDÁSZ |
| `Mány` | `23490` | ELMŰ |

The ÉDÁSZ M1 authority is an administrative-unit list. Exact name presence does not override a separately proven whole-settlement DSO membership.

`EXACT ADMINISTRATIVE-UNIT NAME MATCH != SECOND WHOLE-SETTLEMENT DSO MEMBERSHIP`

All six conflicts are recorded in `registry/dso_service_area_membership_edasz_p49_exceptions.csv` as `CROSS_DSO_WHOLE_CONFLICT_EXCLUDED` and are absent from the P49 pair surface.

## Source-native spelling edges remain fail-closed

After excluding the two already-authorized historical P39 equivalences and the parser-only Pázmándfalu correction, **30 source-native spelling-equivalence diagnostics** remain unresolved. Examples include:

- `Bakonykuti` → diagnostic KSH candidate `Bakonykúti`
- `Dőr` → `Dör`
- `Felcsut` → `Felcsút`
- `Gönyü` → `Gönyű`
- `Kemeneshögyész` → `Kemeneshőgyész`
- `Kővágóőrs` → `Kővágóörs`
- `Sotony` → `Sótony`
- `Sur` → `Súr`
- `Szomod` → `Szomód`
- `Zalalővő` → `Zalalövő`

These are diagnostics only.

`SOURCE SPELLING DIFFERENCE != AUTHORIZED IDENTITY EQUIVALENCE`

P49 does not mint a generalized fuzzy-name, accent-normalization, or typo-correction authority.

## Special / mixed administrative grains remain fail-closed

The unresolved population also includes source forms such as:

- `Ács-Jegespuszta`
- `Gánt Vérteskozma`
- `Isztimér-Királysz.`
- `Kerkateskánd-hegy`
- `Lesencei-Uzsabánya`
- `Lovászi Luku-hegy`
- `Rábapaty-Felsőpaty`
- `Szőce-Rimány`
- `Szt.Királyszabadja`

P49 does not promote those records to whole-settlement membership.

Accordingly the operator extraction state deliberately remains:

`PARTIAL_TRANCHE_MATERIALIZED`

and not a complete operator membership crosswalk claim.

## Normalized storage

Because P49 adds 769 records, repeated operator/source/status fields are stored once in a manifest and the exact identity surface is stored as a two-column pair file:

- `registry/dso_service_area_membership_edasz_p49_pairs.csv`
- `registry/dso_service_area_membership_edasz_p49_manifest.csv`
- `registry/dso_service_area_membership_edasz_p49_exceptions.csv`

The manifest reconstructs the same row-level semantics for every admitted normal P49 identity. The exception file records the one direct-KSH admission, two parser-only admissions, and six excluded cross-DSO conflicts.

`NORMALIZED STORAGE != WEAKER ROW-LEVEL EVIDENCE`

## Completion boundary

P49 closes the complete **currently provable whole-settlement materialization** for ÉDÁSZ under the stated authority paths and cross-DSO conflict gate; it does not close all ÉDÁSZ M1 grains.

`COMPLETE PROVABLE WHOLE-SETTLEMENT MATERIALIZATION != COMPLETE OPERATOR MEMBERSHIP CROSSWALK`

The national canonical crosswalk therefore remains header-only.

P49 does not prove or infer:

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
