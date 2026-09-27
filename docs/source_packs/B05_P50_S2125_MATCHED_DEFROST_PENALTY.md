# B05-P50 — S2125 matched active-defrost penalty and signed thermal derivation

**Date:** 2026-09-27  
**Canonical parent main:** `e9f96b285ca7e2fd993273098d177042393a7869`

## Purpose

P49 acquired the exact raw package but intentionally stopped at:

`OBSERVED_DEFROST_STATE_WINDOW_ENERGY != CAUSAL_DEFROST_PENALTY`.

P50 attacks that residual without creating a universal coefficient.

The primary estimand is deliberately narrow:

> For this exact S2125-12 + VVM320 + S135 installation, during **active HEAT-mode Defrost=1 state**, how does measured whole-NIBE-system electrical energy and signed hydronic thermal transfer differ from matched normal-heating windows that start from similar pre-event operating state?

It does **not** estimate a complete defrost cycle including post-defrost recovery.

## 1. Source alignment

P50 uses only the P49 external raw artifacts.

All target NIBE series have exactly 111,264 rows. Direct Defrost 1805 and compressor-frequency 1803 timestamps are identical row-by-row. Sparse timestamp differences on BT28, BT16, BT12, BT3, BF1, requested frequency and DHW state are at most **1 second**.

P50 therefore uses source-row index alignment, not an arbitrary nearest-time join.

## 2. Source-bound signed thermal derivation

NIBE source-native generated heat power 406 is positive-domain heating output and is not a signed reverse-cycle heat meter.

P50 calibrates a source-bound factor on non-defrost HEAT samples:

`qheat ~= k * BF1 * (BT12 - BT3)`

Calibration window: before 2026-03-01.

- calibration samples: **51,956**
- median factor `k`: **0.0734149054505005 kW/(L/min*K)**

Temporal March holdout:

- n = **23,435**
- MAE = **0.141167 kW**
- MAPE = **4.960373%**
- R² = **0.586578**

The factor p25/p75 is **0.0716525..0.0754107**.

P50 then preserves the sign of `BT12-BT3` during Defrost=1.

This creates an **E2/DER signed thermal estimate**, not E1 source-native signed heat metering.

## 3. Matched-control design

Pre-event state is the five source samples immediately before Defrost=1.

Strict matching dimensions and calipers:

- BT28: ±1.0 °C
- BT16: ±1.5 °C
- current compressor frequency: ±5 Hz
- requested compressor frequency: ±5 Hz
- BT12: ±2 °C
- BT3: ±2 °C

Additional controls:

- same HEAT/DHW pre-mode class;
- candidate within ±14 days;
- no non-zero Defrost inside a ±20-minute candidate buffer;
- candidate control window itself has Defrost=0;
- compressor positive for at least 80% of the window;
- source qheat positive for at least 70%;
- control mode remains stable;
- 3–5 nearest controls required;
- Victron measured-time coverage at least 98%.

HEAT mode is defined as pre-five-sample DHW-valve mean <=0.1.
DHW is >=0.9.
Intermediate states are TRANSITION and are excluded from the primary branch.

## 4. Match coverage and balance

All active events: **381**.

- STRICT: **301**
- RELAX_1_5: 18
- RELAX_2_0: 18
- NO_MATCH: 35
- transition-mode excluded: 9

Primary canonical subset:

- **266 strict HEAT events**

Strict HEAT control reuse:

- unique control windows: **1,094**
- assignments: **1,326**
- maximum reuse: 6
- 95th percentile reuse: 2

Median absolute pre-state difference, with p95 in parentheses:

- BT28: **0.16 °C** (0.6275)
- BT16: **0.14 °C** (0.815)
- compressor: **0.4 Hz** (1.6)
- requested compressor: **0.4 Hz** (1.6)
- BT12: **0.24 °C** (0.995)
- BT3: **0.22 °C** (0.905)

## 5. Active HEAT electrical uplift

For the 266 strict HEAT events:

- event electrical energy mean: **0.294184 kWh**
- matched-control electrical energy mean: **0.195402 kWh**
- direct event-minus-control uplift mean: **0.098782 kWh**
- direct uplift median: **0.118281 kWh**
- p05: **-0.062446 kWh**
- p95: **0.192707 kWh**

10,000-draw event bootstrap, fixed seed 20260927:

- median 95% CI: **0.110834..0.128713 kWh**
- mean 95% CI: **0.088584..0.108279 kWh**

Negative event deltas are preserved. P50 never clamps them to zero.

### Independent internal cross-check

An equal-duration electrical window immediately preceding the event gives:

- median local uplift: **0.117024 kWh**
- matched-vs-local correlation: **0.833360**
- median matched-minus-local difference: **-0.003039 kWh**
- median absolute matched/local difference: **0.019386 kWh**

This is an internal reproduction check on the same raw meter, not independent external validation.

## 6. Signed thermal active-state effect

Strict HEAT active-state signed thermal event energy:

- mean: **-0.268228 kWh**
- median: **-0.260139 kWh**
- median bootstrap 95% CI: **-0.290281..-0.238928 kWh**

Matched normal-heating thermal delivery minus signed event thermal energy:

- mean service shortfall: **0.881017 kWh**
- median: **0.826803 kWh**
- median bootstrap 95% CI: **0.779830..0.880001 kWh**

Thermal-factor p25/p75 sensitivity moves the median service shortfall only to:

**0.806955..0.849280 kWh**.

This remains E2 because the signed negative-domain power is derived from the source-bound positive-domain calibration rather than measured by a source-native signed heat meter.

## 7. Why DHW is separate

Across matched DHW events, the median direct electrical event-minus-control delta is approximately **-0.018409 kWh**, unlike HEAT.

Therefore:

`HEAT_DEFROST != DHW_DEFROST`

and P50 forbids pooling both modes into one penalty.

## 8. Admission boundary

P50 admits, for this exact installation:

- a matched **active HEAT-state direct electrical uplift distribution**;
- a source-bound **signed active-state thermal DER**;
- a matched **active-state thermal service shortfall distribution**.

P50 does not admit:

- a universal per-event constant;
- a full-cycle penalty including recovery;
- passive-defrost penalty;
- DHW penalty;
- cross-product transfer;
- Hungarian fleet weighting;
- Hungarian weather-transfer frequency.

The strongest current boundary is:

`ACTIVE_STATE_DIRECT_ELECTRIC_UPLIFT != FULL_DEFROST_CYCLE_PENALTY`.

## 9. Residuals

Q-B05-003 remains **E2 / VALIDATION_BLOCKER / MODEL_CONTINUE**.

Residuals:

- `POST_DEFROST_RECOVERY_TAIL_REQUIRED`
- `PASSIVE_DEFROST_BRANCH_REQUIRED`
- `DHW_DEFROST_BRANCH_REQUIRED`
- `STATE_CONDITIONED_EVENT_MODEL_REQUIRED`
- `CROSS_PRODUCT_DEFROST_RUNTIME_COVERAGE_REQUIRED`
- `HUNGARIAN_WEATHER_TRANSFER_VALIDATION_REQUIRED`

The strong pre-compressor-frequency dependence of direct electrical delta is another reason not to mint one universal 0.118 kWh coefficient.

## 10. Readiness

P50 deliberately performs **NO_MECHANICAL_READINESS_UPLIFT**.

- DEFROST remains **20%**
- B05 remains **64%**

A later successor-aware readiness recalibration can score the accumulated P49/P50 evidence separately.
