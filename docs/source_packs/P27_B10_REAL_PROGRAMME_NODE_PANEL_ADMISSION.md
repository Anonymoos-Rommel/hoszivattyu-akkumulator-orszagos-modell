# B10-P27 — REAL PROGRAMME NODE PANEL ADMISSION

Canonical base: `9cb957e06cebdaad309817ee023c45a53a342124`

## Core boundary

P9 proves internal completeness only for the entity and timestamp sets actually supplied to it. That is necessary but not sufficient for a real programme panel.

`P9 INTERNAL PANEL COMPLETENESS != PROGRAMME COHORT COMPLETENESS`

`SUPPLIED ENTITY SET != AUTHORITATIVE PROGRAMME COHORT`

`EXACT NODE MAPPING != COHORT COMPLETENESS`

`REAL PROGRAMME NODE PANEL != NATIONAL PROGRAMME TOTAL UNLESS SCOPE AUTHORITY SAYS SO`

`MISSING ENTITY/TIMESTAMP != ZERO`

## Why P27 exists

P10 managed-load / survivability and P26 limiting-node logic require a real programme node panel before their outputs can be treated as programme results. The current closure audit therefore carries `NO_REAL_PROGRAMME_NODE_PANEL`.

P9 already enforces:

- exact P8 DSO-substation mapping for every supplied entity;
- complete supplied entity x timestamp Cartesian panel;
- no unresolved entity silently disappearing;
- no diversity/flex substitution.

However, a complete two-entity P9 fixture remains only complete for those two supplied entities. It does not prove that those two entities are the authoritative programme cohort for the declared scope.

## P27 authority layer

P27 introduces `RealProgrammeCohortManifest` and a stronger certification decision.

The manifest must identify:

- panel ID;
- programme ID;
- cohort ID;
- exact programme scope ID;
- exact expected entity IDs;
- exact expected timestamp window;
- referenced authority evidence.

Authority level 1–3 OBS/DER evidence must explicitly support:

- `PROGRAMME_COHORT_MANIFEST`;
- panel/programme/cohort/scope bindings;
- expected entity and timestamp counts;
- each exact programme entity membership;
- each exact panel timestamp.

A list supplied by the caller is not self-authenticating.

## Certification sequence

1. Prove the authoritative REAL cohort/window manifest.
2. Compare supplied entities to the exact expected entity set.
3. Compare supplied timestamps to the exact expected timestamp set.
4. Reject SCN/mixed rows and scope mismatch.
5. Run canonical P9 aggregation.
6. Require P9 `NODE_DEMAND_PROVEN` with actual exact-node rows.
7. Only then return `REAL_PROGRAMME_NODE_PANEL_PROVEN`.

Any failure returns `Q_REAL_PROGRAMME_NODE_PANEL_UNRESOLVED` and P27 withholds the numeric P9 node result from the stronger decision.

## No zero-imputation

Missing expected entities or timestamps are recorded as gaps and make the decision Q. They are never treated as zero-load rows.

Likewise, extra entities/timestamps are rejected because the supplied panel would no longer represent the exact authoritative cohort/window.

## Truth boundary

P27 admits REAL programme panels only. Scenario panels remain legitimate P9/P10 analytical inputs, but cannot clear `NO_REAL_PROGRAMME_NODE_PANEL`.

## Materialization

`registry/real_programme_node_panels.csv` is intentionally header-only.

The repository currently has no authoritative real programme cohort manifest plus matching real entity x timestamp demand rows with exact P8 node mappings. Therefore P27 does not clear the blocker.

## Relationship to adjacent slices

- P8: exact entity-to-DSO-substation mapping authority.
- P9: internal entity x timestamp node-demand aggregation.
- P10: managed load and network survivability authority.
- P24/P25: bounded topology and typed endpoint semantics.
- P26: limiting-node authority.
- P27: authoritative REAL cohort/window admission before a P9 panel can be called a real programme node panel.

P27 does not create survivability, limiting-node, reinforcement or CAPEX claims.

## Closure state

`NO_REAL_PROGRAMME_NODE_PANEL` remains active because the canonical registry is header-only. B10 remains `IN_PROGRESS`; readiness remains 15%.
