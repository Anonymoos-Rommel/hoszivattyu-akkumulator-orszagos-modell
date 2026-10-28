# B07 – Háztartási akkumulátor és VPP

## P1 scope

B07-P1 kizárólag a háztartási akkumulátor fizikai állapotátmenetét és a
fizikai rugalmassági burkot adja. A motor nem tartalmaz tarifát, H-tarifás
jogi döntést, VPP-piaci ajánlatot, bevételt, CAPEX-et vagy gazdasági dispatch-et.

## Canonical boundary

The command boundary is AC/grid-side power at the battery interface:

* charging: `stored_energy_added = grid_charge_energy * charge_efficiency`;
* discharging: `grid_energy_delivered = energy_removed_from_storage * discharge_efficiency`.

Each one-way efficiency is applied once. `nominal_capacity_kwh` and
`usable_capacity_kwh` remain separate; SOC is bounded by explicit fractional
limits. Power limits are independent from energy capacity, and the timestep is
explicit in hours.

The engine clips requests only against physical limits and reports curtailed
charge or unserved discharge. Simultaneous opposing commands fail closed.

## Interfaces

`compute_household_balance` accepts base household load, B05 electrical heat-
pump load, other load, onsite generation and battery flows. It returns import,
physical export and any export curtailment. Export permission is a separate
`Q`/`POL`/`SCN` status and is never converted into a tariff result.

`make_b08_handoff` exposes the minimal physical fields for B08:
`net_grid_import_kw`, `net_grid_export_kw`, `battery_charge_kw`,
`battery_discharge_kw`, `physical_up_flex_kw`, `physical_down_flex_kw` and
`soc_fraction`.

## EU-first product evidence

The bounded evidence pack contains German-manufactured or Germany-made
manufacturer claims for VARTA pulse neo and sonnenBatterie 10 performance.
European brand, EU sales or an EU office is not treated as proof of cell origin
or supply-chain independence; those unresolved boundaries remain `Q`. No raw
manual or copyrighted table is stored in the repository.

## Product-specific efficiency boundary (B07-P2)

The product registry keeps direction-specific fields separate from the legacy
single efficiency field:

* VARTA pulse neo 6: the `97.8%` observation is battery-only (`BATTERY_ONLY`),
  not an AC/grid charge or discharge value. The HTW report also distinguishes
  AC-system performance from AC2BAT and BAT2AC measurement curves. Charge,
  discharge and round-trip product values therefore remain `Q`.
* sonnenBatterie 10 performance: sonnen's `75–80%` figure is a practical
  whole-system example, not an exact product/direction value. Charge,
  discharge, round-trip and the precise AC/grid boundary remain `Q`.

No square-root split, direction symmetry, hidden inverter multiplication or
round-trip substitution is allowed. Runtime continues to use explicit SCN
one-way inputs only until product-specific AC/grid evidence is available.

## Readiness boundaries

P1 can close the physical SOC engine, power/energy limits, household balance
and B08 physical handoff for explicit SCN/product fixtures. Runtime
degradation, H-tariff legality, VPP eligibility and market availability remain
unresolved.

Decision snapshot:

* `BATTERY_PHYSICAL_CONTRACT_READY = YES`
* `SOC_ENGINE_READY = YES`
* `PRODUCT_EVIDENCE_READY = YES` for the bounded EU-first evidence pack; product-specific one-way efficiency and cell origin remain Q
* `DEGRADATION_RUNTIME_MODEL_READY = NO`
* `PHYSICAL_FLEXIBILITY_READY = YES`
* `H_TARIFF_BATTERY_INTERFACE_READY = NO`
* `VPP_MARKET_INTERFACE_READY = NO`
* `B08_PHYSICAL_HANDOFF_READY = YES`
* `B07_READY_FOR_NEXT_SLICE = YES`

The next highest-value blocker is a combined B04/B07 evidence slice: prove the
H-tariff meter/battery/export boundary and obtain product-specific AC/DC
one-way efficiency plus cell/supply-chain origin evidence without importing a
foreign-dependence assumption.

## V1 tested-reference evidence and coordinate

[SAX2026 source reference](../../docs/checkpoints/V1_013_SAX_SOURCE_AND_COORDINATE.md) adds explicit, bounded converter-point consumers and a [proposed discharge-equivalent coordinate contract](../../docs/methodology/b07_discharge_equivalent_reference_contract.md). It does not fill legacy one-way efficiency fields or alter the existing engine. Source-tested DC capacity/cycle efficiency and separate output-axis converter curves permit a conditional reference route; idle, aging, national applicability and legal gates remain distinct. No new state runtime is included in this checkpoint.


V1-038 adopts the separately named [discharge-equivalent reference](discharge_equivalent_reference.py) with explicit initial/terminal inventory, converter boundaries and cycle-eligibility checks. Its constant tested-product applicability and separately supplied idle-exposure aggregate use E2/PROVISIONAL_BASE; calculated balances are DER. [Validation debt](../../registry/b07_reference_validation_debt.json) preserves the E1 upgrade path. Exact component measurements are not required merely to continue the E2 aggregate model. The existing engine remains unchanged; the idle AC proxy does not invent a DC state transition, a national product choice or a complete annual-system efficiency.


## Source temperature and test conditions (V1-052)

The SAX source controls and genuine source-labelled run/aggregate-idle results now
include `source_conditions`. The 5–35 °C manufacturer operating specification is
separate from the unknown measured laboratory ambient. The published common capacity
protocol retains its 100/50/25% nominal-power levels and six retained cycles; its
Fronius D1 example does not become SAX test wattages. The additional low-load method
also retains its own scope. All existing numerical controls, curves and calculations
are unchanged. Synthetic references receive no source-condition authority.

See the [condition handoff checkpoint](../../docs/checkpoints/V1_052_B07_SOURCE_CONDITIONS.md)
and the [reference contract](../../docs/methodology/b07_discharge_equivalent_reference_contract.md).
The exact report, official data asset and datasheet were recovered against their
existing hashes; originals remain private. Q-B07-003 E2 applicability debt, D02
lifecycle and D03 operating/legal availability remain open. This prepares the original
D01 handoff for whole-slice acceptance review; a real reviewed condition commit must
exist before its acceptance metadata can reference it.

## Supplied shared-use schedules (V1-066)

[`shared_use_schedule_contract.evaluate_shared_use`](shared_use_schedule_contract.py)
audits household and state/aggregator use of one physical battery across two
explicit generation-free schedules. It executes each native B07 engine once per
leg and interval, then reconciles supplied actor allocations and independent
energy, power, duration, budget and service-window rights. Shared-capacity access
and a protected inventory pool are separate modes; neither creates charged energy.

Activation under an existing reservation and agreement-versus-household-only
comparisons have distinct baseline bindings. Raw signed connection response,
physical clipping, actor shortages, recharge and terminal inventory stay visible.
Reference idle keeps the DC path and total-connection response unknown while
preserving qualified active-converter component arithmetic and a separately
supplied E2 aggregate AC debit. Contract availability respects the unsplit retained
inventory floor; missing actor rows cannot erase established local violations.
Known-use lower bounds retain whole-window energy/duration and non-replenishing
budget contradictions across earlier allocation gaps while exact ledgers remain
Q. Possible recharge never becomes a fixed initial-budget cap.
Unqualified household correspondence retains upstream protection failures only
as diagnostics for their original subjects. No source, rights split,
dispatch priority, monetary value or permission is chosen by this consumer.

See the [versioned input/status registry](../../registry/b07_shared_use_schedule_contract.json)
and [checkpoint with usage and acceptance coverage](../../docs/checkpoints/V1_066_B07_SHARED_USE_SCHEDULE.md).
Actual site permission, commercial delivery, household economics and national or
network consequences keep their separate gates. Existing B07 APIs, numerical
behavior and readiness declarations are unchanged.

## Explicit reservation-study idealization

The local two-household SCN reuses the same B12 hourly controller/native B07
step. `annual_coordinated_pair()` qualifies the same8760-hour sources, then
audits HH1 and HH2 with separate actor/connection identities. Both start2kWh.
Independent charging is compared with at most one admitted charger each physical
hour: HH1 first, then alternate after admission; full/unsupported candidates are
skipped. No slot splitting, extra price window, reserve borrowing or new engine.
The shared3.436kW battery-charge cap follows from one native charger, not feeder
capacity. Other household load and idle accounting remain in the total import.
Each case's internal reservation-vs-household-only audit is distinct from the
main independent-vs-coordinated comparison. Report per-household evening battery
coverage, waiting, terminal stock and aggregate peak; do not infer national or
operator-service delivery. Lower peaks with missing service/stock are tradeoffs.

`CAPACITY_10KWH_20PCT_18_22_MAX_1_5KW_HOUSEHOLD_PRIORITY` removes only the
evening household discharge price threshold from the 10 kWh sensitivity.
The first 24 physical hours remain hold-only; cheap-price charging remains
00–06 and 10–16 Budapest. The 1.5 kW/load ceiling, 2 kWh protected pool,
initial inventory, curves, losses and transferred-parameter assumptions remain.
Its baseline is the separately preserved price-gated 10 kWh case. Report both
full-year and post-warmup peaks, rebound charging and unequal terminal stocks;
do not label household shifting as operator activation or national delivery.

`CAPACITY_10KWH_20PCT_18_22_MAX_1_5KW` is a separate owner-approved E2
capacity-sensitivity SCN. It uses 10 kWh in the discharged-DC-equivalent
coordinate, 2 kWh initial/protected inventory and at most 1.5 kW household AC
discharge from 18:00 inclusive to 22:00 exclusive Budapest time. Cheap charging
and price thresholds are unchanged. The measured 7.572 kWh reference is retained.

`capacity_sensitivity_reference()` changes only capacity and scenario identity.
It transfers the source curves, supported powers, cycle efficiency and 4.07 W
AC idle proxy without scaling as declared assumptions, not observations of a
10 kWh device. Its exact immutable parameter projection is hash-bound. The
zero-cell-idle opt-in accepts this one named projection; malformed variants and
generic synthetic references gain no waiver. Default idle remains Q. Native
source lineage is retained without granting product or market applicability.
The source-reference constructor still rejects changes under its measured
identity. No operator dispatch or guaranteed 6 kWh evening delivery is implied.

The B12 consumer accepts the explicit `HOUSEHOLD_18_22_MAX_1KW` policy:
18:00 inclusive to 22:00 exclusive Europe/Budapest, at most 1 kW AC toward the
observed hourly household load. Previous 24 closed-hour price conditions,
cheap 00–06/10–16 charging windows, physical curves and protected pool remain.
The default controller is preserved. This is a household-controller comparison
under the same reservation, not operator activation or guaranteed 4 kWh/day.

The isolated household-reference consumer in
`modules/B12/battery_reservation_reference.py` uses the existing SAX converter
and shared-use accounting. The default `run`/`step` idle boundary remains Q.
Only explicit `SCN_ZERO_CELL_SELF_DISCHARGE_SEPARATE_AC_STANDBY` opts into zero
cell-side inventory drain. This is an owner-selected idealization, not a source
measurement, a generic loss default or an actual-site approval. An already
unknown inventory cannot be repaired by the flag. The source-qualified AC idle
aggregate remains separate and is never added to active conversion losses.

The shared-use condition field carries the exact token and the comparison
identity binds it. On an idealized zero-flow interval, the pool audit requires
the preceding validated binary64 decomposition residual to remain exactly
unchanged; no new zero-flow or stock-sized tolerance is granted. Default
behavior and active-flow conservation tolerances stay unchanged.

The first reference comparison uses 1.5144 kWh in both initial inventories,
with a 1.5144 kWh protected pool in the reservation leg and no state activation.
It is a finite-horizon reservation study, not a tested service delivery. Initial
and terminal inventory stay explicit; neither annual cycling nor free terminal
credit is inferred. The price signal is retrospective HU wholesale EUR/MWh,
not A1 retail price; original load timestamps stay UTC2025. The first24 hours
are hold-only warmup with no fabricated prior prices. Missing required annual
prices stop the real-source calculation. No EV, planned export, H-tariff or VPP
permission, financial support, complete household protection or ROI is assumed.

## Durable project decisions

The [B07/B12 technical SCN contract](../../docs/checkpoints/B07_E2_OWNER_DECISIONS_20261026.md) describes the reference goals, physical assumptions, local result limits and coordinated-charge scope. Scenario parameters remain separate from exploratory scheduling examples and actual market permissions; public access to the identified local result artifacts is not established.

### Local E2 two-household shared charging budget (2026-10-27)

`B12.battery_reservation_reference.annual_shared_budget_pair` reuses the existing
native constant-hour physics and three distinct scenarios: independent,
whole-hour alternating, and shared-budget charging. The exact AC input budget
is `ref.charge.point(ref.charge.upper)[0]`, not its displayed rounded value and
not a feeder or total meter-import limit. Equal half budgets are first offered;
actual unused AC input is reassigned in ascending current inventory order,
with HH1 as deterministic tie-break. Full/unsupported cases are skipped using
the native curve domain; no extrapolation or subhour switching. Initial stock,
reserve, causal price history, cheap windows, evening priority and loss/idle
assumptions remain unchanged. Service and terminal stock may deteriorate: the
annual comparison must report these rather than silently tune the controller.
No network activation, national inference, funding revenue or ROI is implied.

The shared cap is enforced on exact rational representations of binary64
commands and admitted powers. Subtraction is conservatively rounded down when
needed; no physical tolerance permits cap excess. Decimal display/projection
may differ by approximately one ULP and is reported separately in evidence.
# Local E2 winter household-priority sensitivity (2026-10-27)

`modules.B12.battery_reservation_reference.WINTER_PRIORITY` is a separate,
owner-approved local SCN. December/January/February, determined in
Europe/Budapest, permits household discharge 15:00 inclusive to 22:00 exclusive;
15:00–16:00 charging is disabled even when discharge is physically unavailable.
Other months retain 18:00–22:00. Existing source curves, 10 kWh discharge-equivalent
capacity, initial/protected 2 kWh, household 1.5 kW actual-load cap, causal previous 24
closed physical-hour median, first 24-hour hold and shared AC charge budget are
unchanged. Default functions still select the old evening policy.

This is an in-sample sensitivity motivated by the same 2025 historical profiles,
not an out-of-sample controller validation, national result or operating right.
Earlier discharge can reduce later household battery coverage. The annual
comparison must retain every 18:00–22:00 service delta, recharge rebound, losses
and each actual terminal inventory; no free reset, assumed top-up or tuning to
erase an unfavorable tradeoff is permitted. Native B07 physics is unchanged.

# Local mixed-reference household pair (2026-10-27)

The explicit B12 `MIXED_HP_BASE` profile assignment selects the existing common
base plus W55 HP increment for HH1, and the same common base column alone for
HH2. No scaling, time shift or new profile shape is introduced. This is an
owner-approved two-reference-state SCN, not two independently observed homes.
Default calls retain the earlier identical-profile comparison.

Each household now supplies its own aligned LoadHour to the existing shared
charge allocator; its reservation-versus-household-only audit also uses that
same household's load. Profile assignment and selected columns are bound into
the scenario/provenance. The upstream full-profile A1 qualification is not
presented as qualification of the derived HH2 whole load. The existing source
hash and evidence debt remain available through the source baseline.

The mixed pair compares the original evening policy and the approved winter
policy with identical source inputs, initial inventories and physical limits.
Hourly own-load coverage, recharge, losses and terminal inventory must be
reported per household as well as jointly. No population weights, operating
rights, financial value or national relief is inferred.

# Local one-hour SCN signal stress test (2026-10-27)

`ONE_SIGNAL` is an optional, separately identified exception to the winter mixed
pair, not a live network request. It is issued 2025-01-03 08:00Z and valid only
09:00–10:00Z (10:00–11:00 Budapest). The date is a predeclared calendar rule,
not selected from historical peaks. No signal elsewhere; old defaults unchanged.

During that one hour charging is disabled. Extra own-load discharge is allowed
only above 2 kWh plus each household's most recent closed local 18–22 own-load
block converted through the existing discharge curve. The estimator uses own
base+HP load, not previously delivered battery energy, caps AC demand at 1.5 kW,
and does not apply charging/cycle losses again to discharge-equivalent stock.
Missing/duplicate/unsupported history is Q, never a zero estimate. No extra
discharge then; signal-hour charging remains disabled. A known zero block may
legitimately give zero. The computed stock floor is conservatively rounded up
only to avoid binary64 understatement; no discretionary safety factor is added.

First 24-hour hold, native power/stock/domain guards and no export remain. The
evening estimate is a persistence SCN, not guaranteed next-evening coverage.
The existing household-only audit is retained as a reference, not relabelled a
pure reserve-only causal effect after adding the signal response. The actual
comparison is against the accepted mixed winter pair, with all hourly evening
deltas, recharge, losses and terminal stock exposed. Current price vintage and
fast real-world load-following availability remain unverified; hourly own-load
following is the existing E2 response approximation. No operational entitlement,
national conclusion, financial value or publication is implied.

### Three consecutive predeclared SCN events (local successor)

`THREE_SIGNALS` adds only the owner-approved January 3-5 schedule: each event is
issued at 09:00 Budapest and valid 10:00-11:00 the same day. It uses the same
mixed winter pair, native physics and previous closed evening stock estimator.
No stock reset or special refilling occurs between events. Each ID is unique;
duplicate, unordered or overlapping schedules are rejected before execution.
The returned provenance distinguishes scheduled events from actually processed
ones when an input interval covers only part of the schedule. The original
single-event identity, no-signal default and their saved results are preserved.

Each event refreshes the estimate from its own latest fully closed 18-22 block.
Missing history stays Q and cannot reuse an older successful estimate. Repeated
responses can consume or defer energy and reduce later household service: this
is a stress test of persistence-based protection, not guaranteed evening cover,
real operational signal validation, national capability or financial value.

### Previous full winter 15-22 budget sensitivity (local successor)

`THREE_SIGNALS_FULL_BLOCK` retains the same three January 3-5 signals and all
physical/charging/discharging rules. Only their reserve estimate now uses the
previous complete local 15-22 own-consumption block (seven hours), converted by
the same native discharge inverse curve. Missing afternoon data remains Q even
when the old 18-22 subset is complete. There is no fallback to an older evening,
extra safety factor, forecast or stock reset. The separate case identity and
reserve-estimation provenance distinguish this sensitivity from the preserved
three-signal 18-22 case. Both are persistence SCNs, not future supply guarantees.
Legacy single-event, three-event and no-signal defaults keep their old meaning.

### Maximum of two prior complete winter blocks (local successor)

`THREE_SIGNALS_TWO_BLOCKS` preserves the January 3-5 events and all other rules.
It reserves 2 kWh plus the larger exact DC requirement of the last TWO complete
local 15-22 own-consumption blocks. Each block uses the same native inverse
discharge curve; the larger exact sum is selected before conservative binary
projection, with the latest block winning a tie. Both block records and the
selected date remain in provenance. Missing/invalid/unsupported history yields
Q/no extra discharge, without skipping gaps or reverting to a single block.
This is a separate approved E2 sensitivity, not a forecast guarantee or an
additional safety percentage; prior one-block variants remain unchanged.

### Conditional reference AC_GRID intake

`project_b08_reference` reuses native `step` for actual admitted AC flows and
post-step same-duration alternative charge/discharge bounds, including native
conservative clipping. These are conditional reference bounds, not changes
relative to a current command, simultaneous promises, installed ratings or
operator availability. The explicit reference reserve is physical input; the
2 kWh actor pool, estimator floors, household cap and shared charging budget
remain separate controller/rights constraints and must not be inferred from
the physical maxima. No controller or scenario is changed by this intake.

B08 `GridBoundaryRecord.from_discharge_equivalent_reference` admits only SCN
rows from the qualified named reference and explicit idle convention, rejecting
unknown inventory or required context. It includes disjoint household and HP
loads once, native admitted energy/duration, and provisional AC standby once
only for idle intervals. There is no PV/export scope. All five legacy diagnostic
fields are absent: discharge-equivalent x/C is not BMS SOC. Reference identity,
source IDs and exact input hash are in source_refs; callers retain the matching
input audit and qualified profile references. Outside-unit HP auxiliaries,
installed applicability and Q-B07-003 remain explicit debt. Legacy handoff and
existing tests retain their meaning; no national aggregation or rights follow.

