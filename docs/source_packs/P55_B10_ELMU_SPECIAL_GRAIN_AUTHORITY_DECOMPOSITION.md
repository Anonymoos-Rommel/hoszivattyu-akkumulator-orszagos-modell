# B10-P55 — ELMŰ SPECIAL-GRAIN AUTHORITY DECOMPOSITION

Status date: 2026-09-05

Canonical base: `1ced1bc432085c248aefc1503d6427345baae99d`

## Purpose

P55 closes the accounting ambiguity around the exact **four unresolved ELMŰ current-M1 source tokens** left fail-closed by P46.

It is a source-grain classification slice, not a membership-normalization or promotion slice.

P55 asks one narrow question:

> What exact authority class applies to each of the four P46 residual source tokens, without inventing a parent-settlement, district-collapse, suffix-stripping, or usage-location rule?

P55 adds **zero** service-area membership rows.

## Authority surface

Current DSO authority remains:

- `SRC-B10-ELMU-M1-CANDIDATE-2025`
- official ELMŰ M1 attachment:
  `https://www.eon.hu/content/dam/eon/eon-hungary/documents/pest-megyei-halozat/tarsasagunkrol/%C3%BCzletszab%C3%A1lyzatok/2025/0617/ELMu_elo_usz_melleklet_20250410.pdf`
- currentness status: `CURRENT_2026_DER_APPROVED_PACKAGE_REVISION_LINEAGE`

P55 introduces no new external identity authority. It consumes the P46 source accounting and the semantic distinctions already frozen there.

## Exact residual accounting

P46 fully accounted the 132 current M1 source tokens as:

- 43 source tokens represented by historical P22/P37 whole-settlement rows;
- 83 additional source tokens resolving directly to new exact whole-settlement identities;
- 2 composite source tokens resolved by identity-specific corroboration to 4 whole-settlement identities;
- **4 residual source tokens** intentionally unresolved at whole-settlement grain.

P55 freezes those exact four residual tokens in:

- `registry/dso_service_area_membership_elmu_p55_residual_authority_audit.csv`
- `registry/dso_service_area_membership_elmu_p55_authority_manifest.csv`

The residual set has exactly **4 unique source tokens / 4 source occurrences**.

Exact P55 audit-set SHA-256 over sorted
`source_token|source_occurrence_count|residual_class|admission_status` rows:

`0bbd9865dc9add46ee7991a5f205457e9b1c755c4be6180051a94d9ec253a384`

## 1. Budapest

Source token:

`Budapest`

P55 class:

`MULTI_DISTRICT_CITY_TOKEN`

Admission status:

`UNRESOLVED_NO_SINGLE_CANONICAL_WHOLE_SETTLEMENT_ID`

P46 already established the controlling workflow boundary:

`BUDAPEST TOKEN != ONE CANONICAL KSH WHOLE-SETTLEMENT ID`

P55 does not collapse district-grain identities, choose a synthetic whole-city KSH identifier, or infer that a city-level source token is equivalent to one canonical settlement row for the B10 crosswalk.

`CITY-LEVEL SOURCE TOKEN != AUTHORIZED SINGLE CANONICAL WHOLE-SETTLEMENT IDENTITY`

## 2. Named settlement-part tokens with parent context

Two source tokens have explicit named settlement-part plus parent context:

- `Bankháza (Kiskunlacháza)`
- `Domonyvölgy (Domony)`

P55 class:

`NAMED_SETTLEMENT_PART_WITH_PARENT_CONTEXT`

Admission status:

`UNRESOLVED_USAGE_LOCATION_AUTHORITY_REQUIRED`

The parenthetical parent name is context only. It does not establish that the whole parent settlement belongs to ELMŰ and does not resolve which usage locations inside the parent settlement are in the ELMŰ service area.

Therefore:

`NAMED SETTLEMENT PART + PARENT CONTEXT != WHOLE-PARENT MEMBERSHIP`

and:

`PARENT NAME PRESENCE != EXACT USAGE-LOCATION BOUNDARY`

P55 does not infer whole Kiskunlacháza or whole Domony membership from these source forms.

## 3. Explicit subsettlement area

Source token:

`Tass üdülőterület`

P55 class:

`EXPLICIT_SUBSETTLEMENT_AREA`

Admission status:

`UNRESOLVED_USAGE_LOCATION_AUTHORITY_REQUIRED`

The source form is explicitly narrower than whole-settlement `Tass`.

P55 therefore preserves:

`EXPLICIT SUBSETTLEMENT AREA != WHOLE-SETTLEMENT MEMBERSHIP`

The token may not be broadened by suffix stripping, semantic simplification, or parent-name substitution.

## Exact class partition

The full four-token residual set is now decomposed exactly as:

- 1 `MULTI_DISTRICT_CITY_TOKEN`;
- 2 `NAMED_SETTLEMENT_PART_WITH_PARENT_CONTEXT`;
- 1 `EXPLICIT_SUBSETTLEMENT_AREA`.

No residual token remains unclassified inside the P46 four-token set.

This is an accounting/classification completion only. It does **not** mean the underlying service-area membership problem is resolved.

`COMPLETE RESIDUAL CLASSIFICATION != COMPLETE OPERATOR MEMBERSHIP CROSSWALK`

## Boundaries preserved

P55 does not:

- add or alter service-area membership rows;
- infer whole-settlement membership from a settlement part;
- infer exact usage-location membership;
- collapse Budapest districts to one canonical settlement identity;
- strip `üdülőterület` or any other suffix;
- split or normalize arbitrary source tokens;
- perform fuzzy, accent, edit-distance, or phonetic matching;
- infer an exact DSO node;
- infer headroom, limiting-node status, reinforcement need, cost, or programme-incremental CAPEX.

The governing boundaries are:

`SOURCE-GRAIN CLASSIFICATION != MEMBERSHIP AUTHORITY`

`SOURCE FORM PRESENCE != WHOLE-SETTLEMENT IDENTITY AUTHORITY`

`USAGE-LOCATION REQUIREMENT != USAGE-LOCATION RESOLUTION`

## State impact

P55 adds **zero** service-area membership rows.

ELMŰ remains:

`43 historical + 87 P46 = 130 materialized whole-settlement identities`

The operator extraction state remains:

`PARTIAL_TRANCHE_MATERIALIZED`

The four residual source tokens remain unresolved for membership admission, but are now completely and explicitly classified by source grain.

The canonical national crosswalk remains header-only.

The standing blockers remain active, including:

- `NO_COMPLETE_KSH_DSO_MEMBERSHIP_CROSSWALK`
- `PARTIAL_SETTLEMENT_USAGE_LOCATION_RESOLUTION_REQUIRED`
- `NO_COMPLETE_NATIONAL_DSO_NODE_INVENTORY`
- `NO_REAL_PROGRAMME_NODE_PANEL`

B10 remains `IN_PROGRESS`; readiness remains **15%**.
