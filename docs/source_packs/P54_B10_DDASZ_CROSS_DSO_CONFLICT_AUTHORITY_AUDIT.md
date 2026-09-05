# B10-P54 — E.ON DDÁSZ cross-DSO conflict authority audit

Status date: 2026-09-05

Canonical base: `9dcf020fa33fbea41b97200b60bdfb3c34beeaaa`

## Purpose

P54 is a fail-closed authority-audit slice over the exact two cross-DSO whole-settlement conflicts excluded by P48 for E.ON Dél-dunántúli Áramhálózati Zrt.:

- `04109 Dusnok`
- `16018 Mélykút`

P54 does not add service-area membership rows. It sharpens the authority boundary between current DDÁSZ administrative-unit presence, current MVM Démász whole-settlement authority, and historical E.ON network-licensee corroboration.

## Current DDÁSZ authority

P48 remains the current DDÁSZ source path through `SRC-B10-EON-DDASZ-M1-CANDIDATE-2025`, approved-package M1 revision `20241209`.

The official M1 is titled `E.ON DÉL-DUNÁNTÚLI ÁRAMHÁLÓZATI ZRT. TERÜLETI ILLETÉKESSÉGE` and contains both `Dusnok` and `Mélykút` as source tokens.

P48 already freezes the source semantics as `ADMINISTRATIVE_UNITS_IN_M1`. Exact name presence therefore does not itself prove a second whole-settlement DSO membership.

`CURRENT DDÁSZ M1 ADMINISTRATIVE-UNIT PRESENCE != CURRENT DDÁSZ WHOLE-SETTLEMENT MEMBERSHIP`

## Current MVM Démász authority

`SRC-B10-MVM-DEMASZ-SERVICE-AREA-2026` is the current operator publication used by P45. It separates:

- 256 settlements wholly inside the MVM Démász service area; and
- 20 settlements partly inside the service area.

Both P54 identities are already on the proven whole-settlement MVM Démász surface:

- `04109 Dusnok` is present in the historical materialization tranche as `WHOLE_SETTLEMENT_MEMBERSHIP_PROVEN`;
- `16018 Mélykút` is present in the P45 completion tranche as `WHOLE_SETTLEMENT_MEMBERSHIP_PROVEN`.

P54 does not weaken or duplicate those current whole-settlement decisions.

## Historical E.ON corroboration

P54 reuses the official E.ON-hosted 2022 E.ON Áramszolgáltató 5th appendix introduced for comparison in P53:

`https://www.eon.hu/content/dam/eon/eon-hungary/documents/hatarozatok-szabalyzatok-aram/eas/2022/EON_Aramszolg_egyetemes_USZ_fugg_mell_korrekturazott_tervezet.pdf`

The appendix is a `Település | Hálózati engedélyes | Megye` table.

It assigns both:

- `Dusnok` → `E.ON Dél-dunántúli Áramhálózati Zrt.`
- `Mélykút` → `E.ON Dél-dunántúli Áramhálózati Zrt.`

This is useful historical network-licensee corroboration, but it is not current 2026 authority and it does not establish the effective date or geometry of any later territorial change, split, or usage-location boundary.

`HISTORICAL DDÁSZ NETWORK-LICENSEE ASSIGNMENT != CURRENT DDÁSZ WHOLE-SETTLEMENT MEMBERSHIP`

## Exact authority decision

For both identities P54 preserves the current MVM Démász whole-settlement membership and blocks a second DDÁSZ whole-settlement promotion.

The exact conflict class is:

`CURRENT_ADMIN_UNIT_VS_WHOLE_MEMBERSHIP_CONFLICT_HISTORICAL_DDASZ_CORROBORATED`

The DDÁSZ admission result is:

`NO_SECOND_WHOLE_SETTLEMENT_PROMOTION`

Future DDÁSZ-side resolution requires claim-specific current authority such as an effective territorial/boundary publication or exact usage-location service-area authority.

P54 does **not** infer that either settlement is:

- currently split between the two DSOs;
- dual-supplied at whole-settlement grain;
- transferred on a particular date;
- partly inside DDÁSZ today;
- an operator-name or source-name error.

`HISTORICAL + CURRENT SOURCE PRESENCE != CURRENT BOUNDARY AUTHORITY`

`CONFLICTING OPERATOR SURFACES != DUAL WHOLE-SETTLEMENT MEMBERSHIP`

## Exact audit set

The two-row audit is stored in:

`registry/dso_service_area_membership_ddasz_p54_cross_dso_conflict_audit.csv`

Canonical row digest SHA-256:

`e6b1bb101d87390a17e0d6c30527dc0ae07edb528993e5a86731f3b983fa0be6`

## P48 residual accounting

P54 does not alter P48 population counts.

DDÁSZ remains:

`43 historical + 777 P48 = 820 materialized current provable whole-settlement identities`

The **296** P48 residual source tokens now have the following explicit accounting boundary:

`296 = 14 spelling diagnostics + 2 cross-DSO conflicts + 280 other unresolved source tokens`

P53 audited the 14 spelling diagnostics. P54 audits the exact 2 cross-DSO conflicts. The remaining 280 source tokens are not classified further by P54 and remain fail-closed.

`RESIDUAL ACCOUNTING != RESIDUAL IDENTITY RESOLUTION`

## Non-claims and B10 state

P54 does not prove complete DDÁSZ membership, current DDÁSZ partial-settlement boundaries for Dusnok or Mélykút, exact usage-location membership, exact DSO nodes, complete topology, limiting nodes, headroom sufficiency, reinforcement need, reinforcement cost, programme-incremental CAPEX, or timed programme CAPEX.

The national canonical crosswalk remains header-only.

The standing blockers remain active, including:

- `NO_COMPLETE_KSH_DSO_MEMBERSHIP_CROSSWALK`
- `PARTIAL_SETTLEMENT_USAGE_LOCATION_RESOLUTION_REQUIRED`

B10 remains `IN_PROGRESS` and readiness remains **15%**.
