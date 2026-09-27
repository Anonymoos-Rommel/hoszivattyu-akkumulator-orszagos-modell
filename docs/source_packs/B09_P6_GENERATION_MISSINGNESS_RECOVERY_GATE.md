# B09-P6 — Generation missingness recovery authority gate

**Date:** 2026-09-27  
**Canonical parent main:** `cbe0965197a01c2d9ba3a92723cd22969e49b9d5`

## Purpose

P5 acquired the real 2025 Hungarian ENTSO-E A75 panel but retained 4,820 affected MTUs because three expected numeric production-type series contain literal single-space source cells:

- Fossil Gas: 2
- Fossil Oil: 4,817
- Hydro Water Reservoir: 1

P6 narrows the recovery route. It does not impute any value.

## 1. ENTSO-E area-view cross-check is exhausted

Three registered GUI exports of the identical 2025 A75 product were independently acquired:

- BZN|HU
- CTA|HU
- Hungary (HU)

Their workbook byte hashes differ because the workbook carries the selected area label, but after normalizing that label the sheet content is identical.

Normalized sheet-content SHA-256:

`09ede94527e3539fa38885de859d236e7df0875933409069d3020911373b25fb`

The exact same single-space cells occur in all three views.

Therefore:

`COUNTRY_VIEW != INDEPENDENT_RECOVERY_SOURCE`

`BIDDING_ZONE_VIEW != INDEPENDENT_RECOVERY_SOURCE`

`CONTROL_AREA_VIEW != INDEPENDENT_RECOVERY_SOURCE`

for Hungary on this A75 product.

## 2. Primary recovery source: MAVIR aggregate fuel-type publication

The official MAVIR publication surface exposes export controls for start time, end time, resolution and file format and lists both:

- **Erőművi termelés tüzelőanyag szerinti bontásban - Nettó elszámolási mérés alapján**
- **Erőművi termelés tüzelőanyag szerinti bontásban - Nettó üzemirányítási mérés alapján**

Canonical official page:

https://rtdwweb.mavir.hu/rtdwweb/webuser/GenerateChartsServlet?hunLang=hu-hu&tabId=tab7679

Both 2025 datasets must be acquired.

Reason:

`SIMILAR TITLE != SAME MEASUREMENT BOUNDARY`

No MAVIR value may be spliced into A75 until the candidate series is validated on all available overlapping non-missing A75 intervals for:

- production-type mapping;
- unit;
- PT15M interval alignment;
- timezone/interval start semantics;
- numeric scale;
- sign;
- measurement boundary;
- agreement/tolerance.

The measurement basis that best reproduces the complete A75 observations becomes the only admissible recovery candidate.

## 3. ENTSO-E A73 unit-level route is secondary only

ENTSO-E's official implementation guide defines:

- A75 / A16: Actual Generation per Production Type;
- A73 / A16: Actual Generation Output per Generation Unit.

However Commission Regulation (EU) No 543/2013 Article 16(1)(a) requires actual generation output per generation unit only for units with installed generation capacity **100 MW or more**.

Therefore:

`SUM(A73 PUBLISHED UNITS) != PROVEN COMPLETE A75 PRODUCTION_TYPE TOTAL`

unless an independent completeness proof establishes that all contributors to the relevant production type are captured.

A73 can still be useful to:

- validate large-unit contributions;
- explain individual source gaps;
- bound or cross-check a MAVIR recovery;
- recover a value only where completeness for that production type and interval is separately proven.

It is not the preferred aggregate repair route.

## 4. Fail-closed admission

Current policy remains:

`LITERAL_SINGLE_SPACE != ZERO`

`MISSING != INTERPOLATED_BY_DEFAULT`

`MAVIR_VALUE != A75_REPLACEMENT_WITHOUT_OVERLAP_VALIDATION`

`A73_UNIT_SUM != COMPLETE_AGGREGATE_WITHOUT_COMPLETENESS_PROOF`

The current 4,820 affected MTUs remain blocked.

## 5. Exact next acquisition

Acquire both official MAVIR 2025 fuel-type exports, preferably at PT15M:

1. net settlement measurement basis;
2. net operational measurement basis.

For each raw export preserve externally:

- exact bytes;
- filename;
- SHA-256;
- retrieval timestamp;
- source URL;
- selected date range;
- selected resolution;
- file format.

Raw bytes remain external-only until reuse/publication authority is established.

After acquisition:

1. parse source-native categories;
2. align timestamps to A75;
3. compare each candidate category against all complete overlapping ENTSO-E intervals;
4. select or reject measurement basis;
5. recover only values whose semantic and numeric equivalence is demonstrated;
6. recompute remaining missing MTUs.

## 6. Blocker state

Q-B09-001 remains:

- evidence tier: **E3**
- blocker class: **MODEL_BLOCKER**
- model blocker: **yes**

Exact residual:

`MAVIR_2025_FUEL_TYPE_EXPORTS_REQUIRED -> SEMANTIC_ALIGNMENT_AND_OVERLAP_VALIDATION_REQUIRED -> SOURCE_GAP_RECOVERY_REQUIRED`

No readiness uplift.

## Official references

MAVIR public data export:
https://rtdwweb.mavir.hu/rtdwweb/webuser/GenerateChartsServlet?hunLang=hu-hu&tabId=tab7679

ENTSO-E Transparency Platform:
https://transparency.entsoe.eu/

ENTSO-E data extraction implementation guide:
https://transparency.entsoe.eu/content/static_content/download?path=%2FStatic+content%2Fweb+api%2FIG-for-TP-data-extraction-process.pdf

Commission Regulation (EU) No 543/2013:
https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32013R0543
