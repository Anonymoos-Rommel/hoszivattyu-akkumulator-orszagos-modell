# B02-P115 — OFFICIAL TYPE-WEIGHTED ENVELOPE TIGHTENING

## Goal

P102's 82.7861029945% calibrated retrofit floor was intentionally conservative.
It used exact WBL/P21 population mass but, within each construction-period x
building-group stratum, propagated the minimum over every compatible KEOP23
type because point type assignment was unavailable.

P115 removes that **national type-mixture** uncertainty using a new authoritative
source-native type-weight surface.

This is a numeric blocker-repair slice.

## 1. New authority: Hungary BTR1

Hungary's First Biennial Transparency Report, submitted to UNFCCC, publishes
Table 28 "Building typology of Hungary".

The table uses the same 23-type residential typology family as the P79-P102
chain and gives occupied-dwelling counts for every type.

The report cites, among its typology sources:

T. Csoknyai, J. Farkas, L. Formanek, M. Horváth,
Building Typology Study, KEOP-7.9.0/12-2013-0019, Budapest, 2015.

That is the same source family underlying the P79/P80/P102 KEOP23 type system.

Source-native BTR1 totals:

- types 1-12 FAMILY_HOUSE: 2,333,452
- types 13-23 MULTI_DWELLING: 1,393,712
- total: 3,727,164

## 2. Denominator repair

P115 does **not** assert:

BTR 3,727,164 = canonical Census 4,008,541.

Instead:

1. P21 retains the canonical national group masses:
   - FAMILY_HOUSE = 2,423,136
   - MULTI_DWELLING = 1,585,405
   - total = 4,008,541.
2. BTR1 counts are normalized only *within* FAMILY_HOUSE and MULTI_DWELLING.
3. Those source-native conditional type shares are applied to the corresponding
   P21 canonical group mass.

Therefore:

BTR_TYPE_WEIGHT != CENSUS_DWELLING_IDENTITY

and the denominator mismatch does not enter through an invented raw-total
substitution.

## 3. P102 type state reused unchanged

P115 does not alter P102 component physics.

For 19 of 23 types, P102 already has a historical renovated external-wall mean
above the 0.24 W/m2K reference, making the calibrated type-level wall deficit
share 1.0.

Only four types remain partially unresolved:

| Type | Group | P102 floor |
|---|---|---:|
| 11 | FAMILY_HOUSE | 29.8% |
| 15 | MULTI_DWELLING | 26.5% |
| 16 | MULTI_DWELLING | 26.5% |
| 23 | MULTI_DWELLING | 10.6% |

All other type floors are 100%.

This proves that a whole-stock multiglazed-Uw search is unnecessarily broad
for the programme action bound.

## 4. Official-type-weighted group results

Using BTR1 within-group type weights:

- FAMILY_HOUSE calibrated deficit floor:
  **98.6623368297%**
- FAMILY_HOUSE calibrated upper edge:
  **99.1844446768%**
- MULTI_DWELLING calibrated deficit floor:
  **93.4863091514%**
- MULTI_DWELLING calibrated upper edge:
  **94.0430472723%**

## 5. Canonical P21 national propagation

Applying those group-specific shares to the exact P21 group masses gives:

- calibrated national deficit floor:
  **96.6151829747%**
- calibrated deficit floor expected dwelling-equivalent:
  **3,872,859.2218**
- calibrated upper edge:
  **97.1509873286%**
- HP_ONLY lower:
  **0%**
- HP_ONLY candidate upper:
  **3.38481702535%**
- HP_ONLY candidate upper expected dwelling-equivalent:
  **135,681.7782**

The lower HP_ONLY edge remains zero because P115 still does not prove an
observed all-component-compliant population mass.

## 6. Material tightening versus P102

P102:

- floor = 82.7861029945%
- HP_ONLY upper = 17.2138970055%

P115:

- floor = 96.6151829747%
- HP_ONLY upper = 3.38481702535%

Tightening:

**13.8290799802 percentage points**.

This is a material national model improvement.

## 7. Residual blocker is now four-type specific

The old broad search:

CURRENT_MULTIGLAZED_WINDOW_REALIZED_UW_DISTRIBUTION_REQUIRED

is no longer the correct national action-bound acquisition target.

The exact remaining combined target is:

TYPES_11_15_16_23_CURRENT_ENVELOPE_POSTSTATE_REQUIRED

decomposed to:

- TYPES_11_15_16_REPLACED_WINDOW_UW_QUALITY_REQUIRED
- TYPES_11_15_16_23_RENOVATED_WALL_U_QUALITY_REQUIRED

Type 23 has zero P102 not-replaced-window deficit share; its remaining
uncertainty is the renovated-wall branch.

## 8. P79 boundary retained

P115 does not delete P79.

P79 remains required where WBL location/period cells need a local compatible
type set.

P115 only replaces the unnecessary **national type-mixture min-over-candidate
propagation** with source-native official type weights.

Thus:

NATIONAL TYPE MIX != LOCAL WBL POINT TYPE ASSIGNMENT.

## 9. Readiness

This is a material numerical tightening, but the full B02 transition/design-load
chain still has independent residuals.

Therefore no arbitrary readiness uplift is taken:

- B02 remains 55%
- PEAK_LOAD_EFFECT remains 50%

## Source

### SRC-B02-HU-UNFCCC-BTR1-BUILDING-TYPOLOGY-2025

Hungary - First Biennial Transparency Report.

Publisher/submission surface: UNFCCC.

Role:
authoritative current government-reported 23-type residential building-stock
model and occupied-dwelling type weights.

## Canonical boundaries

BTR TYPE WEIGHT != CENSUS DWELLING IDENTITY

WITHIN-GROUP TYPE SHARE != RAW BTR TOTAL AS CANONICAL DENOMINATOR

OFFICIAL MODEL-WEIGHTED CALIBRATION != OBSERVED HOUSEHOLD FAIL RATE

NATIONAL TYPE MIX != LOCAL WBL POINT TYPE ASSIGNMENT

TYPE 11/15/16/23 RESIDUAL != WHOLE-STOCK MULTIGLAZED UW BLOCKER
