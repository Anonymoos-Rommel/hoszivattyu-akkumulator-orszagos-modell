# B10-P60 — E.ON ÉDÁSZ cross-DSO conflict authority audit

Status date: 2026-09-05

Canonical base: `26ce8c7ebb6cd3e9117f049034e0b606cad195d6`

## Purpose

P60 is a fail-closed authority-audit slice over the exact six cross-DSO whole-settlement conflicts excluded by P49 for E.ON Észak-dunántúli Áramhálózati Zrt.:

- `04321 Bodorfa`
- `07922 Szentgál`
- `17543 Bocfölde`
- `18731 Pilisszentkereszt`
- `20589 Nagykapornak`
- `23490 Mány`

P60 adds zero service-area membership rows. It sharpens the authority boundary between current ÉDÁSZ administrative-unit presence, already-proven current DDÁSZ or ELMŰ whole-settlement memberships, and historical E.ON network-licensee evidence.

## Current ÉDÁSZ authority

P49 remains the current ÉDÁSZ source path through `SRC-B10-EON-EDASZ-M1-CANDIDATE-2025`, approved-package M1 revision `20241209`.

The current ÉDÁSZ M1 contains all six names as source-native administrative-unit tokens.

Exact source-token presence does not itself prove a second current whole-settlement DSO membership.

`CURRENT ÉDÁSZ M1 ADMINISTRATIVE-UNIT PRESENCE != CURRENT ÉDÁSZ WHOLE-SETTLEMENT MEMBERSHIP`

## Current competing whole-settlement authority

Current repository authority already proves:

- `04321 Bodorfa` → E.ON DDÁSZ
- `07922 Szentgál` → E.ON DDÁSZ
- `17543 Bocfölde` → E.ON DDÁSZ
- `20589 Nagykapornak` → E.ON DDÁSZ
- `18731 Pilisszentkereszt` → ELMŰ
- `23490 Mány` → ELMŰ

The DDÁSZ identities are present on the P48 current whole-settlement materialization surface. The ELMŰ identities are present on the P46 current whole-settlement materialization surface.

P60 preserves those current whole-settlement decisions and does not mint a second ÉDÁSZ whole-settlement membership.

## Historical E.ON network-licensee evidence

P60 reuses the official E.ON-hosted 2022 E.ON Áramszolgáltató 5th appendix already used by P53/P54:

`https://www.eon.hu/content/dam/eon/eon-hungary/documents/hatarozatok-szabalyzatok-aram/eas/2022/EON_Aramszolg_egyetemes_USZ_fugg_mell_korrekturazott_tervezet.pdf`

The appendix is a `Település | Hálózati engedélyes | Megye` table.

For four current DDÁSZ conflicts, the historical table contains both ÉDÁSZ and DDÁSZ rows for the same settlement:

- `Bodorfa`
- `Szentgál`
- `Bocfölde`
- `Nagykapornak`

This is historical dual-E.ON-licensee corroboration. It does not establish the geometry, usage-location boundary, effective date, or current persistence of any split.

`HISTORICAL DUAL-LICENSEE ROWS != CURRENT DUAL WHOLE-SETTLEMENT MEMBERSHIP`

For the two current ELMŰ conflicts, the same historical E.ON table corroborates an ÉDÁSZ row for:

- `Pilisszentkereszt`
- `Mány`

P60 does not use that historical ÉDÁSZ row to override the current ELMŰ whole-settlement authority. It also does not treat the historical E.ON table as authority to exclude ELMŰ or to infer a transfer date.

`HISTORICAL ÉDÁSZ ASSIGNMENT != CURRENT ÉDÁSZ WHOLE-SETTLEMENT MEMBERSHIP`

## Exact authority decision

For all six identities P60 preserves the already-proven current DDÁSZ or ELMŰ whole-settlement membership and blocks a second ÉDÁSZ whole-settlement promotion.

Two audit classes are used:

- four rows: `CURRENT_EDASZ_ADMIN_UNIT_VS_OTHER_DSO_WHOLE_MEMBERSHIP_CONFLICT_HISTORICAL_DUAL_EON_LICENSEE_CORROBORATED`
- two rows: `CURRENT_EDASZ_ADMIN_UNIT_VS_ELMU_WHOLE_MEMBERSHIP_CONFLICT_HISTORICAL_EDASZ_CORROBORATED`

The ÉDÁSZ admission result is uniformly:

`NO_SECOND_WHOLE_SETTLEMENT_PROMOTION`

Future ÉDÁSZ-side resolution requires:

`CURRENT_CLAIM_SPECIFIC_BOUNDARY_OR_USAGE_LOCATION_AUTHORITY`

P60 does not infer that any of the six settlements is currently split, dual-supplied at whole-settlement grain, transferred on a particular date, partly inside ÉDÁSZ today, or affected by an operator-name error.

`HISTORICAL + CURRENT SOURCE PRESENCE != CURRENT BOUNDARY AUTHORITY`

`CONFLICTING OPERATOR SURFACES != DUAL WHOLE-SETTLEMENT MEMBERSHIP`

## Exact audit set

The six-row audit is stored in:

`registry/dso_service_area_membership_edasz_p60_cross_dso_conflict_audit.csv`

Canonical row digest SHA-256 over sorted rows using all audit columns in file order:

`1643326c0f67b228b4948d64a9ccde241b9d8dbe262d52ebe2864f5320fb885b`

## P49 / P51 unresolved accounting

P60 does not alter ÉDÁSZ population counts.

ÉDÁSZ remains:

`45 historical + 769 P49 = 814 materialized current provable whole-settlement identities`

The unresolved population remains exactly:

`59 = 30 P50 spelling diagnostics + 6 P60 cross-DSO conflicts + 23 P51 residual source forms`

Occurrence accounting remains:

`60 = 30 + 6 + 24`

P60 resolves authority classification for the six conflict rows only. It does not resolve their exact current ÉDÁSZ usage-location geography.

`RESIDUAL ACCOUNTING != RESIDUAL IDENTITY RESOLUTION`

## Non-claims and B10 state

P60 does not prove complete ÉDÁSZ membership, exact current cross-DSO boundaries for these six settlements, exact usage-location membership, exact DSO nodes, complete topology, limiting nodes, headroom sufficiency, reinforcement need, reinforcement cost, programme-incremental CAPEX, or timed programme CAPEX.

The national canonical crosswalk remains header-only.

The standing blockers remain active, including:

- `NO_COMPLETE_KSH_DSO_MEMBERSHIP_CROSSWALK`
- `PARTIAL_SETTLEMENT_USAGE_LOCATION_RESOLUTION_REQUIRED`

B10 remains `IN_PROGRESS`; readiness remains **15%**.
