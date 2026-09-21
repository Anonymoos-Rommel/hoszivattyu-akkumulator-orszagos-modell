# B02-P81 — current legal envelope U-value authority

**State:** `CURRENT LEGAL AFFECTED-COMPONENT U BOUNDS QUALIFIED / NATIONAL ASSIGNMENT STILL Q`

**Canonical base:** `7ac15e0531ffca88c2943e16d719f93c0835638b`

**Implementation date:** 2026-09-21

## 1. Purpose

P80 materialized the historical KEOP23 baseline U matrix and the dissertation's
reference-retrofit post-state U constraints.

P81 adds the current Hungarian legal authority:

`9/2023. (V. 25.) EKM rendelet`.

The core legal scope rule is section 3(3):

> structures of an existing building affected by an energy-saving renovation
> must satisfy Annex 1 sections 1 and 2.

Therefore the current component requirement can be bound to an explicit
post-retrofit action without pretending that every existing component already
has that U-value.

## 2. Current legal U requirements

Annex 1 section 1.1 provides:

| P80 component | Current legal source category | U max |
| --- | --- | ---: |
| EXTERNAL_WALL | homlokzati fal | **0.24 W/m2K** |
| FLAT_ROOF | laposteto | **0.17** |
| PITCHED_ROOF | futott tetoteret hatarolo szerkezetek | **0.17** |
| ATTIC_FLOOR | padlas es buvoter alatti fodem | **0.17** |
| BASEMENT_CEILING | also zarofodem futetlen terek felett | **0.26** |
| WINDOW | fa/PVC homlokzati uvegezett nyilaszaro >0.5 m2 | **1.10** |

For windows the legal requirement includes the frame, glazing, spacer and
similar functional elements according to the Annex note.

## 3. P80 pitched-roof gap

P80 correctly kept:

`TABLE_9_1_HAS_NO_EXPLICIT_PITCHED_ROOF_ROW`

open in the historical dissertation source.

The current legal source explicitly contains:

`Futott tetoteret hatarolo szerkezetek -> 0.17 W/m2K`.

Therefore for a P80 PITCHED_ROOF component that actually bounds heated attic
space and is affected by an energy-saving renovation:

`P80 PITCHED_ROOF U GAP -> RESOLVED_BY_CURRENT_LEGAL_AUTHORITY`.

This does not retroactively invent a row in historical Table 9.1.

## 4. Applicability boundary

The current U requirement is action-conditioned.

`CURRENT LEGAL U REQUIREMENT != CURRENT STOCK U OBSERVATION`.

`LEGAL REQUIREMENT FOR AFFECTED COMPONENT != REQUIREMENT FOR UNTOUCHED COMPONENT`.

Thus:

### Envelope renovation action

For an explicit energy-saving renovation affecting the component, under the
current EKM regime and without an applicable protection exception, P81 admits
the current legal U upper bound.

### AIR_TO_WATER_HP_ONLY

P80 defines HP-only as preserving the building envelope.

Therefore:

`HP_ONLY -> NO ENVELOPE LEGAL U TRIGGER`

for an untouched envelope component.

The current U-state still depends on:

`CURRENT_NO_ACTION_BASELINE_U_SURFACE_REQUIRED`.

## 5. Exceptions and transition rules

P81 does not assume universal legal applicability.

The decree excludes protected buildings/elements where compliance with minimum
energy-efficiency requirements would alter the value underlying monument or
local protection.

The decree also contains transitional handling for renovation implemented under
support relationships launched before promulgation where TNM-based requirements
were set.

Therefore national materialization requires:

`NATIONAL_LEGAL_ENVELOPE_EXCEPTION_REGIME_REQUIRED`.

Record/project legal applicability can then resolve:

- current EKM regime;
- applicable protection exception;
- legacy supported-program regime.

## 6. Relationship to P80 historical reference values

P80 historical reference values remain useful model provenance.

P81 does not overwrite them.

For affected components in the current legal regime, current legal authority is
stronger for legal compliance.

Notably:

- wall: historical reference 0.24 / current legal 0.24;
- flat roof: 0.17 / 0.17;
- attic floor: 0.17 / 0.17;
- basement ceiling: 0.26 / 0.26;
- wood/PVC window: historical 1.15 / current legal **1.10**;
- heated-attic boundary: historical P80 explicit row missing / current legal
  **0.17**.

Canonical boundary:

`LEGAL U-MAX != REALIZED POST-RETROFIT U POINT`.

## 7. Blocker effect

P80:

`POST_RETROFIT_COMPONENT_U_VALUE_SURFACE_REQUIRED
 -> PARTIAL_RESOLVED_ACTION_CONDITIONED`.

P81:

`POST_RETROFIT_COMPONENT_U_VALUE_SURFACE_REQUIRED
 -> PARTIAL_RESOLVED_CURRENT_LEGAL_ACTION_CONDITIONED`.

Retired as a current affected-component blocker:

`TABLE_9_1_HAS_NO_EXPLICIT_PITCHED_ROOF_ROW`.

Current U-state residual:

1. `NATIONAL_AFFECTED_ENVELOPE_COMPONENT_ASSIGNMENT_REQUIRED`;
2. `NATIONAL_LEGAL_ENVELOPE_EXCEPTION_REGIME_REQUIRED`;
3. `CURRENT_NO_ACTION_BASELINE_U_SURFACE_REQUIRED`;
4. `COMPONENT_AREA_GEOMETRY_SURFACE_REQUIRED`.

## 8. Non-claims

P81 does not claim:

- every existing dwelling has current-law U-values;
- every programme dwelling receives envelope renovation;
- an untouched HP-only envelope must be upgraded by virtue of HP installation;
- protected or legacy-program cases automatically use current EKM values;
- legal U-max is an achieved point U-value;
- component areas are known;
- national design load is solved;
- Q-B02-004 is closed.

B02 readiness remains **55%**.
