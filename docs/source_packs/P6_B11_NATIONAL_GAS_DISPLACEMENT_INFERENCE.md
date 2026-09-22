# B11-P6 — national gas-displacement inference layer

## Purpose

P6 applies the project-wide population-inference policy to B11 without weakening exact participant, gas-quality-point or billing claims.

Core rules:

`NATIONAL GAS QUALITY DISTRIBUTION != PARTICIPANT GAS-QUALITY POINT`

`NATIONAL APPLIANCE CLASS MIX != SEASONAL EFFICIENCY DISTRIBUTION`

`COUNTY GAS SALES CONTROL != PARTICIPANT GAS VOLUME`

`PUBLIC REPOSITORY MATERIALIZATION != MODEL USABILITY`

## Existing national evidence admitted

B11 already contains:

- KSH census gas-heating population evidence;
- county household-gas sales controls;
- a useful-space-heat -> gas-input-energy -> gas-volume bridge;
- explicit GCV/LHV energy-basis handling;
- FGSZ gas-quality accounting methodology and point-level source lineage.

P6 additionally admits an already-canonical weighted Hungarian household survey control from:

`SRC-B02-TARKI-REKK-HOUSEHOLD-ENERGY-SURVEY-2022`

The published gas-heating subsample is **N=657** and reports:

- traditional gas boiler: **26.66%**
- condensing gas boiler: **32.73%**
- gas convector: **40.61%**

The three shares sum to 100%.

These are appliance-class population weights only. They do not provide seasonal efficiency values and cannot classify an individual WBL cell or programme participant.

## Gas-quality layer repair

B11-P5 remains the exact participant/point authority.

For an individual participant, billing point or source-native gas-quality claim, P5 still requires:

- exact participant -> gas-quality point mapping;
- exact point identity;
- exact period coverage;
- explicit GCV and LHV values;
- source lineage.

P6 changes only the national/programme inference plane.

A national bcm-displacement estimate may use a defensible region- or point-weighted GCV/LHV distribution with:

- explicit temporal alignment;
- explicit geographic/consumption weighting;
- bounded uncertainty;
- source provenance;
- no silent promotion of historical point statistics to current programme truth.

An exact participant-to-point crosswalk for every programme household is not a national bcm prerequisite.

## Repository materialization boundary

FGSZ public access and raw-table republication are separate questions.

P6 retires public-repository raw materialization as a prerequisite for national model use.

This does not grant permission to republish FGSZ point values.

Any runtime/private/external data path still requires source-specific legal/use authority and reproducible provenance.

## Seasonal appliance-efficiency layer

The old implicit requirement for one national seasonal gas-efficiency constant is replaced by:

`APPLIANCE_CLASS_WEIGHTED_BOUNDED_SEASONAL_EFFICIENCY_REQUIRED`

The TÁRKI-REKK survey now provides current Hungarian gas-appliance class weights.

Still missing are defensible seasonal fuel-conversion efficiency bounds for:

- traditional gas boilers;
- condensing gas boilers;
- gas convectors.

EU Ecodesign/product metrics remain product/regulatory evidence and are not silently converted into Hungarian in-use seasonal stock efficiency.

Once class-specific efficiency bounds exist, P6 permits their weighted/set-valued propagation rather than requiring one exact national efficiency point.

## Current national admission state

Current state:

`Q_NATIONAL_GAS_DISPLACEMENT`

Remaining national residuals include:

- class-specific seasonal efficiency bounds;
- temporally aligned bounded GCV/LHV distribution;
- multi-fuel gas-share decomposition;
- DHW/cooking end-use boundary;
- post-retrofit rebound bound;
- calibration/reconciliation to observed gas sales;
- explicit uncertainty propagation.

B03 wholesale/import valuation is downstream of physical bcm displacement and remains separate.

## Exact-claim boundary

P6 does not weaken:

- exact participant gas-volume claims;
- exact participant gas-quality point mapping;
- exact point-period GCV/LHV claims;
- exact appliance efficiency claims.

## Readiness

B11 remains **30%**.

P6 makes the national evidence problem materially narrower and materializes a real appliance-class population control, but it does not yet produce programme bcm displacement, so no arbitrary readiness uplift is applied.
