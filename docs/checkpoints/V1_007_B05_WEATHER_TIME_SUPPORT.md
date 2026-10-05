# V1 checkpoint 007: reused weather and physical interval support

The existing canonical panel already contains five observed reference profiles of 8,760 hours each and one 72-hour observed cold event. All 43,872 rows have temperature and relative humidity, unique consecutive station-profile timestamps, and explicit source IDs. No new meteorological data acquisition or national weighting is required for this handoff.

## Source semantics

The current official [HungaroMet HABP_1H description](https://odp.met.hu/climate/observations_hungary/hourly/historical/Leiras_automata_oras-HABP_1H_hist-hu.pdf), PDF page 2, specifies:

- `Time`: “mérési időpont (UTC)”
- `ta`: “elmúlt óra átlaghőmérséklete”
- `u`: “órás pillanatnyi relatív nedvesség”

Existing stable authority: `SRC-B05-HUNGARY-HOURLY-DESC-2026`; observed panel authority: `SRC-B05-HUNGARY-HOURLY-HIST-2026`. The source timestamp is therefore the end of the temperature averaging interval. Humidity is an endpoint observation, not a co-averaged hourly humidity measurement. Using it in an hourly defrost model requires the model's separate approximation/validation contract.

## Small adapter, unchanged observations

`modules/B05/weather.py` now exposes `HourlyWeatherInterval`: source endpoint retained as `interval_end_utc`, preceding boundary as `interval_start_utc`, and humidity's endpoint support labelled explicitly. A same-hour energy/price join must use the interval-start key. The adapter rejects empty/mixed profiles, mixed stations, duplicate/gapped/reversed timestamps, off-hour or non-UTC endpoints, invalid temperature and impossible humidity. Missing humidity is retained as unknown.

For every existing profile labelled by 2025 source timestamps, the covered physical interval is **2024-12-31 23:00 UTC through 2025-12-31 23:00 UTC**. It is a complete 8,760-hour source window, not exactly the midnight-to-midnight 2025 calendar energy window. The source data are not shifted, filled or relabelled as another observation. Exact calendar-year consumption comparison requires the missing boundary hour or an explicitly different window.

The cold event covers 72 hours and retains the observed −21.9 °C minimum. It is neither a predicted future winter nor an official return-period guarantee.

## Remaining integration

This adapter prevents a known one-hour join error, but does not itself complete the price/load/weather consuming model. No nationwide weather probabilities, building demand, supply temperatures, defrost correction or eligibility are inferred. B05-D01 stays INTEGRATING until the physical-demand contract is populated and the joint runtime is tested.
