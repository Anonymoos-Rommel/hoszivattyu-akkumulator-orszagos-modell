# B02-P71 — gas-convector emitter-intervention lower bound

**State:** `HUNGARIAN EMITTER INTERVENTION PARTIALLY RESOLVED / GAS-CONVECTOR LOWER BOUND QUALIFIED`

**Canonical base:** `1430df3eb2182e41c065320cdb127b13250d7008`

**Implementation date:** 2026-09-21

## 1. Purpose

P70 strengthened the dwelling-level distribution nonreuse floor to the exact
KSH NHEAT share.

A different programme question remains:

> how much of the Hungarian stock is already proven to require intervention at
> the heat-emission system itself?

P71 answers this only where the current emitter class is already admitted.

## 2. Existing authority

P39 supplies the approved calibrated primary-heating gas-convector margin:

`0.233`

over the exact occupied-dwelling universe:

`4,008,541`.

Therefore:

`4,008,541 * 0.233 = 933,990.053`

calibrated expected dwelling-equivalents.

The result remains `ASS`, not OBS.

P41 separately qualifies the current gas-convector transition semantics:

- current emitter: `GAS_CONVECTOR`;
- current topology: `NON_HYDRONIC_ROOM_HEATING`;
- programme transition path: `REPLACE_EXISTING_DISTRIBUTION`;
- current hydronic design temperature: `NOT_APPLICABLE`.

## 3. Emitter implication for the canonical programme route

For:

`CENTRAL_HYDRONIC_AIR_TO_WATER`

a current gas convector cannot itself become the target hydronic heat emitter.

Therefore the P39/P41 branch requires a **new hydronic heat-emission system**.

Canonical implication:

`GAS_CONVECTOR + CENTRAL_HYDRONIC_AWHP -> NEW_HYDRONIC_HEAT_EMISSION_SYSTEM_REQUIRED`.

At national population level:

`NEW_HYDRONIC_HEAT_EMISSION_SYSTEM_REQUIRED_SHARE >= 0.233`.

And:

`NEW_HYDRONIC_HEAT_EMISSION_SYSTEM_REQUIRED >= 933,990.053 calibrated expected dwelling-equivalents`.

## 4. Grain boundary

This is a dwelling/system-level intervention requirement.

It is **not**:

- the number of radiators;
- the number of heated rooms;
- a room-level KEEP/UPSIZE/CHANGE/ADD label;
- proof that every gas-convector dwelling receives radiators rather than
  surface heating or another admitted hydronic emission solution;
- an integer observed household count.

Therefore:

`DWELLING REQUIRES NEW HYDRONIC HEAT-EMISSION SYSTEM != EMITTER UNIT COUNT`.

and:

`SYSTEM REQUIREMENT != ROOM-GRAIN ACTION DISTRIBUTION`.

## 5. Relationship to P70 NHEAT

P70 proves:

`NHEAT -> NEW_OR_REPLACE_DISTRIBUTION_REQUIRED`

for 1,173,639 exact DER dwellings on the same central-hydronic AWHP route.

P71 does **not** turn the complete NHEAT share into a new-emitter share.

Reason: P22 identifies topology, not the exact current room-device inventory.
Some source-unresolved room devices could in principle be reused or reconnected
after a new central distribution is designed; P70 alone does not settle that.

Therefore:

`NHEAT NONREUSE FLOOR != NEW EMITTER UNIT FLOOR`.

The stronger P70 29.278458% distribution floor and the P71 23.3% emitter-system
floor answer different questions.

## 6. Blocker effect

Previous:

`HUNGARIAN_EMITTER_INTERVENTION_ASSIGNMENT = Q`.

P71:

`HUNGARIAN_EMITTER_INTERVENTION_ASSIGNMENT = PARTIAL_RESOLVED_LOWER_BOUND`.

Remaining emitter residual:

1. `NON_GAS_CONVECTOR_EMITTER_INTERVENTION_ASSIGNMENT`;
2. `ROOM_GRAIN_ACTION_DISTRIBUTION`.

The separate distribution residual remains:

- `CENTRAL_DISTRICT_REUSE_VS_NONREUSE_ASSIGNMENT`.

Optional monetary residual remains:

- `MARKET_REALIZED_COST_DISTRIBUTION` only if central/expected CAPEX is
  required instead of the already-qualified official upper ceiling.

## 7. Non-claims

P71 does not claim:

- 23.3% is the final national emitter-intervention share;
- 933,990.053 is an integer household observation;
- one new radiator per gas-convector dwelling;
- any national radiator-unit count;
- any national KEEP/UPSIZE/CHANGE/ADD room-action mix;
- 29.278458% NHEAT equals new-emitter prevalence;
- Q-B02-004 is closed.

B02 readiness remains 55%.
