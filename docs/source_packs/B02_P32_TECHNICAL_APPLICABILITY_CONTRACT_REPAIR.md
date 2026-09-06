# B02-P32 — technical applicability contract repair

**State:** `INTERNAL CONTRACT REPAIR / ZERO EVIDENCE BLOCKER CLOSURES`

**Base:** `77a21bf2d82c4f7e99a75655ba1db0f8799c4e23`

## 1. Purpose

P31 did not identify a new evidence result. It identified three internal contract defects that had to be repaired before later evidence or model closure could be evaluated safely:

1. the canonical OÉNY emitter taxonomy could not encode `GAS_CONVECTOR` explicitly;
2. the temperature contract could not distinguish structurally non-applicable hydronic temperatures from unknown or missing values;
3. the P9 technical-readiness gate required design-temperature evidence unconditionally.

P32 repairs only those semantics.

`P32 closes zero evidence blockers`

`P32 does not validate the P30 emitter linkage`

`P32 does not create current stock emitter evidence`

`P32 does not create current stock design-temperature evidence`

B02 readiness remains `55%`.

## 2. Emitter taxonomy repair

Both current OÉNY schemas now include:

`GAS_CONVECTOR`

as an explicit `emitter_types` value.

This preserves the P25/P30 category without collapsing it into `OTHER`.

Hard boundary:

`EXPLICIT GAS CONVECTOR != GENERIC OTHER`

The enum addition is representation capability only. It is not evidence that any OÉNY record, WBL cell or national stock row contains a gas convector.

## 3. Temperature applicability repair

Both current OÉNY schemas now include:

`temperature_status = NOT_APPLICABLE`

and:

`temperature_basis = NOT_APPLICABLE`

For that state the contract requires:

- `supply_temperature_c = null`;
- `return_temperature_c = null`;
- `temperature_basis = NOT_APPLICABLE`.

The validator enforces the same rule.

Hard boundaries:

`NOT_APPLICABLE != Q`

`NOT_APPLICABLE != MISSING`

`NOT_APPLICABLE != ZERO`

`NOT_APPLICABLE != REFERENCE_ASSUMPTION`

A numeric hydronic pair cannot coexist with a `NOT_APPLICABLE` state.

## 4. P9 applicability gate repair

`assess_technical_readiness_enrichment()` now distinguishes:

### 4.1 APPLICABLE

For an applicable/hydronic current system, the previous P18 rule remains unchanged:

- `design_temperature_status` must be real evidence (`OBS` or `DER`);
- `design_temperature_direct_authority_status` must be `QUALIFIED`.

Otherwise the existing design-temperature blockers remain.

### 4.2 NOT_APPLICABLE

For a non-hydronic current system, a hydronic supply/return pair is not required **only if**:

- `design_temperature_applicability = NOT_APPLICABLE`;
- `design_temperature_applicability_authority_status = QUALIFIED`;
- `design_temperature_status = NOT_APPLICABLE`.

The status string therefore cannot self-authorize its own exception.

Hard boundary:

`NON-HYDRONIC APPLICABILITY STATUS != APPLICABILITY AUTHORITY`

If applicability is not separately admitted, the gate returns:

`DESIGN_TEMPERATURE_APPLICABILITY_NOT_ADMITTED`

If an alleged non-hydronic system supplies an `OBS`/`DER` hydronic temperature status instead of `NOT_APPLICABLE`, the gate returns:

`NON_HYDRONIC_TEMPERATURE_STATUS_NOT_NOT_APPLICABLE`

If applicability itself is unknown/unsupported, the gate returns:

`DESIGN_TEMPERATURE_APPLICABILITY_UNKNOWN`

## 5. No automatic emitter-to-applicability promotion

P32 deliberately does not add a rule such as:

`GAS_CONVECTOR -> automatically QUALIFIED NOT_APPLICABLE`

The taxonomy and the gate are now capable of expressing the correct state, but a stock-level applicability claim still needs its own admitted authority.

This prevents a representation fix from becoming an evidence shortcut.

## 6. Historical P1K/P31 preservation

The already-sent P1K/OÉNY request and P31 gap audit are historical records and are not rewritten retroactively.

P31 remains true as an audit of the repository state at its own base commit. Its tests now verify that the P31 audit register recorded the three internal gaps rather than incorrectly requiring those defects to remain forever in the current schemas/code.

Current P32 amendments are machine-readable in:

`registry/b02_p32_internal_contract_repairs.csv`

## 7. Current evidence state remains unchanged

P32 changes no evidence admission row for the P30 calibrated gas-convector linkage.

Therefore these remain open:

- `NO_VALIDATION_METRICS`;
- `UNCONTROLLED_INDEPENDENCE_ASSUMPTION`;
- `NO_JOSEPH_APPROVAL`.

Technical readiness also remains:

`TECHNICAL_READINESS_ARCHETYPE = Q`

with the current stock-level blockers still recorded as:

- `NO_CURRENT_HEAT_EMITTER_EVIDENCE`;
- `NO_CURRENT_DESIGN_TEMPERATURE_EVIDENCE`.

The second label remains the current aggregate stock blocker because no complete applicability partition plus hydronic design-temperature authority has yet been admitted. P32 merely prevents non-hydronic records from being semantically misclassified as missing hydronic temperatures once such authority exists.

## 8. What P32 does not prove

P32 does not prove:

- how many dwellings are non-hydronic;
- how many gas-convector dwellings exist in any WBL cell;
- that P30 probabilities are valid;
- any design-temperature distribution for radiator/floor/wall/ceiling/fan-coil systems;
- any national OÉNY emitter or temperature distribution;
- any heat-pump readiness rate.

`CONTRACT REPAIR != EVIDENCE`

`ENCODABLE STATE != OBSERVED STATE`

`NOT_APPLICABLE PATH != NATIONAL NON-HYDRONIC SHARE`

## 9. Next evidence order

After P32 the correct order remains evidence-first:

1. obtain genuinely independent/current emitter evidence or detailed REKK/TÁRKI microdata;
2. obtain or build a defensible applicability partition where needed;
3. obtain representative/complete current design/calculation pairs for the applicable hydronic subset;
4. evaluate validation metrics against evidence not used as the calibration target;
5. control the remaining independence assumption;
6. propagate design-aware uncertainty when the necessary survey-design inputs exist;
7. only then request Joseph approval and evaluate closure.

No readiness or evidence blocker should be closed merely because P32 makes the contract logically correct.
