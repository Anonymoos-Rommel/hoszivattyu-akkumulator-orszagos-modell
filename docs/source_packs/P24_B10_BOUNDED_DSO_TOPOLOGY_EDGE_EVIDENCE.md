# B10-P24 — bounded DSO topology-edge evidence

Status date: 2026-09-03
Canonical base: `888f47495159b5b721748cfc30b0af88f43b90ce`

## Core rule

`PUBLIC PROJECT FACT CAN PROVE BOUNDED TOPOLOGY EDGE`

but

`BOUNDED TOPOLOGY EDGES != COMPLETE DSO TOPOLOGY`

and independently:

`TOPOLOGY EDGE != POWER FLOW DIRECTION != THERMAL CAPACITY != HEADROOM != LIMITING NODE != PROGRAMME REINFORCEMENT REQUIREMENT != PROGRAMME-INCREMENTAL CAPEX`

P24 creates the first explicit topology-evidence layer in B10. It does not infer missing edges, reconstruct an operator graph from geographic proximity, or translate settlement names into nodes without source authority.

## Exact evidence boundary

A P24 edge is admitted only when an official operator, MVM group technical executor, TSO/regulator or equivalent authoritative project source explicitly binds the relevant physical relation. The registry preserves the source-native relation at the precision actually stated by the source.

A named line is not silently rewritten into endpoint substations. A cross-operator endpoint is not silently reassigned to the DSO. Project ownership, power-flow direction, thermal rating, current headroom and limiting-node status are all separate claims.

## MVM Démász — Csongrád–Szentes 132 kV connection

Official MVM XPert source:

`https://xpert.mvm.hu/hu-HU/Hirek/20240701_CsongradSzentes132kV`

The project communication states that, for MVM DÉMÁSZ Áramhálózati Kft., a 132 kV overhead/cable connection is being constructed between the **Csongrád 132/22 kV** and **Szentes 132/22 kV** substations. It gives the overhead route length as 16 km 831 m.

P24 therefore records one bounded `SUBSTATION_TO_SUBSTATION_LINE` at 132 kV between the already source-published Csongrád and Szentes DSO substation identities.

Source ID:

`SRC-B10-P24-MVM-DEMASZ-CSONGRAD-SZENTES-132KV-2024`

This proves the bounded physical connection only. It does not prove line rating, N-1 capability, available headroom, power-flow direction or programme relevance.

## MVM Émász — Maklár insertion into the Füzesabony–Eger line

Official MVM Émász source:

`https://www.mvmhalozat.hu/aktualitasok/125150`

The 2026 project communication states that a new **132/22 kV** substation was built at Maklár and that an additional **132 kV line section** was constructed through which the **Füzesabony–Eger** transmission line was inserted into the new substation.

P24 deliberately preserves this as:

- endpoint A: exact Maklár DSO substation identity;
- endpoint B: source-native named network element `Füzesabony–Eger line`;
- edge kind: `SUBSTATION_INSERTION_INTO_NAMED_LINE`;
- voltage: 132 kV.

It does **not** invent separate Füzesabony and Eger substation endpoints from the line name.

Source ID:

`SRC-B10-P24-MVM-EMASZ-MAKLAR-132KV-2026`

## OPUS TITÁSZ — Buj–Nyíregyháza-Nyírjes 132 kV connection

Official OPUS TITÁSZ source:

`https://www.opustitasz.hu/tarsasagunk/sajtokozlemenyek-hirek/sajtokozlemenyek/atadtak-az-orszag-egyik-legnagyobb-aramhalozati-alallomasat`

The source states that the double-circuit high-voltage line connected to the **Nyíregyháza-Nyírjes** substation starts from MAVIR's **Buj 400/132 kV** substation and extends for more than 32 km.

P24 records the 132 kV physical relation with the TSO endpoint preserved as `MAVIR:BUJ:400/132KV`. This does not imply that Buj is an OPUS-owned node, nor does it convert the cross-operator interface into a complete topology or capacity statement.

Source ID:

`SRC-B10-P24-OPUS-TITASZ-BUJ-NYIRJES-132KV-2025`

The same broad project family is also consistent with the Hungarian Government's official Nyíregyháza industrial-park network-development decision, which separately names Buj 400/132 kV reinforcement and Nyíregyháza-Nyírjes 132/22 kV development. P24 does not need that secondary authority to mint the edge because the operator source already states the physical relation exactly.

## Materialized facts

`registry/dso_topology_edge_facts.csv` contains exactly three first-tranche observed topology facts:

- MVM Démász: Csongrád ↔ Szentes, 132 kV;
- MVM Émász: Maklár ↔ named Füzesabony–Eger line, 132 kV;
- OPUS TITÁSZ: MAVIR Buj ↔ Nyíregyháza-Nyírjes, 132 kV.

Every row is `OBS` and `TOPOLOGY_EDGE_PROVEN`.

These three facts are intentionally **not** a topology inventory. The absence of another edge in this registry means only that P24 did not materialize it.

## Contract behavior

`modules/B10/dso_topology_edge_contract.py` requires exact authority-bound:

- operator/service-area identity;
- edge ID;
- endpoint A;
- endpoint B;
- edge kind;
- voltage;
- source lineage.

Authority level 1–3 OBS/DER evidence can prove a bounded edge only when all required support tokens are explicit. Otherwise the decision is `Q_TOPOLOGY_EDGE_UNRESOLVED` and authoritative endpoints/voltage are withheld.

This prevents:

- settlement-proximity topology inference;
- automatic settlement-to-node conversion;
- missing-edge completion;
- project communication → complete operator graph promotion.

## Closure effect

P24 adds real topology evidence but does not clear any current Issue #10 closure blocker by itself. In particular it does not create:

- complete national DSO topology;
- complete national DSO node inventory;
- real programme entity-to-node panel;
- managed-peak survivability result;
- limiting-node result;
- reinforcement requirement;
- programme-incremental CAPEX.

Therefore `modules/B10/integration_closure_contract.py` is intentionally unchanged in this slice: no existing blocker is falsely removed or refined merely because three bounded physical relations are now known.

B10 remains `IN_PROGRESS`; readiness remains **15**.
