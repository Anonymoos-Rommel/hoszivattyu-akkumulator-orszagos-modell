# B10-P59 — DDÁSZ remaining residual source-grain decomposition

## Purpose

P59 freezes the exact remaining DDÁSZ residual source-form population after the P48 whole-settlement materialization, P53 spelling-authority audit, and P54 cross-DSO conflict audit.

This slice is classification-only. It does not create DSO service-area membership.

## Current authority

Operator: `EON_DDASZ`

Source: `SRC-B10-EON-DDASZ-M1-CANDIDATE-2025`

Official current M1 attachment:

`https://www.eon.hu/content/dam/eon/eon-hungary/documents/hatarozatok-szabalyzatok-aram/EDE/2025/EDE_elo_usz_melleklet_20241209%20%28v1%29.pdf`

P58 already locks this exact URL to the canonical DDÁSZ source registry.

## Reproducible residual reconstruction

The historical P48 locator probe at head
`9f7540c84eb1508427168ccb593cb88b5c121624`, workflow run
`33903341019`, reported:

- 1116 source tokens;
- 1116 unique source tokens;
- 299 unique unresolved source forms at that probe stage.

Five of those 299 source forms were subsequently admitted by bounded P48 exception paths:

- `Gödre`;
- `Zalakomár`;
- the parser-artifact forms leading to `Husztót`, `Pogányszentpéter`, and `Szaporca`.

P53 separately freezes 14 spelling-equivalence diagnostics. Therefore the residual source-form population addressed by P59 is:

`299 - 5 - 14 = 280`

The two P54 cross-DSO conflicts, `Dusnok` and `Mélykút`, were exact KSH-match admission conflicts and were not members of the probe's 299 unresolved-form set. They are therefore not subtracted from 299 a second time.

The P54 operator-level accounting remains exactly:

`296 = 14 spelling diagnostics + 2 cross-DSO conflicts + 280 P59 other unresolved source forms`

## Source-form classes

P59 uses lexical source-form shape only. It creates no geographic interpretation.

### `EXPLICIT_DELIMITED_MULTI_COMPONENT_SOURCE_FORM`

The source form contains an explicit delimiter-like hyphen pattern: whitespace-hyphen-whitespace or hyphen followed by whitespace.

Count: **86**.

Examples include `Bakóca - Felsőkövesd`, `Báta- Furkótelep`, and `Szentlászló - Szentegyed - Riticspuszta`.

### `COMPACT_HYPHENATED_SOURCE_FORM`

The source form contains a hyphen but does not satisfy the explicit delimiter-like syntax above.

Count: **7**.

The exact compact set is:

- `Cserkút-szőlőhegy`
- `Dióspuszta-Hitmes-Zalasor`
- `Gyapa-puszta`
- `Pécs-Szikuti d.`
- `Pécs-Vasas`
- `Söjtör-barátipuszta`
- `Söjtör-Szénásvölgy`

### `STANDALONE_NONEXACT_SOURCE_FORM`

The source form contains no hyphen. `STANDALONE` describes only the lexical shape of the source token; it does not claim that the token is a current whole settlement.

Count: **187**.

The three classes reconcile exactly:

`86 + 7 + 187 = 280`

## Authority status

All 280 forms remain:

`UNRESOLVED_AUTHORITY_REQUIRED`

Required future authority:

`IDENTITY_GRAIN_OR_USAGE_LOCATION_AUTHORITY`

P59 does not decide whether an individual source form denotes a settlement part, historical name, estate, major, puszta, district, bathing area, locality, compound administrative expression, source spelling defect, or another source-native grain. Such decisions require claim-specific evidence rather than lexical inference.

## Frozen boundaries

`SOURCE-FORM SYNTAX != SETTLEMENT-PART SEMANTICS`

`DELIMITER PRESENCE != PARENT-CHILD AUTHORITY`

`COMPACT HYPHEN != AUTHORITY TO SPLIT A SOURCE TOKEN`

`STANDALONE SOURCE FORM != WHOLE-SETTLEMENT IDENTITY`

`SOURCE-GRAIN CLASSIFICATION != MEMBERSHIP AUTHORITY`

`COMPLETE RESIDUAL FORM CLASSIFICATION != COMPLETE OPERATOR MEMBERSHIP CROSSWALK`

Accordingly P59 performs no compound splitting, suffix stripping, punctuation repair, accent/fuzzy normalization, edit-distance matching, parent inference, KSH-code assignment, whole-settlement promotion, or usage-location resolution.

## State impact

P59 adds **zero service-area membership rows**.

DDÁSZ remains:

`43 historical + 777 P48 = 820 materialized current provable whole-settlement identities`

The operator remains `PARTIAL_TRANCHE_MATERIALIZED`.

The canonical national KSH-to-DSO crosswalk remains header-only. `NO_COMPLETE_KSH_DSO_MEMBERSHIP_CROSSWALK` and `PARTIAL_SETTLEMENT_USAGE_LOCATION_RESOLUTION_REQUIRED` remain active.

B10 remains `IN_PROGRESS`; readiness remains **15%**.
