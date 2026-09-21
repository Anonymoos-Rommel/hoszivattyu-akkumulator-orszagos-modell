# B02-P76 — reuse CAPEX superset envelope

**State:** `REUSE CAPEX PARTIALLY RESOLVED IN KEHOP STRUCTURAL FAMILY-HOUSE SCOPE`

**Canonical base:** `8a0cf3692db9326783a30198521ccaf7542aa1fe`

**Implementation date:** 2026-09-21

## 1. Why P76 exists

P75 quantified the structural overlap between the canonical P21/WBL stock and
the current KEHOP family-house / pre-2007 property scope.

The remaining reuse-path question was still framed too broadly:

`REUSE_PATH_CAPEX_BOUND_REQUIRED`.

P76 separates:

1. a source-native official replacement-package ceiling;
2. a conservative modelled reuse-path upper bound;
3. legal/funding eligibility.

These are not the same claim.

## 2. Current KEHOP technical action authority

The current KEHOP Plusz-4.1.7-24 call explicitly permits:

- `3.4.1.2` secondary heating-circuit adaptation;
- heat-emitter modernization **or** replacement;
- floor/ceiling heating/cooling systems in the stated activity;
- `3.4.1.3` automatic central/source-side and local/emitter-side controls.

Therefore the P75 structural family-house scope has a current Hungarian
technical action authority for reuse-compatible secondary-side modernization.

Canonical boundary:

`KEHOP TECHNICAL ACTION AUTHORITY != NATIONAL ACTION FREQUENCY`.

This partially resolves the earlier family-house action-authority gap.

## 3. Source-native cost ceiling

Annex 1 publishes:

### Hőleadók cseréje

- material maximum: **1,422,400 HUF/set**;
- labour maximum: **2,133,600 HUF/set**;
- total maximum: **3,556,000 HUF/set**.

The package includes:

- new heat emitters;
- secondary heating circuit;
- HMV tank;
- controls;
- modern pipework;
- installation materials;
- demolition of existing emitters and pipes.

This remains:

`QUALIFIED_OFFICIAL_UPPER_BOUND`

for the source-native complete replacement package.

It is not a source-native reuse-only price.

## 4. Conservative reuse-path transfer

P76 defines the counted reuse-path secondary work as a subset of the complete
replacement package work scope.

This is an explicit modelling boundary:

`REUSE SECONDARY WORK ⊆ COMPLETE REPLACEMENT PACKAGE WORK`.

Only under that condition P76 allows:

`REUSE SECONDARY CAPEX <= 3,556,000 HUF/set`.

Evidence status:

`ASS_CONSERVATIVE_SUPERSET_UPPER_BOUND`.

Therefore:

`OFFICIAL REPLACEMENT PACKAGE CEILING != OFFICIAL REUSE PRICE`.

and:

`CONSERVATIVE SUPERSET CAP != MARKET-TYPICAL OR EXPECTED COST`.

If an individual project contains reuse-path work outside the complete package
scope, this bound fails closed and record/project cost evidence is required.

## 5. Exact P75 reuse-compatible population envelope

Reuse can only occur in the P73 `CENTRAL_HEATING` branch.

The P75 exact CI-materialized family-house components are:

### definitely pre-2007

- CENTRAL scenario: **1,124,830.282889203**
- FLAT scenario: **1,117,527.277634664**

So the conservative reuse structural upper is:

**1,124,830.282889203 expected dwelling-equivalents**.

### possible pre-2007

Including the complete cutoff-straddling Y2001-2010 band as an upper envelope:

- CENTRAL scenario: **1,298,476.155320049**
- FLAT scenario: **1,293,455.782466441**

So the possible reuse structural upper is:

**1,298,476.155320049 expected dwelling-equivalents**.

The lower bound is zero because P73 keeps the central reuse/nonreuse split
latent.

## 6. Aggregate conservative CAPEX sensitivity

Using the ASS superset ceiling:

### definite-pre2007 structural upper

`1,124,830.282889203 × 3,556,000`

= **3,999,896,485,954.006 HUF**

### possible-pre2007 structural upper

`1,298,476.155320049 × 3,556,000`

= **4,617,381,208,318.095 HUF**

These are deliberately wide programme-planning upper sensitivities.

They are not:

- expected expenditure;
- market estimates;
- funding demand;
- legally eligible KEHOP claim amounts;
- final programme CAPEX.

## 7. Legal eligibility is a different question

P75 correctly kept current KEHOP legal/project eligibility unresolved.

P76 keeps that fact.

But Q-B02-004 is a **technical programme model** question, not a claim that a
specific household can receive current KEHOP funding.

Therefore:

`CURRENT KEHOP FUNDING ELIGIBILITY != TECHNICAL REFERENCE COST AUTHORITY`.

P76 retires:

`KEHOP_LEGAL_ELIGIBILITY_CONDITIONS`

**as a technical-model blocker only**.

It remains Q whenever the requested claim is actual current-programme funding
eligibility.

## 8. Blocker effect

Previous:

- `REUSE_PATH_CAPEX_BOUND_REQUIRED`;
- `REUSE_FAMILY_HOUSE_OR_FULL_NATIONAL_SCOPE_ACTION_AUTHORITY_REQUIRED`;
- `KEHOP_LEGAL_ELIGIBILITY_CONDITIONS`.

P76:

- `REUSE_PATH_CAPEX_BOUND_REQUIRED`
  -> `PARTIAL_RESOLVED_WITHIN_KEHOP_STRUCTURAL_SCOPE`;
- family-house action authority
  -> `PARTIAL_RESOLVED_KEHOP_FAMILY_HOUSE_SCOPE`;
- KEHOP legal eligibility
  -> `RETIRED_AS_TECHNICAL_MODEL_BLOCKER`.

Current cost/action residual becomes:

1. `REUSE_OUTSIDE_KEHOP_STRUCTURAL_SCOPE_CAPEX_BOUND_REQUIRED`;
2. `REUSE_ACTION_AUTHORITY_OUTSIDE_KEHOP_STRUCTURAL_SCOPE_REQUIRED`;
3. `NONREUSE_OUTSIDE_KEHOP_STRUCTURAL_SCOPE_CAPEX_BOUND_REQUIRED`.

Other residuals remain:

- `NATIONAL_TRANSITION_RESPONSE_MATERIALIZATION_BY_ARCHETYPE_REQUIRED`;
- `B05_PRODUCT_OPERATING_POINT_COVERAGE_REQUIRED`;
- `NON_GAS_CONVECTOR_EMITTER_INTERVENTION_ASSIGNMENT`;
- `ROOM_GRAIN_ACTION_DISTRIBUTION`;
- `MARKET_REALIZED_COST_DISTRIBUTION` only if central/expected CAPEX is
  required.

## 9. Non-claims

P76 does not claim:

- 3.556 M HUF is an official reuse price;
- reuse always costs less than replacement as an empirical market fact;
- every family house satisfies current KEHOP legal eligibility;
- every structurally compatible central-heating house is reuse;
- the aggregate upper sensitivities are expected programme expenditure;
- the KEHOP ceiling applies outside its structural source scope;
- Q-B02-004 is closed.

B02 readiness remains **55%**.
