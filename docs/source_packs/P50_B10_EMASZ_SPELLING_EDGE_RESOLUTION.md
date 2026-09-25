# B10-P50 — MVM Émász identity-specific spelling-edge resolution

Status date: 2026-09-05

Canonical base: `52c281a1a93a9f22a615ddae2ec14fb918b19c58`

## Purpose

P50 resolves exactly the two MVM Émász whole-settlement spelling edges that P47 deliberately left fail-closed. It does not create a fuzzy-name rule, accent-normalization rule, parent-settlement rule, or named-subsettlement promotion rule.

## Locked boundaries

`SOURCE SPELLING DIFFERENCE != AUTHORIZED IDENTITY EQUIVALENCE`

`IDENTITY-SPECIFIC OFFICIAL KSH-CODE BRIDGE != GENERAL ACCENT NORMALIZATION`

`COMPLETE PROVABLE WHOLE-SETTLEMENT MATERIALIZATION != COMPLETE OPERATOR MEMBERSHIP CROSSWALK`

`WHOLE SETTLEMENT != NAMED SUBSETTLEMENT OR SETTLEMENT PART`

`DSO SERVICE-AREA MEMBERSHIP != EXACT DSO NODE`

## Upstream state

P47 accounts for 749 current MVM Émász M1 source tokens. It materializes 650 whole-settlement identities and leaves exactly two potential whole-settlement spelling edges unresolved:

- MVM `Fóny` versus KSH `Fony` (`17932`);
- MVM `Hídvégardó` versus KSH `Hidvégardó` (`25672`).

P47 also leaves 99 parenthesized named-subsettlement / special-grain tokens outside whole-settlement promotion.

## Identity authority chain

### Current DSO territorial authority

`SRC-B10-MVM-EMASZ-M1-2026`

The current MVM Émász M1 lists the source-native forms `Fóny` and `Hídvégardó`.

### Current/immutable KSH identity authority

`SRC-B10-KSH-HNK-2019-SETTLEMENT-IDS`

The official KSH gazetteer publishes the five-digit settlement identifiers:

- `17932` — `Fony`;
- `25672` — `Hidvégardó`.

The registered KSH identity contract also records the current TSZJ rule that the settlement identifier is immutable from creation until dissolution and is not reassigned.

### Official historical code bridge

Official Magyar Közlöny / Nemzeti Jogszabálytár source:

`https://njt.jog.gov.hu/document/d9/d9f220055320000041_13.PDF`

The official table publishes:

- `FÓNY` with KSH code `0517932`;
- `HÍDVÉGARDÓ` with KSH code `0525672`.

The five-digit settlement-identifier suffixes are therefore exactly `17932` and `25672`, matching the immutable KSH identities above. This is evidence for these two identities only.

## P50 materialization

P50 adds exactly two DER whole-settlement identities:

- source token `Fóny` → KSH `Fony` (`17932`);
- source token `Hídvégardó` → KSH `Hidvégardó` (`25672`).

Exact P50 pair-set SHA-256:

`64ac0eb08ac5ff5833a5ad86f4fecdadd3e7382664543349f46109a280aea9e4`

Therefore:

**650 pre-P50 materialized MVM Émász whole-settlement identities + 2 P50 = 652 materialized whole-settlement identities.**

This closes the complete provable whole-settlement identity layer identified by P47. It does **not** close the operator membership crosswalk because the 99 named/special-grain M1 tokens remain usage-location / grain gated.

## Storage

- `registry/dso_service_area_membership_emasz_p50_pairs.csv` stores the exact two canonical KSH code/name pairs;
- `registry/dso_service_area_membership_emasz_p50_identity_bridges.csv` stores the two source-native forms and their official historical KSH-code bridges;
- `registry/dso_service_area_membership_emasz_p50_manifest.csv` binds the two rows to MVM Émász whole-settlement DER semantics.

## Non-claims

P50 does not prove:

- membership for any of the 99 parenthesized named-subsettlement / special-grain tokens;
- complete MVM Émász operator membership crosswalk;
- complete national KSH-to-DSO membership crosswalk;
- exact DSO node identity;
- topology or limiting-node status;
- headroom sufficiency;
- reinforcement requirement or cost;
- programme-incremental CAPEX.

The canonical national crosswalk remains header-only. `NO_COMPLETE_KSH_DSO_MEMBERSHIP_CROSSWALK` and `PARTIAL_SETTLEMENT_USAGE_LOCATION_RESOLUTION_REQUIRED` remain active. B10 remains `IN_PROGRESS`; readiness remains **15%**.
