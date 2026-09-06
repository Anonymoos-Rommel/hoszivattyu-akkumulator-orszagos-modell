# B02-P25 — TÁRKI–REKK 2022 current gas-convector emitter anchor

**State:** `CURRENT NUMERIC EMITTER CONTROL QUALIFIED / COMPLETE STOCK ASSIGNMENT Q`

**Reference date:** 2026-09-06

## 1. Purpose

P23 bounded the public aggregate emitter surfaces and P24 proved that individual official e-tanúsítás certificates can carry current heat-emitter evidence. P25 asks a narrower quantitative question:

> Is there a contemporary, nationally representative public Hungarian survey that publishes a numeric current heat-emitter/device control which can constrain later B02 emitter linkage without fabricating a WBL assignment?

The answer is **yes for gas convectors**, but not for the complete emitter stock.

## 2. Public source

Primary public study:

- **Title:** `Az orosz gáz kivezetésének lehetősége Magyarországon`
- **Research:** BME + Regionális Energiagazdasági Kutatóközpont (REKK), with TÁRKI household fieldwork
- **Public PDF:** https://rekk.hu/downloads/projects/ECF_HU_Gas_phaseout_REKK_study_final.pdf
- **Survey fieldwork:** 2022-10-15 to 2022-11-02
- **Full successful sample:** `N = 1,013` households
- **Method:** personal interviews; 81-question questionnaire; multistage proportionally stratified probability sampling
- **Weighting/representativeness:** the final sample was weighted with KSH controls and is reported as representative by region and residential building type
- **Reported overall full-sample margin of error:** `3.4%`

Canonical source ID for this P25 evidence surface:

`SRC-B02-TARKI-REKK-HOUSEHOLD-ENERGY-SURVEY-2022`

The public report is used directly; no private survey microdata and no request response are required for P25.

## 3. Exact published gas-heating device control

Section 10.1 / Figure 11 of the public study reports the heating-device distribution among households using gas for heating:

- universe: `GAS_HEATING_HOUSEHOLDS`;
- sample for this figure: `N = 657`;
- traditional gas boiler: `26.66%`;
- condensing gas boiler: `32.73%`;
- gas convector: `40.61%`;
- the three published shares sum to exactly `100.00%`.

The accompanying text states that the gas convector is the most widespread heating device and is present in roughly two-fifths of households that heat with gas.

The three values are published calculations from an observed household survey. In the repository they are therefore recorded as `DER`, not as direct WBL `OBS` rows.

## 4. Why gas convector is an emitter anchor but boilers are not

For the present B02 claim:

`GAS CONVECTOR = CURRENT EMITTER/ROOM-HEATING DEVICE CONTROL`

but:

`TRADITIONAL GAS BOILER != RADIATOR`

`CONDENSING GAS BOILER != RADIATOR`

A boiler is a heat generator. It does not identify whether the dwelling distributes heat through radiators, floor heating, wall heating or another hydronic emitter.

The boiler shares remain useful figure-reconciliation controls, but they do not close the heat-emitter blocker.

## 5. Survey questionnaire semantics

The same study publishes its household questionnaire in the appendix. It explicitly distinguishes primary and secondary heating equipment, including:

- district heating;
- traditional gas boiler;
- condensing gas boiler;
- gas convector;
- wood/mixed-fuel boiler;
- stove / tile stove / fireplace;
- split air conditioner;
- heat pump;
- other electric heating, including electric boiler / electric radiator / floor heating / fan heater.

This confirms that the 40.61% gas-convector result is based on an explicit device category, not an inference from fuel alone.

## 6. Relationship to the complete WBL011 stock

P22 already has exact 2022 Census heating-mode and heating-fuel observations for all `116,452` positive WBL full-joint cells / `4,008,541` occupied dwellings.

P25 does **not** multiply the 40.61% survey share across WBL gas-fuel cells.

The necessary boundaries are:

`NATIONALLY REPRESENTATIVE SURVEY CONTROL != WBL CELL ASSIGNMENT`

`HOUSEHOLD SURVEY UNIVERSE != OCCUPIED-DWELLING WBL UNIVERSE WITHOUT RECONCILIATION`

`GAS-CONVECTOR SHARE AMONG GAS-HEATING HOUSEHOLDS != SHARE AMONG ALL OCCUPIED DWELLINGS`

`HEATING FUEL != EMITTER TYPE`

No assumption is made that every gas-heating WBL cell has the same 40.61% convector probability.

## 7. Uncertainty boundary

The report states a `3.4%` margin of error for the full `N=1,013` sample.

P25 does **not** attach that number to the conditional `N=657` gas-heating-device distribution without a separate subgroup uncertainty calculation.

Therefore:

`FULL-SAMPLE MARGIN OF ERROR != CONDITIONAL SUBGROUP MARGIN OF ERROR`

The exact published point shares are preserved, but a later calibrated linkage must define and propagate its own uncertainty method.

## 8. STADAT chronology correction

P22 described KSH STADAT 14.8.2.2 as a `2022` household-survey heating-mode distribution. Fresh inspection shows that the public archive page was last updated in 2022 but its displayed annual series ends at **2020**.

P25 corrects that wording only; it does not alter any P22 WBL assignment, because P22 never used the STADAT percentages in runtime.

Canonical boundary:

`PAGE UPDATE YEAR 2022 != DATA REFERENCE YEAR 2022`

The complete P22 WBL011 Census assignment remains unchanged and authoritative for source-native heating topology.

## 9. Admission impact

P25 establishes:

`PUBLIC CURRENT GAS-CONVECTOR NUMERIC CONTROL = QUALIFIED_CONTROL_ONLY / DER`

It does **not** establish:

- a complete occupied-stock emitter assignment;
- a WBL direct join;
- radiator versus surface-heating allocation for boiler-heated dwellings;
- district-heated dwelling emitter type;
- a current design supply/return temperature pair;
- technical eligibility.

Therefore the current technical-readiness state remains:

`TECHNICAL_READINESS_ARCHETYPE = Q`

with exactly:

- `NO_CURRENT_HEAT_EMITTER_EVIDENCE`;
- `NO_CURRENT_DESIGN_TEMPERATURE_EVIDENCE`.

The first blocker is now quantitatively narrowed by a real current numeric emitter anchor, but it is not closed.

## 10. Next evidence use

The next justified emitter-model step, if undertaken, is not a national 40.61% broadcast. It is a calibrated partial linkage that must first establish a defensible relationship between:

1. the survey `GAS_HEATING_HOUSEHOLDS` universe;
2. source-native WBL heating-mode × heating-fuel cells;
3. any settlement/building-type controls available for the gas-heating population;
4. explicit uncertainty propagation.

Until that exists, P25 remains an evidence anchor only.

## 11. Non-claims

P25 does not claim that:

- 40.61% of all Hungarian dwellings use gas convectors;
- 40.61% of every gas-fuel WBL cell uses gas convectors;
- boiler-heated dwellings are radiators;
- the full-sample 3.4% margin of error applies to Figure 11's N=657 subgroup;
- survey households and Census occupied dwellings are interchangeable units;
- the public report closes either remaining technical-readiness blocker;
- B02 readiness should increase merely because this control is now registered.
