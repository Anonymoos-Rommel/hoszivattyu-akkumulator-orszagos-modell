# B02-P30 — gas-convector marginal reconciliation

**State:** `MARGINAL RECONCILIATION RESOLVED / EMITTER LINKAGE STILL Q`

**Base:** `e30392c9ed63d03758c800e458d93d91b1474e52`

**Audit date:** 2026-09-06

## 1. Purpose

P29 left four blockers on the calibrated gas-convector-to-WBL linkage candidate:

1. `NO_JOSEPH_APPROVAL`;
2. `NO_VALIDATION_METRICS`;
3. `NO_MARGINAL_RECONCILIATION`;
4. `UNCONTROLLED_INDEPENDENCE_ASSUMPTION`.

P30 closes only `NO_MARGINAL_RECONCILIATION`.

It does not qualify the emitter linkage and does not change B02 technical readiness.

## 2. First attempted domain and falsification

The first candidate tested the strongest defensible topology shortcut: permit gas-convector probability only inside WBL cells with source-native room heating (`NHEAT`) and a network-gas-bearing heating-fuel category.

The exact committed 2022 WBL full joint gives:

- occupied dwellings: `4,008,541`;
- gas-bearing heating-fuel dwellings: `2,496,034`;
- gas-bearing share of occupied dwellings: `62.2678924826%`;
- `NHEAT + gas` dwellings: `693,075`.

Applying the P25 conditional gas-convector control (`40.61%` among gas-heating households) to the WBL gas-bearing universe would imply `1,013,639.4074` expected gas-convector dwellings. The strict `NHEAT + gas` domain contains only `693,075` dwellings, requiring a probability of `1.46252484565`.

That is impossible.

Therefore P30 explicitly rejects the shortcut with:

`ROOM_GAS_DOMAIN_TOO_SMALL`

No central-heating cell is relabelled merely to force the target to fit.

Canonical boundary:

`HEATING MODE != EMITTER`

`NHEAT + GAS != PROVEN GAS CONVECTOR`

## 3. Estimand separation

The REKK report Figure 11 publishes gas convector at `40.61%` among `N=657` households using gas at least partly for heating.

A later FEANTSA report by Tamás Csoknyai reproduces the 2022 survey's distribution of **primary heating system types** and reports gas convector at `23.3%` of the full sample. Its figure cites the same REKK 2022 survey as source [29].

These are different estimands:

`40.61% CONDITIONAL GAS-DEVICE SHARE != 23.3% PRIMARY-HEATING STOCK SHARE`

P30 therefore does not multiply the `40.61%` conditional subgroup share across the WBL stock. The calibrated stock-level primary-heating model uses the `23.3%` full-sample primary-heating control.

The 23.3% control is published to one decimal place, so P30 treats it as a rounded calibration control rather than fabricated exact microdata.

## 4. Structural-prior family

P30 requires a non-uniform shape before calibration. It does not invent current household-level emitter evidence.

The shape uses:

- the already-qualified P21 per-cell `FAMILY_HOUSE` / `MULTI_DWELLING` probability surface;
- historical KSH/TABULA Table 5 gas-convector shares only as structural priors:
  - family house: `21.6%`;
  - small multi-family (4–9 flats): `18.0%`;
  - large non-panel multi-family (10+ flats): `27.4%`;
  - panel 10+ lower-bound scenario: `0.0%`, DER from the source table's explicit `100%` district-heating entry for that historical class.

The historical percentages are not promoted to current evidence.

Canonical boundary:

`HISTORICAL STRUCTURAL PRIOR != CURRENT STOCK OBSERVATION`

The three multi-family values define a structural scenario family rather than one silently selected household-level truth.

## 5. Calibration method

For each WBL cell, P30 forms a pre-calibration structural prior from the P21 family probability and one of the multi-family prior scenarios.

Non-gas WBL cells are constrained to gas-convector probability `0` in every scenario.

For gas-bearing cells, P30 applies one common logit intercept shift per scenario and solves it by bisection so that:

`SUM(dwelling_count * calibrated_probability) = 4,008,541 * 0.233`

The published rounded calibration target is therefore:

`933,990.053 expected dwellings`

This is an expected calibrated model quantity, not an observed integer stock count.

## 6. Exact reconciliation result

On the complete `116,452`-row WBL full joint, all three structural scenarios reproduce the same 23.3% primary-heating control in expectation.

CI diagnostic at the P30 calibrated-model implementation state:

- `MULTI_PANEL_LOWER_BOUND`
  - logit shift: `1.485888745554`
  - maximum cell probability: `0.546818744073`;
- `MULTI_SMALL_4_9`
  - logit shift: `0.862707020848`
  - maximum cell probability: `0.394625691093`;
- `MULTI_LARGE_OTHER_10_PLUS`
  - logit shift: `0.644230927218`
  - maximum cell probability: `0.409586471633`.

Maximum absolute target residual across all three scenarios:

`5.42495399714e-08 dwellings`

All probabilities remain within `[0,1]`; non-gas cells remain exactly zero.

Therefore the successor admission row may truthfully set:

`marginal_reconciliation = yes`

Canonical boundary:

`EXACT MARGINAL RECONCILIATION != VALIDATION`

## 7. What remains unresolved

P30 does not claim that the scenario family identifies the true cell-level emitter distribution.

The same 23.3% national margin can be reproduced by materially different structural shapes. No independent current emitter-specific cross-tab or microdata validation has yet selected or validated one of those shapes.

Therefore the remaining blockers are exactly:

1. `NO_JOSEPH_APPROVAL`;
2. `NO_VALIDATION_METRICS`;
3. `UNCONTROLLED_INDEPENDENCE_ASSUMPTION`.

In particular:

`EXACT MARGINAL RECONCILIATION != INDEPENDENCE CONTROL`

Joseph approval is intentionally last: approval cannot substitute for validation or independence control.

## 8. Technical-readiness boundary

P30 materializes no WBL emitter assignment CSV and creates no OBS/DER emitter stock surface.

Its probability outputs remain `ASS` model quantities.

Therefore:

`CALIBRATED ASS SURFACE != CURRENT HEAT-EMITTER EVIDENCE`

`CALIBRATED ASS SURFACE != TECHNICAL READINESS AUTHORITY`

B02 technical readiness remains `Q` on exactly:

- `NO_CURRENT_HEAT_EMITTER_EVIDENCE`;
- `NO_CURRENT_DESIGN_TEMPERATURE_EVIDENCE`.

B02 readiness remains `55%`.

## 9. Source lineage

Current calibration control:

- `SRC-B02-FEANTSA-CSOKNYAI-HEAT-TRANSITION-2024`
  - FEANTSA, *Heat Transition Options for the Least Performing Buildings of Hungary*, May 2024;
  - Figure 5: 2022 primary heating system distribution, gas convector `23.3%`;
  - the figure cites source [29], the REKK/TÁRKI 2022 survey.

Conditional gas-device control and questionnaire semantics:

- `SRC-B02-TARKI-REKK-HOUSEHOLD-ENERGY-SURVEY-2022`
  - Figure 11: `40.61%` gas-convector share among `N=657` gas-heating households;
  - questionnaire Q19 separately defines primary heat generator and includes gas convector as a distinct category.

Historical structural prior only:

- `SRC-B02-TABULA-HU-TYPOLOGY-BROCHURE-2014`
  - Table 5, KSH 2012 building-type gas-convector shares;
  - context/structural-prior use only, never current household-level authority.

Current target stock and structural linkage:

- `SRC-B02-KSH-CENSUS-API-2022`;
- P15 exact WBL full joint;
- P21 approved calibrated building-type linkage.
