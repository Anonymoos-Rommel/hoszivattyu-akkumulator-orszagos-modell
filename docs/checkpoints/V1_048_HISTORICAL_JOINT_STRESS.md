# V1-048: dated historical weather/load/source-balance windows

Scope: a bounded first consumer for B19-D01 in the existing 58-slice plan.
B08/B09 accepted source handoffs and the completed UTC2025 weather handoff are
reused. No new data, national defaults, heat weights, prices, budget, programme
policy or complete B12 calculation is selected. B19-D01 remains INTEGRATING;
no module readiness or whole-programme acceptance is advanced.

## Why this result is useful

Cold weather, highest load and highest source-reference residual do not need
to occur together. Combining their separately observed maxima would create an
unobserved historical event. The consumer identifies dated, single-metric-selected
windows and preserves the actual coincident values of every retained quantity.
It does not assert that all stressors were jointly extreme. These references
can support later explicitly justified stress tests, without supplying their
intervention, operating policy, probability or feasibility verdict.

## Existing authorities and physical support

`modules/B19/historical_joint_stress.py` consumes the manifest
`registry/b19_historical_joint_stress_manifest.json`. The complete new manifest
is SHA-256-bound by the consumer, including its source evidence, spatial scope,
validation debt and excluded claims. Three existing repository authorities are
separately pinned; no thermal/building/device assumptions are imported.

- `SRC-B08-ENTSOE-ACTUAL-TOTAL-LOAD-2026`: accepted source-native Actual Total
  Load, DER/E2. The original 2025 actual column is used; day-ahead forecast
  never substitutes for observation. Original acquisition date 2026-09-27.
- `SRC-B09-ENTSOE-ACTUAL-GENERATION-TYPE-2026` and
  `SRC-B09-MAVIR-FUEL-NET-OPERATIONAL-2026`: accepted generation and signed
  recovery. B09 source-record Q and QUALIFIED_E2_MODEL_USE remain visible;
  published actual may include provider estimates. Original acquisition date
  2026-09-27. The inherited 9,965 recovery-copy checks remain part of execution.
- `SRC-B05-HUNGARY-HOURLY-HIST-2026` and
  `SRC-B05-HUNGARY-HOURLY-RECENT-20261002`: Budapest station 44527 temperature.
  The existing V1-039 complete-calendar handoff preserves 8,759 historical
  hours plus the exact recent endpoint at 2026-01-01 00:00 UTC. Its original
  source/retrieval/hash lineage remains in the weather admission. Temperature
  is the preceding-hour mean; humidity's different endpoint support is not
  used or promoted to a co-averaged observation.

Existing source methodology:
[ENTSO-E Detailed Data Descriptions v3r4](https://eepublicdownloads.entsoe.eu/clean-documents/Transparency/MoP_Ref2_DDD_v3r4.pdf)
and [HungaroMet hourly description](https://odp.met.hu/climate/observations_hungary/hourly/historical/Leiras_automata_oras-HABP_1H_hist-hu.pdf).
This checkpoint reuses previously qualified source bytes and methods; it does
not claim a fresh public retrieval or a newer revision.

The physical common window is [2025-01-01 00:00 UTC, 2026-01-01 00:00 UTC):
35,040 quarter-hour source intervals and 8,760 complete hourly means. It is a
UTC calendar year. The missing preceding generation hour still prevents a
complete Budapest civil-year panel; a complete meteorological winter or a
return-period sample is not inferred. Fixed UTC durations do not gain/lose an
hour at civil DST transitions.

Spatial scope is Budapest station weather paired with HU bidding-zone source
load/generation. It is not national meteorological representation, causal load
response to weather, or a regional grid-capacity model. Original weather
quality flags are not promoted to homogenized climate evidence.

## Arithmetic and selection

1. Read and verify the accepted eight originals and three grid handoffs through
   the existing historical source consumer. Hash-check the accepted complete
   weather handoff and its interval-start/end, station and source identities.
2. Require exactly four consecutive PT15M records within each physical weather
   hour. For every grid quantity, hourly MWh is the sum of MW × 0.25 h. Window
   mean MW is total MWh divided by the caller-declared physical hours.
3. Preserve injection, withdrawal and signed generation separately, with
   generation = injection − withdrawal and residual = load − generation.
   Negative source residuals are not clipped; withdrawals are not counted twice.
4. Consider all 8,760 − H + 1 complete, contiguous windows starting on UTC hour
   boundaries for explicit integer H. There is no wrap, padding, interpolation
   or incomplete final window. H has no default and is an analysis parameter,
   not an adopted operating duration, policy or risk tolerance.
5. Select minimum mean Budapest temperature, maximum mean source load and
   maximum mean source-reference residual separately. Preserve every exact tie
   and all co-occurring temperature/energy/mean-power quantities in each window.
6. Use rational arithmetic derived from original decimal text for integration,
   rolling sums and ranking. Output exact numerator/denominator plus a 50-digit
   half-even Decimal display. Display rounding never decides a tie or selector.
   Decimal context is isolated from caller precision/rounding/traps.
7. Exhaust the entire upstream stream, including its after-last-yield checks,
   before returning any result. A malformed final quarter or unreconciled
   recovery invalidates the complete result; no earlier partial winner escapes.

These are hourly/window averages. They are not quarter-hour maxima,
instantaneous peaks, installed capacity requirements or dispatch schedules.

## Genuine 72-hour example

H=72 is explicitly declared for this diagnostic, with 8,689 evaluated windows.
It is not a default. All three winners are unique in these inputs. Values below
are rounded display summaries of exact source arithmetic; each row preserves
its own contemporaneous quantities.

| Selector | UTC start (exclusive end is +72 h) | Mean Budapest °C | Mean source load MW | Mean signed generation MW | Mean source residual MW |
|---|---|---:|---:|---:|---:|
| Coldest temperature | 2025-02-18 08:00 | −2.672222 | 6,224.682188 | 4,388.009309 | 1,836.672878 |
| Highest source load | 2025-01-20 07:00 | −1.612500 | 6,518.641910 | 4,421.740521 | 2,096.901389 |
| Highest source residual | 2025-12-15 06:00 | 1.298611 | 6,183.123438 | 3,621.670049 | 2,561.453389 |

The load/residual winners are not the coldest Budapest window. That observation
is a historical coincidence result, not proof of a stable climate/system
relationship. No probability or future stress frequency follows from one year.

The complete-window energy totals reproduce the inherited source accounting:
load 43,210,006.60250 MWh; signed generation 33,946,421.02700 MWh; residual
9,263,585.57550 MWh. These totals are DER/E2 source comparisons. The residual
is not observed imports/exports, unmet demand, LOLE or monetizable savings.
Actual exchange and matching separate storage accounting remain unavailable.

## Unchanged debt and publication boundary

Q-B08-001 and Q-B09-001 retain their existing evidence/validation status. Station
coverage, source quality and the restricted year remain explicit boundaries.
The five national heat debts, selected participant heat, installed-electricity
reconciliation and programme economics remain unaffected. No new source
admission, whole-B19 closure or programme risk ranking is claimed.

The API writes no files and publishes no originals or complete numeric panel.
Callers own external paths and output storage. Public code, methods and narrow
derived summaries do not grant source redistribution rights. This local slice
still requires separately reconciled authorization before public publication.

## Reproduction

The public API requires source_paths for all eight accepted acquisition IDs,
handoff_paths for civil_load/generation/recovery_lineage, weather_path for the
accepted complete calendar handoff, and explicit window_hours. Each path is
consumer-local; source IDs and hash contracts supply semantic authority.

    python -m modules.B19.historical_joint_stress --paths-json EXTERNAL_PATH_MAPPING.json --window-hours 72
    python -m unittest discover -s tests -p 'test_b19_historical_joint_stress.py' -v
    python tools/validate_registry.py
    python -m unittest discover -s tests -v

The external path mapping has exactly source_paths, handoff_paths and
weather_path. Missing originals or mismatched bytes fail closed. Genuine
original-source replay, independent numerical/source reconstruction, focused
adversarial tests and the canonical suite have separate exact-artifact receipts.
Synthetic fixtures test arithmetic and failure behavior; they are not source
admissions. Hosted CI is separate from local validation and is not yet claimed.
