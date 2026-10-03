# V1 evidence and feasibility execution contract

Status: OWNER-AUTHORIZED EXECUTION PLAN, 2026-10-01. This branch implements the approved V1 research plan. It does not authorize merging, releases, repository-security changes or changes to the evidence-quality threshold. Existing canonical evidence, population-inference and V1.2 portfolio-transition policies remain authoritative.

## Purpose and claim boundary

Deliver a sourced, reproducible, conditional Hungarian national feasibility calculation suitable for academic and governmental technical discussion, including potential funding discussions. It must cover the complete B01–B20 result chain: household, fiscal, financing, macroeconomic, environmental and execution consequences. It is not construction approval, a household eligibility determination or a promise of funding.

Use E1 when readily available and acceptable E2 with explicit validation debt otherwise. An E2 label is not a populated input. Three publications are not three independent sources if they share the same original observation. Legal, tariff and named-site/network authority cannot be inferred from averages.

The 58 identifiers in `registry/v1_research_plan.json` organize the approved work, not 58 additional gates before the first calculation. Reuse existing accepted data and group coherent changes into small reviewable patches. A slice may close through verified reuse; no new code, source or commit quota is required.

## Stages and dependencies

1. Establish the shared target population, temporal/unit conventions and explicit POL/SCN assumptions. The proposed 2025 observed energy year, 2022 stock bridge and 2026 monetary basis require input-specific suitability checks; they do not silently replace existing source periods.
2. Materialize the B01–B11 minimum physical, price and network handoffs with supported E1/E2 data or legitimate POL/SCN values. Do not require every later exact research question to close.
3. Establish the B12 complete input/accounting contract: costs, tariffs, lifetime, financing and affordability. B12 computation follows this entry contract; requiring B12 results before starting B12 is circular.
4. B12 household cash flow, B13 fiscal ledger and B14 current funding map may proceed in parallel on accepted upstream inputs. B15 remains blocked until all three have sourced numerical outputs, as the charter requires.
5. B16–B19 results feed back into feasible rollout; B18 capacity evidence cannot be deferred past a claimed feasible schedule. Re-run the connected model after material B10/B13/B18 feedback.
6. B20 delivers a stable reproducible input/output package. A final interactive application remains separately gated by the existing charter.

Slice phase `A` denotes the initial data/physical minimum, `V` the complete V1 stage, and `V↔A` later execution-capacity evidence that also constrains early rollout. E2-to-E1 upgrades are a separate sensitivity-ranked debt queue, not a prerequisite to every provisional computation.

## Data acceptance and research lifecycle

Each material input must identify quantity, unit, temporal and geographical grain, reference period, target population/product/system boundary, source lineage and reuse rights. Apply all eight E2 criteria in the existing evidence policy; retain stronger contradictions and Hungarian applicability checks. Preserve correlated uncertainty and historical joint events. Do not manufacture a joint distribution from unrelated marginals or build an automatic low/base/high Cartesian source-gap grid.

For each slice:

- Inspect and reuse existing canonical source IDs, artifacts and consumers before new acquisition.
- Extract or derive reproducibly, recording retrieval time, source revision, normalization and uncertainty. A landing page is only an acquisition lead.
- Integrate accepted data into its actual consumer and test unit/time/boundary compatibility, missingness, conservation and relevant sensitivity.
- Record evidence debt and downstream effects. Close only after reviewing the exact changed content and its applicable tests; a research link or passing schema test alone is insufficient.
- Follow canonical authority and the owner-approved quality criteria for routine data admission. Do not introduce a new owner-per-datum approval gate. Ask for a decision only when scope, core claims, evidence-quality threshold, paid acquisition or external-contact authority changes.

Plan states are `NOT_STARTED`, `RESEARCHING`, `INTEGRATING`, `REVIEW_REQUIRED`, `ACCEPTED`, and `PAUSED`. A pause does not mean completion. For each research log entry record date, source families inspected, remaining unknown, promising next lead, expected decision value and the reason to continue/pause/close. The journal must contain only public-safe research facts, not private conversations or raw telemetry.

Continue when there is a concrete new promising source or method with material expected decision value. Complete when predefined applicability/evidence acceptance is met and the data is integrated and tested. Pivot or pause when leads repeat the same original, rights/access prevent use, or further search has no material expected decision value. There is no fixed query/iteration quota and no unbounded search requirement. A required E3 input remains a blocker; do not silently reduce the promised V1 scope to evade it.

## Boundaries and publication

Only genuinely public, cost-free and reuse-appropriate acquisition is in this execution scope. Do not depend on custom statistical delivery. Do not publish private raw telemetry, personal information, internal correspondence or uncleared external document copies. Preserve external-only provenance when redistribution is not cleared, following `AGENTS.md`.

Use one `agent/` authoring branch, small commits and a draft PR. Never force-push shared history, push directly to main, merge or change security/production settings. Record exact head and checks at review checkpoints. Keep passed, failed and never-run checks distinct. A local suite pass is not live-source or national-result validation.

## Initial checkpoint and known defects

Baseline: `144c0d96cee674fbea4bf951826e68f000b45705`. This adoption changes planning only: no source is promoted, no blocker is closed, no module readiness score is raised and no national result is asserted. B12–B20 requirements in the plan are proposed operational contracts for currently unstarted modules, not claims that those modules already exist.

Prior component audit identified separately interpolated B05 Q/P/COP inconsistency at Stiebel A−2/W40 (a component issue, not an estimated national error). B10 national cohorts/annual incremental CAPEX remain unpopulated. These require evidence/consumer fixes rather than status relabelling.

References: [charter](../../PROJECT_CHARTER.md), [evidence policy](evidence_tier_and_validation_debt_policy.md), [population inference](population_inference_policy.md), [portfolio contract](v12_portfolio_transition_contract.md).
