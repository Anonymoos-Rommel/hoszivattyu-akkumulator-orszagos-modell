# V1 checkpoint 009: historical type prior and area bridge experiment

## Purpose

Reuse the already acquired 23-type source and current KSH/P21 controls to run a real population-weighted experiment. Do not turn the older permission to use E2 into unpopulated inputs, but do not promote experimental weights or prototype areas to current observations either.

## Source-native facts, separate from model assumptions

The [Csoknyai dissertation](https://real-d.mtak.hu/1472/7/dc_2011_22_doktori_mu.pdf), Table 7.2, printed/PDF p40, supplies the census-based 2011 dwelling counts for all 23 types: total **4,363,754 dwellings**. This is not the 2,029 surveyed buildings or the 2,702,183 residential-building count. The source universe includes occupied and unoccupied stock; its exact reconciliation to every KSH 2011 dwelling category remains debt.

Tables 14.16–17, pp153–154, give the same type counts and **336,839,750 m² of useful dwelling area**. Table 14.15, p152, supplies the author's applied conversion to full-heating reference area: 1.05 for types 13–18 and 23 and 1.10 for 19–22. For 1–12, 1.00 is derived from the text, not a numerical table cell. These are author-applied model factors, not measured current heated fractions.

The author's Chapter 10.1 method scales a net-heated-area intensity by corrected census dwelling area under full useful-area heating, 20°C and the heating season. This area bridge does not subtract partially unheated dwelling rooms. Table 14.7 total building area includes non-dwelling/unheated spaces, so its heated/total ratio must not be applied to census dwelling area.

Only attributed numeric facts and derived records are curated; the original PDF/table images are not republished. Exact source identity, scopes and hash are in `registry/b02_keop23_prior_manifest.json`.

## Four explicit experiments, not E2 type weights

`modules/B02/keop_prior_calibration.py` preserves every observed full-joint WBL cell and existing P21 group control. The 2011 type counts inform relative composition among source types valid in the **same construction year**. A finite WBL band uses an explicitly assumed year distribution; open tails receive no invented start/end year.

Example: Y1946–1960 FAMILY has type 4 for 1946–1959 and types 5/6 for 1960. The uniform-year experiment assigns 14/15 to type 4 and 1/15 jointly to 5/6. Naively normalizing whole historical type counts would put roughly 75% on5/6; that method is not used.

The declared assumptions include historical within-year type composition transferred to 2022, the finite-band year shape, and conditional independence from omitted county/wall/area/comfort/heating fields. This is a research SCN, **not an admitted population-energy joint**. Three alternatives change one coherent shape at a time: existing P21 FLAT, early-weighted years, or late-weighted years. No independent component-level low/base/high grid is constructed.

## Actual full-data run

All four runs use 116,452 WBL cells and conserve 4,008,541 occupied dwellings, including 3,389,817 non-district dwellings. The maximum cell residual is below 8×10⁻¹² from floating-point arithmetic. HEAT12 is excluded only using the original joint classification.

Reference experiment, m² per dwelling-equivalent:

| Separate area basis | ALL occupied stock | NON_DISTRICT |
|---|---:|---:|
| Table 14.7 heated prototype geometry |94.101|96.491|
| Table 14.17/16 historical census dwelling area |79.480|81.261|
| Historical dwelling area × author's full-heating factor |81.006|82.563|

The last two rows transfer 2011 type means onto 2022 model weights. They are SCN exposures, not 2022 observed area. Prototype volume remains paired with prototype geometry; it is not combined with the alternative census-area exposure as a new invented building.

For NON_DISTRICT prototype area, the finite-year EARLY/LATE experiment changes the result by approximately ±1.283%; P21 FLAT changes it by −0.269%. These are geometry diagnostics, not heat-demand confidence bounds. Full reproducible output is `V1_009_CALIBRATION_DIAGNOSTICS.json`.

## Compatibility diagnostic and next step

About 41.03% of the reference non-district assignment mass has a synthetic prototype heated area numerically above its closed WBL dwelling-area band's upper edge. This is not a count of erroneous or ineligible dwellings: prototype means, whole-building heated area and conditional dwelling area are not identical. It demonstrates why the current age/group-only weights cannot yet allocate actual heat to WBL cells. No hard area filter, arbitrary open-band midpoint, hidden scaling or exact household type is introduced.

Next, use the historical dwelling-area exposure and the source's explicit full-heating bridge as separate calibration inputs. Keep type_id with its prototype intensity/geometry, use current P95 rather than superseded P85 facade logic, and retain unresolved within-type states and current-area transfer as debt. The existing annual E2 heat reference remains an aggregate calibration reference; this experiment does not change its scope or authorize participant multiplication, annual-to-peak conversion, household eligibility or source-gap averaging.

Verification covers the 23-type source controls, prior hash/source/group guards, 42 conditional weight vectors, open tails, exact WBL/P21 conservation and separation of area bases. Independent focused review supports the SCN experiment, not an E2 weighting admission or complete V1 validation.
