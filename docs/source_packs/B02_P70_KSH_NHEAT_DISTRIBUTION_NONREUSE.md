# B02-P70 — KSH NHEAT distribution non-reuse assignment

**State:** `EXACT KSH NHEAT NON-REUSE LOWER BOUND / CENTRAL+DISTRICT RESIDUAL OPEN`

**Canonical base:** `67d3703e48c45c60c84c005d1d5752bc3d403d6c`

**Implementation date:** 2026-09-21

## 1. Purpose

P69 repaired the action grain and left:

`HUNGARIAN_DISTRIBUTION_NONREUSE_ASSIGNMENT`

as one of the remaining Q-B02-004 blockers.

P70 resolves the complete KSH/P22 `ROOM_BY_ROOM_OR_NO_HEAT` branch for one
explicitly bounded programme route:

`CENTRAL_HYDRONIC_AWHP`.

It does not generalize this result to air-to-air or other heat-pump routes.

## 2. KSH source-native semantics

The official 2022 Census definitions separate:

- district heating;
- central heating serving several dwellings;
- central heating serving one dwelling;
- room heating.

KSH defines room heating as rooms being heated **individually** by convector,
stove or another device. The same category also contains dwellings where no
heating equipment or heating conditions existed at enumeration.

P22 materializes these source categories as an exact disjoint occupied-stock
partition:

- `HEAT111`, `HEAT112` -> `CENTRAL_HEATING`;
- `HEAT12` -> `DISTRICT_HEATING`;
- `NHEAT` -> `ROOM_BY_ROOM_OR_NO_HEAT`.

Therefore, for a programme route requiring a central hydronic distribution:

`NHEAT -> NO SOURCE-NATIVE REUSABLE CENTRAL DISTRIBUTION`.

Hence:

`NHEAT -> NEW_OR_REPLACE_DISTRIBUTION_REQUIRED`.

This is a topology statement, not an emitter-type statement.

## 3. Exact P22 population result

The P70 runtime consumes the committed 116,452-row P22/WBL occupied-stock joint.

Exact result:

- occupied dwellings: **4,008,541**;
- `ROOM_BY_ROOM_OR_NO_HEAT`: **1,173,639**;
- share: **0.292784581722... = 29.278458%**.

Therefore the central-hydronic-AWHP route has a national lower bound of:

**1,173,639 dwellings**

requiring a new or replaced central distribution.

The complementary reuse ceiling is:

- dwellings: **2,834,902**;
- share: **0.707215418278... = 70.721542%**.

This ceiling does not assert that all remaining dwellings can actually reuse
their distribution. Central and district-heated dwellings still require
separate transition assignment.

## 4. Relationship to P39 gas convectors

P39 provides a calibrated primary gas-convector share:

`0.233`.

P41 proves that the gas-convector subtype requires
`REPLACE_EXISTING_DISTRIBUTION`.

But the exact overlap between the calibrated P39 gas-convector population and
the P22 NHEAT topology is not fully identified.

Therefore:

`NHEAT_SHARE + GAS_CONVECTOR_SHARE`

is forbidden.

The valid fail-closed union lower bound is:

`max(NHEAT_SHARE, GAS_CONVECTOR_SHARE)`.

Numerically:

`max(0.292784581722, 0.233) = 0.292784581722`.

Thus P22/KSH, not the calibrated gas-convector margin, now determines the
national non-reuse lower bound.

## 5. Runtime contract

New module:

`modules/B02/distribution_nonreuse_assignment.py`

provides:

- explicit `CENTRAL_HYDRONIC_AWHP` route admission;
- exact P22 NHEAT aggregation;
- P39/P22 overlap-safe `max()` lower-bound composition;
- exact non-reuse lower count/share;
- complementary reuse upper bound.

`modules/B02/transition_set_propagation.py` now consumes this stronger P70
lower bound instead of the old P69 23.3% floor.

## 6. Programme significance

The improvement is material:

- old proven floor: **23.3%** / **933,990.053 calibrated expected dwelling-equivalents**;
- P70 floor: **29.278458%** / **1,173,639 exact DER dwellings**.

P70 therefore proves that at least 1.17 million occupied Hungarian dwellings
cannot be modelled as reusing an existing central distribution on the scoped
central-hydronic-AWHP route.

This affects downstream:

- distribution-system material quantities;
- installation labour;
- hydraulic design workload;
- programme timing;
- CAPEX upper-bound propagation.

It does not by itself identify those quantities.

## 7. Q-B02-004 effect

The broad residual:

`HUNGARIAN_DISTRIBUTION_NONREUSE_ASSIGNMENT`

is now partially resolved with exact national authority for the NHEAT branch.

Remaining distribution residual:

`CENTRAL_AND_DISTRICT_DISTRIBUTION_REUSE_VS_NEW_OR_REPLACE_ASSIGNMENT`.

Other residuals remain:

- `HUNGARIAN_EMITTER_INTERVENTION_ASSIGNMENT`;
- `ROOM_GRAIN_ACTION_DISTRIBUTION`;
- `MARKET_REALIZED_COST_DISTRIBUTION` only if a central/expected monetary CAPEX
  estimate is required.

Q-B02-004 remains OPEN.

B02 readiness remains **55%**; no arbitrary percentage uplift is inferred from
one strengthened bound.

## 8. Non-claims

P70 does not claim:

- every NHEAT dwelling contains a gas convector;
- every NHEAT dwelling requires the same physical retrofit package;
- NHEAT count equals emitter replacement count;
- central/district-heated dwellings can all reuse their distribution;
- the P22 and P39 populations are disjoint;
- a national room-level KEEP/UPSIZE/CHANGE/ADD distribution;
- Q-B02-004 closure.
