# B10-P5 — Programme-incremental reinforcement requirement & CAPEX attribution gate

## Purpose

B10-P5 creates the executable fail-closed boundary between published DSO
headroom screening, an authoritative reinforcement determination, the canonical
B10-P3 `WITHOUT_PROGRAM` / `WITH_PROGRAM` attribution decision and numeric
programme-incremental CAPEX.

The governing rule is:

`PUBLISHED HEADROOM EXCEEDANCE != PROVEN REINFORCEMENT PROJECT != PROVEN REINFORCEMENT COST != PROVEN PROGRAMME-INCREMENTAL CAPEX`.

B10-P5 does **not** publish a Hungarian reinforcement cost proxy. The repository
currently has no programme-demand mapping to exact DSO substations, no
programme-specific MGT/network-study reinforcement decisions and no separable
programme-incremental reinforcement-cost observations.

## Official MVM process authority

Fresh audit date: 2026-09-02.

The official MVM Démász page
`https://mvmhalozat.hu/aram/oldalak/1477`, titled
**“ÚJ CSATLAKOZÁS, TELJESÍTMÉNYNÖVELÉS, FÁZISBŐVÍTÉS HÁLÓZATÉPÍTÉSSEL”**, states
that when no public network is available nearby or the requested capacity cannot
be served from the existing network, public-network construction, connection
line and metering work may be necessary. After the request, MVM performs a site
survey and sends a műszaki-gazdasági tájékoztató (MGT). The MGT states the
necessary network-construction works, their expected implementation deadline
and estimated payable costs. Later, after detailed design, the costs are
refined before the network-connection contract and payment request.

This source is an authority for the **process boundary** only. It does not prove
that the proposed heat-pump/battery programme causes any specific reinforcement,
it is not a nationwide reinforcement-cost dataset and its customer-payable
amounts are not automatically equal to total DSO reinforcement investment or
programme-incremental CAPEX.

## Published headroom is screening only

B10-P1 and B10-P2 remain authoritative for their own source-native headroom
semantics. Published free capacity remains indicative network information and
not an individual connection decision. `MGT_REQUIRED` remains the connection
authority boundary.

P5 therefore uses only these screening states:

- `WITHIN_PUBLISHED_HEADROOM_SCREENING`;
- `EXCEEDS_PUBLISHED_HEADROOM_SCREENING`;
- `Q`.

Even when programme demand exceeds published headroom, the only supported
statement is that the programme demand exceeds the published screening value and
an individual DSO/MGT/network-study investigation is required. It does not prove
a transformer replacement, feeder reinforcement, new substation, timing or
cost.

Conversely, demand within the published scalar headroom does not prove
`NO_REINFORCEMENT_REQUIRED`. Voltage, short-circuit level, protection, network
topology, medium/low-voltage constraints and quality requirements remain outside
the scalar screening value.

## Grain and horizon

A screening-linked P5 record requires exact continuity of:

- network operator;
- `DSO_SUBSTATION` region identity;
- planning horizon.

`CURRENT` and `FIVE_YEAR` remain distinct. No interpolation or silent horizon
substitution is allowed.

P5 rejects national, ENTSO-E control-area, county, settlement,
`DSO_SERVICE_AREA`, household-count, population-share and consumption-share
records when used as if they were exact substation mappings. The two P4 RRF
baseline projects remain service-area umbrella projects and cannot become P5
node mappings. Q-B01-002 therefore remains open.

## Screening truth

A screening computation is derived truth, never source-native OBS:

- Q input propagates Q;
- SCN programme demand remains SCN-bounded;
- otherwise a valid comparison is at most DER;
- missing remains missing and is not zero;
- negative/non-finite quantities fail closed.

## Reinforcement evidence gate

B10-P5 reuses the canonical B10-P3 `InfrastructureEvidence` hierarchy and P3
classifier. It does not create a competing project-attribution model.

For a P3 difference flag to be accepted by P5, referenced evidence must carry
claim-specific support bound to the same project, operator, exact
`DSO_SUBSTATION` region and horizon. The bounded claims are:

- `REINFORCEMENT_REQUIRED`;
- `INCREMENTAL_SCOPE`;
- `INCREMENTAL_CAPACITY`;
- `ACCELERATION`;
- `UPSIZE`.

Headroom screening alone can never set any of these P3 flags.

Programme causality remains governed by P3 and can never be OBS. `DER`, `SCN`
and `Q` remain the only allowed causality truths. Temporal coincidence is not
causality.

## Three separate cost concepts

P5 explicitly distinguishes:

1. `CUSTOMER_CONNECTION_CHARGE_HUF`;
2. `TOTAL_REINFORCEMENT_PROJECT_COST_HUF`;
3. `PROGRAM_INCREMENTAL_CAPEX_HUF`.

They are not interchangeable.

An exact customer-payable MGT amount does not automatically establish total DSO
reinforcement project CAPEX and does not automatically establish programme
incremental CAPEX. A total reinforcement-project cost also cannot be copied into
the programme ledger.

## Claim-specific programme CAPEX authority

P3 generic `COST` authority remains necessary for numeric cost, but P5 adds a
more specific gate. Numeric programme CAPEX requires:

- exact project identity;
- exact `cost_component_id`;
- referenced evidence bound to the same operator, node and horizon;
- P3-compatible `COST` support;
- and at least one relevant claim-specific cost authority:
  - `PROGRAM_INCREMENTAL_COST`,
  - `ACCELERATION_COST`, or
  - `UPSIZE_COST`.

Generic `COST`, `CUSTOMER_CONNECTION_CHARGE` or
`TOTAL_REINFORCEMENT_PROJECT_COST` support alone is insufficient. A manually
selected smaller value is also insufficient. Evidence for one project or cost
component cannot authorize another.

The existing P3 full-project-cost-copy and baseline/incremental double-count
guards remain unchanged.

## Registry outcome

`registry/incremental_capex_attribution.csv` remains header-only in P5. This is
intentional, not missing implementation. There is no source-supported real
programme-incremental reinforcement row yet.

`registry/baseline_infrastructure.csv` remains the two P4 observed RRF baseline
projects only. They are not reclassified as programme-induced infrastructure.

Q-B10-001 remains `OPEN / PARTIALLY_BOUNDED`. P5 adds the executable physical
and evidence gate that must be satisfied before a real reinforcement delta or
numeric programme CAPEX can be attributed. Still missing are actual
programme-demand-to-node mapping, real DSO/MGT studies, exact programme-caused
scope and separable incremental cost evidence.

Q-B10-002 remains `OPEN`; P5 is not a fulfilment-probability model. B10 readiness
remains 15 because no real programme-specific reinforcement/CAPEX evidence has
been added.

## Explicit exclusions

No national CAPEX, Ft/kW proxy, national headroom, third DSO adapter,
county↔DSO or ENTSO-E↔DSO mapping, household/B01-to-substation allocation,
OPUS generic assessment adapter, power-flow, voltage-drop, short-circuit,
feeder topology, reinforcement optimisation, project scheduling, actual MGT
submission or Q-B10-002 closure is included.
