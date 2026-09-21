# B02-P73 — central-heating latent distribution split

**State:** `CENTRAL POINT ASSIGNMENT RETIRED AS BLOCKER / FULL SET PROPAGATABLE`

**Stacked base:** B02-P72 head `0373c84af5bb3af206d2d1103e8c352082057f3d`

**Implementation date:** 2026-09-21

## 1. Purpose

P72 leaves exactly **2,216,178 CENTRAL_HEATING** dwellings inside the canonical
3,389,817-dwelling non-district physical screen.

The source does not identify how many of these dwellings can reuse their
existing distribution under the central-hydronic air-to-water route.

P73 does not fabricate that share.

Instead it asks whether a point share is actually required.

## 2. Latent split

Define:

`x = fraction of CENTRAL_HEATING dwellings requiring NEW_OR_REPLACE distribution`.

Canonical domain:

`x in [0,1]`.

Then:

`central_nonreuse = x * 2,216,178`

`central_reuse = (1-x) * 2,216,178`.

Because P72 already qualifies all 1,173,639 NHEAT dwellings as nonreuse on this
route:

`total_nonreuse = 1,173,639 + x * 2,216,178`

`total_reuse = (1-x) * 2,216,178`.

The total is conserved for every admissible x:

`total_nonreuse + total_reuse = 3,389,817`.

## 3. Endpoint proof

At `x=0`:

- nonreuse = **1,173,639**;
- reuse = **2,216,178**;
- nonreuse share = **34.622488%**;
- reuse share = **65.377512%**.

This reproduces P72 exactly.

At `x=1`:

- nonreuse = **3,389,817**;
- reuse = **0**.

Therefore the P72 aggregate interval is exactly the image of the complete
central latent split.

No midpoint is needed.

## 4. Why point assignment is not a model blocker

For any programme metric whose outcome envelope is known separately for:

- `REUSE_EXISTING_DISTRIBUTION`; and
- `NEW_OR_REPLACE_DISTRIBUTION_REQUIRED`;

the aggregate programme metric is affine in x.

Therefore its extrema over `x in [0,1]` occur at the endpoints.

The full admissible set can be propagated without choosing a central reuse
percentage.

Canonical rule:

`POINT ESTIMATE NOT IDENTIFIED != MODEL BLOCKED`.

More specifically:

`UNKNOWN CENTRAL SPLIT + COMPLETE PATH OUTCOME BOUNDS -> BOUNDED PROGRAMME OUTPUT`.

But:

`UNKNOWN CENTRAL SPLIT + MISSING PATH OUTCOME BOUNDS -> Q`.

The blocker is then the missing **outcome response**, not the missing point
share.

## 5. What KSH CENTRAL_HEATING does and does not prove

P22's KSH topology identifies centralized heating.

It does not by itself prove:

- hydronic distribution medium;
- current flow/return temperature;
- hydraulic adequacy;
- emitter adequacy at post-retrofit target temperature;
- direct AWHP reuse readiness.

Therefore P73 does not label the 2,216,178 central dwellings as either reuse or
nonreuse.

`CENTRAL_HEATING != HYDRONIC_REUSE_READY`.

Record/archetype evidence on distribution medium and reuse adequacy remains
useful to tighten the latent set and for record-level decisions.

It is not required merely to preserve a valid conservative national bound.

## 6. Blocker effect

P72 residual:

`CENTRAL_HEATING_REUSE_VS_NONREUSE_ASSIGNMENT`.

P73:

`RETIRED_AS_POINT_BLOCKER`.

Replacement distribution residual:

- `REUSE_PATH_OUTCOME_BOUNDS`;
- `NONREUSE_PATH_OUTCOME_BOUNDS`.

Q-B02-004 also retains:

- `NON_GAS_CONVECTOR_EMITTER_INTERVENTION_ASSIGNMENT`;
- `ROOM_GRAIN_ACTION_DISTRIBUTION`;
- `MARKET_REALIZED_COST_DISTRIBUTION` only if a central/expected monetary
  estimate is required.

## 7. Non-claims

P73 does not claim:

- x = 0.5;
- any point central reuse or nonreuse share;
- CENTRAL_HEATING is always hydronic;
- all existing central distributions are reusable;
- all existing central distributions require replacement;
- the resulting wide interval is decision-useful for every metric;
- Q-B02-004 is resolved.

B02 readiness remains 55%.
