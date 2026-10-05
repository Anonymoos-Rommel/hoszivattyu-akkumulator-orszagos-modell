# V1-057 — dated Hungarian wholesale-price source handoff

## Original task and bounded reference

B04-D02 calls for a dated hourly or daily wholesale-price series in EUR/MWh or
HUF/MWh, with the Hungarian bidding zone, source as-of and a boundary separate
from the household bill. It does not require the entire licensed 2015–2026
HUPX history or a forward curve. An optional household dynamic product is not
needed to admit a correctly scoped wholesale source.

This handoff introduces an explicitly selected official SMARD Hungarian
publisher-hourly reference. The padded originals cover
[2024-12-31T00:00Z, 2026-01-02T00:00Z). They support two distinct caller-selected
windows: physical `utc2025` and Hungarian `civil2025`. Each contains 8,760
hours, but the civil-year endpoints are 2024-12-31T23:00Z and
2025-12-31T23:00Z. Equal row counts do not make these intervals identical.

At this first-stage boundary B04-D02 is `REVIEW_REQUIRED`. Any later acceptance
must bind the actual independently reviewed implementation commit and successful
hosted verification, under a separately approved metadata-only step. B04's
module status, readiness and dependencies remain unchanged; accepted source
handoffs do not close national B01–B11 feasibility gates.

## Official access, exact identity and intended use

The official unauthenticated SMARD download page exposes its public export
configuration and read-only export route. The request identifies module
`8000262`, data ID `262`, and explicit UTC-millisecond bounds. The selected
column is **Hungary [€/MWh] Calculated resolutions**. `DE-LU` is the enclosing
page/API display region, not the selected price bidding zone.

The exact publisher-hourly CSV is 435,514 bytes, SHA-256
`83cf09dc3624d1f4e60132163820996017434105ebe018f7c751ae490108f860`.
The original-resolution CSV is 1,741,751 bytes, SHA-256
`007005936f18ecf03030f2d786d621374e4db8777ec2b7f814d2bdfaa572ea50`.
Five official JSON weeks corroborate 2,976 overlapping price values and epoch
starts at year boundaries, daylight-saving transitions and the auction-period
change. They are a second serialization from the same source lineage, not an
independent market-price source or full-year JSON recovery.

SMARD's current numerical Market data/Download terms explicitly state CC BY 4.0
and require **Bundesnetzagentur | SMARD.de** attribution. The guide includes
Hungary and identifies exchanges as primary owners. Intended model use is
qualified for this SMARD numerical product; it does not relicense direct HUPX
or ENTSO-E exports. No HU-specific exclusion was found in the inspected source
materials, while third-party-rights and warranty caveats remain explicit.
Documentation, logos, site source code and legal-source bytes are not assumed
to share the numerical-data licence. All original bytes and detailed numeric
panels remain in private preservation; none is copied into this public patch.

Sources: [SMARD data use](https://www.smard.de/en/datennutzung),
[official download](https://www.smard.de/en/downloadcenter/download-market-data),
[officially linked guide](https://www.smard.de/en/user-guide),
[market-resolution notice](https://www.smard.de/en/15-minute-wholesale-prices-available-218078).
Selection and derived UTC endpoints must be identified as changes, without
implying publisher endorsement or additional restrictions on licensed data.

## Source time, resolution and vintage

The CSV provides offset-free local clock labels. SMARD documents CET/CEST
interval-start conventions. Every displayed start matches the explicit
request-anchored contiguous physical UTC sequence, and the JSON epochs
independently distinguish both autumn folds. Berlin and Budapest offsets agree
throughout this exact source window. Spring and autumn civil days have 23 and
25 hours respectively; repeated local clocks remain distinct physical rows.

Each CSV has two displayed end-label anomalies: the source uses naive local
clock addition at the daylight-saving boundaries. The original label is kept
unchanged. The physical UTC end is **DER** from identified UTC start plus the
declared interval duration, not independently localized from the displayed
end. No original byte is repaired, no repeated hour dropped, and no missing
interval is imputed.

Before 2025-10-01T00:00+02:00 (2025-09-30T22:00Z), the original-resolution
export repeats each hourly price in four quarter rows. These are not four
independent native auction clearings. Later native prices are quarter-hourly.
The hourly export is publisher-calculated throughout and retains its original
price lexemes. In this frozen window every hourly price is within
0.005 EUR/MWh of the four-quarter duration-weighted mean. That is an observed
source-serialization discrepancy, not a recovered unrounded price or a full
model-uncertainty bound. The exact publisher tie-rounding rule is unknown.

The UTC-year contains 8,760 hourly rows and 35,040 displayed quarter rows with
no observed missing/nonfinite prices or duplicate physical starts. All negative
prices are retained. No null-input interpolation is needed in these acquired
files; this does not prove the upstream feed never revised or reconstructed
values. Source guidance allows later corrections.

As-of means retrospective retrieval on 3 October 2026. The CSV has no per-row
original publication time or revision identifier. Configuration version and
weekly JSON generation/ETag/Last-Modified describe their own files, not what
was known at the original auction or delivery date. This is not a forecast.

The transition article's visible publication date is **10 October 2025**; its
HTML datetime is 2025-10-10T00:00:00+02:00, equivalent to 9 October at 22:00Z.
The existing source ID ending `20251009` and frozen author notes are retained
as lineage. Operative publication metadata uses the displayed date and keeps
it separate from the **1 October delivery transition**. Numeric evidence is
unaffected.

## Compatible consumer and valuation boundary

`read_wholesale_reference(source_paths, *, window)` uses exact supplied local
source paths and a pinned manifest. The caller chooses `utc2025` or
`civil2025`; no source is downloaded or selected silently. Normalized rows keep
source identity, labels and price lexemes beside exact rational prices and
derived physical UTC endpoints. Source drift, incorrect HU identity, malformed
or incomplete rows and incompatible time contracts fail closed.

`value_wholesale_reference` additionally requires aligned nonnegative imported
energy in MWh and the explicit convention
`CALLER_DECLARED_HOURLY_FLAT_WHOLESALE_ENERGY_ONLY_REFERENCE`, with
`within_hour_profile=FLAT` and a caller-supplied profile ID. Exact rational
arithmetic preserves negative-price credits and avoids ambient Decimal-context
rounding. A supplied unit or varying reference profile remains a declared
scenario, never a programme default.

After the auction-period change, a publisher-hourly price supports this
explicit hourly-flat reference convention. It does not exactly price arbitrary
uneven quarter-hour procurement, dispatch or export; source-cent rounding
remains visible. Daily averages cannot silently be distributed over varying
hourly energy either. Valuation is in EUR and excludes household tariffs,
retail spread, VAT/network/fixed charges, FX conversion, contractual settlement,
export remuneration, dispatch permission, forecasts and programme benefits.

The private materializer writes a `receipt.json` containing normalized source
rows and any explicitly requested valuation. It reuses the unchanged hardened
B13 private-output guard, as a storage utility only. That dependency does not
add a fiscal model gate or financial authority. Numeric output is never a
public repository artifact, and existing/unsafe output paths fail closed.

## Preserved neighbouring boundaries

Existing A1/B/H household tariff arithmetic and the optional spread-inclusive
MVM D backcast are unchanged. MVM prices are not inverted to manufacture a
wholesale original. Its missing historical original remains a separate
preservation limitation; it is not needed for this new source handoff.

No retail tariff, FX rate, national representative weight, household entitlement,
operational permission, actual procurement cost, programme scale or forward
path is inferred. A matched B19 price integration remains a subsequent distinct
source-to-consumer task. Existing event timestamps already establish historical
window timing; future probabilities and owner decision thresholds belong to
separate later uses, not invented prerequisites for this dated price handoff.
