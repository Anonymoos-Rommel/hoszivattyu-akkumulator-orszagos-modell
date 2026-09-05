# B01-P4 — Canonical programme-target variable harmonization

## Purpose

B01-P4 removes the last active global-registry representation of the original
2,000,000-household working hypothesis and its 2,500,000 ceiling.

B01-P2 and B01-P3 had already established the semantic boundary:

`LEGACY TARGET HYPOTHESIS != PHYSICAL POPULATION REFERENCE != TECHNICALLY ELIGIBLE STOCK != PROGRAMME TARGET`

The global `registry/variables.csv` still carried the pre-P2 values as if they
were an active `POL` default and maximum. That created a risk that a downstream
consumer could silently resurrect the superseded target.

## Canonical variable state

`VAR-B01-TARGET-HOUSEHOLDS` now has:

- `default_value = <blank>`;
- `min_value = 0`;
- `max_value = <blank>`;
- `status = Q`.

The variable therefore defines the field and unit, but does not define a
numerical national target.

Every actual rollout run must provide an explicit `POL` or `SCN` target through
the B01-P2 rollout contract. If a target is bounded by a population reference,
that reference must be named with its own evidence status and semantics.

## Historical values

The following values remain available only for audit/history:

- `2,000,000` — original working hypothesis;
- `2,500,000` — original registry ceiling.

They are not current defaults, ceilings, observed stock, technical eligibility,
or programme results.

The B01-P2 registry continues to preserve the 2,000,000 value explicitly as
`legacy_original_hypothesis_households` so old calculations remain traceable.

## Current physical reference

B01-P3 provides the exact current physical population reference:

- occupied dwellings: `4,008,541 OBS`;
- district-heated occupied dwellings: `618,724 DER_FROM_OBS_WBL011_CELLS`;
- non-district-heated occupied dwellings: `3,389,817 DER_FROM_OBS_WBL011_CELLS`.

The exact 3,389,817 value is not written into the programme-target variable as a
default or maximum because:

`NON-DISTRICT-HEATED OCCUPIED DWELLING != TECHNICALLY ELIGIBLE HEAT-PUMP DWELLING`

B02 technical eligibility remains a separate downstream gate.

## Fail-closed consequence

A consumer that reads `VAR-B01-TARGET-HOUSEHOLDS` and receives a blank numeric
value must not substitute:

- 2,000,000;
- 2,500,000;
- 3,389,817;
- the occupied-dwelling universe;
- any gas/electricity customer count;
- zero.

It must require an explicit target input or return `Q/BLOCKED` according to the
calling contract.

## Readiness

B01 readiness remains **35%**. This slice removes a stale hidden assumption but
does not solve `Q-B01-001`, B02 national technical eligibility, the real annual
capacity path, or regional/settlement household allocation.
