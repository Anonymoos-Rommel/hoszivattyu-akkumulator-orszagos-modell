# B05-P53 — S2125 DHW-origin active-defrost branch

**Date:** 2026-09-27  
**Canonical parent main:** `db517eb2b1ffea64d8b136a72986f337fba0c1ae`

## Purpose

P50 proved that pre-DHW active-defrost events do not behave electrically like the primary HEAT branch, but it intentionally left:

`DHW_DEFROST_BRANCH_REQUIRED`

P53 resolves that exact-system branch without pooling it with HEAT and without converting one state-window number into a universal full-cycle penalty.

The owner raw bytes remain **EXTERNAL_ONLY**.

## 1. Reproduction gate

P53 operates on the exact pinned P49 archive/member identities already re-materialized and verified in P52.

Before introducing any new DHW interpretation, P53 reproduces P50:

- matched DHW events: **46**
- direct active-state electrical event-minus-control median:
  **-0.01840895219596715 kWh/event**

It also reproduces the P50 strict HEAT branch and signed HEAT event result during the local analysis, confirming that the same matching/integration semantics are in use.

## 2. Primary DHW branch

P53 does not make the relaxed P50 DHW set primary.

Primary branch:

- strict P50 pre-state calipers only;
- exact pre-mode = DHW;
- same +/-14 day matching window;
- clean Defrost=0 control window;
- no non-zero Defrost within +/-20 minutes around candidate start;
- stable DHW control mode;
- compressor positive for at least 80% of control;
- source qheat positive for at least 70%;
- 3-5 nearest controls;
- Victron measured-time coverage >=98%.

Result:

- strict DHW events: **35**
- all matched sensitivity: **46**

## 3. Active-state electrical result

Strict DHW n=35:

- median direct electrical delta: **-0.0198199906391567 kWh/event**
- mean: **-0.022273809092797428 kWh/event**
- p05: **-0.08859835238254066**
- p95: **+0.0689657319951354**

10,000-draw event bootstrap, fixed seed 20260927:

- median 95% CI:
  **-0.0585694121214747 .. -0.0053369687204228 kWh**
- mean 95% CI:
  **-0.03847398365828543 .. -0.004375578152612496 kWh**

All matched n=46 reproduces the P50 median:

- median: **-0.01840895219596715 kWh**
- median bootstrap 95% CI:
  **-0.03238244060902125 .. +0.000139193853206**
- mean: **-0.01863156944006356 kWh**
- mean bootstrap 95% CI:
  **-0.03339751471191761 .. -0.003122585692059247**

The strict branch is therefore the primary exact-system result. The broader matched median CI narrowly touches zero and is retained as sensitivity rather than hidden.

## 4. DHW hidden-state audit

Because P50 did not include tank temperature in the HEAT-oriented matching vector, P53 explicitly attacks BT6 as a potential hidden DHW state.

Adding pre-BT6 calipers while retaining the P50 strict dimensions gives:

| BT6 caliper | supported events | median electric delta |
|---|---:|---:|
| +/-0.5 C | 23 | -0.024561 kWh |
| +/-1.0 C | 27 | -0.024983 kWh |
| +/-1.5 C | 30 | -0.026444 kWh |
| +/-2.0 C | 32 | -0.025705 kWh |

Therefore the negative active-state electrical delta is not removed by explicit tank-state matching.

No BT6 caliper is promoted to a universal model rule from this single installation.

## 5. The key DHW routing result

The pre-five-sample mode is DHW, but the thermal path during active defrost is usually not.

Within the strict n=35 active windows:

- QN10 DHW share <=0.1: **32 events**
- QN10 DHW share >=0.9: **3 events**

Across all matched n=46:

- diverted: **42**
- retained: **4**

Therefore:

`PRE_DEFROST_DHW_STATE != DHW_THERMAL_PATH_DURING_ACTIVE_DEFROST`

This makes it invalid to take the P50 HEAT signed-thermal shortfall and simply rename it a DHW thermal penalty.

## 6. Immediate DHW-state resumption

After the active Defrost=1 endpoint:

- **34/35** strict events return to QN10 DHW>=0.9 with compressor>0 either at the first post-event sample or within **1.0333 min**;
- one strict event does not show that return within the 90-minute observation search.

This is direct exact-system state evidence, not a fleet recovery-time model.

## 7. Source-native DHW energy counter

P53 uses source-native register **1583 — Brauchwasser, nur Verdichter** as a positive-domain cumulative DHW energy counter.

Global source audit:

- adjacent source differences inspected: **111,263**
- negative steps: **0**
- positive increments are quantized at **0.1 kWh**

The register is therefore suitable for bounded positive-domain window-delta comparisons.

It is **not** a signed thermal meter.

### Strict active-state service comparison

For the 35 strict DHW-origin events:

- median event-window register increment: **0.5 kWh**
- median matched-control increment: **0.8000000000001819 kWh**
- matched-control minus event median: **0.20000000000027285 kWh**
- mean shortfall: **0.31142857142857405 kWh**
- p05/p95: **0.0 .. 0.75 kWh**

Bootstrap median 95% CI:

**0.20000000000027285 .. 0.3999999999996362 kWh**

Because the source register resolution is 0.1 kWh, P53 does not claim sub-0.1 kWh physical precision from these decimal representations.

This creates the central DHW interpretation:

> During the active state, whole-system electrical energy can be slightly lower than matched normal DHW operation while the source-native DHW energy counter accumulates materially less DHW energy.

Therefore:

`DHW_ACTIVE_STATE_ELECTRIC_DELTA != DHW_SERVICE_EFFECT`

and neither quantity is a full-cycle penalty.

## 8. Source-native DHW counter recovery

P53 follows the strict n=35 events minute-by-minute out to 90 minutes.

A sustained counter recovery is called only when:

- cumulative matched DHW counter shortfall is <=0;
- for five successive minute checkpoints;
- no new non-zero Defrost contaminates the event trajectory;
- at least three original matched controls remain clean.

Result:

- observed sustained recovery before censoring: **26/35**
- censored/not recovered under the clean contract: **9**

Recovered subset:

- median recovery time after active-state endpoint: **14.5 min**
- bootstrap median 95% CI: **8.5 .. 17.5 min**
- p05/p95: **3.0 .. 49.75 min**

For the 9 censored/not-recovered events, maximum clean horizon:

- median: **19 min**
- p75: **25 min**
- p90: **30.6 min**

Therefore:

`OBSERVED_DHW_COUNTER_CATCHUP_SUBSET != FLEET_RECOVERY_DISTRIBUTION`

## 9. Why no signed DHW thermal DER is admitted

P50's signed factor was calibrated on positive-domain non-defrost HEAT.

P53 separately tests the same physical form on positive-domain non-defrost DHW samples:

- calibration n: **7,241**
- median factor:
  **0.0707213578500707 kW/(L/min*K)**
- factor p25/p75:
  **0.06911764705882353 .. 0.07285714285714286**

March temporal holdout:

- n: **3,992**
- MAE: **0.319916743 kW**
- MAPE: **6.346324%**
- R2: **-3.891217**

Together with the observed QN10 path change during active defrost, this is not a sufficient basis for a signed DHW heat-removal model.

P53 therefore uses the source-native positive-domain DHW counter and leaves signed negative thermal removal **NOT_ADMITTED**.

## 10. Admission result

P53 resolves:

`DHW_DEFROST_BRANCH_REQUIRED`

to:

`RESOLVED_FOR_EXACT_SYSTEM_ACTIVE_DHW_ORIGIN_AND_SOURCE_NATIVE_COUNTER_BRANCH`

Admitted for this exact installation:

- strict pre-DHW active-defrost electrical effect;
- P50 matched-DHW reproduction;
- BT6 hidden-state sensitivity;
- direct QN10 route-switch structure;
- source-native DHW cumulative-energy active-window shortfall;
- bounded censored source-counter recovery evidence.

Not admitted:

- one universal DHW defrost constant;
- signed DHW heat-removal kWh;
- universal full-cycle DHW electrical penalty;
- cross-product or Hungarian event-frequency transfer.

## 11. Q-B05-003 after P53

Q-B05-003 remains:

**E2 / VALIDATION_BLOCKER / MODEL_CONTINUE**

Residuals:

- `RECOVERY_TAIL_CENSORING_AND_FULL_CYCLE_PARAMETER_ADMISSION_REQUIRED`
- `PASSIVE_INCREMENTAL_ELECTRIC_AND_THERMAL_DOMAIN_VALIDATION_REQUIRED`
- `STATE_CONDITIONED_PREDICTIVE_MODEL_VALIDATION_REQUIRED`
- `CROSS_PRODUCT_DEFROST_RUNTIME_COVERAGE_REQUIRED`
- `HUNGARIAN_WEATHER_TRANSFER_VALIDATION_REQUIRED`

The separate generic `DHW_DEFROST_BRANCH_REQUIRED` residual is removed for the exact S2125 system.

## 12. Readiness

P53 deliberately applies **NO_MECHANICAL_READINESS_UPLIFT**.

- DEFROST remains **20%**
- B05 remains **64%**

A successor-aware readiness recalibration remains separate.

## Raw-data governance

No owner raw bytes, transfer credentials or private correspondence are committed.
