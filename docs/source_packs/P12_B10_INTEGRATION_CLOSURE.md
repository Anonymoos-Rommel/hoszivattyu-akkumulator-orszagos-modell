# B10-P12 — Integration / closure gate

Canonical base: `c554193430bd979243db93620fbdc1454d4d6b84`

## Core rule

`CONTRACT BOUNDED != REAL EVIDENCE POPULATED != PRIMARY OUTPUT POPULATED != ACCEPTANCE SATISFIED != MODULE CLOSED`

P12 adds no external network fact and no new numeric model output. It is a
repository-state integration audit over the canonical B10 P1-P11 contracts,
registries and Issue #10 acceptance wording.

The current executable assessment is:

`B10_CLOSURE_BLOCKED`

B10 therefore remains `IN_PROGRESS`, readiness remains 15%, and Issue #10 must
remain open.

## Issue #10 acceptance audit

Issue #10 requires:

1. transmission and distribution constraints separated;
2. regional penetration and hosting/receptivity;
3. managed peak and physical survivability;
4. timed investment pathway;
5. `Q-05` and `Q-07` handled.

P12 deliberately distinguishes a bounded authority contract from a populated
acceptance result.

### 1. Transmission / distribution separation

Status: `CONTRACT_BOUNDED`.

B10-P7 explicitly separates `TRANSMISSION`, `DISTRIBUTION` and
`COORDINATED_TSO_DSO` from voltage, operator identity, attribution and programme
causality. This is the correct authority boundary, but it is not a complete
national inventory of transmission/distribution constraints or projects.

### 2. Regional penetration and hosting

Status: `Q_UNRESOLVED`.

B10-P8 separates administrative geography, DSO service area and exact
`DSO_SUBSTATION` topology. B10-P9 admits programme demand only through an exact,
complete entity-by-timestamp panel at P8-proven nodes.

Still missing:

- complete national DSO coverage;
- reproducible canonical geography / DSO correspondence (`Q-B01-002` remains
  `OPEN`);
- populated real programme node-demand panel;
- populated regional hosting/readiness outputs.

`registry/regional_readiness.csv` remains header-only.

Published headroom remains screening evidence, not a general hosting-capacity
claim.

### 3. Managed peak and physical survivability

Status: `CONTRACT_BOUNDED`.

B10-P10 separates physical flexibility capability, commitment, activation,
delivery, managed node load and network survivability. Managed load requires
exact P9 lineage, while survivability requires a separate claim-specific
DSO/network study.

Still missing:

- a real programme entity-by-timestamp node panel;
- real delivered programme flexibility / managed-peak population;
- claim-specific real survivability studies covering the programme nodes.

The contract exists; the acceptance output is not populated.

### 4. Timed investment pathway

Status: `CONTRACT_BOUNDED`.

B10-P11 separates project delivery dates from CAPEX spend dates and requires a
complete, exact project/operator/node/component/schedule/period-bound cash-flow
authority before programme-incremental CAPEX may be periodised.

Still missing:

- real programme-specific reinforcement records;
- real programme-incremental CAPEX rows (`Q-B10-001` remains `OPEN`);
- calibrated forward fulfilment/timing model (`Q-B10-002` remains `OPEN`);
- complete authoritative programme CAPEX cash-flow schedules.

`registry/incremental_capex_attribution.csv` remains header-only.

### 5. `Q-05` and `Q-07`

Status: `LEGACY_LABEL_UNRESOLVED`.

The current repository has no globally unique canonical question IDs named
`Q-05` or `Q-07`. `docs/methodology/question_identifiers.md` explicitly explains
that short `Q-xx` labels from internal briefs are ambiguous and must not be
silently reused or guessed.

The known V1.2 mappings include `H-15 -> Q-B10-001` and
`Q-19 -> Q-B10-002`; they do **not** establish any mapping for the Issue #10
labels `Q-05` or `Q-07`.

P12 therefore refuses to infer a mapping. Issue #10 cannot satisfy this
acceptance row until the legacy labels are explicitly mapped to canonical
question IDs or the acceptance wording itself is canonically corrected.

## Primary-output audit

Issue #10 names four primary outputs. None is currently populated at the
programme/regional closure level:

| Output | P12 status | Reason |
|---|---|---|
| Regional CAPEX | `Q_UNRESOLVED` | P3/P5/P11 authority exists, but the programme incremental CAPEX registry is header-only. |
| Regional timing | `Q_UNRESOLVED` | P6 has two bounded baseline examples; P11 has no real programme timed-CAPEX schedule. |
| Connection demand | `Q_UNRESOLVED` | P9 is executable, but no complete real programme node panel is canonical. |
| Limiting nodes | `Q_UNRESOLVED` | P1/P2 headroom is source-native screening; there is no complete national coverage plus real managed-load/survivability population. |

Missing is not zero. A header-only registry is not an empty-value national
result; it means the output has not been populated canonically.

## Canonical blockers carried by P12

At minimum:

- `Q-B01-002` — OPEN;
- `Q-B10-001` — OPEN / partially bounded;
- `Q-B10-002` — OPEN / partially bounded;
- `LEGACY:Q-05` — unmapped;
- `LEGACY:Q-07` — unmapped;
- no national DSO coverage;
- `regional_readiness.csv` header-only;
- `incremental_capex_attribution.csv` header-only;
- no real programme node panel;
- no real managed-peak + survivability-study population;
- no real timed programme CAPEX pathway.

## Why P12 does not raise readiness

P1-P11 materially improve the **safety and authority architecture** of B10. They
prevent false national headroom, false reinforcement, false programme CAPEX,
false managed-peak benefit and false investment timing.

However, readiness is not a count of completed contracts. The primary model
outputs are still unpopulated and the critical data/evidence questions remain
open. Raising readiness solely because the fail-closed gates exist would confuse
model architecture with empirical coverage.

Therefore:

- B10 status remains `IN_PROGRESS`;
- B10 readiness remains `15`;
- no Issue #10 checkbox is rewritten by P12;
- Issue #10 remains open;
- no `regional_readiness.csv` row is added;
- no `incremental_capex_attribution.csv` row is added;
- no national CAPEX, hosting, managed-peak or limiting-node value is invented.

## What would be required for a future closure

A later closure candidate must explicitly re-audit, at minimum:

1. canonical mapping/resolution of the Issue #10 legacy `Q-05` / `Q-07` labels;
2. resolution of the spatial/coverage boundary needed for regional programme
   demand;
3. populated real or explicitly authoritative scenario programme-node demand;
4. managed-peak and claim-specific survivability evidence at the required nodes;
5. programme reinforcement attribution and separable programme-incremental
   CAPEX;
6. authoritative or explicitly bounded timed CAPEX schedules;
7. populated primary outputs at their declared regional grain;
8. all remaining closure-critical canonical questions resolved or explicitly
   accepted as non-blocking by a documented authority.

Until then the correct result is `B10_CLOSURE_BLOCKED`.
