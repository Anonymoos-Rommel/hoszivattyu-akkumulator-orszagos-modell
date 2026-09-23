# B02-P102 — RENOVATED ENVELOPE U-QUALITY CALIBRATION

## Goal

Narrow the P101 residual:

`CURRENT_RENOVATED_ENVELOPE_U_QUALITY_TIGHTENING_REQUIRED_FOR_HP_ONLY_LOWER_BOUND`

using already-admitted P80 physical evidence before acquiring a new source.

## 1. Source boundary

Csoknyai Table 8.3 explicitly separates renovated and unrenovated component
U-values by the 23 synthetic residential types.

The source also explicitly warns that renovated averages must be treated with
caution because renovated-case counts are often low. Where occurrence is very
low or zero, the source intentionally leaves the result N/A.

Therefore P102 admits these values only as:

`HISTORICAL RENOVATED SYNTHETIC-TYPE CALIBRATION`.

They are not current household observations.

## 2. Full P80 renovated-U audit

Against the P100/P96 reference-programme limits:

| Component | Valid renovated U types | Above target | At/below target | Missing/N/A |
|---|---:|---:|---:|---:|
| External wall, 0.24 | 19 | 19 | 0 | 4 |
| Attic floor, 0.17 | 14 | 12 | 2 | 9 |
| Flat roof, 0.17 | 8 | 8 | 0 | 15 |
| Pitched roof, 0.17 | 16 | 15 | 1 | 7 |
| Basement ceiling, 0.26 | 11 | 11 | 0 | 12 |
| Replaced window, 1.15 | 0 | 0 | 0 | 23 |

The result is important but does not justify household-level classification.

## 3. Why the external wall is binding in P102

TARKI-REKK Table 38 publishes 2022 type-level:

- insulated facade;
- insulated attic;
- window replacement.

For the facade, the semantic link is direct enough for bounded synthetic-type
calibration:

`INSULATED FACADE -> EXTERNAL WALL RENOVATED BRANCH`.

For 19/23 types P80 has a physical renovated external-wall mean U. Every one
of those 19 means is worse than the reference 0.24 W/m2K limit.

At the synthetic type-mean model layer P102 therefore treats both wall branches
as calibrated deficient for those 19 types.

Critical boundary:

`RENOVATED TYPE MEAN ABOVE TARGET != ALL RENOVATED HOUSEHOLDS FAIL`.

For types 11, 15, 16 and 23 the historical renovated wall U is missing. Their
current insulated-facade branch remains unresolved.

## 4. Why the top-envelope data are not directly promoted

TARKI-REKK exposes one 2022 `hőszigetelt padlás` metric.

P80 separates:

- ATTIC_FLOOR;
- FLAT_ROOF;
- PITCHED_ROOF.

P102 does not silently identify the single current metric with one of these
physical component states. The historical occurrence surfaces also show that a
naive denominator identity would not be safe.

Therefore the top-envelope renovated-U audit is retained as calibration
evidence only.

## 5. Window blocker

The historical source publishes:

- replaced-window share;
- non-replaced-window mean U.

It does **not** publish a replaced-window U statistic.

TARKI-REKK 2022 likewise publishes a window-replacement share, not achieved U.

Therefore:

`WINDOW REPLACED SHARE != REPLACED WINDOW U`.

The primary next evidence residual becomes:

`CURRENT_REPLACED_WINDOW_U_QUALITY_EVIDENCE_REQUIRED`.

## 6. Type-level tightening rule

For each type:

1. current uninsulated facade share remains a calibrated wall deficit;
2. if the historical renovated external-wall mean exists and exceeds 0.24,
   the current insulated-facade branch is also classified as calibrated
   deficient at the synthetic type-mean layer;
3. if renovated wall U is missing, the insulated branch remains unresolved;
4. current not-replaced windows retain the P101 calibrated deficit marginal;
5. wall/window overlap remains unknown, so the combined floor is bounded
   set-theoretically.

No independence assumption is introduced.

## 7. P79/P21 propagation

The complete P79 candidate-type sets are propagated over all 14 WBL
construction-period x P21 building-group strata.

The P21 CENTRAL and FLAT building-group models then weight those strata over
the exact 4,008,541 occupied-dwelling universe.

The validated national results are:

- CENTRAL calibrated type-mean retrofit-floor lower edge:
  **83.1880896082%** = **3,334,628.6791 expected dwelling-equivalents**;
- CENTRAL candidate-set upper edge of that calibrated floor:
  **98.4485726963%**;
- FLAT calibrated type-mean retrofit-floor lower edge:
  **82.7861029945%** = **3,318,514.8808 expected dwelling-equivalents**;
- FLAT candidate-set upper edge:
  **98.4317137822%**.

The conservative structural calibrated floor is therefore:

**82.7861029945%**.

Relative to P101's **37.7812177225%** floor, the P102 historical-renovated
wall-quality calibration increases the model-layer floor by:

**45.0048852720 percentage points**.

The corresponding HP_ONLY candidate upper edge tightens from **62.2187822775%**
to **17.2138970055%**. The HP_ONLY lower edge remains **0%** because no current
population mass is yet proven compliant across all applicable envelope
components.

These numbers are synthetic type-mean calibrated programme bounds, not observed
household failure rates and not a final national retrofit mandate.

Exact values are materialized in `p102_national_action_bounds.csv` and frozen
by regression.

## 8. Blocker effect

P101:

`CURRENT_RENOVATED_ENVELOPE_U_QUALITY_TIGHTENING_REQUIRED_FOR_HP_ONLY_LOWER_BOUND`

P102 splits this into concrete residuals:

1. `CURRENT_REPLACED_WINDOW_U_QUALITY_EVIDENCE_REQUIRED`;
2. `MISSING_HISTORICAL_RENOVATED_WALL_U_TIGHTENING_REQUIRED`.

The first is the primary next acquisition target because replaced-window U is
absent for all 23 types.

## 9. Readiness

P102 is a material numerical tightening of the envelope action surface, but it
does not establish current household compliance and it does not complete the
full design-load chain.

Therefore:

- **B02 remains 55%**;
- **PEAK_LOAD_EFFECT remains 50%**;
- **Q-B02-004 remains OPEN_NARROWED**.

## 10. Canonical boundaries

`HISTORICAL RENOVATED TYPE MEAN U != CURRENT RENOVATED HOUSEHOLD U`

`RENOVATED TYPE MEAN ABOVE TARGET != ALL RENOVATED HOUSEHOLDS FAIL TARGET`

`CALIBRATED TYPE-BRANCH DEFICIT != OBSERVED HOUSEHOLD FAIL SHARE`

`CURRENT INSULATED ATTIC != IDENTIFIED P80 TOP-ENVELOPE COMPONENT`

`WINDOW REPLACED SHARE != REPLACED WINDOW U`
