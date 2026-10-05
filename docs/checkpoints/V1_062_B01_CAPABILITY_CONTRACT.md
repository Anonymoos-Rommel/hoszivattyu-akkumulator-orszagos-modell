# V1-062 – B01 component capability and separate programme conditions

## Problem and resulting behaviour

The historical S0–S5 contract requires consecutive completed gates. Its S1
means demand reduction or justified absence of that work; S4 means generic
flexibility readiness. Those labels do not prove specifically accepted
insulation or a battery, and completion of the full programme does not require
every building to follow one installation order.

B01 now exposes `assess_household_capabilities` as the canonical component
assessment entry point. It composes the rules in
`registry/household_capability_contract.json` and returns independent physical,
action, complete-package, subsidy-exit and operation-condition results. For
example, an accepted battery can be available before the heat pump or envelope
work, while the full programme and subsidy exit remain unresolved. No PV gate
is introduced.

## Scope and evidence semantics

The input is one explicitly identified household, site and configuration /
comparison basis at an ISO date. `CompletionEvent` stores accepted completion
history. `DatedAssertion` stores a claim-specific `PASS`, `FAIL` or `UNKNOWN`
within an explicit half-open validity interval. The source-qualified validity
interval is an input, not an assumed lifetime. Nonoverlapping later assertions
can withdraw operation or availability without deleting completion history.

Actual facts require individual-record `OBS` or `DER` evidence and references.
Scenario facts require `SCN`; unresolved assertions require `Q`. The resulting
conjunction is derived, preserving all contributing input labels and references.
Population estimates, policy intentions and assumptions cannot certify a
specific household, site or legal gate. Facts from another household, site,
basis or truth context cannot be mixed. Overlapping claims, duplicate evidence
identifiers, malformed truthy values and future facts fail validation.

Shared programme eligibility and household-cashflow assertions have an explicit
`applies_to` subject set. An HP-only qualification cannot pass a battery,
envelope, state-service or subsidy-exit condition. Evidence for a whole package
must explicitly name the covered subjects. Overlapping assertions for disjoint
subjects can coexist, but conflicting coverage cannot silently overwrite a
claim. The decoder requires explicit evidence grain and rejects unknown
snapshot fields, including misplaced population scope or legacy provenance.

This is an evidence-contract evaluator. A supplied assertion must already have
been qualified for its exact claim; merely naming a source does not establish
that qualification. The evaluator does not inspect source content or compute
financial flows. Its `PASS` is not a new permission, a selection, an expenditure
authorization, a subsidy payment or an executed intervention.

## Partial order and independent results

1. Battery and envelope acceptance have their own technical/site prerequisites.
   Neither universally requires a heat pump. Heat-pump readiness requires the
   sizing/service, emitter/hydraulic, electrical and actual site conditions for
   the declared building. It does not universally require newly installed
   insulation when the actual design is already supported.
2. Action readiness is evaluated independently of completed commissioning.
   A proposal or passed prerequisite never creates a completed component. A
   list of ready actions is not a schedule or a jointly funded portfolio.
3. Insulation can reuse specifically assessed, technically accepted existing
   envelope scope. Generic S1 demand reduction or an unsupported “not required”
   assertion cannot satisfy it. Windows and doors are included where required
   by the assessed scope, without automatic replacement of adequate elements.
4. `complete_triple` requires accepted completion and current availability /
   adequacy of heat pump, battery and insulation, plus programme technical QA.
   It is a current technical result. Historical events remain separate if a
   component subsequently becomes unavailable.
5. `subsidy_exit_conditions` additionally requires programme eligibility, the
   strictly lower unsubsidized total-energy-bill comparison, full first-day and
   every interim/payment-period household cashflow protection, and exact
   subsidy applicability / exit timing. Annual energy savings cannot replace
   the full household floor. An unknown or failed financial gate does not
   erase the physical asset record.
6. Grid charge, household discharge, export and state/aggregator-service
   permission conditions are separate. Non-export service does not imply export. State
   service also needs its actual metering/control conditions; no kWh, kW,
   reserve percentage, revenue or dispatch feasibility is inferred.
   Each operation separately reports programme preconditions, which also need
   subject-matched eligibility and the full household floor. A valid right
   remains visible when programme use fails that floor. State-service cashflow
   evidence must include foregone household arbitrage, losses, wear and assigned
   replacement costs on the declared comparison basis.

## Compatibility and boundaries

The historical `household_state_model.json`, S0–S5 APIs, portfolio selection and
`b01_state_stock_scn.json` fixture remain unchanged in behaviour. They are
explicit compatibility/history interfaces. The adapter preserves the original
record and gates as versioned provenance and infers no new component, programme
completion, subsidy-exit or service-right assertion, including from S1/S4/S5.

The new synthetic `b01_capability_scn.json` fixture runs through B01's public
entry point. It contains no actual household or national population weight.
Tests cover independent installation orders and valid prerequisites, missing
components, the separate financial/legal conditions, expiry/withdrawal,
identity/truth/date adversaries, immutable inputs and legacy compatibility.

Within-year multiphase scheduling with one annual resource ledger, the weighted
population-unit bridge, benefit/score semantics, battery dispatch and dynamic
state-use allocation, D-tariff billing and full B12 cashflows remain separate
audit corrections. No target, horizon, budget, weight, price or battery-use
share is chosen here. Original B01-D01/P01 requirements and all accepted source
handoffs remain unchanged; this slice is not whole-task B01 acceptance or a
national result.

## Existing public authority and method bindings

- [Owner policy digest](../../registry/owner_policy_decisions.json),
  `POL-OWNER-20261004`: full triple, household floor and building-specific scope.
- [Cohort subsidy contract](../../registry/subsidy_reinvestment_policy_contract.json):
  separate completion, bill, cashflow and subsidy-scope conditions.
- [Population inference policy](../methodology/population_inference_policy.md):
  aggregate evidence is not individual permission.
- [Evidence-tier policy](../methodology/evidence_tier_and_validation_debt_policy.md):
  physical modelling may retain explicit validation debt; legal/site claims
  remain fail-closed.
- [B05](../../modules/B05/README.md), [B06](../../modules/B06/README.md),
  [B07](../../modules/B07/README.md): component-specific technical boundaries.
- [B04 topology authority handoff](V1_055_H_TOPOLOGY_AUTHORITY.md): researched
  tariff/topology applicability does not prove an actual installation's operation
  permission. No universal H-contract condition is introduced.

All bindings reuse the public repository baseline at
`5f6c8d4b34aee7e489f846ccb16eff47bf650e55`. No original external document or
private conversation is included in this public change.
