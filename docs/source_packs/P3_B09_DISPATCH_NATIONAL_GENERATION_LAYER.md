# B09-P3 — dispatch/storage boundary and national generation layer

## Purpose

P3 resolves the B09 dispatch/storage authority question and separates national Hungarian control-area generation from regional DSO/county generation claims.

Core rules:

`HOUSEHOLD_B07_DISPATCH_ALREADY_IN_B08_LOAD != B09_SYSTEM_STORAGE`

`PHYSICAL_RESIDUAL_SURPLUS != DISPATCH_DECISION`

`NATIONAL_CONTROL_AREA_GENERATION != REGIONAL_DSO_COUNTY_GENERATION`

`PUBLIC_REPOSITORY MATERIALIZATION != MODEL_USE_AUTHORITY`

## Physical adequacy baseline

B09-P1 remains the default physical adequacy model.

It compares B08 net grid load against explicit generation and produces:

- residual demand;
- unserved/residual load;
- surplus supply;
- energy integrals;
- physical residual/surplus peaks.

These are physical identities only.

They do not imply:

- dispatch;
- curtailment;
- reserve activation;
- market commitment;
- economic optimization;
- monetizable system value.

## Household battery boundary

The B07 household battery action is already reflected before B09:

`B07 -> B08 grid-load handoff -> B09 adequacy`

Therefore the same household battery must not be dispatched again inside B09.

B08 `physical_up_flex_kw` and `physical_down_flex_kw` are capability limits, not dispatch instructions.

## Optional system-storage dispatch

P3 permits a future separate system-storage path, but only as:

`EXPLICIT_SYSTEM_STORAGE_SCHEDULE`

This route requires:

- separate system-storage asset identity;
- explicit charge/discharge schedule;
- power and energy limits;
- explicit SOC state transition;
- storage-efficiency authority;
- schedule evidence/scenario authority.

No implicit optimizer is introduced.

Even a physically valid schedule does not establish market optimality, reserve qualification or monetary value.

## National observed-generation layer

B09-P2 already establishes source-native ENTSO-E generation semantics:

- A75 Actual Generation per Production Type;
- A16 Realised;
- A08 resource-type aggregation;
- Bxx production types;
- Hungarian area `10YHU-MAVIR----U`;
- PT15M/PT30M/PT60M source intervals;
- UTC/provenance/checksum contract.

P3 clarifies:

`NO DSO/COUNTY GENERATION PANEL != NATIONAL GENERATION BASELINE BLOCKED`

The source-native Hungarian control-area series can support a national generation baseline without first constructing regional generation.

A real numeric national generation baseline still requires:

- real acquired A75 panel;
- source-specific model-use authority;
- complete acquisition provenance;
- explicit expected production-type manifest so missing types are not silently converted to zero.

## Regional generation boundary

National control-area generation cannot be:

- relabelled as DSO generation;
- relabelled as county generation;
- spatially split by production type without evidence.

Regional adequacy requires compatible regional load and generation grain or a separately validated calibrated mapping contract.

## Source permission boundary

Model-use authority and public-repository redistribution are separate.

P3 does not grant A75 raw-response reuse permission and does not add raw ENTSO-E values to the repository.

## Open-question effect

### Q-B09-002

`RESOLVED_CONTRACT`

The architecture is now explicit:

- default physical adequacy = no dispatch;
- B07 household storage already affects B08 and cannot be double counted;
- optional system storage requires a separate asset/SOC/schedule authority.

### Q-B09-001

`OPEN_NARROWED`

Regional generation is no longer a prerequisite for a national Hungarian control-area generation baseline.

Remaining national blockers are:

- real numeric A75 acquisition;
- source-specific model-use authority;
- acquisition provenance;
- complete production-type manifest.

## Readiness

B09 remains **35%**.

P3 resolves the architecture question and narrows the national evidence problem, but no real national numeric generation snapshot or dispatch result has been admitted.
