# B10-P25 — topology endpoint typing and canonical DSO-node link gate

Status date: 2026-09-04
Canonical base: `582db4095dff8c45bd775392c1bee42824095b33`

## Core rules

`EDGE ENDPOINT TOKEN != DSO SUBSTATION NODE`

`DSO SUBSTATION ENDPOINT != CANONICAL DSO NODE LINK`

`TSO SUBSTATION != DSO NODE INVENTORY`

`NAMED LINE != SUBSTATION`

`TYPED ENDPOINTS != COMPLETE TOPOLOGY != CONNECTED COMPONENT`

P24 created the first bounded topology-edge layer. P25 hardens the next semantic boundary: P24 endpoint tokens are heterogeneous physical network elements and must not be fed into later graph logic as if every endpoint were a canonical DSO substation node.

## Why P25 is required

The three P24 edges already expose three distinct endpoint classes:

1. DSO substations;
2. one MAVIR/TSO substation;
3. one source-native named transmission/distribution line element.

Without explicit endpoint typing a later graph implementation could silently:

- convert the named `Füzesabony–Eger` line into a substation node;
- treat MAVIR Buj as an OPUS-owned DSO node;
- infer a canonical node identity for Nyíregyháza-Nyírjes from a project label alone;
- calculate connected components over semantically incompatible endpoint objects.

P25 prevents these promotions.

## Materialized endpoint facts

`registry/dso_topology_endpoint_facts.csv` contains the six unique P24 endpoints.

### MVM Démász — Csongrád and Szentes

The P24 project source explicitly proves the two 132/22 kV substations as physical endpoints of the 132 kV connection.

The already-materialized P19 node facts independently contain the exact node IDs:

- `MVM_DEMASZ:CSON:132KV` — Csongrád;
- `MVM_DEMASZ:SZEN:132KV` — Szentes.

Therefore both endpoints are:

- `DSO_SUBSTATION`;
- `TOPOLOGY_ENDPOINT_PROVEN`;
- `CANONICAL_DSO_NODE_LINK_PROVEN`.

This exact linkage does not prove complete operator topology, capacity, power-flow direction, limiting-node status or programme relevance.

## MVM Émász — Maklár and the named Füzesabony–Eger line

The P24 project source explicitly states that the new Maklár 132/22 kV substation was inserted into the named Füzesabony–Eger 132 kV line.

Maklár is also independently present in the P23 attributed node-fact tranche as exact node ID:

`MVM_EMASZ:MAKL`

Therefore Maklár is:

- `DSO_SUBSTATION`;
- `TOPOLOGY_ENDPOINT_PROVEN`;
- `CANONICAL_DSO_NODE_LINK_PROVEN`.

The opposite endpoint token remains the source-native named network element:

`MVM_EMASZ:FUZESABONY-EGER-LINE:132KV`

It is typed as:

- `NAMED_LINE`;
- `TOPOLOGY_ENDPOINT_PROVEN`;
- `CANONICAL_DSO_NODE_LINK_NOT_APPLICABLE`.

P25 does not invent separate Füzesabony or Eger substation identities from the line name.

## OPUS TITÁSZ / MAVIR — Buj and Nyíregyháza-Nyírjes

The P24 OPUS source explicitly states that the double-circuit high-voltage connection serving Nyíregyháza-Nyírjes starts from MAVIR's Buj 400/132 kV substation.

Buj is therefore typed as:

- `TSO_SUBSTATION`;
- operator context `MAVIR`;
- scope `HU_TRANSMISSION_SYSTEM`;
- `TOPOLOGY_ENDPOINT_PROVEN`;
- `CANONICAL_DSO_NODE_LINK_NOT_APPLICABLE`.

It is not relabelled as an OPUS node.

Nyíregyháza-Nyírjes is explicitly a 132/22 kV DSO substation endpoint in the project authority and is therefore:

- `DSO_SUBSTATION`;
- `TOPOLOGY_ENDPOINT_PROVEN`.

However, the P19 attributed OPUS node-fact tranche does not contain an exact canonical Nyíregyháza-Nyírjes node ID. P25 therefore keeps:

`Q_CANONICAL_DSO_NODE_LINK_UNRESOLVED`

No fuzzy/name-based mapping is used.

## Executable contract

`modules/B10/topology_endpoint_contract.py` separates two claims:

1. endpoint identity/type;
2. canonical DSO node linkage.

Endpoint identity requires exact authority-bound support for:

- endpoint ID;
- endpoint kind;
- operator context;
- scope;
- referenced topology edge.

A DSO endpoint may expose a canonical DSO node reference only with separate explicit `CANONICAL_DSO_NODE_LINK` evidence.

Non-DSO endpoint kinds can never carry a canonical DSO-node link:

- `TSO_SUBSTATION` → not applicable;
- `NAMED_LINE` → not applicable.

If exact endpoint authority is missing, endpoint status is `Q_TOPOLOGY_ENDPOINT_UNRESOLVED`.

If a DSO substation endpoint is proven but exact canonical node linkage is not, the endpoint remains proven while the link is withheld as `Q_CANONICAL_DSO_NODE_LINK_UNRESOLVED`.

## Graph boundary

P25 intentionally does **not** compute:

- graph connected components;
- paths;
- adjacency closure;
- inferred missing edges;
- electrical islands;
- power-flow direction;
- thermal capacity;
- headroom;
- limiting nodes.

A connected-component calculation becomes meaningful only over a future explicitly typed and adequately populated topology graph. Six typed endpoints and three bounded edges are not such a graph.

## Closure effect

P25 does not clear an existing Issue #10 closure blocker. It prevents semantic corruption in later topology processing and makes the P24 evidence safely machine-consumable.

`modules/B10/integration_closure_contract.py` therefore remains unchanged.

B10 remains `IN_PROGRESS`; readiness remains **15**.
