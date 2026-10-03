# V1-050: dated Hungarian industry-structure source handoff

This continues **B16-D01** in the approved 58-task plan. It supplies the first
B16 numerical economic-structure reference. The task remains **INTEGRATING**;
whole-module readiness stays 0. B16-D02 programme effects and the B15 dependency
gate are unchanged. A historical national-account table is not a programme
spending vector or a national deployment default.

## Exact source and applicability

The source is Eurostat's [national industry-by-industry input-output table,
naio_10_cp1750](https://doi.org/10.2908/NAIO_10_CP1750), compiled and transmitted by
the Hungarian Central Statistical Office. The frozen query selects Hungary,
2023 and MIO_NAC. It contains 40,390 numeric cells in the domestic-origin,
imported-origin and total-use tables. Original JSON and explanatory HTML files
are retained externally; the public change contains code, tests, provenance and
interpretation, not original source files.

The units are **million HUF at 2023 current prices**, with the table's basic-price
boundary. They are neither constant-price amounts nor 2026 purchaser-price
project costs. The [Hungarian metadata](https://ec.europa.eu/eurostat/cache/metadata/EN/naio_10_n_esms_hu.htm)
identifies the 2023 table as the **2025 national data vintage**. The payload's
2026-09-30 dataset-global update is a separate date. A same-source output-series
probe has no Hungarian 2024 output value, although 2024 exists in its global
time dimension. The latest populated Hungarian year in that probe is 2023;
there is no extrapolation or missing-year zero substitution.

These are P1, DER official compiled national accounts. Industry-by-industry
construction uses Model D's fixed product-sales-structure assumption, drawing on
statistical and administrative sources, balancing and estimation. Exact
transcription and accounting closure do not turn the cells into independently
observed programme transactions. Other KSH/Eurostat national-account consumers
share part of this source lineage and are not independent corroborating samples.
The metadata's newer specific annual-publication statement from end-2025 is
retained alongside its older five-yearly wording.

[Eurostat's valuation explanation](https://ec.europa.eu/eurostat/en/web/esa-supply-use-input-tables/information-data)
states that national SUIOT imports use CIF; FIGARO's inter-country tables use a
different FOB convention. This handoff does not equate the two or derive a
CIF/FOB, retail/basic-price, currency or inflation bridge.

## Disjoint industries, signs and missingness

The payload contains 104 industry-labelled positions plus accounting rows and
final-use columns. Fifteen industry aggregates overlap their finer children;
summing all positions would double-count them. The admitted partition has
**89 disjoint source-native leaf slots**, retaining the separate L68A/L68B
real-estate categories. The extra source slot is consistent with the explicit real-estate split; this
reconciliation is inferred from the payload labels, while the metadata states
88-industry detail. T97, T98 and U have
explicit-zero intermediate columns and are retained; they are not deleted to
force a different count. Both classification and source positions are pinned.

Each flow has all 7,921 cells in the 89-by-89 intermediate matrix. Outside these
cores the full cube has **4,259 sparse absent positions**. Absence remains null,
never an inferred zero. For example, an imported-flow value-added row is not a
reported zero value-added observation. The domestic table's imported-input
account row is likewise not a second domestic-origin flow. DOM and IMP describe
origin, not the geography of final demand; domestic output can be exported.

Signed values are preserved, including within the intermediate matrices:

- H53 to L68A: total -6,784 = domestic -6,368 plus imported -416 million HUF
- K64 to L68A: total -247,081 = domestic -232,011 plus imported -15,070 million HUF

Their detailed economic explanation is not established by the acquired
metadata. This is explicit interpretation debt before any positive-coefficient
or multiplier use. These values are not missingness, floating-point errors or
permission to clamp to zero. Inventory and tax/subsidy signs also remain intact.

## Accounting handoff

The consumer reads an explicitly supplied, exact pinned original file and
returns its source-native cells and bounded reconciliations. It performs no
network request, source replacement or output-file materialization. Its
manifest binds the source, code lists, year, units, partition and interpretation.

The qualified source's 16 identity families have exactly zero residual at the
published integer-million-HUF resolution. These include all leaf row/column
sums; overlapping-aggregate children; total versus domestic plus imported use;
output, adjusted intermediate consumption, net product taxes and gross value
added; domestic-table imported inputs; supply; value-added components; and
signed final-use/capital-formation identities. Accounting closure describes
this compiled source table, not the precision of the underlying economy.

A useful source control is intermediate use: 40,986,434 domestic plus 40,971,399
imported equals 81,957,833 million HUF. Reported gross output is 149,793,419 and
gross value added is 65,157,153 million HUF. Gross output is not GDP, neither is
a programme benefit, and these quantities cannot be added as separate benefits.
No programme shock, matrix inverse, multiplier, employment or fiscal result is
computed.

## Reuse and remaining dependencies

[Eurostat's copyright notice](https://ec.europa.eu/eurostat/help/copyright-notice)
supports statistical numerical reuse with attribution, subject to its specific
exceptions. Qualification covers this HU-only national table, not unrestricted
world-table redistribution. Source: Eurostat, based on KSH national accounts,
retrieved 2026-10-03. Decoding and reconciliations are project-derived processing;
Eurostat is not responsible for these analyses or conclusions. Original source
files remain external-only in this checkpoint.

A programme application still needs a supported expenditure-to-industry
crosswalk, domestic procurement boundary, purchaser/basic-price and time/currency
bridges, matching employment/hours/FTE evidence, capacity and displacement or
alternative-use assumptions, and the required B11/B12/B13/B15 outputs. The broad
industry labels do not identify heat-pump, battery or installer cohorts. No
employment table, positive-technology interpretation, net GDP/jobs, fiscal
headroom, national deployment or current capacity claim is admitted.

## Verification

Original-source acquisition and interpretation qualification, independent
source/oracle review, hermetic consumer tests, genuine-source acceptance and
canonical aggregate testing are separate checks. Exact file hashes and their
actual outcomes are recorded in `V1_050_VERIFICATION.json`. Source qualification
alone is not whole-slice acceptance or hosted CI. Publication and hosted tests
are separately authorized after the exact local packet is frozen.
