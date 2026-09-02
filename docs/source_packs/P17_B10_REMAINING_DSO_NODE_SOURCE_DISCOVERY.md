# B10-P17 — Remaining DSO node-source discovery audit

## Canonical base

`69654a5d5a0b76f4debe5a57f4a8eb29e4c57fed`

## Core rule

`SOURCE MENTIONS A SUBSTATION != CANONICAL NODE-BEARING SOURCE != COMPLETE OPERATOR NODE INVENTORY`

P17 audits the four operators left unresolved by P16. It does not weaken the P16 completeness gate and does not infer a complete inventory from project news, methodology documents, rules, maps, or generation-side capacity publications.

## Discovery result

### ELMU

Official E.ON publication found:

- https://www.eon.hu/content/dam/eon/eon-hungary/documents/kapacitaspublikacios-eljaras/1_465-Kozzeteteli-eljaras-tajekoztato-EEL.pdf

The document states that ELMU publishes available generation/feed-in connection capacities in its high-voltage and HV/MV substations. This is authoritative evidence that a node-bearing publication family exists, but it is not the consumption-side programme headroom dataset required for the B10 household electrification pathway, and it does not establish complete physical node inventory. Therefore P17 records the source family but keeps consumption-side node-source authority and inventory completeness Q.

### EON_DDASZ

The P17 official-source search did not pin a current operator-specific consumption-side node-bearing publication with stable source identity. The current 2026 Distribution Code annex family is authoritative for definitions/rules, not an operator node inventory. Status remains Q; this is not a claim that no public source exists.

### EON_EDASZ

Same bounded result as EON_DDASZ: no current operator-specific consumption-side node-bearing publication was pinned in this slice. Status remains Q; no negative availability claim is made.

### MVM_EMASZ

Official MVM sources identify individual MVM Emasz substations and projects (for example Maklar 132/22 kV, Miskolc Bogancs utca 132/22 kV, Gyongyoshalasz and Jasbereny), and the current MVM free-capacity methodology states the semantics for consumption-side substation capacity publication. These sources prove node existence/project facts only for the named nodes. P17 did not identify a current canonical MVM Emasz consumption-side node table analogous to the MVM Demasz dataset pinned in P1. Therefore the operator-wide node-bearing dataset remains Q and no inventory completeness is claimed.

Relevant official sources:

- methodology: https://mvmhalozat.hu/attachments/41913
- Maklar project: https://www.mvmhalozat.hu/aktualitasok/125150
- Miskolc project: https://mvmhalozat.hu/aktualitasok/125020

## P17 conclusion

The four-DSO blocker is refined rather than falsely cleared:

- ELMU: official generation-side node-publication family identified; consumption-side programme node source still unresolved;
- EON_DDASZ: current canonical consumption-side node source unresolved;
- EON_EDASZ: current canonical consumption-side node source unresolved;
- MVM_EMASZ: official named-node/project evidence exists, but current operator-wide consumption-side node table unresolved.

No operator receives `COMPLETE_NODE_INVENTORY_PROVEN`.

## Closure effect

P17 replaces the coarse `FOUR_DSO_NODE_SOURCE_DISCOVERY_UNRESOLVED` blocker with evidence-specific blockers:

- `ELMU_CONSUMPTION_NODE_SOURCE_UNRESOLVED`
- `EON_DDASZ_NODE_SOURCE_UNRESOLVED`
- `EON_EDASZ_NODE_SOURCE_UNRESOLVED`
- `MVM_EMASZ_OPERATOR_NODE_TABLE_UNRESOLVED`

`NO_COMPLETE_NATIONAL_DSO_NODE_INVENTORY` and `HEADROOM_NODE_SET_NOT_INVENTORY_COMPLETENESS` remain.

No topology, entity-to-node mapping, limiting-node result, survivability result, reinforcement, programme CAPEX, or readiness uplift is created.