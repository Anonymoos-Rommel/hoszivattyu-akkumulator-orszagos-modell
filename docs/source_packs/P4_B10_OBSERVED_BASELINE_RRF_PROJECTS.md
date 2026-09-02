# B10-P4 — Observed baseline RRF infrastructure ledger

## Scope and selection

This slice applies the canonical B10-P3 baseline/incremental contract to the
first two bounded, official project applications only:

- MVM Démász: `RRF-6.1.1-21-2022-00006`;
- OPUS TITÁSZ: `RRF-6.1.1-21-2022-00001`.

Both projects are completed network-development programmes that pre-date and
are independent of the proposed heat-pump/battery programme. Their realised
scope is therefore `WITHOUT_PROGRAM` baseline. No programme causality or
programme-incremental CAPEX is claimed.

## Source audit and status gate

The official MVM project page identifies the exact project and beneficiary and
publishes the exact grant `42,909,187,827 HUF` and 50% support rate. The official
MVM completion communication dated 2026-06-15 explicitly states successful
completion, reports the realised network scope and 782 MW realised renewable/PV
integration capability. The completion communication uses rounded financial
wording; it is not the authority for the exact grant precision.

The official OPUS project/funding page identifies the exact project/operator and
publishes exact total project cost `41,489,280,000 HUF`, exact support
`20,744,640,000 HUF`, and a 378 MW project-page capability statement. The
official OPUS completion communication dated 2026-06-15 is the OPERATING status
authority and reports 261 MW realised additional weather-dependent integration
capability. Its financial wording is rounded (`41.489` / `20.744` billion HUF),
so it cannot mint the higher-precision exact ledger cost.

Every ledger row references each source needed for its machine claims. The
completion source must explicitly support `OPERATING` with `OBS` truth. For the
OPUS exact cost, the separately referenced project/funding source must explicitly
support `COST`; completion-only provenance is insufficient. A planning/project
page, generic company page, headroom publication or unrelated source cannot mint
the operating status. The runtime records are materialised by
`rrf_baseline_ledger.py` and classified by the existing P3
`classify_infrastructure()` function; no second classifier is introduced and the
P3 cost gate is not weakened.

## Grain and asset type

The rows are umbrella DSO network-development projects, not substations. The
canonical grain is `DSO_SERVICE_AREA` with opaque IDs
`MVM_DEMASZ:SERVICE_AREA` and `OPUS_TITASZ:SERVICE_AREA`. These IDs convey only
the source-declared DSO service territory. They create no geometry, county or
settlement crosswalk, `DSO_SUBSTATION` mapping, B08/B09 handoff or national
aggregation. P4 validation explicitly prevents these rows from entering the
P1/P2 DSO-substation headroom assessment path.

The bounded asset type is
`MULTI_ASSET_DSO_NETWORK_DEVELOPMENT_PROGRAM`. Umbrella totals are not split
among substations, lines, transformers or digital assets without exact
non-overlapping component-cost authority.

## Cost treatment

| Project | Baseline cost | Programme-incremental cost | Evidence verdict |
|---|---:|---:|---|
| MVM Démász `RRF-6.1.1-21-2022-00006` | blank | blank | Project page publishes exact grant `42,909,187,827 HUF` and 50% rate; no official source in this slice directly states an exact total project cost, so grant ÷ 50% is not recorded. |
| OPUS TITÁSZ `RRF-6.1.1-21-2022-00001` | `41,489,280,000 HUF` | blank | Referenced official project/funding page explicitly states the exact total and support. Completion evidence is separately required for OPERATING and only gives rounded financial wording. |

Blank is not zero. The incremental registry remains header-only because this
slice attributes no heat-pump/battery programme cost.

## Capacity semantics

The MVM completion communication reports 782 MW realised additional renewable/PV
generation integration capability. The OPUS project page reports 378 MW as its
project-page capability statement, while the OPUS completion communication
reports 261 MW realised additional weather-dependent integration capability.
These source claims are preserved rather than collapsed or relabelled. The 378
MW figure is not called realised completion capacity.

None of these figures is household heat-pump consumption headroom, DSO free
capacity, MGT permission, B08 load capacity or national headroom. They are
retained as source evidence semantics only and are not placed into P1/P2
consumption-headroom fields. They are not added together.

## Registry and open questions

`registry/baseline_infrastructure.csv` contains exactly the two rows above.
`registry/incremental_capex_attribution.csv` remains header-only. No national
readiness row or national aggregate is added. Q-B10-001 remains
`OPEN / PARTIALLY_BOUNDED`: the contract now has two observed baseline
applications, but the complete Hungarian project inventory and all
programme-incremental CAPEX remain unproven. Q-B10-002 remains `OPEN` because
completed examples do not establish fulfilment probabilities for future
contracted, funded or tendered projects. B10 readiness remains 15.

Explicitly out of scope: all other DSOs, national scaling, county↔DSO and
ENTSO-E↔DSO/substation mappings, consumption-headroom aggregation, MGT
replacement, power-flow, reinforcement optimisation, household allocation and
any programme-induced CAPEX.
