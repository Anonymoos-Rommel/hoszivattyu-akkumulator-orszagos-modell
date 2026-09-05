# B02-P3 — Eligibility layer harmonization

## Purpose

B02-P3 removes the remaining semantic ambiguity between the physical dwelling universe, B02 technical eligibility, V1.2 S2 transition readiness and later legal/economic programme eligibility.

Canonical boundary:

`PHYSICAL SCREENING != TECHNICAL ELIGIBILITY != S2 READINESS != LEGAL ELIGIBILITY != ECONOMIC ELIGIBILITY != FINAL PROGRAMME ELIGIBILITY`

This slice does not create a new national eligible-dwelling count and does not close any missing technical evidence.

## Why this slice is required

The historical global variable `VAR-B02-ELIGIBLE-DWELLINGS` has broad wording combining legal, technical and economic conditions. B02-P2 deliberately did not silently redefine that variable because doing so would change an existing public contract without an explicit compatibility decision.

B02-P3 therefore makes the layer split machine-readable in `registry/b02_eligibility_layer_contract.csv`.

The historical variable remains blank and `Q`. It is classified only as:

`DEPRECATED_UMBRELLA_ONLY`

It is not the canonical B02 technical output and must not be used to populate any eligibility layer.

## Layer contract

### 1. Physical screening scope

Current exact 2022 reference:

- occupied dwellings: 4,008,541;
- district-heated occupied dwellings: 618,724;
- non-district-heated occupied dwellings: **3,389,817**;
- status: `DER_FROM_OBS_WBL011_CELLS`.

Canonical source:

`registry/b01_non_district_heated_population_2022.csv`

This is a physical population reference only.

### 2. Technical eligibility

Owner: B02.

Canonical output:

`registry/b02_technical_eligibility_gate.csv:technical_eligible_dwellings`

A real record can pass only when the B02-P2 gate has explicit evidence for:

- physical scope;
- thermal distribution / emitter-temperature compatibility;
- hydraulic readiness;
- electrical readiness;
- permit readiness.

Missing evidence remains `Q`. A real PASS or FAIL requires `OBS`/`DER` evidence.

Current national technical eligible count: **blank / Q**.

### 3. S2 transition readiness

Technical eligibility is necessary but not sufficient for `S2 TECHNICALLY_READY`.

The V1.2 state machine also requires the S1 predecessor gate:

`demand_reduction_measured_or_not_required`

Therefore:

`TECHNICALLY_ELIGIBLE != S2_TRANSITION_READY`

Current result: `S2_Q`.

### 4. Legal programme eligibility

B02 does not decide programme-law eligibility. A legal programme rule and claim-specific legal evidence are required at the appropriate household/archetype/phase grain.

Technical readiness, census membership, tariff availability or an OÉNY certificate cannot be promoted into legal programme eligibility.

Current result: **blank / Q**.

### 5. Economic eligibility

Owner: B12 economic layer.

Affordability, eligible CAPEX, financing capacity, support need and household cash-flow constraints are not technical properties.

Technical readiness and physical scope cannot prove economic eligibility.

Current result: **blank / Q**.

### 6. Final programme eligibility

Final programme eligibility is an orchestration decision, not a B02 output. It requires explicit satisfaction of the applicable physical, technical, legal, economic and policy-scope gates.

No single upstream count may be relabelled as the final eligible stock.

Current result: **blank / Q**.

## Legacy compatibility

`VAR-B02-ELIGIBLE-DWELLINGS` remains in `registry/variables.csv` to avoid silently breaking historical references. Its broad wording is interpreted only as a legacy umbrella. It must remain numerically blank and `Q` until a future explicit migration can remove or replace it without downstream ambiguity.

New code must use claim-specific canonical outputs instead:

- physical population: B01-P3 population registry;
- technical eligibility: B02-P2 technical eligibility registry;
- S2 readiness: B02-P2 S2 transition field;
- legal/economic/final eligibility: future claim-specific materializations.

## Fail-closed rules

- missing != zero;
- `Q` != `FAIL`;
- physical population != eligible population;
- technical PASS != legal PASS;
- technical PASS != economic PASS;
- technical PASS != S2 unless the S1 predecessor is satisfied;
- a legacy umbrella field is never authority for a narrower claim;
- final programme eligibility cannot be inferred from a single layer.

## Current questions

B02-P3 does not close:

- `Q-B02-001` — national technically suitable stock;
- `Q-B02-004` — national emitter/design-temperature evidence;
- `Q-B01-001` — final programme-target household definition.

B02 readiness remains 55%. This is semantic harmonization, not new national evidence.
