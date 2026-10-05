# V1-065 – Signed metrics, explicit utility traces and public-HUF ratios

## Executable boundary

`modules.B01.engine.compare_benefit_ratios` consumes typed `ComparisonFrame`,
`MetricDefinition`, `RatioPolicy` and `Candidate` objects. It returns each raw
measurement, utility trace, constraint result, protection/overlap assessment,
ratio state and comparable tie groups in one report. The versioned contract is
`registry/b01_benefit_metric_contract.json`; complete and adverse SCN callers
are in `tests/test_b01_benefit_metric_contract.py`.

Only `RATIO_ORDERING` is supported. There is no new MCDA, lexicographic engine,
general benefit sum, financial model, optimiser, allocation or permission.
The legacy APIs and their exact fixture output remain unchanged. In particular,
legacy `hard_minimum` is literally a lower bound, including under `MINIMIZE`;
it cannot stand in for a raw-cost upper ceiling.

## Measurement and comparison identity

A metric has a version and content digest, actual concept, native unit/counting
grain, actor/consolidation boundary, total or incremental meaning,
counterfactual method, accounting/time basis and valuation convention.
Non-monetary metrics need no invented money or B12 Case. Monetary definitions
retain B12 `MoneyBasis`: currency, nominal/real basis, price date and convention.
Explicit not-applicable semantics differ from unresolved fields.

Schema 1.2.0 makes `quantity_dimension` explicit: `MONETARY`, `NONMONETARY`
or unresolved. A monetary quantity with missing MoneyBasis remains Q while
retaining its signed raw value. Deleting that metadata cannot turn it into a
physical metric. A nonmonetary definition requires both an exact supported
nonmonetary unit token and an inapplicable MoneyBasis. The dimension itself is
part of the versioned definition digest; it is never inferred from missing data.

The bounded output vocabulary is recorded in the registry contract. Monetary
output currently supports only `HUF`; physical/count diagnostics support the
listed exact tokens, including `kWh` and `job-year`. Native other currencies
may still be retained within an explicit upstream Conversion. No aliases,
scaled amounts or compound units are interpreted. `Ft`, `forint`, `HUF/year`,
`HUF/household` and currency-bearing physical labels cannot enter through the
nonmonetary route. Unsupported output units fail explicitly; callers must
provide a supported, separately qualified upstream output instead of relying
on a guessed conversion. Compatible signed HUF and kWh routes remain valid.
Known currency, nominal/real, price-date, convention and valuation-method
conflicts are rejected; missing monetary basis or dimension remains Q.

Measurements retain the exact signed value, definition/candidate/frame digests,
producer output identity/version/status, native event periods, evaluation period,
and qualified upstream transformation lineage. Their content digest includes
that full context. Negative and zero effects are valid. `None` means Q; bools,
floats, NaN and infinity are rejected. Fraction arithmetic remains exact across
decimal context settings. A number cannot repair an unresolved definition.

Each candidate keeps its own household or population, record/project, bundle,
baseline and programme IDs. The shared frame fixes scope, geography, service,
evaluation horizon, aligned world and comparison/valuation methodology. A shared
HUF label is insufficient. Different households and their distinct baselines
can compare; different worlds, bases and denominator contracts cannot be pooled.

Native event periods need not coincide: upfront spending and later benefit may
bind one explicitly qualified evaluation contract. Native B12 periods are
inclusive; B01 planning periods are half-open. A `PeriodAdapter` explicitly
binds equivalent covered dates, timezone and qualification. No implicit endpoint
shift or annual-value/12 cash inference occurs.

## Constraints and utility

Raw `LOWER_BOUND`, `UPPER_BOUND` and `RANGE` constraints use the exact metric,
unit and frame, with inclusive endpoints. A known violation survives another
unknown bound. An unknown applicable endpoint is Q, not an unlimited bound.
Preference direction does not reinterpret the operator.

`UtilityMapping` contains its own version/digest, exact metric/frame binding,
raw direction, explicit domain and monotone piecewise-linear anchors. Higher
utility is preferred. Knots, endpoints, plateaus and interpolation segments
are returned exactly. Duplicate abscissae and unsupported nonmonotonic maps
are rejected; values outside the supplied domain remain Q. No sample min/max,
clipping, extrapolation, equal weights or weighted aggregate is inferred.
Two unitless utilities are not automatically cardinally comparable.

A utility constraint names its exact map digest, independently from a raw
constraint. Changing a map/version requires a new binding. Only declared
objectives and required constraints gate the ratio method. Optional utility
or diagnostic Q results and unused weights remain visible without preventing
an otherwise complete explicit ratio scenario. Roles cannot remove the
mandatory household protection.

## Ratio, overlap and partial ordering

The policy selects one numerator and one public-HUF denominator definition.
Gross public outlay, net public cost and seed bridge are different definitions.
The numerator may be physical or monetary; output retains its unit per HUF.
Only a known positive denominator permits division. Zero/negative/unknown
denominators remain distinct unranked cases; signed and zero numerators are
preserved. No actor ledgers, financial transfers or benefit streams are added
or netted automatically.

`OverlapAssessment` binds the exact candidate/frame and numerator/denominator
outputs. It preserves accounting scope, supplied contributions, inclusion and
exclusion, known overlapping endpoints, coverage and qualification. Duplicate
economic contributions and known conflicts fail. Different IDs do not prove
economic independence. A shared physical/source event is provenance, not an
automatic exclusivity key: distinct economically qualified effects can share
it. Complete SCN coverage is a conditional premise; unknown review stays Q.
Utility redundancy notes are separate from monetary contributions.

Ordering is descending exact ratio, grouped into ties. Stable candidate IDs
only present ties; they create no preference. Blocked, unresolved and
nonpositive-denominator cases remain in the report. Arithmetic scope is
incomplete while unresolved or nonpositive-denominator alternatives remain;
there is no complete-winner field. The report grants neither spending nor
technical/legal authority and does not reserve V1-063/064 resources.

The explicit A/B/C mathematical witness uses a budget of 10: A costs 6 with
benefit 12, while B and C each cost 5 with benefit 9. Ratio-first A prevents B
or C fitting the remainder; B+C yields 18 versus A's 12. These are synthetic
unitless arithmetic values, never programme inputs. The production code does
not implement even this tiny selection algorithm.

## First-day/interim household protection

`HouseholdProtection` binds the exact candidate/bundle/counterfactual and frame,
plus the digest of its qualified cash-period inventory, first cashflow date
and applicability. `CashCoverage` explicitly marks initial, interim, payment
and settlement scope `REQUIRED`, `NOT_APPLICABLE` or `Q`. A single payment
period may cover several relevant scopes; separately qualified absence does
not force invented periods. First-day coverage is mandatory, actual relevant
periods must be covered and a missing inventory never passes vacuously.

Known qualified failure dominates uncertainty elsewhere. A high utility,
annual benefit or positive present-value result cannot offset a first-day or
interim deficit. The engine checks supplied period assessments, without
calculating household cashflows or reusing a population mean as record proof.

Population comparison instead needs a scoped joint qualifying-population
output, model/version/hash, weighting, diagnostics, coverage, uncertainty and
structural sensitivity, with explicit SCN or admitted E1/E2 qualification and
validation debt. It does not require an exhaustive household census. Its
conditional population protection result grants no individual pass. A mean,
another population or one record's assessment cannot satisfy that binding.

## B12 producer compatibility

`bind_b12_output` retains the exact Case and AccountingAudit, including their
MoneyBasis, Policy, Valuation, Conversion, native inclusive dates and original
statuses. It verifies the audit by replaying the existing unchanged B12
producer on that exact Case, so a same-ID Case with different data cannot reuse
another audit. This adds no financial model. A valid Case or an
`EXTERNAL_ADMISSION` pointer does not provide numerical readiness: actual
accounting remains Q; absent valuation/affordability outputs remain Q.

Only an actually present ready native synthetic bucket supplies a number.
Its concept, actor and total/incremental semantics stay bound to the native
bucket. Total Case project cost is not public spending; native household
cashflow is not a national economic benefit. Upstream conversions preserve
original/target bases, original/converted/factor values and exact supplied
identity. Unresolved B12 transformation inputs remain visible as Q. This code
does not generate currency-converted or discounted results.

Submitted native Valuation/Conversion records are checked before readiness,
using B12's recursive type checks and native Scalar/Reference/Period rules.
Bare missing fields are malformed; properly typed Q rates and references
remain Q. Required dates and references cannot be omitted. Known valuation
rates retain the native ratio unit and greater-than-minus-one domain; the
discount-rate basis must match, and known nominal/real/inflation rates must
satisfy B12's existing Fisher identity. Conversion retains its typed method,
date, factor unit and known positive-factor multiplication identity. Supplied
identities use B12's precision-50 `ROUND_HALF_EVEN` convention. These checks
validate existing inputs; they compute no new financial result, choose no rate
and impose no full Case on an otherwise qualified independent output.

A submitted Conversion additionally supplies `original_money_basis`, the exact
native B12 MoneyBasis for its original scalar. The metric's MoneyBasis provides
the target context. Original/target scalar basis IDs and currency units must
match those explicit records; a dimensionless factor cannot turn a physical
source unit into the declared monetary currency. Basis IDs remain opaque:
their spelling never supplies a currency, price date or nominal/real convention.
One shared basis ID cannot name conflicting known source and target contexts.
The transformation qualification and output digest bind this complete context.
Absent original or target money context stays Q, and a typed Q convention
remains Q. Malformed context and known currency/basis mismatches reject.
Explicitly qualified currency/deflator conversions retain their supplied
values; no exchange rate or conversion result is inferred. Physical numerators
without a monetary Conversion remain valid and need no full B12 Case.

The existing Case transition domain is S0–S5. The adapter requires qualified
exact candidate correspondence; it does not invent a legacy transition for a
composite annual bundle. A composite bundle may instead consume its separate
appropriately qualified upstream Measurement output. No universal full-Case
requirement is imposed on physical metrics or independent qualified totals.

## Method provenance and unchanged policy

The observed document identities `SRC-B01-METHOD-EU-EEFIRST-2024-2143` and
`SRC-B01-METHOD-EU-EEFIRST-2026-0839` are registered with exact original hashes,
dates and URLs. Their earlier method-reference aliases remain in the contract.
Original HTML is external-only and is not republished.

[Recommendation 2024/2143](https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32024H2143),
Annex 4.2 and 4.4, supports explicit financial/economic perspectives, transfer
boundaries and impact valuation/overlap. [Recommendation 2026/839](https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32026H0839),
Annex 4.2.3 and 6.1–6.8, supports explicit baselines, valuation periods,
aggregation, robustness and distributional effects. Employment already in a
GDP valuation cannot be monetised twice in the same total; a distinct employment
diagnostic or preference dimension is a separate question. These method
references select no programme metric, denominator, price or weight.

The 2026 Table 12 illustration has gross-benefit difference 300, cost difference
200 and net-benefit difference 100; 7/3 rounds to 2.3. The adjacent prose's
additional-investment 300 conflicts with that table. The source inconsistency
is retained as a limitation; none of its illustrative figures becomes a
numerical model input. The general NPV/BCR distinction remains useful.

The accepted owner metric, public denominator and weights remain unset.
`Q-B01-006` stays OPEN. Explicit scenarios cannot make a canonical request
ready. Original 58-task criteria/readiness, source admissions, V1-062/063/064,
B12 and legacy B01 outputs remain unchanged. B15 is not started, and this
contract produces no new national numerical result or policy acceptance.

## Verification

- `python -m unittest discover -s tests -p test_b01_benefit_metric_contract.py -v`
- `python tools/validate_registry.py`
- `python -m unittest discover -s tests -v`

The focused tests cover the 20 reviewed acceptance groups plus adverse
period-scope, same-ID producer, conversion, actor and overlap bindings. The
legacy fixture output SHA256 remains
`fd8fbc5bbb97820b4ed26cde510b636cb90af1a0ca0440aec014503eb58dca7a`.
