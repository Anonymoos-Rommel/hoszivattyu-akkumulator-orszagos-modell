# B10-P34 — E.ON current consumption-capacity source resolution

Status date: 2026-09-04
Canonical base: `f7853345396cbc5e42e27722c8ee34df8e54d6d1`

## Purpose

P34 is an evidence-only slice. It introduces no new authority contract or semantic gate.

Its only purpose is to revisit the three exact P23 source-discovery blockers:

- `Q-B10-P23-ELMU-2026-CONSUMPTION-PUBLICATION-URL`;
- `Q-B10-P23-EON-DDASZ-2026-CONSUMPTION-PUBLICATION-URL`;
- `Q-B10-P23-EON-EDASZ-2026-CONSUMPTION-PUBLICATION-URL`.

The governing boundary remains:

`MANDATORY PUBLICATION DUTY != PINNED PUBLICATION URL != NODE-BEARING SOURCE != COMPLETE OPERATOR NODE INVENTORY`

and:

`NODE-BEARING SOURCE != REPOSITORY-MATERIALIZED NODE SET != COMPLETE NETWORK TOPOLOGY`

## New evidence

### 1. ENTSO-E / EU DSO Entity Capacitypedia

The joint ENTSO-E / EU DSO Entity TSO-DSO Cooperation Platform lists a dedicated **E.On Hungary** DSO profile in Capacitypedia:

`https://www.tsodsoplatform.eu/capacitypedia/hungary/eon-hungary`

The Capacitypedia recent-update log records the E.On Hungary DSO subpage as added on **2026-07-20**.

The E.On Hungary profile states that the grid-hosting-capacity publication is **Published** and supplies the following public access link:

`https://www.eon.hu/hu/lakossagi/ugyintezes/kiemelt-informaciok/szabad-kapacitas.html`

The DSO-submitted metadata states:

- geographic coverage: the three E.ON Hungarian DSOs — **ELMŰ, ÉDÁSZ, DÉDÁSZ**;
- spatial granularity: **nodal (substation), HV/MV**;
- voltage coverage: 132 kV and HV/MV substations;
- time horizon: **2026Q1** and **2031Q1 (Y+5)**;
- format: **table**;
- displayed capacity types: **available, requested**;
- update frequency: **quarterly**.

This is materially stronger than the P23 search state because it identifies the exact operator publication page and explicitly binds that page to all three E.ON DSOs and nodal HV/MV hosting-capacity information.

### 2. Official E.ON publication target

The supplied Capacitypedia access link resolves to the official E.ON page titled **Szabad kapacitás**:

`https://www.eon.hu/hu/lakossagi/ugyintezes/kiemelt-informaciok/szabad-kapacitas.html`

The page is dynamically rendered in the auditable web environment, so P34 does **not** claim source-native row extraction from the E.ON page itself.

Therefore:

`OFFICIAL CURRENT PAGE PINNED != SOURCE-NATIVE ROWS EXTRACTED`

### 3. Legal publication duty remains separately proven

P23 already pinned the current consolidated 273/2007. (X. 19.) Korm. rendelet:

`https://njt.jog.gov.hu/jogszabaly/2007-273-20-22`

The legal source proves the 2026 MV/HV publication duty. P34 does not use the legal duty to infer the URL; the URL is now independently pinned by the E.On Hungary DSO submission in Capacitypedia.

## Registry effect

`registry/dso_consumption_publication_authorities.csv` now replaces the three P23 URL-Q rows with current P34 source-authority rows.

`registry/dso_node_inventory_sources.csv` now records all three E.ON operators as:

`NODE_BEARING_SOURCE_BOUNDED`

with source semantics:

`PUBLISHED_CONSUMPTION_HEADROOM_NODE_SET`

The source URL is the same official E.ON page because the Capacitypedia DSO submission explicitly states that the page covers all three E.ON Hungarian DSOs.

## What P34 clears

The following blockers are cleared:

- `Q-B10-P23-ELMU-2026-CONSUMPTION-PUBLICATION-URL`;
- `Q-B10-P23-EON-DDASZ-2026-CONSUMPTION-PUBLICATION-URL`;
- `Q-B10-P23-EON-EDASZ-2026-CONSUMPTION-PUBLICATION-URL`.

This means all six Hungarian DSO operator rows now have a bounded consumption-side node-bearing publication source.

## What P34 does NOT clear

P34 does not prove that any one of those publication sets is an exhaustive physical node inventory.

The following remain active:

- `NO_COMPLETE_NATIONAL_DSO_NODE_INVENTORY`;
- `PUBLISHED_NODE_SET_REPOSITORY_MATERIALIZATION_BLOCKED`;
- `HEADROOM_NODE_SET_NOT_INVENTORY_COMPLETENESS`;
- `NO_COMPLETE_KSH_DSO_MEMBERSHIP_CROSSWALK`;
- `PARTIAL_SETTLEMENT_USAGE_LOCATION_RESOLUTION_REQUIRED`;
- `NO_REAL_PROGRAMME_NODE_PANEL`;
- `NO_REAL_MANAGED_PEAK_SURVIVABILITY_STUDY`;
- `NO_REAL_TIMED_PROGRAMME_CAPEX`;
- `INCREMENTAL_CAPEX_ATTRIBUTION_HEADER_ONLY`.

No E.ON node rows are copied into the repository in P34. No completeness, topology, entity-to-node mapping, limiting-node, reinforcement, CAPEX or timing claim is minted.

## Closure effect

P34 removes three stale source-discovery blockers from the limiting-node closure audit and records `B10-P34` as the current E.ON source-resolution reference.

The primary B10 outputs remain unpopulated and the substantive programme-specific evidence gaps remain. B10 therefore remains `IN_PROGRESS`; readiness remains **15%**.
