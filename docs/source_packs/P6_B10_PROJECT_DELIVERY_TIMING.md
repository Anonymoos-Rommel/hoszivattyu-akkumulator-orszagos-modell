# B10-P6 — Project delivery timing & fulfilment evidence gate

## Purpose

B10-P6 separates four different timing concepts that must not be collapsed:

1. a source-native planned completion date;
2. a source-native expected/committed completion date published before completion;
3. an observed actual completion date;
4. a calibrated future completion probability.

Only the first three are currently evidenced. The fourth remains Q.

A retrospective schedule difference is not a fulfilment probability.

## Canonical boundary

The executable contract is `modules/B10/project_delivery_timing_contract.py`.

Source-native timing claims use:

- `PLANNED_COMPLETION`;
- `EXPECTED_COMPLETION`;
- `ACTUAL_COMPLETION`.

Planned/expected targets must also state whether the repository has a verified
pre-completion snapshot:

- `EX_ANTE_VERIFIED` — the source publication date proves the target existed
  before the claimed completion date;
- `CURRENT_PAGE_ONLY` — the current official page states a target date, but the
  repository has not proven that the same value existed before completion.

Actual completion uses `NOT_APPLICABLE` for snapshot status and must be
source-native `OBS`.

A schedule variance may be `DER` only when an `EX_ANTE_VERIFIED` target and a
separately evidenced `ACTUAL_COMPLETION` refer to the exact same project and
network operator.

No numeric completion probability is permitted in P6. A later model would need
an explicit calibrated project cohort, methodology, calibration date, scope and
source authority. Two completed projects are not a probability model.

## MVM Démász RRF project

Project:

`RRF-6.1.1-21-2022-00006`

The current official MVM Démász project page states:

- project identity and beneficiary;
- a planned completion date of `2026-04-30`;
- the project development scope.

The official MVM completion communication separately establishes successful
completion on `2026-06-15`.

P6 deliberately does **not** calculate a 46-day forecast error from those two
dates. The current project page is live and may have been edited after project
completion; the repository does not possess a version-pinned pre-completion
snapshot proving that `2026-04-30` was the exact target published before the
completion event.

Therefore the MVM timing ledger records:

- target date: `2026-04-30`;
- target snapshot: `CURRENT_PAGE_ONLY`;
- actual completion: `2026-06-15`;
- schedule variance: blank / `Q`;
- completion probability: blank / `Q_NO_CALIBRATED_DELIVERY_MODEL`.

This is a deliberate fail-closed distinction between a current source-native
statement and historical forecast-performance evidence.

## OPUS TITÁSZ RRF project

Project:

`RRF-6.1.1-21-2022-00001`

Official OPUS TITÁSZ communication dated `2024-09-30` states that, under this
exact RRF project, the company undertook a 378 MW network-capability objective by
`2026-04-03` and expected to meet or exceed that objective by that date.

Because the communication itself is dated before the target, this is an
`EX_ANTE_VERIFIED` timing claim.

The separate official completion communication establishes project completion
on `2026-06-15`.

For timing only, P6 may therefore derive:

`2026-06-15 - 2026-04-03 = 73 days`

The 73-day value is `DER`. It is a deterministic retrospective calendar
difference between two exact source-bound dates. It is not:

- a general OPUS delay factor;
- a DSO project-duration model;
- a completion probability;
- a programme implementation probability;
- a national timing assumption.

## Source authority

Existing P4 sources remain authoritative for the two actual completion events:

- `SRC-B10-MVM-DEMASZ-RRF-COMPLETION-2026`;
- `SRC-B10-OPUS-TITASZ-RRF-COMPLETION-2026`.

The existing MVM project source remains the current-page authority for the
`2026-04-30` planned date:

- `SRC-B10-MVM-DEMASZ-RRF-PROJECT-2026`.

P6 adds one exact ex-ante OPUS timing source:

- `SRC-B10-OPUS-TITASZ-RRF-TIMING-2024`;
- publisher: OPUS TITÁSZ Zrt.;
- publication date: `2024-09-30`;
- project: `RRF-6.1.1-21-2022-00001`;
- expected/undertaken target: `2026-04-03`.

No raw source document is committed.

## Relationship to P3/P4/P5

P6 does not change B10-P3 attribution status or cost authority.

P6 does not alter the two P4 `OPERATING` baseline rows or their cost semantics.

P6 does not use P5 headroom screening as a project schedule signal. Published
headroom, MGT process timing and project delivery timing remain separate
concepts.

## Q-B10-002

P6 changes Q-B10-002 from completely unbounded to **OPEN / PARTIALLY_BOUNDED**
semantically:

Bounded now:

- exact source-native target-date claim types;
- exact source-native actual completion dates;
- distinction between verified ex-ante and current-page-only target evidence;
- deterministic retrospective schedule variance where both dates are valid.

Still unresolved:

- representative historical DSO project cohort;
- status-transition history;
- procurement/construction-stage conditional probabilities;
- calibrated delivery-probability method;
- forward timing model for future reinforcement projects;
- national/regional timed investment path.

The registry question status remains `OPEN` because the probability model is not
solved.

## Readiness

B10 readiness remains 15.

P6 adds a timing evidence contract and two bounded real-project timing rows, but
it does not solve programme-demand-to-node mapping, future reinforcement scope,
regional CAPEX, national DSO coverage or a calibrated timed investment path.

## Explicit exclusions

P6 does not create:

- completion probabilities;
- delay multipliers;
- average DSO delivery duration;
- national schedule assumptions;
- project-start dates where not directly sourced;
- construction-stage interpolation;
- future reinforcement schedules;
- programme rollout dates;
- programme CAPEX;
- new baseline projects.
