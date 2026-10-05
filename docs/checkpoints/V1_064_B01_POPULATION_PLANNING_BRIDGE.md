# V1-064 – Dated population planning and separate actual records

## Executable result

`B01.engine.create_population_plan(inputs=..., plan_id=..., version=...)`
composes a thin qualified-output adapter, conserved dated population planning,
intervention alternatives, resource requirements, aligned joint uncertainty and
a separately scoped record report. Its contract is
`registry/b01_population_planning_contract.json`. The complete synthetic
consumer witnesses are in `tests/test_b01_population_planning_bridge.py`.
They are arithmetic/interface examples, not empirical inputs or policy defaults.

The current source demonstration, `engine.population_source_demo()`, calls the
existing B02-P84 `build_population_controls` and
`current_repository_envelope`. It reproduces **40 controls and 3,389,817
occupied non-district-heated dwellings at the 2022 census reference date
(2022-10-01)**, retaining the canonical
`SRC-B02-KSH-CENSUS-API-2022` identity and the exact committed control-artifact
hash. Terminal technical eligibility is still **Q, [0, 3,389,817]**, with no
covered terminal-outcome population. No new P84 estimator is implemented.

These controls do not provide a 2028 stock, programme target, intervention-
specific eligible population, joint state distribution, resource coefficients,
actual household identities or individual permissions. Accordingly the source
demo leaves those fields Q. It cannot instantiate an allocatable planning set
without separately supplied qualifications or explicit scenario premises.

## Adapter and scientific boundary

`PlanningInputs` binds a versioned closed population, native counting unit,
geography and reference date; calendar/timezone; versioned state definitions;
qualified cell/origin partition; options; controls; and all supplied joint
worlds. `EvidenceBinding` distinguishes `ADMITTED_ESTIMATE` from `SCN`.

The admitted route requires explicit claim scope, model/version, output digest,
source/control hashes, selection and weighting reference, validation diagnostics,
structural sensitivity, uncertainty method, one central definition and declared
coverage/missingness. E2 supports model continuation with explicit validation
debt. E3 is only an explicit scenario. No exhaustive actual-record list or
universal E1 condition is added. A status string or source reference alone does
not constitute admission.

Scientific admission, disjointness of real-world partitions and completeness of
resource inventories remain upstream qualified claims. This code checks their
bound identity, completeness and arithmetic; it does not validate source truth,
select a calibration algorithm or make a new scientific admission. All option
eligibility and resource coefficient claims must be named by the binding. An
empty resource inventory also needs its explicit inventory qualification.
Population intervention eligibility means the joint qualifying population for
that precise option. A screening count, mean cash surplus or individual pass
cannot be substituted for it. Household first-day/interim protection and legal,
network and programme gates retain their existing record-level contracts.

There is exactly one native represented-mass quantity per lot/world. Household,
dwelling and building units are distinct; sample expansion weights are not
accepted as counting units or multiplied by already expanded cell mass. Exact
integer/decimal-string/Decimal/Fraction inputs preserve fractional mass without
rounding, including independent of Decimal context precision. Floats, booleans,
nonfinite and negative values are rejected. Explicit zero differs from None/Q.

The qualified target-control universe is declared independently from the control
rows actually supplied. An omitted whole control stays visible with its uncovered
scope; deleting a row cannot shrink a claimed national population. A bounded
regional scope declares its exact own target universe.

Cells carry disjoint canonical scope atoms within their controls. Reconciliation
at a compatible population/unit/geography/date is exact. Uncovered atoms remain
visible, so a regional subset can be evaluated without inventing a national
completion. A Q control remains Q even when supplied scenario mass is known.
Historical-vintage controls require a separate roll-forward premise and are
reported as historical context, never current observed reconciliation. General
reclassification, split/merge, geography changes and changed definitions require
a new qualification and session; old schedule digests cannot be reused.

## Reservation, time and uncertainty

The caller submits a `FixedSchedule` with the session definition digest, current
revision, explicit order reference and immutable `Allocation` records. The same
full requested quantities, options and dates are evaluated unchanged in every
joint realization. Every world covers the same cell/lot/option/resource universe;
coefficient and population values carry matching world identities. No unrelated
marginals are multiplied, no world-specific clipping or optimization occurs, and
no probabilities, confidence interpretation or robust acceptance rule is inferred.
If probabilities are supplied, all must be supplied and sum exactly to one;
the evaluator retains them without imposing a decision rule.

An option/world requires an explicit supplied eligible-origin interval set,
bound to its exact option and source-state definition. Its union must equal any
claimed eligible scalar; coordinates must be disjoint and within the relevant
origin population. The selected interval must be covered. Missing joint sets
remain UNKNOWN even when marginals are known; the code never creates
`[0, eligible_mass]` from a scalar. These are statistical mass coordinates,
not actual household identities. Child offsets resolve back to their root
coordinates, retaining membership across phases. Equal option marginals with
different cross-option overlap can therefore produce different feasibility for
the same fixed decisions.

A successful allocation reserves an exact interval of its source lot immediately.
The mass remains in its source state, marked reserved, until `effective_on`,
which takes effect at the start of that calendar date. Source remainder and
child lot form disjoint lineage. Stock does not disappear during work. A child
can undergo another phase only when its predecessor endpoint is effective by
the declared next work start. A composite option executes its qualified endpoint
without inventing component sequence or intermediate completion.

Source interval reservations persist across calls. An alias resolves to the same
source lot. Overlapping alternatives cannot select that mass again. Stable
allocation-event identities prevent duplicate aliases. Identical retries at the
current revision are idempotent; a stale revision is rejected even for a retry.
Changed allocations, definitions or child identities require requalification.
The fixed decisions also cannot select overlapping source intervals when an
earlier request was infeasible in one world. Failed requests do not release that
choice to an implicit world-specific fallback; a different alternative needs a
new explicit qualified plan. Keeping this decision history does not post failed
mass or resource reservations.
Malformed requests are rejected before any mutation. A per-world failed
allocation posts neither stock nor resource commitments. Earlier successful
allocations persist, and the report labels the complete schedule
`NOT_FULLY_ADMISSIBLE` when any allocation was rejected. The shown stock is the
explicitly admitted subset, not a clipped or repaired version of the full plan.

Each outcome reports population admissibility separately from resource status.
The accepted transitions remain proposed population stock. Relabelling an
allocation `IMPLEMENTED` is rejected; no planning status can create an observation.
Transition throughput sums accepted phases. Unique planning mass uses the union
of conserved root-origin intervals, so repeated phases are not new participants.
Neither quantity is an actual household or dwelling completion count.

This is an offline owned session, not a distributed database transaction or
amendment/refund authority. Durable concurrency and cancellations are deferred.

## Resource requirements and optional fit

Each per-native-unit coefficient retains kind, unit, pool, region, actor, basis
and evidence reference under the joint binding. Multiplication is exact. There
is no unit conversion, household-to-dwelling factor or population-expanded
individual permission. Different actors, regions, price bases and pools cannot
be silently combined.

`FLOW` requires an explicit due date and is summed by that date's calendar year.
`OCCUPANCY` has an explicit half-open interval and reports time segments and
concurrent peak. Workforce, equipment and payment windows can differ from work
start and completion: a deposit before work and occupancy after completion keep
their own dates. Moving only a stock milestone cannot move a payment or release
capacity. The bridge has no cash-balance, dispatch or financial model.

Optional `ResourceEnvelope` values check only explicitly compatible intervals.
A `PASS` belongs to that envelope and its dates. Missing or partial envelope
coverage is separately `Q_UNCOVERED_RESOURCE_DATES`, never unlimited capacity.
Known demand may be planned without an envelope, but is explicitly reported as
`REQUIREMENTS_KNOWN_CAPACITY_SCOPE_INCOMPLETE`; this does not establish actual
capacity, funding or programme feasibility. A known envelope excess rejects the
allocation in that world. An envelope with no matching resource/date demand is
`NOT_APPLICABLE` and cannot gate unrelated work. Explicitly known zero demand
fits the contract's nonnegative capacity domain even when the ceiling is Q;
that `PASS` preserves the null ceiling and its source rather than inventing zero
or unlimited capacity. A Q required coefficient, or positive applicable demand
against a Q envelope, leaves the allocation unresolved and unposted. Requested demands, including
unknowns and failed-world requests, remain visible in each outcome. The full
fixed-schedule demands are also aggregated independently of which allocations
were admitted, with separate envelope checks. Posted requirements refer only
to the admitted subset; rejected mass never silently shrinks the requested plan.

No B18 programme supply, B12 household finance, owner policy number, actual
funding, network connection or installer reservation is invented. The V1-063
actual-household bundle interface is not reused by presenting a population cell
as a fictional household.

## Actual correspondence

`session.report(records=..., record_as_of=...)` validates explicit dated
`RecordCorrespondence` inputs and calls the unchanged
`engine.assess_household_capabilities` for supplied `CapabilitySnapshot` records.
Every snapshot keeps its own household/site/basis/context/evidence and date. A
planning cell cannot substitute for it, and a population evidence scope cannot
pass its individual-record validator. Record assessments remain separate even
when the population link is unresolved.

The relation declares many-to-many cardinality explicitly. Several visits to
one household do not add households. Several households can share a dwelling;
one household can appear at several dwellings. For DWELLING native grain,
`population_unit_id` must equal the declared canonical `dwelling_id`; for
HOUSEHOLD grain it must equal `household_id`. This is the first interface's
supported shared-canonical-ID namespace convention, not proof that real entities
are identical. Different source namespaces need a qualified upstream crosswalk;
unreconciled aliases are rejected. Mapping truth still depends on its qualified
evidence. For BUILDING grain, the qualified population-unit identity is a building identity
independent of the separately reported site and dwelling. No site, meter or
connection identity is automatically treated as a building.

Conflicting active cell membership for one source unit, or contradictory
household/site identity for one record, produces unresolved exceptions. Stale
membership and changed population definitions do not count as qualified links.
Duplicate identical relations are counted once; conflicting snapshots for the
same record are rejected. REAL and SCN counts are separate, at record, household,
dwelling, source-population-unit and site grain. Correspondence does not replace,
subtract from or recalibrate population mass, and one passing record is never
expanded into weighted implementations or permissions.

## Validation and unchanged authority

Focused witnesses cover exact source replay, fractional conservation, zero/Q,
partition coverage and vintage, admitted E2, cumulative alternatives/aliases,
revision atomicity, milestone boundaries, repeated phases, composite endpoints,
fixed-world infeasibility, resource timing/units/gaps, correspondence cardinality
and unchanged actual gates. Registry validation calls the real P84 consumer.

Canonical verification commands:

- `python -m unittest discover -s tests -p test_b01_population_planning_bridge.py -v`
- `python tools/validate_registry.py`
- `python -m unittest discover -s tests -v`

The original 58-task acceptance criteria/readiness, source handoffs, owner policy,
V1-062/V1-063 behavior and legacy fixtures are unchanged. This interface is not
an accepted empirical national portfolio or original-task completion.
