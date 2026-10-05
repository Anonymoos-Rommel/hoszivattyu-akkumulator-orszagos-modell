# V1-025: B12 input/accounting contract (draft)

Base: `6b8ef9da4946a0b7ec510732183a001d529a7908`.
Status: implementation candidate; independent content review and the final
aggregate run remain required. No source admission or numerical module closure
is claimed by this checkpoint.

## Scope and resulting behavior

The new B12 package supplies immutable section records and three operations:
`validate_case`, `assess_readiness`, and `audit_accounting`. A well-formed missing
input remains null/Q with its exact path, reason and acquisition reference.
Known initial cost can remain available while eligibility, later O&M, income or
valuation inputs are missing. Baseline and programme scopes and event identities
remain separate, including explicit absent-leg declarations.

Only permanently labelled synthetic witnesses execute the accounting consumer.
External E1/E2 review references are accepted as pointers but not resolved here;
actual-source numerical outputs remain Q. A source ID, evidence-tier label or
explanation is never sufficient numerical admission. Future review follows the
existing canonical evidence policy, without a new owner-per-datum approval gate.
Structural validity and individual permission are distinct outcomes.

Available synthetic identities cover full/eligible initial cost, VAT, lifecycle
cost, gross retail bills, unfinanced and financed economic cash, dated bank
liquidity, recurring budget residual and outstanding debt. Unavailable dependent
row columns are null. Arithmetic uses Decimal with explicit local precision and
rounding. It does not interpolate annual schedules into monthly cash.

The core delayed-grant fixture reconciles 127,000 HUF full invoice, 57,000 gross
loan draw, 1,000 withheld fee, later 20,000 grant and two 28,500 principal payments.
It produces −127,000 unfinanced and −108,000 financed lifetime cash. Opening
60,000 liquidity briefly becomes −11,000 before reimbursement. Direct supplier
finance preserves economics without inventing bank inflows. Noncash terminal
value is separate and cannot cure that deficit.

## Revision 2: invariant review repairs

Independent review of the first candidate found gaps that its passing configured
suite did not cover. Revision 2 repairs six invariant families: unique economic
and fixed-charge events; output-specific missingness; recursive nested field
validation; lifecycle/debt chronology; B04 producer-context binding; and reciprocal
receipt/invoice/asset references. The first candidate’s receipts remain historical
and are not treated as validation of these revised bytes.

The focused witnesses now include changed cash dates and caller keys around the
same meter interval; income versus recurring-receipt duplication; support IDs
crossing forgiveness, grants and resources; gross-only VAT with multiple refunds;
capital Q with known recurring components; required-field mutations across every
section family; zero/known/Q rate dimensions; valid same-day replacement chains
and invoice prepayment; explicit maturity payments/refinancing versus unresolved
labels; heating/outside-season producer replay; and replacement-linked terminal
sales. Positive counterfactual reuse, separate meters, distinct income components,
known partial refunds and later-maturing outstanding debt remain legal.

An in-window unpaid maturity balance now leaves complete finance, liquidity and
recurring outputs Q until dated treatment is present. Unknown VAT cannot produce
a known refund cash result. Unknown capital grants/costs do not hide a known
recurring budget. Unavailable columns remain null even when other views compute.
The B04 adapter and validator replay the existing producer with explicit product,
distributor, service interval, load/connection scope, quantity, months and allocation;
matching money alone cannot authorize a season or context change.

## Revision 3: final neighboring boundaries

Three narrow neighboring corrections preserve the distinction between malformed
units and missing data. Policy floor and reserve values must use the case's money
currency and basis. Negative floors remain valid; reserve stock is nonnegative.
No floor metric, sign, value or affordability policy is selected by validation.
For overlapping meter/service scopes, only two known positive fixed charges
establish a duplicate charge. An unknown fee may be zero, so structurally valid
partial bills remain Q for the dependent bill/cash outputs. Known positive
duplicates still fail and legitimate zero-fee allocations remain possible.
The B04 adapter and replay also require native HUF monetary fields, and case
validation binds their nominal monetary price-date anchor to 2026. Retagging
unchanged HUF charges as EUR is rejected in both constructor and whole-case
mutation paths. Independently declared EUR scenarios without B04 remain valid;
this adds no currency conversion machinery or general currency default. A claimed
price-year rebasing or isolated conversion row cannot replace the B04 monetary
anchor. Later service, settlement and evaluation dates remain valid under the
explicit frozen-nominal-2026 scenario.

Revision-2 evidence and aggregate receipts are preserved as historical results;
this revision requires its own exact-byte independent replay and full run.

## Preserved authorities

B06/B07 retain technical cost/lifecycle authority, B03/B04 price/bill authority,
B11 physical/reference-state authority, B14 funding-rule and eligibility authority,
B13 fiscal consolidation and B15 full financing mix. The B12 inventory describes
missing consumer handoffs rather than duplicate source variables or household
records. It does not add a formal source blocker or close evidence debt.

B03 gas remains MARKET_RESIDENTIAL_FINAL only. B04's gross tariff snapshot and
source IDs are preserved; a complete annual invoice, H site eligibility, dynamic
energy-only retail bridge or future forecast is not inferred. B14's pinned rules,
original envelopes, suspended intakes and maximum terms do not become awards,
procurement estimates, accessible funding or household loan approval.

Household/person/dwelling mappings, representative/calibrated inference,
uncertainty and E2 validation debt remain explicit. No exhaustive-population
microdata requirement is introduced. Qualified aggregate controls can coexist
with an unresolved coherent joint income/spending/liquidity/debt/dwelling handoff;
release, source-base and denominator reconciliation are still needed.

Both B12 globals remain null/Q. B01's existing 15-year rollout scenario and
12/15/20 reporting authority remain unchanged; no asset life, discount rate,
owner floor meaning/value, reserve, debt or adoption policy is defaulted. No
NPV/IRR/DSCR, affordability decision, national estimate, support gap, fiscal engine
or B15 export is implemented. B15 remains blocked.

## Files and verification

Owned additions are `modules/B12/__init__.py`,
`modules/B12/input_accounting_contract.py`, `modules/B12/README.md`,
`registry/b12_input_inventory.json`,
`tests/test_b12_input_accounting_contract.py`, and this draft checkpoint.
No existing production module, global variable, policy, workflow or source
registry is changed by these six files. Shared plan/status integration is reviewed
separately by the integrating lead.

- PASS: 51 focused B12 positive/negative and crossing witnesses
- PASS: 154 relevant existing tests covering B03; B04 canonical, dynamic, H/battery,
  outside-H/B and source checks; B11 physical/reference-state; B14; evidence and
  population policies; registry, V1.2 portfolio and V1 research plan
- PASS: `python tools/validate_registry.py`
- PASS: whitespace validation for the candidate additions
- NOT_RUN here: final full `python -m unittest discover -s tests -v`, reserved for
  the integrating lead after independent review and shared-file integration
- NOT_RUN: actual household source admission, live-source verification, financial
  product validation, national computation and B15 release

Verification receipts and exact SHA-256/Git-blob file freeze are preserved by the
integrating workflow outside source data. Initial development iterations are
not represented as passing final checks. A synthetic/schema pass is neither
source verification nor a national household result.
