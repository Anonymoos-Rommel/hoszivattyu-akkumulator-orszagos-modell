# B10-P6 — Project delivery timing and evidence precision

## Canonical boundary

The executable contract is `modules/B10/project_delivery_timing_contract.py`.
Source-native target, event and reporting claims are OBS; compatible date
subtraction is DER. Missing performance/physical evidence remains Q.

The following evidence objects are separate:

1. A source-stated planned/expected target date
2. A report that a project was completed by its publication date
3. An exact source-declared project-completion date
4. An exact physical in-service/energization event
5. A future completion probability from a calibrated model

Only the first three are evidenced for the two current RRF rows. Neither
umbrella source proves all components physically operating or the last asset's
energization. Source-reported aggregate generation-integration capability is
preserved separately from consuming headroom and operational coverage.

## Required date and scope semantics

`ProjectTimingEvidence` retains `PLANNED_COMPLETION`, `EXPECTED_COMPLETION` and
`ACTUAL_COMPLETION`, but claim type alone cannot prove exact event timing.
Every admissible comparison needs:

- `milestone_type`: `PROJECT_COMPLETION`, `CAPABILITY_TARGET` or
  `PHYSICAL_IN_SERVICE`, with `UNSPECIFIED` fail-closed by default
- `scope_id` and `scope_source_id`: the source explicitly binds that milestone
  and physical/programme/quantity scope; project/operator identity is insufficient
- `date_relation`: `EXACT`, `ON_OR_BEFORE` or `OPEN`
- `date_precision`: explicit `DAY` for bounded dates
- `date_authority`: `SOURCE_STATED_TARGET_DATE`, `SOURCE_STATED_EVENT_DATE` or
  `PUBLICATION_REPORTING_BOUND`
- Publication date, independently of claimed event/target date

A publication reporting bound cannot be declared `EXACT`. It supplies only an
upper bound, never an invented lower bound or exact actual date. The registry
preserves `actual_claimed_date` and event bounds separately. The OPUS project
page's publication date is unknown and blank; its explicit event date remains
valid. The separately dated news report is a different source authority.

Legacy records missing these qualifiers remain constructible, but their exact
completion, physical timing and schedule variance fail closed. No numeric
completion probability is permitted in this slice.

## Variance admission

DER variance requires all of the following:

- Exact project and operator correspondence
- Exact, compatible milestone and scope explicitly bound in both cited sources
- An exact source-stated target with `EX_ANTE_VERIFIED` authority and a known
  publication date no later than the event
- An exact source-stated actual event date

Only then is `actual_date - target_date` a same-milestone variance. A negative
value is allowed; a probability is never inferred. `CURRENT_PAGE_ONLY` cannot
prove a historical forecast. Matching source identifiers or calendar arithmetic
alone do not establish semantic correspondence. Synthetic test fixtures provide
explicit matching physical scope; their arithmetic does not validate real RRF
performance claims.

## MVM Démász: RRF-6.1.1-21-2022-00006

`SRC-B10-MVM-DEMASZ-RRF-PROJECT-2026` states planned project completion
2026-04-30. The current page is not a verified historical target revision.

`SRC-B10-MVM-DEMASZ-RRF-COMPLETION-2026` is a completion report published
2026-06-15. It reports successful completion and aggregate capability, without
separately dating completion, commissioning or last-asset energization.

Therefore:

- Target: 2026-04-30, `CURRENT_PAGE_ONLY`
- Project completed-by upper bound: 2026-06-15, `ON_OR_BEFORE`
- Exact actual date and lower bound: blank/Q
- Physical in-service date: blank/Q
- Historical target-scope correspondence: `UNRESOLVED`
- Schedule variance and probability: blank/Q

The publication date is not substituted for an event date.

## OPUS TITÁSZ: RRF-6.1.1-21-2022-00001

`SRC-B10-OPUS-TITASZ-RRF-TIMING-2024`, published 2024-09-30, binds
2026-04-03 to a 378 MW additional-transfer-capability objective. It also reports
376.409 MW already achieved by that communication. This is dated ex-ante target
authority, not a dated target for last-asset energization or project closure.

`SRC-B10-OPUS-TITASZ-RRF-PROJECT-2026` explicitly declares project completion
2026-06-15. It is the exact date authority and must be referenced by the timing
row. It continues to state a 378 MW project-page capability figure.

`SRC-B10-OPUS-TITASZ-RRF-COMPLETION-2026`, dated 2026-06-15 in the official
news index (`SRC-B10-OPUS-TITASZ-NEWS-INDEX-2026`), reports project completion and 261 MW additional weather-dependent
integration capability. The 378 MW, interim 376.409 MW and reported 261 MW
claims have no verified scope/definition/revision bridge in this slice.

Therefore exact source-declared project completion is preserved, while
`pairing_status=UNRESOLVED`, schedule variance blank/Q and physical delivery
blank/Q. The former 73-day value is withdrawn as a performance claim. Although
the calendar subtraction is arithmetically correct, it does not establish a
like-for-like target-fulfilment or physical-delivery delay and has no machine
performance field.

## Downstream boundaries and acquisition

P3/P4 retain independent `WITHOUT_PROGRAM` baseline attribution, the bounded
`PROJECT_COMPLETED_REPORTED` status and separately sourced OPUS exact cost.
Neither row is relabelled under construction, merely budgeted or operating.

P11 retains project-completion reporting separately from physical delivery.
Matching physical target/actual scope is also explicitly bound to the exact P5
substation/infrastructure/component key; pair equality cannot stand in for that
cross-contract correspondence.
Administrative variance cannot enter P11 physical delay fields. P11/P33 still
require separately authorised complete CAPEX cash-flow evidence; neither a
project date nor a physical delivery date can assign expenditure to a period.
No P32 amount or P33 schedule is generated by these two RRF rows.

Q-B10-002 remains OPEN / PARTIALLY_BOUNDED and readiness remains 15. To restore
real performance comparisons, acquire MVM's historical target revision and exact
same-event date, and OPUS's achieved-date evidence for the precise 378 MW target
or an ex-ante target for the exact project-completion milestone. Component-level
physical transitions require their own commissioning/in-service evidence. A
representative cohort and calibrated method remain necessary for probabilities.

The source-native audit was rechecked 2026-10-01. Current retrieved bytes are
version evidence for that inspection, not proof of the original historical page
contents. No external HTML is committed or licensed for public redistribution by
this repair. See `docs/checkpoints/V1_021_B10_TIMING_PRECISION_REPAIR.md` for the
change and verification boundary.
