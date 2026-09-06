# B02-P31 — negative-space technical gap audit

**State:** `AUDIT COMPLETE / ZERO BLOCKER CLOSURES / INTERNAL CONTRACT GAPS IDENTIFIED`

**Base:** `1a29594e0acb3f71e99144b4c5a4e7fff2371087`

**Audit date:** 2026-09-06

## 1. Purpose

P30 left the calibrated gas-convector emitter linkage at `ASS / Q` with three blockers:

1. `NO_JOSEPH_APPROVAL`;
2. `NO_VALIDATION_METRICS`;
3. `UNCONTROLLED_INDEPENDENCE_ASSUMPTION`.

The next step is deliberately **not** to close either technical blocker.

P31 follows an exclusion-first / missing-evidence-first strategy:

1. identify what the current evidence cannot prove;
2. identify candidate routes that are structurally impossible or semantically invalid;
3. identify internal contract gaps that would prevent correct ingestion or readiness logic even if new external data arrived;
4. only after those gaps are resolved should validation, independence control and approval be reconsidered.

**P31 closes zero blockers.**

It creates no readiness uplift and does not materialize any emitter or design-temperature stock assignment.

Canonical boundary:

`GAP AUDIT != BLOCKER CLOSURE`

`NEGATIVE EVIDENCE != MISSING AS ZERO`

`CONTRACT GAP != EXTERNAL DATA GAP`

## 2. Current canonical state preserved

P31 does not modify `registry/b02_calibrated_linkage_admission.csv`.

The P30 successor therefore remains:

- claim: `CALIBRATED_GAS_CONVECTOR_EMITTER_LINKAGE_P30`;
- model: `B02-P30-PRIMARY-CONVECTOR-STRUCTURAL-PRIOR-LINKAGE-CANDIDATE`;
- output: `ASS`;
- status: `Q`;
- blockers:
  - `NO_JOSEPH_APPROVAL`;
  - `NO_VALIDATION_METRICS`;
  - `UNCONTROLLED_INDEPENDENCE_ASSUMPTION`.

The technical-readiness blockers also remain unchanged:

- `NO_CURRENT_HEAT_EMITTER_EVIDENCE`;
- `NO_CURRENT_DESIGN_TEMPERATURE_EVIDENCE`.

B02 readiness remains `55%`.

## 3. Validation: what is missing and what is excluded

### 3.1 The 23.3% control cannot validate the model it calibrates

P30 exactly calibrates the model family to the published `23.3%` full-sample primary-heating gas-convector share.

Therefore agreement with `23.3%` is a calibration identity, not an out-of-sample or independent validation result.

`CALIBRATION TARGET REPRODUCTION != VALIDATION`

A validation metric requires information not already consumed as the fitted national margin.

### 3.2 FEANTSA Figure 6 is useful context but not independent validation

The FEANTSA/Csoknyai report publishes primary-heating system types by 14 building types in Figure 6 and states that gas convectors occur in both single-family and multi-family buildings.

However:

- Figure 6 cites source `[29]`, the same REKK/TÁRKI 2022 survey used by the P25/P30 evidence chain;
- the report explicitly cautions that the representativity of the 2022 building-type survey view is questionable and discusses likely post-2015 over-representation;
- no source-native numeric Figure 6 cross-tab has been acquired into the repository.

Therefore Figure 6 cannot honestly serve as an **independent** held-out validation dataset for P30.

It may later support same-source structural diagnostics if exact values and survey design are obtained, but:

`SAME-SURVEY DESCRIPTIVE CROSS-TAB != INDEPENDENT VALIDATION`

### 3.3 Published gas-heating diagnostics are not gas-convector diagnostics

P28 already pins construction-period and settlement-type distributions for gas-heating households.

Those distributions condition on gas-heating status, not gas-convector use.

Therefore they cannot validate the P30 gas-convector allocation shape.

`GAS-HEATING MARGINS != GAS-CONVECTOR MARGINS`

The KSH 2022 heating-mode definition independently reinforces the same boundary: source-native room heating groups convector, stove and other room devices together and also includes dwellings with no heating equipment. Heating mode is not a current emitter label.

### 3.4 The detailed REKK/TÁRKI database is the shortest missing-data route

P28 records that the detailed survey database can be made available on request for scientific publication or policy analysis.

The repository does not currently contain that microdata.

If lawfully obtained with the necessary design metadata, it could potentially provide:

- gas-convector conditional cross-tabs;
- current emitter-specific building-type / construction-period / settlement diagnostics;
- final survey weights;
- stratum/PSU or replicate-weight inputs required by the P29 design-aware uncertainty method;
- a direct test of whether P30's structural shape is supportable.

Until acquisition occurs, this is a **missing external dataset**, not a closed validation route.

## 4. Falsified emitter-domain shortcut remains excluded

P30 already proved:

- exact WBL gas-bearing dwellings: `2,496,034`;
- exact `NHEAT + gas` dwellings: `693,075`;
- `40.61%` of the WBL gas-bearing universe implies `1,013,639.4074` expected convector dwellings;
- a hard `NHEAT + gas` support restriction would require probability `1.46252484565`.

Therefore:

`NHEAT + GAS AS HARD GAS-CONVECTOR DOMAIN = FALSIFIED`

P31 preserves that negative result. It must not be reintroduced as a convenience constraint in a later closure slice.

## 5. OÉNY: public access and pilot routes do not yet close stock evidence

### 5.1 Public machine access

P1-M found that the official public e-tanúsítás UI exposes a machine-readable browser search path, but not a documented public bulk API or P1K-compatible readiness feed.

Its 22-field mapping found:

- `0` fully available P1K fields;
- `1` partial field;
- `20` not publicly available fields;
- `1` uncertain field.

Particularly unproven as public bulk fields are:

- current emitter;
- emitter evidence;
- supply/return temperature;
- temperature basis.

Therefore:

`PUBLIC UI != PUBLIC BULK READINESS AUTHORITY`

### 5.2 Existing pilot request is still pending

P19 proves that the anonymized OÉNY pilot request was sent on `2026-08-22 10:31:17 Europe/Budapest` and remains `REQUEST_SENT / AWAITING_RESPONSE` in the repository.

That request includes source-native emitter and supply/return temperature fields if they exist structurally.

The dispatch fact does not prove response, field existence, data release or representativeness.

### 5.3 Even a successful pilot is not national evidence

P1-K explicitly prohibits turning a successful pilot into a national emitter or design-temperature distribution unless the sampling frame, stratification, selection probability and weighting are separately established.

Therefore:

`OENY PILOT RECORDS != NATIONAL STOCK AUTHORITY`

The pilot may prove field availability, extraction feasibility and record-level evidence. It does not automatically close the P18 direct-authority boundary.

## 6. Internal contract gap #1 — gas convector cannot be represented explicitly

This is a newly identified internal inconsistency.

P25/P30 now use `GAS_CONVECTOR` as an explicit current emitter/device category.

However both canonical OÉNY schemas currently restrict `emitter_types` to:

- `RADIATOR`;
- `FLOOR_HEATING`;
- `WALL_HEATING`;
- `CEILING_HEATING`;
- `FAN_COIL`;
- `AIR_HEATING`;
- `DIRECT_ELECTRIC`;
- `OTHER`;
- `NOT_STATED`;
- `UNREADABLE`.

Affected schemas:

- `schemas/oeny_readiness_pilot.schema.json`;
- `schemas/oeny_heat_emitter_annotation.schema.json`.

`GAS_CONVECTOR` is absent.

Mapping an explicit gas convector to `OTHER` would destroy the exact category used by the current calibrated-linkage chain.

Therefore:

`EXPLICIT GAS CONVECTOR != GENERIC OTHER`

Before any future OÉNY record/pilot is used to validate or bind the P30 emitter model, the canonical emitter taxonomy must be deliberately reviewed and, if approved, extended.

P31 records this gap but does not change the schemas.

## 7. Internal contract gap #2 — non-hydronic temperature applicability is not representable

The canonical OÉNY schemas currently allow temperature states such as `OBS`, `Q` and, in the pilot schema, `NOT_IN_SOURCE`.

They do **not** provide an explicit `NOT_APPLICABLE` state.

That distinction matters.

A gas convector is not an existing hydronic emitter circuit with a current supply/return water-temperature pair. For such a current system, a hydronic design pair may be structurally inapplicable rather than merely unknown.

Canonical boundary:

`UNKNOWN TEMPERATURE != NON-HYDRONIC NOT-APPLICABLE TEMPERATURE`

Without an explicit applicability state, later ingestion risks conflating:

1. a hydronic system whose design pair is missing;
2. a non-hydronic system for which the current hydronic pair does not exist.

P31 records this as an internal contract gap. It does not yet choose the replacement enum or migration design.

## 8. Internal contract gap #3 — P9 currently requires design-temperature evidence globally

`modules/B02/archetype_admission_gate.py` currently evaluates technical readiness in two unconditional steps after stock admission:

1. require current heat-emitter evidence and direct authority;
2. require current design-temperature evidence and direct authority.

There is no emitter-dependent hydronic-applicability branch.

Therefore a future explicitly proven non-hydronic current emitter would still receive:

`NO_CURRENT_DESIGN_TEMPERATURE_EVIDENCE`

unless a design-temperature pair were supplied.

For a gas convector that would be semantically wrong: inventing a hydronic supply/return pair is forbidden, while leaving it `Q` treats structural non-applicability as missing evidence.

This is not a reason to close the design-temperature blocker now. It is a reason to refine the contract **before** closure is attempted.

Required future distinction:

`HYDRONIC CURRENT SYSTEM -> DESIGN/CALCULATION PAIR REQUIRED`

`NON-HYDRONIC CURRENT SYSTEM -> HYDRONIC PAIR NOT APPLICABLE`

The exact implementation and taxonomy are deferred to a later explicit contract-correction slice.

## 9. Design-temperature evidence remains genuinely missing for the applicable stock

P26 proves one public current HET record with:

- radiator heat emission;
- `70/55 C` hydronic calculation input;
- record-level DER / `CALCULATION_INPUT` semantics.

That proves the route exists.

It does not prove a national radiator default or a stock-level design-temperature distribution.

`RADIATOR RECORD 70/55 C != NATIONAL RADIATOR DEFAULT`

Likewise:

- boiler type does not prove emitter type;
- emitter type does not prove design temperature;
- reference temperatures do not prove current building design values;
- operating measurements do not satisfy the narrower P18 design-authority gate unless the contract is explicitly changed.

After the applicability correction, representative or complete design/calculation pairs would still be required for the hydronic subset if technical readiness needs that current-system characteristic.

## 10. P31 machine-readable audit

The complete negative-space register is:

`registry/b02_p31_remaining_technical_gap_audit.csv`

It separates:

- `MISSING_EVIDENCE`;
- `MISSING_EXTERNAL_DATA`;
- `PENDING_EXTERNAL_RESPONSE`;
- `FALSIFIED_DOMAIN`;
- `EXCLUDED_AS_*` evidence routes;
- `PROHIBITED_INFERENCE`;
- `INTERNAL_TAXONOMY_GAP`;
- `INTERNAL_APPLICABILITY_GAP`;
- `INTERNAL_GATE_SEMANTIC_GAP`.

No row has `closure_effect` other than `NONE`.

## 11. Correct work order after P31

P31 changes the recommended order of work.

### Phase A — repair internal semantics before consuming new evidence

1. review the canonical emitter taxonomy and the `GAS_CONVECTOR` representation gap;
2. define an explicit non-hydronic temperature applicability state;
3. make P9 design-temperature requirements conditional on the current-system applicability contract;
4. preserve the rule that non-applicable is not zero, not unknown and not an invented temperature.

### Phase B — acquire missing evidence

5. pursue the detailed REKK/TÁRKI microdata route for emitter-conditional structure, validation and design-aware uncertainty;
6. continue to await/process the already-sent OÉNY pilot request without treating it as national evidence;
7. seek additional independent current emitter/design-temperature sources only if they can supply genuinely different evidence rather than restating the same survey.

### Phase C — only then evaluate closures

8. compute validation metrics against evidence not consumed as the calibration target;
9. test and control remaining conditional-independence assumptions;
10. propagate uncertainty using the P29 method when survey-design inputs exist;
11. only after all substantive gates are satisfied request Joseph approval;
12. only after model admission and the technical applicability contract are coherent reconsider readiness closure.

This order deliberately prevents checkbox closure ahead of evidence.

## 12. Final P31 effect

P31 is an audit slice only.

It does **not** change:

- `validation_metrics = no`;
- `independence_assumption_controlled = no`;
- `approval_status = NOT_APPROVED`;
- P30 output evidence `ASS`;
- P30 status `Q`;
- technical-readiness status `Q`;
- `NO_CURRENT_HEAT_EMITTER_EVIDENCE`;
- `NO_CURRENT_DESIGN_TEMPERATURE_EVIDENCE`;
- B02 readiness `55%`.

The main new result is not a closure but a stricter statement of what must be fixed or obtained before closure is legitimate.
