# B05-P51 — S2125 post-defrost recovery tail and state-conditioned validation surface

**Date:** 2026-09-27  
**Canonical parent main:** `233a4aa4f3ad5cf132ef64c5befac3583e3597f8`

## Purpose

P50 resolved the active HEAT-state matched event effect but explicitly left:

- `POST_DEFROST_RECOVERY_TAIL_REQUIRED`
- `STATE_CONDITIONED_EVENT_MODEL_REQUIRED`

P51 attacks both without minting one universal full-cycle coefficient.

## 1. Recovery-tail contract

P51 extends each P50 strict HEAT event and the exact same matched controls beyond the first observed Defrost=0 sample.

At each recovery checkpoint, P51 requires:

- no later non-zero Defrost in the event tail;
- no DHW contamination;
- at least 95% HEAT-state samples;
- Victron measured-time coverage >=98%;
- at least three of the original P50 matched controls still clean;
- matched controls themselves remain Defrost=0 and HEAT.

No missing electrical time is filled.

### Complete-case trajectory

Exactly **48** strict HEAT events remain clean at every checkpoint:

`0 / 5 / 10 / 15 / 20 / 30 / 45 min`.

Because this is a selected complete-case subset:

`CLEAN_45MIN_COMPLETE_CASE != ALL_DEFROST_EVENTS`.

Median cumulative electrical uplift:

- active endpoint: **0.117806 kWh**
- +5 min: **0.123372**
- +10 min: **0.143339**
- +15 min: **0.162047**
- +20 min: **0.187476**
- +30 min: **0.267631**
- +45 min: **0.343058**

Median cumulative thermal service shortfall:

- active endpoint: **0.914140 kWh**
- +5 min: **0.920142**
- +10 min: **0.851569**
- +15 min: **0.695930**
- +20 min: **0.551235**
- +30 min: **0.184858**
- +45 min: **-0.128300**

Thus in this selected clean subset, thermal service has caught up/overshot by 45 minutes at the median while electrical uplift continues to accumulate.

Paired 45-minute tail relative to the active-state endpoint:

- extra electrical uplift median: **+0.212087 kWh**
- bootstrap median 95% CI: **0.161419..0.255001**
- thermal shortfall reduction median: **0.997607 kWh**
- bootstrap 95% CI: **0.835607..1.154461**

This directly proves:

`ACTIVE_STATE_UPLIFT != FULL_CYCLE_PENALTY`.

## 2. Sustained recovery and censoring

P51 also searches minute-by-minute out to 90 minutes.

A recovery is called only when cumulative matched thermal shortfall is <=0 for **five successive minute checkpoints**.

Result:

- strict HEAT source events: **266**
- observed sustained recovery before contamination/censoring: **30**
- censored or not recovered under the clean contract: **236**

Among the 30 observed recoveries:

- median recovery time after active-state endpoint: **33.5 min**
- bootstrap median 95% CI: **30.5..36.5 min**
- p05/p95: **24.8..48.2 min**
- median electrical uplift at recovery: **0.299768 kWh**
- bootstrap median 95% CI: **0.212288..0.350872 kWh**

Among the censored/not-recovered events, maximum clean horizon has:

- median: **8.5 min**
- p75: **19 min**
- p90: **30.5 min**

Therefore P51 does **not** infer a population recovery-time distribution from the 30 observed recoveries.

`SUSTAINED_RECOVERY_OBSERVED_SUBSET != POPULATION_RECOVERY_TIME_DISTRIBUTION`.

## 3. State-conditioned active-event surface

P50 showed that a universal active-state electrical uplift is misleading.

Across the 266 strict HEAT events:

- correlation(pre-compressor Hz, direct electrical uplift) = **-0.750045**
- correlation(pre-compressor Hz, thermal service shortfall) = **+0.562792**

P51 therefore materializes a descriptive pre-compressor-frequency surface:

| Pre-event compressor | n | Active electrical uplift median | Bootstrap median 95% CI | Thermal shortfall median |
|---|---:|---:|---:|---:|
| <=30 Hz | 71 | 0.138917 kWh | 0.133286..0.151626 | 0.718935 kWh |
| >30..40 Hz | 108 | 0.134534 | 0.126174..0.143821 | 0.738738 |
| >40..50 Hz | 38 | 0.058616 | 0.043336..0.074859 | 0.992657 |
| >50 Hz | 49 | 0.001314 | -0.030035..0.047344 | 1.241749 |

This surface makes the main physical point explicit:

> High pre-defrost compressor loading can produce little or no **incremental active-state electricity** versus matched normal operation, while the **thermal service shortfall is larger**.

Therefore direct electrical uplift alone is not a sufficient defrost-state descriptor.

## 4. Why no continuous predictive equation is admitted

P51 tested simple continuous OLS candidates using pre-frequency and additional state variables.

A temporal March holdout contains only **9** strict HEAT events.

Candidate continuous formulas do not stably beat the constant-median baseline on holdout MAE.

Therefore:

`STATE_BIN_SURFACE != CONTINUOUS_PREDICTIVE_FORMULA`.

The bin surface is admitted as E2 validation evidence, not as the final runtime model.

## 5. Current interpretation

P51 partially resolves:

`POST_DEFROST_RECOVERY_TAIL_REQUIRED`

to:

`RECOVERY_TAIL_CENSORING_AND_FULL_CYCLE_PARAMETER_ADMISSION_REQUIRED`.

It also partially resolves:

`STATE_CONDITIONED_EVENT_MODEL_REQUIRED`

to:

`STATE_CONDITIONED_PREDICTIVE_MODEL_VALIDATION_REQUIRED`.

Still open:

- passive defrost branch;
- DHW defrost branch;
- recovery censoring / full-cycle parameter admission;
- predictive state model validation;
- cross-product runtime evidence;
- Hungarian weather/event-frequency transfer.

Q-B05-003 remains **E2 / VALIDATION_BLOCKER / MODEL_CONTINUE**.

## 6. Readiness

P51 deliberately applies **NO_MECHANICAL_READINESS_UPLIFT**.

- DEFROST remains **20%**
- B05 remains **64%**

Readiness scoring remains a separate successor-aware recalibration task.

## 7. Raw-data governance

No owner raw bytes, transfer credentials or private correspondence are added to the repository.

P51 stores only bounded deterministic DER outputs and fail-closed interpretation rules derived from the already pinned P49 raw artifact identities.
