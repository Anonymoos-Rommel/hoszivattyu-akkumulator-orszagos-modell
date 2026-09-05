# B10-P62 — Cross-operator partial/whole membership supersession

## Purpose

P61 returned B10 from residual classification to blocker-directed authority acquisition and exposed a semantic conflict that must be corrected before more spatial rows are promoted.

The current MVM Démász M1 explicitly states that MVM Démász operates low-/medium-voltage distribution network on **part** of 20 administrative settlements. P61 then showed that 13 of those settlements also have an exact current administrative-unit token in another DSO M1. Those counterpart rows had already been materialized historically as `WHOLE_SETTLEMENT_MEMBERSHIP_PROVEN`.

A current explicit partial-settlement claim and an effective whole-settlement claim for another operator cannot be silently consumed as if they described one unambiguous settlement-grain routing fact.

P62 therefore introduces an append-only **effective-admission supersession layer**.

## Core distinction

`RAW MATERIALIZED WHOLE CLAIM != EFFECTIVE CURRENT WHOLE-SETTLEMENT ADMISSION`

Historical/materialized rows remain in their original append-only source tranches for auditability. P62 does **not** rewrite those files. Instead, downstream effective membership admission must apply the exact P62 supersession set before any canonical crosswalk or programme routing is populated.

## Exact 13 supersessions

### OPUS TITÁSZ — 9

- `Csabacsűd`
- `Dévaványa`
- `Gyomaendrőd`
- `Kunszentmárton`
- `Szeghalom`
- `Tiszakécske`
- `Tiszasas`
- `Tiszaug`
- `Zsadány`

### ELMŰ — 3

- `Dabas`
- `Péteri`
- `Újhartyán`

### E.ON DDÁSZ — 1

- `Mohács`

For each exact `(settlement_name, prior_operator_id)` pair:

- prior raw status remains auditable as `WHOLE_SETTLEMENT_MEMBERSHIP_PROVEN`;
- P62 effective status is `WHOLE_SETTLEMENT_CLAIM_SUPERSEDED`;
- the counterpart current M1 token is retained only as administrative-unit presence until current claim-specific boundary or exact usage-location authority resolves the internal split.

The conflict authority is:

`SRC-B10-MVM-DEMASZ-M1-2026`

P61 already pins that current M1 as the canonical exact-20 MVM Démász partial-settlement authority.

## Effective counts after P62

The raw materialization counts remain historical audit counts. Effective whole-settlement counts after exact P62 supersessions are:

| Operator | Raw materialized whole | P62 superseded | Effective whole |
|---|---:|---:|---:|
| ELMŰ | 130 | 3 | 127 |
| E.ON DDÁSZ | 820 | 1 | 819 |
| E.ON ÉDÁSZ | 814 | 0 | 814 |
| MVM Démász | 256 | 0 | 256 |
| MVM Émász | 650 | 0 | 650 |
| OPUS TITÁSZ | 395 | 9 | 386 |

P61's `Tass üdülőterület -> ELMU:SERVICE_AREA` record is a separate `PARTIAL_SETTLEMENT` usage-location membership and is not part of the whole-settlement counts.

## Why this is not a demotion of source evidence

The original M1 tokens remain real source facts. What changes is the **claim admitted from them**.

An exact settlement-name token in an operator M1 may prove that the administrative unit is present in that operator's territorial authority surface. Once another current operator source explicitly proves partial coverage inside the same administrative settlement, the unqualified token cannot continue to authorize an effective whole-settlement routing claim without an independent boundary proposition.

P62 therefore supersedes only the over-broad claim, not the underlying source token.

## Executable gate

`modules/B10/effective_service_area_membership_contract.py` introduces exact-pair supersession logic.

A raw `WHOLE_SETTLEMENT_MEMBERSHIP_PROVEN` row is:

- `EFFECTIVE_WHOLE_SETTLEMENT_MEMBERSHIP` when no exact supersession applies;
- `WHOLE_SETTLEMENT_CLAIM_SUPERSEDED` when its exact `(settlement_name, operator_id)` is present in the P62 ledger.

`require_effective_whole_membership()` fails closed for superseded rows.

The rule is exact only. There is no fuzzy matching, normalization, parent promotion, counterpart propagation, or inferred boundary.

## Frozen boundaries

`CURRENT PARTIAL-SETTLEMENT AUTHORITY + COUNTERPART ADMINISTRATIVE-UNIT TOKEN != TWO WHOLE-SETTLEMENT MEMBERSHIPS`

`ADMINISTRATIVE-UNIT PRESENCE != EFFECTIVE WHOLE-SETTLEMENT MEMBERSHIP WHEN A CURRENT PARTIAL CONFLICT EXISTS`

`RAW HISTORICAL MATERIALIZATION != CURRENT EFFECTIVE ADMISSION`

`CLAIM SUPERSESSION != SOURCE-TOKEN DELETION`

`CROSS-OPERATOR CONFLICT != AUTHORITY TO INFER THE INTERNAL BOUNDARY`

`SUPERSEDED WHOLE CLAIM != PROVEN COUNTERPART PARTIAL USAGE-LOCATION MEMBERSHIP`

`PARTIAL-SETTLEMENT SERVICE-AREA MEMBERSHIP != EXACT DSO NODE`

## B10 state

P62 corrects the effective spatial authority surface but does not close the national spatial blocker:

- canonical national crosswalk remains header-only;
- `NO_COMPLETE_KSH_DSO_MEMBERSHIP_CROSSWALK` remains active;
- `PARTIAL_SETTLEMENT_USAGE_LOCATION_RESOLUTION_REQUIRED` remains active;
- P61's one resolved Tass usage-location remains valid;
- the 13 P62 cases now explicitly require boundary/usage-location authority rather than carrying contradictory effective whole claims;
- B10 remains `IN_PROGRESS` at 15% readiness.

This is a correctness-preserving prerequisite for further blocker reduction: future authority acquisition can now resolve the 13 cases against a clean effective-admission surface instead of layering new evidence on top of contradictory whole-settlement claims.
