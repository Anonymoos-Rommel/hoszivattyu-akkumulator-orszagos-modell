# B12 input and accounting contract

Status: **contract only; sourced numerical outputs remain Q**. B15 is blocked.
This slice implements the entry contract in the approved
[V1 execution plan](../../docs/methodology/v1_evidence_feasibility_execution.md),
not an affordability decision, estimator, tariff engine or financing optimizer.

## Public operations and admission

`validate_case(case)` validates immutable section records, known identities and
scope compatibility. Malformed or contradictory inputs raise
`B12ContractError`; well-formed missing inputs survive as null/Q with field paths,
reasons and acquisition references. `assess_readiness(case)` returns dependencies
for each output. `audit_accounting(case)` returns available scoped synthetic
amounts, event rows and unavailable checks. There is no module-ready flag.

All records live in `input_accounting_contract.py`. `Scalar` requires a finite
`Decimal`, unit, reference period, basis and OBS/DER/ASS/SCN/POL/Q lineage. Bool,
float, NaN and infinity are rejected. Explicit zero has the same provenance
requirements as any number. Nested material fields are runtime-validated even inside heterogeneous section
rows; required fields cannot be replaced by None. Financial identities use local precision 50 and
ROUND_HALF_EVEN without implicit currency rounding. Supplied source amounts
must already reflect their declared rounding convention.

Every collection is a `Section`: explicit `NONE`, populated `ROWS`, or `Q`.
At the case level, each leg needs rows or an explicit `absent_legs` declaration.
Omitting baseline debt, maintenance or income cannot silently make it zero.
The baseline and programme are retained separately; dates of cash settlement,
measurement reference periods and bill service intervals are distinct.

Only `SYNTHETIC_WITNESS` cases execute arithmetic in this slice. Their material
values carry explicit scenario references, never source IDs or observed claims.
External admission references are accepted as structured pointers for future
canonical review, but their truth is not established by strings or explanatory
metadata. Such cases validate structurally and return Q/unavailable for all
numerical outputs, with no actual-source audit rows. Existing E1/E2 review can
later qualify real inputs with exact quantity, scope and use bindings, all eight
E2 criteria and explicit validation debt. No owner-per-datum approval requirement
is introduced. E3 does not become a canonical base, and no population status
returns an individual loan, tariff, grant, property or technical permission.

## Input sections and accounting boundaries

- `Case` binds existing B01 intervention/archetype/region and S-state transition
  references without issuing a technical transition. `Scope` keeps household,
  dwelling, payer role and separately reconciled cost/payment shares. Costs
  are already attributed to that payer; B12 does not multiply dwelling counts
  into household IDs or infer ownership shares
- `Cost` and `Asset` retain upstream B06/B07 technical/cost authority, full payable
  gross cost, separate eligible subset and caps, invoice event, bundle inclusions,
  generation, replacement retirement, life, coverage and terminal treatment.
  B10 network investment is not automatically a household charge. B14 caps are
  not market quotes. Initial CAPEX can remain available when later O&M or income
  is Q. Gross-only invoices leave their VAT split Q; net+VAT must equal gross.
  Recoveries retain dated transfers and aggregate refunds cannot exceed invoice
  VAT. Unknown invoice VAT blocks dependent refund/cash outputs. Eligibility cannot erase ineligible cost or mean cost minus grant
- `BillInput.from_b04` accepts the exact upstream `Bill`, preserving gross
  consumption/fixed/total charges, source IDs and
  `SCN_CONSTANT_2026_TARIFF_SNAPSHOT`. The caller supplies meter, service interval,
  settlement date, physical profile, months, connection/load scope and discount
  allocation. The adapter and validator replay the existing B04 producer with
  that exact context and match charges and source IDs, including H season checks.
  B04 monetary fields remain native HUF with a nominal 2026 price-date anchor;
  unchanged numbers cannot be retagged EUR or relabelled to a different price year.
  Service, settlement and evaluation dates can be later under the frozen scenario;
  isolated conversion rows do not authorize rebasing those amounts.
  This does not restrict separately specified non-B04 currency scenarios. Final
  charges receive no second VAT addition. Overlapping service intervals on one
  meter cannot carry duplicate fixed charges, even with different end-use labels,
  cash dates or caller keys. Only known positive duplicate fees are rejected; an
  unknown fee remains Q for dependent bill/cash outputs. Common service/end-use coverage is
  separate from H's eligible-load gate, so a gas-to-heat-pump comparison is possible
- Gas input is limited to B03 `MARKET_RESIDENTIAL_FINAL` with explicit B11 m3
  reference state. Wholesale/import, B13 regulated gas, useful heat, net-energy-only
  dynamic backcasts and system values cannot become household retail receipts.
  H's conditional price does not grant site or battery permission. Frozen B04
  prices do not imply a complete annual invoice or future observed bill
- `Instrument` accepts supplied nominal dated schedules, not a borrowing limit,
  THM/APR coupon or amortization builder. Opening + draw + capitalized interest
  and fees − principal − noncash extinguishment must equal closing debt. Row
  continuity, term, borrower and unique instrument IDs are checked. Residual debt
  at in-window maturity stays Q for complete finance, bank and recurring outputs
  until an explicit dated settlement is supplied; a balloon/refinance reference
  alone cannot clear it. Horizon end does not extinguish later-maturing debt. ZERO and supplied periodic opening-balance accrual have
  narrow checks; other interest correctness stays explicitly unverified/Q
- `Receipt` keeps payer, beneficiary, event and allocated invoice. Conditional
  grants stay conditional; B14 rules, suspended intakes and historical envelopes
  are not awards or cash. Direct supplier payments settle the same dated invoice
  and do not create bank deposits. A cash grant and principal forgiveness cannot
  share one support event, including across resource/instrument collections. Withheld fees are deducted once from gross draws;
  capitalized fees increase liability without a current cash outflow
- `Resource` separates net income, recurring receipts and required non-energy
  spending from energy, O&M/insurance, debt and CAPEX. Income components cannot
  be counted again under recurring-receipt labels. Signed income loss remains
  signed. Gross HFCS income, HI0220-as-complete-spending, debt stock, per-person
  amounts and conditional medians cannot silently become household net budget
  inputs. Required spending coverage and gross-to-net/period bridges are explicit
- `LiquidAsset` binds the household and scope, opening stock date, separate asset
  component, access, encumbrance, disposal cost and spendable balance. Total
  wealth/home equity is not cash. `PopulationBinding` preserves representative
  or calibrated inference requirements and unit/target bridges. Coherent joint
  evidence is required, not exhaustive records or multiplied unrelated marginals
- `MoneyBasis`, `Conversion`, `Policy` and `Valuation` preserve original currency,
  source price date, explicit conversion factor, nominal/real convention and
  owner-controlled floor/actor/group/reserve/debt policy. Cash schedules remain
  nominal. Floor and reserve inputs use the case money currency/basis; floors
  may be negative and reserve stock is nonnegative, without selecting a metric
  or default. Fisher's identity can be checked with supplied rates, but a real
  valuation still needs flow-by-flow conversion in a later consumer. No owner
  floor, discount, adoption, service or alternative gas-price default is supplied.
  The existing B01 rollout horizon is not an asset life or financial horizon

Replacement generations form an acyclic chain with nondecreasing commissioning
dates; cash prepayment is distinct from commissioning, and a same-day ordered
replacement is allowed. Each replacement links its predecessor’s cost schedule.
A terminal cash sale must reciprocally bind the same-leg SALE receipt, generation
and amount; a grant or operating receipt cannot satisfy that link.

The independent views are full unfinanced investment cash, financed economic
cash, dated bank liquidity and recurring budget residual. Principal is excluded
from the first view and included in the latter debt views. Own-fund withdrawal
is neither new income nor a second investment cost. Noncash terminal value has a
separate valuation bucket and never repairs liquidity. Unavailable dependent
columns are null, even when an independent row identity is available. Capital-only cost/grant/residual gaps do not suppress a known recurring budget. Annual
aggregates cannot certify intrayear liquidity; there is no annual/12 interpolation.

## Reproducible synthetic example

The complete fixtures in
[`test_b12_input_accounting_contract.py`](../../tests/test_b12_input_accounting_contract.py)
are permanently labelled synthetic and are not stored in `data/processed`.
An invoice of 127,000 HUF, loan draw of 57,000, withheld fee of 1,000 and later
20,000 grant produces −127,000 unfinanced cash and −108,000 financed lifetime
cash after two 28,500 principal payments. Opening cash of 60,000 briefly becomes
−11,000 before reimbursement. Moving the grant changes liquidity but not total
lifetime cost; supplier settlement preserves economics without a bank deposit.

Run `python -m unittest discover -s tests -p test_b12_input_accounting_contract.py -v`.
The tests also cover negative/partial paths, lifecycle, debt, actual B04 read-only
handoff, B14 rule containment, money bases and structural population scope.

## Remaining work

[`b12_input_inventory.json`](../../registry/b12_input_inventory.json) is a Q input
inventory referencing upstream authorities, not a second dataset or schema engine.
Hungarian aggregate income/asset controls can exist while the qualified joint
net-income/spending/liquidity/debt/dwelling handoff remains unadmitted. Source-base,
release, denominator, missingness and temporal reconciliation remain necessary.
The inventory adds no formal blocker and closes no existing evidence debt.

B12-D01/D02/D03 and both existing B12 global handoffs remain unaccepted/Q until
sourced computation exists. B13 fiscal consolidation, B14 current funding/award
quantities and B15 full financing mix remain their owners' responsibilities.
NPV, IRR, DSCR, support gap, maximum affordable financing, national uptake and
eligibility decisions are not exposed. Future consumers must distinguish negative
cash flow, nonexistent/nonunique IRR, zero-debt DSCR not-applicability, missing
inputs and inconsistent valuation basis rather than return zero or infinity.
