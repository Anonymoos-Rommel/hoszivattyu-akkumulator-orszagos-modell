# B10-P16 — National DSO node inventory gate

Status: contract/source-boundary slice. No national node inventory is claimed.

## Core rule

`PUBLISHED HEADROOM NODE SET != COMPLETE DSO NODE INVENTORY != ELECTRICAL TOPOLOGY != ENTITY-TO-NODE MAPPING != LIMITING NODE`

P1 and P2 already prove exact source-native `DSO_SUBSTATION` identities for MVM Démász and OPUS TITÁSZ headroom publications. P16 makes explicit that these row sets cannot silently become an exhaustive physical/network inventory.

## Why this slice is required

The B10 limiting-node output needs a reproducible node universe before programme demand, managed peak and survivability evidence can be assessed consistently. Operator identity (P14), service-area membership (P15), a published headroom row (P1/P2) and an exhaustive operator node population are four different claims.

A missing row in a free-capacity publication therefore means only that the node is not present in that acquired publication. It must not be interpreted as proof that the substation/node does not exist.

## Current source audit — 2026-09-02

### MVM Démász

Canonical P1 source:

- `SRC-B10-MVM-DEMASZ-CONSUMPTION-HEADROOM-2026`
- `https://mvmhalozat.hu/attachments/41914`

The current MVM distribution-capacity landing states that current and forward-looking free-capacity information is published for network-connection purposes and is indicative rather than connection authority. It exposes the MVM Démász consumption-side free-capacity publication. P1 already preserves its source-native node identity.

This establishes a node-bearing source, not an exhaustive DSO asset/topology inventory.

### OPUS TITÁSZ

Canonical P2 source:

- `SRC-B10-OPUS-TITASZ-CONSUMPTION-HEADROOM-2026`
- `https://www.opustitasz.hu/storage/documents/ugyfelek/halozati-szolgaltatasok/Al%C3%A1llom%C3%A1sok_szabad_kapacit%C3%A1sai.pdf`

The current OPUS landing publishes current and forward-looking substation free-capacity data. P2 preserves the exact `(station_code, station_name)` source row identity.

Again, this proves a node-bearing publication, not source-declared exhaustive operator node population.

### ELMŰ / E.ON DDÁSZ / E.ON ÉDÁSZ / MVM Émász

P16 does not promote a current canonical node-bearing source for these four operators. The manifest records source discovery as Q. This is deliberately not a claim that no such public data exists; it means only that no exact current source has been pinned into the canonical B10 evidence chain in this slice.

## Executable boundary

`modules/B10/dso_node_inventory_contract.py` separates:

1. exact node identity;
2. existence of a node-bearing source;
3. explicit source authority that the node population is complete;
4. national completeness across all six current DSO operators.

`NODE_BEARING_SOURCE_BOUNDED` is insufficient for `OPERATOR_NODE_INVENTORY_COMPLETE`.

National completion requires every P14 operator to have both a bounded node-bearing source and separate claim-specific completeness authority.

## Registry outcome

`registry/dso_node_inventory_sources.csv` contains exactly the six P14 operators and records current source coverage state.

Current state:

- MVM Démász: node-bearing source bounded; inventory completeness Q;
- OPUS TITÁSZ: node-bearing source bounded; inventory completeness Q;
- ELMŰ: node source discovery Q;
- E.ON DDÁSZ: node source discovery Q;
- E.ON ÉDÁSZ: node source discovery Q;
- MVM Émász: node source discovery Q.

`registry/dso_node_inventory.csv` remains header-only. P16 does not duplicate P1/P2 fixture/example rows into a purported national inventory.

## Closure effect

P16 refines the old blocker:

`NO_NATIONAL_DSO_NODE_INVENTORY`

into the more precise current blockers:

- `NO_COMPLETE_NATIONAL_DSO_NODE_INVENTORY`;
- `FOUR_DSO_NODE_SOURCE_DISCOVERY_UNRESOLVED`;
- `HEADROOM_NODE_SET_NOT_INVENTORY_COMPLETENESS`.

The limiting-node output remains Q because a complete node universe is not yet proven and no real managed-peak/survivability population exists.

## Explicit non-claims

P16 does not create:

- electrical adjacency/topology;
- feeder/transformer connectivity;
- household or programme entity to node mapping;
- hosting capacity beyond source-native P1/P2 semantics;
- a binding limiting-node result;
- reinforcement requirement;
- programme-incremental CAPEX;
- any readiness uplift.

B10 remains `B10_CLOSURE_BLOCKED`, `IN_PROGRESS`, readiness 15%.
