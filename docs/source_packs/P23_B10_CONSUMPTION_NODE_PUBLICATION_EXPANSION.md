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

The prior source-manifest blocker

`MVM_EMASZ_OPERATOR_NODE_TABLE_UNRESOLVED`

is therefore cleared at the operator node-source layer and MVM Émász becomes:

`NODE_BEARING_SOURCE_BOUNDED`

with

`Q_INVENTORY_COMPLETENESS_UNPROVEN`.

P23 materializes 45 MVM Émász source-native node identity facts in:

`registry/dso_published_node_facts_p23.csv`

Every row is `OBS`, `DSO_SUBSTATION`, `NODE_IDENTITY_PROVEN` and explicitly not a completeness claim.

## 2026 publication duty — exact legal authority

P23 separately registers the current legal authority in:

`registry/dso_consumption_publication_authorities.csv`

The primary source is the current consolidated text of 273/2007. (X. 19.) Korm. rendelet:

`https://njt.jog.gov.hu/jogszabaly/2007-273-20-22`

The relevant claims are distinct:

- 8. § (7) requires a distribution licensee to publish on its website, at least quarterly, medium/high-voltage substation current free transformer capacity, five-year likely free capacity, capacity tied up by ongoing connection procedures, constrained/flexible-connection substations or areas, and the methodology used to determine those values;
- the same provision explicitly makes the published information indicative rather than a connection entitlement;
- 126/A. § (6) makes the 8. § (7) duty applicable at medium and high voltage from **2026-01-01**; low-voltage publication follows from 2027-01-01.

Therefore the legal duty is `OBS` authority. It does **not** identify an operator-specific file URL by itself.

## E.ON trio — exact URL blocker remains

For ELMŰ, E.ON DDÁSZ and E.ON ÉDÁSZ the current 2026 publication duty is now proven from primary law.

P23 performed targeted official-domain and indexed-document searches for the exact current consumption-side publication file/page. The exact URL was not pinned in the auditable web representation.

This is deliberately **not** converted into a negative claim. In particular:

`SEARCH ABSENCE != PUBLICATION ABSENCE != NON-COMPLIANCE`

The exact current URL therefore remains:

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
- ELMŰ/DDÁSZ/ÉDÁSZ: 2026 publication duty proven, exact current consumption-publication URL unresolved;
- no operator has `COMPLETE_NODE_INVENTORY_PROVEN`;
- `registry/dso_node_inventory.csv` remains header-only.

Thus:

`THREE DSO CONSUMPTION NODE SETS != SIX DSO COMPLETE NODE INVENTORY`

## Topology boundary

Public project communications can prove bounded physical edges or named substations, but those facts must remain in a separate topology-edge evidence layer. A project statement such as a new substation being connected by splitting a named 132 kV line can support a bounded observed edge; it cannot reconstruct the complete distribution topology.

P23 therefore does not create topology, limiting-node, entity-to-node, survivability, reinforcement or CAPEX outputs.

## Closure effect

At the node-source manifest layer, `MVM_EMASZ_OPERATOR_NODE_TABLE_UNRESOLVED` is cleared.

The E.ON discovery problem is narrowed from generic source discovery to the exact 2026 publication-URL gate. `NO_COMPLETE_NATIONAL_DSO_NODE_INVENTORY`, `HEADROOM_NODE_SET_NOT_INVENTORY_COMPLETENESS`, `NO_REAL_MANAGED_PEAK_SURVIVABILITY_STUDY` and the remaining spatial/programme blockers remain.

B10 remains `IN_PROGRESS`; readiness remains **15**.
