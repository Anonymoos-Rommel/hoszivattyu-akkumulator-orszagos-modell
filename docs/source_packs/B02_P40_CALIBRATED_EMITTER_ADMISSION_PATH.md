# B02-P40 — calibrated heat-emitter admission path repair

**State:** `INTERNAL ADMISSION CONTRACT REPAIR / ZERO EVIDENCE BLOCKER CLOSURES`

**Base:** `954d12e0d70fe3c460b4b7f9810d36b92cf4ea8d`

**Audit / implementation date:** 2026-09-06

## 1. Purpose

P39 qualified the P38 calibrated gas-convector linkage under the generic P12 calibrated-linkage governance contract:

`APPROVED / JOSEPH / QUALIFIED`

Its output evidence remains `ASS`.

That exposed one remaining architecture asymmetry in P9. Building-type and primary-energy stock linkage can be consumed through either direct authority or an independently admitted calibrated/modelled path, while heat-emitter readiness still accepted only direct `OBS`/`DER` authority under P18.

P40 repairs that asymmetry without weakening the evidence boundary.

Hard boundaries:

`P12 MODEL ADMISSION != COMPLETE HEAT-EMITTER STOCK AUTHORITY`

`ONE-EMITTER MARGINAL != COMPLETE EMITTER ASSIGNMENT`

`CALIBRATED ASSIGNMENT != DIRECT OBSERVATION`

`P40 CLOSES ZERO EVIDENCE BLOCKERS`

## 2. Direct P18 path remains unchanged

P18 direct heat-emitter authority remains valid and unchanged.

A direct path still requires explicit current `OBS`/`DER` emitter evidence at `WBL_FULL_JOINT` or reproducibly joinable `DWELLING_RECORD` grain, complete occupied-stock assignment, a WBL-compatible key and reproducible repository binding.

P40 does not reinterpret `ASS` or `MODELLED` output as direct evidence and does not weaken any P18 condition.

## 3. New calibrated heat-emitter authority wrapper

P40 adds:

`modules/B02/archetype_admission_gate.py::assess_calibrated_heat_emitter_authority`

The wrapper is deliberately separate from generic P12 model admission.

A calibrated heat-emitter output may become current-stock heat-emitter authority only if all of the following hold:

1. the underlying calibrated model is already `QUALIFIED` under P12;
2. output evidence remains `ASS` or `MODELLED`;
3. the target universe is exactly `OCCUPIED_DWELLING_STOCK`;
4. the output grain is `WBL_FULL_JOINT` or reproducibly joinable `DWELLING_RECORD`;
5. the model explicitly targets the **current** emitter state, not a proposed modernization;
6. the assignment is complete for the claimed occupied-stock universe;
7. a WBL-compatible join key exists; and
8. the repository binding is reproducible.

Missing any one condition returns `Q`.

For a categorical/probabilistic emitter model, `complete assignment` means an exhaustive current-emitter assignment over the claimed stock universe. A probability or count for only one emitter class is not complete merely because it is evaluated over every WBL row.

## 4. P39 is intentionally insufficient for P40 authority

The current P39 row proves that the exact P38 gas-convector model has passed the P12 model-quality and governance gates.

It does **not** provide an exhaustive assignment across radiator, surface heating, fan-coil, gas convector, direct electric, stove/fireplace and other current emitter states.

Therefore the current P39 model must be evaluated as:

- `model_admission_status = QUALIFIED`;
- `output_evidence_status = ASS`;
- `publishes_complete_assignment = false`.

The calibrated-emitter authority wrapper consequently returns:

`Q / NO_COMPLETE_HEAT_EMITTER_ASSIGNMENT`

Thus P39 model approval remains real and useful without falsely closing technical readiness.

## 5. P9 technical-readiness integration

After P40 the heat-emitter branch accepts two explicit routes:

### 5.1 Direct route

`heat_emitter_status = OBS | DER`

requires:

`heat_emitter_direct_authority_status = QUALIFIED`

Otherwise:

`HEAT_EMITTER_DIRECT_EVIDENCE_NOT_ADMITTED`

### 5.2 Calibrated route

`heat_emitter_status = APPROVED_CALIBRATED_MODEL`

requires:

`heat_emitter_calibrated_authority_status = QUALIFIED`

Otherwise:

`CALIBRATED_HEAT_EMITTER_MODEL_NOT_ADMITTED`

The status token cannot self-authorize the calibrated path. Generic P12 approval alone cannot bypass the P40 complete-stock authority wrapper.

## 6. Design-temperature semantics are unchanged

P40 changes only heat-emitter admission symmetry.

P32 temperature applicability remains canonical:

- hydronic/applicable systems require separately admitted current design/calculation temperatures;
- non-hydronic systems may use `NOT_APPLICABLE` only with separately qualified applicability authority.

No emitter model may manufacture a design-temperature pair.

## 7. Current state after P40

P40 creates no new external evidence and no current full-stock emitter assignment.

Therefore current state remains:

- `CALIBRATED_GAS_CONVECTOR_EMITTER_LINKAGE_P39 = APPROVED / JOSEPH / QUALIFIED`;
- P39 output evidence = `ASS`;
- `TECHNICAL_READINESS_ARCHETYPE = Q`;
- blockers remain exactly:
  - `NO_CURRENT_HEAT_EMITTER_EVIDENCE`;
  - `NO_CURRENT_DESIGN_TEMPERATURE_EVIDENCE`;
- B02 readiness remains `55%`.

No current evidence row is promoted from `ASS`/`MODELLED` to `OBS`/`DER`.

## 8. Effect on the next evidence search

P40 changes the *kind* of blocker-killer that is admissible, not the current evidence state.

A future closure no longer requires direct observation of every occupied dwelling if a complete current-stock emitter assignment can instead be built as an approved calibrated model. That model must still satisfy P12 governance plus the P40 exhaustive-assignment and reproducible-binding gate.

This permits a defensible combination of current survey, record-level emitter evidence and independent stock-model controls without converting any component into fake direct observation.

The next evidence task is therefore to obtain enough independent current emitter structure to construct and validate an exhaustive WBL-bound emitter model, not merely another national marginal for one emitter class.
