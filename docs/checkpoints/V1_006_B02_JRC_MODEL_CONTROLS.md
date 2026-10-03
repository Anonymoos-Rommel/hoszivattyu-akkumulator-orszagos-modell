# V1 checkpoint 006: JRC residential model controls

Source: European Commission Joint Research Centre, JRC-IDEES-2023, CC BY 4.0. Selected native cells and arithmetic checks by repository authors; the Commission is not responsible for this use.

## Source and use boundary

The official [Hungary ZIP](https://jeodpp.jrc.ec.europa.eu/ftp/jrc-opendata/JRC-IDEES/JRC-IDEES-2023_v1/JRC-IDEES-2023_HU.zip) contains the Residential workbook, revision v2023-1.00, cover date 2025-11-06. The selected 2022–2023 controls retain sheet, row, year, native code, unit, original formula text and cached value. There are 256 cells: 244 present and 12 missing. Original binary source files are retained locally with hashes; the UTF-8-only publication route has not archived the ZIP/XLSX in Git. The publisher's exact copyright notice is archived.

The [technical documentation](https://publications.jrc.ec.europa.eu/repository/bitstream/JRC144707/JRC144707_01.pdf), printed pp20–24, describes a decomposition calibrated to Eurostat. Heating-equipment efficiency uses EU Ecodesign assumptions. Household counts derive from population and household size; dwellings, vacant homes and secondary residences are not separately identified. Useful area and useful energy are model quantities. Equipment-based useful energy is not the standard-comfort design load of a specific dwelling. These dependencies make JRC and Eurostat related evidence, not independent surveys.

**Admission: RESEARCH_CALIBRATION_CONTROLS_ONLY. No E2 base is admitted by this checkpoint.** The current KSH occupied-dwelling universe and B02 physical/eligibility gates are unchanged.

## Actual comparable 2023 reconciliation

Conversion: 1 ktoe = 41.868 TJ. The comparisons use the same year and explicitly matched boundaries, not source titles alone.

| Quantity | JRC (TJ) | Current Eurostat (TJ) | JRC minus Eurostat |
|---|---:|---:|---:|
| Total final energy, including ambient heat | 224710.452 | 224710.365 | +0.087 |
| Natural gas plus biogas, total | 104339.700 | 104340.000 | −0.300 |
| Space heating, excluding ambient heat | 157577.359 | 154434.034 | +2.0354% |
| Water heating, all energy products | 27895.932 | 31160.452 | −10.4765% |

The JRC gas end-use native codes specify **NG_Biogas**, even where the row label says Natural gas. Comparing only the summary's natural-gas component would create a false product-boundary discrepancy. Likewise, JRC thermal final energy excludes ambient heat; its Eurostat-style fuel total includes it.

The 10.48% difference is an **end-use decomposition discrepancy**, not uncertainty in total household consumption. Current revisions and JRC's own allocation adjustments have not been separately identified. It is therefore not labelled a reconciled methodological revision, averaged away, or adopted as an uncertainty interval.

## Controlled sensitivity actually run

For gas plus biogas, both space-heating and water-heating vectors are compared together: native JRC useful energy versus current same-year Eurostat final energy multiplied by the corresponding unchanged native JRC useful/final ratio. This is an explicit diagnostic scenario, not a new canonical input.

| 2023 gas end use | Native JRC useful TJ | Matched Eurostat FEC × unchanged JRC ratio, useful TJ | Difference |
|---|---:|---:|---:|
| Space heating | 57897.782 | 56713.981 | −1183.801 |
| Water heating | 9574.415 | 9378.619 | −195.796 |

This isolates the effect of the source decomposition on one comparable gas boundary. It does not bound efficiency uncertainty, estimate programme savings, test heat-pump performance or rank full-model sensitivity. No independent low/base/high Cartesian inputs or source averages are introduced.

## Validation and next decision

The consumer checks selected native sums, useful/final efficiency identities, ambient-heat separation, missing efficiency when final energy is zero, explicit units and exact years. Re-extraction from the pinned workbook reproduces the canonical extract. Formula text and cached values were inspected; this is not workbook-wide recalculation proof. The extractor uses an existing openpyxl installation only and makes no workbook edits.

Before E2 selection, retain one declared source-year basis, settle the usable equipment/output boundary, and evaluate the end-use discrepancy as a coherent structural sensitivity in the consuming V1 model. Household-to-dwelling mapping and the current Hungarian stock applicability remain explicit validation debt. A source-backed aggregate calibration does not identify each dwelling's geometry or terminal outcome.
