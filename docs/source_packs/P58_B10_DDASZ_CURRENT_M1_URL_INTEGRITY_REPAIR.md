# B10-P58 — DDÁSZ current M1 authority URL integrity repair

Status date: 2026-09-05

Canonical base: `374592ec7128946b53d814d0ee6c4ac840f95eed`

## Purpose

P58 is a narrow evidence-integrity repair for the DDÁSZ current M1 authority lineage used by P53.

P53 correctly preserved the fail-closed spelling-equivalence result, but its authority manifest contained a path-identity typo in `current_source_url`:

`.../EDD/2025/EDD_elo_usz_melleklet_20241209%20%28v1%29.pdf`

The canonical DDÁSZ current M1 authority already used elsewhere in B10 is:

`https://www.eon.hu/content/dam/eon/eon-hungary/documents/hatarozatok-szabalyzatok-aram/EDE/2025/EDE_elo_usz_melleklet_20241209%20%28v1%29.pdf`

P58 repairs only that source-lineage inconsistency.

## Canonical authority basis

The exact repaired URL is already the DDÁSZ current M1 source URL in:

- `registry/dso_service_area_membership_sources.csv`, source id `SRC-B10-EON-DDASZ-M1-CANDIDATE-2025`;
- `registry/dso_service_area_crosswalk_authorities.csv`;
- `docs/source_packs/P22_B10_EON_CURRENT_M1_AUTHORITY_RESOLUTION.md`;
- `docs/source_packs/P38_B10_DDASZ_KSH_CROSSWALK_EXPANSION.md`.

Therefore P58 does not introduce a new source, new authority, new revision, or new currentness claim.

`P53 SOURCE-URL TYPO REPAIR != NEW DDÁSZ AUTHORITY`

`SOURCE-LINEAGE CONSISTENCY REPAIR != IDENTITY-EQUIVALENCE AUTHORITY`

## P53 semantic result is unchanged

P53 remains an audit of the exact fourteen P48 DDÁSZ source-spelling edges.

Its result remains:

- 4 historical canonical-form DDÁSZ corroborations;
- 10 historical repetitions of the current source variant;
- 0 current source-form identity equivalence authorizations;
- 0 service-area membership promotions.

The P53 authority semantics therefore remain:

`HISTORICAL_COMPARISON_ONLY`

and:

`MIXED_4_CANONICAL_CORROBORATIONS_10_VARIANT_REPETITIONS_NO_CURRENT_EQUIVALENCE`

The historical comparison source remains historical-only and cannot bind a current M1 source variant to a KSH identity.

## Exact repair

P58 changes exactly two pre-existing P53 artifacts:

1. `registry/dso_service_area_membership_ddasz_p53_authority_manifest.csv`
   - replaces the incorrect `EDD/.../EDD_...` current source URL with the canonical `EDE/.../EDE_...` DDÁSZ M1 URL;
2. `tests/test_b10_p53_ddasz_spelling_authority_audit.py`
   - replaces the old `EDD_elo_usz_melleklet_20241209` substring expectation with exact equality to the canonical DDÁSZ current M1 URL.

P58 additionally adds a dedicated regression test that requires the P53 manifest URL to equal the canonical DDÁSZ source-registry URL exactly and rejects the stale `EDD` path identity.

## State preserved

P58 does not change:

- P48 DDÁSZ materialization: `43 historical + 777 P48 = 820` materialized current provable whole-settlement identities;
- P48 residual accounting: `296` unresolved source tokens;
- P53 spelling-edge accounting: `14` unresolved spelling diagnostics;
- P54 accounting: `296 = 14 spelling diagnostics + 2 cross-DSO conflicts + 280 other unresolved source tokens`;
- any KSH identity;
- any DSO membership row;
- any currentness classification;
- the national canonical crosswalk;
- any node/headroom/reinforcement/CAPEX claim.

P58 adds **zero** service-area membership rows.

The standing blockers remain active, including:

- `NO_COMPLETE_KSH_DSO_MEMBERSHIP_CROSSWALK`;
- `PARTIAL_SETTLEMENT_USAGE_LOCATION_RESOLUTION_REQUIRED`.

B10 remains `IN_PROGRESS` and readiness remains **15%**.

## Regression boundary

After P58:

`P53 CURRENT SOURCE URL == CANONICAL DDÁSZ CURRENT M1 SOURCE URL`

must hold exactly.

The regression gate also freezes:

`EDD PATH IDENTITY != DDÁSZ CURRENT M1 CANONICAL SOURCE IDENTITY`

without deriving any additional substantive evidence from the URL correction itself.
