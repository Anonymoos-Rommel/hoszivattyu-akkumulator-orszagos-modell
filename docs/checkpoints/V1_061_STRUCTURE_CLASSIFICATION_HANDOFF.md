# V1-061 structural-data handoff

B16-D01 can now be reviewed as one descriptive data handoff. It combines the
already qualified HU2023 national input-output and persons/hours references
with the missing explicit historical import ratios and an official, versioned
classification bridge for domestic expenditure packages. It does not calculate
programme spending, multipliers, net GDP or employment effects.

## Original criterion and reused evidence

The original criterion is unchanged: HU × industry/product × year;
input-output amounts at a declared current/base price and HUF/EUR unit;
import share; value added; employment/FTE; and a bridge between FIGARO codes
and the domestic expenditure package.

| Original field | Exact handoff | Limitation retained |
| --- | --- | --- |
| Industry accounts | V1-050 national Model D industry-by-industry, HU2023, current-price million HUF, basic prices, national vintage2025 | This numerical source is not renamed FIGARO or a product-by-product table. |
| Import share | IMP / TOTAL with TOTAL = DOM + IMP at one named historical origin-use cell | Denominator, source signs, zero and missing values remain explicit; no programme leakage or embodied-import inference. |
| Value added | Existing native B1G and exact accounting reconciliation | Output, GVA and GDP differ; absent imported GVA remains absent. |
| Employment | V1-051 domestic persons and actual hours, with one-way 89-to-64 industry aggregation | No FTE conversion, complete missing-sector imputation, matched-vintage coefficient or installer capacity. |
| Expenditure classification | 27 conditional routes in 11 declared package groups, versioned CPA2.1/NACE Rev.2 and exact FIGARO2026 codes | Actual supplier industry, amounts, price conversion and mixed-invoice split remain unresolved until evidenced. |

The data task supplies a classification reference, not a usable monetary shock
vector. Monetary amounts, suppliers, purchaser/basic-price decomposition and
net-effect assumptions are separate downstream inputs. They are not silently
filled or turned into additional requirements for this descriptive handoff.
B16-D02, B16 module readiness, B12/B13/B15 gates and national readiness remain
unchanged.

## Source-qualified package bridge

The [classification manifest](../../registry/b16_spending_classification_manifest.json)
records six new exact official originals, private retained ESA authority,
row/page witnesses, dependency hashes and all conditional routes. The original
files and detailed source extracts stay outside the public repository.

The groups cover heat-pump equipment and installation, accumulator/inverter
equipment, building electrical and local grid works, alternative envelope
materials, installed insulation and joinery, condition-based window/door goods,
qualifying combined residential works, architectural/engineering/testing
services, vocational education and price-conversion services. These are
classification alternatives or separately evidenced components, not a selected
bill of materials or a requirement to buy every item. Unlisted items and
unresolved mixed-contract components remain unresolved.

The official [FIGARO July2026 description workbook](https://circabc.europa.eu/ui/group/cec66924-a924-4f91-a0ef-600a0531e3ba/library/a6a89ef1-2926-48f9-9268-dd53b6fe7957/details)
supplies actual product and industry codes. For example, machinery is
CPA_C28/C28, construction CPA_F/F, and education CPA_P85/P85. National IO and
employment use P for education. The alias is explicit; a shared label does not
make the code namespaces or source vintages interchangeable. Its July release
label and the UI's June29 modified date are preserved separately.

The [official CPA correspondence workbook](https://circabc.europa.eu/ui/group/d11cc50e-9ad7-41f5-8381-a51f98b792f9/library/065082f9-dd82-4ccb-aa61-d3405df52c0a/details)
exposes material version differences. Old CPA2.1 27.20.23 contains the lithium-ion
subset that becomes CPA2.2 27.20.24; old 27.20.24 instead denotes parts. Old
28.25.13 splits between non-reversible heat pumps and refrigeration/reversible
heat-pump equipment. All native target relations are retained. Their existence
does not establish whole-class equivalence, allocation weights, customs treatment
or classification of a named WM50/battery configuration.

Product class, characteristic NACE activity, actual supplier industry, national
IO key and FIGARO aggregate code are distinct fields. Actual supplier and
monetary allocation are null/Q. The consumer requires explicit CPA2.1 and NACE
Rev.2 arguments and rejects automatic CPA2.2 relabelling. It does not infer
industry from the location of a shop or assign a manufacturer's whole output
to this programme.

The [NACE Rev.2 manual](https://ec.europa.eu/eurostat/documents/3859598/5902521/KS-RA-07-015-EN.PDF)
provides characteristic-activity qualifications. The separate December2020
energy-refurbishment guide supplies context; its CPA2008 table is not relabelled
as CPA2.1. Its repeated construction code and EGSS gross-output treatment are
not silently repaired or imported as a programme demand vector.

## Valuation and double counting

Installed-work output and all materials/equipment embedded in it must not both
be entered as extra final demand. A combined invoice is not automatically
residential construction output; actual contract output and unallocated
residuals must be kept. Window/door replacement remains condition-based.

ESA2010 §§3.56–3.57 and 9.33–9.38 distinguish trade margins from full resale
values and transport margins from separate transport services. Manufacturer or
trader transport embedded in price is not counted again. Household-arranged
third-party freight for final consumption is a separate service. Signed trade
margins are preserved. No margin percentage, VAT treatment, price-year/currency
conversion or CIF-to-FOB numerical bridge is invented.

A subsidy, loan or guarantee finances activity; it is not itself a product
purchase or an additional GDP contribution.

## Historical import ratio interface

`load_historical_import_reference` delegates source admission to the unchanged
V1-050 reader. The original remains pinned to its exact bytes, HU2023 and
MIO_NAC. `read_import_ratio(row=..., column=...)` supplies native DOM/IMP/TOTAL
amounts and an exact reduced numerator/denominator, independent of Decimal
context. It never clamps source-signed values.

The 90 permitted rows (89 leaves plus TOTAL) and 106 use columns yield 9,540
named query positions: 8,065 nonnegative shares, 1,233 undefined zero
denominators, 180 all-origin missing positions and 62 signed accounting ratios.
These are query positions, not a disjoint additive table: TOTAL and control
columns overlap. Account rows, including GVA and output, and overlapping industry
parents are excluded. A positive numerical ratio formed from negative source
amounts remains a signed accounting ratio, not a valid propensity.

## Review and conditional acceptance

First-stage status is REVIEW_REQUIRED. Exact source qualification, independent
consumer review, genuine-source replay and canonical validation must be bound to
the frozen packet. Whole B16-D01 acceptance is a separate metadata stage only
after the actual published implementation passes the approved hosted run with
zero skips. No completion is asserted by this preparation document.

The accepted baseline is commit
`f9ba7b95761ba2083b1f26a5d8131217bea8fe28`. Existing IO and employment code and
manifests remain byte-identical. Classification originals, private conversation,
B13 method preparation and source extracts are excluded from this public patch.
