# V1 checkpoint 008: scoped annual heat E2 reference

## Admission and one canonical base

`registry/b02_v1_annual_heat_admission.json` admits one coherent **2022 JRC national annual calibration vector**, DER / E2_PROVISIONAL_BASE, under the existing eight-criterion evidence policy. The original SH-household/DHW branches are retained. This is a populated, reproducible reference, not merely permission to continue and not a complete B02 slice closure.

The scope is national annual calibration. The KSH 3,389,817 non-district occupied dwellings are used only as a declared normalization denominator. JRC energy is **not** multiplied by a JRC/KSH count ratio. The resulting dwelling-equivalent intensity is not an observed mean dwelling or an allocation to programme participants.

## Actual 2022 reference

| Quantity | Value |
|---|---:|
| Native JRC non-district SH households | 3,738,170 |
| KSH normalization denominator, occupied non-district dwellings | 3,389,817 |
| SH thermal service, excluding circulation | 29,266.755 GWh/year |
| DHW thermal service, including existing solar | 4,966.647 GWh/year |
| Circulation, separately retained | 440.378 GWh/year |
| Solar already included in DHW | 176.962 GWh/year |
| Existing advanced-electric heating already included in SH | 485.785 GWh/year |
| SH normalized reference | approximately 8,634 kWh/dwelling-equivalent/year |
| DHW normalized reference | approximately 1,465 kWh/dwelling-equivalent/year |

The solar and existing heat-pump components are not automatically new heat-pump replacement opportunities. Nor does separating circulation establish that all auxiliary energy would be saved by a retrofit.

## Why the paired source is necessary

The [JRC-IDEES Hungary workbook](https://jeodpp.jrc.ec.europa.eu/ftp/jrc-opendata/JRC-IDEES/JRC-IDEES-2023_v1/JRC-IDEES-2023_HU.zip) provides native `RES_hhdet_num/fec/tes` cells. All nine SH cohorts sum to 4,174,806 model households in 2022; each cohort's DHW options reconcile to its parent. The adapter excludes the **whole** DistrHeat SH cohort, including its electric/solar DHW. Subtracting only the H8000 DHW energy carrier would incorrectly retain 61.574 GWh of that cohort's other DHW service.

Source units, exact cells, native codes, formulas and cached values remain in the 558-cell extract, which reproduces the pinned workbook. This is not workbook-wide formula recalculation. Source provenance and reuse terms are in the existing JRC manifest; the binary archive gap remains explicit.

## Coherent sensitivity and cancellation

The JRC and current Eurostat 2022 H8000 total final energy agree to 0.0016 TJ, but their SH/WH allocations differ substantially. At fixed total H8000 final energy and unchanged native efficiencies, substituting the current Eurostat SH/WH shares changes **district** useful energy by −501.571 GWh SH and +550.273 GWh DHW.

These are not non-district uncertainty bounds. When the same change is applied consistently to the national total and the excluded district cohort, it cancels from national-minus-district in both branches. A regression explicitly checks that cancellation. Subtracting updated district energy from a frozen national total would manufacture a false non-district effect.

A separate diagnostic keeps native district non-H8000 DHW intensity fixed and substitutes the KSH district count as a count-equivalent. It transfers 25.678 GWh from non-district to district DHW, conserving national energy, a −0.517% change to the non-district DHW reference. This is an explicit structural SCN, not an observed correction or confidence interval. It does not replace the admitted native base.

## Validation debt and permitted continuation

The [admission record](../../registry/b02_v1_annual_heat_admission.json) names five debts: energy/dwelling universe, end-use/cohort assignment, Hungarian useful/final efficiencies, archetype/programme allocation, and annual-to-hourly weather/service normalization. Each identifies possible evidence, the claim it would upgrade and finalization materiality.

The KSH mixed-fuel categories cover 831,922 non-district dwellings (24.54%) without consumption shares or dominant-system identification. This prevents an unqualified fuel/archetype energy join; it does not require exhaustive household microdata and does not block this aggregate reference. Public representative evidence or a documented calibrated estimator with structural sensitivity remains the route forward.

Allowed next work: calibrate the existing P21/P79/P80 and later physical surfaces to this annual reference with explicit population/energy boundaries. Forbidden: multiply the reference intensity by a selected participant count, infer peak kW from annual kWh, certify household eligibility, or label the model reference OBS. Q-B02-004's existing E2 MODEL_CONTINUE authority remains in force; its exact-validation debt is not erased.

Verification: exact source extraction; paired count/energy reconciliation; circulation and solar separation; seven focused tests including coherent ledger sensitivity and missing/wrong-year cases; independent focused source/code review. This is not whole-V1 scientific validation.
