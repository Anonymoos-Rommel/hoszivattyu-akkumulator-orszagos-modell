# B05-P8 — empirical cold-winter / multi-day return-period contract

## Purpose

P8 narrows Q-B05-002 without manufacturing an official HungaroMet "1-in-10" statistic.

The repository already contains:

- five station-specific complete observed 2025 calendar-year profiles;
- one observed 72-hour coldest-window profile selected from the previously acquired historical archives;
- exact source-native HungaroMet `ta` semantics.

What it does **not** currently contain is a committed multi-year sequence of complete meteorological winters from which a return-period distribution can be derived.

Canonical boundaries:

`PROJECT-DERIVED EMPIRICAL RETURN PERIOD != OFFICIAL HUNGAROMET 1-IN-10`

`STATION RETURN PERIOD != NATIONAL POPULATION-WEIGHTED CLIMATE`

`OBSERVED RECORD EXTREME != RETURN-PERIOD ESTIMATE`

`PARAMETRIC TAIL EXTRAPOLATION != DEFAULT`

## 1. Canonical winter block

P8 adopts the already-established B08-P3 meteorological-winter reporting window:

`winter_Y = [Dec 1 00:00 of Y-1, Mar 1 00:00 of Y)`

in `Europe/Budapest`.

The local bounds are converted to UTC before selecting HungaroMet source records.

A winter block is admissible only when every expected hourly `ta` value exists exactly once.

Missing hours are not:

- interpolated;
- forward/backward filled;
- substituted from another station;
- reconstructed from `t`, `tn` or `tx`.

## 2. Two explicit cold metrics

P8 keeps two different estimands.

### 2.1 Cold winter metric

`WINTER_MEAN_TA_C`

Mean source-native hourly `ta` over the complete Dec-Feb winter.

This addresses the "cold winter" part of Q-B05-002.

### 2.2 Multi-day extreme metric

`WINTER_MIN_72H_MEAN_TA_C`

Within each complete winter, select the coldest contiguous 72-hour `ta` mean.

The 72-hour event must lie wholly inside that winter.

This addresses the multi-day extreme-cold part of Q-B05-002.

The two metrics must not be substituted for one another.

## 3. Non-parametric empirical recurrence

For each station and metric, complete winters are sorted from coldest to warmest.

For rank `r` among `n` complete winters:

`annual exceedance probability = r / (n + 1)`

`empirical return period = (n + 1) / r`

For a target 10-year recurrence:

`p_target = 0.1`

P8 does not interpolate a point value between the adjacent observed order statistics.

Instead it reports an interval:

`[colder observed bound, warmer observed bound]`

whose plotting positions bracket `p_target`.

This preserves the finite-sample uncertainty visible in the actual archive.

## 4. Why no GEV/Gumbel default is fitted

A parametric extreme-value fit may be useful later as a sensitivity model, but P8 does not make it the canonical first route because:

- the canonical five-station archive lengths differ;
- the shortest selected station history is materially shorter than the longest;
- the project does not yet carry a validated stationarity/nonstationarity model;
- a fitted tail can create apparent precision beyond the observed record.

Therefore:

`NO PARAMETRIC TAIL EXTRAPOLATION BY DEFAULT`

If a later slice adds GEV/Gumbel or climate-trend modelling, it must remain a separately identified model layer with diagnostics and uncertainty.

## 5. Current committed-data audit

The current public repository contains:

- five `OBSERVED_REFERENCE_YEAR` profiles for calendar year 2025;
- one `OBSERVED_EXTREME_COLD_SPELL` 72-hour event from 2005.

These rows do not form a multi-year sequence of complete Dec-Feb winters.

Therefore:

`CURRENT_COMMITTED_COMPLETE_WINTER_BLOCKS = 0`

for return-period estimation.

The existing observed event remains valid:

- station: Szombathely 15310;
- 2005-02-07 09:00Z to 2005-02-10 08:00Z;
- 72-hour mean `ta = -14.286 C`.

But:

`OBSERVED RECORD EVENT != 10-YEAR EVENT`

## 6. Reproducible re-materialization

P8 adds:

`tools/materialize_b05_extreme_weather.py`

The tool consumes the same five canonical external HungaroMet `HABP_1H` historical ZIP families already used by B05-P3.

Raw ZIP files remain external acquisition inputs and are not committed.

The tool emits only derived outputs:

1. `b05_weather_winter_extremes.csv`
   - station;
   - winter label;
   - completeness;
   - winter mean `ta`;
   - coldest 72-hour mean `ta`;
   - exact 72-hour event timestamps.

2. `b05_weather_empirical_return_period.csv`
   - station;
   - metric;
   - complete-winter count;
   - target return period;
   - plotting-position ranks;
   - colder/warmer empirical bracket;
   - evidence/status boundary.

3. `b05_weather_empirical_station_envelope.csv`
   - only when every canonical station has a qualified bracket;
   - spatial envelope only;
   - no population weighting and no national-frequency claim.

## 7. Prospective programme use

A historical empirical 10-year bracket can be used as a bounded **stress scenario** after materialization.

Prospective use must remain explicit:

`HISTORICAL EMPIRICAL RECURRENCE -> SCN STRESS INPUT`

unless separate evidence justifies treating the historical process as a current future-frequency model.

A changing climate means that historical rank recurrence must not silently become a future probability claim.

Residual:

`STATIONARITY_SENSITIVITY_REQUIRED`

## 8. National/spatial boundary

P8's five stations provide explicit spatial anchors.

Without a separate geographic/population/climate-zone weighting model:

- station-specific return periods remain station-specific;
- a min/max multi-station envelope is allowed as a stress envelope;
- no national average "Hungarian 1-in-10 temperature" is minted.

Therefore:

`MULTI-STATION ENVELOPE != NATIONAL RETURN PERIOD`

## 9. Q-B05-002 state

Q-B05-002 becomes:

`OPEN_NARROWED`

Resolved by P8:

- canonical winter window;
- winter metric;
- multi-day extreme metric;
- completeness rule;
- non-parametric recurrence method;
- finite-sample bracketing;
- station/national boundary;
- official-vs-project-derived semantics;
- executable raw-to-derived materializer.

Remaining before a numeric project-derived 10-year bracket can be canonical:

- reacquire the external multi-year raw historical station archives;
- materialize complete-winter block series;
- run the P8 estimator;
- retain stationarity/nonstationarity sensitivity for prospective programme use.

An official HungaroMet "1-in-10" label is not claimed.

## 10. Readiness

The `COLD_1_IN_10` sub-gate can move from pure Q/method-absent to **PARTIAL method-ready**.

B05 module readiness remains **64%** because no numeric multi-year empirical bracket is yet materialized and no arbitrary module-level percentage uplift is justified.
