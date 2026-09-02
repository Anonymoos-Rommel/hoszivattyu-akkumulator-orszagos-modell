# B10-P9 — Programme demand → exact DSO node aggregation gate

Canonical base: `5ddb22fce84ae58cc808d35252052ed00f416135`

## Core rule

`HOUSEHOLD LOCATION != PROVEN DSO NODE != PROGRAMME ELECTRIC LOAD != SIMULTANEOUS NODE PEAK != HOSTING CAPACITY`

B10-P9 adds no new external network fact. It is a contract/integration slice over
already canonical B05/B07/B08 physical-load boundaries, the B10-P8 exact spatial
authority gate, and the B10-P1 source-native headroom screening contract.

## Existing canonical inputs

- B05 exposes explicit heat-pump electrical demand at physical operating points and
  simulation timesteps. B10-P9 does not replace the B05 physical model.
- B07 keeps battery power at the AC/grid-side boundary and exposes battery charging
  separately from discharge/flexibility. B10-P9 may consume the positive charging
  component, but it does not net discharge or physical flexibility against load.
- B08 already aggregates explicit timestamped AC-grid boundary records and rejects
  population scaling, inferred missing values and mixed region schemes. P9 does not
  duplicate B08's system-load engine or reinterpret ENTSO-E control-area geography.
- B10-P8 is the only P9 spatial handoff: the same entity must be `EXACT_NODE_PROVEN`
  at the exact `DSO_SUBSTATION` node. Service-area membership, administrative
  location, postcode/municipality, proximity or confidence are insufficient.
- B10-P1 remains the MVM Démász source-native headroom screening authority. P9 can
  hand a proven node peak into that existing screening function only on the exact
  same node key. The result remains `MGT_REQUIRED` and is not hosting-capacity or
  reinforcement authority.

## Executable P9 boundary

`ProgrammeDemandSnapshot` is one explicit entity/timestamp decomposition with:

- heat-pump import kW;
- battery charging import kW;
- other programme import kW explicitly excluding the first two components;
- P8 spatial-authority decision;
- truth context and evidence status;
- source references.

All three numeric components are mandatory. A genuinely absent component is an
explicit `0`; omission is never interpreted as zero.

The contract accepts only a complete Cartesian entity × timestamp panel for one
bounded `scope_id`. It rejects duplicate rows, mixed truth contexts and inconsistent
timesteps. If any entity has unresolved exact-node authority, any row has `Q` demand
evidence, or an entity's node binding changes inside the panel, the result is
`Q_NODE_DEMAND_UNRESOLVED` and contains **no numeric node rows or peaks**.

This is deliberate: an unresolved entity could belong to any candidate node, so a
partial node total cannot be published as the programme total for that node.

## Simultaneity and peak semantics

For a proven complete panel, P9 first sums entities **within the same timestamp and
exact node**, then selects the maximum explicit timestamped node total.

Therefore:

`SUM(NAMEPLATE_KW) != COINCIDENT_NODE_PEAK_MW`

P9 does not create a diversity/coincidence factor. It uses only the explicit common
timestep panel. The resulting peak semantics are:

`UNMANAGED_POSITIVE_PROGRAMME_IMPORT`

with management authority:

`NO_DIVERSITY_OR_FLEX_AUTHORITY`

Battery discharge, VPP dispatch, pre-heating/load shifting and guaranteed flexibility
are intentionally excluded. Those belong to the later managed-peak / physical
survivability gate.

## Headroom handoff

`screen_programme_node_peak_against_mvm_headroom()` delegates to the existing P1
`assess_incremental_demand()` contract and therefore requires exact node identity.
The output is only an indicative published-headroom screening result. It does not
prove:

- hosting capacity;
- safe/unsafe operation;
- MGT approval;
- reinforcement requirement;
- reinforcement project identity;
- programme-incremental CAPEX;
- managed peak;
- network physical survivability.

OPUS TITÁSZ remains source-native and separate. P9 does not invent a cross-DSO
headroom normalisation or an OPUS assessment adapter.

## Explicit non-results

B10-P9 publishes no:

- county → DSO mapping;
- settlement/postcode → substation mapping;
- nearest-node GIS truth;
- national DSO coverage;
- national programme peak;
- generic diversity factor;
- battery/VPP managed-peak claim;
- hosting-capacity claim;
- reinforcement requirement;
- programme CAPEX;
- readiness uplift.

`regional_readiness.csv` and `incremental_capex_attribution.csv` remain unchanged.
Q-B01-002, Q-B10-001 and Q-B10-002 remain open/bounded as before. B10 readiness
remains 15%.
