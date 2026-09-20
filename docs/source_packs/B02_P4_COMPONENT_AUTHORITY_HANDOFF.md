# B02-P4 — Technical Component Authority Handoff

**Date:** 2026-09-05

**Status:** CONTRACTED / NO NATIONAL ELIGIBLE-STOCK UPLIFT

## Decision

B02-P2 defines the three current technical eligibility components, and B02-P3 separates technical eligibility from physical, legal, economic and final programme eligibility. P59 moved PERMIT out of the B02 technical component set into the separate site legal/delivery authority. B02-P4 now freezes which repository modules may author real PASS/FAIL evidence for each technical component.

The core boundary is:

`B02 CONSUMES TECHNICAL COMPONENT EVIDENCE != B02 AUTHORS EVERY COMPONENT`

In particular:

- `B02 != ELECTRICAL AUTHORITY`
- `B02 != PERMIT AUTHORITY`
- `Q != SELF-AUTHORIZATION`

## Canonical producer map

| Component | Consumer | Permitted producer modules | Current state |
|---|---|---|---|
| `THERMAL_DISTRIBUTION` | B02 | B02 | Q |
| `HYDRAULIC` | B02 | B02; B06 | Q |
| `ELECTRICAL` | B02 | B08; B10 | Q |
| `PERMIT` | B01; B18 | B18; B10 | CONTRACTED |

Machine-readable authority: `registry/b02_technical_component_authority.csv`.

The mapping is a repository architecture contract. It does not itself create OBS/DER evidence and does not close any current gap.

## Fail-closed rules

1. A real `PASS` or `FAIL` component decision requires `OBS` or `DER` evidence under B02-P2.
2. B02-P4 additionally requires an explicit producer module for every real `PASS` or `FAIL`.
3. The producer must be listed for that exact component in the authority registry.
4. A `Q` component carries no producer-module claim. Missing evidence cannot acquire authority merely by naming a module.
5. `THERMAL_DISTRIBUTION` remains a B02 component-decision responsibility. B02 may consume a P65-qualified B06 post-retrofit emitter/temperature decision as evidence, but B06 is **not** itself a permitted P4 component producer. This prevents a producer-module label from bypassing P65. Missing current-stock evidence is not reconstructed and no national emitter/temperature distribution is created.
6. `HYDRAULIC` may be direct B02 building evidence or a B06 derivation only when source building/system evidence exists.
7. `ELECTRICAL` must arrive from B08/B10 electrical-load/network authority. B02 archetype, heating fuel or existing heat-pump presence cannot prove electrical readiness.
8. `PERMIT` is not a B02 technical component after P59. Its separate B01/B18 site legal/delivery authority may consume B18/B10 evidence; OÉNY record presence cannot prove permit readiness.

## Current repository implication

P57-P59 and P65 separate **national stock coverage** from **record/project gate execution**.

The executable per-record technical gate has contracted decision routes for the
required transition components, but this does **not** produce a national
technically eligible dwelling count. A concrete record remains `Q` whenever
its required OBS/DER component evidence is missing.

The historical stock gaps for emitter type, design water temperature, hydraulic
state and electrical state remain visible in the gap matrix as national-data
coverage questions. They are not treated as aggregate prerequisites that must
be solved before a real building can be assessed through its own project
evidence.

Therefore:

- national technical eligible dwellings remain blank/Q;
- `Q-B02-001` remains OPEN because the size/composition of the nationally
  technically suitable stock is still unknown;
- `Q-B02-004` remains OPEN because the national emitter/design-temperature
  distribution is still unknown;
- those open national questions do not authorize inference for an individual
  record and do not prevent P65 from resolving a properly evidenced individual
  post-retrofit thermal-distribution design;
- `THERMAL_DISTRIBUTION.current_authority_status` remains `Q` because the
  authority route is not itself real-building evidence.

## Runtime

`modules/B02/technical_component_authority.py` is the canonical real-record wrapper above the generic B02-P2 eligibility engine.

It rejects:

- B02-authored electrical readiness;
- B02-authored permit readiness;
- real component decisions without an explicit producer;
- producer claims on Q components;
- unknown or wrong producer-module mappings.

This slice allocates claim authority only. It does not infer an eligible population and does not convert cross-module availability into evidence completeness.

**P65 amendment — 2026-09-20:** B06 now supplies a bounded,
P65-qualified post-retrofit emitter/temperature **evidence decision** that B02
may consume. The P4 component producer remains B02. This preserves the
authority boundary because `technical_component_authority.py` validates
producer modules but does not independently re-run P65.
