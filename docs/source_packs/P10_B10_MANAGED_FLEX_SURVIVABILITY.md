# B10-P10 — Managed peak / flexibility / physical-survivability authority gate

Canonical base: `b4df334fa12b89186d25e8999db7927de433f947`

## Core rule

`PHYSICAL FLEX CAPABILITY != COMMITTED/AVAILABLE FLEX != DISPATCHED/DELIVERED FLEX != MANAGED NODE LOAD != NETWORK SURVIVABILITY`

B10-P10 is an authority/integration slice. It does not create new Hungarian
network capacity, VPP participation, dispatch history or network-study facts.

## Existing canonical inputs

- B07 exposes a physical battery flexibility envelope at the AC/grid-side
  boundary. Its own readiness snapshot keeps `VPP_MARKET_INTERFACE_READY = NO`.
- B08 carries physical up/down-flex diagnostics but explicitly does not dispatch
  assets or make headroom/reinforcement decisions.
- B10-P8 is the exact DSO_SUBSTATION spatial authority gate.
- B10-P9 creates an unmanaged positive programme-import panel from the exact
  entity/timestamp/node lineage and does not apply a diversity/flex offset.
- B10-P5 remains the reinforcement/CAPEX authority gate.

## External authority audit

Official EU electricity-market rules support the separation used here:

1. Commission Regulation (EU) 2017/2195, Article 16 requires a balancing service
   provider to qualify before providing balancing-energy/capacity bids. Article
   18 separately requires rules for qualification, procurement/transfer of
   balancing capacity, aggregation, data exchange and evaluation of service
   provision. Source: `https://eur-lex.europa.eu/eli/reg/2017/2195`.
2. Regulation (EU) 2019/943, Article 13 treats redispatch of generation, energy
   storage and demand response as an explicit system action selected under
   defined mechanisms; technical capability alone is not the redispatch event.
   Source: `https://eur-lex.europa.eu/eli/reg/2019/943/oj/eng`.

These sources justify a gate between physical capability and dispatch/service
provision. They do **not** prove that any household battery in this programme is
qualified, contracted, activated or delivered in Hungary.

## Executable P10 boundary

`FlexDispatchSnapshot` preserves, per exact entity/timestamp/node:

- physical up-flex capability kW;
- committed up-flex kW;
- dispatched up-flex kW;
- delivered up-flex kW;
- truth context and claim-specific evidence.

Numerically:

`delivered <= dispatched <= committed <= physical capability`.

The numerical ordering is necessary but not sufficient authority.

### REAL truth

A REAL managed reduction requires separately referenced, entity/node/timestamp
bound evidence for:

- physical capability;
- commitment;
- activation;
- delivered flexibility.

A dispatch command without delivered-flex proof remains Q for REAL managed-load
arithmetic.

### SCN truth

An explicit SCN dispatch may reduce an SCN managed-load path only when activation
is explicitly bound to the same entity/node/timestamp. It remains a scenario
result and cannot be promoted to observed/guaranteed VPP delivery.

### Commitment and capability

Physical capability alone subtracts zero.
A proven commitment without dispatch/delivery also subtracts zero.

## Exact entity lineage

P10 consumes the original P9 `ProgrammeDemandSnapshot` panel and re-runs the P9
aggregation contract. The flex panel must contain exactly the same entities and
timestamps, with each flex row on the same P8-proven DSO_SUBSTATION node and the
same timestep.

Missing entity/timestamp/node lineage is not zero and cannot be repaired by a
count, confidence score, service-area share or proximity proxy.

If any flex row is unresolved, the managed-load result is
`Q_MANAGED_NODE_LOAD_UNRESOLVED` with no numeric managed rows or managed peaks.

## Managed-load semantics

Only sufficiently authorised dispatch/delivery is subtracted from the P9
positive programme import. P10 does not allow flex to create negative programme
import; reverse-power-flow/export authority is separate.

The output may be:

- `MANAGED_NODE_LOAD_PROVEN` for bounded REAL delivered-flex evidence;
- `SCN_MANAGED_NODE_LOAD` for explicit scenario dispatch;
- `Q_MANAGED_NODE_LOAD_UNRESOLVED` otherwise.

These statuses are **not** hosting-capacity, MGT, safe/unsafe or reinforcement
statuses.

## Physical network survivability

A managed peak, a P1 headroom screening result and a flex quantity cannot prove
physical network survivability.

`evaluate_network_survivability()` requires a separately referenced high-authority
DSO/network-study claim bound to:

- network operator;
- exact network-study ID;
- exact DSO_SUBSTATION node;
- the assessed managed peak value;
- an explicit `NETWORK_SURVIVABILITY` claim.

Without that, status remains `Q_NETWORK_SURVIVABILITY_UNRESOLVED`.

Even a proven survivability decision does not mint reinforcement project identity,
programme causality or programme-incremental CAPEX; those remain P3/P5 questions.

## Explicit non-results

B10-P10 publishes no real programme VPP dispatch/delivery rows and no real network
survivability row. It creates no:

- generic diversity factor;
- assumed VPP availability percentage;
- guaranteed battery response;
- county/DSO or settlement/substation mapping;
- national DSO coverage or national managed peak;
- hosting-capacity claim;
- reinforcement requirement/project;
- programme-incremental CAPEX;
- readiness uplift.

`regional_readiness.csv` and `incremental_capex_attribution.csv` remain unchanged.
B10 readiness remains 15%.
