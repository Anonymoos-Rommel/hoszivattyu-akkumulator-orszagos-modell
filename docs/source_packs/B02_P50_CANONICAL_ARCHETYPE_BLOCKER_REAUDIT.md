# B02-P50 — canonical archetype blocker re-audit and Q-B02-002 closure

**State:** `Q-B02-002 RESOLVED / NO ELIGIBILITY COUNT CREATED / Q-B02-001 + Q-B02-004 REMAIN OPEN`

**Base:** `a1f5daac96e264b1a47760cd64aedb13b5d72b1c`

**Audit date:** 2026-09-20

## 1. Purpose

The project-wide population inference policy changed one methodological premise:

`NO FULL-POPULATION DATA != BLOCKER`

`NO DEFENSIBLE POPULATION INFERENCE == BLOCKER`

P50 applies that rule to the still-open Q-B02-002 question:

> Which variables and category boundaries form the canonical building archetypes?

The question had remained OPEN after earlier slices even though later canonical work had already supplied both the dimension contract and an admitted calibrated WBL linkage.

P50 does not invent new population data. It re-audits the current canonical repository state.

## 2. Existing canonical evidence

### 2.1 Dimension and category contract

`registry/archetype_dimensions.csv` already CONTRACTS the required B02 dimensions, including:

- geography;
- occupancy;
- construction period;
- wall material;
- floor-area band;
- comfort;
- heating mode;
- heating fuel;
- heat-pump presence;
- building type;
- heat emitter;
- primary energy;
- optional energy class.

The current building-type categories are explicitly:

- `FAMILY_HOUSE`;
- `MULTI_DWELLING`.

Construction-period harmonisation is separately contracted, including the source-preserving `Y_GE2011` bridge.

### 2.2 Exact WBL population binding

B02-P15 materialises the source-native WBL011 occupied-stock full joint:

- 116,452 positive rows;
- 4,008,541 occupied dwellings;
- source-native WBL dimensions retained.

This is the exact population-control surface to which calibrated archetype outputs bind.

### 2.3 Approved calibrated linkage

B02-P21 provides:

- `B02-P21-PUBLIC-KSH-BUILDING-TYPE-LINKAGE`;
- `B02-P21-PUBLIC-KSH-PRIMARY-ENERGY-LINKAGE`.

The current P12 admission registry records both as:

`APPROVED / JOSEPH / QUALIFIED`

with:

- target-grain compatibility;
- representativeness diagnostics;
- validation metrics;
- exact marginal reconciliation;
- uncertainty method;
- uncertainty propagation;
- controlled independence assumptions;
- reproducible WBL binding.

Building-type output remains `ASS`; primary-energy output remains `MODELLED`.

## 3. Why Q-B02-002 can now close

Historical slices correctly rejected the inference:

`2015 PROXY != 2022 WBL SUBCELL OBSERVATION`

That boundary remains true.

But the current project no longer requires direct full-population observation when a calibrated population inference passes the canonical admission gate.

Therefore:

`NO DIRECT BUILDING-TYPE OBSERVATION != NO BUILDING-TYPE AUTHORITY`

P21 supplies the admitted calibrated authority required by the project-wide policy.

The canonical archetype variables/category boundaries are already contracted and the building-type/primary-energy population linkage is already reproducible and admitted.

Therefore:

`Q-B02-002 -> RESOLVED`

## 4. Non-claims

P50 does not claim:

- building-type output is OBS or DER;
- every WBL association is observed;
- heat-emitter distribution is known;
- design-temperature distribution is known;
- national technical eligibility is known;
- the current 55% B02 readiness should increase automatically.

The calibrated output retains its original evidence class and uncertainty.

## 5. Remaining B02 blocker chain

After P50 the current high-level chain is:

1. `Q-B02-004` — national heat-emitter + design-temperature inference;
2. `Q-B02-001` — national technically suitable stock after technical inference + exclusion rules;
3. `Q-B01-001` — programme-target household definition after technical/legal programme eligibility is combined.

This ordering follows the project dependency logic and avoids searching for downstream values before upstream physical classification exists.
