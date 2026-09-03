# B10-P19 — public DSO fact materialization correction

Audit date: 2026-09-03
Canonical base: `a5db422f65106e2df901c33998c80e706b55600e`

## Core correction

P18 used an intentionally conservative repository-publication boundary. P19 narrows that boundary so that ordinary public facts are not treated as unusable merely because the source website or PDF carries copyright/republication terms.

The current rule is:

`PUBLIC FACT USE != SOURCE-DOCUMENT REPUBLICATION != BULK DATABASE RECONSTRUCTION`

and independently:

`SOURCE-PUBLISHED NODE SET != COMPLETE OPERATOR NODE INVENTORY`

A station name, source-native code and voltage identity publicly published by a DSO may therefore be materialized as an attributed fact when the exact fact is supported by the source. P19 still does not authorize copying the source document layout, graphics, prose or a full unrelated source database, and it does not convert a published headroom list into an exhaustive physical network inventory.

## MVM Démász

Official source:

`https://mvmhalozat.hu/attachments/41914`

Fresh 2026-09-03 text and rendered-page inspection agree on the station/code/voltage rows. P19 materializes 43 source-published node-identity rows into `registry/dso_node_inventory.csv`.

Only identity facts are materialized here:

- operator;
- service area;
- station / switching-station label;
- four-letter source code;
- voltage grain where the source distinguishes it.

The source also publishes current/five-year N-1 capacity, winter-evening demand and indicative free capacity. Those P1 headroom semantics remain separate from P19 node identity and are not used as proof of inventory completeness, connection permission, reinforcement or programme CAPEX.

## OPUS TITÁSZ

Official source:

`https://www.opustitasz.hu/storage/documents/ugyfelek/halozati-szolgaltatasok/Al%C3%A1llom%C3%A1sok_szabad_kapacit%C3%A1sai.pdf`

The current served PDF still has a revision/render disagreement:

- extracted text reports `Érvényes 2026.07.22-től` and DBDK five-year capacity `12,1 MW`;
- rendered page reports `Érvényes 2026.04.01-től` and DBDK five-year capacity `14,8 MW`.

P19 therefore does **not** choose a current capacity value or revision date.

However, the code/name node identities are common to the inspected representations. P19 materializes 48 code/name identity rows while keeping the capacity/version layer fail-closed. The two DEBR voltage-specific rows remain distinct because the source itself distinguishes `Debrecen OVIT 11 kV` and `Debrecen OVIT 22 kV`.

## Repository effect

`registry/dso_node_inventory.csv` is no longer header-only. It contains 91 attributed `NODE_IDENTITY_PROVEN` rows:

- 43 MVM Démász source-published identities;
- 48 OPUS TITÁSZ source-published identities.

This is a bounded **published node subset**, not a national node inventory.

The following remain Q:

- complete operator node population for all six DSOs;
- ELMŰ consumption-side node source;
- E.ON DDÁSZ consumption-side node source;
- E.ON ÉDÁSZ consumption-side node source;
- MVM Émász operator-wide consumption node table;
- exact household/programme entity-to-node mapping;
- managed-peak survivability;
- limiting-node claim;
- reinforcement and programme-incremental CAPEX.

## Service-area crosswalk

P19 does not yet populate `registry/dso_service_area_membership_crosswalk.csv`. The same corrected public-fact principle will be used in the next spatial acquisition increment, but KSH settlement-code normalization and partial-settlement handling remain mandatory; a settlement name alone is still not a KSH identifier and partial settlements still require usage-location authority.

## Closure effect

The old blocker `PUBLISHED_NODE_SET_REPOSITORY_MATERIALIZATION_BLOCKED` is no longer valid for atomic node-identity facts and is removed from the current B10 closure assessment.

B10 remains `IN_PROGRESS` and closure-blocked because materialized source-published node subsets do not prove complete national topology or programme-node mapping. The evidence gain is nevertheless material, so readiness moves from 15% to 20%.
