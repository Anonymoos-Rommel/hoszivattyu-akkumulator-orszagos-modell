# B02-P2 — Technical eligibility admission gate

## Purpose

B02-P2 turns the existing B02 readiness evidence rules into an executable,
fail-closed technical-eligibility boundary. It does **not** manufacture a
national eligible-dwelling count.

Core separation:

`PHYSICAL SCREENING SCOPE != TECHNICAL ELIGIBILITY != S2 TRANSITION READINESS != LEGAL/ECONOMIC PROGRAMME ELIGIBILITY`

This distinction is necessary because B01-P3 now provides an exact physical
starting population, while the B02 evidence gap matrix still contains unresolved
S2 fields.

## Physical screening reference

The current physical reference comes from B01-P3:

- occupied dwellings: **4,008,541**;
- district-heated occupied dwellings: **618,724**;
- non-district-heated occupied dwellings: **3,389,817**;
- status: `DER_FROM_OBS_WBL011_CELLS`.

The **3,389,817** figure is therefore a physical screening reference only. It is
not a technical-eligibility count, programme target, legal eligibility count or
selected-household count.

## Technical gate

A real record may become `ELIGIBLE` only if it is explicitly admitted to the
physical screening scope and all four technical components pass:

1. `THERMAL_DISTRIBUTION` — claim-specific evidence that the existing or
   explicitly required emitter/temperature arrangement satisfies the approved
   technical criterion;
2. `HYDRAULIC` — topology, controllability and capacity readiness;
3. `ELECTRICAL` — connection, metering and required electrical readiness at the
   relevant building/region grain;
4. `PERMIT` — the required technical/legal implementation prerequisite at the
   building/phase grain.

The gate intentionally consumes **component decisions**, not inferred raw
proxies. A heating fuel, WBL heating mode, building-type proxy, coarse OÉNY
heating-system quality or existing heat-pump flag does not automatically satisfy
any component.

### Evidence rules

- `PASS` requires explicit `OBS` or `DER` evidence and at least one evidence
  reference;
- `FAIL` also requires explicit `OBS` or `DER` evidence and at least one evidence
  reference;
- missing or unproven evidence is `Q`, never `FAIL` and never zero;
- `ASS`, `SCN` and `POL` cannot prove a real technical pass/fail;
- an explicit technical `FAIL` is enough to return `BLOCKED`; unknown unrelated
  components do not erase a proven blocker;
- if no blocker is proven but one or more required components remain unknown,
  the result is `Q`;
- `ELIGIBLE` requires all four components to pass.

`OUT_OF_SCOPE` is kept separate from a technical `FAIL`. A record can be outside
the physical programme scope without being technically unsuitable.

## S2 transition is a separate gate

The V1.2 household state model requires S1 before S2. Therefore:

`TECHNICALLY_ELIGIBLE != S2_TRANSITION_READY`

`assess_s2_transition_readiness()` requires both:

- B02 technical eligibility = `ELIGIBLE`; and
- the S1 predecessor gate `demand_reduction_measured_or_not_required` = `PASS`
  with `OBS`/`DER` evidence.

A technically eligible dwelling with unresolved S1 evidence remains `S2_Q`.

## Current repository result

`assess_current_repository_gate()` reads the canonical B02 S0–S2 evidence gap
matrix and B01 physical-population registry.

Current blockers are:

- `GAP-B02-S2-HEAT-EMITTER`;
- `GAP-B02-S2-DESIGN-TEMPERATURE`;
- `GAP-B02-S2-HYDRAULIC`;
- `GAP-B02-S2-ELECTRICAL`;
- `GAP-B02-S2-PERMIT`.

Consequently:

- physical screening reference = **3,389,817**;
- national technically eligible dwellings = **blank**;
- technical eligibility status = **`Q`**;
- S2 transition status = **`S2_Q`**.

This is a useful result: the model can now distinguish a proven technical
blocker from missing evidence without inflating or shrinking the national stock.

## Relationship to existing B02 evidence

B02-P2 consumes and preserves the earlier contracts:

- P1-I readiness bridge;
- P1-J S0–S2 evidence gap matrix;
- P1-K OÉNY pilot acceptance contract;
- P1-M public machine-access audit;
- P1-L OÉNY data-request release package.

The P1-M audit found zero fully public P1K-compatible readiness fields and the
P1-L package remains `READY_FOR_HUMAN_REVIEW / NOT SENT`. B02-P2 therefore does
not promote the OÉNY public UI into a national readiness source.

## Variable-boundary clarification

The existing global `VAR-B02-ELIGIBLE-DWELLINGS` remains **blank / `Q`** and
retains its older broad wording covering legal, technical and economic
conditions. B02-P2 does not silently redefine that legacy variable.

For this slice, the canonical machine output for **technical eligibility only**
is:

`registry/b02_technical_eligibility_gate.csv:technical_eligible_dwellings`

That field is also blank / `Q` in the current repository state. A later explicit
registry harmonization may split the legacy broad variable into technical,
legal/programme and economic eligibility surfaces. Until then, B02-P2 must not
populate the broad legacy variable from technical evidence alone.

Legal programme eligibility, economic eligibility, cash-flow and support
eligibility belong to B01/B12 and later portfolio layers.

## Non-results

B02-P2 does not provide:

- a national technical-eligibility count;
- a representative national emitter distribution;
- a national design-temperature distribution;
- hydraulic readiness prevalence;
- building-level electrical headroom;
- permit readiness prevalence;
- an S1 before/after result;
- legal/economic programme eligibility;
- a real annual rollout selection.

`Q-B02-001` and `Q-B02-004` remain open.
