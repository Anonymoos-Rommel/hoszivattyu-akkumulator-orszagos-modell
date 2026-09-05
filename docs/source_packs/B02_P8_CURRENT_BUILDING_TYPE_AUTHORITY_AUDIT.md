# B02-P8 — Current 2022 building-type authority audit

**Status:** `NO CURRENT PUBLIC WBL-COMPATIBLE BUILDING-TYPE STOCK AUTHORITY IDENTIFIED / Q-B02-002 REMAINS OPEN`

**Base:** B02-P7 merged main `f100103c7a58d7570fddc7404a53397480e53a3c`

**Audit date:** 2026-09-05

## Purpose

B02-P6 added a 2016 national observed control for the existing 2015-based building-type proxy. B02-P7 closed the separate construction-period mismatch. The remaining critical question is whether an official 2022/current KSH source can supply building type at a grain that is valid for the 2022 WBL archetype linkage.

P8 audits three current official KSH source families and freezes the boundary before any further proxy promotion.

Canonical boundaries:

`2022 CENSUS QUESTIONNAIRE != BUILDING-TYPE STOCK OBSERVATION`

`CENSUS-ASSISTED TRANSACTION CLASSIFICATION != OCCUPIED-STOCK DISTRIBUTION != WBL JOINT AUTHORITY`

`CURRENT SOURCE REFERENCE != CURRENT STOCK AUTHORITY`

## 1. 2022 Census housing questionnaire

Source ID: `SRC-B02-KSH-CENSUS-QUESTIONNAIRE-2022`

Official questionnaire:
https://nepszamlalas2022.ksh.hu/media/idegennyelvu_kerdoivek/KSH_nepszamlalas_2022_angol.pdf

The published 2022 housing questionnaire asks, among other items:

- construction year;
- external wall material;
- dwelling use;
- ownership;
- room counts;
- floor area;
- water, hot water and wastewater;
- heating mode;
- heating energy source;
- equipment including heat pump.

There is no building-type question corresponding to the 2016 Mikrocenzus `1–3 dwelling residential building` versus `4+ dwelling residential building` distinction.

Therefore the 2022 Census questionnaire does not provide source-native `FAMILY_HOUSE` / `MULTI_DWELLING` stock observations.

This is a schema finding only. It does not imply that KSH has no administrative or internal building-level information elsewhere.

## 2. 2022 Census static-table publication inventory

Source ID: `SRC-B02-KSH-CENSUS-STATIC-TABLES-2022`

Official table inventory:
https://nepszamlalas2022.ksh.hu/eredmenyek/statikus-tablak

The published housing table list includes:

- dwelling counts;
- occupied-dwelling ownership;
- basic dwelling characteristics;
- equipment;
- heating mode;
- comfort.

No building-type housing table is listed in the official static-table inventory.

This proves only a public-publication boundary. It does not authorize treating the absence of a public table as evidence that no underlying building-type information exists inside KSH systems.

## 3. KSH Ingatlanadattár methodology

Source ID: `SRC-B02-KSH-REAL-ESTATE-METHODOLOGY-2026`

Official methodology:
https://www.ksh.hu/s/ingatlanadattar/modszertan

The methodology states that:

- the source is housing-market information originating from property-transfer / duty-office records;
- published records are restricted to transactions where square-metre price can be calculated because floor area is available;
- for the 2023–2024 data compilation, 2022 Census results were also used to refine building-type classification.

This is important evidence that KSH possesses a census-assisted building-type classification path. It is not, however, a 2022 occupied-dwelling stock distribution.

The transaction universe is selected by sale activity and by availability of floor-area information. It cannot be substituted for the complete occupied-dwelling WBL universe without a separately approved representativeness and calibration model.

Therefore:

`TRANSACTION BUILDING TYPE != OCCUPIED-STOCK BUILDING TYPE`

and:

`CENSUS-ASSISTED CLASSIFICATION != WBL JOIN KEY`

## Executable authority gate

The gate is implemented in:

`modules/B02/building_type_authority_gate.py`

A candidate can qualify as current building-type authority for the Q-B02-002 closure path only if all required conditions hold:

1. reference year is 2022 or later;
2. source universe is the occupied dwelling stock;
3. source grain is WBL-compatible settlement type, county × settlement type, or a finer reproducibly joinable dwelling-record grain;
4. taxonomy is compatible with the canonical `FAMILY_HOUSE` / `MULTI_DWELLING` split;
5. evidence is `OBS` or `DER`;
6. the source publishes a stock distribution;
7. a reproducible WBL-compatible join key exists.

Missing any one condition returns `Q` with an explicit reason. No candidate is promoted by source prestige, recency, or semantic similarity alone.

Machine-readable audit:

`registry/b02_current_building_type_authority_audit.csv`

All three audited source families remain `Q` for the Q-B02-002 authority gate.

## Q-B02-002 effect

`Q-B02-002` remains **OPEN**.

P8 closes an ambiguity, not the question itself:

- the 2022 Census public questionnaire does not supply building type;
- the published Census static-table inventory does not expose a building-type stock table;
- the KSH transaction database has building-type classification and uses 2022 Census information for classification refinement, but its universe is transactions, not occupied stock.

The valid next closure paths are therefore narrowed to:

1. a KSH/admin current source that directly exposes occupied-stock building type at WBL-compatible grain; or
2. an explicitly approved calibrated statistical linkage model with representativeness diagnostics and uncertainty propagation.

The current 2015-based settlement-type projection remains `ASS`.

## Other B02 gates

Unchanged:

- `Q-B02-001` remains OPEN;
- `Q-B02-004` remains OPEN;
- national technical/final eligible dwellings remain blank/Q;
- the 3,389,817 non-district-heated occupied dwellings remain a DER physical-screening reference only;
- no emitter, design-temperature, hydraulic, electrical, permit, COP, retrofit-cost or programme-eligibility claim is created.

**No readiness uplift. B02 remains 55%.**

## Provenance and reuse

The inspected sources are official KSH web publications. KSH's website reuse policy has already been recorded in B02 as CC BY 4.0 with KSH attribution required. The new source-history manifests therefore record attribution-cleared repository reuse, while exact HTML/PDF snapshots remain pending because the current connector cannot preserve exact source bytes. No SHA-256 is fabricated.
