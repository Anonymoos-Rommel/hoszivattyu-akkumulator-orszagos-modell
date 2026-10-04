# V1-059: dated gas-quality and household-control handoff

This checkpoint supplies a bounded B11-D02 native source/control consumer. It does not establish a national residential gas-quality estimate, a physical conversion or an actual household bill. Whole-task acceptance is a separate, actual-commit-bound step.

## What the source handoff establishes

The original B11-D02 task asks for gas-quality quantities and reference conditions, their spatial/time scope, and annual Hungarian residential sales and end-use controls. The qualified sources can supply these as a dated inventory. They do not yet identify a national residential physical heating-value distribution or an actual household bill.

Two FGSZ exit-point panels remain separate. The 2025/26 revision 4 document was issued on 31 March 2026 and is effective from 1 April to 30 September 2026; its table observations are calendar 2024. The 2026/27 revision 1 applies from 1 October 2026 to 30 September 2027 and its exit table reports calendar 2025. Its contents and composition captions cannot override each table's actual year. The separately published 2024/25 gas-year panel is another period and is not substituted for a calendar year.

The original workbooks and PDF tables agree at the source display precision. Agreement between two representations from the same publisher is a transcription control, not independent physical validation. Native missing cells, overlapping group and child points, virtual, storage and export sections, and source extrema inconsistencies remain visible. The inventory is not a disjoint residential sample, so rows are not summed or assigned equal population weights.

FGSZ labels the NCV values as informative. GCV uses a 25/0 degree Celsius calorific/volume reference and kWh per cubic metre; NCV uses 15/15 degrees Celsius and MJ per cubic metre. Unit rescaling by 3.6 does not align their reference states. The inspected source does not supply the moisture declaration needed by the existing physical-conversion contract. The handoff therefore does not instantiate that contract or replace TABULA's 0.92 source convention.

The visibly inconsistent cross-border equation in the source is retained as a source defect and excluded from operational use. Source-prescribed accounting factors, their applicability dates and their specific purposes are distinct from the historical point observations. This consumer does not create a new physical conversion or choose a national coefficient.

## Household controls and unresolved differences

The existing county gas-sales consumer supplies the 2024 KSH county/capital inventory and its national controls. The original yearbook is bound separately. Its definition excludes gas boilers serving multiple dwellings from the household gas category. The volume reference state is not established by the inspected table and scope note.

The separately published KSH annual mean implies a different total from the yearbook sales control. Both statements remain attributed to their own source and metric; no mean of the two, silent preference or population bridge is introduced. The existing source-native county rounding difference is retained.

Eurostat household end-use, energy-balance and gas-commodity series retain their exact dimensions, units, missingness, quality statuses and different update dates. Heating, water heating and cooking remain separate from useful heat and from the selected programme stock. Native TJ and TJ_GCV labels are not converted into a claim of matching physical calorimetric reference states. The near-0.90 statistical reconciliation and end-use rounding residual are descriptive checks, not a measured gas-quality ratio or a replacement for the existing source convention.

The reader must refuse unsupported study periods and physical/national promotion. Comparing these controls does not authorize dividing unmatched household energy by KSH volume to manufacture an observed heating value. An aggregate application needs compatible population coverage, reference states, weights and uncertainty; an exhaustive household-to-point census is not required.

## Source use and preservation

The current intended use is this owner's private personal source analysis. FGSZ's notice leaves that use available; it does not establish a broader content redistribution or deployment licence. Our own code, synthetic tests and restrained factual source provenance are distinct from publishing the source content. Original documents, workbooks and the detailed numerical output remain external-only in private preservation.

All material source artifacts have exact retrieval and byte identities. The 2019 Energy Balance Guide was inspected through the official web reference, but its original binary is not retained; that evidence remains explicitly web-only. The distinct 2025 questionnaire user manual is not relabelled as an energy-balance methodology authority. No unsupported binary hash or source-specific HHQ calorific basis is invented.

## Acceptance and validation boundary

The independent source/criterion map supports a complete bounded D02 handoff once an actual consumer and its output are independently verified. Source qualification alone is not acceptance. B11 module-wide gas displacement, sales calibration, actual billing, national selection and programme impacts remain separate claims and gates.

The implementation binds every required original source and inherited consumer before producing a private output. Synthetic tests, a genuine unmocked source replay, independent comparison against the frozen preimplementation oracle, registry validation and canonical tests are recorded in the accompanying verification record. The public research-plan status stays review-required until separately approved publication, actual zero-skip hosted validation and any approved conditional acceptance step.

## Reproduction

The source reader is `modules.B11.gas_quality_reference.read_gas_quality_reference`.
It requires an exact artifact-ID to local-path mapping and the explicit
`historical_scope=CALENDAR_2024_SOURCE_AND_CONTROL_HANDOFF`. The calendar-2025
panel is a separate later reference; it is not joined to the 2024 controls.
All thirteen original artifacts and the six existing source-consumer/data
dependencies must match their pins. The KSH county and Eurostat end-use
consumers are reused; their canonical code and data are unchanged.

The source-map JSON is one object mapping each manifest `artifact_id` to an
explicit local filename. It contains no source-content upload instruction or
automatic network request. From an exact Git checkout, use a fresh ignored
private output directory:

```sh
python tools/materialize_b11_gas_quality_reference.py \
  --source-map /private/path/source_map.json \
  --historical-scope CALENDAR_2024_SOURCE_AND_CONTROL_HANDOFF \
  --output-dir data/interim/b11_source_reference
```

The unchanged private-output guard rejects public/tracked storage, symlinked
destinations and overwrites. Validation is completed before output creation.
The full receipt retains both panels, source lexemes and display formats,
missingness and QC flags, inherited controls and unresolved diagnostics. It is
written with private permissions and is not a public repository artifact.
