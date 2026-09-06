# B02-P42 — radiator stock, reuse and retrofit-quantity contract

**State:** `METHOD CONTRACTED / NATIONAL RADIATOR STOCK AND RETROFIT QUANTITY Q`

**Canonical base:** `43f87b39bd035689de145e6a6eafdf09f9264094`

**Implementation date:** 2026-09-06

## 1. Purpose — programme intent first

P42 corrects a programme-level mistake that would otherwise be easy to make after P41:

> proving that a radiator-equipped dwelling can follow a heat-pump transition path is not the same as knowing how many radiator systems exist, what they are, how many units can remain, and how many units must be changed.

The B02 issue contract already defines the principal B02 output as:

`ARCHETYPES + HEAT DEMAND + HEAT-EMITTER SYSTEM + RETROFIT NEED`

The downstream B06 issue contract then requires the minimum retrofit package, retrofit CAPEX, reduced heat demand and modified COP profile.

Therefore the P42 objective is not to manufacture another PASS token. It is to make the radiator branch useful for the actual national programme.

Hard boundary:

`GATE PASS != PROGRAMME SUFFICIENCY`

## 2. Existing canonical evidence

### 2.1 P26 public certificate route

P26 proves one real current certificate route:

- HET record `HET-1008-3097`;
- current radiator heat emission;
- current calculation pair `70/55 C`;
- `DER` record evidence;
- no WBL direct join;
- no national completeness.

Source pack:

`docs/source_packs/B02_P26_PUBLIC_CERTIFICATE_DESIGN_TEMPERATURE_ROUTE.md`

This proves that current radiator and temperature data can exist at record level.

It does **not** prove the number or type distribution of radiators in the occupied stock.

### 2.2 FEANTSA / BME heat-transition analysis

Canonical existing source ID:

`SRC-B02-FEANTSA-CSOKNYAI-HEAT-TRANSITION-2024`

External source:

`https://www.feantsa.org/files/Themes/Energy/2024/heat-transition/Full.pdf`

Exact relevant locator for P42:

- PDF page 18 of 27 / printed pages 36–37;
- section `Difficulties with switching to air-to-water heat pumps`;
- the text distinguishes legacy radiator systems, high/medium design temperatures, building-shell retrofit and the possibility that an existing radiator system can remain after heat demand is reduced;
- PDF page 24 of 27 / printed page 47 concludes that high heat demand can require changing existing heat emitters.

P42 uses this only as engineering/transition evidence.

`FEANTSA TRANSITION LOGIC != NATIONAL RADIATOR INVENTORY`

No external PDF is committed to this repository.

### 2.3 B06 emitter-performance and inventory contract

Canonical downstream contract:

`modules/B06/data_contract.md`

B06 already requires an emitter record to preserve, where evidenced:

- manufacturer;
- model/type;
- dimensions;
- nominal output;
- nominal flow/return/room rating condition;
- nominal delta-T;
- temperature exponent `n`;
- correction method;
- explicit inventory quantity before emitter outputs may be summed.

Current bounded product evidence:

`data/processed/emitter_performance_evidence.csv`

contains one source-backed Purmo panel-radiator performance record. This is a replacement/sizing evidence fixture and is **not** Hungarian stock prevalence evidence.

Hard boundary:

`PRODUCT PERFORMANCE RECORD != EXISTING STOCK INVENTORY`

## 3. Required B02 radiator outputs

A useful national radiator result needs all of the following layers.

### R1 — radiator-heated dwelling count

For every claimed programme/archetype scope:

- represented dwellings;
- dwellings with current radiator heat emission;
- evidence/model status;
- uncertainty;
- source lineage.

Hard boundary:

`CENTRAL HEATING != RADIATOR`

and:

`BOILER TYPE != RADIATOR TYPE`

### R2 — installed radiator unit count

The programme must estimate the physical number of radiator units, not only the number of radiator-heated dwellings.

Hard boundary:

`RADIATOR DWELLINGS != RADIATOR UNITS`

This quantity later matters for:

- procurement volume;
- labour volume;
- valves and fittings;
- disposal/recycling;
- logistics;
- installation timing;
- CAPEX.

### R3 — type/configuration/size distribution

At minimum, the stock model must be able to represent the evidenced distribution across useful engineering classes such as:

- steel panel radiator, including configuration/type where evidenced;
- cast-iron sectional radiator;
- aluminium sectional radiator;
- bathroom/towel or other hydronic radiator;
- explicit `UNKNOWN`.

Where dimensions or section counts are available they must remain attached to the record or calibrated stock bin.

No manufacturer/model is invented for historical radiators when the source does not provide it.

### R4 — reuse versus upgrade requirement

For a current radiator, neither age nor a legacy boiler temperature decides whether the emitter stays.

The reusable/upgrade decision requires the post-envelope-retrofit design heat loss and the radiator output at the **proposed heat-pump target temperature**.

P42 therefore keeps the room-level physical gate in:

`modules/B02/archetype_admission_gate.py::assess_radiator_thermal_arrangement()`

The gate requires:

- admitted current radiator identity;
- complete heated-room coverage;
- room-specific design heat loss;
- radiator output at the proposed target flow/return pair;
- evidence for the chosen `REUSE_EXISTING_RADIATOR` or `UPGRADE_RADIATOR` action;
- B05 admission of the heat-pump target operating domain;
- no room-level capacity shortfall;
- reproducible binding.

A whole-dwelling sum cannot hide one undersized room.

Hard boundaries:

`CURRENT 70/55 C != REQUIRED FUTURE 70/55 C`

`RADIATOR PRESENT != RADIATOR REUSABLE`

`BUILDING-SHELL RETROFIT != EMITTER RETROFIT`

`ROOM HEAT LOSS AFTER RETROFIT -> EMITTER REQUIREMENT`

### R5 — replacement quantity handoff to B06

B02 must ultimately deliver enough information to report, by archetype/programme scope:

- existing radiator units;
- units reusable as-is;
- units requiring upsizing/replacement;
- additional units if required;
- required replacement emitter output bands / target-temperature context;
- uncertainty.

B06 then owns:

- exact replacement engineering/product selection;
- product-specific performance correction;
- hydraulic integration;
- installation package;
- CAPEX and downstream COP impact.

Hard boundary:

`B02 RETROFIT NEED != B06 PRODUCT SELECTION != B06 CAPEX`

## 4. Executable programme-sufficiency gate

`modules/B02/radiator_stock_requirement.py::assess_radiator_programme_stock()`

returns `QUALIFIED` only if the claimed stock scope has all of:

- represented dwelling count;
- radiator-heated dwelling count;
- installed radiator unit count;
- admitted stock authority;
- complete type/size distribution with admitted authority;
- complete reuse/upgrade classification with admitted authority;
- replacement-unit quantity with admitted authority;
- documented uncertainty;
- reproducible repository binding.

This gate intentionally accepts either direct or properly admitted modelled stock evidence at the evidence-status layer, but the corresponding authority fields must separately be `QUALIFIED`.

A sizing PASS for one dwelling does not satisfy this gate.

## 5. Current P42 evidence state

The public/current repository evidence does **not** yet provide a complete Hungarian radiator inventory.

Therefore the P42 stock registry remains `Q` for:

- `RADIATOR_STOCK_DWELLING_COUNT`;
- `RADIATOR_STOCK_UNIT_COUNT`;
- `RADIATOR_TYPE_SIZE_DISTRIBUTION`;
- `RADIATOR_REUSE_UPGRADE_REQUIREMENT`;
- `RADIATOR_REPLACEMENT_QUANTITY`.

The current blockers are correspondingly:

- `NO_NATIONAL_RADIATOR_DWELLING_COUNT`;
- `NO_NATIONAL_RADIATOR_UNIT_COUNT`;
- `NO_NATIONAL_RADIATOR_TYPE_SIZE_DISTRIBUTION`;
- `NO_STOCK_LEVEL_RADIATOR_REUSE_UPGRADE_CLASSIFICATION`;
- `NO_REPLACEMENT_RADIATOR_QUANTITY`.

No national radiator count is inferred from central heating, gas boiler prevalence, district heating, FEANTSA heating-generator charts, P26's single certificate or the B06 Purmo product record.

## 6. Relationship to aggregate technical-readiness blockers

P42 changes the *required programme output*, not the current national evidence state.

The aggregate P9 row therefore remains:

`TECHNICAL_READINESS_ARCHETYPE = Q`

with:

- `NO_CURRENT_HEAT_EMITTER_EVIDENCE`;
- `NO_CURRENT_DESIGN_TEMPERATURE_EVIDENCE`.

B02 readiness remains `55%`.

This is deliberate. P42 prevents the project from closing B02 merely by finding a semantic route around those blockers while losing the physical inventory and retrofit quantities required by the programme.

## 7. Next evidence target

The next radiator blocker-killer must target **stock characterization**, not another eligibility exception.

Priority evidence order:

1. BME current residential building-stock model: whether its EPC/system input layer contains current radiator/emitter class, dimensions or stock distributions;
2. OÉNY/ÉKM current certificate population: whether anonymised/aggregate emitter classes and any useful dimensional/output fields can be supplied;
3. REKK/TÁRKI or linked research microdata: whether the survey contains radiator/central-emitter details beyond the public heating-device categories;
4. only if those fail, calibrated stock reconstruction using independent public controls, with explicit uncertainty and no promotion to OBS/DER.

The desired result is not merely:

`RADIATOR PATH = PASS`

It is:

`HOW MANY + WHAT TYPE + KEEP/CHANGE + HOW MANY NEW UNITS -> B06`
