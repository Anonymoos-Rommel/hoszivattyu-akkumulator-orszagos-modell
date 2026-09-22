# B05-P9 — HungaroMet historical winter blocks and empirical cold-stress materialization

## Purpose

P9 executes the B05-P8 method on the five canonical HungaroMet historical HABP_1H station archives and materializes real derived cold-winter evidence.

Raw HungaroMet ZIP files remain external and are **not** committed.

Core boundaries:

`PROJECT-DERIVED EMPIRICAL RETURN PERIOD != OFFICIAL HUNGAROMET 1-IN-10`

`MULTI-STATION ENVELOPE != NATIONAL RETURN PERIOD`

`72H MEAN STRESS COVERAGE != HOURLY EVENT COVERAGE`

`SINGLE-MANUFACTURER COLD DOMAIN != CROSS-MANUFACTURER COHORT DOMAIN`

## 1. Acquisition

Canonical archives were re-acquired on 2026-09-22 from the official HungaroMet ODP historical hourly directory.

The exact file names and SHA-256 values are recorded in:

`registry/b05_p9_hungaromet_raw_acquisition_manifest.csv`

The five archives are:

| Station | Archive period | Complete winters used |
|---|---|---:|
| 15310 Szombathely | 2002-02-27 .. 2025-12-31 | 23 |
| 44527 Budapest Pestszentlőrinc | 2002-01-01 .. 2025-12-31 | 23 |
| 58102 Szeged belterület | 2002-01-01 .. 2025-12-31 | 23 |
| 46304 Kecskemét K-puszta | 2002-01-01 .. 2025-12-31 | 23 |
| 52744 Miskolc Diósgyőr | 2013-06-27 .. 2025-12-31 | 12 |

Total complete Dec-Feb blocks: **104**.

Every admitted winter block has complete source-native hourly `ta` coverage over the canonical Europe/Budapest Dec-Feb window.

## 2. Materialized derived data

### 2.1 Complete winter block table

`data/processed/b05_weather_winter_extremes.csv`

Contains 104 rows with:

- station ID;
- winter label year;
- exact UTC winter bounds;
- expected and observed hourly counts;
- full-winter mean `ta`;
- coldest contiguous 72-hour mean `ta`;
- exact coldest-72h event timestamps.

### 2.2 Empirical 10-year station brackets

`data/processed/b05_weather_empirical_return_period.csv`

For four 23-winter stations, the 10-year target `p=0.1` is bracketed by rank 2 and rank 3:

- rank 2 empirical T = 12 years;
- rank 3 empirical T = 8 years.

For Miskolc with 12 complete winters, the target is bracketed by:

- rank 1 empirical T = 13 years;
- rank 2 empirical T = 6.5 years.

No interpolation is performed.

| Station | Complete winters | 10y winter-mean bracket °C | 10y coldest-72h-mean bracket °C |
|---|---:|---:|---:|
| Szombathely 15310 | 23 | -1.466991 .. -0.973796 | **-12.376389 .. -10.802778** |
| Budapest 44527 | 23 | -0.934074 .. -0.680046 | **-10.352778 .. -10.186111** |
| Szeged 58102 | 23 | -0.213843 .. 0.168194 | **-11.656944 .. -10.304167** |
| Kecskemét 46304 | 23 | -1.506481 .. -1.106528 | **-13.331944 .. -12.952778** |
| Miskolc 52744 | 12 | -2.156435 .. 0.160509 | **-11.656944 .. -9.644444** |

## 3. Five-station stress envelope

`data/processed/b05_weather_empirical_station_envelope.csv`

Historical empirical station envelope:

- winter mean, 10-year target:
  **-2.156435 .. 0.168194 °C**
- coldest 72-hour mean, 10-year target:
  **-13.331944 .. -9.644444 °C**

This is an envelope across the five selected station-specific brackets.

It is **not**:

- a population-weighted national average;
- a national climate-zone probability;
- an official HungaroMet 1-in-10 statistic;
- a future-frequency forecast.

For programme sizing it is admissible as a bounded historical **SCN stress input**.

A future-probability claim would still require explicit stationarity/nonstationarity or climate-change authority.

## 4. Product-domain consequence

P9 compares the 10-year 72h-mean stress envelope with the canonical B05 product-domain evidence.

### 4.1 STIEBEL W35

Current continuous/source-native cold domain:

`-15 .. +7 °C`

P9 10-year 72h-mean envelope:

`-13.331944 .. -9.644444 °C`

Therefore the **72h mean stress-coordinate envelope is inside the W35 STIEBEL domain**.

Cold-side margin at the envelope's colder endpoint:

`-13.331944 - (-15) = 1.668056 °C`

This does **not** prove hourly event coverage.

The previously materialized observed 72-hour event reached **-21.9 °C hourly minimum**, so below--15 W35 evidence remains required if an hourly extreme-event runtime simulation is in scope.

### 4.2 Cross-manufacturer W35 cohort

P7 cross-manufacturer common W35 coordinates begin at **-7 °C**.

Therefore:

`CROSS-MANUFACTURER W35 COMMON DOMAIN != 10-YEAR COLD-STRESS COVERAGE`

For a cross-manufacturer cold-stress cohort, a second manufacturer needs evidence at or below **-13.331944 °C**, or another defensible bounded cold-domain evidence route.

### 4.3 W45

Current continuous STIEBEL W45 domain:

`-7 .. +7 °C`

Every station-specific 10-year 72h bracket is fully below -7 °C.

Therefore the cold W45 gap is now quantified:

`COLD W45 PERFORMANCE DOMAIN TO AT LEAST -13.331944 °C REQUIRED`

for full coverage of the five-station 10-year 72h-mean stress envelope.

No extrapolation is allowed.

### 4.4 W55

Continuous cold-side W55 performance surface remains Q.

The existing isolated/common A7/W55 observations cannot define a continuous cold-weather W55 domain.

## 5. Effect on Q-B05-002

Q-B05-002 can be **RESOLVED for canonical model use**.

The project now has:

- a reproducible official-source hourly archive;
- exact winter/event definitions;
- complete historical winter blocks;
- a non-parametric empirical recurrence method;
- five numeric station brackets;
- a five-station bounded stress envelope;
- explicit finite-record uncertainty;
- explicit station/national and historical/future boundaries.

The resolution is:

`PROJECT-DERIVED EMPIRICAL 10-YEAR HISTORICAL COLD STRESS`

It is **not** an official HungaroMet 1-in-10 label.

Prospective future-frequency claims remain outside this resolution and require separate climate nonstationarity evidence.

## 6. Effect on Q-B05-001

Q-B05-001 remains OPEN_NARROWED.

P9 changes its residuals:

1. **cold W35 cross-manufacturer evidence**
   - required at/below the stress envelope if cohort inference is desired;
   - current -15 W35 evidence is STIEBEL-only.

2. **cold W45**
   - now quantitatively required to at least -13.331944 °C for the 10-year 72h-mean envelope.

3. **continuous W55**
   - still required.

4. **below -15 W35**
   - no longer required merely to cover the P9 10-year 72h **mean** coordinate;
   - remains a separate hourly-event requirement because the observed event layer contains hours below -15 °C.

## 7. Public-repository boundary

The repository stores:

- derived winter metrics;
- derived empirical brackets;
- derived stress envelope;
- raw acquisition filenames, source URLs and SHA-256 checksums.

It does not store the raw HungaroMet ZIP archives.

The temporary GitHub Actions acquisition/materialization probe used during P9 is removed before merge-ready state.

## 8. Readiness

Sub-gates can advance because real multi-year evidence is now materialized:

- `WEATHER_INPUT`: strengthened multi-year historical evidence;
- `COLD_1_IN_10`: numeric historical empirical stress is now materialized;
- `WEATHER_PERFORMANCE_DOMAIN_COVERAGE`: stress-domain gaps are now quantified.

The overall B05 module readiness remains **64%**.

Reason: the module still has major independent product/runtime blockers (Q-B05-001, defrost, part-load/cycling, DHW priority, W55 continuity and national physical-demand interface). P9 should not manufacture an overall percentage uplift merely because one critical weather question is now resolved.
