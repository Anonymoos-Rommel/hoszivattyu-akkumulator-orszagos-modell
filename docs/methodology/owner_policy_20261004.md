# Owner policy and cohort financing recorded on 4 October 2026

The project owner selected household protection, benefit-per-public-HUF
priority and a **2028-01-01** planning start, then clarified how completed
household cohorts would release recurring energy subsidies for later
cohorts. The bounded digest is `registry/owner_policy_decisions.json`.
The exact conversation is retained privately. These are **POL** intentions
and functional requirements, not observations, current-law changes or a
verified national financing result.

## Protected household and selection priority

Household cash flow must not worsen because of the programme from its first
day. This is a mandatory household constraint. The state may invest over a
longer period; no first-day nonnegative state cash-flow floor was selected.
When need-first selection conflicts with benefit per public HUF, the latter
has priority **subject to household protection**. The benefit metric,
public-cost denominator, time basis, normalization and numerical weights
remain unselected. No GDP, tax, import or household-saving score is silently
substituted for the missing combined metric.

Compare the same household's programme and without-programme cash flows on
a compatible service, price and time basis. The protected quantity is
incremental net household cash flow, not absolute household income. Initial
obligations and every relevant payment or settlement period must be checked.
A positive annual total or later gain cannot conceal an earlier household
funding deficit. Missing cash dates or financing leave compliance unknown.
An archetype average cannot establish a particular household's compliance.

Account for energy, operation, maintenance, replacement, own funds, loan
disbursements, repayments, interest/fees and grants at their cash dates.
Capital payments and financing principal are distinct entries, not duplicate
costs. A future grant cannot fund a prior payment without a separately
sourced bridge that also preserves the household constraint.

## Completed triple packages and subsidy exit

The owner's later clarification replaces the earlier shorthand about
households whose conversion is underway. The intended subsidy-exit cohort
consists of households with **heat pump, battery and insulation all
completed**, with the required technical acceptance. Enrolment, work in
progress, or a single completed component does not trigger this mechanism.

For the named policy scenario, exit requires an **unsubsidized total
household energy bill below the prior subsidized comparison baseline**.
The comparison must declare the compatible service, price, billing period
and baseline. The full first-day household cash-flow test remains separate
and mandatory; a lower energy bill alone cannot conceal financing or
maintenance burdens. Current legal eligibility and the hypothetical policy
change must remain distinguishable.

Only the subsidy actually replaced for the qualifying household/cohort is
attributable. The national subsidy appropriation, an import bill, the
household's tariff benefit and the state's cash payment are different
quantities. No generic gas/oil subsidy or universal recipient coverage is
assumed merely because it was mentioned as an example.

## Recurring fiscal release and reinvestment

Each completed qualifying cohort can reduce the recurring state subsidy
needed in subsequent applicable periods. Later cohorts add their own
attributable release. For each cohort and period, compare the state subsidy
without the programme with the remaining subsidy with the programme within
the same recipient, purpose and accounting scope. Count that period's
avoided amount once. Do not book cumulative prior savings or their
capitalized value again as current-year cash.

The reusable amount is **net actually available released fiscal cash**
after the relevant dated public costs, reserves, compensation and existing
obligations. The portion retained for the programme is controlled by an
explicit, time-varying reinvestment share from 0 to 1. The other share is
withdrawn by the state. Household bill savings stay in the household ledger;
any later tax or repayment flow needs its own evidence and accounting.
A cost or obligation deducted in net available release is not deducted again
from programme cash: each dated cash movement has one ledger/attribution
identity. Other programme expenditure is booked separately exactly once.

An unset annual ceiling does not mean an unlimited budget. Seed investment,
upfront training and timing bridges need separately evidenced financing.
Future avoided spending is not cash already available. A negative fiscal
balance remains a visible financing gap; it is not erased by applying a
zero floor to a reported release.

At a reinvestment share of zero, this particular funding feedback is lost.
Physical household savings can remain, and other funding sources may still
support rollout. The model must calculate delay or extra funding need from
the full financing and capacity constraints. At a share of one, all net
available eligible release is retained; this alone does not prove that the
programme is self-financing.

More completed cohorts may support faster rollout, but acceleration is an
endogenous result. Workforce, training lags, equipment supply, grid limits
and finance constrain it. No exponential growth rate or automatic annual
completion increase is selected.

## Physical, delivery and macro boundaries

Insulation reduces useful heat demand before heat-pump conversion is
calculated. Heat-pump electricity uses post-retrofit useful heat divided by
qualified seasonal performance, with storage losses and service deficits
explicit. Gas uses its own compatible final-energy/efficiency basis. An
SPF of 3 is a conditional illustration, not a verified annual WM50 input or
a bill ratio. Do not add envelope and heat-pump saving percentages as if
they were independent amounts.

Building size, type, condition, heat loss and required work determine the
package using existing typologies. The envelope assessment includes
condition-appropriate windows and doors; already adequate openings are not
automatically replaced. Their joint thermal effect is accounted once.

The long-lived insulation mechanism does not set the whole package's
operating cost to zero. Electricity, maintenance, battery/heat-pump renewal
and residual value need source-bound actor and timing assignments.
Future energy prices are not assumed to rise monotonically.

Upfront vocational capacity for heat-pump, insulation and electrical work
is part of the programme design to size against rollout. Training costs,
qualified-worker output, lags and other market work remain explicit inputs.
Delivery conditions include qualified verified firms/workers, invoiced
work, registered employment and independent technical acceptance. State
sponsorship alone is not proof of formal employment or quality.

Investment and training activity, actual fiscal release, household spending,
saving/debt repayment and net tax/employment effects are separate channels.
A net macro claim needs a baseline, import leakage, alternative uses of
funds, displacement and capacity effects. Gross spending, GDP, turnover,
jobs and tax receipts cannot be added as independent benefits.

## Canonical values and intended controls

`registry/subsidy_reinvestment_policy_contract.json` records the cohort
identity, gates, actor ledgers, period accounting and future parameter
interface. It prepares these requirements without claiming a new household
evaluator, macro model, numerical programme result or user interface.

The planned date is 2028-01-01. The owner discussed an approximate 10–20-year
project range but selected no single horizon. The existing 8–25-year
technical range and 12/15/20-year reporting points remain. The historical
15-year registry default is cleared; explicit scenario/test fixtures remain.
The annual public ceiling, exact target, reinvestment share, debt ceiling,
benefit metric, weights and output tolerances remain unpopulated.

The eventual interface should allow deliberate policy scenarios around one
checked canonical baseline. Reinvestment share is time varying, displayed
as 0–100%; other controls cover seed funds, training/installation capacity,
prices, costs and subsidy rules, with their units, dates and source/scenario
status visible. Missing inputs, financing gaps and infeasible combinations
must be explicit. This is not a massive Cartesian uncertainty grid or an
instruction to build the final application before its upstream contracts.

The 900/100-billion subsidy sequence and 500,000/250,000-HUF household figures
were illustrations. The later20–25million-HUF package example was explicitly
clarified as illustration only, not a cost estimate or SCN input. None are
forecasts, targets, observed means or
canonical inputs. The roughly 1,000-billion national subsidy claim is a
separate dated official-source check, not the default reinvestable amount.

B01-P01 and B13-P01 are partially specified. B19-D02 and the original evidence
and numerical acceptance criteria remain open. Public publication, main
merge, spending and new source disclosure require their own authority.
