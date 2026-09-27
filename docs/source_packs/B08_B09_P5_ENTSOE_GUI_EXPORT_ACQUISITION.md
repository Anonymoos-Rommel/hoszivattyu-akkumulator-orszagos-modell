# B08/B09-P5 — Registered ENTSO-E GUI export acquisition and completeness audit

**Date:** 2026-09-27  
**Parent slice:** B08/B09-P4  
**Raw files:** external-only; not committed

## 1. Result

The P4 access blocker is resolved without requiring a REST API token.

A registered Transparency Platform user exported the required 2025 Hungarian datasets directly from the official GUI.

Canonical current distinction:

`ACCESS BLOCKER RESOLVED != ALL SOURCE VALUES COMPLETE`

B08 now has a complete real load baseline suitable for model continuation under E2/external-only evidence.

B09 now has the real A75 panel and an expected production-type manifest, but the source itself contains blanks in three active series. Those blanks are not converted to zero.

## 2. B08 acquired load evidence

### 2025 UTC source panel

External workbook:

`GUI_TOTAL_LOAD_DAYAHEAD_202501010000-202601010000.xlsx`

SHA-256:

`1712362093a2957a8870bff5c8758f53a3358587bc7fa9a54e8ee3ba6ecf301d`

Audit:

- source: ENTSO-E Transparency Platform registered GUI export;
- product: Actual Total Load [6.1.A];
- area: BZN|HU;
- period: 2025-01-01 00:00 UTC -> 2026-01-01 00:00 UTC;
- resolution: PT15M;
- data rows: 35,040;
- missing Actual Total Load: 0;
- duplicate MTUs: 0;
- time gaps: 0.

### Exact Europe/Budapest 2025 civil-year boundary

B08-P3 defines the canonical calendar year in Europe/Budapest, which corresponds to:

`2024-12-31 23:00 UTC -> 2025-12-31 23:00 UTC`

The previously acquired 2024 registered GUI export is complete and supplies the preceding one-hour boundary:

`GUI_TOTAL_LOAD_DAYAHEAD_202401010000-202501010000.xlsx`

SHA-256:

`66caeba6f85fdef5eecfa9efb2d5a3c0bc2003bf0a344faf2bce01f786b54228`

It contains 35,136 PT15M rows (leap year), with zero missing Actual Total Load values.

Therefore the exact local civil-year base can be assembled by:

- the final four intervals of the 2024 export; plus
- the 2025 export through 2025-12-31 23:00 UTC;
- excluding the final four UTC-year intervals 2025-12-31 23:00 -> 2026-01-01 00:00 UTC.

No interpolation is required.

## 3. B09 acquired generation evidence

External workbook:

`AGGREGATED_GENERATION_PER_TYPE_GENERATION_202501010000-202601010000.xlsx`

SHA-256:

`c7b332bb63d927730a84082571ad8d1e2f143e10de7b497825d45ca74bbbc05d`

Product:

**Actual Generation per Production Type / Aggregated Generation per Type [16.1.B&C]**

Audit:

- area: BZN|HU;
- period: 2025-01-01 00:00 UTC -> 2026-01-01 00:00 UTC;
- resolution: PT15M;
- data rows: 35,040;
- duplicate MTUs: 0;
- time gaps: 0;
- all interval durations: 15 minutes;
- 21 source production-type columns.

## 4. Expected production-type manifest

A separate official registered GUI export was acquired:

`GUI_GENERATION_INSTALLED_PERTYPE_202501010000-202601010000.xlsx`

SHA-256:

`f70c10756a400a1b663e6b20b17422941ecd6b2cc1e4e8b74571b69781936564`

Product:

**Installed Generation Capacity Aggregated [14.1.A]**

The installed-capacity export has numeric capacity for exactly the same 14 production types that expose numeric generation in A75:

1. Biomass
2. Fossil Brown coal/Lignite
3. Fossil Gas
4. Fossil Hard coal
5. Fossil Oil
6. Geothermal
7. Hydro Run-of-river and pondage
8. Hydro Water Reservoir
9. Nuclear
10. Other
11. Other renewable
12. Solar
13. Waste
14. Wind Onshore

Seven production types are source-native `n/e` in both installed capacity and every A75 interval:

- Energy storage
- Fossil Coal-derived gas
- Fossil Oil shale
- Fossil Peat
- Hydro Pumped Storage
- Marine
- Wind Offshore

P5 therefore closes the previous expected-production-type-manifest gap without treating a merely absent column as zero.

## 5. Source-native active-series gaps

Three expected numeric generation series contain blank cells.

### Fossil Gas

- numeric: 35,038 / 35,040;
- blanks: 2.

### Fossil Oil

- numeric: 30,223 / 35,040;
- blanks: 4,817;
- blank runs: 1,496;
- longest blank run: 100 consecutive PT15M intervals.

The same column contains explicit numeric `0.00` elsewhere.

Therefore:

`BLANK != ZERO`

### Hydro Water Reservoir

- numeric: 35,039 / 35,040;
- blanks: 1.

Across all 14 expected numeric production types:

- complete intervals: **30,220 / 35,040**;
- complete-all-active coverage: **86.244292%**;
- affected intervals: **4,820**.

No missing active value is imputed in P5.

## 6. Evidence and reuse boundary

The current ENTSO-E Terms state that Data Users may use Transparency Platform Data for any purpose, subject to the Terms and source attribution.

The 2023 free-reuse list grants CC-BY 4.0/free redistribution to the listed data items. Actual Total Load [6.1.A] and Actual Generation [16.1.B&C] are not established as listed free-reuse items by the inspected list.

Therefore P5 separates:

`MODEL USE OF LAWFULLY ACCESSED OFFICIAL DATA`

from:

`PUBLIC REPUBLICATION OF RAW WORKBOOK BYTES`

Raw XLSX files remain `EXTERNAL_ONLY` and are not committed.

Repository evidence preserves source identity, external filename, SHA-256, period, grain, completeness and residual gaps.

## 7. Blocker transitions

### Q-B08-001

Previous P4:

`E3 / MODEL_BLOCKER / ENTSOE_REGISTERED_EXPORT_OR_API_TOKEN_REQUIRED`

P5:

`E2 / VALIDATION_BLOCKER / MODEL_CONTINUE`

Canonical base:

`SINGLE_EXTERNAL_ONLY_OFFICIAL_A65_2025_LOAD_PANEL`

The exact Europe/Budapest year is available by source-native stitching; no source-value gap remains.

Validation debt:

- public raw redistribution/free-reuse authority;
- raw workbook remains external-only.

### Q-B09-001

Previous P4:

`ENTSOE_REGISTERED_EXPORT_OR_API_TOKEN_REQUIRED`

Access is now resolved.

Current:

`E3 / MODEL_BLOCKER`

Exact residual:

`ACTIVE_PRODUCTION_TYPE_SOURCE_MISSINGNESS_TREATMENT_REQUIRED`

The next useful work is not another generic ENTSO-E access search. It is targeted recovery or authoritative treatment of the three active-series source gaps, dominated by Fossil Oil.

## 8. No silent low/base/high branch

P5 follows the project-wide evidence-tier contract.

It does not create low/base/high alternatives for missing generation rows.

Either:

1. source-native values are recovered; or
2. one defensible canonical missingness treatment is established and explicitly labelled; or
3. the affected output remains fail-closed.

## Official references

ENTSO-E Transparency Platform:
https://transparency.entsoe.eu/

Actual Generation per Production Type:
https://transparency.entsoe.eu/generation/r2/actualGenerationPerProductionType/show?name=

ENTSO-E Terms of Use:
https://transparency.entsoe.eu/content/static_content/download?path=%2FStatic+content%2Fterms+and+conditions%2F230309_ENTSOE_Transparency_Terms_Conditions_MC_APPROVED.pdf

2023 List of Data Available for Free Re-use:
https://transparency.entsoe.eu/content/static_content/download?path=%2FStatic+content%2Fterms+and+conditions%2F231018_List_of_Data_available_for_reuse.pdf
