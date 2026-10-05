# V1-058 — co-occurring historical HU–AT market windows

## Original data task

B19-D01 calls for dated historical windows containing weather, price, load,
supply and timing together, a HU/EU connection, and a separation of statistical
uncertainty, structural unknowns and policy stress. This candidate adds actual
Hungarian and Austrian day-ahead price observations to the existing qualified
UTC2025 station-weather and Hungarian source-load/generation reference.

The reference remains a bounded historical handoff. B19's module dependencies,
readiness and later policy/decision tasks are unchanged. An accepted individual
data handoff does not accept the whole risk module or establish national
B01–B11 readiness. Any later task acceptance must bind the actual reviewed
implementation commit after the approved hosted verification step.

## Source identity and the bounded regional connection

The Hungarian field reuses the accepted V1-057 observation reader. The added
Austrian field is **Austria bidding-zone day-ahead EUR/MWh**, official SMARD
module `8004170`, data ID `4170`. `DE-LU` is the API/page display container,
not the selected price geography. The retained official configuration and
guide identify Austria as a separate bidding zone since 1 October 2018.

The Austrian publisher-hourly CSV is 435,236 bytes, SHA-256
`a16cae90346dbc0fed8a9ed739500a79c6ef0cacf7346337353e33c7e0de6937`.
The original-resolution CSV is 1,740,654 bytes, SHA-256
`ee43eac03fb07017d58dff65aa49e3705b3040dcdc99505a6153ee79e5fa7d0b`.
Both padded exports cover [2024-12-31T00:00Z, 2026-01-02T00:00Z).
Five official JSON weeks corroborate 2,976 overlapping physical quarter-hour
starts and exact prices around year boundaries, DST and the resolution change.
The index identifies source files; it is not itself a complete price series.
These are representations of the same SMARD/ENTSO-E price lineage, not an
independent exchange-price validation.

The independently qualified source has complete 8,760-hour UTC2025 coverage.
All physical hourly starts and original start/end labels align with the
separately qualified Hungarian panel. Negative and zero prices remain valid
observations. No interpolation or clipping is needed in these frozen exports.
This does not prove that the publisher never revised historical values.

One explicitly named Austrian comparator supplies a **HU–AT market-price
connection** within the EU. It does not establish EU-wide representativeness,
physical bilateral flow, available imports or usable reserve. Equal prices do
not prove an unconstrained connection, and a spread alone does not prove a
particular congestion mechanism or causal explanation.

## Rights, preservation and provenance

The regulator's retained source-specific numerical Market data terms support
CC BY 4.0 use with **Bundesnetzagentur | SMARD.de** attribution. The precise
scope is the SMARD-published numerical product. This does not relicense direct
exchange/ENTSO-E exports, editorial pages, site code, the guide or logos.
Selections and derived physical endpoints must be identified as changes;
no endorsement is implied. All original files and detailed real numeric
outputs remain in private preservation, outside this public candidate.

Existing exact rights, configuration, guide and resolution-notice evidence is
reused by source ID and digest. Source filenames and local storage paths are
not semantic authority. The new eight-source acquisition package has its own
frozen provenance, independent review and preserved original responses.

Sources: [SMARD numerical data use](https://www.smard.de/en/datennutzung),
[official download](https://www.smard.de/en/downloadcenter/download-market-data),
[officially linked guide](https://www.smard.de/en/user-guide),
[market-resolution notice](https://www.smard.de/en/15-minute-wholesale-prices-available-218078).

## Physical time, source resolution and vintage

Both CSVs use offset-free local clock labels. The exact requested UTC grid,
local calendar decoding and epoch witnesses establish physical starts. Vienna,
Berlin and Budapest offsets agree throughout this bounded source interval.
The 23-hour spring day and 25-hour autumn day are retained. Repeated autumn
labels denote distinct physical intervals.

Each Austrian CSV has two displayed end-clock anomalies from naive local-time
addition at the DST changes. Source labels remain unchanged; physical UTC ends
are explicitly DER from the identified start and interval duration. The
consumer must not localize the printed end independently or repair originals.

Before 2025-09-30T22:00Z, the original-resolution display repeats each native
hourly price in four quarter rows. These are not four independent quarter-hour
auction observations. From 1 October 2025 local delivery, native auction periods
are quarter-hourly. Publisher-hourly prices remain calculated releases with
their original lexemes. Every padded Austrian hourly price reconciles to the
four-quarter mean within 0.005 EUR/MWh; this observed representation difference
is neither a recovered unrounded price nor a statistical confidence interval.
The publisher's exact tie-rounding rule remains unknown.

The transition notice's displayed publication date is 10 October 2025. Its
midnight +02:00 HTML timestamp falls on the preceding UTC date; the old retained
source ID is lineage, not a different delivery-transition date.

HU and AT are separate retrospective retrieval snapshots on 3 October 2026.
They do not establish an atomic two-zone revision vintage. Per-record revision
and original auction-publication times are absent. HTTP and JSON generation
metadata describe files, not what was known at delivery. Current price or
future-vintage claims are excluded.

## Joint observations and their interpretation

The comparison domain is the existing physical UTC2025 reference. A civil-year
panel with the same number of rows has different endpoints and is incompatible.
The analysis duration must be supplied explicitly. The existing 72-hour example
is a caller-declared illustration, not a stress horizon, policy choice or
national default.

Every complete contiguous hourly-start window is considered, with exact ties
preserved. The result must retain the actual coincident station temperature,
load, injection, source withdrawal, signed generation, source-reference residual,
HU price and AT price. Separate single-metric selections identify dated windows;
the other variables describe that same window. Independently selected extremes
are never combined into one invented event. Exact signed HU−AT differences and
descriptive means are market observations, not monetary procurement results.

HungaroMet temperature is a preceding-hour mean at Budapest station 44527,
without national weather weighting or a causal temperature response. Accepted
B08/B09 source qualifiers remain explicit: load is E2, published generation may
include provider estimates, and signed source withdrawal is retained. The
source load/generation residual is not measured cross-border exchange. Absent
compatible exchange/storage accounting cannot be inferred from a price panel.
Source generation is not future available capacity or an adequacy guarantee.

## Three distinct uncertainty categories

- **Statistical description:** exact same-domain ranks, ties and observed
  co-occurrence over a fixed finite period. Overlapping windows are dependent.
  No future event probability, return period or stochastic confidence estimate
  follows from complete historical coverage.
- **Structural unknowns:** station-versus-zone geography; source estimates and
  unobserved revisions; separate HU/AT retrieval vintages; rounded prices;
  changing native auction resolution; one-year support and no complete
  meteorological winter; absent exchange/storage observations and incomplete
  physical supply accounting; one comparator rather than the EU as a whole.
- **POL stress:** no adopted shock, threshold, risk tolerance or design horizon.
  Later caller/owner-declared policy scenarios remain labelled POL/SCN and
  separate from the historical observations. Missing dependence is not replaced
  by independent random draws or an arbitrary Cartesian low/base/high grid.

The module does not call a wholesale valuation function or construct an energy
purchase profile. Household retail, FX, dispatch, programme cashflow, fiscal
headroom, national savings and feasibility verdicts remain outside this handoff.

## Compatible consumer and private output

`historical_joint_market.calculate_reference(source_paths, handoff_paths, *,
weather_path, hu_source_paths, at_source_paths, window, window_hours)` requires
explicit `window="utc2025"` and a valid integer physical duration. It reuses
accepted weather/load/generation and HU observation consumers, with a distinct
pinned Austrian reader. No source download or silent source selection occurs.

The receipt preserves normalized hourly observations and price lexemes, every
complete coincident window, five separate selectors (cold, load, source residual,
HU price and AT price) with all exact ties, and descriptive rank counts against
the same enumerated domain. Price means are arithmetic time means, not
load-weighted procurement costs. Signed HU−AT spreads retain both directions.

To keep large tie sets exact without a quadratic list of event pairs, temporal
comparison uses each selector's union of tied-window coverage and intersections
of those unions. That is a coverage-set comparison, not a claim that every
individual pair of tied windows overlaps. Original half-open UTC windows and
their identities remain available.

The CLI `tools/materialize_b19_joint_market.py` requires `--paths-json`,
`--window utc2025`, `--window-hours` and `--output-dir`. Its caller-owned paths
map stable source IDs to exact private originals and existing handoffs. All
input sources must finish validation before any result is returned. Source
drift, malformed/missing/extra/shifted intervals and an incompatible domain
fail closed. There is no valuation call, monetary amount or adopted scenario.

The materializer writes only the explicitly selected private receipt, using
the existing hardened private-output guard. This utility reuse does not add a
fiscal model dependency. Public repository paths, unsafe/existing targets and
partial or invalid serialization must fail closed. Detailed real numeric
results are excluded from the public packet; public tests use synthetic data.

## Verification boundary

Source qualification alone is not whole-task acceptance. Exact local consumer,
aggregate-test and independent-review evidence is recorded in
`V1_058_VERIFICATION.json`, with local and hosted stages kept separate. At the
first-stage boundary B19-D01 is `REVIEW_REQUIRED`; any conditional acceptance
must refer to the actual published reviewed implementation after successful
hosted verification, not a placeholder or an unverified later tree.

Observed-domain variable ranks are not programme-driver rankings. B19-D02 owner
thresholds and B19-D03 decision-value prioritization, economic rank reversals
and binding programme constraints still need their own integrated evidence.
No general uncertainty multiplier is introduced.
