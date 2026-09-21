# B02-P72 — align transition-set scope to the canonical non-district physical screen

**State:** `DENOMINATOR REPAIRED / DISTRICT REMOVED FROM B02 PHYSICAL-SCOPE RESIDUAL`

**Canonical base:** `fe9bc465e6fa43d171a1c6405df2f40e4badd045`

**Implementation date:** 2026-09-21

## 1. Problem

P70 correctly identified the exact KSH NHEAT count:

`1,173,639`.

But the P69/P70 transition-set runtime still expressed its share against the
full occupied universe:

`4,008,541`.

That denominator is not the canonical B02 physical screening scope.

B01-P3 and `registry/b02_eligibility_layer_contract.csv` define:

`PHYSICAL_SCREENING_SCOPE = occupied + non-district-heated`.

Exact 2022 value:

`3,389,817`.

Therefore:

`FULL OCCUPIED UNIVERSE != B02 PHYSICAL-SCREENING DENOMINATOR`.

## 2. Exact scope reconciliation

The P22 topology partition is:

- CENTRAL_HEATING: **2,216,178**;
- DISTRICT_HEATING: **618,724**;
- ROOM_BY_ROOM_OR_NO_HEAT: **1,173,639**;
- total occupied: **4,008,541**.

B01-P3 independently fixes:

- non-district physical scope: **3,389,817**;
- district-heated outside that physical scope: **618,724**.

And exactly:

`2,216,178 + 1,173,639 = 3,389,817`.

Therefore the in-scope transition population is:

`CENTRAL_HEATING + NHEAT`.

The district branch is not part of this B02 physical-screening denominator.

## 3. Correct P70 floor within programme physical scope

P70's NHEAT count does not change.

The denominator changes from the source universe to the canonical physical
screen:

`1,173,639 / 3,389,817 = 0.3462248847`.

Therefore:

`NEW_OR_REPLACE_DISTRIBUTION_REQUIRED_SHARE >= 34.622488%`

**within the B02 physical screening scope**.

The complement is:

`REUSE_EXISTING_DISTRIBUTION_SHARE <= 65.377512%`.

In count terms:

- nonreuse lower bound: **1,173,639 dwellings**;
- reuse upper bound: **2,216,178 dwellings**.

The latter equals the exact CENTRAL_HEATING branch and is only an upper bound.

## 4. District-heating scope boundary

P72 does not claim that district heating is technically unsuitable, inferior,
or legally impossible to include in any future policy.

It says something narrower:

the already-canonical B01-P3/B02 physical screen used by this transition model
is **non-district-heated**.

Therefore:

`DISTRICT_HEATING -> OUT_OF_B02_PHYSICAL_SCREENING_SCOPE`

for this contract.

Hard boundary:

`OUT_OF_PHYSICAL_SCREENING_SCOPE != TECHNICALLY_INELIGIBLE`.

## 5. Runtime effect

New:

`modules/B02/programme_scope_transition.py`

provides the exact scope reconciliation and topology classification.

Updated:

`modules/B02/transition_set_propagation.py`

now uses:

`NHEAT / NON_DISTRICT_PHYSICAL_SCOPE`

instead of:

`NHEAT / FULL_OCCUPIED_UNIVERSE`.

The count upper bound also contracts from 4,008,541 to 3,389,817.

## 6. Residual contraction

Old residual:

`CENTRAL_DISTRICT_REUSE_VS_NONREUSE_ASSIGNMENT`.

This mixed an out-of-scope district branch into the B02 physical-screening
transition problem.

P72 retires that residual as scope mixing.

Current distribution residual:

`CENTRAL_HEATING_REUSE_VS_NONREUSE_ASSIGNMENT`.

Its exact maximum domain is:

**2,216,178 dwellings**.

Q-B02-004 also retains:

- `NON_GAS_CONVECTOR_EMITTER_INTERVENTION_ASSIGNMENT`;
- `ROOM_GRAIN_ACTION_DISTRIBUTION`;
- `MARKET_REALIZED_COST_DISTRIBUTION` only if central/expected monetary CAPEX
  is required.

## 7. Non-claims

P72 does not claim:

- 3,389,817 dwellings are technically eligible;
- 3,389,817 dwellings are final programme participants;
- all 2,216,178 CENTRAL_HEATING dwellings can reuse distribution;
- all 2,216,178 CENTRAL_HEATING dwellings require replacement;
- district-heated dwellings are universally excluded from all future policy;
- Q-B02-004 is resolved.

B02 readiness remains 55%.
