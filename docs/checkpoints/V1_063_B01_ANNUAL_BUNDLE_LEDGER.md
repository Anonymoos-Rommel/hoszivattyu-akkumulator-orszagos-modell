# V1-063 – Annual planning for household bundles

## Result and correction

The historical S0–S5 selector permits one adjacent transition per household in
one call; separate calls start fresh capacity totals. The new
`B01.engine.create_annual_plan` entry point creates one owned annual reservation
ledger. It can reserve several component actions at the same household, in
parallel or in a declared partial order, while charging their combined resource
requirements once and counting the household once.

The selection unit is an explicitly qualified annual household bundle. It is
atomic: a resource shortfall cannot leave only part reserved while retaining
financial proof for a different full package. The bundle can be a qualified
staged programme case and need not finish the complete heat-pump, battery and
insulation package that year. No universal installation order or own-PV
requirement is added. A caller supplies the order in which alternative bundles
are considered; this is not an optimal benefit ranking.

## Qualified scope and household protection

The joint qualification binds the exact bundle fingerprint: household, site,
configuration/comparison basis, counterfactual, action set, dates, dependencies,
technical assertions and resource/cost inputs. It separately reports programme
eligibility and full first-day/interim household cashflow protection as an
explicit prospective `SCN`. The [component contract](V1_062_B01_CAPABILITY_CONTRACT.md)
also checks each action's own subject-matched prerequisites at its planned start.

Separate affordable phases do not establish that their combination is
affordable. A failed or unknown household floor cannot be offset by another
household, aggregate system value or public benefit. The evaluator consumes
qualified assertions; it does not calculate B12 cashflows or qualify original
source documents. Population estimates cannot certify individual permissions.

The fingerprint also binds the exact qualified requirement-domain catalogue and
version. For each action, every catalogue pool is declared `REQUIRED`,
`NOT_REQUIRED` or `Q` with provenance. Required uses must be supplied; a
not-required declaration carries no invented quantity. Missing domain coverage
is unknown, even when another domain has a nonempty use list. The catalogue is
itself an externally qualified input, or Q; the code does not claim to discover
all physical requirements. Synthetic qualified inventories may be used to test
explicit bounded scenarios.

## Three distinct resource calculations

1. `ANNUAL_FLOW` sums unique non-reusable use quantities over the year. Available
   work-hours, equipment pieces, trade mass and financial values keep their own
   units and source scope; no conversion is inferred.
2. `CONCURRENT` computes the largest sum of overlapping occupied calendar-date
   intervals. Disjoint intervals can reuse a capacity. Installed load/occupancy
   retains its own interval and is not shortened automatically when installation
   labour finishes. This arithmetic does not calculate power flow or diversity.
3. `PUBLIC_CASH` checks both the annual ceiling and dated available balance at
   payment/debit due dates. The opening balance is explicitly January 1 before
   all declared in-year debits/commitments. Prior-year settled movements are
   already reflected in that opening balance and are not deducted again. A
   future receipt cannot repair an earlier payment-date gap. A June receipt can
   support a July payment even when the plan is reserved in May. Separately
   evidenced/scenario bridge funding may be supplied; this does not require
   aggregate state fiscal cashflow to be nonnegative.

Every quantity has exact Decimal input, unit, reference/price basis and
OBS/DER/ASS/SCN/POL/Q lineage. Internal sums and comparisons use exact rational
arithmetic, independent of the caller's Decimal precision. Null/Q, qualified
zero and a negative opening cash balance remain distinct. Negative opening
availability can expose a funding gap; negative resource use does not create a
credit. Output quantities preserve the constraint unit/basis/scope and source
references. `remaining` means ceiling minus use/peak, not a cash account balance.

When some nonnegative uses or opening commitments are unknown, the known sum/peak is only a lower
bound. If it already exceeds the ceiling, the condition remains `FAIL` while
the full total and remainder remain null. A known earlier cash gap also remains
a failure; an unknown future receipt cannot repair it. Unknown incoming funding
can affect only dates at which it could already have become available.

Calendar timezone and year are explicit; intervals are half-open and contained
in that year. The bounded interface uses calendar dates, not hourly dispatch or
intraday settlement. A receipt's availability date must be qualified for that
settlement date; its mere posting date is not sufficient. Cross-year obligations
must be provided in their proper annual window or a governed upstream split;
this reader does not silently clip them.

National and regional ceilings constrain the same unique event. They are not
two costs and are never summed into a financial total. Resource-holder, unit,
basis and scope must match. Stable source work, asset-generation and resource/
cash-event identity are distinct from proposal aliases. Changing aliases cannot
create a second installation, charge, receipt or a self-financing cash movement.

Each explicitly bounded resource pool has exactly one pool-total view, plus
optional local subviews. The total is not automatically national: a regional
independent pool can use that region as its total. Every use must match the
total's scope and a view for every declared geographic scheme; omitting a tag
or naming an uncovered region cannot fall back to the broader view. The total
checks all pool uses, including when a malformed scope would otherwise evade a
local view. One source funding event belongs to one pool and cannot finance a
second pool. Its occurrences in national/regional views remain one source
receipt, constrained by the common pool total. Each cash pool requires an explicit
`CashPoolQualification`: a qualified fungible pool with non-additive access
ceilings, with SCN/DER status, references and scope. A subview receipt must bind
an existing pool-total source event. It cannot increase that event's amount,
make it available earlier or resolve an unknown root amount. A smaller/later
access cap requires its own qualified `CashViewRestriction`; its derived or
scenario lineage remains separate from the original receipt facts. An unknown
restricted amount remains Q.

These are additional access ceilings over one fungible pool, not exclusive
regional allocations of named source receipts. Such earmarking would require
a conserved source-to-payment allocation contract and is outside this interface.
The pool-total cash path funds every payment once; additional views only tighten
its admissibility. They cannot be summed into extra funding.

## Ledger ownership and repeat calls

`AnnualPlanSession` owns its current immutable state. A reserve call supplies an
expected revision, not a substitute old ledger. Successful atomic batches keep
the prior digest, declared order reference and ordered-input digest. Subsequent
calls include existing opening obligations and reservations. Identical retries
return `ALREADY_RESERVED` without another debit or revision.

At most one qualified bundle is reserved per household in this identified annual
ledger, not per lifetime. Another alternative, changed selected payload or
cancellation returns `REQUALIFICATION_REQUIRED`; the prior reservation remains.
No refund, rebooking or release of actual obligations is inferred. Validation
failure leaves the session unchanged, including when an earlier candidate in
that batch appeared to fit. The session retains revision history; cross-process
storage and distributed locking are outside this offline contract. A separate
scenario cannot be added to the same committed plan as though it were new work.

## Joint network and empirical limits

Resource reservations remain `SCN_CONDITIONAL_RESOURCE_RESERVATIONS` and imply
no actual funding, commissioning, operation right, subsidy exit or completed
national programme. An independent joint-network result must match the complete
active-set digest, planning basis, opening uses, their knowledge state/provenance
and horizon. An absent, stale or
mismatched study remains unknown. Individual action passes, territorial
membership and indicative published DSO MW cannot establish joint connection
feasibility or a fungible national headroom budget.

The existing [B18 references](../../modules/B18/README.md) do not supply active
regional installer-hours, job productivity, available device counts or delivery
quotas. The [B10 contract](../../modules/B10/README.md) keeps indicative headroom
separate from node/connection authority. [B12](../../modules/B12/README.md) still
does not provide real external bundle cashflow decisions. The owner has selected
no annual budget, and future avoided subsidies are not already available cash.
Qualified prospective assumptions may support explicit scenario calculations;
the code does not require future observed receipts merely to plan a scenario.

Tests use synthetic quantities to exercise atomicity, parallelism/dependencies,
cumulative calls, stale revisions, aliases, household floors, source missingness,
unit/actor/geographic distinctions, concurrent occupancy and cash timing. The
historical S0–S5 fixture and the V1-062 capability contract remain compatible.

No target, horizon, budget amount, capacity, score weight, conversion factor,
diversity factor or battery-use share is supplied as a default. Weighted
population planning units, benefit semantics, full financial/network models and
general amendments remain separate. Original 58-task acceptance criteria,
readiness values, source admissions and dependencies are unchanged.
