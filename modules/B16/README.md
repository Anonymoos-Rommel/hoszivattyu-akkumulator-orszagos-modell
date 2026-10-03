# B16 — Hungarian historical industry-structure reference

Status: **bounded B16-D01 source handoff only**. This package reads and reconciles
one exact official 2023 Hungarian industry-by-industry input-output table. It
neither completes B16-D01/B16 nor releases the B15 dependency gate.

## Source and permitted meaning

- Stable source: `SRC-B16-EUROSTAT-KSH-HU-IOT-2023`, Eurostat `naio_10_cp1750`,
  compiled by KSH. [Official dataset](https://doi.org/10.2908/NAIO_10_CP1750).
- Country HU, year **2023**, annual, source unit **MIO_NAC = million HUF**;
  current prices and basic-price table, national data vintage **2025**.
- The dataset-global update of 2026-09-30 is not a country-specific revision,
  reference year or current-period estimate. This snapshot was retrieved
  2026-10-03. An independent coverage query has latest populated HU output
  year 2023; the dataset-wide 2024 member does not supply a Hungarian value.
- Evidence is **P1 / E1 / DER**: official compiled and balanced national accounts,
  including a Model D transformation with fixed product-sales structure.
  It is not an independently measured census of transactions or programme effects.
- KSH and Eurostat dissemination share national-account lineage. Other KSH-derived
  consumers are not independent evidence just because their publisher/table differs.

The [pinned manifest](../../registry/b16_industry_structure_reference_manifest.json)
records source/metadata/coverage/valuation/reuse identities and attribution. The
reader binds its exact manifest bytes and exact source original SHA256/size.
No caller-supplied manifest or hash override is supported. Original response bytes
remain external-only and are not distributed in the repository or test fixtures.
A changed publisher response requires a new qualified source snapshot and review.

## Minimal read-only interface

```python
from modules.B16.industry_structure_reference import (
    HISTORICAL_ACCOUNTING_REFERENCE, load_industry_structure_reference,
)

reference = load_industry_structure_reference(
    "/explicit/private/path/to/reviewed-original.json",
    source_id="SRC-B16-EUROSTAT-KSH-HU-IOT-2023",
    reference_year=2023,
    unit="MIO_NAC",
    claim=HISTORICAL_ACCOUNTING_REFERENCE,
)
cell = reference.read_cell(row="H53", column="L68A", flow="TOTAL")
# cell.value == -6784, integer million HUF; cell.truth_status == "DER"
missing = reference.read_cell(row="B1G", column="TOTAL", flow="IMP")
# missing.value is None; missing.truth_status == "Q", never imported GVA = 0
report = reference.report()
```

Every load requires explicit source path, source identity, year, unit and claim.
There is no downloader, directory search, automatic year/programme/scenario
selection, storage writer or implicit currency/price-base conversion. The source
payload, source-native dimension labels/positions, cell metadata and returned
report are deeply immutable. An unknown code raises an error; an omitted valid
source coordinate returns null/Q. Source values use native integers, so hostile
ambient Decimal precision, rounding, exponent bounds and traps cannot alter sums.

The CLI prints a derived reference report to stdout only:

```sh
python -m modules.B16.industry_structure_reference \
  --source /explicit/private/path/to/reviewed-original.json \
  --source-id SRC-B16-EUROSTAT-KSH-HU-IOT-2023 \
  --reference-year 2023 --unit MIO_NAC \
  --claim HISTORICAL_ACCOUNTING_REFERENCE
```

## Partition, signs and account boundaries

The 123 source row codes and 121 column codes mix industries, 15 overlapping
parent groups, totals and supplementary accounts. The checked non-overlapping
partition contains **89 source-native leaf slots**, retaining L68A and L68B.
Metadata states 88 industries. The extra source slot is consistent with the
explicit L68A/L68B split; this reconciliation is inferred from payload labels,
not an explicit explanation in the metadata. Finer labels do not establish
independently observed detail. T97/T98/U zero intermediate-input columns remain
included. T97 output and GVA are nonzero. Parent groups are reconciled against
children, never added to leaf totals.

All three 89 × 89 cores are complete: 7,921 cells each. Across the full cube there
are 40,390 numeric cells and 4,259 missing sparse positions. Published zero,
negative value and missing key remain distinct; absent flags are not invented.

- DOM means domestic-origin uses, including exports.
- IMP means imported-origin uses, including export uses.
- TOTAL = DOM + IMP is checked in the origin-use block only. It is not a rule
  for the supplementary accounts: IMP GVA/output cells are absent. P7 and TS_BP
  account rows are TOTAL-only; the supplementary IMP row is DOM-only.
- Trade-detail rows P7_U2/P7_U3 and columns P6_U2/P6_U3 are unavailable, not zero.
  Optional all-origin missing positions are counted separately from tested
  identities. Missing required cells or asymmetric origin availability fail closed.
- National SUIOT import values follow CIF convention. No bridge to FIGARO
  FOB/basic-price trade, COMEXT trade, energy retail prices or programme spending
  is supplied by this package.

The signed core anchors are H53 → L68A: −6,784 = −6,368 + −416 and K64 → L68A:
−247,081 = −232,011 + −15,070 (TOTAL = DOM + IMP, million HUF). The detailed economic
cause is not explained in the acquired metadata. Preserve that interpretation
debt before any structural-response use; do not clamp values, assume positive
coefficients or reinterpret them as missing.

## Accounting controls and verification

The report provides **16 exact integer accounting-identity families**: core origin
splits; both-axis leaf totals and parent/child sums; output, GVA, intermediate
consumption and net-product-tax bridges; domestic imported-input rows; output and
import total-use identities; value-added components; consumption, capital and
export final uses; signed inventory/valuables; total uses and full use-block
origin splits. It includes tested/unavailable counts and maximum residuals.
Required missing cells or nonzero residuals reject admission.

Observed source accounting controls, million HUF, at the historical boundary:

- Basic-price intermediate use: 40,986,434 DOM + 40,971,399 IMP = 81,957,833 TOTAL
- Intermediate use 81,957,833 + net product tax 2,678,433 = adjusted consumption 84,636,266
- Adjusted consumption 84,636,266 + GVA 65,157,153 = gross output 149,793,419
- Gross output 149,793,419 + imports 57,506,061 = total supply/use 207,299,480

These are separate accounting concepts. Gross output, GVA, total supply and GDP
are not interchangeable. Exact identities show internal consistency at the
published precision; they do not establish causal responses or net benefits.

Hermetic suite:

```sh
python -m unittest discover -s tests -p 'test_b16_industry_structure_reference.py'
```

Tests use an authored two-industry signed accounting fixture, not the original
panel. They exercise all 16 identities with targeted corruptions, missingness,
source/manifest identity, sparse JSON syntax, source unit/date/shape, immutable
values, partition overlap and Decimal independence. A genuine-source acceptance
run requires the explicit external original and is separate from hermetic CI.
Private parser/reconciler helpers are test mechanisms, not source admission APIs.

## Not supplied

No programme shock, inverse, multiplier, technical coefficient, expenditure map,
current/national deployment default, jobs/employment/FTE, net GDP, fiscal effect,
financing result or currency/price conversion. Employment inputs do not exist in
this handoff. Separate sources and explicit applicability contracts would be
required, including price year, counterfactual, crowding-out and capacity limits.
B16-D02 and wider B16 acceptance remain open.

Source: Eurostat, `naio_10_cp1750`, Hungary 2023, compiled by KSH; retrieved
3 October 2026. Accounting checks and summaries are project-derived. Eurostat is
not responsible for the transformation or conclusions. Numerical reuse with
attribution is qualified; source-original republication is not authorized here.
