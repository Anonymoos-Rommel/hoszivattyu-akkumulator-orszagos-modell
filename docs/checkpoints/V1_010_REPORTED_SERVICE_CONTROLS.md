# V1 checkpoint 010: reported service controls and normalization boundary

The [REKK/TÁRKI report](https://rekk.hu/downloads/projects/ECF_HU_Gas_phaseout_REKK_study_final.pdf), body Table1, printedp17/PDFp41 of the pinned revision, provides 2022 gas-use-group means. The overall household sample is1013, weighted by region/building type. The four-row extract preserves the total and gas-primary, gas-secondary-only and no-gas-heating groups. Temperature and heated-area share are reported usage, not metered annual heat. Item-specific sample sizes and covariance are not supplied. The no-gas group includes district heating. These facts cannot identify non-district participant heat or23 physical-type allocations.

Only attributed numerical facts are published. The original PDF/image is external; manifest records its SHA256, fieldwork, locator and reuse boundary. The extractor reproduces all16 decimal cells from the pinned PDF using existing pdftotext. It excludes the separate KSH area comparator and financial rows.

## Executable use

`reported_service_controls.py` exposes a control vector and recomposes each reported mean individually from rounded group shares. Residuals remain visible: temperature−0.006223°C, dwelling area+0.001857m², heated-area share+0.004712 percentage points. It does not alter the printed totals. It rejects calculating mean heated area from separate mean area and mean heated fraction because their cross-moment is missing.

This is a source-control integration, **not an E2 heat-allocation admission**. No slice is closed. No temperature becomes a design input or policy default.

## Why a universal calibration factor is not introduced

Existing historical geometry/type priors and the national2022 JRC annual reference have different time, population and service boundaries. The exploratory50.18TWh historical normative exposure and29.27TWh annual reference therefore cannot define an observed prebound fraction. One national conservation equation cannot identify23 type-specific usage levels. Full occupancy is not deducted twice after using the occupied KSH universe. Space heating, DHW, circulation, final/useful/primary energy and each weather year remain separate.

B06's existing effect-surface contract intentionally holds climate and service constant before/after an intervention. A comfort change needs a separate service/energy-carrier calculation. B11's existing bounded gas balance is not a total-energy or cash-flow balance; gas displacement can coexist with increased electricity use. No existing gate is loosened.

## Next useful run and stop condition

Use populated same-service physical cases first; the existing Zalavár pair and annual-only TABULA controls are concrete candidates. Research whether a low-dimensional usage model has enough published group information and applicability for a defensible base. Do not pursue repeated versions of the same adaptation curve as independent evidence. Do not wait for universal household measurements, silently force all types to the national total, or convert missing correlations into independence. A choice of the headline programme service objective is prepared separately and has not been activated.

Verification: four targeted tests pass; the original-PDF extraction reproduced the curated CSV byte-for-byte. Focused code review covered hash/period/group boundaries and the cross-moment guard; source-page visual checking was performed by the author. This is not full independent scientific validation.
