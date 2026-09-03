# B10-P19 — public DSO fact materialization correction

Audit date: 2026-09-03
Canonical base: `a5db422f65106e2df901c33998c80e706b55600e`

## Core correction

P18 used an intentionally conservative repository-publication boundary. P19 narrows that boundary so ordinary public facts are not treated as unusable merely because the source website or PDF carries copyright/republication terms.

The current rule is:

`PUBLIC FACT USE != SOURCE-DOCUMENT REPUBLICATION != BULK DATABASE RECONSTRUCTION`

and independently:

`SOURCE-PUBLISHED NODE SET != COMPLETE OPERATOR NODE INVENTORY`

A station name, source-native code and source-distinguished voltage identity may therefore be stored as an attributed public fact when the exact fact is supported by the DSO publication. P19 still does not authorize copying the original document layout, graphics or prose, and does not convert a published headroom list into an exhaustive physical network inventory.

## MVM Démász

Official source:

`https://mvmhalozat.hu/attachments/41914`

Fresh 2026-09-03 text and rendered-page inspection agree on the station/code/voltage rows. P19 stores 43 attributed source-published node-identity facts in:

`registry/dso_published_node_facts.csv`

The fact registry preserves:

- operator;
- service area;
- station / switching-station label;
- four-letter source code;
- voltage grain where the source distinguishes it;
- exact source lineage.

The source also publishes current/five-year N-1 capacity, winter-evening demand and indicative free capacity. Those P1 headroom semantics remain separate from P19 node identity and are not used as proof of inventory completeness, connection permission, reinforcement or programme CAPEX.

## OPUS TITÁSZ

Official source:

`https://www.opustitasz.hu/storage/documents/ugyfelek/halozati-szolgaltatasok/Al%C3%A1llom%C3%A1sok_szabad_kapacit%C3%A1sai.pdf`

The currently served PDF still has a revision/render disagreement:

- extracted text reports `Érvényes 2026.07.22-től` and DBDK five-year capacity `12,1 MW`;
- rendered page reports `Érvényes 2026.04.01-től` and DBDK five-year capacity `14,8 MW`.

P19 therefore does **not** choose a current capacity value or revision date from that disagreement.

However, the inspected representations support the same code/name node identities. P19 stores 48 attributed code/name identity facts while keeping the capacity/version layer fail-closed. The two DEBR voltage-specific rows remain distinct because the source itself distinguishes `Debrecen OVIT 11 kV` and `Debrecen OVIT 22 kV`.

## Repository effect

`registry/dso_published_node_facts.csv` contains 91 attributed `NODE_IDENTITY_PROVEN` fact rows:

- 43 MVM Démász facts;
- 48 OPUS TITÁSZ facts.

This registry is deliberately separate from `registry/dso_node_inventory.csv`, which remains header-only. The distinction is intentional:

`ATTRIBUTED PUBLISHED NODE FACT != CANONICAL COMPLETE NODE INVENTORY`

Thus P19 makes the public facts usable by later exact-node logic without silently asserting national topology completeness.

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

P19 does not alter the P18 canonical full-node-inventory closure gate. The old P18 `PUBLISHED_NODE_SET_REPOSITORY_MATERIALIZATION_BLOCKED` label continues to describe full canonical node-inventory materialization, not whether individual public facts may be cited or used.

B10 therefore remains `IN_PROGRESS`, readiness 15%, and closure-blocked. P19 is an evidence-availability correction, not a completeness claim.
