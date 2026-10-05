# V1-066: supplied shared-battery schedules

## Scope

One conditional consumer evaluates a supplied household/state schedule for one
battery and one connection point. It supplies no optimiser, dispatch priority,
rights percentage, tariff strategy, product choice or new source value. The
physical purpose includes a household grid battery without on-site generation.
The original task/readiness, source, legal and policy contracts remain unchanged.

The implementation is `modules/B07/shared_use_schedule_contract.py`; its public
evaluator is `evaluate_shared_use(case)`. The versioned registry is
`registry/b07_shared_use_schedule_contract.json`. The registry's twenty acceptance
groups map directly to executable test methods. Implemented coverage is an author
statement, not an independent review or original-task acceptance verdict.

## Input and identity

`SharedUseCase` and its frozen records require explicit values; scenario examples
are in the focused tests, not runtime defaults. `Term("Q", None, reference)` is an
unknown quantity; `Term("NOT_APPLICABLE", None, reference)` is explicit
inapplicability where permitted. A known zero is `Term("SCN", 0, reference)`.
Bare null cannot mean zero, no limit, absent permission or an unknown agreement.
`Unknown(reason)` represents a wholly unresolved allocation, agreement, idle
accounting or protection input.

The case and each agreement carry a content SHA256, computed with only that
record's own digest field blanked (`content_digest`). `Identity` fixes the device,
connection, two actors, coordinate, exact capacity denominator and native
executor digest. Every leg and interval binds that identity. The baseline binds
its complete leg and explicit method, purpose, scope, version and independent
scenario qualification. `comparison_digest` binds both complete schedules and
that baseline meaning. A hash establishes content identity, not source truth.

Time is half-open UTC. Intervals are contiguous, nonoverlapping and have unique
interval and physical-event IDs within each counterfactual leg. Explicit idle
intervals cover gaps. Opposing concurrent requests fail before netting. Ordered
charge/discharge use requires explicit subintervals and continuous state. There
is no interval-level reset field. The two legs share starting physical inventory,
exogenous household/heat-pump/other loads, device and time boundaries.

The supported comparisons are:

- `ACTIVATION_WITH_EXISTING_RESERVATION`: the same agreement, initial reservation
  and exogenous transfers in both legs; the baseline has no state activation.
- `RIGHTS_AGREEMENT_VS_HOUSEHOLD_ONLY`: an explicit household-only baseline and the
  actual supplied agreement. Unactivated reservation effects remain in the
  comparison, including foregone household discharge.

These scopes cannot be substituted, pooled into one service metric or reused
under another comparison hash. Household self-use and the declared state service
have separate exact identifiers. No baseline can label state activation as
household service.

## Native physics and allocation

`STORED_USABLE_KWH_SCN` uses the unchanged `BatterySpec`/`BatteryEngine.step` with
explicit one-way efficiencies and the required
`CONDITIONAL_OMITTED_STANDING_LOSS` condition. The single executor's state and
throughput counters continue across explicit interval durations. Its native
stored-energy credit and debit remain visible.

`DC_DISCHARGE_EQUIVALENT_REFERENCE` calls the unchanged native `run` once per leg,
which calls `step` once per aggregate interval. It preserves source pins, source
conditions, curve identity, post-clipping efficiency, E2 applicability and
Q-B07-003. A declared mathematical reference retains its native SCN/E3 status.
Credit is cycle efficiency times admitted charge DC, and debit is admitted
discharge DC. This is neither BMS SOC nor an inferred nominal-capacity conversion.

An absolute `Allocation` row for each actor supplies admitted AC energy,
coordinate credit/debit, charge-converter loss, cycle-bookkeeping loss and
discharge-converter loss. Actors never execute separate converter curves.
Directed actor identities and every aggregate component must reconcile with the
one native result. Requests, original allocations and residuals remain visible.
Negative components, duplicate actor/service allocations and allocation beyond
one actor's request fail. Partial/missing allocation stays Q; a known
contradiction still fails. Each provided actor row also has its own reconciliation
status. A locally reconciled, exactly identified row is checked against that
actor's known energy right, budget and protected/free pool even if the other row
is missing. Such a local contradiction is retained as FAIL without filling the
missing row or advancing the uncertain complete ledger. Active BMS loss is never
added separately.

Numerical tolerance is explicitly supplied, bounded by the native energy
allowance and a small relative envelope, and scaled down with flows below one
kWh. It cannot grow with initial inventory or national totals. Finite inputs
whose aggregate arithmetic overflows fail rather than produce an infinite result.

## Rights and chronological inventory

Each agreement declares exact actors, mode and identity. `RightsWindow` separates
effective and service windows, AC charge/discharge caps, maximum coordinate draw,
callable duration and a continuous `Budget`. Budget windows bind independently.
The supported contract has one continuous draw budget for each actor; adjacent
rights revisions reference that same budget. Splitting or aliasing the budget
cannot restore it. Explicit replenishment is `NONE`,
`ATTRIBUTED_CHARGE_CREDIT`, or `Q`; charging otherwise leaves the cumulative debit
in place. This consumer implements no other reset or borrowing rule.

`SHARED_CAPACITY_ACCESS` grants conditional access to current shared inventory,
not exclusive charged energy. The current and post-interval availability use the
single device's inventory and both actors' admitted use. Contract-qualified
drawable inventory respects the larger of the native physical reserve and the
separate agreement minimum-total-retained inventory, as well as the actor pool,
energy right and budget. Physical drawable inventory and shared retained-floor
headroom are reported separately. A Q retained floor leaves contract availability
Q while known physical inventory stays inspectable. Actor availability figures
are conditional ceilings under the same unsplit shared floor; they are not
additive reservations or a dispatch priority. Power, duration and time fields
remain separate; a kWh quantity is no future kW guarantee.

`PROTECTED_INVENTORY_POOL` retains the supplied state pool R and household/free
pool F, with x = R + F. Household draws F and state draws R. Explicit attributed
charge credits restore their own pools. Unique, strictly chronological boundary
transfers reserve/release existing inventory and never change x. Negative pool
balances and unmet initial targets are retained as failures; they are not clipped
into fulfilled promises. Earlier failure survives a later recharge or transfer.
No transfer from future charge, same-instant transfer cycle or hidden cross-pool
borrowing is supported. Unknown physical state or unreconciled actor allocation
makes both pool balances unknown. An explicit minimum total retained inventory is
a separate constraint from both the right and the protected pool.

Each rights row reports original requests, independent caps/windows, budget before
and after, energy right remaining, callable duration, and available coordinate
inventory before and after both actors' admitted flows. Expired windows grant no
availability. Actor unserved energy and full-request-power equivalent unserved
hours remain in the allocation report. Requested activity and admitted
constant-power activity are separate; a wholly unserved request consumes no
admitted callable duration. The full-power unserved equivalent is an accounting equivalent,
not an inferred partial-interval dispatch.

Unknown earlier actor allocation keeps the exact cumulative energy, budget and
admitted-duration ledgers Q. Separate lower bounds sum only locally reconciled
nonnegative use. Subtracting those bounds from a known whole-window draw or
duration cap, or from a non-replenishing budget, yields conservative remaining
upper bounds. Later known use or accumulated known use beyond such a bound is
FAIL even while the exact ledger stays Q. A lower bound of zero means no use has
been established, not that missing use was zero. Raw negative diagnostic upper
bounds expose a proven overrun; they are not available inventory or a dispatch
promise. Unknown cases within the bounds remain Q without invented failures.

The budget bound follows the continuous budget ID across adjacent rights, while
draw and duration bounds follow each exact rights window. An explicit attributed-
charge replenishment rule or Q replenishment receives no fixed initial-budget
upper bound: uncertain prior recharge may make later use feasible. Charge does
not replenish a `NONE` budget or reduce cumulative draw/duration. Requested
activity is checked against the duration upper bound even with unknown admission;
only known admitted activity advances its lower bound. No allocation, priority,
rights percentage, recharge amount or exact remaining balance is inferred.

## Connection, rebound and idle

When its included AC boundary is qualified, the raw connection identity is total
matched load plus admitted charge minus admitted discharge. The unchanged
household helper is called without an export clip. Import and export remain
nonnegative views of that raw signed quantity.
Separate explicit connection limits produce infeasibility without changing the
discharged energy or inventing a physical sink. Unknown actual export permission
is distinct from a physical zero-export envelope.

Response is signed baseline connection minus actual connection. A reduction in
planned charging can produce upward response with no battery discharge. Supplied
recharge produces negative response. Initial/terminal inventories and the
actual-minus-baseline terminal difference remain explicit. A service-only
horizon is a bounded result and creates no free recharge, cycle-adjusted benefit
or sustained availability.

Reference idle preserves native `Q_IDLE_INVENTORY` and subsequent
`Q_PREVIOUS_INVENTORY`. Zero admitted active flow does not establish zero total
battery electricity. If the reference enters idle handling, including a declined
unsupported active request, total-connection values and response remain Q. A
separately labelled active-converter component may still have a known signed
connection contribution and response. Component envelope failures remain visible
at that component scope. All-active qualified reference schedules and explicitly
conditional stored-engine schedules retain their established AC results.

An explicit `IdleAccounting` exposure names idle intervals
and their total hours. For the exact source reference it may retain the accepted
E2 aggregate AC debit and a separately supplied actor AC overhead allocation.
That debit is not subtracted from DC inventory; its DC attribution stays Q.
A known E2 aggregate debit does not supply an instantaneous AC path or an observed
peak and is never spread automatically across the named intervals. It therefore
does not by itself admit the broader total-connection response.
Native conditional empty-state components remain diagnostic, and adding the same
component again with the proxy is rejected. Active exposure cannot be relabelled
idle to count losses twice.

## Status and downstream boundaries

Input shape/identity, native physical trajectory, requested schedule fulfillment,
actor allocation, contract rights, connection envelopes, response and inventory
completeness have separate outputs. A clipped native trace can be known while the
requested schedule has a known shortage. An earlier known shortage or contract
failure is not erased by a later unknown inventory state. Unrelated permission
or economic Q does not erase the physical SCN witness.

Actual charging, discharging, export and aggregation remain four independent Q or
known-exclusion records. This consumer cannot approve actual site execution.
Commercial commitment, activation authority, actual delivery and national/network
value stay Q. B04 topology and dynamic-tariff producers are unchanged. This slice
does not calculate or acquire a tariff result; a supplied tariff-only component
cannot become complete household benefit. Later B04 pricing retains its matched
quarter-hour nonnegative-import, within-month retrospective net-energy boundary.

There is no B10 projection, adapter, evidence-token generator or REAL admission.
The existing B10 consumer fixture verifies that a matched SCN 3 kW upward claim
against 1 kW positive programme import applies at most 1 kW; the 2 kW remainder
stays outside that reduction. This is a boundary witness, not a bridge from this
case's total household connection scope or a network study result.

Financial components (tariff energy, wear, compensation, reservation opportunity,
recharge payment and terminal valuation) remain supplied and separately typed.
No sum, price, bill, wear, opportunity, affordability, ratio or cashflow result is
computed. Optional `QualifiedProtection` preserves an exact upstream native V65
Candidate/ComparisonFrame/cash-period assessment, plus explicit household and
comparison correspondence. It reuses the unchanged native protection validator. The upstream native status,
subject and exact hashes are retained as a separate diagnostic. Q or pointer-only
subject/counterfactual correspondence leaves this household's mapped protection
Q, even if that upstream subject has a known FAIL. Once correspondence is
qualified, first-day/interim FAIL remains FAIL with unrelated completeness Q or a
positive annual component. Full-agreement-effect qualification is required to
preserve PASS.
Without qualified protection, complete household protection remains Q. A full
B12 Case is not a prerequisite for a physical schedule.

## Verification

Canonical `tools/validate_registry.py` now has one additive shared-use loader hook.
It verifies the versioned boundaries, no defaults/automatic downstream admission,
all twenty acceptance entries and exact native dependency bytes. Existing registry
gates and their behavior are retained. Canonical unittest discovery executes the
focused behavioral witnesses and the unchanged repository suites. The local
preparation packet records final-byte test counts, logs, changed-file hashes,
patch and reconstructed tree separately; no publication or acceptance is implied.
