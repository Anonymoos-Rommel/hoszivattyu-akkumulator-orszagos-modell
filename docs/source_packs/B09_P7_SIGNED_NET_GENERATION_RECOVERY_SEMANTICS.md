# B09-P7 — Signed net-generation recovery semantics

**Date:** 2026-09-27  
**Parent:** B09-P6 generation missingness recovery  
**Purpose:** make the selected MAVIR net-operational recovery physically executable without corrupting sign semantics.

## 1. Problem carried from P6

P6 recovered exact official numeric values for every missing 2025 ENTSO-E A75 cell, but the selected MAVIR net-operational source contains negative values.

The previous B09 engine deliberately required:

`delivered_generation_kw >= 0`

Therefore a direct negative assignment would have violated the existing generation boundary.

The prohibited shortcuts remain:

`negative -> 0`

`negative -> abs(value)`

`negative -> positive delivered generation`

## 2. Directional signed-net representation

P7 introduces a separate boundary:

`SIGNED_NET_GENERATION_AC`

One source-native signed value `v` is represented by two non-negative directional legs:

`injection_kw = max(v, 0)`

`source_withdrawal_kw = max(-v, 0)`

and:

`net_generation_kw = injection_kw - source_withdrawal_kw = v`

Only one directional leg may be positive for one source value.

The legacy `GENERATION_AC` boundary remains non-negative and cannot carry source withdrawal.

Therefore all existing scenario and A75-positive behavior remains fail-closed and backward-compatible.

## 3. Adequacy identity

B09 now computes:

`net_generation = sum(injection - source_withdrawal)`

`residual_demand = B08_net_grid_load - net_generation`

This is the only place the source withdrawal enters the adequacy balance.

It is **not** separately added to B08 load.

That avoids double counting while preserving the signed generation-side contribution exactly.

Commission Regulation (EU) No 543/2013 Article 2(27) defines total load through the system balance of generation and imports minus exports and storage use, while Article 16 requires aggregated actual generation by production type. P7 keeps the recovery on the generation side of that balance rather than silently rewriting the load series.

## 4. Exact-missing-cell recovery contract

`modules/B09/signed_net_recovery_contract.py` is fail-closed.

It requires:

1. a complete explicit A75 source panel containing both numeric and missing cells;
2. an explicit expected Bxx production-type manifest;
3. exact PT15M Hungarian control-area grain;
4. recovery rows only for the P6-validated types:
   - B04 Fossil Gas
   - B06 Fossil Oil
   - B12 Hydro Water Reservoir
5. a recovery row for every missing A75 key;
6. no recovery row for any numeric A75 key;
7. one of the exact admitted P6 MAVIR net-operational source hashes.

Therefore:

`RECOVERY_KEYS == A75_MISSING_KEYS`

and:

`NUMERIC_A75_CELL -> CANONICAL_A75_VALUE`

## 5. Evidence status

The raw ENTSO-E and MAVIR workbooks remain external-only because public redistribution/reuse authority has not been established for the raw numeric files.

Recovered rows therefore remain qualified/Q-derived model input rather than publication-cleared OBS.

This is sufficient for model continuation under the project-wide E2 policy because:

- the official source values exist;
- exact hashes and provenance are pinned;
- the recovery transformation is deterministic;
- missing values are not synthesized;
- sign is preserved;
- numeric A75 values are never replaced.

## 6. Blocker transition

Previous:

`Q-B09-001 = E3 / MODEL_BLOCKER`

Residual:

`SIGNED_NET_GENERATION_RECOVERY_SEMANTICS_REQUIRED`

P7:

`SIGNED_NET_GENERATION_RECOVERY_SEMANTICS_REQUIRED -> RESOLVED_EXECUTABLE`

Current:

`Q-B09-001 = E2 / VALIDATION_BLOCKER / MODEL_CONTINUE`

Remaining validation/finalization debt:

- external raw artifact retention;
- public redistribution/reuse authority if raw values are to be republished;
- decision-grade provenance publication.

## 7. No broader inference

P7 does **not** claim:

- that negative net-operational values are gross plant auxiliary consumption measurements;
- that MAVIR settlement and operational measurements are interchangeable;
- that unit-level A73 is complete;
- that regional DSO/county generation is identified;
- that storage dispatch is authorized.

It only preserves the selected official signed net-operational contribution at the exact missing A75 cells.

## Official references

MAVIR publication surface:
https://rtdwweb.mavir.hu/rtdwweb/webuser/GenerateChartsServlet?hunLang=hu-hu&tabId=tab7679

ENTSO-E Actual Generation per Production Type:
https://transparency.entsoe.eu/generation/r2/actualGenerationPerProductionType/show?name=

Commission Regulation (EU) No 543/2013:
https://eur-lex.europa.eu/eli/reg/2013/543/oj/eng/pdf
