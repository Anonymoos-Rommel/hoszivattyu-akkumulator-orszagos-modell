# B02-P63 — design-temperature semantic repair

**State:** BASELINE DESIGN-TEMPERATURE POPULATION REQUIREMENT RETIRED / POST-RETROFIT TEMPERATURE = TRANSITION-DERIVED OUTPUT / Q-B02-004 OPEN

**Stacked base:** B02-P62 head 70e096c9a9e53e87ff4da33f77d82e070628cd67

**Research / implementation date:** 2026-09-20

## 1. Purpose

P51 originally narrowed Q-B02-004 to two missing national surfaces: non-district hydronic emitter mix and design-temperature distribution. P61 then established that current emitter/hydraulic/electrical readiness is not an aggregate eligibility precondition. P62 added a current external Hungary-specific surface-heating presence band.

P63 asks whether the programme actually needs a separately observed baseline stock distribution of design supply/return temperature before post-retrofit COP and emitter decisions can be modelled.

The answer is no.

The programme needs baseline emitter/system composition for quantity and retrofit-scope weighting; post-retrofit room/building heat load; emitter identity/capacity or replacement design; hydraulic transition design; a derived post-retrofit design temperature; and population weighting of those transition outputs.

Canonical boundaries:

CURRENT DESIGN TEMPERATURE != POST-RETROFIT DESIGN TEMPERATURE

EMITTER CLASS != FIXED WATER TEMPERATURE

BASELINE NATIONAL DESIGN-TEMPERATURE DISTRIBUTION != REQUIRED PROGRAMME INPUT

POST-RETROFIT DESIGN TEMPERATURE = TRANSITION-DERIVED OUTPUT

## 2. Existing repository authority

### P26 — current-system temperature as record evidence

B02-P26 recovers one real HET-identified current radiator calculation: current state, radiator heat emission, 70/55 C calculation input, and explicit separation from a proposed 55/45 C modernization case.

P63 preserves this as useful calibration/validation evidence. It does not require a national distribution of current HET calculation pairs.

### B06-P65 — post-retrofit design point

P65 admits a post-retrofit numeric supply temperature only through room-by-room emitter design, signed post-retrofit MEP design, or measured post-retrofit design-point evidence.

For room-by-room design P65 requires post-state design heat load for every heated room; exact emitter identity/dimensions/quantity; source-native nominal output and correction method; explicit flow/return/room-temperature points; and hydraulic/design evidence. The common building supply temperature is the maximum room requirement.

The causal direction is therefore:

POST-RETROFIT LOAD + EMITTER ARRANGEMENT + HYDRAULICS -> REQUIRED DESIGN TEMPERATURE

not a national baseline temperature lookup.

## 3. External semantic authority — EHI 2021

Source: SRC-B02-EHI-EPBD-LOW-TEMP-EMITTERS-2021

Public authority:
https://ehi.eu/wp-content/uploads/2021/12/EHI_EPBD_position_paper_-_final_w_annex.pdf

EHI states that heating-water temperature is a building/heating-system design and operation feature rather than an inherent emitter product property. Design temperatures depend on building heat/cooling load and system design; operating temperature changes with load/heating curve and rarely equals the design temperature through the heating season.

P63 uses this as semantic/method authority only, not Hungarian population evidence.

Forbidden shortcuts:

RADIATOR -> 70/55 C

SURFACE HEATING -> EXACT 35/28 C

unless a record or explicit transition scenario supplies that design.

## 4. Field validation — Fraunhofer 2023

Source: SRC-B02-FRAUNHOFER-HP-TEMP-META-2023

DOI:
https://doi.org/10.1002/ente.202300379

The open-access field meta-analysis covers more than 50 residential heat-pump systems. A heating-curve subset contains floor heating n=9, radiators n=14, and mixed radiator + floor systems n=23.

Reported average mean heat-pump temperatures are 33.2 C for floor heating, 38.4 C for mixed systems and 38.9 C for radiators. These are field operating-temperature summaries, not design temperatures.

The more important result is structural: heating curves vary within emitter categories; mixed systems can behave close to floor-heating systems or be controlled by a radiator bottleneck; required temperature depends on heat demand and installed emitter area/capacity; bottleneck radiator replacement can lower required temperature.

Therefore:

MIXED SYSTEM != ONE FIXED TEMPERATURE

RADIATOR PRESENCE != HIGH-TEMPERATURE REQUIREMENT

The sample is not Hungarian and is not used as a prevalence weight.

## 5. Four temperature concepts

### A. Current-system calculation/design temperature

Example: P26 current HET 70/55 C.

Use: record-level current context, calibration, validation, optional admitted prior. Not mandatory as a complete national stock surface.

### B. Post-retrofit design temperature

Authority: P65.

Use: B06 -> B05 sizing handoff; KEEP/UPSIZE/CHANGE/ADD/REPLACE decision; design-point COP/capacity; hydraulic transition.

This is a derived transition output.

### C. Seasonal operating temperature

Use: seasonal COP/SPF model, commissioning/monitoring and heating-curve optimization.

It varies with outdoor temperature and load and is not equal to a design point.

### D. Technology-reference temperature

P62 examples: surface heating around 35/28 C; modern radiators typically 55 C or lower; traditional radiator context around 70–80 C.

Use: engineering scenario bounds, model validation and sensitivity. Not household truth, Hungarian population weights or automatic category assignment.

## 6. Population-model consequence

The national programme should not follow:

HOUSEHOLD STOCK -> ASSIGN OBSERVED DESIGN TEMPERATURE TO EVERY DWELLING -> TRANSITION

The correct chain is:

BASELINE ARCHETYPE + EMITTER POPULATION MODEL

-> POST-ENVELOPE ROOM/ARCHETYPE HEAT LOAD

-> CURRENT EMITTER CAPACITY / REPLACEMENT ACTION

-> HYDRAULIC TRANSITION DESIGN

-> POST-RETROFIT DESIGN SUPPLY/RETURN

-> B05 HEAT-PUMP PERFORMANCE

-> POPULATION-WEIGHTED COP / CAPEX / PROCUREMENT OUTPUT

For a national study, admitted archetype/calibrated transition models may replace individual records with explicit uncertainty. For a real dwelling, P65 record/project evidence remains mandatory.

## 7. Q-B02-004 residual after P63

P63 retires DESIGN_TEMPERATURE_DISTRIBUTION as a separately required baseline population evidence surface.

The remaining programme-population problem becomes:

1. KSH_DENOMINATOR_BRIDGE
2. MIXED_SYSTEM_OVERLAP
3. OTHER_EMITTER_SHARE
4. TRANSITION_MODEL_POPULATION_WEIGHTING

The fourth item means that after a P65-compatible transition model produces design-temperature/COP outcomes by archetype/path, those outputs must be weighted across the calibrated stock with explicit uncertainty.

Q-B02-004 therefore remains OPEN, but the external-data search space is materially smaller.

## 8. Heat-emitter archetype role repair

registry/archetype_dimensions.csv previously labelled heat emitter as eligibility_input with an unknown policy implying missing emitter evidence could block eligibility.

That is stale after P61/P65.

P63 changes the current role to archetype_key with programme meaning: retrofit quantity, CAPEX, procurement, transition-path weighting and COP distribution.

Missing population emitter classification remains Q/uncertainty for those programme outputs. It is not an automatic technical FAIL.

## 9. Historical gates remain historical

P9/P18/P26/P32/P40/P41 historical source packs remain unchanged.

The earlier TECHNICAL_READINESS_ARCHETYPE admission gate may still describe bounded current-state enrichment semantics for legacy/reuse paths. It may not reintroduce complete national current design-temperature coverage as a prerequisite for the current programme technical gate.

Current programme authority is governed by P61 plus P65/P57/P58.

## 10. Machine-readable contract

P63 adds registry/b02_p63_design_temperature_semantics.csv separating baseline emitter class, current-system design/calculation temperature, post-retrofit design temperature, realized operating temperature, water-temperature semantics and current Q-B02-004 residual.

Core current rule:

BASELINE_NATIONAL_DESIGN_TEMPERATURE_DISTRIBUTION_REQUIRED = NO

## 11. Non-claims

P63 does not claim that current 70/55 C systems are irrelevant; every radiator can operate at 55 C; every surface system operates at exactly 35/28 C; the Fraunhofer sample represents Hungary; field mean temperatures are design points; emitter prevalence is solved; mixed-system share is known for Hungary; Q-B02-004 is resolved; or B02 readiness should increase.

## 12. Next logical search

External searching should now focus on population composition rather than a national temperature lookup table.

Priority:

1. bound MIXED_SYSTEM_OVERLAP;
2. bound OTHER_EMITTER_SHARE;
3. resolve or safely bypass the EHI-to-KSH denominator mapping;
4. build a calibrated emitter-population envelope;
5. run P65-compatible transition scenarios across that envelope;
6. propagate temperature/COP/CAPEX distributions with uncertainty.

The programme objective remains: estimate what must actually be changed and what it will cost while preserving record-level engineering responsibility.
