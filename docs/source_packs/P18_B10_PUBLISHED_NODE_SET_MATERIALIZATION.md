# B10-P18 — published node-set repository materialization audit

Audit date: 2026-09-03
Canonical base: `5ecde21c6768a73e59ff18dffc27a1d910b63f41`

## Decision

P18 does **not** populate `registry/dso_node_inventory.csv`.

The current evidence supports the existence of source-published, consumption-side
node-bearing headroom sets for MVM Démász and OPUS TITÁSZ, but it does not support
copying those full source populations into the public repository as a canonical
node inventory.

The governing rule is:

`PUBLIC SOURCE ACCESS != REUSE CLEARANCE != REPOSITORY MATERIALIZATION`

and independently:

`SOURCE-PUBLISHED NODE SET != COMPLETE OPERATOR NODE INVENTORY`

Therefore:

`KNOWN SOURCE-PUBLISHED NODES ⊂ UNKNOWN FULL DSO NODE UNIVERSE`

No missing node is interpreted as a nonexistent node.

## MVM Démász fresh audit

Canonical source:

`https://mvmhalozat.hu/attachments/41914`

The current official MVM free-capacity landing page still exposes the MVM Démász
consumption-purpose publication. A fresh 2026-09-03 inspection of the one-page PDF
confirmed that the visible render and extracted text agree on the source-native
station / four-letter code / voltage structure, including multiple voltage-grain
rows for the same station code where published.

This is sufficient to retain:

`PUBLISHED_CONSUMPTION_HEADROOM_NODE_SET`

as a bounded source semantic. It is not sufficient to establish
`COMPLETE_OPERATOR_NODE_POPULATION`.

The current MVM impressum states that the website content is copyright protected
and that use/republication requires the relevant MVM company's prior written
consent. P1 already kept the raw PDF and normalized numeric acquisition external.
P18 applies the same conservative boundary to full source-derived node-set
materialization in this public repository.

Result:

- source-published node set: bounded;
- current source text/render consistency: verified in this audit;
- public-repository reuse clearance: not established;
- repository node-row materialization: blocked/external-only;
- operator inventory completeness: Q.

## OPUS TITÁSZ fresh audit

Canonical landing page:

`https://www.opustitasz.hu/ugyfelek/halozati-szolgaltatas-es-termekek/alallomasok-szabad-kapacitasai`

Canonical linked PDF:

`https://www.opustitasz.hu/storage/documents/ugyfelek/halozati-szolgaltatasok/Al%C3%A1llom%C3%A1sok_szabad_kapacit%C3%A1sai.pdf`

P2 separately recorded a verified 2026-09-01 acquisition whose exact PDF snapshot
was effective 2026-07-22 and whose extracted/rendered controls agreed at that time.
P18 does not rewrite or invalidate that historical snapshot audit.

However, the fresh 2026-09-03 current-source inspection is not internally clean:

- the PDF text extraction reports `Érvényes 2026.07.22-től`;
- the rendered page visibly reports `Érvényes 2026.04.01-től`;
- the text extraction reports DBDK / Debrecen Délkelet five-year free capacity
  `12,1 MW`;
- the rendered page visibly reports `14,8 MW`.

This is treated as a **current source snapshot/render-text disagreement**, not as a
basis for choosing one value or silently reconciling the versions.

The OPUS legal notice also states that downloadable documents and other information
materials are copyright protected and that use beyond personal use — including
storage, copying and distribution — requires prior written consent.

Result:

- source-published node set: bounded historically by P2;
- fresh current source snapshot: Q because render/text disagree;
- public-repository reuse clearance: not established;
- repository node-row materialization: blocked/external-only;
- operator inventory completeness: Q.

## Registry effect

P18 adds:

`registry/dso_published_node_set_materialization.csv`

This registry records source-level materialization decisions only. It does not
contain station rows or capacity values.

`registry/dso_node_inventory.csv` remains header-only by design.

That is a positive fail-closed result: the repository now distinguishes

1. a node-bearing official publication;
2. an exact externally verified source snapshot;
3. legal/reuse clearance for repository materialization;
4. a repository-materialized node set;
5. complete operator node inventory.

None of those stages may silently mint the next one.

## P17 relationship

P17 remains authoritative for the four source-discovery families that were
unresolved after P16:

- ELMU: generation-side substation publication evidence exists, but consumption-side
  programme node authority remains Q;
- EON_DDASZ: current operator-specific consumption node source unresolved;
- EON_EDASZ: current operator-specific consumption node source unresolved;
- MVM_EMASZ: named-substation/project evidence exists, but no current operator-wide
  consumption node table is pinned.

P18 does not create node rows for any of those operators.

## Earlier B10 boundaries preserved

- B10-P3 baseline/programme attribution remains unchanged.
- B10-P4 observed baseline infrastructure remains unchanged.
- B10-P5 reinforcement and programme-incremental CAPEX authority remains unchanged.
- B10-P6 delivery-timing authority remains unchanged.
- P1/P2 headroom information remains indicative and `MGT_REQUIRED`.
- headroom exceedance still does not prove reinforcement.
- a published node set still does not prove an exhaustive network inventory.
- no household or programme entity is mapped to an exact node by P18.
- no limiting node, survivability result, reinforcement project or CAPEX is minted.

## Closure effect

B10 remains:

- `B10_CLOSURE_BLOCKED`;
- `IN_PROGRESS`;
- readiness `15`;
- Issue #10 OPEN.

The limiting-node path remains blocked by:

- no complete national DSO node inventory;
- unresolved consumption-side/operator-wide node sources for four DSO source families;
- no cleared repository materialization of the two currently bounded consumption
  node-set publications;
- headroom node sets not proving inventory completeness;
- no real programme managed-peak/survivability study population.

P18 deliberately creates no readiness uplift.
