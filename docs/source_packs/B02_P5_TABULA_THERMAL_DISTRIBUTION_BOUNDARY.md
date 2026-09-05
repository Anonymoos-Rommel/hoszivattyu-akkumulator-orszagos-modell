# B02-P5 — TABULA / EPISCOPE Thermal-Distribution Evidence Boundary

**Date:** 2026-09-05

**Status:** `ALTERNATE_NATIONAL_SOURCE_AUDITED / Q-B02-004 REMAINS OPEN`

## Purpose

B02-P2 requires explicit evidence for `THERMAL_DISTRIBUTION`, and B02-P4 makes B02 the producer authority for current emitter/temperature evidence. B02-P5 audits the Hungarian TABULA/EPISCOPE national building-typology line as an alternate source path so that typology heat-generator data cannot later be misused as current heat-emitter or hydraulic-readiness evidence.

Canonical boundary:

`HEAT GENERATION DATA != HEAT DISTRIBUTION DATA != CURRENT EMITTER EVIDENCE != DESIGN TEMPERATURE EVIDENCE != HYDRAULIC READINESS`

## Sources audited

1. EPISCOPE country page for Hungary:
   `https://episcope.eu/building-typology/country/hu/`
2. BME / EPISCOPE national typology brochure:
   `https://episcope.eu/fileadmin/tabula/public/docs/brochure/HU_TABULA_TypologyBrochure_BME.pdf`
3. EPISCOPE/TABULA download and third-party usage rules:
   `https://episcope.eu/communication/download/`

Machine-readable audit:
`registry/b02_tabula_thermal_distribution_audit.csv`

## National statistics availability result

The Hungarian EPISCOPE country page explicitly separates heat-supply topics:

- `S-2.1 Centralisation of the heat supply (for space heating)` — available;
- `S-2.2 Heat distribution and storage of space heating systems` — **not marked available**;
- `S-2.3 Heat generation of space heating systems` — available.

The underlying references are historical Hungarian statistical sources, including the 2001 census and the 2010 Household Budget and Living Conditions Survey. These may provide building-stock context but are not current household technical-readiness observations.

The decisive result for B02 is the `S-2.2` gap. An available heat-generator distribution cannot be transformed into a radiator/floor-heating/fan-coil distribution, pipe topology, hydraulic balancing state, design supply temperature or heat-pump readiness.

## Brochure result

The national typology brochure is a modelling/typology document. It states that, for building services, the modelling uses the solution considered most characteristic for the given building type, and it warns that reliable results for an individual building require professional assessment.

The building display sheets provide typical heat-generation system descriptions such as constant-temperature or condensing gas boilers. Those descriptions are useful context for building archetypes, but they are not a national observed emitter inventory.

During the B02-P5 audit:

- no source-native text field proving current emitter type was identified;
- no explicit design supply/return temperature pair was identified;
- a radiator-like schematic visible on a display sheet is treated as illustration, **not** as `OBS` current-emitter evidence;
- boiler type does not authorize a supply-temperature inference.

Therefore the brochure is `CONTEXT_ONLY` for the B02 technical gate.

## Effect on existing gaps

### `GAP-B02-S2-HEAT-EMITTER`

Remains `Q/GAP`.

TABULA/EPISCOPE does not provide the missing national current-emitter distribution required to open the B02 technical eligibility gate.

### `GAP-B02-S2-DESIGN-TEMPERATURE`

Remains `Q/PARTIAL`.

The Hungarian legal 55/45 °C reference remains a calculation/reference condition, not observed building data, and the TABULA brochure does not supply a stock-level observed design-temperature distribution.

### `GAP-B02-S2-HYDRAULIC`

Remains `Q/GAP`.

The explicit absence of Hungarian `S-2.2` heat-distribution/storage statistics prevents TABULA from acting as national hydraulic-readiness authority.

## Remaining evidence path

The primary unresolved path remains the already-contracted OÉNY request/pilot:

- structured or document-backed current emitter evidence;
- explicit supply/return temperature with evidence basis;
- later representativeness proof before any national prevalence estimate.

If OÉNY cannot supply these fields, the fallback remains a separately designed representative technical survey stratified by building type, construction period, settlement type and heating mode.

`Q-B02-004` therefore remains OPEN.

## History snapshot and reuse

The TABULA/EPISCOPE download page states that third-party use of the TABULA approach, data and files in research projects and software applications is intended and desired, with visible attribution to `IEE Projects TABULA + EPISCOPE (www.episcope.eu)`.

Accordingly, repository-copy reuse is treated as cleared subject to that attribution requirement.

History manifest:
`evidence/history/SRC-B02-TABULA-HU-TYPOLOGY-BROCHURE-2014/manifest.csv`

The binary PDF itself is intentionally still `PENDING_BINARY_ACQUISITION`: the current connector/runtime cannot persist the exact bytes into Git without using the repository-prohibited base64 workaround. No SHA-256 is fabricated. A later local/Codex acquisition must copy the PDF byte-for-byte, calculate its SHA-256 and update the manifest.

## Readiness impact

No readiness uplift.

- physical screening reference remains 3,389,817 DER;
- national technical eligible count remains blank/Q;
- `Q-B02-001` remains OPEN;
- `Q-B02-004` remains OPEN;
- B02 readiness remains 55%.
