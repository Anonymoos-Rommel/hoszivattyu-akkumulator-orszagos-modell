# B02-P104 — EKR VERIFIED WINDOW-COMPLIANCE ROUTE

## Goal

Continue from P103:

`CURRENT_REPLACED_WINDOW_REALIZED_UW_DISTRIBUTION_REQUIRED`

and test whether direct national realized-Uw data are genuinely the only
defensible route to classify the current replaced-window branch.

They are not.

P104 identifies a second authoritative Hungarian route: **verified EKR window
actions with technical opening records**.

## 1. Current EKR window action family

The current 18/2025. (VII. 31.) EM catalogue, as amended, contains:

- 1.2 — Nyílászáró korszerűsítés és csere;
- 1.4 — Családi ház nyílászáró csere normatív számítással;
- 1.6 — Társasház nyílászáró csere normatív számítással.

The current catalogue identifies window replacement as action type:

`1103 - Épületszerkezetek - Felújítás - Nyílászáró cseréje`.

The affected structure must satisfy the current 9/2023 ÉKM Annex 1 U-value
requirement after the action.

This is already materially stronger than a generic historical replacement
label.

## 2. The technical record contains U-quality evidence

The current catalogue is not merely a legal target.

For the detailed 1.2 route, the recorded technical parameters include:

- replaced opening type/glazing;
- count;
- area;
- new opening type/glazing;
- replaced opening U;
- **new opening U**.

For the 1.6 condominium route, supporting documentation includes:

- manufacturer;
- type;
- **opening U-value**;
- manufacturer performance declarations;
- contractor declaration of installed technical characteristics;
- before/after photographs;
- invoices/supporting documents;
- verification/inspection evidence.

Therefore:

`EKR TECHNICAL RECORD -> DOCUMENTED NEW OPENING U / COMPLIANCE EVIDENCE`.

This is not a population estimate; it is a record-level evidence route.

## 3. HEM verification matters

The Energy Efficiency Act requires HEM savings used in the system to be
verified by a registered audit organisation.

Verification establishes the actual implementation of the action and correct
application of the required calculation methods and principles.

Therefore P104 distinguishes:

`GENERIC LEGAL REQUIREMENT`

from:

`VERIFIED EKR ACTION + TECHNICAL RECORD`.

The latter is admissible record-level DER/POL evidence for the affected
openings.

It is still not a laboratory measurement of in-situ Uw.

## 4. Executable classification

For a recognised EKR window action:

1. HEM verification is required;
2. the technical record is required;
3. explicit new-opening U is compared to the current P103 programme target.

For the current P103 wood/PVC reference target:

- `U_new <= 1.10 -> AFFECTED_OPENING_REFERENCE_SATISFIED_VERIFIED_EKR`;
- `U_new > 1.10 -> AFFECTED_OPENING_REFERENCE_DEFICIT_VERIFIED_EKR`;
- missing verification/technical U -> unresolved.

This deliberately avoids:

`EKR LABEL -> AUTOMATIC COMPLIANCE`.

## 5. Affected opening is not whole-dwelling compliance

A window action can be partial.

The current EKR complex-measure rule explicitly distinguishes the case where
**all openings of the affected property** are replaced.

Therefore:

`VERIFIED EKR AFFECTED OPENING != WHOLE DWELLING WINDOW COMPLIANCE`.

Whole-dwelling window satisfaction requires either:

- verified full-dwelling opening coverage; or
- independent proof that all remaining openings already satisfy the reference.

Without that, the dwelling window state remains unresolved.

## 6. Public HEM publication boundary

The public MEKH HEM documentation creates a crucial split.

Without login, a HEM identifier can expose generic fields such as:

- HEM identifier;
- saving amount;
- beneficiary;
- implementation date;
- lifetime.

A public summary exposes:

- total reported HEM count;
- aggregate verified saving.

But the public surface does **not** establish publication of:

- measure type 1103;
- window measure code;
- new opening type;
- new opening U;
- full-dwelling opening coverage.

The richer administrative submission layer does contain the implemented
measure name/type and the catalogue technical workflow contains the detailed
window parameters.

Thus:

`ADMINISTRATIVE TECHNICAL FIELD != PUBLIC POPULATION SURFACE`.

## 7. OÉNY/EPC route re-audit

P104 also rechecked the OÉNY/EPC route.

Current certification rules require detailed supporting calculations for
building envelope/opening structures, and the OÉNY process retains a detailed
calculation document.

But the existing official OÉNY schema/user-guide audit and the 2025 JustReno
assessment agree on the practical population boundary:

- detailed certificate data are not exposed as a public representative bulk
  window-U dataset;
- the EPC population is not a random/representative sample of the entire
  housing stock;
- public OÉNY statistics are aggregate certificate counts rather than detailed
  opening-performance distributions.

Therefore OÉNY remains a possible administrative extraction route, not a
publicly materialized national replaced-window Uw surface.

## 8. P103 blocker repair

P103 phrased the blocker as:

`CURRENT_REPLACED_WINDOW_REALIZED_UW_DISTRIBUTION_REQUIRED`.

P104 proves this was too narrow because there are now two admissible closure
routes:

### Route A — direct physical distribution

Representative/calibrated current replaced-window Uw evidence.

### Route B — verified administrative compliance cohort

EKR 1103 technical records with:

- verified implementation;
- new opening U;
- programme-target comparison;
- enough coverage information to promote affected openings to whole-dwelling
  window state where justified.

Therefore the old direct-U-only blocker is superseded by:

`CURRENT_REPLACED_WINDOW_COMPLIANCE_POPULATION_SURFACE_REQUIRED`.

## 9. Exact remaining sub-residuals

The new population blocker decomposes into:

1. `EKR_1103_TECHNICAL_COHORT_AGGREGATE_REQUIRED`
2. `NON_EKR_REPLACED_WINDOW_UW_DISTRIBUTION_REQUIRED`
3. `FULL_DWELLING_WINDOW_COVERAGE_OR_REMAINING_STATE_REQUIRED`

The independent wall residual remains:

`MISSING_HISTORICAL_RENOVATED_WALL_U_TIGHTENING_REQUIRED`.

## 10. National numeric effect

No public 1103 technical cohort aggregate was identified.

No defensible non-EKR replaced-window population Uw distribution was identified.

Therefore P104 does **not** change the validated P102 national bounds:

- structural calibrated retrofit floor:
  **82.7861029945%**;
- HP_ONLY lower:
  **0%**;
- HP_ONLY upper:
  **17.2138970055%**.

This is intentional. P104 resolves the evidence architecture at record level
and makes the exact missing population surface explicit without inventing a
share.

## 11. Readiness

- **B02 remains 55%**;
- **PEAK_LOAD_EFFECT remains 50%**;
- **Q-B02-004 remains OPEN_NARROWED**.

## 12. Canonical boundaries

`GENERIC LEGAL REQUIREMENT != VERIFIED EKR ACTION`

`VERIFIED EKR AFFECTED OPENING != WHOLE DWELLING WINDOW COMPLIANCE`

`PUBLIC TOTAL HEM COUNT != EKR 1103 WINDOW COUNT`

`ADMINISTRATIVE TECHNICAL FIELD != PUBLIC POPULATION SURFACE`

`EKR WINDOW ACTION != ALL REPLACED WINDOWS`

`EKR COHORT != NON-EKR REPLACED WINDOW STOCK`
