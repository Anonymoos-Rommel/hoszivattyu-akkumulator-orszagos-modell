# B02-P37 — current emitter dependence-control closure

**State:** `UNCONTROLLED INDEPENDENCE ASSUMPTION RESOLVED / NUMERIC JOINT EXECUTION STILL FAIL-CLOSED / LINKAGE Q`

**Base:** `f19437f0429663ba8b10f73a63a09d6d5c7e33f6`

**Audit date:** 2026-09-06

## 1. Purpose

P30 left exactly three admission blockers on the current gas-convector emitter linkage candidate:

1. `NO_JOSEPH_APPROVAL`;
2. `NO_VALIDATION_METRICS`;
3. `UNCONTROLLED_INDEPENDENCE_ASSUMPTION`.

P37 closes **only** `UNCONTROLLED_INDEPENDENCE_ASSUMPTION`.

It does not create validation metrics, does not request Joseph approval, does not materialize a WBL emitter assignment and does not promote any model output to OBS.

## 2. Why P30 still had an independence-control problem

P30 exactly reconciled the national 23.3% primary gas-convector margin, but several materially different building-type structural shapes could reproduce the same total. Historical KSH/TABULA building-type shares were therefore used only as structural priors.

That meant the current building-type / primary-emitter dependence had not yet been tied to a current same-record authority.

Canonical boundary inherited from P30:

`OBSERVED MARGINS != JOINT DISTRIBUTION`

and:

`EXACT MARGINAL RECONCILIATION != INDEPENDENCE CONTROL`

## 3. Same-record current dependence authority exists

The TÁRKI–REKK 2022 household survey contains both sides of the required dependence on the **same household questionnaire record**.

### 3.1 Building type

Source:

- `SRC-B02-TARKI-REKK-HOUSEHOLD-ENERGY-SURVEY-2022`
- URL: `https://rekk.hu/downloads/projects/ECF_HU_Gas_phaseout_REKK_study_final.pdf`
- exact locator: questionnaire appendix 7.1, printed page 121 / PDF page 144, Q11.

Q11 is mandatory and records:

- `1` — 1–3 dwelling family house;
- `2` — 4–9 dwelling apartment building;
- `3` — >10 dwelling apartment building.

### 3.2 Primary heat generator

Same source and same questionnaire record:

- exact locator: questionnaire appendix 7.1, printed page 123 / PDF page 146, Q19.

Q19 is a single-response primary-heat-generator variable and explicitly contains:

- `4` — `gázkonvektor`.

Therefore:

`BUILDING TYPE MARGIN + EMITTER MARGIN != REQUIRED CROSS-PRODUCT`

because the source survey observes both variables jointly at household level.

Canonical replacement:

`SAME-RECORD Q11 × Q19 JOINT = DEPENDENCE AUTHORITY`

## 4. Survey design is compatible with dependence control

The REKK report documents:

- 1,826 contacted households;
- 1,013 successful interviews;
- fieldwork from 2022-10-15 through 2022-11-02;
- multistage proportionally stratified probability sampling;
- final TÁRKI weighting from KSH data by region and building type;
- stated representativeness along those two weighting dimensions.

Source locator:

- same REKK report;
- chapter 3, `Lakossági kérdőíves felmérés összefoglalója`, printed page 12 / PDF page 35.

The full-sample 3.4% margin of error is **not** reused as a gas-convector subgroup uncertainty estimate. P29 remains authoritative on uncertainty semantics.

## 5. The observed joint has already been published

Source:

- `SRC-B02-FEANTSA-CSOKNYAI-HEAT-TRANSITION-2024`
- URL: `https://www.feantsa.org/files/Themes/Energy/2024/heat-transition/Full.pdf`
- exact locator: printed pages 20–21, Figure 6, `Applied heating system types used as primary heat generators according to building type, 2022, [29]`, plus the accompanying paragraph.

Figure 6 publishes the 2022 primary-heat-generator distribution **according to building type**. `Gas convector` is an explicit legend category. The accompanying text states that gas convectors are widespread not only in single-family houses but also in multi-family houses.

The figure cites source `[29]`, the TÁRKI–REKK 2022 survey already used by P25/P30.

This is decisive for the present blocker:

`CURRENT OBSERVED BUILDING-TYPE × PRIMARY-HEAT-GENERATOR JOINT != INDEPENDENT-MARGINAL ASSUMPTION`

P37 does **not** digitize unlabeled stacked-bar segments and does not invent exact percentages from graphic widths.

## 6. Exact joint recovery route also exists

REKK's official project page states that the **complete and detailed database** of the 2022 household survey can be provided to interested users for scientific publication or public-policy analysis.

Source:

- `SRC-B02-REKK-TARKI-2022-FULL-DETAILED-DATABASE-AVAILABILITY`
- URL: `https://rekk.hu/elemzes/341/az-orosz-gaz-kivezetesenek-lehetosege-magyarorszagon`
- exact locator: project-page paragraph beginning `A háztartási felhasználók 1000 fős személyes lekérdezését...`; sentence stating that the complete detailed database can be made available and requests should be addressed to the project leader.

This proves an existing exact same-record recovery route. P37 does not depend on a bespoke statistical table being invented later and does not itself send a data request.

## 7. Executable P37 control

`modules/B02/emitter_dependence_control.py` separates dependence control from numeric joint execution.

Dependence is `CONTROLLED` only if all of the following are explicit:

1. survey source ID;
2. joint-publication source ID;
3. reference period;
4. building-type variable;
5. emitter variable;
6. target emitter code;
7. both variables are on the same household record;
8. building-type weighting is documented;
9. an observed joint publication exists;
10. silent marginal cross-product is forbidden;
11. a historical prior is forbidden from overriding the current joint authority.

For P37 these gates pass with:

- building-type variable: `Q11`;
- emitter variable: `Q19`;
- target emitter code: `4 = gázkonvektor`;
- survey: TÁRKI–REKK 2022;
- current joint publication: FEANTSA Figure 6.

Therefore:

`independence_assumption_controlled = yes`

and `UNCONTROLLED_INDEPENDENCE_ASSUMPTION` is removed from the successor admission row.

## 8. Numeric execution remains fail-closed

The public Figure 6 establishes the joint and its dependence structure but does not print exact numeric values for every stacked-bar segment.

Therefore P37 separately returns:

`numeric_execution_status = NOT_EXECUTABLE`

with:

`NO_EXACT_NUMERIC_JOINT_CELLS`

until exact cells are available from a source-provided table or the retained detailed database.

This is intentional:

`INDEPENDENCE CONTROL != EXACT NUMERIC JOINT CELLS`

and:

`PUBLIC JOINT CHART != FABRICATED CELL PERCENTAGES`

No WBL cell receives a new current gas-convector probability in P37.

## 9. Historical priors are demoted from dependence authority

The KSH/TABULA historical building-type gas-convector percentages may remain a **sensitivity / historical structural prior** for P30 lineage, but P37 forbids them from overriding the current same-record joint authority.

Canonical rule:

`HISTORICAL STRUCTURAL PRIOR != CURRENT DEPENDENCE AUTHORITY`

Any future executable cell allocation must respect the current observed joint or exact same-record microdata-derived joint. It may not silently fall back to an independent cross-product or treat the historical prior as current truth.

## 10. Admission impact

P37 appends:

`CALIBRATED_GAS_CONVECTOR_EMITTER_LINKAGE_P37`

to `registry/b02_calibrated_linkage_admission.csv`.

Its state is:

- `approval_status = NOT_APPROVED`;
- `representativeness_diagnostics = yes`;
- `validation_metrics = no`;
- `marginal_reconciliation = yes`;
- `uncertainty_method = yes`;
- `uncertainty_propagation = yes`;
- `independence_assumption_controlled = yes`;
- `output_evidence_status = ASS`;
- `current_status = Q`.

Remaining blockers are now exactly:

1. `NO_JOSEPH_APPROVAL`;
2. `NO_VALIDATION_METRICS`.

Thus:

`UNCONTROLLED_INDEPENDENCE_ASSUMPTION = CLOSED`

but:

`INDEPENDENCE CONTROL != VALIDATION`

Joseph approval remains last and cannot substitute for validation.

## 11. Technical-readiness boundary

P37 closes a calibrated-linkage admission blocker only.

It does not create household-level OBS emitter assignments and does not create a national technical-eligibility count.

Technical-readiness blockers remain:

- `NO_CURRENT_HEAT_EMITTER_EVIDENCE`;
- `NO_CURRENT_DESIGN_TEMPERATURE_EVIDENCE`.

B02 readiness remains `55%`.

## 12. Repository evidence policy

Every external claim in P37 is represented only by authority + public URL + exact document/page/question/figure locator + bounded metadata.

**REFERENCED SOURCE DOCUMENT BYTES MUST NOT ENTER THE PUBLIC REPOSITORY.**

No REKK PDF, FEANTSA PDF, survey database, screenshot, spreadsheet, export or other external source binary is committed.
