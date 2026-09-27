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


## 7. Settlement-basis acquisition — 2026-09-27

Human acquisition context confirms that the first four MAVIR fuel-type XLSX exports are:

**Erőművi termelés tüzelőanyag szerinti bontásban - Nettó elszámolási mérés alapján**

External-only artifacts:

- `export_1.xlsx` — SHA-256 `b0c1a200cad877732c44799ef7efef328bf4fdd5cec9df5d25610d3844a372df`
- `export_2.xlsx` — SHA-256 `935c538b1116c2df565ec18873908e4e70ced71cdd0f6644a3c4d6e69d8508bb`
- `export_3.xlsx` — SHA-256 `100a7eea4f4a3ba9f4cf7e6313dcd4a7fb43b2e5359d42b2f17098cf05108edf`
- `export_4.xlsx` — SHA-256 `96e570491e1c7bb4fd61961ceec5aa56b6a4f3d09f92f80f02e74efb4465fce3`

The four files form a complete 2025 source panel after converting source-local offset-aware interval-end labels to UTC interval starts:

- unique PT15M UTC starts: **35,040**
- duplicate UTC starts: **0**
- time gaps: **0**
- missing numeric source values across the 15 exported generation fields: **0**

The candidate therefore contains a numeric value for every current A75 source gap:

- Fossil Gas: **2 / 2**
- Fossil Oil: **4,817 / 4,817**
- Hydro Water Reservoir: **1 / 1**

### Complete-overlap validation against ENTSO-E A75

For intervals where A75 itself is numeric:

| Production type | Overlap n | Correlation | MAE (MW) | Mean MAVIR-A75 bias (MW) |
|---|---:|---:|---:|---:|
| Fossil Gas | 35,038 | 0.99584611 | 82.52844326 | -82.44199095 |
| Fossil Oil | 30,223 | 0.99793166 | 0.09153049 | -0.08209523 |
| Hydro Water Reservoir | 35,039 | 0.99981660 | 0.05858135 | -0.04823614 |

Interpretation:

- **Fossil Oil** — very strong candidate equivalence, but not admitted until the second MAVIR measurement basis is compared.
- **Hydro Water Reservoir** — very strong candidate equivalence, but not admitted until the second MAVIR measurement basis is compared.
- **Fossil Gas** — high shape correlation but a large systematic level offset; the settlement-basis series is **not directly spliceable** into A75.

Therefore:

`COMPLETE_CANDIDATE_COVERAGE != CANONICAL_RECOVERY_ADMISSION`

and:

`HIGH_CORRELATION != SAME_MEASUREMENT_BOUNDARY`

The exact next acquisition is now only:

**Erőművi termelés tüzelőanyag szerinti bontásban - Nettó üzemirányítási mérés alapján**

for the same full 2025 PT15M period.

Updated residual:

`NET_OPERATIONAL_2025_EXPORT_REQUIRED_FOR_DUAL_BASIS_SELECTION -> DUAL_BASIS_OVERLAP_SELECTION_REQUIRED -> GAP_RECOVERY_ADMISSION_REQUIRED`


## 8. Net-operational acquisition and dual-basis selection

The second official MAVIR measurement basis is now acquired:

**Erőművi termelés tüzelőanyag szerinti bontásban - Nettó üzemirányítási mérés alapján**

Exact external-only source hashes are recorded in:

`registry/b09_p6_mavir_operational_acquisition.csv`

The raw files overlap and extend beyond the canonical year. P6 therefore uses the explicit half-open UTC extraction window:

`[2025-01-01T00:00:00Z, 2026-01-01T00:00:00Z)`

This yields exactly:

- **35,040** unique PT15M interval starts;
- **0** time gaps;
- **26,404** timestamps occurring in more than one raw file;
- **0** full-row disagreements across those overlapping copies.

### Dual-basis validation

The selected recovery basis is the **net operational** MAVIR series for all three affected A75 production types.

| Production type | Basis | Correlation | MAE MW | Mean bias MW | Selection |
|---|---|---:|---:|---:|---|
| Fossil Gas | settlement | 0.9958461087 | 82.5284432616 | -82.4419909527 | reject for recovery boundary |
| Fossil Gas | operational | 0.9999966663 | 0.2305897311 | -0.0061843998 | **selected** |
| Fossil Oil | settlement | 0.9979316596 | 0.0915304900 | -0.0820952255 | secondary |
| Fossil Oil | operational | 0.9991878070 | 0.0052377329 | -0.0023304106 | **selected** |
| Hydro Water Reservoir | settlement | 0.9998165968 | 0.0585813522 | -0.0482361369 | secondary |
| Hydro Water Reservoir | operational | 0.9999887048 | 0.0041866777 | -0.0019938640 | **selected** |

Thus:

`DUAL_BASIS_SELECTION_REQUIRED -> RESOLVED`

### Exact recovery values

Every current A75 missing cell has an exact operational-source value.

- Fossil Gas: **2/2** — `-5.790 MW`, `-54.592 MW`
- Fossil Oil: **4,817/4,817**
  - negative: **4,809**
  - zero: **6**
  - positive: **2**
  - range: **-0.788 .. 2.005 MW**
- Hydro Water Reservoir: **1/1** — `-0.180 MW`

No interpolation is required.

## 9. Remaining blocker — signed net-generation semantics

The current B09 runtime deliberately enforces:

`delivered_generation_kw >= 0`

and the ENTSO-E observed-generation contract enforces:

`power_mw >= 0`

The selected MAVIR recovery source is explicitly a **net operational measurement** and contains signed negative values at many of the exact A75 missing cells.

Therefore the following operations remain forbidden:

`NEGATIVE_RECOVERY -> ZERO`

`NEGATIVE_RECOVERY -> ABS(VALUE)`

`NEGATIVE_RECOVERY -> POSITIVE_GENERATION`

P6 does not alter engine semantics.

The numeric acquisition gap is closed, but Q-B09-001 remains E3 / MODEL_BLOCKER until a bounded runtime contract explicitly represents the signed net-operational contribution without double counting or false relabelling.

Exact residual:

`SIGNED_NET_GENERATION_RECOVERY_SEMANTICS_REQUIRED`

The next slice should solve only that physical/runtime boundary.
