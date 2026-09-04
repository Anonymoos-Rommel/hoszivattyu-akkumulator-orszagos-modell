# B10-P26 — limiting-node authority gate

Status date: 2026-09-04
Canonical base: `4d057e20260be4ccec7ba30aaa309aea053fb25c`

## Purpose

Issue #10 requires **binding / limiting nodes** as a primary B10 output. Before P26 the repository already separated:

- exact DSO-substation programme demand;
- published headroom screening;
- managed-load and survivability authority;
- bounded topology edges;
- heterogeneous topology endpoint types and exact canonical DSO-node links.

What was still missing was an executable rule for the stronger statement:

> this exact DSO substation is a limiting / binding node for this exact network-study case.

P26 adds that rule.

## Core boundary

`PUBLISHED HEADROOM EXCEEDANCE != LIMITING NODE`

`BOUNDED TOPOLOGY EDGE != LIMITING NODE`

`TOPOLOGY ENDPOINT != LIMITING NODE`

`NETWORK SURVIVABILITY STUDY != LIMITING NODE`

`LIMITING NODE != REINFORCEMENT REQUIRED`

`LIMITING NODE != PROGRAMME-INCREMENTAL CAPEX`

The distinction is deliberate. A published headroom exceedance is a screening result. A topology edge is a physical relation. A survivability decision proves only what its claim-specific network study states. None of these facts independently proves that a particular DSO substation is the binding constraint for the programme case.

## Exact limiting-node grain

P26 accepts only:

`DSO_SUBSTATION`

The candidate node must also pass the P25 canonical DSO-node-link gate. A named line endpoint or a TSO substation endpoint cannot be silently promoted into a DSO limiting node.

## Required context

A limiting-node evaluation requires all of the following to agree exactly:

- network operator;
- network study ID;
- study case ID;
- canonical DSO-substation node ID;
- CURRENT or FIVE_YEAR horizon;
- REAL or SCN truth context;
- assessed managed peak MW;
- constraint kind;
- claim-specific source lineage.

The supplied P25 topology endpoint must be `TOPOLOGY_ENDPOINT_PROVEN`, must be typed `DSO_SUBSTATION`, and must have `CANONICAL_DSO_NODE_LINK_PROVEN` to the exact candidate node.

The supplied P10 survivability result must be `SURVIVABILITY_PROVEN`, for the same exact node and the same assessed managed peak.

P5 headroom screening is optional context. If supplied, operator, exact node and horizon must match. Its `WITHIN`, `EXCEEDS` or `Q` status is **not** part of the limiting-node proof predicate.

## Claim-specific authority

A limiting-node claim is admitted only if referenced authority-level 1–2 evidence explicitly binds:

- `NETWORK_OPERATOR:<...>`;
- `NETWORK_STUDY_ID:<...>`;
- `STUDY_CASE_ID:<...>`;
- `NODE_REGION_ID:<...>`;
- `NODE_REGION_GRAIN:DSO_SUBSTATION`;
- `HORIZON:<CURRENT|FIVE_YEAR>`;
- `TRUTH_CONTEXT:<REAL|SCN>`;
- `ASSESSED_MANAGED_PEAK_MW:<...>`;
- `CONSTRAINT_KIND:<...>`;
- and either `LIMITING_NODE` or `NON_LIMITING_NODE`.

REAL cases accept OBS/DER authority. SCN cases require SCN authority. Missing or weaker evidence returns `Q_LIMITING_NODE_UNRESOLVED` and withholds authoritative peak/constraint outputs.

The same exact study case cannot simultaneously prove both `LIMITING_NODE` and `NON_LIMITING_NODE`.

## Constraint kinds

P26 preserves four explicit constraint categories:

- `THERMAL_LIMIT`;
- `VOLTAGE_LIMIT`;
- `CONTINGENCY_LIMIT`;
- `SOURCE_STATED_UNSPECIFIED`.

`SOURCE_STATED_UNSPECIFIED` is allowed only to preserve an authoritative source that identifies a node as limiting without publishing the physical mechanism. P26 does not invent a thermal, voltage or contingency mechanism.

## Current materialization

`registry/limiting_node_assessments.csv` is intentionally header-only.

This does **not** mean there are no limiting nodes. It means the canonical repository does not yet contain a claim-specific authoritative network study that satisfies the P26 gate for a real programme node/case.

Therefore:

- `NO_REAL_MANAGED_PEAK_SURVIVABILITY_STUDY` remains;
- the limiting-node output remains unresolved;
- no B10 readiness increase is justified;
- no reinforcement or programme-CAPEX claim is created.

## Relationship to P24/P25

P24 proves only bounded topology relations.

P25 types topology endpoints and separates endpoint identity from canonical DSO-node linkage.

P26 consumes only a P25-proven DSO-substation endpoint with an exact canonical node link. This prevents named lines and TSO substations from leaking into the limiting-node output.

## Relationship to P10

P10 proves network survivability only when a claim-specific authoritative study binds the exact node and assessed managed peak.

P26 deliberately requires that P10 result but adds the stronger, separate claim:

`SURVIVABILITY_PROVEN != LIMITING_NODE_PROVEN`

A network can be survivable while still having a binding element under a particular criterion, and a source can state survivability without identifying the limiting node. P26 therefore requires explicit limiting/non-limiting authority.

## Relationship to P5

P5 explicitly states:

`PUBLISHED HEADROOM EXCEEDANCE != PROVEN REINFORCEMENT PROJECT`

P26 adds the parallel boundary:

`PUBLISHED HEADROOM EXCEEDANCE != LIMITING NODE`

Even a positive screening overload cannot mint a binding-node claim. Conversely, a within-headroom screening result cannot prove that the node is non-limiting under a full network-study case.

## Closure effect

P26 creates the missing **limiting-node authority contract** but does not populate real limiting-node evidence. The existing Issue #10 blockers therefore remain active.

B10 remains `IN_PROGRESS`; readiness remains **15%**.
