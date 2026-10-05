# V1-032: native UTC2025 historical source-reference balance

Status: bounded consumer implementation and source reproduction; pending exact consumer review and checkpoint acceptance. This checkpoint does not accept a whole B08/B09 slice, module, or programme result.

## Scope and interface

`modules/B08/historical_source_balance.py` reads the already accepted B08/B09 sources through their existing source identities, byte pins and contracts. `iter_historical_source_balance(source_paths, handoff_paths)` yields source-native Decimal interval results; `historical_source_balance(source_paths, handoff_paths)` consumes the complete stream before returning calculated totals, UTC months, technology totals, coincidence and all maximum ties. Neither API writes files or accepts programme profiles, targets, dispatch, battery runtime or future-supply inputs.

Callers supply paths for exactly eight original acquisition IDs: B08B09-P5-R01/R02/R03/R04 and B09-P6-OP01/02/03/04. The three handoff keys are `civil_load`, `generation`, and `recovery_lineage`. Their SHA-256 pins are checked against the accepted V1-016/V1-017 verification records. Paths belong to the calling environment and are never embedded in this consumer's public manifest. The manifest binds original sources, accepted handoffs and unchanged source contracts; it contains no numeric series.

The iterator is a stream: complete-window validation requires exhaustion. Consumers that need an all-or-nothing year result should use the summary API. Original worksheet XML is streamed using the existing hash-verifying B09 reader, ignoring stale worksheet dimension metadata. Recovery storage is bounded to the 4,820 accepted missing-cell records and their 9,965 copy locators; summaries retain months, types and extrema/ties rather than the full panel.

## Native time window and remaining boundary

The complete window is `[2025-01-01T00:00:00Z, 2026-01-01T00:00:00Z)`: 35,040 contiguous interval-start PT15M records and 8,760 hours. Every original interval end, source row, active production type, source unit, geography, and actual-versus-forecast identity is checked. Missing/duplicate/extra, shifted, hourly and out-of-window records fail closed.

The original B08 R01 worksheet supplies all 35,040 load intervals, including the final UTC hour. Its accepted Budapest civil-year CSV overlaps B09 for only 35,036 intervals; all overlapping values are compared exactly. The final four R01 intervals are read directly, with no shift or fill. The B08 R02 companion is retained for its accepted civil-load provenance and byte identity; it does not supply generation.

B09 still lacks `[2024-12-31T23:00:00Z, 2025-01-01T00:00:00Z)`, the preceding hour needed for a complete Budapest 2025 civil year. This consumer therefore does not establish a complete civil year or meteorological winter. The complete in-window Budapest DST transition days retain 92 and 100 intervals.

## Quantity and evidence contract

For each admitted source value `v` in MW, injection is `max(v, 0)`, source withdrawal is `max(-v, 0)`, and signed generation is injection minus withdrawal. The source-reference residual is Actual Total Load minus signed generation. Interval energy is MW × 0.25 h; the accepted runtime kW panel is checked against the exact existing float MW × 1,000 conversion, but runtime floats never enter the source arithmetic. Decimal arithmetic uses an explicit precision of 40 and does not change the caller's Decimal context across iterator yields.

Original nonnegative A75 values are preserved. Only original blank B04/B06/B12 cells can use the accepted signed recovery, with exact timestamps, original cells, deterministic selected source and all identical-copy locators retained. All 9,965 retained recovery-copy values and explicit-offset interval-end timestamps are replayed against their original MAVIR cells. The earlier accepted full-field MAVIR overlap reconciliation remains inherited from V1-017; this is not a new replay of every operational field.

Source withdrawals are gas, oil and reservoir net-operational contributions. They enter once, on the generation side, and are not renamed pumping or measured gross plant auxiliary consumption. Every structural `n/e` cell remains explicit: B03/B07/B08/B10/B13/B18/B25 are excluded from the active type sum, not converted into measured zero. In particular, neither pumped storage B10 nor energy storage B25 is dispatched or zero-filled.

The derived comparison is `DER` from `E2_PROVISIONAL_BASE` inputs. Per-interval source identities preserve the B08 `DER` and B09 record-level `Q` provenance and `QUALIFIED_E2_MODEL_USE`; Q-B08-001 and Q-B09-001 remain validation debt. ENTSO-E published actual generation may include provider estimates. There is no meter-only OBS promotion or raw-reuse rights promotion.

[ENTSO-E Detailed Data Descriptions v3r4](https://eepublicdownloads.entsoe.eu/clean-documents/Transparency/MoP_Ref2_DDD_v3r4.pdf), released 2023-12-15, defines total load using net generation and exchange, including losses and subtracting storage absorption (printed pp. 18–19). Generation is interval-average net output by type, with an estimates caveat (printed p. 74). This targeted definition verification is metadata only; no document snapshot or SHA-256 is claimed. Current-MoP v3.5 context does not replace the directly inspected v3r4 text.

Numerical alignment is not complete physical-accounting validation. Observed cross-border exchange and matching separate storage consumption are not provided. The residual and its positive/negative integrals are not observed imports/exports, unmet demand, adequacy, LOLE, programme headroom or monetizable savings.

## Genuine source execution

The consumer calculated the following from original cells and accepted recovery lineage, rather than reading the prior diagnostic's summary as its numeric input:

| DER quantity from qualified E2 sources | MWh |
|---|---:|
| Actual Total Load | 43,210,006.60250 |
| Generation injection leg | 33,946,572.22775 |
| Source withdrawal leg | 151.20075 |
| Signed generation | 33,946,421.02700 |
| Source-reference residual | 9,263,585.57550 |
| Positive residual integral | 11,464,429.51525 |
| Negative residual magnitude integral | 2,200,843.93975 |

The residual is positive in 27,811 intervals, negative in 7,229, and zero in none. Annual, monthly, per-technology and monthly-per-technology totals conserve exactly. All 490,560 accepted active-type runtime records are checked. There are 485,740 preserved numeric A75 cells, 4,820 recovered cells and 245,280 structural `n/e` cells. Recovery signs are 4,812 negative, six zero and two positive; recovery types are B04: 2, B06: 4,817, B12: 1. No active missing value remains.

| System extremum | UTC interval start | MW | Coincident load / signed generation / residual, MW |
|---|---|---:|---|
| Load maximum | 2025-01-20 11:00 | 7,449.97 | 7,449.97 / 4,630.57 / 2,819.40 |
| Signed-generation maximum | 2025-10-08 09:45 | 7,178.34 | 4,144.29 / 7,178.34 / −3,034.05 |
| Signed-generation minimum | 2025-06-08 02:00 | 1,915.62 | 3,705.44 / 1,915.62 / 1,789.82 |
| Residual maximum | 2025-06-26 17:45 | 3,589.59 | 6,610.60 / 3,021.01 / 3,589.59 |
| Residual minimum | 2025-04-21 09:15 | −3,504.092 | 2,530.31 / 6,034.402 / −3,504.092 |
| Source-withdrawal maximum | 2025-06-30 10:45 | 54.592 | 4,262.39 / 5,591.848 / −1,329.458 |

Each system extremum is unique in these inputs. The API retains all system and technology maximum ties; the genuine type results include 50 geothermal maximum timestamps and three reservoir maximum timestamps. Technology maxima are not summed to construct a coincident system peak.

The accepted runtime's maximum per-cell representation difference is 2 × 10⁻¹³ MW. Its integrated signed-energy difference from source Decimal arithmetic is −8.53550 × 10⁻¹³ MWh. These differences are reported and excluded from the exact source totals.

## Verification and publication boundary

Focused synthetic tests cover endpoint/grid completeness, the final native UTC hour, unit/geography/product/type and forecast substitution, missing active values, structural-zero rejection, source sign and double-counting errors, exact recovery selection/copies, original-cell timestamps, hash/byte identity, provenance and evidence drift, monthly/type conservation, positive/negative/zero residuals, ties and caller Decimal context isolation. Genuine-source execution verifies the existing complete source bundle and handoffs. Independent source/arithmetic replay found no source correction; exact new-consumer review and final aggregate checks belong to the checkpoint acceptance record.

The new four-file scope is the module, its manifest, its focused tests and this checkpoint note. No existing engine, shared registry, source acquisition, source materializer or full numeric panel is changed. Source workbooks, complete panels, execution logs and exact result/freeze evidence remain external or ignored. Full-suite validation, publication and narrow acceptance are separate lead responsibilities.
