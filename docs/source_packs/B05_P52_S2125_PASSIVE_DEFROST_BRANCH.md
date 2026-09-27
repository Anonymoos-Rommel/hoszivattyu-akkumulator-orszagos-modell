# B05-P52 — S2125 passive-defrost branch characterization

**Date:** 2026-09-27  
**Canonical parent main:** `ac2022f43a665a3d27eeaf2c043d18e6c36b25e7`

## Purpose

P50/P51 kept passive defrost separate from active reverse-cycle defrost.

P52 attacks that residual using the exact P49 owner raw package. The raw bytes remain **EXTERNAL_ONLY**. The repository stores only exact artifact identities, bounded aggregate results and fail-closed interpretation rules.

Primary question:

> In this exact S2125-12 + VVM320 + S135 installation, what does direct `Defrost=2` passive operation look like electrically and operationally, and is there enough evidence to admit a separate passive penalty?

## 1. Raw identity gate

The re-materialized owner archive and both members reproduce the exact P49 SHA-256 identities:

- archive: `01736c38535b25030800bd2fba12a54f5ddc676304c3458573be1950e8664d92`
- NIBE member: `ca79f165777f3626d68def05fda3331678bc73fa29371e74a2530ccc4d850440`
- Victron member: `a3b6e88a9e2783c35511096192aee1a5aef58b57a9a1b40c9a1eff93e55a4456`

P52 therefore operates on the exact canonical P49 source package rather than on a new export.

As in P49-P51, transfer URL/password/private correspondence and raw bytes are not committed.

## 2. Direct passive-state population

Direct NIBE register 1805 contains:

- passive samples: **102**
- contiguous passive runs: **22**
- median state-run duration: **180.5 s**
- mean duration: **278.136 s**
- p05/p95 duration: **60.0 / 1058.1 s**
- minimum/maximum: **58 / 1140 s**

Pre-five-sample operating-mode classification using the same DHW-valve rule as P50 gives:

- HEAT: **9**
- DHW: **11**
- TRANSITION: **2**

This mode split is descriptive exact-system evidence only.

## 3. Component-state identity

Across all **102/102** direct passive samples:

- current compressor frequency 1803 = **0 Hz**
- requested compressor frequency 301 = **0 Hz**
- source-native generated heat power 406 = **0 kW**
- outdoor fan speed 401 is **positive on every sample**

Outdoor-fan speed over the passive samples:

- minimum: **91**
- median: **454**
- maximum: **457**

Heating-medium pump speed 1636 is observed at:

- 0: 9 samples
- 30: 90 samples
- 55: 3 samples

BT28 at passive-run start ranges from **4.0 to 12.2 C**, median **5.25 C**. P52 does not infer the configured passive cut-out from these observations.

This exact field evidence is consistent with the manufacturer controller semantics already pinned in P33:

`PASSIVE_DEFROST = COMPRESSOR_OFF + FAN_ON`

It is observably distinct from active reverse-cycle Defrost=1.

## 4. Relationship to compressor demand

For every passive sample, requested compressor frequency remains zero.

The time from passive-state end to the next observed positive compressor-frequency sample is:

- minimum: **14.0 min**
- median: **75.5 min**
- p05/p95: **15.87 / 529.22 min**

By pre-mode:

- HEAT median: **81.02 min**
- DHW median: **53.98 min**

Also, **17/22** passive runs begin within approximately 1.1 minutes of the last positive compressor sample.

P52 therefore does not model passive defrost as an interruption of an ongoing compressor request in this exact system. This does **not** prove zero building-level thermal consequence or authorize transfer to other controllers/products.

## 5. Exact P49 electrical-integration reproduction

Before evaluating passive windows, P52 reruns the exact P49 Victron integration rule on all 381 active state windows:

- first observed direct-state sample to first subsequent Defrost=0 sample;
- only Victron samples whose timestamps lie inside the state window;
- trapezoidal integration over consecutive power samples with gap <=5 s;
- no gap filling;
- no scaling to 100% coverage.

The active result reproduces P49:

- median measured covered energy: **0.298304446 kWh**
- mean: **0.297705541 kWh**
- p05/p95: **0.194261265 / 0.379839980 kWh**
- minimum measured-time coverage: **99.375704%**
- median coverage: **99.848176%**
- total measured covered energy: **113.425811 kWh**

This is the internal reproduction gate for the passive derivation.

## 6. Passive measured state-window electricity

Applying the same integration rule to the 22 direct passive windows gives:

- median measured covered energy: **0.004854669 kWh**
- mean: **0.008794744 kWh**
- p05/p95: **0.000562853 / 0.028889919 kWh**
- minimum/maximum: **0.000462136 / 0.031689773 kWh**
- total measured covered energy: **0.193484365 kWh**

Measured-time coverage is materially lower than for the much longer active events:

- minimum: **59.6677%**
- median: **94.9480%**
- p05/p95: **75.5983 / 99.6985%**
- windows with >=98% coverage: **9/22**

The lower coverage is dominated by short state windows and unmeasured boundary time under the unchanged P49 no-gap-fill contract.

For descriptive normalization only, measured-covered intervals imply median whole-system power **80.640888 W** across the 22 runs. This is not a causal passive-defrost increment.

Therefore:

`PASSIVE_STATE_WINDOW_ENERGY != PASSIVE_INCREMENTAL_PENALTY`

and P52 does not scale the missing boundary time to 100%.

## 7. Matched-control attack

P52 explicitly attempts a passive matched-control design rather than assuming the observed state-window energy is incremental.

The strict attack inherits P50 pre-state calipers:

- BT28: +/-1.0 C
- BT16: +/-1.5 C
- current compressor frequency: +/-5 Hz
- requested compressor frequency: +/-5 Hz
- BT12: +/-2 C
- BT3: +/-2 C

and requires:

- same HEAT/DHW pre-mode;
- candidate within +/-14 days;
- no non-zero defrost within the control window or +/-20-minute buffer;
- compressor off throughout the passive-duration control window;
- stable control mode;
- at least three controls before any branch-level matched effect may be admitted.

Result:

- HEAT passive events with >=3 strict controls: **5/9**
- DHW passive events with >=3 strict controls: **0/11**
- TRANSITION events: excluded from canonical matching

This is insufficient for a branch-wide passive electrical penalty, especially because the larger DHW branch has no strict matched support.

P52 therefore admits **no canonical matched passive increment**.

## 8. Thermal boundary

The P50 signed-thermal factor was calibrated on positive-domain, non-defrost HEAT operation.

Passive Defrost=2 is a different domain:

- compressor = 0;
- requested compressor = 0;
- source-native qheat 406 = 0;
- fan remains on.

P52 does not silently transfer the P50 factor into this compressor-off passive domain.

Therefore no signed passive heat-removal kWh is admitted.

`P50_SIGNED_THERMAL_FACTOR != PASSIVE_THERMAL_DER_WITHOUT_DOMAIN_VALIDATION`

The observed zero source-native generated-heat signal is not re-labelled as proof of zero building thermal cost.

## 9. Admission result

P52 resolves the former generic passive branch residual to a narrower exact-system state:

`PASSIVE_DEFROST_BRANCH_REQUIRED`

->

`PARTIAL_RESOLVED_TO_DIRECT_PASSIVE_STATE_AND_MEASURED_WINDOW_ELECTRICITY`

Admitted for this exact installation:

- direct passive event identity and count;
- exact component-state characterization;
- duration/mode distribution;
- exact measured-covered whole-system state-window electricity;
- explicit no-concurrent-compressor-request observation.

Not admitted:

- universal passive event constant;
- branch-wide causal incremental passive electricity;
- signed passive thermal penalty;
- passive event frequency transfer to another product or Hungary.

Residual:

`PASSIVE_INCREMENTAL_ELECTRIC_AND_THERMAL_DOMAIN_VALIDATION_REQUIRED`

## 10. Q-B05-003 and readiness

Q-B05-003 remains:

**E2 / VALIDATION_BLOCKER / MODEL_CONTINUE**

Residuals after P52:

- `RECOVERY_TAIL_CENSORING_AND_FULL_CYCLE_PARAMETER_ADMISSION_REQUIRED`
- `PASSIVE_INCREMENTAL_ELECTRIC_AND_THERMAL_DOMAIN_VALIDATION_REQUIRED`
- `DHW_DEFROST_BRANCH_REQUIRED`
- `STATE_CONDITIONED_PREDICTIVE_MODEL_VALIDATION_REQUIRED`
- `CROSS_PRODUCT_DEFROST_RUNTIME_COVERAGE_REQUIRED`
- `HUNGARIAN_WEATHER_TRANSFER_VALIDATION_REQUIRED`

P52 deliberately performs **NO_MECHANICAL_READINESS_UPLIFT**:

- DEFROST remains **20%**
- B05 remains **64%**

## Raw-data governance

No owner raw bytes, temporary transfer URL, password or private correspondence are added to the public repository.
