# V1.029 — B17-D01 emission-factor source reference

Status: **reference-only candidate; D01 integrating, readiness 0, no accepted artifacts**.
This checkpoint does not admit a programme input or close the B17-D01 evidence gate.
Shared research-plan, source-registry and module-status edits belong to the lead's
subsequent integration review. B17-D02 health and B17-D03 valuation remain open.

## Scope and API

`modules/B17/emission_factor_reference.py` reads one exact external qualified
panel, its exact original panel, the independent qualification, and the original
PDF bytes keyed by the two stable factor-source IDs:

- `SRC-B17-IPCC-2006-STATIONARY`
- `SRC-B17-EEA-SMALL-COMBUSTION-2023`

Call `read_emission_factor_reference(panel_path, original_panel_path,
qualification_path, source_paths)`. The caller supplies paths; filenames never
establish authority. All source, panel and qualification hash/length gates pass
before any factor record is returned. The PDF sources must also have a successful
acquisition status and PDF signature. The exact public manifest has its own
code-pinned SHA-256. No API accepts replacement pins, downloads evidence or writes
an output file. There is no materializer in this checkpoint.

The returned immutable records preserve source coordinate, original ordinal,
stable semantic row identity, fuel/device/sector/tier, pollutant, NCV fuel-input
unit, interval semantics, PM boundary, source/default status, and applicability
limits. Numeric JSON lexemes become exact `Decimal` values without a binary-float
round trip. All 36 central factors and 72 bounds must equal the original panel.
The runtime checks reviewed transcription lineage; it does not re-extract PDF
numbers or independently audit the source's underlying studies.

`read_context_reference(path, source_id)` verifies the exact bytes of one of six
qualified contextual sources and returns immutable provenance metadata only.
It cannot return a factor or select a programme input. The successful official
NID uses the complete ID `SRC-B17-HU-NID-2026-OFFICIAL`. The failed generic
`SRC-B17-HU-NID-2026` is a retained HTML placeholder and cannot be resolved by
alias, title or year. Superseded IIR/NID identities and discovery pages are
historical records, excluded from both consumer entry points.

## External lineage and metadata corrections

The original research pack is retained unchanged outside the repository. The
public manifest publishes provenance, hashes and interpretation contracts, not
original documents or the complete numeric factor panel. Its source records add
explicit titles, authorities, P1 official/P2 primary-industry priority, source-evidence status, document and
reference periods, claim scope, retrieval time, currentness limits and
external-only reuse status. The EEA electricity page records its 10 July 2026
publication date separately from acquisition on 2 October 2026.

Pinned lineage:

- Original factor panel: SHA-256
  `e87212ae2b3e865b808d03d6f31be7cdfe2e976524f7e22137c16ec9fff3f619`,
  31,884 bytes
- Qualified external panel: SHA-256
  `402e7bd4663d5d7689a7bf1d543e9394335e393f628fd293cd72f1f044172d4f`,
  48,367 bytes
- Independent qualified interpretation: SHA-256
  `ab59a5838b71cca37259a434872ba28abc76c8fbd69b1c4c5f1e65836824ff64`,
  6,134 bytes

The manifest also pins the original source manifest, original pack manifest and
independent source review. The runtime requires the original panel and
qualification bytes; the other review/pack hashes document audit lineage rather
than additional runtime inputs. Stable row IDs are source/table/fuel/pollutant
identities, independent of ordinal. The original ordinal and canonical metadata
digest bind each row back to the untouched original panel.

The qualification makes exactly four metadata corrections, with all numbers
unchanged:

1. Original rows 19 and 20 are Table 3-4 Tier 1 gaseous-fuel averages. Their
   corrected abatement wording no longer calls the table Tier 2; it states that
   abatement is unspecified and no numerical adjustment has been selected
2. Original rows 23 and 24 retain Table 3-14's native technology label **Stoves**.
   The pack's narrower “conventional stoves” wording is retained as original
   provenance, not silently promoted to a source-native limitation

Every record separately exposes original abatement and original fuel/device
wording. Actual EEA Tier 2 rows explicitly expose source **NA** independently of
`numerical_abatement_adjustment = NOT_SELECTED`. Neither NA nor retained legacy
pack wording establishes an installed Hungarian device's control status.

## Evidence and downstream boundaries

These are **ASS official method defaults**. Independent verification establishes
retained-source transcription fidelity, not observed Hungarian household
emissions or E1/E2 programme applicability. A later explicit applicability
assessment may support an E2 provisional base; this checkpoint selects none.

- Preserve individual CO2, CH4, N2O, NOx-as-NO2 and PM2.5 mass. Biogenic combustion
  CO2 is a separate physical quantity, never zero or proof of carbon neutrality
- IPCC uses kg of individual gas/TJ NCV fuel input; EEA uses g pollutant/GJ NCV
  fuel input. No GCV/NCV ratio, useful-heat conversion, delivered-electricity
  factor, gas m3 reference-state bridge, GWP or CO2e convention is selected
- Native source intervals remain bounds. No distribution, dependence model,
  national confidence interval or Cartesian source-gap scenario set is implied
- PM filterable-only, total primary including condensables, and unclear
  boundaries remain distinct. PM2.5 is not added to PM10/TSP; emissions do not
  establish ambient concentration, exposure, health or monetary effects
- Hungarian NID coefficients retain their activity-year and sector scope. A
  power-plant table is not residential evidence; the current narrative does not
  establish an exact 2025 residential coefficient. Country-specific lignite
  treatment and Hungarian/IPCC fuel-class differences require a bridge
- Hungarian IIR device allocations require denominator, vintage and energy-share
  reconciliation before weighting. Household/device counts are not fuel-input
  weights. Representative/calibrated population inference is allowed under the
  project policy; exhaustive household microdata are not a prerequisite
- EEA gross-generation GHG averages and AIB production, residual and supplier
  CO2 accounting averages remain distinct contextual references. Gross/net,
  direct/lifecycle and CO2/CO2e boundaries cannot be collapsed. None establishes
  marginal programme response or a physical import-origin trace
- Broad refrigerant inventory assumptions are not selected heat-pump charge,
  leakage, lifetime or recovery inputs. Missing leakage remains unknown, not zero

No factor selection, activity weighting, emission calculation, national
inference, health result, valuation result or programme default is implemented.
The B05/B09/B11 activity, electricity and fuel-input bridges remain necessary for
any later programme consumer.

## Verification

Focused command:

`python -m unittest discover -s tests -p 'test_b17_emission_factor_reference.py' -v`

All 21 tests pass. Fixtures contain synthetic numeric lexemes and synthetic source
bytes only. They cover immutable exact Decimal records, corrected lineage,
source/metadata/row identity, duplicate and malformed JSON/rows, invalid numeric
values, interval ordering, every mandatory evidence pin and length, PDF
signature/acquisition status, historical-ID rejection, contextual-only output,
manifest tampering, and a read-only positive entry-point execution.

Genuine external execution also passes: 36 records and all 108 numeric cells equal
the original panel; the four qualified corrections apply; both original factor
PDFs and all six contextual sources pass their exact pins; all eight
failed/historical/discovery IDs are rejected. All 34 original-pack files are
byte-identical before and after execution. Detailed execution evidence, the
corrected numeric panel, normalization script and exact-byte review freeze remain
outside the repository.

Only focused checks ran at this implementation stage. Full aggregate validation,
independent candidate review, shared-registry integration, commit and publication
are separate lead-controlled steps; this checkpoint claims none of them.
