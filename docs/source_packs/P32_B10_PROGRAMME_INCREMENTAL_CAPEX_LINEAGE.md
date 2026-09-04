# B10-P32 — REAL programme-incremental CAPEX lineage gate

## Purpose

P31 proves that an exact REAL P30 limiting-node lineage is authoritatively linked to an exact P5 reinforcement-required project. P31 deliberately does not expose numeric programme-incremental CAPEX.

P32 closes the next semantic boundary: numeric programme-incremental CAPEX may enter the REAL limiting-node/reinforcement chain only when the canonical P31 decision is reproduced, the canonical P5 numeric CAPEX is reproduced from the same infrastructure record, and separate component-specific evidence explicitly binds that exact cost component and amount to the exact P31 reinforcement lineage.

## Core rules

`P31 REINFORCEMENT LINK != PROGRAMME-INCREMENTAL CAPEX`

`P5 NUMERIC CAPEX != P31-LINKED NUMERIC CAPEX`

`SAME PROJECT != SAME COST COMPONENT`

`TOTAL PROJECT COST != PROGRAMME-INCREMENTAL CAPEX`

`CUSTOMER CONNECTION CHARGE != PROGRAMME-INCREMENTAL CAPEX`

`HANDCRAFTED P31 DECISION != CANONICAL P31 AUTHORITY`

## Gate

A proven P32 result requires all of the following:

1. the supplied P31 decision exactly reproduces the canonical P31 gate from the supplied P31 link, P30 lineage and P5 infrastructure record;
2. P31 status is `REAL_LIMITING_NODE_REINFORCEMENT_LINK_PROVEN`;
3. exact equality of reinforcement-link ID, project, operator, study ID, study case, DSO-substation node and horizon;
4. the P5 infrastructure record carries the exact same project/operator/node and exact `cost_component_id`;
5. canonical P5 re-evaluation proves `REINFORCEMENT_REQUIRED` and a programme incremental/accelerated attribution;
6. canonical P5 exposes a numeric `program_incremental_capex_huf`; missing remains missing and is never converted to zero;
7. the P32 amount exactly reproduces the canonical P5 numeric amount;
8. the P32 attribution status exactly reproduces canonical P5 attribution;
9. referenced authority-level 1–3 OBS/DER evidence explicitly binds the exact P31 reinforcement lineage to the exact cost component and exact numeric programme-incremental CAPEX amount.

If any condition fails, the result is `Q_REAL_PROGRAMME_INCREMENTAL_CAPEX_LINEAGE_UNRESOLVED` and the authoritative cost component, amount and attribution are withheld.

## Cost boundaries

P32 does not weaken P5 cost semantics. In particular:

`CUSTOMER_CONNECTION_CHARGE_HUF != TOTAL_REINFORCEMENT_PROJECT_COST_HUF != PROGRAM_INCREMENTAL_CAPEX_HUF`

A total project cost, customer connection charge, generic cost authority, arbitrary smaller number or unbound cost component cannot mint programme-incremental CAPEX.

## Materialization

`registry/programme_incremental_capex_lineage.csv` is intentionally header-only.

There is currently no authoritative REAL row that simultaneously satisfies the P27–P31 programme/study/limiting-node/reinforcement chain and the P5 component-specific numeric programme-incremental CAPEX gate.

Therefore no numeric programme-incremental CAPEX is materialized by P32.

## Readiness

P32 changes contract coverage, not evidence coverage. Existing blockers remain active, including `NO_REAL_PROGRAMME_NODE_PANEL` and `NO_REAL_MANAGED_PEAK_SURVIVABILITY_STUDY`.

B10 remains `IN_PROGRESS`; readiness remains **15%**.
