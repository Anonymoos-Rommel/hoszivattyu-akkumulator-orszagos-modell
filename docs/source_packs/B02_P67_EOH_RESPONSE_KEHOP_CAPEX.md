# B02-P67 — EoH response envelope + KEHOP official cost ceiling

**State:** `FOREIGN RESPONSE AUTHORITY QUALIFIED / HUNGARIAN COST CEILING QUALIFIED / Q-B02-004 NARROWED`

**Base:** P66 feature head `9949d26743942da1c9c3924ce67e9fe2b9d2f0e6`

**Implementation date:** 2026-09-21

## 1. Purpose

P66 reduced Q-B02-004 to two broad evidence needs:

- action/archetype response;
- CAPEX price authority.

P67 replaces both broad labels with source-bounded authorities and narrower residuals.

Canonical boundaries:

`FOREIGN RESPONSE FREQUENCY != HUNGARIAN POPULATION WEIGHT`

`EMITTER MEASURE COUNT != P66 ACTION LABEL`

`MEASURED SPF != DESIGN-POINT COP`

`OFFICIAL MAXIMUM ELIGIBLE COST != MARKET-TYPICAL COST`

## 2. DESNZ/BEIS Electrification of Heat response surface

The Electrification of Heat Demonstration Project was funded by BEIS/DESNZ and led by Energy Systems Catapult.

Official project reporting records **742 installed heat pumps** across a broad range of British housing types and states that **93%** of installed homes required replacement of at least one radiator.

The public Property, Design and Installation dataset contains a Property_ID link key and fields covering building form, age, floor area, heating system, MCS space-heating load, installed heat-pump size, emitter measures and installation costs.

The public Heat Pump Performance Data Summary contains the same Property_ID and measured/derived performance outputs including SPFH4 and mean space-heating flow/return temperatures. The catalogue states that performance data were collected at approximately two-minute intervals between October 2020 and September 2023, then cleansed, quality checked and analysed.

### Reproducible analysed snapshot

For reproducible derivation, P67 inspected a public research mirror of the source exports:

- Property/design/install blob: `f6080882d5941fb603e02e5138b05e39e2c247cd`
- performance-summary blob: `87a590ee13b2d7ff9beb9c04d4694b18f065b57f`

The mirror is **transport only**, not authority. Authority remains the DESNZ/ESC datasets.

The analysed snapshot contains exactly **742 installed systems**, reconciling to the official project total. Of those, **689** have at least one positive source-native emitter-measure count:

`689 / 742 = 0.928571...`

which reproduces the official rounded 93% finding.

This reconciliation is used as an integrity check, not as a Hungarian prevalence estimate.

## 3. Conditional response envelope

The machine-readable response registry is:

`registry/b02_p67_eoh_response_envelope.csv`

It retains source-bounded conditional distributions for:

- installed sample size;
- emitter-measure presence;
- emitter measure-count P10/P50/P90;
- MCS space-heating design load P10/P50/P90;
- joined measured mean space-heating flow temperature P10/P50/P90;
- joined measured SPFH4 P10/P50/P90.

The primary stratification used in this slice is source-native house form:

- Detached;
- Semi-Detached;
- Mid-Terrace;
- End-Terrace;
- Flat.

No UK frequency is used as a Hungarian stock weight.

## 4. Why this does not directly close the P66 action taxonomy

The source-native fields `Measures_emitters_LT`, `Measures_emitters_Std` and `Measures_Fanassist` quantify emitter measures. They do not encode the P66 mutually exclusive transition decisions:

- KEEP;
- UPSIZE;
- CHANGE;
- ADD;
- REPLACE.

Therefore:

`EOH EMITTER MEASURE != P66 ACTION LABEL`

The correct use is validation/calibration of the physical response envelope after P21/P65 supplies Hungarian stock weighting and the record/project transition engine supplies P66 action semantics.

The remaining action blocker is now specifically:

`P66_ACTION_CROSSWALK + P21_HUNGARIAN_REWEIGHTING`

not generic missing response data.

## 5. Measured flow temperature and SPF boundary

The joined performance subset provides actual monitored operating response.

P67 retains mean space-heating flow temperature and SPFH4 as measured/derived realized-operation outputs.

Boundary:

`SPFH4 != B05 DESIGN-POINT COP`

The measured response may validate or calibrate the B05/B06 chain. It may not overwrite the design-point physics engine.

## 6. Hungarian official CAPEX upper-bound authority

KEHOP Plusz-4.1.7-24, effective **2025-10-15**, Annex 1 publishes maximum gross eligible material and labour costs.

Relevant source-native rows:

| Measure | Material max | Labour max | Total max |
| --- | ---: | ---: | ---: |
| Hőleadók cseréje | 1,422,400 Ft/set | 2,133,600 Ft/set | **3,556,000 Ft/set** |
| Air-water heat-pump system | 6,438,980 Ft/set | 2,112,867 Ft/set | **8,551,847 Ft/set** |
| Floor-heating pipe system | 18,034 Ft/m2 | 19,050 Ft/m2 | **37,084 Ft/m2** |
| Ceiling heating/cooling | 19,050 Ft/m2 | 31,750 Ft/m2 | **50,800 Ft/m2** |

These are explicit programme maximums.

Therefore:

`CAPEX_PRICE_AUTHORITY -> QUALIFIED_OFFICIAL_UPPER_BOUND`

for upper-bound analysis.

They are not admitted as:

- market-average prices;
- expected realized prices;
- minimum costs;
- household-independent total project costs.

The response/action model still determines which package and how much area/quantity applies.

## 7. Q-B02-004 effect

P67 retires the broad statement that no response or Hungarian price authority exists.

Current residual:

1. `P66_ACTION_CROSSWALK`
2. `P21_HUNGARIAN_REWEIGHTING`
3. `MARKET_REALIZED_COST_DISTRIBUTION` — only if a central/expected monetary CAPEX estimate is required.

An official programme cost **upper envelope** can already be constructed once action/quantity propagation is available.

B02 readiness remains **55%**. This slice adds stronger usable evidence but does not yet produce the national programme action/COP/CAPEX result.

## 8. Non-claims

P67 does not claim:

- 92.86% Hungarian emitter replacement;
- any EoH house-form share as a Hungarian prevalence;
- that every EoH emitter measure is REPLACE;
- that measured SPFH4 equals design COP;
- that KEHOP ceilings are market averages;
- a national point CAPEX;
- Q-B02-004 closure.
