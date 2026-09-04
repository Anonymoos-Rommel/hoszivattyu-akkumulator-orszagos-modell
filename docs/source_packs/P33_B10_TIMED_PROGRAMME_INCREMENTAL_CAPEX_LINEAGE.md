# B10-P33 — REAL timed programme-incremental CAPEX lineage

## Purpose

B10-P32 proves a numeric programme-incremental CAPEX amount and cost component on the exact REAL limiting-node → reinforcement lineage. B10-P11 independently proves whether a project/component CAPEX amount is reconciled to a complete cash-flow schedule.

P33 closes the missing lineage boundary between those two authorities.

## Core rules

`P32 PROGRAMME-INCREMENTAL CAPEX LINEAGE != TIMED CAPEX SCHEDULE`

`P11 TIMED_PROGRAMME_CAPEX_PROVEN != P32-LINKED TIMED CAPEX`

`SAME PROJECT/COMPONENT/AMOUNT != SAME CAPEX LINEAGE`

`DELIVERY DATE != CAPEX CASH-FLOW TIMING`

`SCN TIMED CAPEX != REAL TIMED CAPEX`

`HANDCRAFTED P32 DECISION != CANONICAL P32 AUTHORITY`

## Gate

`evaluate_real_timed_programme_incremental_capex_lineage()` requires:

1. the supplied P32 decision to reproduce the canonical P32 gate exactly;
2. P32 status `REAL_PROGRAMME_INCREMENTAL_CAPEX_LINEAGE_PROVEN`;
3. exact `capex_lineage_id`, `reinforcement_link_id`, project, operator, study, case, node, horizon and cost-component identity;
4. the P33 CAPEX amount to reproduce the P32 numeric amount;
5. canonical P5 reproduction from the same reinforcement project;
6. canonical P11 reconstruction from the same project, target/actual timing evidence and cash-flow evidence;
7. P11 status `TIMED_PROGRAMME_CAPEX_PROVEN` — `SCN_TIMED_PROGRAMME_CAPEX` is not REAL authority;
8. one exact P11 schedule ID and exact cost component whose cash-flow total reconciles to the P32/P33 programme-incremental CAPEX;
9. separate authority-level 1..3 `OBS`/`DER` evidence explicitly linking the exact P32 `capex_lineage_id` to that exact P11 `schedule_id` and amount.

A delivery target or observed completion date does not allocate CAPEX to any period. P11 cash-flow authority remains the timing authority.

## Fail-closed behaviour

Any missing or mismatched lineage remains:

`Q_REAL_TIMED_PROGRAMME_INCREMENTAL_CAPEX_LINEAGE_UNRESOLVED`

Q withholds:

- authoritative cost component;
- schedule ID;
- numeric timed programme-incremental CAPEX;
- cash-flow rows.

Missing is not zero.

## Materialization

`registry/timed_programme_incremental_capex_lineage.csv` is intentionally **header-only**.

No authoritative REAL P27 programme panel, P28 study input, complete P29 REAL survivability result, P30 limiting-node result, P31 reinforcement link, P32 numeric CAPEX lineage and P11 complete REAL cash-flow schedule are jointly materialized in the repository.

Therefore P33 adds no REAL timed CAPEX row and clears no existing B10 blocker.

`NO_REAL_PROGRAMME_NODE_PANEL`, `NO_REAL_MANAGED_PEAK_SURVIVABILITY_STUDY`, `NO_REAL_TIMED_PROGRAMME_CAPEX` and `INCREMENTAL_CAPEX_ATTRIBUTION_HEADER_ONLY` remain active.

B10 remains `IN_PROGRESS`; readiness remains **15%**.
