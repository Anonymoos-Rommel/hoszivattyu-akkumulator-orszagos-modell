# B10-P29 — REAL survivability study-result admission

Canonical base: `91bacd3672ab69f9b9cba08c161f99e37fe2ca4d`

## Core boundary

`REAL MANAGED-PEAK STUDY INPUT != SURVIVABILITY STUDY RESULT`

`P10 NETWORK SURVIVABILITY != EXACT STUDY-CASE/HORIZON RESULT`

`NUMERIC PEAK MATCH != RESULT-LINEAGE BINDING`

`MISSING RESULT NODE != SURVIVABILITY`

`SURVIVABILITY STUDY RESULT != LIMITING NODE`

`SURVIVABILITY STUDY RESULT != REINFORCEMENT REQUIRED`

## Purpose

P28 proves that exact REAL managed peaks were admitted to one exact network study/case/horizon. P10 can prove a node-level `NETWORK_SURVIVABILITY` claim bound to operator, network-study ID, exact DSO-substation and assessed managed peak, but P10 predates P28 and does not bind study-case ID or horizon.

P29 closes that lineage gap.

## Gate

A P29 result is proven only when:

- P28 status is `REAL_MANAGED_PEAK_STUDY_INPUT_PROVEN`;
- every exact P28 study-input node appears exactly once in the result set;
- no extra result node exists;
- result study-input ID, operator, study ID, study-case ID and horizon exactly match P28;
- result managed peak exactly matches the P28 node peak;
- authority-level 1–2 OBS/DER evidence explicitly supports both `NETWORK_SURVIVABILITY_STUDY_RESULT` and `NETWORK_SURVIVABILITY` plus the full exact lineage;
- the same evidence also clears the canonical P10 node-level survivability gate.

Any missing/extra/duplicate/mismatched result returns `Q_REAL_SURVIVABILITY_STUDY_RESULT_UNRESOLVED` and withholds proven node results.

## Materialization

`registry/survivability_study_results.csv` is intentionally header-only.

There is still no authoritative REAL programme cohort + managed-flex panel + exact P28 study-input binding + complete authoritative survivability-result set in the repository.

Therefore:

- `NO_REAL_PROGRAMME_NODE_PANEL` remains active;
- `NO_REAL_MANAGED_PEAK_SURVIVABILITY_STUDY` remains active;
- no limiting-node claim is minted;
- no reinforcement or programme-incremental CAPEX claim is minted.

## Readiness

P29 strengthens lineage and completeness semantics only. B10 remains `IN_PROGRESS`; readiness remains 15%.
