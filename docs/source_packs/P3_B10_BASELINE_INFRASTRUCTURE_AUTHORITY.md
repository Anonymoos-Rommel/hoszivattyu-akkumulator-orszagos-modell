# B10-P3 — Baseline Infrastructure Authority & Attribution

Status: **CONTRACTED / PARTIALLY BOUNDED**

## Purpose

B10-P3 defines the smallest canonical authority needed to distinguish existing
network infrastructure from infrastructure that can be attributed to the
heat-pump/battery programme. It does not estimate national network CAPEX or
close the complete Hungarian project inventory.

## Two-world counterfactual

All attribution is evaluated against two explicit worlds:

- `WITHOUT_PROGRAM`: what is already operating, under construction, contracted,
  or credibly funded/allocated without this programme;
- `WITH_PROGRAM`: the same world plus an explicitly evidenced programme-induced
  scope, capacity, acceleration, upsizing, or cost component.

Temporal coincidence is not causality. The forbidden shortcut is
`incremental_cost = total_project_cost`.

## Classification authority

The machine contract preserves these status distinctions:

| Status | Default treatment |
|---|---|
| `OPERATING` | baseline when identity/effective date/evidence are complete |
| `UNDER_CONSTRUCTION` | baseline when the construction authority is evidenced |
| `CONTRACTED` | baseline unless separately evidenced acceleration/upsizing exists |
| `BUDGETED_OR_ALLOCATED` | baseline candidate with funding/allocation evidence |
| `OPEN_TENDER` | unresolved; tender is not a contract or funding proof |
| `ANNOUNCED_UNFUNDED` | unresolved; announcement is not baseline proof |
| `PROGRAM_ACCELERATED_OR_UPSIZED` | only the proven difference is attributable |

`PROGRAM_INCREMENTAL` and `PROGRAM_ACCELERATED_OR_UPSIZED` are attribution
outcomes, not permission to copy the whole project cost.

## Evidence hierarchy and truth

The contract requires project identity, source references and an effective date.
Evidence is ranked: (1) regulatory/authority decision, (2) DSO/MAVIR official
plan, (3) tender/contract/funding document, (4) official project notice, then
(5) other evidence. `OBS` may describe a source-native status, but program
causality is restricted to `DER`, `SCN` or unresolved `Q`; it can never be
promoted to `OBS` merely because dates overlap.

Authority level alone is not a status proof. Baseline classification requires a
referenced high-authority item whose `supports` claim is status-specific:
`OPERATING`, `UNDER_CONSTRUCTION`, `CONTRACTED` or `FUNDED_OR_ALLOCATED`.
Announcement, tender, plan, funding, construction and operation are separate
claims; no one is inferred from another. Only evidence named in `source_refs`
can satisfy status, contractual/funding or cost gates, and record-level truth
cannot outrank the truth of the relevant referenced evidence.

Numeric cost, capacity and timing fields are accepted only when the relevant
authority explicitly supports them. Missing is not zero.

## Fresh official-source audit

The audit checked the official MEKH regulator portal, MAVIR system-operator
publication area, MVM Hálózat's 17 September 2024 network-development notice,
and OPUS TITÁSZ's 15 August 2022 RRF network-development communication. These
sources confirm that official network-development and RRF project publications
exist. They do not, as inspected, provide a complete project-level ledger that
proves causal incrementality for this programme. The MVM and OPUS communications
are therefore retained as source-audit evidence, not copied into numeric B10
baseline or CAPEX rows.

The existing MVM Démász and OPUS TITÁSZ headroom publications remain headroom
authority only. Headroom evidence cannot become project-cost evidence.

## Registry verdict and question state

`registry/baseline_infrastructure.csv` and
`registry/incremental_capex_attribution.csv` remain header-only. No placeholder
numeric row is permitted. The validator rejects any premature project-row
population in this slice and preserves the existing regional-readiness grain.

Q-B10-001 changes from **OPEN (unbounded)** to **OPEN / PARTIALLY_BOUNDED**:
classification taxonomy, evidence hierarchy, counterfactual semantics and
double-count protection are now canonical, while the complete project inventory
and numeric incremental CAPEX remain unproven. B10 readiness remains **15**.
Q-B10-002 remains **OPEN**.

## Explicit exclusions

No third DSO headroom adapter, county↔DSO crosswalk, ENTSO-E→substation mapping,
national headroom, national CAPEX estimate, power-flow, reinforcement
optimisation, household allocation, connection approval, MGT replacement,
Q-B10-001 full closure, or Q-B10-002 closure is included.

