# B02-P114 — CURRENT HUNGARIAN WINDOW-GLAZING POPULATION BOUND

## Goal

P114 stops treating the KEHOP/FAIR 1103 administrative route as the only path
to current-window evidence.

It admits direct, current, representative Hungarian physical-stock evidence
from the 2023 EU-SILC household-energy-efficiency module and combines it with
current Hungarian technical authority.

This is a numeric evidence slice, not another FAIR semantics slice.

## 1. Direct current Hungarian window-stock observation

Eurostat's assessment of the 2023 EU-SILC ad-hoc household-energy-efficiency
module reports the following Hungary HC004 current window-type distribution:

- only single glazing: 16.2%
- only double glazing: 63.1%
- triple glazing or more: 12.2%
- mixed single and double/triple glazing: 5.3%
- mixed double and triple glazing: 3.2%
- don't know: 0.0%

Therefore the share with at least one single-glazed window is:

16.2% + 5.3% = 21.5%.

HC004 is a current household/dwelling characteristic, not a renovation-event
proxy.

## 2. Same-survey non-district marginal

The same EU-SILC 2023 Hungary module reports HC001:

- district heating: 15.4%
- central heating: 6.1%
- individual heating: 78.1%
- non-fixed heating: 0.3%
- no heating: 0.1%
- don't know: 0.0%

Therefore:

NON_DISTRICT = 84.6%.

P114 does not assume independence between HC001 and HC004.

## 3. Dependence-free Frechet bound

Let:

A = single-glazing-present = 0.215

B = non-district = 0.846

Then:

P(A intersect B) >= max(0, 0.215 + 0.846 - 1) = 0.061.

Conditioned on the non-district household population:

0.061 / 0.846 = 0.072104018913.

Therefore at least 7.2104018913% of the current Hungarian non-district
household population has at least one single-glazed window.

The upper dependence-free edge is:

min(0.215, 0.846) / 0.846 = 0.254137115839.

Thus the exact no-independence interval is:

[7.2104018913%, 25.4137115839%]

for single-glazing presence among non-district households.

This is not an observed HC001 x HC004 cross-tab.

## 4. Single glazing is a direct current technical deficit class

Current 9/2023 EKM authority sets the glazing requirement at:

U <= 1.0 W/m2K.

The official 2nd Appendix technical reference gives:

ordinary 4 mm single glazing U_glass = 5.8 W/m2K.

Therefore single glazing is directly above the current glazing reference.

This proves a physical deficit class.

It does not manufacture a whole-window Uw value because the current whole-window
requirement also depends on frame, glazing and spacer effects.

## 5. Why double glazing is not promoted to compliance

The same official technical appendix gives materially different U_glass values
for double glazing depending on construction, coating and gas fill, including
approximately:

- 2.9 W/m2K
- 1.6 W/m2K
- 1.2 W/m2K
- 1.1 W/m2K.

Therefore:

DOUBLE GLAZING != CURRENT WHOLE-WINDOW COMPLIANCE.

The same fail-closed rule is retained for triple glazing because HC004 does not
identify coating, gas fill, frame or realized whole-window Uw.

## 6. Consequence for the blocker

The broad claim that there is no direct current national window-population
surface is no longer correct.

P114 supplies:

- direct current Hungary glazing-type shares;
- a hard observed 21.5% single-glazing-present national marginal;
- a same-survey 84.6% non-district marginal;
- a dependence-free minimum 7.2104018913% single-glazing presence within the
  non-district household population;
- direct Hungarian technical proof that single glazing is a current glazing
  deficit class.

The next performance blocker is:

CURRENT_MULTIGLAZED_WINDOW_REALIZED_UW_DISTRIBUTION_REQUIRED

An exact multiplication into the B02 Census dwelling count still requires:

HC004_HOUSEHOLD_TO_B02_DWELLING_POPULATION_BINDING_REQUIRED

No 1:1 household-to-dwelling identity is assumed.

## 7. KEHOP 1103 route after P114

The KEHOP/FAIR route remains valuable as a recent replaced-window technical
calibration route.

It is no longer the only available route to a direct national current-window
physical observation.

## 8. Overall programme bound

P114's direct window-deficit floor is smaller than the already admitted P102
calibrated structural retrofit floor.

Therefore it must not be added as if the two deficits were disjoint.

Current overall numeric state remains:

- calibrated retrofit floor: 82.7861029945%
- HP_ONLY lower: 0%
- HP_ONLY upper: 17.2138970055%
- B02 readiness: 55%
- PEAK_LOAD_EFFECT: 50%

## Sources

### SRC-B02-EUROSTAT-SILC-2023-ENERGY-MODULE-ASSESSMENT

European Commission / Eurostat assessment of the 2023 EU-SILC modules.

Role:
source-native Hungary HC001 and HC004 current marginals.

### SRC-B02-EU-2021-2052-HC001-HC004

Commission Implementing Regulation (EU) 2021/2052.

Role:
official HC001/HC004 semantics, household collection unit and current reference
period.

### SRC-B02-HU-2023-EKM-CURRENT-U

9/2023. (V. 25.) EKM rendelet, official NJT text.

Role:
current glazing and whole-window U requirements.

### SRC-B02-HU-EKM-APPENDIX2-GLAZING-U

Official government technical Appendix 2.

Role:
reference glazing U values, including 4 mm single glazing = 5.8 W/m2K and the
wide double-glazing range.

## Canonical boundaries

SINGLE GLAZING PRESENT != WHOLE-WINDOW UW VALUE

DOUBLE GLAZING != CURRENT UW COMPLIANCE

TRIPLE GLAZING != CURRENT UW COMPLIANCE

HOUSEHOLD-WEIGHTED SURVEY SHARE != EXACT DWELLING COUNT

MARGINALS + FRECHET != OBSERVED JOINT TABLE
