# V1-051: descriptive labour attachment and plan reconciliation

This continues B16-D01 with a previously missing numerical labour dimension,
after reconciling all 58 original V1 tasks against work through V1-050. The new
attachment is a **dated historical description with compatibility diagnostics**.
It does not calculate labour coefficients, FTE, installer capacity, new jobs or
programme economic effects. B16-D01 remains INTEGRATING, B16-D02 remains
NOT_STARTED, and B15's upstream gate and all module-readiness values are unchanged.

## Employment source and meaning

The exact [Eurostat detailed-industry employment source,
nama_10_a64_e](https://doi.org/10.2908/NAMA_10_A64_E), compiled by KSH, supplies
Hungary 2023 domestic-concept employment. The consumer admits EMP_DC (all
employment), SAL_DC (employees) and SELF_DC (self-employed) in two native units:
THS_PER, thousand annual-average persons, and THS_HW, thousand hours actually
worked. Neither is a count of newly created jobs. No full-time annual-hours
denominator is supplied, so there is no FTE conversion.

These are P1/DER official compiled national accounts, not directly observed
intervention effects. [Hungarian employment metadata](https://ec.europa.eu/eurostat/cache/metadata/EN/nama_10_pe_esms_hu.htm)
describes survey, administrative and estimation inputs. Its 2025-10-22 content
update, the 2026-10-03 retrieval and the payload's 2026-10-02 dataset-global update
are separate dates. The exact country-specific employment revision vintage is
not established by them. Nationally resident employed persons are a separate
concept and do not replace employment in resident producing units.

The source totals are 4,784.37 thousand employed persons and 7,984,708 thousand
actual hours. The employee/self-employed splits remain explicit. Source-native
A10 controls and the population/employment table are consistency checks within
the same KSH/Eurostat compilation family, not independent empirical replication.

## One-way classification bridge and missingness

The original [ESA 2010 manual](https://ec.europa.eu/eurostat/web/products-manuals-and-guidelines/-/ks-02-13-269)
Chapter 23 A*64 table supports aggregation of V1-050's 89 disjoint IO leaf slots
into 64 groups. Every leaf belongs to exactly one group. L68A and L68B combine
into L68; aliases such as D/D35 do not become additional industries. The bridge
only aggregates IO amounts. It never distributes employment back to finer IO
leaves or identifies occupations, technologies or installers.

The selected employment core contains 384 positions: 340 numeric and 44 absent.
For each native unit, EMP and SAL have 63 populated groups; U is absent. SELF has
44 populated groups and 20 absent groups. Missing SELF remains null even when
EMP equals SAL. An absent employment observation does not become zero because
an IO sector has zero output or a partial sum equals a published total.

Observed-row person sums differ from the reported total by -0.01, +0.03 and
+0.01 thousand persons for EMP, SAL and SELF. Observed-row hour sums match the
reported total. These are **partial observed-sum diagnostics**, not closure of
a fully observed 64-sector partition. Available EMP-minus-SAL-minus-SELF
residuals reach 0.01 thousand persons and are zero for hours. Display-rounding
compatibility is not a statistical confidence interval or a balancing rule;
no missing or residual cell is filled, repaired or suppressed.

## Accounting compatibility is not assumed

The existing IO reader and its original source/manifest remain unchanged. Its
reference year is 2023 and its national data vintage is 2025. A separate current
[nama_10_a64](https://doi.org/10.2908/NAMA_10_A64) query supplies P1 and B1G controls,
in 2023 current-price million HUF. It does not replace the frozen IO table.

At total economy, current minus frozen P1 is +53,929 million HUF and current minus
frozen B1G is -74,433 million HUF. All 130 group/total comparisons are retained:
for each indicator, 63 differ, T agrees, and U is absent in the current control.
The [Hungarian national-accounts metadata](https://ec.europa.eu/eurostat/cache/metadata/EN/na10_esms_hu.htm)
warns of compatibility differences involving annually compiled SUT/IOT.

These controls prove the accounting snapshots differ. They do not identify the
exact employment vintage, measure an employment revision, or prove every
observed difference is exclusively caused by revision. The attachment therefore
does not claim a coherent matched-vintage labour satellite. Joint intensities
need an aligned snapshot or a separately qualified compatibility bridge. There
is no division of persons/hours by the frozen IO output, no currency or price-base
conversion, and no multiplier or effect calculation.

## What the 58-task reconciliation changes

The three previously accepted task objects remain unchanged: B04-D01 household
tariff table, B08-D01 load source handoff and B09-D01 signed-generation source
handoff. All 58 identifiers, original requirements, dependencies and historical
`existing_at_base` descriptions are preserved. A source subinput is not relabelled
as whole-task acceptance, and no completion percentage is inferred.

This packet applies selected, bounded metadata corrections from that audit;
other evidence-link cleanup remains separately recorded. Current records now
acknowledge already reviewed work:

- B07-D01 records V1-038's conditional runtime and E2 aggregate idle accounting;
  B07-D03 is INTEGRATING for its explicit command/reserve/endpoint mechanics.
  Actual operating policy, legal access and availability remain unresolved.
- B19 is IN_PROGRESS for V1-048's historical joint-window consumer. This does not
  add the still-missing compatible price/timing/programme stress inputs.
- B11 and B17 summaries include their later gas/source-accounting and direct-CO2
  consumers. B12 acknowledges the V1-046 17-year ASS/E2 life subinput while full
  costs/assets and cash flow remain Q.
- B14-D01 is INTEGRATING for its existing original-envelope controls. Current
  remaining funds, commitments, payments and project awards remain unestablished.

B07-D01 is an acceptance-by-reuse candidate, but its original source-condition
mapping still needs qualification before whole-task closure. Permitted operating
temperature is not laboratory ambient. No new national/annual-output or exact-BMS
requirement is imposed on the already admitted aggregate E2 method.

## Forward placeholder truth correction

The empty ACER forward row previously used a historical retrieval day as curve
as-of/delivery metadata and carried an unselected BASE label. It now remains Q
under neutral ID `B03-FWD-ACER-UNQUALIFIED`, with all numeric values and unqualified
dates/scenario empty. The former ID is retained as lineage only. The [official
ACER lead](https://aegis.acer.europa.eu/chest/dataitems/1090/view) and April report
context do not establish an exact assessment date or contract tenor; no April
date is substituted.

The historical source retrieval date and Q-B03-004's requested August window are
unchanged. B03-D01 now records the research already performed. Original export,
intended-use rights, energy basis and instrument/time metadata remain unresolved.
Access restrictions were not bypassed. This corrects provenance without admitting
a wholesale price, importing a zero or expanding B12.

## Verification and remaining work

Original-source qualification, a pre-implementation independent numerical oracle,
consumer tests, genuine-source acceptance, reconciliation review and the canonical
aggregate are distinct checks. Their exact outcomes and file hashes are in
`V1_051_VERIFICATION.json`. Publication and hosted tests remain separately scoped.

The national physical core still needs defensible heat/selection and installed-
electricity evidence; financial results need complete compatible costs/prices;
network and rollout claims need representative capacity and timing evidence;
fiscal/funding results need reconciled available resources. Owner target, horizon,
budget, affordability and decision thresholds are normative choices, not missing
statistics to invent. This attachment supplies none of those defaults.

Source attribution: Eurostat, based on KSH national accounts and ESA 2010,
retrieved 2026-10-03. Decoding, aggregation and diagnostic outputs are project
processing; Eurostat is not responsible for these analyses or conclusions.
Numerical reuse conditions and snapshot lineage are recorded in the manifest.
Original JSON, HTML and PDF files remain external-only and outside the public patch.
