# B10-P14 — national DSO operator inventory and territorial grain

## Purpose

P14 removes the coarse `NO_NATIONAL_DSO_COVERAGE` blocker only at the operator-inventory level. It does **not** claim a complete settlement-to-DSO membership crosswalk, national DSO node inventory, household-to-node mapping, hosting capacity, reinforcement requirement or programme CAPEX.

Core rule:

`NATIONAL DSO OPERATOR INVENTORY != SERVICE-AREA MEMBERSHIP CROSSWALK != EXACT DSO NODE INVENTORY != HOUSEHOLD → EXACT NODE MAPPING`

## Current public-source audit — 2026-09-02

### Current electricity distribution licensee set

MVM Next's current technical-administration page directs users to the territorially competent electricity distribution licensee and lists the following six operators:

1. ELMŰ Hálózati Kft.
2. E.ON Dél-dunántúli Áramhálózati Zrt.
3. E.ON Észak-dunántúli Áramhálózati Zrt.
4. MVM Démász Áramhálózati Kft.
5. MVM Émász Áramhálózati Kft.
6. OPUS TITÁSZ Áramhálózati Zrt.

Source:

- `SRC-B10-HU-DSO-CURRENT-LIST-2026`
- https://www.mvmenergiakereskedo.hu/oldalak/70562

A separate current MVM Hálózat safety/public-service page again names the same six operators and attaches broad service-area labels:

- ELMŰ Hálózati Kft. — Budapest és Pest vármegye;
- E.ON Észak-dunántúli Áramhálózati Zrt. — Észak-dunántúli régió;
- E.ON Dél-dunántúli Áramhálózati Zrt. — Dél-dunántúli régió;
- MVM Émász Áramhálózati Kft. — Észak-magyarországi régió;
- MVM Démász Áramhálózati Kft. — Dél-alföldi régió;
- OPUS TITÁSZ Áramhálózati Zrt. — Tiszántúli régió.

Source:

- `SRC-B10-HU-DSO-REGION-LABELS-2026`
- https://www.mvmhalozat.hu/aktualitasok/82858

These sources are sufficient for the **current six-operator inventory** and broad public service-area labels. They are not a normalized polygon or settlement-membership dataset.

### Why administrative geography cannot be promoted to electrical geography

The official MVM Démász service-area page states that the service-area settlement list is contained in the operating licence and distribution business rules, publishes settlements by county, and separately lists settlements where only a **part** of the administrative settlement belongs to the MVM Démász low-/medium-voltage service area.

Source:

- `SRC-B10-MVM-DEMASZ-SERVICE-AREA-2026`
- https://mvmhalozat.hu/aram/oldalak/6454

This proves that a generic rule such as `SETTLEMENT -> UNIQUE DSO` or `COUNTY -> UNIQUE DSO` is not authoritative. P14 therefore does not build a national settlement/county crosswalk from broad region labels.

## Canonical regional-unit decision

For B10 network planning and network-constrained programme aggregation:

- canonical network-regional grain: `DSO_SERVICE_AREA`;
- administrative/reporting geography: separate `ADMINISTRATIVE_REGION` axis;
- exact electrical topology: separate `DSO_SUBSTATION` authority under B10-P8/P9;
- ENTSO-E control-area geography remains separate under B08.

This partially bounds `Q-B01-002`: B10 no longer has an unresolved choice between county and DSO region **for the network model**. However, `Q-B01-002` remains OPEN because a reproducible national administrative-location ↔ DSO-service-area membership crosswalk has not yet been acquired and validated.

## Executable contract

`modules/B10/dso_territorial_coverage_contract.py` validates:

- the exact six current operator identities;
- one canonical `*:SERVICE_AREA` identity per operator;
- referenced evidence for operator inventory;
- referenced evidence for the broad public service-area label;
- `DSO_SERVICE_AREA` as the B10 network-regional grain.

The canonical six-row inventory is:

- `registry/dso_service_area_inventory.csv`

The P14-local source registry is:

- `registry/dso_service_area_sources.csv`

The national assessment can return:

- `NATIONAL_DSO_OPERATOR_INVENTORY_PROVEN`; or
- `Q_NATIONAL_DSO_OPERATOR_INVENTORY`.

Even when the operator inventory is proven, P14 hard-codes the finer authorities as unresolved:

- `Q_SERVICE_AREA_MEMBERSHIP_CROSSWALK`;
- `Q_EXACT_DSO_NODE_INVENTORY`.

No caller-supplied flag can turn either into proven authority.

## P8/P9 relationship

P14 does not modify the P8 rule:

`ADMINISTRATIVE LOCATION != DSO SERVICE AREA != DSO SUBSTATION != ELECTRICAL TOPOLOGY`

P14's six service-area identities may be used as canonical operator/service-area dimensions. They cannot satisfy P8 `EXACT_DSO_SUBSTATION_MAPPING` and cannot enter P9 node demand without separate exact-node authority.

## Closure effect

P14 refines the P12/P13 closure blockers:

- remove: `NO_NATIONAL_DSO_COVERAGE`;
- retain/refine: `Q-B01-002`;
- add precise unresolved membership blocker: `NO_NATIONAL_SERVICE_AREA_MEMBERSHIP_CROSSWALK`;
- add precise topology blocker for limiting-node completeness: `NO_NATIONAL_DSO_NODE_INVENTORY`.

This is real progress in blocker precision, not readiness inflation.

P14 does **not** populate:

- `registry/regional_readiness.csv`;
- `registry/incremental_capex_attribution.csv`;
- a real programme entity×timestamp node panel;
- managed-peak/survivability study rows;
- timed programme-incremental CAPEX.

Therefore:

- B10 remains `IN_PROGRESS`;
- B10 readiness remains **15%**;
- Issue #10 remains OPEN;
- `B10_CLOSURE_BLOCKED` remains the canonical closure result.
