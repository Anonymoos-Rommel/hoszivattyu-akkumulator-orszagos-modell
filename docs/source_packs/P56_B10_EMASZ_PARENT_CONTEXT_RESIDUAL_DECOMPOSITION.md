# B10-P56 — MVM Émász parent-context residual authority decomposition

Status date: 2026-09-05

Canonical base: `892797527cc9e3d37e0725108b3e8ab69759bb67`

## Purpose

P56 closes the accounting ambiguity around the **99 parenthesized named-subsettlement / special-grain MVM Émász source tokens** left fail-closed by P47 and preserved by P52.

It is a **source-form classification slice**, not an identity-normalization, parent-settlement promotion, or usage-location resolution slice.

P56 asks one narrow question:

> What exact current-M1 source-form population constitutes the 99 P47 parent-context residual tokens, and what can be stated about their syntax without inferring membership?

The answer is:

- **99 unique source forms / 99 source occurrences**;
- **98** are well-formed `name (parent-context)` source forms;
- **1** is a source-native malformed closing-parenthesis form: `Mátraszentistván Mátraszentimre)`.

P56 adds **zero** service-area membership rows.

## Authority surface

Current DSO authority remains:

- `SRC-B10-MVM-EMASZ-M1-2026`;
- official MVM Émász M1 attachment exposed from the 2026-05-26 business-rule package;
- M1 title: `Az MVM Émász Áramhálózati Kft. területi illetékessége`;
- URL: `https://mvmemaszhalozat.hu/-/media/emaszhalozat/emasz-halozat-uzletszabalyzat-szabalyzatok/uzletszabalyzat-20260526/msz_uzletszabalyzat_melleklet_2025_i_md_2025_1022.ashx?hash=EB463FF2F46DD05995991DD2B7C06AEA4AAC0195&la=hu-hu`.

Upstream frozen surfaces:

- P47 complete current M1 accounting: 749 source tokens, including 99 parent-context residuals;
- P47 whole-settlement materialization: `45 historical + 605 P47 = 650`;
- P52 two-edge spelling-authority audit, which leaves `Fóny` / `Fony` and `Hídvégardó` / `Hidvégardó` unresolved.

P56 introduces **no new external KSH identity authority** and does not reinterpret P47 or P52.

## Exact 99-row residual surface

The exact residual set is frozen in:

`registry/dso_service_area_membership_emasz_p56_parent_context_residual_audit.csv`

Each row records only:

- the source-native token;
- source occurrence count;
- a syntax-level residual class;
- a fail-closed admission status.

The exact P56 audit-set SHA-256 over sorted
`source_token|source_occurrence_count|residual_class|admission_status` rows is:

`a8bd4942fbd3d286ce8444ce8736b358a92e71c3fc56926665da49072e19c165`

The class partition is exact:

- `98 PARENTHESIZED_PARENT_CONTEXT`
- `1 MALFORMED_PARENT_CONTEXT_TOKEN`

All 99 rows carry:

`UNRESOLVED_USAGE_LOCATION_REQUIRED`

## Parenthetical context is not membership authority

For the 98 well-formed tokens, the text inside parentheses is preserved as **source-native contextual text only**.

P56 does not claim that the parenthetical value proves:

- whole-parent settlement coverage;
- the named source form is a legally defined settlement part;
- the named source form has a particular KSH identifier;
- every usage location inside the named source form belongs to MVM Émász;
- every usage location in the parent settlement belongs to MVM Émász;
- an exact distribution node or feeder assignment.

The governing boundaries are:

`PARENTHESIZED PARENT CONTEXT != WHOLE-PARENT MEMBERSHIP`

`SOURCE-NATIVE PARENT CONTEXT != KSH IDENTITY AUTHORITY`

`SOURCE-FORM PRESENCE != USAGE-LOCATION RESOLUTION`

## Malformed source-native token

The current M1 source surface contains one malformed residual form:

`Mátraszentistván Mátraszentimre)`

P56 preserves that token **verbatim**.

It does not silently repair it to a parenthesized form, insert punctuation, split the token, or infer the intended parent identity.

`MALFORMED SOURCE TOKEN != AUTHORITY TO REPAIR OR NORMALIZE`

A future correction requires explicit source or identity authority specific to that token.

## No generalized parser or normalization rule

P56 does not:

- strip parentheses;
- promote parenthetical text into a canonical settlement field;
- infer a parent/child administrative relationship;
- split compound or malformed labels;
- repair punctuation;
- perform fuzzy, accent, edit-distance, or phonetic matching;
- infer old-to-current settlement-name continuity;
- infer usage-location coverage from locality context;
- infer exact DSO node identity.

The classification exists only to route future evidence work.

`SOURCE-GRAIN CLASSIFICATION != MEMBERSHIP AUTHORITY`

## State impact

P56 adds **zero** service-area membership rows.

MVM Émász remains:

`45 historical + 605 P47 = 650 materialized current provable whole-settlement identities`

The two P52 spelling edges remain unresolved and separate from this 99-token source-grain population.

The operator extraction state remains:

`PARTIAL_TRANCHE_MATERIALIZED`

The canonical national crosswalk remains header-only.

The standing blockers remain active, including:

- `NO_COMPLETE_KSH_DSO_MEMBERSHIP_CROSSWALK`
- `PARTIAL_SETTLEMENT_USAGE_LOCATION_RESOLUTION_REQUIRED`
- `NO_COMPLETE_NATIONAL_DSO_NODE_INVENTORY`
- `NO_REAL_PROGRAMME_NODE_PANEL`

P56 does not prove node identity, headroom, limiting-node status, reinforcement requirement, reinforcement cost, programme-incremental CAPEX, or timing.

`COMPLETE RESIDUAL SOURCE-FORM CLASSIFICATION != COMPLETE OPERATOR MEMBERSHIP CROSSWALK`

B10 remains `IN_PROGRESS`; readiness remains **15%**.
