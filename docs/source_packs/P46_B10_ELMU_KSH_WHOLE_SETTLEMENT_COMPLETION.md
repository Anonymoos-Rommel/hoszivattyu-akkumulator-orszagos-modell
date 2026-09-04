# B10-P46 — ELMŰ / KSH whole-settlement completion

Status date: 2026-09-04

Canonical base: `76b674e28f9736736b3c686517ba47fc111d70df`

## Purpose

P46 is a **completion-first evidence/data slice**, not a new semantic gate.

It finishes every current ELMŰ M1 membership that can be proven at canonical KSH whole-settlement grain without inventing a general name-normalization, delimiter-splitting, fuzzy-match, district-collapse, or settlement-part promotion rule.

The existing P22/P37 ELMŰ materialization remains unchanged. P46 uses a dedicated append-only completion surface:

`registry/dso_service_area_membership_crosswalk_elmu_p46.csv`

## Core boundaries

`SETTLEMENT NAME != KSH SETTLEMENT ID`

`WHOLE SETTLEMENT != NAMED SUBSETTLEMENT OR SETTLEMENT PART`

`IDENTITY-SPECIFIC TOKEN RESOLUTION != GENERAL SPLIT OR FUZZY RULE`

`BUDAPEST TOKEN != ONE CANONICAL KSH WHOLE-SETTLEMENT ID`

`DSO SERVICE-AREA MEMBERSHIP != EXACT DSO NODE`

`DER CURRENTNESS EDGE CAPS CURRENT MEMBERSHIP AT DER`

`COMPLETE PROVABLE WHOLE-SETTLEMENT MATERIALIZATION != COMPLETE OPERATOR MEMBERSHIP CROSSWALK`

`PUBLIC FACT USE != SOURCE-DOCUMENT REPUBLICATION != BULK DATABASE RECONSTRUCTION`

## 1. Current ELMŰ M1 authority

P46 reuses the P22 authority chain:

`SRC-B10-ELMU-M1-CANDIDATE-2025`

Official ELMŰ M1 attachment:

`https://www.eon.hu/content/dam/eon/eon-hungary/documents/pest-megyei-halozat/tarsasagunkrol/%C3%BCzletszab%C3%A1lyzatok/2025/0617/ELMu_elo_usz_melleklet_20250410.pdf`

P22 already established its current 2026 use at:

`CURRENT_2026_DER_APPROVED_PACKAGE_REVISION_LINEAGE`

P46 does not upgrade that currentness edge to OBS. Every P46 membership therefore remains `DER`.

The current M1 list contains **132 comma-delimited source tokens**. P46 accounts for the complete current source list rather than stopping after another arbitrary bounded tranche.

## 2. KSH identity authority

Primary current locator:

`SRC-B10-KSH-HNT-2025-SETTLEMENT-IDS`

Machine-readable helper:

`SRC-B10-KSH-HNT-2025-IRSZHNK-DERIVATION-2026`

For ordinary exact-name rows P46 requires one exact current KSH name/code identity through that existing locator chain.

Two identities deliberately bypass the helper's empty-`Településrész` rule and use direct official KSH 2019 identity instead:

- Göd — `23649`;
- Tahitótfalu — `31963`.

For both, the official KSH 2019 gazetteer directly publishes the whole-settlement identity. This does not create a general exception for settlement-part rows.

## 3. Identity-specific ELMŰ token resolution

The current M1 contains two source tokens that each visibly contain two municipality names:

- `Üröm és Visegrád`;
- `Verőce Zebegény`.

P46 resolves only these two exact tokens, producing the four exact KSH whole settlements:

- Üröm — `11934`;
- Visegrád — `28413`;
- Verőce — `33729`;
- Zebegény — `14960`.

This is corroborated by the separate official ELMŰ településlista, which lists all four names independently:

`https://www.eon.hu/content/dam/eon/eon-hungary/documents/pest-megyei-halozat/Telepuleslista_A4_02.pdf`

That supplemental list is used only as identity-specific corroboration. It is **not** used to establish currentness, to override the current M1, or to authorize a general delimiter/parser rule.

In particular, the older list cannot broaden the current `Tass üdülőterület` token into whole-settlement `Tass` membership.

## 4. Exact source accounting

The 132 current M1 source tokens are fully accounted as follows:

- 43 source tokens already represented by the historical P22/P37 ELMŰ rows;
- 83 additional source tokens resolve directly to new exact whole-settlement identities;
- 2 composite source tokens are resolved, by the narrow evidence above, to 4 additional whole-settlement identities;
- 4 source tokens remain intentionally unresolved at whole-settlement grain.

Therefore P46 adds exactly **87** new DER whole-settlement rows.

Current materialized ELMŰ whole-settlement state after P46:

**43 historical + 87 P46 = 130 materialized whole-settlement identities.**

The exact 87-pair set is regression-frozen by canonical `code|name` SHA-256:

`4c4f4159b8546b6517230c07276a44a755064813a7aca6368f1f8c94125707e3`

## 5. Four fail-closed source cases

P46 does not promote these four current M1 tokens:

1. `Budapest`
   - the KSH identity surface is district-grain rather than one canonical whole-settlement row for this workflow;
2. `Bankháza (Kiskunlacháza)`
   - named settlement-part context, not whole Kiskunlacháza authority;
3. `Domonyvölgy (Domony)`
   - named settlement-part context, not whole Domony authority;
4. `Tass üdülőterület`
   - explicitly narrower than whole-settlement Tass.

Their absence is not zero, not negative evidence, and not permission to infer the parent whole settlement.

Because these mixed/special-grain cases remain unresolved, the ELMŰ source registry deliberately remains:

`PARTIAL_TRANCHE_MATERIALIZED`

P46 therefore does **not** claim `COMPLETE_OPERATOR_M1_MATERIALIZED`.

## 6. Non-claims and closure state

P46 does not prove:

- complete national KSH-to-DSO membership;
- usage-location resolution for mixed/partial settlement cases;
- exact DSO node identity;
- node topology or feeder/substation assignment;
- headroom sufficiency;
- limiting-node status;
- reinforcement requirement or cost;
- programme-incremental CAPEX.

The canonical national crosswalk remains header-only.

The blockers remain active, including:

- `NO_COMPLETE_KSH_DSO_MEMBERSHIP_CROSSWALK`;
- `PARTIAL_SETTLEMENT_USAGE_LOCATION_RESOLUTION_REQUIRED`;
- `NO_COMPLETE_NATIONAL_DSO_NODE_INVENTORY`;
- `NO_REAL_PROGRAMME_NODE_PANEL`.

B10 remains `IN_PROGRESS`; readiness remains **15%**.
