# B02-P38 — independent emitter validation metrics

**State:** `NO_VALIDATION_METRICS RESOLVED / LINKAGE STILL Q`

**Base:** `c655a763a38bfcdbd28da445a6c13310b1920706`

**Audit date:** 2026-09-06

## 1. Purpose

P37 left exactly two admission blockers on the current gas-convector emitter linkage candidate:

1. `NO_JOSEPH_APPROVAL`;
2. `NO_VALIDATION_METRICS`.

P38 closes only `NO_VALIDATION_METRICS`.

It does not approve the linkage, does not create OBS emitter assignments, does not create a national technical-eligibility count, and does not change B02 technical readiness.

## 2. Validation principle

The P30 model is calibrated to the TÁRKI–REKK / FEANTSA 23.3% national primary gas-convector control. Reusing that calibration source as validation would be circular.

P38 therefore requires an **external holdout source outside the P30 calibration lineage** and a metric that can actually reject a structural scenario.

Canonical boundary:

`CALIBRATION TARGET != VALIDATION METRIC`

and:

`INDEPENDENT HOLDOUT != REUSED CALIBRATION MARGIN`

## 3. Binding external holdout — Budapest broad-category upper bound

Source:

- source ID: `SRC-B02-DAIKIN-HU-HEATING-STOCK-2022`;
- authority: Daikin Hungary Kft.;
- URL: `https://www.daikin.hu/content/dam/DACE-HU/Press-releases/2022/Daikin_sajtokozlemeny_Futeskorszerusites_Hoszivattyus_javaslatok_20220824.pdf`;
- exact locator: PDF page 2, paragraph beginning `A területi megoszlást elemezve`.

The source reports that Budapest has roughly 800 thousand properties and that **23% (187 thousand dwellings) use convector or stove heating**.

P38 does **not** relabel that broad category as gas convector.

Instead it uses the logically safe subset relation:

`PRIMARY GAS CONVECTOR ⊂ CONVECTOR OR STOVE`

Therefore a modeled Budapest primary-gas-convector share may not robustly exceed the reported broad-category share.

Canonical boundary:

`CONVECTOR OR STOVE != GAS CONVECTOR`

but:

`GAS-CONVECTOR SHARE <= CONVECTOR-OR-STOVE SHARE`

is an admissible upper-bound test when scope and denominator are aligned.

## 4. Source precision is preserved

The Daikin Budapest share is reported as a whole percentage: `23%`.

P38 therefore does not pretend the source supplied an exact `0.230000...` threshold. The executable contract treats the source-compatible rounding interval as:

`[22.5%, 23.5%)`

This is **not** a confidence interval and is not a fitted tolerance. It is only the arithmetic interval implied by reporting to the nearest whole percent.

Classification:

- model share `<= 22.5%` -> `CLEAR_PASS`;
- model share `> 22.5%` and `<= 23.5%` -> `CONSISTENT_WITH_REPORTED_BOUND`;
- model share `> 23.5%` -> `FAIL`.

No threshold was selected after looking at the scenario results.

## 5. Exact P30 Budapest holdout results

The complete WBL011 occupied-stock joint contains:

- Hungary: `4,008,541` occupied dwellings;
- Budapest (`HU110`): `800,338` occupied dwellings.

The P30 scenario family produces these direct Budapest all-dwelling primary-gas-convector shares:

| P30 structural scenario | Budapest modeled share | Independent holdout result |
|---|---:|---|
| `MULTI_PANEL_LOWER_BOUND` | `9.9937732%` | `CLEAR_PASS` |
| `MULTI_SMALL_4_9` | `22.8165175%` | `CONSISTENT_WITH_REPORTED_BOUND` |
| `MULTI_LARGE_OTHER_10_PLUS` | `26.2239407%` | `FAIL` |

The third scenario exceeds even the `23.5%` upper rounding edge and is therefore rejected.

This is a genuinely discriminatory holdout:

`ONE EXTERNAL METRIC -> ONE STRUCTURAL SCENARIO REJECTED`

The surviving P38 candidate family is exactly:

- `MULTI_PANEL_LOWER_BOUND`;
- `MULTI_SMALL_4_9`.

The rejected scenario is exactly:

- `MULTI_LARGE_OTHER_10_PLUS`.

P38 does not choose between the two retained scenarios and does not hide their structural uncertainty.

## 6. Independent national diagnostic — non-binding

The same Daikin source, PDF page 2, paragraph beginning `Szakmai becslések szerint`, reports approximately:

- `600,000` occupied properties heated by convectors;
- another `200,000` properties using gas convectors and wood;
- later it describes gas-convector replacement potential affecting about `800,000` households.

P30's calibrated national expectation is:

`933,990.053 dwellings`

So the model-minus-source diagnostic difference is about:

`133,990.053`

or about `16.75%` relative to the approximate 800,000 external figure.

P38 deliberately does **not** convert this approximate industry estimate into a pass/fail test, because its mixed-heating semantics and estimation method do not justify inventing a tolerance.

Canonical boundary:

`APPROXIMATE INDUSTRY ESTIMATE != HARD NATIONAL ACCEPTANCE BAND`

The national metric remains `DIAGNOSTIC_ONLY`.

## 7. Second independent source — Budapest CARES 2023

Source:

- source ID: `SRC-B02-BUDAPEST-CARES-HOUSEHOLD-SURVEY-2023`;
- authority: Metropolitan Research Institute / Budapest CARES;
- URL: `https://mri.hu/en/wp-content/uploads/sites/2/2024/09/Survey-of-households-in-Budapest-about-energy-efficiency.pdf`.

Exact locators:

- printed pages 6-7, `3 Methodology`:
  - in-person survey, 13 October–7 November 2023;
  - `2,009` Budapest owner households;
  - representative to the Budapest housing stock through quotas for 13 building types, adult age and district housing-stock share;
  - the sample is compared against Census 2022 characteristics and is considered representative for Budapest;
- printed page 9, Figures 4-5 and accompanying text:
  - primary heating source by family-house and MFAB sector;
  - gas heaters are explicitly split between traditional boilers, condensing boilers and convectors;
- printed page 13, Figure 10 and accompanying paragraph:
  - `Gas convector` is an explicit heating-source category;
  - gas convectors are stated to be highly overrepresented in the worst-performing MFAB and family-house segments.

This is an independent, current structural holdout demonstrating non-flat building/heating dependence.

P38 does not digitize unlabeled chart segments and therefore does not fabricate exact CARES gas-convector percentages.

Canonical boundary:

`VISIBLE CHART SEGMENT != SOURCE-PUBLISHED EXACT NUMBER`

CARES is registered as `STRUCTURAL_HOLDOUT_ONLY`; the binding numerical holdout remains the Daikin Budapest upper bound.

## 8. Executable validation contract

`modules/B02/emitter_validation_metrics.py` computes P30 outputs directly from the committed WBL011 full joint and applies the independent Budapest holdout.

It requires no manual transcription of model values.

The contract:

1. derives the exact Budapest WBL denominator from `county_code = HU110`;
2. evaluates all P30 structural scenarios;
3. preserves source reporting precision;
4. rejects any scenario that robustly exceeds the broad external upper bound;
5. retains only non-failing scenarios;
6. keeps the approximate national estimate diagnostic-only;
7. declares validation metrics present only when the external holdout is genuinely discriminatory — at least one scenario survives and at least one is rejected.

Thus P38 does not satisfy the validation gate by merely documenting a source that agrees with everything.

## 9. Admission impact

P38 appends successor claim:

`CALIBRATED_GAS_CONVECTOR_EMITTER_LINKAGE_P38`

with model ID:

`B02-P38-EXTERNALLY-BOUNDED-CONVECTOR-LINKAGE-CANDIDATE`

The successor state is:

- `approval_status = NOT_APPROVED`;
- `representativeness_diagnostics = yes`;
- `validation_metrics = yes`;
- `marginal_reconciliation = yes`;
- `uncertainty_method = yes`;
- `uncertainty_propagation = yes`;
- `independence_assumption_controlled = yes`;
- `output_evidence_status = ASS`;
- `current_status = Q`.

The remaining admission blocker is exactly:

`NO_JOSEPH_APPROVAL`

Therefore:

`NO_VALIDATION_METRICS = CLOSED`

but:

`VALIDATION METRICS PRESENT != JOSEPH APPROVAL`

and:

`VALIDATED MODEL CANDIDATE != CURRENT EMITTER OBSERVATION`.

## 10. Technical-readiness boundary

P38 does not create household-level observed emitter assignments.

Technical readiness remains fail-closed on exactly:

- `NO_CURRENT_HEAT_EMITTER_EVIDENCE`;
- `NO_CURRENT_DESIGN_TEMPERATURE_EVIDENCE`.

B02 readiness remains `55%`.

## 11. Repository evidence policy

Every external source claim is stored only as authority + public URL + exact locator + bounded semantics.

**REFERENCED SOURCE DOCUMENT BYTES MUST NOT ENTER THE PUBLIC REPOSITORY.**

No Daikin PDF, MRI/CARES PDF, screenshot, extracted image, spreadsheet, survey database or other external source binary is committed.
