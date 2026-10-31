# B02-P114 - Conditional Hungarian 2023 window-glazing empirical interval

## Scope and published observations

The Eurostat 2023 EU-SILC assessment reports Hungary HC004 glazing categories:
only single 16.2%, only double 63.1%, triple or more 12.2%, mixed single/multi
5.3%, mixed double/triple 3.2%, don't know 0.0%. Published single-glazing
presence is 16.2% + 5.3% = 21.5%; this is not a glazing-area proportion.
HC001 reports district 15.4%, central 6.1%, individual 78.1%, non-fixed 0.3%,
no heating 0.1%, don't know 0.0%; the complement of district is 84.6%.
HC001 identifies the mainly used heating system, not every secondary system.

The reference period is 2023. Both variables have household/current/H-file
scope (assessment pages 9-12). HC004 is glazing type, not a renovation event
or measured Ug/Uw (pages 22-23). No later-stock transfer is admitted.

## Evidence for a common scope and its remaining limits

The Hungarian rows appear in Annex 1, Distribution of filled values, pages
165 and 168. Annex 2 reports missing flag -1 as 0.0% for both variables
(page 253), HC004 not-applicable flag -8 as 0.0% (page 271), and survey/interview
flag 1 as 100% for both (page 273). This corroborates common intended scope
and published near-complete coverage. Rounded flags do not identify exact
denominators, weights or release versions; 0.0% is not proof of exact zero.
Missing metadata does not establish incompatible populations or unweighted tables.

Hungarian Annex 5 (2024 quality report) describes generalized weight sharing,
DB090/RB050, raking and trimming. Annex 11 describes the 2019-2024 revision
in 2025 Q2 using 2022 Census controls; new weights affected all indicators,
while other processing refinements concerned income. The assessment's data
extraction date is 1 August 2025 (page 7). This chronology is compatible with
the revision, but no exact HC001/HC004 table weight/release binding is supplied.

## Preserved conditional Frechet algebra

Let A = published single-glazing presence = 0.215 and
B = published non-district marginal = 0.846. If these refer to the same
empirical probability measure, without independence:

max(0, 0.215 + 0.846 - 1) = 0.061;
min(0.215, 0.846) = 0.215;
0.061 / 0.846 = 0.072104018913;
0.215 / 0.846 = 0.254137115839.

The preserved conditional empirical interval is
[7.2104018913%, 25.4137115839%]. It is not a proven uncertainty-free national
population bound or observed HC001 x HC004 joint table. Sampling and publication
rounding uncertainty remain separate even if the common empirical measure is
later confirmed. Many computed digits do not imply that precision in observations.
No confidence level, replacement bound, independence assumption or Q-to-zero
conversion is introduced. A defensible aggregate proof may suffice; exhaustive
microdata is not automatically required by population-inference policy.

## Glazing reference comparison and separate physical gaps

The recorded 9/2023 EKM glazing reference is U <= 1.0 W/m2K; official Appendix 2
gives ordinary 4 mm glazing 5.8 W/m2K. This supports a reference-class comparison,
not a measured Ug/Uw or legal retrofit duty for each surveyed record.
Reference double-glazing values include 2.9, 1.6, 1.2 and 1.1 W/m2K;
layer count does not establish whole-window compliance. Frame, spacer, geometry
and actual construction are needed. The recorded wood/PVC whole-window 1.10 W/m2K
reference cannot be applied to HC004 as an observed Uw value.

The existing function and legacy state key for a single-glazing deficit mean
this reference comparison only. Explicit record-level proof remains false.

## Explicit validation debt

- HC001_HC004_TABLE_DENOMINATOR_WEIGHT_RELEASE_BINDING_REQUIRED
- HC001_HC004_SAMPLING_AND_PUBLICATION_ROUNDING_UNCERTAINTY_REQUIRED
- HC004_HOUSEHOLD_TO_B02_DWELLING_POPULATION_BINDING_REQUIRED
- CURRENT_MULTIGLAZED_WINDOW_REALIZED_UW_DISTRIBUTION_REQUIRED
- HC001_HC004_2023_TO_TARGET_PERIOD_STOCK_BRIDGE_REQUIRED

No 1:1 household-to-dwelling identity, Census denominator substitution, or later
year stock identity is admitted. The 2025 ilc_enevh_01 persons/renovation share
is a different estimand and does not close these debts.
KEHOP/FAIR 1103 remains a secondary technical calibration route, not the sole
route and not a representative national stock estimator by itself.

## Unchanged overall result

The conditional P114 calculation is not added to P102 or used to tighten it.
Existing calibrated retrofit floor 82.7861029945%, HP_ONLY lower 0%, HP_ONLY
upper 17.2138970055%, B02 readiness 55%, PEAK_LOAD_EFFECT 50% remain unchanged.
This classification correction is not source adoption or full B02 closure.

## Sources and provenance limits

Existing stable source IDs remain authoritative for their recorded claims:
SRC-B02-EUROSTAT-SILC-2023-ENERGY-MODULE-ASSESSMENT (published HC001/HC004);
SRC-B02-EU-2021-2052-HC001-HC004 (variable semantics);
SRC-B02-HU-2023-EKM-CURRENT-U (recorded technical requirements);
SRC-B02-HU-EKM-APPENDIX2-GLAZING-U (reference glazing values).
This correction performs no new legal-currentness or model-adoption decision.

Methodology checked against the original official documents on 2026-10-31:
- https://ec.europa.eu/eurostat/cache/metadata/Annexes/ilc_simsilc_hu_an_Weighting_procedures.docx
- https://ec.europa.eu/eurostat/cache/metadata/Annexes/ilc_simsilc_hu_an_revision_2019_2024.docx
- https://ec.europa.eu/eurostat/documents/1012329/22538672/EU_SILC_2023_modules_assessment.pdf/e9ed8f81-ccd2-f4f0-bb51-82747cc37ecc?t=1762965861237

Original bytes and audit receipts are retained in the separate private project
archive; no external DOCX/PDF bytes or transformed full-text copies are added
to this repository. Document existence is not exact table weight/release proof.

## Boundaries

SINGLE GLAZING PRESENT != WHOLE-WINDOW UW VALUE
DOUBLE/TRIPLE GLAZING != CURRENT UW COMPLIANCE
HOUSEHOLD SHARE != EXACT DWELLING COUNT
MARGINALS + FRECHET != OBSERVED JOINT TABLE
CONDITIONAL EMPIRICAL INTERVAL != TRUE POPULATION HARD BOUND
REFERENCE 2023 != LATER TARGET STOCK
GLAZING REFERENCE COMPARISON != RECORD-LEVEL DEFICIT OR LEGAL DUTY
