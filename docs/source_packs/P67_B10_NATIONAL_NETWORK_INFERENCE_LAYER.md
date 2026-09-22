# B10-P67 — national network-impact inference layer

## Purpose

P67 applies the project-wide population-inference policy to B10.

The old implicit requirement that national programme modelling must wait for a complete Hungarian DSO node inventory is retired.

Core rules:

`NO COMPLETE NATIONAL NODE INVENTORY != NATIONAL MODEL BLOCKED`

`NO DEFENSIBLE NETWORK POPULATION INFERENCE == NATIONAL MODEL BLOCKED`

`NATIONAL NETWORK ESTIMATE != SPECIFIC NODE PASS/FAIL`

`PUBLIC REPOSITORY MATERIALIZATION != MODEL USABILITY`

## Two evidence planes

### National / programme plane

A bounded national network-impact estimate may be built from:

- operational DSO service-area coverage;
- representative DSO/node headroom evidence;
- explicit programme-demand distributions by DSO/network stratum;
- representative reinforcement-project cohorts;
- programme-incremental attribution distributions;
- managed-peak/survivability evidence;
- delivery-timing distributions;
- explicit population calibration and uncertainty propagation.

A complete national node digital twin is not a prerequisite for this layer.

### Exact node / project plane

Specific claims remain fail-closed:

- exact entity -> DSO substation demand;
- exact limiting node;
- exact reinforcement requirement;
- exact DSO/MGT/network-study decision;
- exact programme-incremental project CAPEX;
- exact timed CAPEX schedule.

P8/P9/P10/P26/P28-P33 exact-lineage rules remain authoritative for those claims.

## Existing evidence already usable

P64 accepted the current resolved-only service-area surface as operationally complete:

- 3,155 settlements total;
- 3,052 exact whole-settlement memberships;
- 1 exact partial-only usage-location resolution;
- 96.767036% any effective resolved settlement presence;
- 3.232964% no materialized effective resolution.

The unresolved residual remains Q and may not be imputed.

All six canonical DSOs have a bounded current consumption-side node-bearing publication source in `registry/dso_node_inventory_sources.csv`.

This proves source coverage, not complete node inventories.

The baseline infrastructure ledger contains two completed RRF DSO projects from two operators. They are useful calibration cases but are not a representative programme-incremental reinforcement/CAPEX cohort.

## Blocker repairs

### Spatial completeness

`NO_COMPLETE_KSH_DSO_MEMBERSHIP_CROSSWALK`

and

`PARTIAL_SETTLEMENT_USAGE_LOCATION_RESOLUTION_REQUIRED`

are retired as all-or-nothing national-modelling blockers.

Replacement:

`DISCLOSED_RESIDUAL_SPATIAL_UNCERTAINTY_REQUIRED`

Exact claims about unresolved locations still require exact evidence.

### Complete node inventory

`NO_COMPLETE_NATIONAL_DSO_NODE_INVENTORY`

is retired as a blocker for national expected-impact estimation.

Replacement:

`DEFENSIBLE_REPRESENTATIVE_NODE_COHORT_REQUIRED`

A complete relevant node authority remains necessary for exhaustive limiting-node claims.

### Public-repository materialization

`PUBLISHED_NODE_SET_REPOSITORY_MATERIALIZATION_BLOCKED`

is retired as a public-repository prerequisite for model use.

Replacement:

`SOURCE_ACCESS_PROVENANCE_AND_RUNTIME_USE_AUTHORITY_REQUIRED`

Raw republication still requires source-specific reuse permission.

### Programme node demand

`NO_REAL_PROGRAMME_NODE_PANEL`

becomes:

`DEFENSIBLE_PROGRAMME_DEMAND_DISTRIBUTION_BY_DSO_STRATUM_REQUIRED`

A specific-node claim still requires exact entity-to-node mapping.

### Reinforcement / CAPEX

`INCREMENTAL_CAPEX_ATTRIBUTION_HEADER_ONLY`

becomes:

`REPRESENTATIVE_REINFORCEMENT_COHORT_AND_INCREMENTAL_CAPEX_DISTRIBUTION_REQUIRED`

Exact project programme-CAPEX claims still require the P3/P5/P31/P32 lineage.

### Timing

`NO_REAL_TIMED_PROGRAMME_CAPEX`

becomes:

`DEFENSIBLE_REINFORCEMENT_DELIVERY_TIMING_DISTRIBUTION_REQUIRED`

Exact timed project CAPEX still requires P11/P32/P33 lineage.

## Current admission state

P67 does not mint a national network-impact number.

The national plane is currently:

`Q_NATIONAL_NETWORK_INFERENCE`

because the following are still missing:

- programme demand distribution by DSO/network stratum;
- representative numeric headroom cohort;
- representative programme reinforcement/CAPEX cohort;
- representative delivery-timing cohort;
- representative survivability evidence;
- explicit network-population calibration;
- explicit uncertainty propagation.

This is a materially narrower and achievable evidence problem than requiring a complete national node inventory.

## Readiness

B10 remains **15%**.

P67 repairs the evidence architecture but does not invent numeric national network outputs, so no arbitrary readiness uplift is applied.
