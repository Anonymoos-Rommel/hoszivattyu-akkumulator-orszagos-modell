# B02-P70 — KSH NHEAT national distribution-nonreuse floor

**State:** `NHEAT NONREUSE LOWER BOUND QUALIFIED / CENTRAL+DISTRICT RESIDUAL OPEN`

**Canonical base:** `67d3703e48c45c60c84c005d1d5752bc3d403d6c`

**Implementation date:** 2026-09-21

## 1. Purpose

P69 repaired the action grain and left:

`HUNGARIAN_DISTRIBUTION_NONREUSE_ASSIGNMENT`

as one of the remaining Q-B02-004 residuals.

P70 asks a narrower question:

> Which Hungarian occupied dwellings are already source-natively known not to
> have a reusable **central distribution** for the programme's central hydronic
> air-to-water heat-pump route?

The answer is the KSH WBL011 `NHEAT` branch.

## 2. Exact source-native controls

P13 independently checked the national WBL011 control:

`FUTES_TOH=NHEAT = 1,173,639 dwellings`.

P22 binds the source-native heating-mode classes to:

- CENTRAL_HEATING;
- DISTRICT_HEATING;
- ROOM_BY_ROOM_OR_NO_HEAT.

The complete occupied universe is:

`4,008,541 dwellings`.

The exact topology partition is therefore:

| P22 class | Dwellings |
| --- | ---: |
| CENTRAL_HEATING | 2,216,178 |
| DISTRICT_HEATING | 618,724 |
| ROOM_BY_ROOM_OR_NO_HEAT / NHEAT | 1,173,639 |
| **TOTAL** | **4,008,541** |

## 3. KSH semantics

The official 2022 Census definition states that room heating means rooms are
heated individually by convector, stove or another device. The same category
also contains dwellings where no heating equipment or heating conditions were
available at enumeration.

Therefore:

`NHEAT != CENTRAL_HEATING`

and:

`NHEAT != PROVEN REUSABLE CENTRAL DISTRIBUTION`.

For the programme route used by the B05/B06 chain:

`CENTRAL_HYDRONIC_AIR_TO_WATER`

the NHEAT branch must receive either:

- a **new** central distribution, or
- replacement/reconfiguration of the existing room-heating arrangement.

P70 therefore qualifies:

`NHEAT -> NEW_OR_REPLACE_DISTRIBUTION_REQUIRED`.

It does not distinguish NEW from REPLACE.

## 4. Exact national lower bound

`1,173,639 / 4,008,541 = 0.2927845817...`

Therefore:

`NEW_OR_REPLACE_DISTRIBUTION_REQUIRED_SHARE >= 29.278458%`

and:

`NEW_OR_REPLACE_DISTRIBUTION_REQUIRED_DWELLINGS >= 1,173,639`.

This is stronger than the earlier P39/P41 calibrated gas-convector floor:

`0.233 -> 933,990.053 expected dwelling-equivalents`.

P70 does **not** add the two floors.

Hard boundary:

`NHEAT FLOOR + GAS-CONVECTOR FLOOR != VALID UNION`

because the gas-convector/NHEAT overlap is not identified.

The source-native KSH NHEAT floor simply dominates the current top-level lower
bound.

## 5. Reuse upper bound

The complement is:

`4,008,541 - 1,173,639 = 2,834,902`.

Therefore:

`REUSE_EXISTING_DISTRIBUTION <= 2,834,902 dwellings`

or:

`REUSE_EXISTING_DISTRIBUTION_SHARE <= 70.721542%`.

This is an **upper bound only**.

It does not state that all central- or district-heated dwellings can reuse their
current distribution.

## 6. Runtime

New module:

`modules/B02/distribution_nonreuse_assignment.py`

It:

- reproduces the P22 exact topology totals;
- fails if the NHEAT control drifts from 1,173,639;
- qualifies NHEAT for the central hydronic air-to-water nonreuse path;
- refuses to classify CENTRAL_HEATING or DISTRICT_HEATING as reuse/nonreuse
  without additional evidence;
- refuses to promote the P70 rule to a different programme route.

`modules/B02/transition_set_propagation.py` now consumes the P70 NHEAT floor
instead of the older calibrated 0.233 floor.

## 7. Blocker effect

The broad:

`HUNGARIAN_DISTRIBUTION_NONREUSE_ASSIGNMENT`

becomes:

`PARTIAL_RESOLVED_LOWER_BOUND`.

The remaining distribution blocker is now:

`CENTRAL_DISTRICT_REUSE_VS_NONREUSE_ASSIGNMENT`.

Q-B02-004 residuals:

1. `CENTRAL_DISTRICT_REUSE_VS_NONREUSE_ASSIGNMENT`;
2. `HUNGARIAN_EMITTER_INTERVENTION_ASSIGNMENT`;
3. `ROOM_GRAIN_ACTION_DISTRIBUTION`;
4. `MARKET_REALIZED_COST_DISTRIBUTION` only if a central/expected monetary
   estimate is required.

## 8. Non-claims

P70 does not claim:

- every NHEAT dwelling has a gas convector;
- every NHEAT dwelling requires REPLACE rather than NEW;
- the 23.3% gas-convector margin can be added to NHEAT;
- every CENTRAL_HEATING dwelling has a reusable hydronic circuit;
- every DISTRICT_HEATING dwelling has a reusable in-dwelling emitter system;
- the result applies to air-to-air or other heat-pump architectures;
- Q-B02-004 is closed.

B02 readiness remains 55%.
