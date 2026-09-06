# B02-P27 — Calibrated current-emitter linkage feasibility

**State:** `CANDIDATE CONTRACTED / NO STOCK ASSIGNMENT / Q`

**Base:** `85644ed851b9acb518d2c6a3ba0bac35eb4ea395`

**Audit date:** 2026-09-06

## 1. Purpose

P25 established a current nationally representative numeric emitter/device control: the TÁRKI–REKK 2022 survey reports gas convectors at `40.61%` among `N=657` gas-heating households. P26 separately established that a real current HET certificate can carry explicit record-level radiator plus hydronic design-temperature evidence.

Neither result is a stock assignment.

P27 therefore asks the next narrower question:

> Can the P25 gas-convector control be admitted as a calibrated WBL-level current-emitter linkage using the already-canonical P12 calibrated-linkage framework?

The current answer is **not yet**.

Canonical boundary:

`NUMERIC SURVEY CONTROL != WBL CELL ASSIGNMENT`

`TARGET-GRAIN COMPATIBILITY != REPRESENTATIVENESS RECONCILIATION`

`NATIONAL POINT SHARE != CELL-LEVEL CONDITIONAL PROBABILITY`

`MODEL CANDIDATE != APPROVED MODEL != QUALIFIED STOCK AUTHORITY`

## 2. Reused canonical evidence

P27 introduces no new external authority. It reuses:

- `SRC-B02-TARKI-REKK-HOUSEHOLD-ENERGY-SURVEY-2022` from P25;
- `SRC-B02-KSH-CENSUS-API-2022` and the materialized WBL011 full occupied-stock joint;
- the generic P12 calibrated-linkage admission contract in `modules/B02/calibrated_linkage_admission.py`;
- the P18 rule that record/document evidence is not stock-level technical authority.

The target grain is already known and reproducible: the WBL011 full occupied-stock joint contains `116 452` positive cells and `4 008 541` occupied dwellings.

P27 does not create a second emitter taxonomy and does not change the P22 heating-system assignment.

## 3. Why direct broadcasting is prohibited

P25's `40.61%` value has the source universe:

`GAS_HEATING_HOUSEHOLDS`

The WBL target universe is:

`OCCUPIED_DWELLING_STOCK`

with heating mode, heating fuel, geography, settlement type, construction period, wall material, floor area and comfort jointly observed at cell grain.

The survey report does not publish a direct `cell_id` mapping, and P27 has not established that every WBL gas-related cell has the same conditional gas-convector probability.

Therefore the following is prohibited:

`every gas WBL cell * 0.4061 -> gas-convector assignment`

It would silently assume conditional independence across WBL dimensions and would convert a national survey control into synthetic cell evidence.

The same restriction applies to the traditional- and condensing-boiler shares. A boiler share is a heat-generator control and is not radiator evidence.

## 4. P12 candidate

P27 registers one candidate in `registry/b02_calibrated_linkage_admission.csv`:

`B02-P27-TARKI-REKK-GAS-CONVECTOR-WBL-LINKAGE-CANDIDATE`

Target:

`HEAT_EMITTER`

Output semantics, if the model is later admitted:

`ASS`

The candidate already has:

- explicit model ID;
- explicit calibration sources;
- defined 2022 reference period;
- WBL-compatible target grain;
- mandatory uncertainty propagation requirement.

It deliberately remains `Q`.

## 5. Current blockers

The generic P12 admission gate returns exactly:

- `NO_JOSEPH_APPROVAL`;
- `NO_REPRESENTATIVENESS_DIAGNOSTICS`;
- `NO_VALIDATION_METRICS`;
- `NO_MARGINAL_RECONCILIATION`;
- `NO_UNCERTAINTY_METHOD`;
- `UNCONTROLLED_INDEPENDENCE_ASSUMPTION`.

These are substantive, not paperwork-only blockers.

### 5.1 Representativeness reconciliation

The survey is nationally representative in its own reported design, but P27 has not yet shown that its conditional `GAS_HEATING_HOUSEHOLDS` universe is quantitatively reconciled to the exact WBL heating-mode × heating-fuel target population.

`SURVEY REPRESENTATIVE != TARGET-LINKAGE REPRESENTATIVENESS PROVEN`

### 5.2 Validation metrics

No held-out, external or source-native validation currently demonstrates that a proposed WBL conditional emitter allocation reproduces known emitter controls beyond the single national gas-convector point share.

### 5.3 Marginal reconciliation

No executable model currently proves exact reconciliation between:

1. the source survey gas-heating distribution;
2. the WBL target gas-heating population definition;
3. any lower-grain geography/building-type controls used to shape the linkage.

### 5.4 Uncertainty

P25 explicitly preserves the boundary:

`FULL-SAMPLE 3.4% MARGIN OF ERROR != N=657 CONDITIONAL SUBGROUP UNCERTAINTY`

P27 therefore refuses to manufacture a subgroup confidence interval. A later model must define and propagate a defensible uncertainty method.

### 5.5 Independence

Without additional conditional controls, allocating `40.61%` uniformly over WBL cells would assume that gas-convector prevalence is independent of geography, settlement type, building type, construction period, area and other observed stock dimensions.

That assumption is currently uncontrolled.

## 6. Relationship to design temperature

P27 is an emitter-linkage feasibility slice only.

P26 proves that record-level current radiator systems can carry explicit design/calculation temperature pairs. It does not establish a stock distribution of radiator design temperatures, and P27 does not join `70/55 C` to any WBL cell.

Therefore:

`EMITTER LINKAGE CANDIDATE != DESIGN-TEMPERATURE LINKAGE`

`GAS CONVECTOR != HYDRONIC DESIGN-TEMPERATURE REQUIREMENT`

`RADIATOR RECORD 70/55 C != NATIONAL RADIATOR DEFAULT`

The design-temperature blocker remains independent.

## 7. Admission impact

P27 creates no emitter assignment and no readiness uplift.

Current state remains:

- `CURRENT_STOCK_ARCHETYPE_ASSIGNMENT = QUALIFIED`;
- `CALIBRATED_GAS_CONVECTOR_EMITTER_LINKAGE = Q`;
- `TECHNICAL_READINESS_ARCHETYPE = Q`;
- blockers remain exactly:
  - `NO_CURRENT_HEAT_EMITTER_EVIDENCE`;
  - `NO_CURRENT_DESIGN_TEMPERATURE_EVIDENCE`.

The P18 direct-authority boundary remains unchanged.

## 8. What would justify the next model step

A later calibrated emitter model may be proposed only after the repository can provide, at minimum:

1. an explicit survey-to-WBL gas-heating universe crosswalk;
2. quantitative reconciliation of survey and WBL target margins;
3. at least one defensible conditional shaping/validation surface beyond the national `40.61%` point share;
4. a subgroup uncertainty method;
5. an explicit structural sensitivity for the otherwise-hidden independence assumption;
6. repository-reproducible WBL output;
7. Joseph's explicit approval under the existing P12 governance contract.

Until then:

`NO EMITTER WBL ROW IS MATERIALIZED`

and:

`NO NATIONAL TECHNICAL ELIGIBILITY COUNT IS CREATED`.
