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

The official MVM project page identifies the exact project and beneficiary; the
official MVM completion communication dated 2026-06-15 explicitly states that
the project was successfully completed and reports its realised network scope.
The official OPUS project page identifies the exact project and operator; the
official OPUS completion communication dated 2026-06-15 explicitly states the
completed project and its realised scope.

Only the completion source is referenced by each ledger row's `source_ids` and
it explicitly supports `OPERATING` with `OBS` truth. A planning/project page,
generic company page, headroom publication or unrelated source cannot mint the
operating status. The runtime records are materialised by
`rrf_baseline_ledger.py` and classified by the existing P3
`classify_infrastructure()` function; no second classifier is introduced.

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
| MVM Démász `RRF-6.1.1-21-2022-00006` | blank | blank | Grant `42,909,187,827 HUF` and 50% rate are OBS source facts; no exact total cost is directly stated, so grant ÷ 50% is not recorded. |
| OPUS TITÁSZ `RRF-6.1.1-21-2022-00001` | `41,489,280,000 HUF` | blank | Completion source explicitly states total cost and support amount; only the total is used as baseline cost. |

Blank is not zero. The incremental registry remains header-only because this
slice attributes no heat-pump/battery programme cost.

## Capacity semantics

The MVM completion communication reports 782 MW of additional renewable/PV
generation integration capability. The OPUS project page reports 378 MW,
while the OPUS completion communication reports 261 MW. This source discrepancy
is preserved rather than collapsed into one value. These figures are not
household heat-pump consumption headroom, DSO free capacity, MGT permission,
B08 load capacity or national headroom. They are retained as source evidence
semantics only and are not placed into P1/P2 consumption-headroom fields.

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
