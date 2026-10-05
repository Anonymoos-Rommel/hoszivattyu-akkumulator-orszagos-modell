# V1-044 – Historical cold exposure of the fixed-W55 reference

Scope: B05-D01/B05-D02, bounded reuse of existing sources. The new consumer joins the exact Budapest weather archive to the existing WM50 Vol.5.3 source map. It introduces no thermal engine, extrapolation, national assumption or readiness credit.

## Practical finding

The existing 2025 reference does not test every relevant historical cold condition. Among P9's 23 complete Budapest winter blocks, the coldest observed 72-hour episode is 6–9 January 2017. Its hourly mean outdoor temperatures average −10.8625°C and reach −16.2°C. Forty-five of its 72 hours have no admitted numerical performance at the selected 55°C supply coordinate; 27 have source-map coverage. The 2025 comparison episode has numerical coverage for all 72 hours.

This is an exact source-map coverage count, not 45 proved equipment-failure hours. P26 separately classifies the cold W55 sector as outside this product's outlet-water applicability, using a plotted boundary at approximately −10°C. The present check does not digitize that plot, create an exact physical cutoff or use it to calculate failure duration. P46's unresolved A−15/W50 coordinate remains separate.

For a building that needs 55°C supply in such weather, the open design question is whether its emitters and insulation can support a lower required water temperature, or whether a different source-supported product or explicitly sized backup is needed. The diagnostic chooses none of these. Lowering the temperature label without checking heat delivery would not establish the same service. This finding concerns the named WM50/W55 reference; it is not a general limitation of heat pumps.

## Reproducible source and temporal boundary

Entry point: `modules.B05.cold_domain_reference.calculate_reference(archive_path=...)`.

The caller supplies the existing external archive identified by `SRC-B05-HUNGARY-HOURLY-HIST-2026`, station 44527, SHA256 `a28ec01c28358f9af0cf846ac69642e80b1f6f0972a138d84f9269c08d3fe417`. The function checks its exact bytes, parses those same verified bytes in memory, reruns the existing P9 complete-winter selector and reconciles all 23 rounded published cold-window statistics and endpoints. It selects the lowest 72-hour mean, with the earliest tied episode first. It also selects the existing 2025 winter episode. No observations or hourly panel are written or returned.

P9 timestamps label source observation endpoints. The new consumer states the corresponding half-open physical interval separately:

| Episode | First/last source endpoint UTC | Physical support UTC | Mean/min/max hourly mean °C | Numeric coverage |
|---|---|---|---|---|
| Historical coldest | 2017-01-06 11:00 / 2017-01-09 10:00 | [2017-01-06 10:00,2017-01-09 10:00) | −10.8625 /−16.2 /−5.0 | 27/72 hours |
| Reference 2025 | 2025-02-18 09:00 / 2025-02-21 08:00 | [2025-02-18 08:00,2025-02-21 08:00) | −2.672222… /−8.0 /3.4 | 72/72 hours |

The historical record extreme is not the empirical 10-year bracket, an official return-period claim or a future national design climate. The original P9 winter convention and records are not changed. The variable used is the source's preceding-hour mean `ta`, not instantaneous `t`; no missing value is imputed.

The exact numeric-map edge comes from the existing source points. P26's qualitative operating-envelope interpretation retains its original authority and graphical precision. The previously admitted manufacturer's envelope PDF is not newly republished or promoted: its original bytes were not recovered after the workspace interruption, and a current read attempt returned 403. Existing P26/P46 provenance remains visible; no new external source authority is asserted.

## Output and tests

The result reports each episode's physical duration, temperature summary and numeric-map availability, with source identity and code/source pins. Complete cold-event capacity deficit, backup size, physical failure hours, electricity and SPF remain unavailable. Neither complete numeric coverage nor absent coverage is promoted to installed service or failure. The existing 2025 annual device, gas and tariff references are unchanged.

Focused checks cover the exact −10°C numeric edge and immediate neighbors, wholly supported and unsupported periods, the warm edge, source-endpoint translation, `ta` versus `t`, missing/nonfinite/boolean temperatures, duplicate/gapped/reversed/non-UTC intervals, wrong source/station, alternate supply/mode substitution and altered archive/manifest identity. Genuine-source replay separately reproduces the two windows and counts. Independent exact-content review, configured aggregate and exact-head hosted CI are required before checkpoint closure.

The exploratory private thermal replay is not a public result or an admitted input. The national heat-demand contrast, programme participation and installed-system reconciliation are not supplied by this source-domain check. B05 slice status and readiness remain unchanged.

Attribution: Adatbázis: Meteorológiai Adattár, HungaroMet Nonprofit Zrt. Manufacturer source: Mitsubishi Electric, exact existing source IDs and provenance in the pinned registries.
