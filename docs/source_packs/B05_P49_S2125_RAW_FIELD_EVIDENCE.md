# B05-P49 — S2125 raw field evidence acquisition and integrity gate

**Date:** 2026-09-27  
**Canonical parent main:** `8f0d31648352c495bd627d300849c1a8694e2018`

## Purpose

P38-P40 narrowed the NIBE defrost evidence gap to:

`direct Defrost state + BT28 + BT16 + compressor state/frequency + co-timed electrical/thermal measurements`.

P49 acquires that package from the same field owner/system previously bound by P40.

The raw archive remains **EXTERNAL_ONLY**. The repository stores only metadata, exact SHA-256 identities and bounded aggregate audit results.

No temporary transfer URL, password or private message body is committed.

## Raw artifacts

Archive `nibe_daten_jan_maerz_2026.tar.xz`: 43,020,852 bytes, SHA-256 `01736c38535b25030800bd2fba12a54f5ddc676304c3458573be1950e8664d92`.

Members:

- `nibe_alle_daten_jan_maerz_2026.csv`: 852,552,785 bytes; SHA-256 `ca79f165777f3626d68def05fda3331678bc73fa29371e74a2530ccc4d850440`; 92 measurement series and 10,123,992 measurement rows after excluding repeated Influx CSV headers.
- `nibe_energie_jan_maerz_2026.csv`: 456,363,651 bytes; SHA-256 `a3b6e88a9e2783c35511096192aee1a5aef58b57a9a1b40c9a1eff93e55a4456`; 6,688,265 numeric Victron power rows.

Victron uses only `instanceNumber=33` and spans `2026-01-01T00:00:01.525Z..2026-03-31T23:59:58.272Z`. The field owner confirms that S2125-12 + S135 + VVM320 are all behind this meter.

## NIBE target series

The required direct channels each contain 111,264 source rows over `2026-01-13T12:00:05Z..2026-03-31T23:59:03Z`, with typical 59-61 s cadence:

- 1475 BT3 return
- 1478 BT12 supply/condenser
- 1621 BT28 outdoor
- 1622 BT16 evaporator
- 1803 compressor frequency
- 1805 Defrost
- 40 BF1 flow
- 406 generated heat power
- 1575/1577/1583/1585 cumulative thermal-energy channels

The exact value `-3276.8` is observed eight times each in BT3/BT12/BT28/BT16 and once in BF1. P49 does not invent a manufacturer sentinel meaning. It simply excludes this grossly out-of-domain code from physical statistics.

## Direct Defrost state

1805 counts:

- off 0: 106,928 samples
- active 1: 4,234 samples
- passive 2: 102 samples

Contiguous state runs:

- active: 381
- passive: 22

Active state-run median duration is 660 s; passive median is 180.5 s. Because the controller state is sampled at about one minute, these are source-sampled state windows, not sub-minute physical transition timestamps.

## Co-timed electrical evidence

Each active state run is joined to the Victron whole-NIBE-system power series by UTC.

Integration:

- start = first observed Defrost=1 sample;
- end = first subsequent Defrost=0 sample;
- trapezoidal integration only over consecutive Victron samples with gap <=5 s;
- no gap filling and no scaling to 100% coverage.

Across all 381 active windows:

- minimum measured-time coverage: 99.3757%
- median coverage: 99.8482%
- median measured covered energy: 0.298304 kWh
- mean: 0.297706 kWh
- p05: 0.194261 kWh
- p95: 0.379840 kWh
- minimum: 0.072599 kWh
- maximum: 0.658880 kWh
- total measured covered energy: 113.425811 kWh

These values are **not a causal defrost penalty**.

`OBSERVED_DEFROST_STATE_WINDOW_ENERGY != UNIVERSAL_DEFROST_PENALTY`

`ONE_FIELD_SYSTEM != HUNGARIAN_FLEET_PARAMETER`

## Thermal counters

Over the observed NIBE window:

- 1575 DHW incl. internal heater: +975.2
- 1577 heating incl. internal heater: +4709.3
- 1583 DHW compressor-only: +970.7
- 1585 heating compressor-only: +4709.3

All four counters are monotone with zero downward resets.

P49 does not silently convert them into signed defrost heat removal. Signed thermal event derivation remains open.

## Field cycling/modulation

1803 contains 111,264 samples: 91,055 positive-frequency and 20,209 zero.

Minute-cadence run detection yields:

- 143 positive-frequency runs
- 141 sampled starts
- 141 sampled stops
- 1 run <=10 min
- 6 runs <=20 min

This is exact field runtime evidence for one S2125 system, not Mitsubishi/Dimplex product tau_eq and not fleet weighting.

## Evidence interpretation

Bounded E1/OBS facts now exist for this exact installation: raw integrity, timestamps, direct controller states, BT28/BT16/compressor observations, Victron whole-system power, thermal counters and field cycling.

Derived/model quantities remain E2 where they require causal baseline, thermal integration assumptions, weather transfer, cross-product transfer or population weighting.

Q-B05-003 resolves the former raw-package and multi-timestamp acquisition residuals for this exact system. Remaining: matched defrost penalty + signed thermal event derivation, cross-product runtime coverage and Hungarian weather-transfer validation.

Q-B05-004 gains exact S2125 field runtime validation but still requires exact Mitsubishi/Dimplex transient records and exact emitter-response evidence.

## Readiness

- DEFROST: 20 -> 65
- PART_LOAD_MODULATION: 45 -> 55
- all other component values unchanged

PRODUCT_SCALING remains an intentional E1 contract boundary, not missing-data readiness. Mean of the other 15 components = 67.67%, so canonical rounded B05 readiness becomes **68%** from **64%**.

## Raw-data governance

Raw archive/CSV bytes remain outside the public repository. Repository-safe state is limited to exact hashes, byte sizes, channel identities, bounded aggregate metrics and fail-closed admission rules.
