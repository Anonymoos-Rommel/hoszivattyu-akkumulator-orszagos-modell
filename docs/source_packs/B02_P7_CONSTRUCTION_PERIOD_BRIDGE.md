# B02-P7 — WBL / KSH construction-period bridge

**Status:** `Y_GE2011 AGE-BIN HARMONIZATION EXECUTABLE / Q-B02-002 REMAINS OPEN`

**Base:** B02-P6 merged main `237573129f3c0b471624e499d6d01c3d03430770`

## Purpose

P1-G left one explicit B02 harmonization gap: the KSH Census 2022 WBL construction-period dimension uses a single `Y_GE2011` category, while the KSH experimental energy publication separates the same 2011+ horizon into `2011–2015` and `2016–2022`.

B02-P7 closes that semantic mismatch without inventing a building-type join.

Canonical boundary:

`AGE-BIN HARMONIZATION != BUILDING-TYPE JOIN != OBSERVATION UPGRADE`

and:

`DERIVED PERIOD AGGREGATION != WBL SUBCELL EVIDENCE`

## Existing source contract

The canonical KSH energy dataset is already materialized in:

- `data/processed/b02/ksh_energy_distribution_2022.csv` — 944 published `MODELLED` building-type × construction-period × primary-energy-bin rows;
- `data/processed/b02/ksh_energy_archetype_benchmarks_2022.csv` — 16 building-type × construction-period benchmark rows.

The relevant source-native periods are:

- `2011–2015`;
- `2016–2022`.

For each of the two building types (`FAMILY_HOUSE`, `MULTI_DWELLING`) both periods publish the same complete 59-bin primary-energy grid from 10 to 590 kWh/m²/year.

The WBL target category is:

- `Y_GE2011` — 2011 or later.

The two energy periods therefore partition the WBL target period exactly for reference year 2022.

## Executable bridge

The machine-readable contract is:

`registry/b02_construction_period_bridge.csv`

The executable implementation is:

`modules/B02/construction_period_bridge.py`

For every building type and identical energy bin:

`dwelling_count(Y_GE2011) = dwelling_count(2011–2015) + dwelling_count(2016–2022)`

The aggregation preserves the source building type and energy-bin grain. It does not combine `FAMILY_HOUSE` with `MULTI_DWELLING`, and it does not assign either building type to a WBL row.

## Exact canonical totals

The source benchmark counts independently imply the following 2011+ totals:

| Building type | 2011–2015 | 2016–2022 | Y_GE2011 derived total |
|---|---:|---:|---:|
| FAMILY_HOUSE | 45,682 | 102,240 | **147,922** |
| MULTI_DWELLING | 22,145 | 62,929 | **85,074** |
| **Total** | **67,827** | **165,169** | **232,996** |

The executable test derives the same totals from the full 59-bin distributions, not from these benchmark totals alone.

## Evidence status

The KSH energy distribution is `MODELLED`. Summing published MODELLED bin counts across adjacent source periods is a deterministic arithmetic transformation, therefore the bridge output is canonical `DER` with explicit `MODELLED` source lineage.

It is not `OBS`.

The bridge does not change the evidence status of WBL construction-period observations. `Y_GE2011` remains an `OBS` source-native WBL category within WBL, while the harmonized KSH energy distribution remains a separately derived lineage from MODELLED source rows.

## Fail-closed rules

The bridge rejects:

- a missing source period;
- a missing 10–590 kWh/m²/year bin;
- duplicate source rows;
- negative dwelling counts;
- source rows whose evidence status is not `MODELLED`;
- unknown building types;
- any attempt to use the bridge as WBL building-type authority.

No weighted-mean primary-energy value is made canonical in this slice. The published benchmark means are rounded source outputs; the exact, lossless operation available here is count aggregation on the aligned published energy-bin grid.

## Q-B02-002 effect

`Q-B02-002` remains **OPEN**.

B02-P7 removes the construction-period category mismatch identified in P1-G, but it does not provide the missing joint evidence required to connect building type to WBL cells.

Still missing:

- 2022/current building-type distribution at WBL-compatible grain; or
- an explicitly approved calibrated statistical linkage model with uncertainty propagation.

Therefore:

`HARMONIZED AGE CATEGORY != OBSERVED ARCHETYPE JOINT`

## Other B02 gates

Unchanged:

- `Q-B02-001` remains OPEN;
- `Q-B02-004` remains OPEN;
- national technical/final eligible dwellings remain blank/Q;
- the 3,389,817 non-district-heated dwellings remain a DER physical screening reference only;
- the 2015-based building-type projection remains `ASS`;
- no technical eligibility, COP, emitter, hydraulic or retrofit-cost inference is created.

**No readiness uplift. B02 remains 55%.**
