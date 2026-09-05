# B02-P18 — Current heat-emitter and design-temperature direct authority hardening

**Status:** `DIRECT AUTHORITY CONTRACTED / CURRENT EVIDENCE STILL Q`

**Base:** B02-P17 merged main `57f7f70d912644c0ca1c618ab95ce8d0dd40d433`

**Audit date:** 2026-09-05

## Purpose

B02-P17 closed the remaining raw-token bypass in current-stock archetype admission: an `OBS` or `DER` status is not itself a building-type or primary-energy link authority.

P18 applies the same epistemic rule to the technical-readiness layer.

Canonical boundaries:

`RAW OBS/DER READINESS TOKEN != TECHNICAL DIRECT AUTHORITY`

`DOCUMENT-LEVEL EVIDENCE != STOCK-LEVEL ASSIGNMENT`

`PROPOSED EMITTER != CURRENT EMITTER`

`OPERATING TEMPERATURE EVIDENCE != DESIGN TEMPERATURE AUTHORITY`

`REFERENCE 55/45 C != CURRENT BUILDING DESIGN TEMPERATURE`

This slice does not invent current heat-emitter or temperature data. It defines what future evidence must prove before those fields can enter the P9 technical-readiness archetype.

## 1. Existing canonical evidence surface

The relevant already-canonical sources/contracts are:

- `SRC-B02-OENY-SCHEMA-DICTIONARY-2026`;
- `SRC-B02-OENY-VALIDATION-2026`;
- `SRC-B02-OENY-FULL-EXAMPLE-2026`;
- `SRC-B02-OENY-PUBLIC-CERT-BASICS-2026`;
- `SRC-B02-OENY-PUBLIC-UI-2026`;
- `registry/oeny_public_field_mapping.csv`;
- `schemas/oeny_readiness_pilot.schema.json`;
- `docs/source_packs/P1K_OENY_PILOT_ACCEPTANCE_CONTRACT.md`;
- `docs/source_packs/B02_P5_TABULA_THERMAL_DISTRIBUTION_BOUNDARY.md`.

P1J/P1K already establish that the pinned OENY structured certificate surface has no dedicated current-emitter field and no dedicated current design supply/return temperature pair. Potential document evidence may exist in certificate attachments, but that is not a public stock-level table and not a WBL-compatible assignment.

The current public OENY mapping keeps `emitter_status`, `emitter_types`, `emitter_evidence`, `temperature_status`, `supply_temperature_c`, `return_temperature_c`, `temperature_basis`, and `evidence_pages` as `NOT_PUBLICLY_AVAILABLE`.

A fresh 2026 public-surface recheck is consistent with that boundary: OENY remains the central registry and public certificate lookup exists, but the full certificate is not exposed as a public machine-readable readiness dataset. No current public source was found that upgrades the existing repository evidence state.

## 2. Heat-emitter direct authority

A future direct heat-emitter authority may satisfy P9 only if all of the following are true:

1. reference year is 2022 or later;
2. universe is exactly `OCCUPIED_DWELLING_STOCK`;
3. grain is `WBL_FULL_JOINT` or reproducibly joinable `DWELLING_RECORD`;
4. evidence status is `OBS` or `DER`;
5. the evidence explicitly describes the **current** emitter state, not a proposed modernization;
6. evidence type is explicit and auditable: `TEXT_EXPLICIT`, `TABLE_EXPLICIT`, `SCHEMATIC_EXPLICIT`, or `PHOTO_EXPLICIT`;
7. an evidence locator/page/reference exists;
8. the claimed stock assignment is complete for the claimed universe;
9. a WBL-compatible join key exists;
10. the binding is reproducible in the repository.

Missing any one condition returns `Q`.

The executable gate is:

`modules/B02/archetype_admission_gate.py::assess_direct_heat_emitter_authority`

The OENY pilot schema remains useful for extraction validation, but a valid document annotation does not by itself satisfy stock-level completeness, WBL binding, or representativeness.

## 3. Design-temperature direct authority

P1K deliberately allows several temperature evidence bases because it is an annotation/intake contract. P9 has a narrower claim: current **design-temperature** evidence for technical readiness.

Therefore P18 distinguishes:

- `DESIGN_EXPLICIT` — potentially admissible;
- `CALCULATION_INPUT` — potentially admissible if it explicitly belongs to the current system;
- `OPERATING_MEASURED` — real operating evidence, but not design-temperature authority;
- `REFERENCE_ASSUMPTION` — reference/calculation context only, never current-building evidence;
- `NOT_STATED` — not authority.

A direct design-temperature authority additionally requires:

- both supply and return values;
- finite values inside the schema range;
- supply temperature strictly greater than return temperature;
- explicit evidence locator;
- complete occupied-stock assignment at direct WBL grain or reproducible dwelling-record binding;
- WBL-compatible join key and reproducible repository binding.

The executable gate is:

`modules/B02/archetype_admission_gate.py::assess_direct_design_temperature_authority`

The Hungarian 55/45 C reference condition remains useful as a regulatory/calculation reference. It does not prove that a specific current building, WBL cell, or the national stock is designed or operated at 55/45 C.

## 4. Why OENY does not currently close Q-B02-004

OENY is still the strongest unresolved evidence route because certificate documents can potentially contain current emitter and temperature evidence.

However the current repository evidence proves only that:

- the public lookup does not expose the required readiness fields;
- the full certificate/document is not available as a public reusable readiness table;
- no public complete occupied-stock emitter assignment exists;
- no public complete occupied-stock design-temperature assignment exists;
- no WBL-compatible public join key exists for these fields;
- no representative national weighting contract has been satisfied.

Thus:

`OENY DOCUMENT EXTRACTION PATH EXISTS != CURRENT STOCK DIRECT AUTHORITY`

The existing P1F request remains unsent and P1K remains only `GO_FOR_REQUEST` subject to Joseph's separate send authorization.

## 5. TABULA/EPISCOPE remains context only

P5 already proved:

`HEAT GENERATION DATA != HEAT DISTRIBUTION DATA != CURRENT EMITTER EVIDENCE != DESIGN TEMPERATURE EVIDENCE != HYDRAULIC READINESS`

The Hungarian TABULA/EPISCOPE line does not publish the missing current national heat-distribution/storage statistics, and the typology brochure uses characteristic/modelled building-service solutions. It therefore cannot satisfy either P18 direct gate.

## 6. P9 hardening

Before P18, `assess_technical_readiness_enrichment()` required only raw `OBS`/`DER` status strings for emitter and design temperature.

After P18:

- `heat_emitter_status = OBS/DER` requires `heat_emitter_direct_authority_status = QUALIFIED`;
- `design_temperature_status = OBS/DER` requires `design_temperature_direct_authority_status = QUALIFIED`.

A raw real-evidence token without the separate authority decision fails closed as:

- `HEAT_EMITTER_DIRECT_EVIDENCE_NOT_ADMITTED`;
- `DESIGN_TEMPERATURE_DIRECT_EVIDENCE_NOT_ADMITTED`.

Missing/non-real evidence continues to use the existing blockers:

- `NO_CURRENT_HEAT_EMITTER_EVIDENCE`;
- `NO_CURRENT_DESIGN_TEMPERATURE_EVIDENCE`.

## 7. Current state after P18

No current evidence is promoted.

Current-stock archetype remains `Q` because:

- `NO_CURRENT_BUILDING_TYPE_LINK_AUTHORITY`;
- `NO_PRIMARY_ENERGY_TO_WBL_LINK_AUTHORITY`.

Technical-readiness archetype remains `Q` and additionally lacks:

- current heat-emitter direct authority;
- current design-temperature direct authority.

Questions/state:

- `Q-B02-001`: OPEN;
- `Q-B02-002`: OPEN;
- `Q-B02-004`: OPEN;
- national technical/final eligible count: blank / `Q`;
- B02 readiness: **55%**;
- **no readiness uplift**;
- OENY request: **not sent**.

P18 authorizes no external request, no certificate download, no microdata transfer, and no synthetic WBL allocation.
