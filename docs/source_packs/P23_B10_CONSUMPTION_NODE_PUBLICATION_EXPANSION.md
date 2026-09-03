# B10-P23 — current consumption-side node publication expansion

Status date: 2026-09-03
Canonical base: `56b26ffd3b691c85aa3f9ae6898795a894763ef7`

## Core rule

`MANDATORY PUBLICATION DUTY != PINNED PUBLICATION URL != NODE-BEARING SOURCE != COMPLETE OPERATOR NODE INVENTORY`

and

`ATTRIBUTED PUBLIC NODE FACT != COMPLETE NETWORK TOPOLOGY`

P23 follows P16-P19 and P22. It does not convert a free-capacity publication into exhaustive network topology or a complete operator inventory.

## MVM Émász — current consumption source pinned

Current official MVM Émász distribution-capacity material exposes the consumption-purpose free-capacity table:

`https://mvmemaszhalozat.hu/elmu/file/downloadfile?id=e902f961-006a-44bc-a288-31da7bb6971e`

The publication contains source-native station identifiers and station labels together with current and five-year consumption-side capacity information. P23 uses only the attributable public node-identity facts in this slice; capacity semantics remain governed separately by the B10 headroom contracts.

The prior blocker

`MVM_EMASZ_OPERATOR_NODE_TABLE_UNRESOLVED`

is therefore removed and MVM Émász becomes:

`NODE_BEARING_SOURCE_BOUNDED`

with

`Q_INVENTORY_COMPLETENESS_UNPROVEN`.

P23 materializes 45 MVM Émász source-native node identity facts in:

`registry/dso_published_node_facts_p23.csv`

Every row is `OBS`, `DSO_SUBSTATION`, `NODE_IDENTITY_PROVEN` and explicitly not a completeness claim.

## E.ON trio — discovery blocker narrowed

The current Hungarian electricity implementation framework requires distribution licensees to publish medium/high-voltage substation free-capacity information on a recurring basis from 2026. This changes the discovery question for ELMŰ, E.ON DDÁSZ and E.ON ÉDÁSZ.

P23 does **not** infer the publication URL from the legal duty and does not use search absence as evidence. The exact current 2026 consumption-side publication URL remains unresolved for the E.ON trio.

Accordingly the old generic blockers are narrowed to:

`Q_2026_MANDATORY_CONSUMPTION_PUBLICATION_URL_UNRESOLVED`

for:

- ELMŰ Hálózati Kft.;
- E.ON Dél-dunántúli Áramhálózati Zrt.;
- E.ON Észak-dunántúli Áramhálózati Zrt.

For ELMŰ, the already-proven generation-side node-publication family remains evidence that an operator node-publication mechanism exists, but it is not relabelled as the consumption-side programme source.

## What P23 proves

- MVM Démász: bounded consumption node-bearing source — unchanged;
- OPUS TITÁSZ: bounded consumption node-bearing source — unchanged;
- MVM Émász: bounded consumption node-bearing source — newly proven;
- ELMŰ/DDÁSZ/ÉDÁSZ: exact current mandatory-consumption-publication URL still unresolved;
- no operator has `COMPLETE_NODE_INVENTORY_PROVEN`;
- `registry/dso_node_inventory.csv` remains header-only.

Thus:

`THREE DSO CONSUMPTION NODE SETS != SIX DSO COMPLETE NODE INVENTORY`

## Topology boundary

Public project communications can prove bounded physical edges or named substations, but those facts must remain in a separate topology-edge evidence layer. A project statement such as a new substation being connected by splitting a named 132 kV line can support a bounded observed edge; it cannot reconstruct the complete distribution topology.

P23 therefore does not create topology, limiting-node, entity-to-node, survivability, reinforcement or CAPEX outputs.

## Closure effect

`MVM_EMASZ_OPERATOR_NODE_TABLE_UNRESOLVED` is removed from the active B10 limiting-node blocker set.

The active E.ON discovery blockers are narrowed, not cleared. `NO_COMPLETE_NATIONAL_DSO_NODE_INVENTORY`, `HEADROOM_NODE_SET_NOT_INVENTORY_COMPLETENESS`, `NO_REAL_MANAGED_PEAK_SURVIVABILITY_STUDY` and the remaining spatial/programme blockers remain.

B10 remains `IN_PROGRESS`; readiness remains **15**.
