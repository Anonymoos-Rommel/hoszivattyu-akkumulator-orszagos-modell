# B02-P51 — NÉER2 population-inference re-audit and Q-B02-004 residual narrowing

**State:** `Q-B02-004 OPEN / RESIDUAL BLOCKER NARROWED / NO NATIONAL EMITTER DISTRIBUTION FABRICATED`

**Canonical base:** `e878340cb01818277d326bba8a86ff3dd719e1bd`

**Research date:** 2026-09-20

## 1. Purpose

The project-wide population inference policy changed the standard from exhaustive household microdata to defensible population inference.

P51 therefore re-audits the existing Q-B02-004 evidence chain rather than restarting the search for a complete national emitter database.

Canonical rule:

`NO FULL-POPULATION DATA != BLOCKER`

`NO DEFENSIBLE POPULATION INFERENCE == BLOCKER`

The target question remains:

> What national evidence can classify the housing stock by heat emitter and design supply temperature?

## 2. Existing evidence that already survives re-audit

### 2.1 Gas convectors

B02-P39 remains:

`APPROVED / JOSEPH / QUALIFIED`

The gas-convector emitter linkage is therefore an admitted national population-inference component.

It remains `ASS`/calibrated-model output, not direct observation, and cannot pass/fail a specific dwelling.

### 2.2 District/panel radiator controls

B02-P44 to P49 provide multiple Hungarian bounded controls for radiator/emitter quantity, type and reuse/change logic, including large district-heated cohorts, implemented retrofit portfolios and exact building-level radiator counts.

These are useful calibration/validation surfaces.

They are not silently summed or extrapolated to the entire occupied stock.

## 3. NÉER2 / KEOP representative survey — exact public evidence

Primary authority:

Tamás Csoknyai, *A magyarországi lakóépület-állomány energetikai modellezése, a korszerűsítés lehetőségei*, DSc dissertation, BME / MTA REAL-D, 2022.

URL:

`https://real-d.mtak.hu/1472/7/dc_2011_22_doktori_mu.pdf`

Relevant public locators:

- chapter 7, PDF pp.38-43;
- Table 7.2, PDF p.39;
- Table 7.3, PDF p.40;
- section 7.3, PDF p.40;
- section 7.4.4, PDF p.43;
- Annex 1 / Tables 14.1-14.2, PDF pp.127-128;
- Annex 2 / Tables 14.3-14.4, PDF pp.130-131.

### 3.1 Sample size and representativeness

The survey design targeted 2,000 buildings.

The realised field survey contains **2,029 buildings** across **23 building typology classes**.

The dissertation compares the realised sample against census building/dwelling composition and states that territorial deviations against dwelling-count census shares are only a few per mille, with similarly negligible differences at regional level.

Therefore P51 upgrades the current interpretation from a vague “2000-building typology” to:

`REALISED N=2029 REPRESENTATIVE TECHNICAL SURVEY -> QUALIFIED HISTORICAL POPULATION CALIBRATION SURFACE`

This is not a 2026 observation. Any current-stock use requires explicit recalibration/update uncertainty.

### 3.2 Survey execution quality

The 2,029 on-site surveys were performed by energy-certification experts with the specified Hungarian professional-chamber qualifications and were coordinated/checked by experienced county leads.

The experts also performed the official-method energy calculation for every surveyed building.

Therefore this is materially stronger than a convenience sample, listing sample or engineering case series.

### 3.3 Building-services data model

Section 7.4.4 states that building-services characteristics were captured as selectable technical solution/system-element categories and evaluated by their frequency within building types.

The published Annex 1 extract proves structured fields for, among other things:

- central heat-producer type, count, installation year, capacity, manufacturer and condition;
- individual heat-producer type, count, installation year and condition;
- heating-system modernization year;
- main-pipe length;
- riser count;
- pipe-insulation fields;
- heating metering/settlement.

The Annex introduction explicitly says the published field list was significantly simplified for readability, including building-services systems.

Boundary:

`PUBLISHED EXTRACT OMITS A FIELD != RAW SURVEY NEVER COLLECTED THAT FIELD`

but also:

`RAW DATA MAY BE RICHER != PUBLIC EMITTER DISTRIBUTION RECOVERED`

## 4. What the public NÉER2 material does not currently expose

The inspected public dissertation does **not** publish a national distribution for:

- radiator heat emission;
- surface/floor/wall/ceiling heating;
- fan-coil;
- mixed emitter systems;
- source-native design flow temperature;
- source-native design return temperature.

The public heating-system results in section 8.4 and Tables 14.3-14.4 are primarily heat-producer and energy-carrier distributions.

Therefore:

`HEAT PRODUCER != HEAT EMITTER`

`BOILER != RADIATOR`

`DISTRICT HEATING != RADIATOR`

`HYDRONIC SYSTEM != DESIGN TEMPERATURE`

No such mapping is fabricated in P51.

## 5. Q-B02-004 residual blocker after re-audit

The old broad blocker:

`NO CURRENT HEAT EMITTER EVIDENCE + NO CURRENT DESIGN TEMPERATURE EVIDENCE`

can now be narrowed at national-population level.

Already available:

1. gas-convector national calibrated branch — P39;
2. strong district/panel radiator calibration controls — P44-P49;
3. representative historical national technical survey frame — NÉER2/KEOP, realised N=2029;
4. record-level emitter/temperature decision authority — P65.

Still missing for a defensible national population distribution:

### R1 — non-district hydronic emitter mix

For relevant current stock strata:

`RADIATOR vs SURFACE_HEATING vs MIXED vs OTHER/UNKNOWN`

particularly gas-boiler and other central-boiler households outside the already bounded district/panel branch.

### R2 — design-temperature distribution

An observed or defensibly calibrated distribution of supply/return temperature conditional on the emitter/system classes used in the national model.

Therefore the canonical residual is:

`NON_DISTRICT_HYDRONIC_EMITTER_MIX + DESIGN_TEMPERATURE_DISTRIBUTION`

Q-B02-004 remains `OPEN`.

## 6. Next search logic

Do not search again for “all Hungarian heat emitters”.

Search only for evidence capable of closing R1 or R2:

1. public derivative tables from the NÉER2/KEOP survey that expose emitter classes or richer heating-system code lists;
2. large representative Hungarian housing/energy surveys with direct radiator/surface-heating fields;
3. anonymised or aggregate OÉNY/EPC technical evidence if/when available;
4. current large hydronic datasets that can calibrate the 2015 NÉER2 structure to current stock;
5. only if direct distribution remains unavailable, a calibrated multi-source inference with explicit uncertainty and validation against P39/P44-P49/KSH stock controls.

The model must retain:

`POPULATION ESTIMATE != RECORD PASS/FAIL`

P65 remains the authority for a specific dwelling's post-retrofit supply-temperature decision.
