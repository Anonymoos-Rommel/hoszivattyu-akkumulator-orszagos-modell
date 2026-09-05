# B02-P17 — Primary-energy-to-WBL linkage authority audit and admission hardening

**Status:** `KSH FULL-STOCK MODEL EXISTS / NO PUBLIC REPRODUCIBLE WBL PRIMARY-ENERGY LINK / Q-B02-002 REMAINS OPEN`

**Base:** B02-P16 merged main `e2b21ce30c3698104c79daeed1f6a7e730c5c2e0`

**Audit date:** 2026-09-05

## Purpose

B02-P15 materialized the complete occupied WBL011 stock joint and P16 hardened current building-type direct-link authority. The other current-stock blocker is the primary-energy-to-WBL link.

P17 audits the strongest already-registered KSH energy evidence and prevents raw evidence-status strings from bypassing direct-link or calibrated-model admission.

Canonical boundaries:

`PRIMARY-ENERGY MODEL EXISTS != REPRODUCIBLE WBL LINK AUTHORITY`

`PUBLIC AGGREGATE MODEL OUTPUT != RECORD-LEVEL WBL BINDING`

`LINKED CERTIFICATE SAMPLE != COMPLETE OCCUPIED-STOCK PRIMARY-ENERGY ASSIGNMENT`

`MODELLED FULL-STOCK PREDICTION != OBSERVED WBL PRIMARY-ENERGY JOINT`

`RAW OBS/DER LINK TOKEN != DIRECT-LINK ADMISSION`

`MODEL STATUS TOKEN != MODEL APPROVAL`

## 1. Strongest current KSH evidence

Existing canonical source IDs:

- `SRC-B02-KSH-ENERGY-2025`;
- `SRC-B02-KSH-ENERGY-METHOD-2025`.

The KSH experimental-statistics methodology describes a two-stage evidence surface:

1. energy certificates are address-linked to the 2022 Census dwelling stock;
2. a final random-forest model is applied to the full census housing stock to estimate dwelling-level specific primary-energy demand.

Repository controls already freeze:

- 2022 census housing stock: **4,580,538** dwellings;
- linked energy certificates: **279,020**;
- published family-house energy-bin records: **2,881,310** dwellings;
- published multi-dwelling energy-bin records: **1,694,480** dwellings;
- combined published-bin count: **4,575,790**;
- published-bin residual versus census stock: **4,748** dwellings.

The final KSH model uses census characteristics including variables that overlap materially with WBL dimensions: construction period, wall material, floor area, settlement type, heating fuel and heating-system/fuel combinations. The methodology also distinguishes family-house and multi-dwelling models.

This proves that a highly relevant current primary-energy model exists inside the official KSH analytical environment.

It does not make the repository able to reproduce the individual predictions or join them to the materialized WBL rows.

## 2. Direct evidence path

A direct `OBS`/`DER` primary-energy authority may satisfy P9 only if a separate direct-link admission is `QUALIFIED`.

P17 defines the minimum direct path:

- reference year `2022+`;
- universe exactly `OCCUPIED_DWELLING_STOCK`;
- grain either `WBL_FULL_JOINT` or reproducibly joinable `DWELLING_RECORD`;
- evidence status `OBS` or `DER`;
- primary-energy metric compatible with `SPECIFIC_PRIMARY_ENERGY_KWH_M2_YEAR` or an explicit `PRIMARY_ENERGY_BIN`;
- complete stock assignment for the claimed universe;
- explicit WBL-compatible join key;
- reproducible repository binding.

Missing any one condition returns `Q`.

The executable direct gate is implemented in:

`modules/B02/archetype_admission_gate.py::assess_direct_primary_energy_authority`

## 3. Why the 279,020 linked certificates do not qualify directly

The linked certificates are real source observations, but the public KSH publication exposes only aggregate linkage characteristics and methodology. It does not publish the 279,020 record-level rows or a reusable non-PII key that allows the repository to bind those observations to WBL011 records.

The linked subset is also not a complete assignment of the `DW_OC` occupied-dwelling stock.

Therefore:

`279,020 LINKED OBS RECORDS != COMPLETE OCCUPIED WBL PRIMARY-ENERGY JOINT`

No missing primary-energy values are zero-filled and no sample row is silently expanded to the rest of the stock.

## 4. Why the full-stock KSH random forest does not qualify directly

The KSH publication states that the final random-forest model was applied to the complete 2022 census housing stock. The resulting primary-energy values are explicitly model outputs, not observations.

The public material does not expose:

- the fitted random-forest artifact required to replay individual predictions;
- the individual full-stock predictions;
- a repository-reproducible record key linking those predictions to the committed WBL full joint.

The methodology itself emphasizes that individual dwelling predictions carry materially more uncertainty than grouped territorial or stock-level results. The publication is therefore strong calibration/model evidence, but not a direct WBL assignment authority.

Canonical:

`INTERNAL DWELLING-LEVEL MODEL APPLICATION != PUBLIC REPRODUCIBLE DWELLING-LEVEL OUTPUT`

## 5. P12 calibrated-model candidate

P17 does not discard the KSH random forest. It records it as the strongest current candidate for the existing P12 calibrated primary-energy linkage route.

Canonical candidate ID:

`KSH-RF-2022-PRIMARY-ENERGY`

The candidate has positive evidence for:

- explicit model identity;
- calibration sources;
- 2022 reference period;
- representativeness diagnostics at regional level;
- validation metrics / cross-validation evidence;
- `MODELLED` output semantics.

It remains `Q` because current public/repository evidence does not satisfy all P12 gates, including:

- no Joseph approval;
- no repository-reproducible WBL target binding;
- no complete WBL marginal reconciliation contract;
- no explicit downstream uncertainty method;
- no mandatory uncertainty propagation contract;
- no separately documented independence-assumption control for this repository linkage use.

P17 is **not** an approval of the KSH model for canonical stock assignment.

## 6. P9 token-bypass hardening

P12 already prevented `MODELLED_LINKED` from self-authorizing. P16 defined a separate direct building-type authority gate, but P9 still accepted raw `OBS`/`DER` linkage tokens without an explicit direct-admission result.

P17 closes that generic token-bypass path for both direct linkage dimensions:

- raw `OBS`/`DER` building-type link requires `building_type_direct_authority_status = QUALIFIED`;
- raw `OBS`/`DER` primary-energy link requires `primary_energy_direct_authority_status = QUALIFIED`;
- modelled paths continue to require separate P12 qualification.

Thus:

`EVIDENCE STATUS != LINK AUTHORITY`

## 7. Current state after P17

The current-stock blockers remain exactly:

- `NO_CURRENT_BUILDING_TYPE_LINK_AUTHORITY`;
- `NO_PRIMARY_ENERGY_TO_WBL_LINK_AUTHORITY`.

The reason for the primary-energy blocker is now precise:

`OFFICIAL CURRENT FULL-STOCK MODEL EXISTS / PUBLIC REPRODUCIBLE WBL LINK MISSING / MODEL NOT P12-ADMITTED`

Technical-readiness additionally remains blocked by:

- `NO_CURRENT_HEAT_EMITTER_EVIDENCE`;
- `NO_CURRENT_DESIGN_TEMPERATURE_EVIDENCE`.

## State

- `Q-B02-001`: OPEN;
- `Q-B02-002`: OPEN;
- `Q-B02-004`: OPEN;
- current-stock archetype: `Q`;
- technical-readiness archetype: `Q`;
- national technical/final eligible count: blank / `Q`;
- B02 readiness: **55%**;
- **no readiness uplift**;
- OÉNY request remains unsent.

No external request or microdata transmission is authorized by this slice.
