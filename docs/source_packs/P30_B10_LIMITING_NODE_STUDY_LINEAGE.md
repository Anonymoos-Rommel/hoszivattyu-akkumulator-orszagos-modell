# B10-P30 — REAL limiting-node study-lineage gate

Canonical base: `168d1e8f4e95398cc51249d01ab4e50790d491c2`

## Core boundary

`P10 SURVIVABILITY_PROVEN != P29 COMPLETE STUDY RESULT`

`P26 LIMITING_NODE_PROVEN != P29-LINKED REAL LIMITING NODE`

`SAME NODE/PEAK != SAME STUDY/CASE/HORIZON LINEAGE`

`P29 SURVIVABILITY STUDY RESULT != LIMITING/NON-LIMITING NODE`

`MISSING P29 NODE RESULT != NON_LIMITING NODE`

`LIMITING NODE != REINFORCEMENT REQUIRED`

## Why P30 exists

P26 is the canonical limiting/non-limiting node authority gate. Its design is correct for claim-specific node classification, but it predates P28/P29 and therefore accepts a P10 `NetworkSurvivabilityDecision` directly as its survivability prerequisite.

After P29, REAL programme reasoning has a stronger required lineage: the survivability node result must come from a complete P29 result set that itself is tied to the exact P28 managed-peak study input, study ID, study case, horizon and managed peak.

Without P30, a caller could bypass that stronger lineage by supplying another P10 `SURVIVABILITY_PROVEN` object with the same node/peak pair.

## P30 contract

`evaluate_real_limiting_node_study_lineage()` therefore requires:

1. a REAL `LimitingNodeRecord`;
2. the canonical P25 topology endpoint context required by P26;
3. a P29 `REAL_SURVIVABILITY_STUDY_RESULT_PROVEN` decision;
4. exact operator, study ID, study-case ID and horizon equality between P26 and P29;
5. the exact candidate node to be uniquely present in the P29 complete result set;
6. exact managed-peak equality between the P26 candidate and the P29 node result;
7. canonical P26 evaluation using the exact legacy P10 survivability decision carried by that P29 node result.

P30 does not alter P26's claim-specific proof predicate. It only closes the REAL programme-lineage bypass.

## Fail-closed semantics

The following remain Q and withhold both the P29 result ID and P26 decision:

- P29 result unresolved;
- operator/study/case/horizon mismatch;
- missing or non-unique P29 node result;
- peak mismatch;
- canonical P26 Q or rejection.

A missing P29 node result is not evidence of a non-limiting node.

## Scope

P30 is REAL-only. Existing SCN P26 analysis remains separate and is not promoted to REAL programme evidence.

Even a proven P30 limiting-node lineage does not prove reinforcement requirement, reinforcement project, cost, or programme-incremental CAPEX. Those remain separate downstream claims.

## Materialization

`registry/limiting_node_study_lineage.csv` is intentionally header-only.

There is still no authoritative REAL programme panel + managed-flex panel + exact study input + complete survivability result + claim-specific limiting-node evidence chain materialized in the repository.

Therefore:

- `NO_REAL_PROGRAMME_NODE_PANEL` remains active;
- `NO_REAL_MANAGED_PEAK_SURVIVABILITY_STUDY` remains active;
- no REAL limiting-node lineage row is populated;
- no reinforcement or programme-incremental CAPEX is minted.

## Readiness

P30 strengthens lineage only. It clears no existing blocker and does not materialize a real national/regional result. B10 remains `IN_PROGRESS`; readiness remains 15%.
