# B10-P31 — REAL limiting-node → reinforcement lineage gate

Canonical base: `c36a98a9d9f77c4ce99cf89fc6466c6b1bbc2138`

## Core rules

`REAL LIMITING NODE != REINFORCEMENT REQUIRED`

`SAME NODE/HORIZON != SAME REINFORCEMENT DETERMINATION`

`P30 LIMITING-NODE LINEAGE != P5 REINFORCEMENT PROJECT`

`P5 REINFORCEMENT_REQUIRED != STUDY-CASE LINK`

`REINFORCEMENT REQUIRED != PROGRAMME-INCREMENTAL CAPEX`

## Purpose

P30 proves that a REAL limiting-node conclusion consumes the exact P29/P28
study/case/horizon lineage. P5 separately proves whether a specific exact-node
infrastructure project has authoritative `REINFORCEMENT_REQUIRED` support, and
then separately handles programme attribution and numeric CAPEX authority.

Those two facts are still not the same claim.

P31 adds a narrow outer lineage gate. It requires authoritative evidence that
explicitly links the exact P30 limiting-node study/case/survivability-result
lineage to one exact P5 reinforcement project.

## Admission sequence

A P31 REAL link requires:

1. P30 `REAL_LIMITING_NODE_LINEAGE_PROVEN`;
2. exact `network_operator` match;
3. exact `network_study_id` match;
4. exact `study_case_id` match;
5. exact DSO-substation node match;
6. exact `CURRENT` / `FIVE_YEAR` horizon match;
7. exact P29 `survivability_result_id` match;
8. exact P5 project ID/operator/node/grain match;
9. authority-level 1–2 OBS/DER evidence supporting both
   `LIMITING_NODE_REINFORCEMENT_LINK` and `REINFORCEMENT_REQUIRED`, with all
   study/project bindings above;
10. successful canonical P5 evaluation with
    `reinforcement_required_proven = True`.

A limiting node by itself cannot satisfy step 9 or step 10.

## What P31 preserves from P5

P31 preserves the canonical P5 attribution status only after the exact
reinforcement link is proven. It does **not** expose or create numeric CAPEX.

Therefore:

`LIMITING NODE != REINFORCEMENT REQUIRED != PROGRAMME CAUSALITY != PROGRAMME-INCREMENTAL CAPEX`

A project may be reinforcement-required and still have unresolved programme
attribution or unquantified incremental cost. Conversely, headroom exceedance,
limiting-node status, topology, or a generic project notice cannot create a
reinforcement project or programme CAPEX.

## Materialization

`registry/limiting_node_reinforcement_lineage.csv` is intentionally **header-only**.

No authoritative REAL programme panel / managed-flex study chain / complete
survivability result / limiting-node lineage / exact reinforcement-project link
is currently materialized.

`NO_REAL_PROGRAMME_NODE_PANEL` remains active.
`NO_REAL_MANAGED_PEAK_SURVIVABILITY_STUDY` remains active.
No reinforcement project or programme-incremental CAPEX row is added.

B10 remains `IN_PROGRESS`; readiness remains **15%**.
