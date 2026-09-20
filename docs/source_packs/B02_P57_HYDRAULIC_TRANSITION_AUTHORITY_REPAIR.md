# B02-P57 — hydraulic transition authority repair

**State:** `CURRENT HYDRAULIC READINESS RETIRED AS NATIONAL PRECONDITION / FINISHED-SYSTEM HYDRAULIC TRANSITION GATE ADDED / PROGRAMME SUFFICIENCY STILL FAIL-CLOSED`

**Canonical base:** `6fc73b19668e7a26734878073a3175548bb0c98a`

**Implementation date:** 2026-09-20

## 1. Purpose

P57 resolves a semantic defect in the B02 technical-eligibility contract.

The former aggregate blocker asked whether the **current** building system was already hydraulically ready for a heat pump. That is too strong for a retrofit programme because an existing system may be reused, upgraded, or replaced.

Canonical boundaries:

`CURRENT HYDRAULIC READY != HEAT-PUMP TRANSITION POSSIBLE`

`CURRENT HYDRAULIC NOT READY != DWELLING TECHNICALLY INELIGIBLE`

`HYDRAULIC WORK REQUIRED != HYDRAULIC WORK OPTIONAL`

`REUSE / UPGRADE / REPLACE -> FINISHED-SYSTEM DESIGN -> COMMISSIONING`

P57 therefore removes `GAP-B02-S2-HYDRAULIC` from the **current national precondition** set and replaces it with a record/project-grain fail-closed hydraulic transition gate.

## 2. Evidence basis

### 2.1 Existing Hungarian source already in the repository

B02-P50 records the official ZFR-TÁV/2019 programme guide. The required project technical description includes:

- design secondary temperatures;
- flow rates;
- hydraulic resistance/topology;
- typical emitter types/connections;
- hydraulic balancing concept.

This is project-design information. It is evidence that the hydraulic state can be an explicit retrofit design output rather than a pre-existing national stock property.

P50 additionally records a 2025 PTE residential panel study in which lower-temperature operation is conditional on maintaining required design flow and a suitable hydraulic system. That supports a transition-design gate, not a national ready/not-ready stock flag.

### 2.2 Current MCS design / installation authority

Current MCS heat-pump design guidance requires a system design that determines the proposed emitter arrangement, design flow temperature and system operating requirements, followed by installation/commissioning of the finished system.

P57 uses this only as engineering-method authority. It does not import UK eligibility law into Hungary.

## 3. New canonical hydraulic question

The programme question becomes:

> Can the finished heat-pump system be hydraulically designed and commissioned for this record/project, with reuse, upgrade or replacement explicit?

Three transition paths are admitted:

1. `REUSE_EXISTING_HYDRAULICS`
2. `UPGRADE_EXISTING_HYDRAULICS`
3. `REPLACE_DISTRIBUTION_HYDRAULICS`

For reuse/upgrade, current-system survey evidence is mandatory.

For full replacement, current hydraulic adequacy is not required, but the **new system design is still mandatory**.

## 4. Fail-closed design inputs

A qualified hydraulic transition requires:

- explicit transition path;
- current topology + pipe/manifold basis for reuse/upgrade;
- positive required design flow rate;
- positive required pump head;
- documented system-volume / defrost basis;
- balancing and control plan;
- flush/fill/water-quality plan;
- commissioning plan;
- evidence references;
- reproducible repository binding.

Missing any required input returns `Q`.

## 5. Programme effect

P57 closes only this obsolete aggregate blocker:

`GAP-B02-S2-HYDRAULIC as CURRENT-STOCK NATIONAL PRECONDITION -> RETIRED`

It does **not** assert that Hungarian dwellings are hydraulically ready.

Hydraulic engineering remains mandatory at record/project level and feeds B06/B18 implementation scope and CAPEX.

The remaining current B02 national evidence blockers stay fail-closed.

## 6. Historical preservation

P2/P3/P5 source packs are historical records and are not rewritten.

The gap-matrix row for hydraulic readiness is retained as historical/current-source context, but it is no longer consumed by the canonical current repository technical-eligibility blocker set.

`HISTORICAL GAP RECORD != CURRENT CANONICAL BLOCKER`
