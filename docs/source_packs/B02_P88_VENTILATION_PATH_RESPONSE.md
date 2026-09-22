# B02-P88 — POST-RETROFIT VENTILATION PATH & HRV RESPONSE

## Goal

Turn the remaining P87 ventilation-system unknown into an executable post-retrofit path contract without inventing national mechanical-ventilation prevalence, HRV prevalence, or a national mean heat-recovery efficiency.

Base: `8c6e0ab3605e8112dfcd093e8dce11924d7c7e1b`

## Authorities

### 1. Current Hungarian building-energy law

**9/2023. (V. 25.) EKM rendelet**, 1. melléklet 3.1.2.

Official source:
https://njt.hu/jogszabaly/2023-9-20-8X

The current rule separates two post-state ventilation mechanisms:

- ventilation solved through windows/openings;
- where ventilation is not solved by windows, a regulated central or decentral system must provide the required air exchange, using either exhaust ventilation or heat-recovery ventilation.

For exhaust ventilation, air-inlet elements are part of the system.

This is a design/path authority. It does **not** publish national post-retrofit prevalence.

### 2. Current Hungarian calculation method

**Epuletek energetikai jellemzoinek meghatarozasa — szamitasi modszer**

Canonical source:
`SRC-B06-HU-ENERGY-METHOD-2023`

P87 already established:

- residential required ventilation: `n_required = 0.5 1/h`;
- volumetric air heat capacity: `c_air = 0.35 Wh/m3K`;
- infiltration is a separate term;
- the official infiltration method domain contains `0.00 ... 1.00 1/h`.

### 3. Current Hungarian EKR heat-recovery method

**18/2025. (VII. 31.) EM rendelet**, section 2.8.

Canonical source:
`SRC-B06-HU-EKR-18-2025`

The simplified heat-recovery saving method applies:

`0.35 * V * c * n_required * (eta_new - eta_old)`

to the required ventilation flow.

Therefore P88 decomposes the P87 ventilation coefficient into:

`H_required_air = 0.35 * n_required * V`

`H_infiltration = 0.35 * n_infiltration * V`

and for an explicit HRV project state:

`H_vent,HRV = H_infiltration + (1 - eta) * H_required_air`

No heat-recovery credit is silently applied to infiltration.

### 4. Residential ventilation product eta

**Commission Regulation (EU) No 1253/2014**, Annex IV.

Official source:
https://eur-lex.europa.eu/eli/reg/2014/1253/oj/eng/pdf

For residential ventilation units the product information must include:

- heat-recovery-system type;
- thermal efficiency of heat recovery.

This makes `eta` an admissible **selected-product / procurement / project input**.

It does **not** make product-declared eta an observed national distribution or commissioned installed performance.

## Executable paths

P88 permits exactly:

1. `NATURAL_WINDOW`
2. `MECHANICAL_EXHAUST_WITH_AIR_INLETS`
3. `MECHANICAL_HEAT_RECOVERY`

For the first two paths, no heat recovery is credited.

For `MECHANICAL_HEAT_RECOVERY`, explicit `eta in [0,1]` is mandatory. Missing eta fails closed.

## 14-stratum physical response coefficients

The exact P87 heated-volume surface is reused.

For all 14 WBL-period x building-group strata:

`H_required_air = 0.35 * 0.5 * V`

Materialized global stratum edges:

- required-air coefficient: **25.431534722 ... 110.4705 W/K**
- full-eta recoverable required-air coefficient: **25.431534722 ... 110.4705 W/K**
- infiltration coefficient under the full P87 method-domain upper edge: **0 ... 220.941 W/K**

The first range is the thermal component to which HRV efficiency may apply.

The second component remains controlled by post-retrofit infiltration evidence/assumption.

## Blocker repair

P87 residuals:

- `POST_RETROFIT_AIRTIGHTNESS_CLASS_PREVALENCE_REQUIRED`
- `POST_RETROFIT_MECHANICAL_VENTILATION_PREVALENCE_REQUIRED`
- `POST_RETROFIT_HEAT_RECOVERY_EFFICIENCY_DISTRIBUTION_REQUIRED`
- `ACTION_TO_AIRTIGHTNESS_AND_VENTILATION_SYSTEM_MAPPING_REQUIRED`

P88 distinguishes evidence from programme state.

### Retired as population-evidence blockers

`POST_RETROFIT_MECHANICAL_VENTILATION_PREVALENCE_REQUIRED`

Post-retrofit ventilation path is a programme/project state. Scenario weights may be explicit, but they are not claimed as observed prevalence.

`POST_RETROFIT_HEAT_RECOVERY_EFFICIENCY_DISTRIBUTION_REQUIRED`

The engine needs eta only for a selected HRV path. Eta is bound by selected-product/procurement/project evidence.

### Partially resolved

`ACTION_TO_AIRTIGHTNESS_AND_VENTILATION_SYSTEM_MAPPING_REQUIRED`

The ventilation-system path contract is now executable.

What remains is not a missing national ventilation-system prevalence. It is the physical infiltration state.

### Current ventilation residual

`ACTION_CONDITIONED_POST_RETROFIT_INFILTRATION_REQUIRED`

A window/envelope action does not by itself prove the post-retrofit infiltration rate or airtightness class.

Acceptable future closure routes include:

- representative/calibrated action-conditioned inference;
- explicit programme airtightness target with defensible attainment evidence;
- record/project measurement or qualified design evidence.

## Boundaries

`POST-RETROFIT VENTILATION PATH != OBSERVED NATIONAL PREVALENCE`

`HRV EFFICIENCY != NATIONAL POPULATION DISTRIBUTION`

`PRODUCT-DECLARED ETA != INSTALLED/COMMISSIONED PERFORMANCE`

`WINDOW/ENVELOPE ACTION != PROVEN POST-RETROFIT INFILTRATION`

`MECHANICAL EXHAUST != HEAT RECOVERY`

`INFILTRATION BYPASSES HRV UNLESS SEPARATELY PROVEN`

`VENTILATION THERMAL LOAD != FAN ELECTRICITY`

## Readiness

- B02 remains **55%**
- B06 `PEAK_LOAD_EFFECT` remains **50%**
- `Q-B02-004` remains **OPEN_NARROWED**

No readiness percentage is increased solely because a residual was reclassified correctly. The ventilation thermal-response engine is more complete, but action-conditioned infiltration, transmission geometry, thermal bridges, full location mapping and other independent B06 inputs remain incomplete.
