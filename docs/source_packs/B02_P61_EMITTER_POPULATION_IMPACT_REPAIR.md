# B02-P61 — emitter population-impact layer repair

**State:** `Q-B02-004 OPEN / NOT AN AGGREGATE ELIGIBILITY PRECONDITION / PROGRAMME-SUFFICIENCY IMPACT CONTRACTED`

**Canonical base:** `4c8dcf9de1a2c4e61f21a5b407454b7a2a5dc89c`

**Implementation / research date:** 2026-09-20

## 1. Purpose

P51 correctly narrowed the missing national evidence to:

`NON_DISTRICT_HYDRONIC_EMITTER_MIX + DESIGN_TEMPERATURE_DISTRIBUTION`.

P61 repairs a remaining layer error: the same evidence gap was still described in parts of the canonical question registry as though it had to be closed before a national technical-eligibility estimate could even be attempted.

That is no longer consistent with the current transition architecture.

The canonical current technical contract already states:

`CURRENT_REQUIRED_GAP_IDS = ()`

and the later transition slices establish:

- P65 — thermal distribution is a record/project transition-design component;
- P57 — hydraulic readiness can follow `REUSE / UPGRADE / REPLACE`;
- P58 — electrical readiness can follow existing/upgrade/new-connection paths;
- P59 — site permission/legal delivery is a separate site-level gate.

Therefore:

`CURRENT EMITTER MIX != TECHNICAL ELIGIBILITY PRECONDITION`

`CURRENT EMITTER NOT LOW-TEMP-READY != TECHNICALLY INELIGIBLE`

`EMITTER MIX -> NATIONAL RETROFIT QUANTITY / CAPEX / COP UNCERTAINTY`

`RECORD DESIGN -> KEEP / UPSIZE / CHANGE / ADD / REPLACE`

P61 does not close Q-B02-004. It puts the remaining uncertainty into the correct decision layer.

## 2. Current technical-eligibility architecture

The executable current contract in:

`modules/B02/technical_eligibility_contract.py`

requires, at record/project grain:

- `THERMAL_DISTRIBUTION`;
- `HYDRAULIC`;
- `ELECTRICAL`.

PASS/FAIL requires real `OBS`/`DER` evidence. Missing evidence remains `Q`.

However, current-stock national coverage of emitter, hydraulic or electrical readiness is not an aggregate prerequisite for opening this gate.

This distinction matters because a dwelling with an unsuitable current radiator or pipe network may still have a valid heat-pump transition path after an emitter/hydraulic upgrade. Likewise, an undersized current electrical service can have an explicit DSO upgrade path.

Therefore a national count of current low-temperature-ready emitters is **not** the same estimand as the national count of technically transitionable dwellings.

## 3. Q-B02-001 impact

Q-B02-001 remains OPEN, but its missing evidence changes.

It no longer waits mechanically for Q-B02-004.

A defensible national technical-eligibility estimate instead needs population evidence for the terminal outcomes of the allowed transition paths:

- thermal distribution can/cannot be designed to PASS after allowed emitter actions;
- hydraulic system can/cannot reach a commissioned design after reuse/upgrade/replacement;
- electrical demand can/cannot be served after allowed connection path and DSO decision.

The model must not turn an unknown record into PASS or FAIL.

Therefore:

`Q-B02-004 OPEN != Q-B02-001 MUST WAIT FOR EMITTER PREVALENCE`

but also:

`NO POPULATION TERMINAL TRANSITION-OUTCOME EVIDENCE -> Q-B02-001 REMAINS OPEN`.

## 4. Q-B02-004 impact after P61

Q-B02-004 remains important because programme design needs to know the composition and cost of the transition.

The missing national emitter/design-temperature distribution directly affects:

1. seasonal heat-pump COP distribution;
2. KEEP / UPSIZE / CHANGE / ADD / REPLACE shares;
3. existing and replacement radiator/emitter quantities;
4. emitter/hydraulic retrofit CAPEX;
5. valves, fittings, pipework and labour quantities;
6. procurement and logistics volumes;
7. installation capacity and programme timing;
8. national uncertainty bands for those outputs.

It is therefore a **programme-sufficiency / physical-cost distribution** blocker, not an aggregate eligibility-precondition.

## 5. Existing population evidence retained

### 5.1 Gas convectors — P39

The approved calibrated gas-convector branch remains:

`APPROVED / JOSEPH / QUALIFIED`.

This is population-model evidence, not direct observation of every dwelling and not record-level PASS/FAIL evidence.

### 5.2 District/panel radiator branch — P44 onward

The repository contains Hungarian bounded evidence for:

- radiator quantities in panel/district contexts;
- RADAL and current radiator type/size examples;
- lower-temperature performance;
- KEEP/UPSIZE/CHANGE logic;
- implemented retrofit portfolios;
- old/new emitter schedules.

These are strong calibration and engineering controls. They are not automatically national prevalence weights.

### 5.3 NÉER2/KEOP — realised N=2029

P51 already exacted the representative historical technical survey:

- realised 2029 on-site surveyed buildings;
- 23 typology classes;
- territorial/census representativeness control;
- structured building-services fields.

The public derivative still does not expose a complete radiator/surface-heating/fan-coil distribution or design flow/return distribution.

## 6. New public-source audit

### 6.1 BME RBSM 2026 — uncertainty method, not emitter prevalence

Source:

`SRC-B02-BME-RBSM-2026`

Authority:

`https://pp.bme.hu/me/article/view/43518`

Erdős and Horváth's 2026 BME residential building-stock paper uses EPC-derived building envelope and system characteristics and applies Latin Hypercube Sampling plus global sensitivity analysis to propagate input uncertainty.

This is directly useful as **method authority** for the project-wide population-inference doctrine.

However, the inspected publication's HVAC uncertainty surface uses a traditional gas-boiler archetype and exposes heating-system efficiency rather than a national emitter-class variable. No radiator/surface-heating/fan-coil prevalence or design-temperature distribution is published in the inspected article.

Boundary:

`RBSM UNCERTAINTY FRAMEWORK != RBSM EMITTER PREVALENCE DATA`.

### 6.2 Energiaklub Lakcímke 2010 — qualitative structural prior only

Source:

`SRC-B02-ENERGIAKLUB-LAKCIMKE-2010`

Authority:

`https://lakcimke.energiaklub.hu/lakcimke.pdf`

The Hungarian professional guide states that central heating is predominantly hot-water radiator heating, with floor or other surface-heating systems occurring in smaller numbers. It separately characterises low-temperature surface heating at roughly 40 °C water temperature and central radiator heating as the most widespread high-temperature solution.

This is useful as a **directional structural prior**:

`RADIATOR SHARE > SURFACE-HEATING SHARE WITHIN CENTRAL HYDRONIC STOCK — QUALITATIVE ONLY`.

It cannot create a percentage, confidence interval or current-2026 stock weight.

Boundary:

`PREDOMINANT != NUMERIC SHARE`

`2010 PROFESSIONAL GUIDANCE != 2026 CURRENT-STOCK OBSERVATION`.

### 6.3 KSH OSAP 1831 — current taxonomy / possible flow route

Source:

`SRC-B02-KSH-OSAP-1831-2026`

Authority:

`https://www.ksh.hu/docs/hun/info/02osap/2026/segedlet/s261831.pdf`

The official current KSH construction-work taxonomy separately identifies:

- `1-22-02 Padlófűtés`;
- `1-22-03 Radiátoros fűtés`;
- `1-22-04 Fan-coil szerelése`.

This proves that the official current KSH price-statistics instrument has an explicit taxonomy capable of distinguishing these work types.

The KSH construction-price methodology states that OSAP 1831 is a **quarterly construction-price survey**. Selected construction firms report prices for representative construction items with fixed technical parameters. It is not a national installation-volume census.

It therefore does **not** prove:

- installed residential stock shares;
- current household emitter prevalence;
- a residential denominator;
- national completed-work quantities for these categories;
- national radiator/floor-heating/fan-coil installation flow.

Boundaries:

`CURRENT OFFICIAL TAXONOMY != INSTALLED STOCK DISTRIBUTION`

`CONSTRUCTION PRICE OBSERVATION != INSTALLATION QUANTITY FLOW`.

The practical value is taxonomy and future price/CAPEX interpretation only, not prevalence calibration.

## 7. Existing routes that remain useful

### KSH Miben élünk? 2015

The representative housing survey remains useful for housing/renovation covariates, but its inspected public publication does not provide radiator/floor/fan-coil subtype prevalence.

### BRG Hungary Heating and Cooling 2026

P46 already proves a current Hungary-specific commercial route with an explicit `Residential Radiators Park` surface.

It remains:

`QUALIFIED_PROVIDER_ROUTE / NUMERIC CELLS NOT PUBLICLY ACQUIRED`.

No paywalled value is inferred from the table of contents.

## 8. Machine-readable P61 contract

`registry/b02_p61_emitter_population_impact.csv` assigns each evidence surface:

- evidence role;
- current status;
- population-output use;
- whether it is an eligibility prerequisite;
- allowed programme uses;
- forbidden promotion;
- residual gap.

The aggregate Q-B02-004 row explicitly sets:

`eligibility_precondition = NO`

and retains:

`NON_DISTRICT_HYDRONIC_EMITTER_MIX;DESIGN_TEMPERATURE_DISTRIBUTION`

as programme-output gaps.

## 9. Non-claims

P61 does not claim:

- a national radiator percentage;
- a national surface-heating percentage;
- a national design-temperature distribution;
- a radiator-unit stock count;
- a replacement fraction;
- a technical-eligible dwelling count;
- that every current radiator can remain;
- that every current radiator must be replaced;
- that a 2010 qualitative statement represents the 2026 stock.

No readiness percentage is increased.

## 10. Next research target

The search can now be narrower and more valuable.

### Route A — current EPC/RBSM emitter field recovery

The OSAP 1831 route is now closed as a quantity route: it is price statistics, not installation-volume evidence.

Determine whether the underlying BME/EPC research data model contains an emitter-class field that is simply not used in the 2026 published archetype paper.

### Route B — direct population evidence

Determine whether the underlying BME/EPC research data model contains an emitter-class field that is simply not used in the 2026 published archetype paper.

### Route B — direct population evidence

Continue searching for a representative or calibratable Hungarian sample with direct current:

`RADIATOR / SURFACE_HEATING / MIXED / OTHER`

classification.

Any resulting national estimate must retain explicit weighting/calibration, uncertainty and structural sensitivity.

The correct project architecture is therefore:

`POPULATION EMITTER MIX -> PROGRAMME QUANTITY/COST/COP DISTRIBUTION`

while:

`RECORD TRANSITION DESIGN -> TECHNICAL PASS/Q/FAIL`.
