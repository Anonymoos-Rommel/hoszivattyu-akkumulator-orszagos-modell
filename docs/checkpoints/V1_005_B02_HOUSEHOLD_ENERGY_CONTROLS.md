# V1 checkpoint 005: national household final-energy controls

Scope: B02-D01 partial integration. Source: [Eurostat nrg_d_hhq](https://ec.europa.eu/eurostat/databrowser/product/page/nrg_d_hhq), accessed 2026-10-01. Selection and normalization by repository authors; Eurostat is not responsible for these modifications or interpretations.

## Evidence and actual data

The acquired API response supplies Hungary, annual TJ, 2022–2024: 222 reported cells and 93 explicitly missing cells across seven end-use codes and 15 energy-product codes. Data were updated 2026-06-09; the latest reference year is 2024. The September metadata/navigation update does not make these 2025 or 2026 observations. Original UTF-8 JSON and the inspected general/national metadata HTML are archived byte-for-byte under the stable source ID, with hashes in `registry/b02_eurostat_household_manifest.json`. [Public reuse](https://ec.europa.eu/eurostat/en/help/copyright-notice) is permitted with attribution.

The published 2024 natural-gas controls are:

| End use | TJ of reported final energy |
|---|---:|
| Total household energy use | 103325.000 |
| Space heating | 82546.835 |
| Water heating | 12926.630 |
| Cooking | 7851.534 |

This prevents treating all household gas as space heating. It does **not** establish programme gas savings: the selected target cohort, pre-existing systems and conversion efficiencies still matter.

## Statistical and physical boundary

[General metadata](https://ec.europa.eu/eurostat/cache/metadata/en/nrg_quant_esms.htm) describe annual national reporting and product families. [Hungarian metadata](https://ec.europa.eu/eurostat/cache/metadata/EN/nrg_quant_simsqu_hu.htm), last updated 2024-02-29, identify MEKH reporting and the KSH household energy survey, including weighted extrapolation. That older metadata does not certify the exact 2024 sampling error or a new 2024 survey. These are official compiled controls, labelled DER, not dwelling-level metered useful heat. Eurostat, KSH and MEKH republications are not three independent measurement families.

The table's TOTAL and parent fuel categories overlap their children. Summing all 15 product columns double-counts. Household final energy, ambient heat, purchased energy and useful heat are different boundaries. No blanket boiler efficiency, COP, household-count multiplier or weather correction is applied here. Annual energy is not design peak power. A national all-household total is not the non-district programme denominator.

## Consumer and tests

`tools/extract_b02_eurostat_household.py` checks the pinned source digest and explicit JSON-stat dimensions, reconstructs the full cube, rejects wrong geography/unit/time scope and invalid values, and retains missing cells and source flags. `modules/B02/household_energy_controls.py` reads canonical values with a declared boundary and converts TJ to GWh by division by 3.6.

The end-use balance helper only works when all six child end uses are present. It never fills absent gas-cooling cells with zero. Published zeros, such as 2024 ambient heat for water heating, remain distinguishable from absent values. The 2023 and 2024 all-product balances retain their respective −0.001 and +0.001 TJ rounding residuals; they are not forced to zero. Source reproduction and these failure cases are covered by focused tests.

## Remaining work

B02-D01 stays INTEGRATING. These controls support later physical-model calibration; they do not close useful heat, heated floor area, household system efficiency, terminal eligibility or national uncertainty. The full Invert physical source remains a promising separate lead, presently blocked by the unavailable installed Parquet reader. No package installation, unsupported decoding or external conversion is used to bypass that tooling limit.
