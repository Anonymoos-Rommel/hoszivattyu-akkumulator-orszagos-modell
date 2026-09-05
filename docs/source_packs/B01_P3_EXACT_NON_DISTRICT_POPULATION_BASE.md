# B01-P3 — Exact non-district-heated occupied-dwelling population base

## Purpose

B01-P3 replaces the rounded-share approximation introduced as temporary context in B01-P2 with an exact aggregation of the already committed KSH 2022 `WBL011_HEATING_FUEL` observation cells.

Core boundary:

`OCCUPIED DWELLING != NON-DISTRICT-HEATED OCCUPIED DWELLING != TECHNICALLY ELIGIBLE HEAT-PUMP DWELLING != PROGRAMME TARGET != REAL PROGRAMME PARTICIPANT`

## Canonical national result

The committed B02 WBL011 heating/fuel projection contains exactly **7,682 returned OBS cells** and reconciles to the exact occupied-dwelling universe of **4,008,541** dwellings.

The KSH heating-mode analytical partition used by the existing B02 extractor is:

`HEAT111 + HEAT112 + HEAT12 + NHEAT`

Within that partition `HEAT12` is district heating. Direct aggregation yields:

- occupied dwellings: **4,008,541**;
- district-heated occupied dwellings: **618,724**;
- non-district-heated occupied dwellings: **3,389,817**.

Conservation is exact:

`618,724 + 3,389,817 = 4,008,541`

The **618,724** district-heating total also matches the independent exact national WBL011 control already documented in `P1B_B02_DATA_CONTRACT.md`.

## P2 approximation superseded

B01-P2 used **~3,403,746** non-district-heated occupied dwellings as a temporary `DER_FROM_ROUNDED_KSH_SHARES` estimate because it applied rounded settlement-type heating-mode shares to the national occupied-dwelling population.

P3 supersedes that value for canonical modelling:

- old rounded-share estimate: **3,403,746**;
- exact WBL011 cell aggregation: **3,389,817**;
- difference: **13,929 dwellings**.

The old value remains historical audit context only and must not be used as the current programme population reference.

## Regional materialization

`registry/b01_non_district_heated_population_2022.csv` contains:

- one exact derived row for each of the 19 counties plus Budapest;
- one national control row;
- occupied, district-heated and non-district-heated dwelling counts;
- explicit `DER` status and WBL011 source lineage.

The runtime module also preserves the finer county × settlement-type aggregation available from the committed source cells. The static registry intentionally publishes county/capital totals as the stable B01 handoff grain.

## Evidence semantics

The input cell values are KSH `OBS`. The P3 totals are `DER` because they are deterministic sums and differences of those observed cells.

P3 does **not** infer:

- heat-pump technical suitability;
- emitter compatibility or required flow temperature;
- building-envelope sufficiency;
- electrical connection adequacy;
- programme legal eligibility;
- programme participation;
- settlement or DSO service-area allocation;
- exact DSO node demand.

Therefore:

`3,389,817 NON-DISTRICT-HEATED OCCUPIED DWELLINGS != B02 TECHNICALLY ELIGIBLE STOCK`

## Utility-count boundary

Gas and electricity customer/service-point statistics are not used as dwelling counts. Their semantics differ from the KSH occupied-dwelling census universe and they remain external controls only where claim-appropriate.

## B10 handoff boundary

B10-P64 provides operational DSO geography, but P3 is still only a county/capital physical population base. It cannot be allocated to a DSO service area or exact substation without a separate spatially explicit household/settlement allocation step.

## Reproducibility

The result is reproduced entirely from committed repository data:

`data/processed/b02/ksh_wbl_joint_cells_2022.csv`

using:

`modules/B01/non_district_population.py`

The runtime fails closed on source-row count drift, non-OBS source rows, wrong occupancy context, unexpected heating-mode codes, non-positive returned counts, incomplete geography identity or failure of the three national controls.

## Current B01 state

B01-P3 closes the uncertainty around the **physical non-district-heated occupied-dwelling population base**. It does not close `Q-B01-001` or `Q-B02-001`; the technical eligible stock and real programme-selection/capacity path remain unresolved.
