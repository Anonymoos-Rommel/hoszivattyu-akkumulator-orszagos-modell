# B05-P59 — PART_LOAD_MODULATION successor-aware readiness recalibration

**Date:** 2026-09-28  
**Canonical parent main:** `05298f284f1610e09459d2329bc3c8a7a9da9cb7`

## Purpose

P15-P58 accumulated substantial part-load, cycling, field-runtime and
fan-coil transient evidence while repeatedly preserving
`PART_LOAD_MODULATION = 45%`.

Several later slices explicitly applied `NO_MECHANICAL_READINESS_UPLIFT`.

P59 performs the deferred successor-aware component recalibration.

This slice does not create new physical evidence and does not change the
module-level B05 aggregation rule.

## 1. Why 45% is stale

The current component maturity now contains substantially more than the state
under which 45% was originally retained:

- source-native minimum modulation / minimum-capacity evidence;
- exact same-point minimum COP pairing;
- Mitsubishi bounded minimum floor surface;
- second-manufacturer Dimplex floor surface;
- current-revision Dimplex 30-point Qh/Pel/COP minimum surface;
- certified non-default Cdh / part-load bins;
- executable EN14825 standard-bin cycling method;
- explicit separation of standard-bin Cdh from hourly physical cycling;
- bounded HEM/EN15316 default-policy runtime;
- exact S2125 field cycling/modulation observations;
- exact Trane FCC06 heating transient experiments;
- state-dependent FCC06 physical response and direct runtime;
- normalized FCC06 transient mass sensitivity.

The remaining gaps are real, but they no longer justify representing the
component as only 45% mature.

## 2. Scoring rule

P59 uses 12 evidence gates with integer weights totaling 100.

States:

- `RESOLVED` — full gate credit;
- `PARTIAL` — bounded partial credit;
- `OPEN` — zero credit.

No score is inferred directly from event count, number of sources, or number
of commits.

## 3. Scorecard

| Gate | Weight | Earned | State |
|---|---:|---:|---|
| Source-native minimum modulation surfaces | 14 | 14 | RESOLVED |
| Point-paired minimum capacity/COP | 8 | 8 | RESOLVED |
| Multi-manufacturer bounded product evidence | 8 | 8 | RESOLVED |
| Certified part-load Cdh evidence | 10 | 10 | RESOLVED |
| EN14825 standard-bin cycling method | 8 | 8 | RESOLVED |
| Hourly cycling method separation | 8 | 8 | RESOLVED |
| Explicit bounded default runtime policy | 6 | 6 | RESOLVED |
| Cold/high-supply coordinate coverage | 8 | 5 | PARTIAL |
| Direct field cycling/modulation validation | 8 | 5 | PARTIAL |
| Exact FCU transient physics/direct runtime | 8 | 3 | PARTIAL |
| Product-specific heat-pump transient authority | 8 | 0 | OPEN |
| Exact FCC06 OBS transient mass binding | 6 | 0 | OPEN |
| **TOTAL** | **100** | **75** | **PARTIAL** |

## 4. Why the score is 75 rather than a higher validated range

### Cold/high-supply coverage remains partial

Dimplex current-revision floor coverage is strong and most Mitsubishi blank
cells have been classified, but exact Mitsubishi A-15/W50 remains
source-native Q.

Residual:

`EXACT_SOURCE_NATIVE_A_MINUS15_W50_2D_OPERATING_OR_PERFORMANCE_RECORD_REQUIRED`.

### Field validation remains single-system

P49 supplies exact S2125 field runtime:

- 111,264 compressor-frequency samples;
- 91,055 positive-frequency samples;
- 143 detected compressor-on runs;
- 141 sampled starts/stops.

This is material validation evidence, but:

`ONE_S2125_FIELD_SYSTEM != CROSS_PRODUCT_PART_LOAD_VALIDATION`.

### FCU transient physics is strong but not exact OBS transient closure

P56-P58 supply:

- exact Trane FCC06 product identity;
- 32 identification runs;
- explicit heating fan-speed steps;
- state-dependent `Uo(x,qw)`;
- <6% open-loop validation error;
- executable direct physical runtime;
- algebraic steady-state mass independence;
- normalized `tau/m_w` sensitivity.

But the exact experiment-cited 2010 in-coil water content/direct mass remains
unrecovered for source-bound OBS transient validation.

### Product-specific heat-pump transient evidence remains open

The exact Dimplex VDE and Mitsubishi SZU certification lineages are known, but
the required product-specific seconds-scale transient records / tau_eq evidence
are not yet canonical.

Residuals:

- `EXACT_VDE_328782_TL2_1_REPORT_CONTENT_OR_SOURCE_NATIVE_TRANSIENT_EXCERPT_REQUIRED`;
- `EXACT_PUZ_WM50_TESTED_SPECIMEN_BINDING_AND_SZU_REPORT_OR_SOURCE_NATIVE_TRANSIENT_RECORD_REQUIRED`.

These two open gates prevent P59 from treating the component as validated.

## 5. Recalibrated readiness

Canonical component update:

`PART_LOAD_MODULATION: 45 -> 75`

Status remains:

`PARTIAL`.

Q-B05-004 remains:

- OPEN;
- E2;
- VALIDATION_BLOCKER;
- MODEL_CONTINUE.

Readiness scoring does not erase the blocker residuals.

## 6. B05 overall readiness

B05 overall remains **64%**.

The repository still has no canonical mathematical aggregation from
`heat_pump_readiness.csv` component scores into the B05 row in
`module_status.csv`.

Therefore:

`PART_LOAD_COMPONENT_RECALIBRATION != B05_MODULE_READINESS_RECALIBRATION`.

P59 does not invent an aggregation rule after the fact.

## 7. Successor priorities

The scorecard makes the next high-value evidence explicit.

Zero-credit gates:

1. product-specific Dimplex/Mitsubishi heat-pump transient authority;
2. exact FCC06 study-compatible water mass for OBS transient validation.

Partial gates:

1. Mitsubishi A-15/W50 exact source-native coordinate;
2. cross-product field cycling validation;
3. fuller exact FCU transient closure.

Any future readiness increase must be justified by successor evidence against
these gates. P59 creates no automatic uplift rule.

## Governance

No private field-owner raw bytes, transfer credentials or correspondence are
published by P59.
