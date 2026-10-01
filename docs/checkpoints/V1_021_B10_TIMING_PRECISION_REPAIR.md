# V1-021 — B10 timing and project-status precision repair

Date: 2026-10-01 UTC. Scope: factual precision repair within V1, without a new
national timing value, readiness uplift, source-byte republication or main merge.

## Source-supported correction

- MVM Démász `RRF-6.1.1-21-2022-00006`: the current project page states a
  planned 2026-04-30 finish. The 2026-06-15 news publication reports completed
  works by publication. Exact completion, energization and last-asset in-service
  dates remain Q. The target's historical revision remains unverified.
- OPUS TITÁSZ `RRF-6.1.1-21-2022-00001`: the project page explicitly states
  project completion 2026-06-15. The 2024-09-30 target source binds 2026-04-03 to
  378 MW additional transfer capability and separately reports 376.409 MW
  already achieved. Completion news reports 261 MW integration capability.
  Same-milestone/scope correspondence is unresolved. The previous 73-day
  performance variance is withdrawn; calendar subtraction does not prove delay.
- Neither umbrella completion source proves all assets OPERATING or an exact
  physical in-service transition. `PROJECT_COMPLETED_REPORTED` preserves the
  source-native project-lifecycle fact, and `REPORTING_AS_OF_DATE` qualifies the
  common reporting date. Physical operating coverage/date remain Q.
- `WITHOUT_PROGRAM` baseline attribution remains separate. OPUS's exact
  41,489,280,000 HUF baseline project cost is preserved from its project page.
  MVM exact total cost remains blank; neither project acquires incremental cost.

All dates, capacities and declared amounts above are source-native OBS within
those stated scopes. No population inference or delay calibration is derived.

## Evidence lineage and date authorities

Current source IDs, original URLs, retrieval timestamps, current-byte SHA-256,
prior metadata and source-specific claim boundaries are recorded in
`registry/b10_timing_source_review_manifest.json`. This inspection verifies the
retrieved 2026-10-01 revisions; it does not prove that mutable pages had identical
contents when originally published. Raw external HTML remains outside Git and
is not cleared for public redistribution.

The OPUS completion article body is undated. Its publication date comes from the
separately referenced `SRC-B10-OPUS-TITASZ-NEWS-INDEX-2026`. The exact OPUS
project-completion date comes from `SRC-B10-OPUS-TITASZ-RRF-PROJECT-2026`, not
from the news index or article. MVM news directly carries its publication date.

## Executable and schema boundaries

1. P3 accepts source-supported `PROJECT_COMPLETED_REPORTED` as an independent
   baseline lifecycle fact, requiring an explicit reporting/as-of date basis.
   This does not satisfy an `OPERATING` evidence claim.
2. P4 materializes that lifecycle status, separately binds project cost,
   completion reporting and publication-date authority, and rejects any attempt
   to label the umbrella evidence OPERATING. `RRF_REPORTING_DATE` replaces the
   unsupported shared `RRF_COMPLETION_DATE` name.
3. P6 now requires explicit milestone, physical/programme/quantity scope and
   source binding, date relation, day precision and date authority. Exact
   events and completed-by upper bounds are different outputs. Old untyped
   records remain constructible but cannot mint exact events or variance.
4. DER variance requires matching project/operator and source-bound milestone
   and scope, exact target/event dates, and a dated ex-ante target source that
   predates or coincides with the event. Actual event existence does not depend
   on an ex-ante target. Both current real-project variances remain Q.
5. P11 physical delivery additionally requires a matching intended physical
   scope and explicit source-bound correspondence to the P5 project's exact
   operator, substation, infrastructure type and cost component. A matching
   target/actual pair for another P5 scope remains Q. A physical event for a different phase cannot complete the target.
   Project completion/bounds remain separate reporting fields; administrative
   variance cannot populate physical delay fields. P11/P33 still require
   independent complete CAPEX cash-flow evidence. Date-only inputs yield no
   cashflow; separately proven schedules retain their own periods.
6. The baseline and timing registry headers add these precision/provenance
   qualifiers. `tools/validate_registry.py` pins the supported two-project
   claims and rejects the former operating/date/delay overclaims.

## Validation

Executed on the bounded candidate, without the heavy repository-wide suite:

- `python -m unittest discover -s tests -p 'test_b10*.py' -q`: 701 tests passed
- `python -m unittest discover -s tests -p 'test_registry_contract.py' -q`:
  15 tests passed
- `python tools/validate_registry.py`: valid
- `git diff --check`: passed

Regression coverage includes exact source-declared project completion,
completed-by bounds, publication-date substitution rejection, missing ex-ante
source authority, wrong milestone/phase/quantity scope, wrong-phase and matching-wrong-pair physical
P11 delivery, source-bound RRF row reproduction, OPUS index provenance, stable
cost attribution, and P11/P32/P33 cashflow separation. The generic 73-day
arithmetic fixture is explicitly synthetic and has matching physical scope;
it is not evidence for OPUS performance.

Focused tests are not a full-suite or hosted-CI verdict. Independent review and
aggregate verification bind to the final candidate bytes/commit separately.
B10 readiness remains 15; Q-B10-001 and Q-B10-002 stay OPEN. Representative
cohort acquisition and calibrated timing inference remain separate work.
