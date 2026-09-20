# B02-P59 — permit readiness moved to site legal / delivery gate

**State:** `PERMIT RETIRED FROM B02 TECHNICAL-ELIGIBILITY COMPONENT SET / SITE LEGAL-DELIVERY GATE ADDED`

**Base:** `c16947c03fb29919ea63f78364e992e709d6ff0f`

**Implementation date:** 2026-09-20

## 1. Purpose

P59 repairs a layer error.

The former B02 technical gate required `PERMIT` as if permit readiness were a
building-physics property. It is not.

The relevant authority depends on the **actual site and proposed installation**:
national building rules, local townscape rules, protected/heritage status,
property or condominium consent, outdoor-unit placement, noise and water
disposal.

Therefore:

`PERMIT READINESS != BUILDING PHYSICS`

`NO CURRENT PERMIT DATA != TECHNICALLY INELIGIBLE`

`SITE CLEARANCE UNKNOWN != PASS`

`PENDING != FAIL`

`FINAL REFUSAL WITHOUT COMPLIANT ALTERNATIVE = BLOCKED`

## 2. National rule evidence

The current national building regulation, 280/2024. (IX. 30.) Korm. rendelet,
contains explicit requirements for outdoor mechanical equipment:

- it must not restrict or disturb the proper and safe use of neighbouring property;
- maximum operating noise must comply with environmental noise limits;
- condensate/water disposal may not be directed onto public space and must not
  damage or disturb another property;
- heating systems must be designed and implemented according to applicable
  energy, fire-safety and standards requirements.

These are **installation design constraints**, not a national pre-existing permit
field for the housing stock.

## 3. Local-rule variability

Hungarian municipal regulations show that local conditions differ.

Examples include:

- placement restrictions for heat-pump outdoor units on street-facing facades;
- setback/noise conditions;
- townscape notification procedures that explicitly include heat pumps;
- protected or visually sensitive areas with additional restrictions.

This proves that one national `permit_ready` stock variable is the wrong grain.

## 4. New gate

`assess_site_legal_delivery()` evaluates the proposed site/design.

Required checks:

- national building rule;
- local townscape rule;
- local clearance status where applicable;
- heritage/protected status;
- property/condominium consent where applicable;
- outdoor-unit siting;
- noise compliance basis;
- condensate/water disposal;
- source references and reproducible binding.

Clearance semantics:

- `NOT_REQUIRED` -> may qualify;
- `APPROVED` -> may qualify;
- `PENDING` -> `Q`;
- `REFUSED` + no compliant alternative -> `BLOCKED`;
- `REFUSED` + alternative design -> `Q` until the alternative is cleared.

## 5. Architecture effect

P59 removes `PERMIT` from the B02 **technical eligibility component set**.

Legal/delivery clearance is handed to the programme's legal/implementation
layer (B01/B18 orchestration; B10 where network/connection authority is relevant).

This does not make permission optional. It puts it in the correct layer.

## 6. Historical preservation

P2/P3/P4/P5 source packs remain historical and are not rewritten.

The historical gap row `GAP-B02-S2-PERMIT` remains for lineage, but it is no
longer consumed by the current B02 technical-eligibility gate.

`HISTORICAL GAP RECORD != CURRENT CANONICAL TECHNICAL BLOCKER`
