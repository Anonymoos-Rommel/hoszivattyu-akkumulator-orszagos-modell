# B10-P8 — DSO coverage and spatial-authority boundary

## Purpose

B10-P8 creates the smallest executable authority layer required before programme
demand can enter B10-P1/P2 node-specific headroom or B10-P5 reinforcement logic.

Core rule:

`ADMINISTRATIVE LOCATION != DSO SERVICE AREA != DSO SUBSTATION != ELECTRICAL TOPOLOGY`

The slice deliberately does **not** publish a county/settlement-to-substation
crosswalk.  It separates two different propositions:

1. whether an entity/location is inside a named DSO service area;
2. whether the same entity is authoritatively bound to one exact supplying
   `DSO_SUBSTATION` node.

The first proposition cannot prove the second.

## Fresh official-source audit — 2026-09-02

### MVM Démász service-area publication

Official MVM Hálózat public-service information identifies **MVM Démász
Áramhálózati Kft.** as a licensed electricity distribution operator.  Its
service-area page states that the settlement list is contained in the operating
licence and the distribution business rules and publishes the service area by
county.

Source:

- https://mvmhalozat.hu/aram/oldalak/6454

The same page separately lists settlements where only **part of the
administrative settlement** belongs to the MVM Démász low-/medium-voltage service
area.  This is direct authority against a rule such as
`settlement == unique DSO service area`, and it is stronger still against a rule
such as `settlement == supplying substation`.

The public-service identity page is:

- https://mvmhalozat.hu/aram/oldalak/6451

This evidence can support DSO service-area membership when the exact location is
covered by the official territorial authority.  It does not identify the exact
supplying feeder or substation.

### Connection-point authority

The current consolidated `273/2007. (X. 19.) Korm. rendelet` on the Nemzeti
Jogszabálytár states that available capacity is recorded by usage location and
connection point, and that the network licensee designates the connection point
and starting point.  The network connection contract contains the technical
location of the connection point and its EOV coordinates.

Source:

- https://njt.hu/jogszabaly/2007-273-20-22

This supports the architectural distinction between ordinary administrative
location data and electrical connection/topology authority.  P8 does not infer a
substation from coordinates; coordinates are relevant only when the authoritative
network evidence explicitly binds the same entity/location to the exact network
node.

### Other DSO / national coverage

The audit searched official OPUS TITÁSZ, E.ON/ELMŰ, MVM and MEKH publication
areas for reproducible territorial and connection authority.  P8 does not claim
that a complete, normalized national DSO-territory dataset has been acquired.
National DSO coverage therefore remains open and no national crosswalk is
published.

## Executable contract

`modules/B10/spatial_authority_contract.py` exposes two independent outcomes:

Service area:

- `SERVICE_AREA_PROVEN`
- `Q_SERVICE_AREA_UNRESOLVED`

Exact electrical node:

- `EXACT_NODE_PROVEN`
- `Q_EXACT_NODE_UNRESOLVED`

Service-area proof requires referenced evidence explicitly binding:

- `DSO_SERVICE_AREA_MEMBERSHIP`;
- exact `ENTITY_ID`;
- exact `NETWORK_OPERATOR`;
- exact `SERVICE_AREA_ID`.

Exact node proof is stricter and requires referenced higher-authority evidence
explicitly binding:

- `EXACT_DSO_SUBSTATION_MAPPING`;
- exact `ENTITY_ID`;
- exact `NETWORK_OPERATOR`;
- exact `NODE_REGION_ID`;
- `NODE_REGION_GRAIN:DSO_SUBSTATION`.

An exact connection point, DSO network study, topology record or equivalent
operator evidence may satisfy this only when it explicitly makes the node
binding.  The contract never derives the node from location alone.

## Explicitly non-authoritative inputs

The following may remain useful context but cannot mint exact electrical truth:

- county or other administrative geography;
- settlement or postal location;
- household/building location alone;
- ENTSO-E Hungarian control-area identity;
- DSO service-area membership alone;
- nearest-substation or nearest-line GIS result;
- distance ranking;
- mapping confidence/probability score;
- population, household-count or consumption-share allocation.

`AMBIGUOUS_OR_MULTI_SUPPLY` evidence forces the exact node back to Q even if a
candidate node is present on the record.

## B01 and B08 boundary

Q-B01-002 remains open.  B01 may continue to carry an administrative programme
resolution and B08 may continue to carry its own source-native/control-area or
bounded-SCN region scheme.  P8 does not relabel either into DSO geography.

The B08 source-native observed-load contract remains Hungarian ENTSO-E
control-area grain.  That is not a DSO service-area series and cannot be split to
substations without separate authority.

## P1/P2/P5/P7 relationship

P8 creates no second headroom, reinforcement, CAPEX or network-layer classifier.

- P1 remains the MVM Démász source-native headroom contract.
- P2 remains the OPUS TITÁSZ source-native headroom contract.
- P5 remains the programme-incremental reinforcement/CAPEX authority gate.
- P7 remains the transmission/distribution/network-interface classifier.

`require_exact_dso_substation_mapping()` is the fail-closed handoff gate: node
specific P1/P5 use is authorized only when the P8 decision is
`EXACT_NODE_PROVEN`.

A P8 decision cannot mint:

- headroom;
- connection permission;
- reinforcement requirement;
- programme attribution;
- programme CAPEX;
- transmission/distribution classification;
- completion probability;
- readiness percentage.

## Registry and readiness outcome

P8 publishes no numerical regional-readiness row and no incremental-CAPEX row.
Therefore:

- `registry/regional_readiness.csv` remains header-only;
- `registry/incremental_capex_attribution.csv` remains header-only;
- the two P4 baseline infrastructure rows remain unchanged;
- Q-B01-002 remains OPEN;
- Q-B10-001 remains OPEN / PARTIALLY_BOUNDED;
- Q-B10-002 remains OPEN / PARTIALLY_BOUNDED;
- B10 readiness remains **15**.

Remaining work includes complete national DSO coverage, reproducible exact
programme-location-to-network-node evidence, real programme reinforcement
studies and separable incremental CAPEX.
