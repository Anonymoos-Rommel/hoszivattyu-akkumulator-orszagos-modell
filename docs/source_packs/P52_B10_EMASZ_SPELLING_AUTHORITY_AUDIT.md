# B10-P52 — MVM Émász spelling-equivalence authority audit

Status date: 2026-09-05

Canonical base: `aaf4500e1c5dc39872b70c38660d6320bbf43bb7`

## Purpose

P52 is a fail-closed authority-audit slice following P47 and the P50/P51 ÉDÁSZ authority-decomposition work.

P47 left exactly two potential MVM Émász whole-settlement identities outside materialization solely because the current M1 source-native forms differ from the current KSH locality names:

- `Fóny` versus KSH `Fony` (`17932`);
- `Hídvégardó` versus KSH `Hidvégardó` (`25672`).

P52 asks one narrow question:

> Does an earlier official MVM Émász M1 territorial-jurisdiction attachment independently resolve either of those two spelling edges?

The answer is **no** for the audited historical authority.

## Authorities inspected

Current authority retained from P47:

- `SRC-B10-MVM-EMASZ-M1-2026`
- official current MVM Émász M1 exposed from the 2026-05-26 business-rule package
- URL: `https://mvmemaszhalozat.hu/-/media/emaszhalozat/emasz-halozat-uzletszabalyzat-szabalyzatok/uzletszabalyzat-20260526/msz_uzletszabalyzat_melleklet_2025_i_md_2025_1022.ashx?hash=EB463FF2F46DD05995991DD2B7C06AEA4AAC0195&la=hu-hu`

Historical comparison authority:

- official MVM Émász Elosztói üzletszabályzat M1 attachment published under the 2022-12-21 package
- URL: `https://mvmemaszhalozat.hu/-/media/emaszhalozat/emasz-halozat-uzletszabalyzat-szabalyzatok/uzletszabalyzat-20221221/emaszuzletszabalyzatmelleklet2022-i-mod20221221.ashx?hash=F39A9AA489F5CD51BA2EE04B90C99AE463ED90AC&la=hu-hu`

Diagnostic KSH identity authority remains the exact P47 KSH surface:

- `SRC-B10-KSH-HNT-2025-SETTLEMENT-IDS`
- `SRC-B10-KSH-HNT-2025-IRSZHNK-DERIVATION-2026`

The historical M1 is used **only as audit comparison authority**. It is not currentness authority and does not supersede the current M1.

## Audit result

The exact two P47 spelling diagnostics are materialized in:

`registry/dso_service_area_membership_emasz_p52_spelling_authority_audit.csv`

For both rows:

- the current MVM Émász M1 source token differs from the diagnostic KSH locality name;
- the official 2022-12-21 historical MVM Émász M1 repeats the same source-native variant;
- therefore the historical document supplies no independent canonical-name bridge;
- the row remains `UNRESOLVED_NO_EQUIVALENCE_AUTHORITY`.

Specifically:

| current / historical MVM Émász form | diagnostic KSH identity | result |
| --- | --- | --- |
| `Fóny` | `17932 Fony` | unresolved |
| `Hídvégardó` | `25672 Hidvégardó` | unresolved |

Exact audit-set SHA-256 over sorted
`source_token|diagnostic_ksh_code|diagnostic_ksh_name|historical_comparison_status|admission_status` rows:

`9f68e7eb5c915be7e355ac6384414a00d80e41078fbe067ae92a983ff9979769`

## Fail-closed rule

`HISTORICAL REPETITION OF THE SAME SOURCE VARIANT != INDEPENDENT IDENTITY-EQUIVALENCE AUTHORITY`

and therefore:

`SOURCE SPELLING DIFFERENCE != AUTHORIZED IDENTITY EQUIVALENCE`

P52 deliberately does **not** introduce:

- accent folding;
- edit-distance matching;
- phonetic matching;
- typo correction;
- Hungarian orthographic normalization;
- historical-to-current automatic canonicalization;
- a rule that one unique KSH near-match proves identity.

Any future promotion of either row requires an identity-specific authority that independently binds the MVM Émász source form to the canonical KSH locality identity.

## State impact

P52 adds **zero** new service-area membership rows.

The P47 materialized MVM Émász whole-settlement population remains exactly:

`45 historical + 605 P47 = 650`

The potential whole-settlement layer remains 652, with exactly these two spelling edges outside materialization.

The 99 parenthesized named-subsettlement / special-grain M1 tokens remain a separate usage-location problem and are not altered by P52.

The canonical national crosswalk remains header-only.

## Non-claims

P52 does not prove:

- complete MVM Émász operator membership;
- usage-location membership for the 99 named settlement parts;
- complete national KSH-to-DSO membership;
- exact DSO node identity;
- topology, headroom, limiting node, reinforcement, cost, programme-incremental CAPEX, or timed programme-incremental CAPEX.

B10 remains `IN_PROGRESS`; readiness remains **15%**.
