# B10-P50 — ÉDÁSZ SPELLING-EQUIVALENCE AUTHORITY AUDIT

Status date: 2026-09-05

Canonical base: `52c281a1a93a9f22a615ddae2ec14fb918b19c58`

## Purpose

P50 is a fail-closed authority-audit slice following the P49 completion-first materialization.

P49 left exactly 30 source-native spelling diagnostics outside whole-settlement promotion because a current ÉDÁSZ M1 source token that resembles a KSH locality name is not, by itself, authority to equate the two identities.

P50 asks one narrow question:

> Does an earlier official E.ON Észak-dunántúli M1 territorial-jurisdiction attachment independently resolve any of those 30 current spelling edges?

The answer is **no** for the audited historical authority.

## Authorities inspected

Current authority retained from P49:

- `SRC-B10-EON-EDASZ-M1-CANDIDATE-2025`
- official ÉDÁSZ M1 revision `20241209`
- URL: `https://www.eon.hu/content/dam/eon/eon-hungary/documents/hatarozatok-szabalyzatok-aram/EED/2025/EED_elo_usz_melleklet_20241209%20%28v1%29.pdf`

Historical comparison authority:

- official E.ON Észak-dunántúli Elosztói Üzletszabályzat M1 attachment dated 2017-03-02
- URL: `https://www.eon.hu/content/dam/eon/eon-hungary/documents/hatarozatok-szabalyzatok-aram/EED-elosztoi-uzletszabalyzat/EED_elo_usz_mell__3196_2017.pdf`

Diagnostic identity surface retained from P49:

- official KSH settlement identities already frozen by the P49 30-edge regression set.

The historical M1 is used **only as an audit comparison source**. It is not currentness authority and it does not supersede the current 20241209 M1.

## Audit result

The exact 30 P49 spelling diagnostics are materialized in:

`registry/dso_service_area_membership_edasz_p50_spelling_authority_audit.csv`

For every row:

- the current 20241209 source token differs from the diagnostic KSH locality name;
- the historical 2017 ÉDÁSZ M1 repeats the same source-native variant;
- therefore the historical document supplies no independent canonical-name bridge;
- the row remains `UNRESOLVED_NO_EQUIVALENCE_AUTHORITY`.

Examples:

- `Dőr` remains `Dőr`, not KSH `Dör`;
- `Felcsut` remains `Felcsut`, not KSH `Felcsút`;
- `Gönyü` remains `Gönyü`, not KSH `Gönyű`;
- `Kemeneshögyész` remains `Kemeneshögyész`, not KSH `Kemeneshőgyész`;
- `Nyögér` remains `Nyögér`, not KSH `Nyőgér`;
- `Sotony` remains `Sotony`, not KSH `Sótony`;
- `Úrkut` remains `Úrkut`, not KSH `Úrkút`;
- `Zalalővő` remains `Zalalővő`, not KSH `Zalalövő`.

Exact audit-set SHA-256 over sorted
`source_token|diagnostic_ksh_code|diagnostic_ksh_name|historical_comparison_status|admission_status` rows:

`d99b1835dbe625b6524447a1d1642fe2aaf915fe0c1ea988c2ce8e0da2acb206`

## Fail-closed rule

`HISTORICAL REPETITION OF THE SAME SOURCE VARIANT != INDEPENDENT IDENTITY-EQUIVALENCE AUTHORITY`

and therefore:

`SOURCE SPELLING DIFFERENCE != AUTHORIZED IDENTITY EQUIVALENCE`

P50 deliberately does **not** introduce:

- accent folding;
- edit-distance matching;
- phonetic matching;
- typo correction;
- Hungarian orthographic normalization;
- historical-to-current automatic canonicalization;
- a generic rule that one unique KSH near-match proves identity.

Any future promotion of one of these 30 rows requires an identity-specific authority that independently binds the current ÉDÁSZ source form to the canonical KSH locality identity.

## State impact

P50 adds **zero** new service-area membership rows.

The P49 materialized ÉDÁSZ whole-settlement population remains exactly:

`45 historical + 769 P49 = 814`

The 30 spelling diagnostics remain outside that membership population.

The complete unresolved ÉDÁSZ unique-token count remains **59** because P50 is an authority audit, not a promotion slice.

The six P49 cross-DSO conflicts remain excluded, mixed/special-grain records remain fail-closed, and duplicated `Séska` still does not create a second locality identity.

The national canonical crosswalk remains header-only.

## Non-claims

P50 does not prove:

- complete ÉDÁSZ operator membership;
- complete national KSH-to-DSO membership;
- mixed/special-grain usage-location resolution;
- exact DSO node identity;
- topology, headroom, limiting node, reinforcement, cost, or programme-incremental CAPEX.

B10 remains `IN_PROGRESS`; readiness remains **15%**.
