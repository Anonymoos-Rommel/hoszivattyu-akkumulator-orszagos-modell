# B10-P28 — REAL managed-peak network-study input admission

Canonical base: `ed84f59f0ab7ab62491a4d3c45654707dcc7f673`

## Core boundary

`REAL PROGRAMME NODE PANEL != MANAGED PEAK STUDY INPUT`

`P10 MANAGED NODE LOAD != NETWORK STUDY INPUT`

`NUMERIC PEAK MATCH != STUDY-CASE BINDING`

`STUDY INPUT != NETWORK SURVIVABILITY RESULT`

`STUDY INPUT != LIMITING NODE`

`MISSING STUDY NODE != NON_LIMITING NODE`

## Why P28 exists

B10-P9 proves only the internal entity-by-timestamp completeness of the panel supplied to it. B10-P27 adds the stronger outer gate that the supplied REAL entities and timestamps exactly equal an authoritative programme cohort/window.

B10-P10 can then calculate a managed exact-node programme load from exact flex lineage. That result is still not proof that a DSO/network study actually used those peaks as its study inputs.

P28 closes that remaining admission gap.

## Admission sequence

A REAL managed-peak study input can be proven only through the following chain:

1. the study-input record must identify one exact `network_study_id`, `study_case_id` and `CURRENT`/`FIVE_YEAR` horizon;
2. panel, programme, cohort and scope IDs must exactly match the P27 cohort manifest;
3. P27 must return `REAL_PROGRAMME_NODE_PANEL_PROVEN` for the exact supplied demand rows;
4. P10 must return `MANAGED_NODE_LOAD_PROVEN` for the exact same demand rows plus the exact flex panel;
5. the P10 unmanaged result must equal the P27-certified P9 result, preventing substitution of another internally complete panel;
6. authority-level 1–2 OBS/DER evidence must explicitly bind the P27 panel to the exact network study/case/horizon;
7. each exact DSO-substation node and its exact managed peak MW must be explicitly bound as a study input.

If any step is absent, P28 returns `Q_REAL_MANAGED_PEAK_STUDY_INPUT_UNRESOLVED` and withholds all numeric study-input nodes/peaks.

## Evidence semantics

The network-study input authority must explicitly support the case-level bindings:

- `MANAGED_PEAK_STUDY_INPUT`;
- `STUDY_INPUT_ID:<id>`;
- `NETWORK_OPERATOR:<operator>`;
- `NETWORK_STUDY_ID:<study>`;
- `STUDY_CASE_ID:<case>`;
- `PANEL_ID:<panel>`;
- `PROGRAMME_ID:<programme>`;
- `COHORT_ID:<cohort>`;
- `SCOPE_ID:<scope>`;
- `HORIZON:CURRENT|FIVE_YEAR`;
- `TRUTH_CONTEXT:REAL`;
- `NODE_REGION_GRAIN:DSO_SUBSTATION`;
- `EXPECTED_NODE_COUNT:<n>`.

For every admitted node the source must also bind:

- `STUDY_NODE:<node_id>`;
- `MANAGED_PEAK_MW:<node_id>:<peak_mw>`.

A coincidentally equal numeric peak from another panel, another study case or another horizon is not admissible.

## What P28 does not prove

Even `REAL_MANAGED_PEAK_STUDY_INPUT_PROVEN` does **not** prove:

- network survivability;
- thermal adequacy;
- voltage adequacy;
- contingency adequacy;
- a limiting or non-limiting node;
- reinforcement requirement;
- reinforcement scope or timing;
- programme-incremental CAPEX.

Those remain separate downstream claims under P10, P26 and P5/P11.

## Current materialization

`registry/managed_peak_study_inputs.csv` remains header-only.

The repository still has no authoritative REAL programme cohort plus matching real entity×timestamp demand/flex panel and no authoritative network-study source that binds those exact managed peaks into an exact study case. Therefore:

- `NO_REAL_PROGRAMME_NODE_PANEL` remains active;
- `NO_REAL_MANAGED_PEAK_SURVIVABILITY_STUDY` remains active;
- no limiting-node output is populated;
- no reinforcement or programme-incremental CAPEX is minted.

## Readiness

P28 strengthens the evidence boundary but does not populate a real study input or clear an existing closure blocker. B10 remains `IN_PROGRESS`; readiness remains 15%.
