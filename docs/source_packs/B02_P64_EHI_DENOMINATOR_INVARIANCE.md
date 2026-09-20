# B02-P64 — EHI denominator invariance and national surface-presence band

**State:** `NATIONAL EHI SURFACE-PRESENCE BAND DENOMINATOR-INVARIANT / Q-B02-004 OPEN`

**Canonical base:** `67096cbc7a142e5583c60fb16aeaf2114b07447c`

**Implementation date:** 2026-09-20

## 1. Purpose

B02-P62 established a screenshot-verified Hungary-specific external validation band from EHI 2024:

- houses: 33–66% surface heating & cooling penetration;
- apartments: 33–66% surface heating & cooling penetration.

B02-P63 then retired a separately observed national baseline design-temperature distribution as a required programme input.

The remaining Q-B02-004 note still listed a KSH denominator bridge as though numeric house/apartment population weights were necessary before a national EHI surface-presence validation envelope could be formed.

P64 tests that requirement.

## 2. Mathematical result

Let:

- p_h = EHI houses surface-presence share;
- p_a = EHI apartments surface-presence share;
- w = national weight assigned to houses;
- 1-w = national weight assigned to apartments.

EHI constrains both source-native strata to the same interval:

`p_h in [0.33, 0.66]`

`p_a in [0.33, 0.66]`.

For any:

`0 <= w <= 1`

the aggregate is:

`p_total = w * p_h + (1-w) * p_a`.

Because a convex combination of values inside the same closed interval remains in that interval:

`p_total in [0.33, 0.66]`.

Therefore:

`COMMON STRATUM BOUNDS -> AGGREGATE BOUND INVARIANT TO NUMERIC DENOMINATOR WEIGHTS`.

No KSH family/multi numeric weight is needed merely to preserve the national external validation band.

## 3. What is retired

The following blocker is retired **only for the national EHI validation envelope**:

`KSH_DENOMINATOR_BRIDGE AS NUMERIC WEIGHT REQUIREMENT`.

The P62 national external validation statement can therefore remain:

`HUNGARY RESIDENTIAL SURFACE-PRESENCE VALIDATION BAND = [0.33, 0.66]`

without selecting a family-house share, apartment share, midpoint or point estimate.

Evidence semantics remain:

`DER / EXTERNAL_BINNED_VALIDATION`.

## 4. What is not retired

P64 does not assert:

`EHI_HOUSES = P21_FAMILY_HOUSE`

or:

`EHI_APARTMENTS = P21_MULTI_DWELLING`.

The source-native EHI taxonomy has not been documented at enough detail to justify exact cell-level equivalence.

Therefore the following remain open:

### EHI_TO_P21_SEMANTIC_COVERAGE

The model must document the admissible semantic relationship between the EHI residential frame and the canonical P21 building-type frame.

### P21_STRATUM_EMITTER_ALLOCATION

Even though the overall national EHI interval is denominator-invariant, the model still lacks a justified conditional emitter distribution by:

- P21 building type;
- construction period;
- WBL geography;
- heating mode/fuel;
- other archetype dimensions.

### MIXED_SYSTEM_OVERLAP

Surface presence is not surface-only prevalence. A dwelling can contain radiators and surface heating together.

### OTHER_EMITTER_SHARE

Fan-coils and other emitters cannot be forced into a binary radiator/surface partition.

### TRANSITION_MODEL_POPULATION_WEIGHTING

P63 established that post-retrofit design temperature is a transition-derived output. The programme still needs a population model that weights P65-compatible transition outcomes across the stock.

## 5. Why this matters

Without P64, the model could incorrectly wait for an exact KSH house/apartment denominator before using the EHI national validation interval.

That would be unnecessary.

If both source strata carry the same interval, changing their relative weights cannot move the convex aggregate outside that interval.

This is a mathematical property of the evidence bounds, not a claim that the source taxonomies are identical.

Canonical separation:

`NUMERIC DENOMINATOR WEIGHTS != SEMANTIC CATEGORY MAPPING`.

P64 closes the first issue for the national validation layer and leaves the second explicit.

## 6. Executable contract

Canonical implementation:

`modules/B02/ehi_surface_band_aggregation.py`

The implementation:

1. validates prevalence bounds;
2. returns the common interval without denominator weights only if every input stratum has identical bounds;
3. requires explicit normalized weights if stratum bounds differ;
4. does not materialize a midpoint;
5. labels the result `DER / NATIONAL_VALIDATION_BAND_ONLY`.

Canonical machine-readable evidence:

`registry/b02_p64_ehi_denominator_invariance.csv`.

## 7. Non-claims

P64 does not claim:

- that 33% or 66% is the Hungarian point estimate;
- that the midpoint is 49.5%;
- that the national share is exactly any interior value;
- that EHI houses are identical to P21 FAMILY_HOUSE;
- that EHI apartments are identical to P21 MULTI_DWELLING;
- that the EHI source categories have been assigned to WBL cells;
- that mixed systems are quantified;
- that radiator share equals one minus surface share;
- that Q-B02-004 is resolved.

## 8. Q-B02-004 residual after P64

The current residual becomes:

`EHI_TO_P21_SEMANTIC_COVERAGE`

`+`

`P21_STRATUM_EMITTER_ALLOCATION`

`+`

`MIXED_SYSTEM_OVERLAP`

`+`

`OTHER_EMITTER_SHARE`

`+`

`TRANSITION_MODEL_POPULATION_WEIGHTING`.

The obsolete residual:

`KSH_DENOMINATOR_BRIDGE`

is retained only in historical source packs and is superseded by this current contract for national-band aggregation.

## 9. Next logical step

The next useful step is not to seek exact national radiator and surface-heating percentages immediately.

Instead, build a **set-identified emitter population model** that:

- accepts the P39 gas-convector calibrated branch;
- enforces the EHI 33–66% surface-presence interval;
- preserves mixed-system overlap as an explicit uncertain variable;
- preserves OTHER as a separate residual;
- uses P21/KSH population controls where a conditional allocation is justified;
- propagates every admissible composition through P65-compatible transition scenarios;
- returns bounded CAPEX/COP/procurement outputs rather than one false-precision emitter mix.

If that bounded model passes calibration and uncertainty gates, Q-B02-004 may be resolvable without ever discovering a perfect national microdataset.
