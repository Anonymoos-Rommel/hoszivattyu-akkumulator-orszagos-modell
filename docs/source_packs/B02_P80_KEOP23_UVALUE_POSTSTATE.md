# B02-P80 — KEOP23 baseline U-value matrix and action-conditioned post-state

**State:** `BASELINE MATRIX MATERIALIZED / REFERENCE-RETROFIT POST-STATE PARTIALLY QUALIFIED`

**Canonical base:** `61b4c115aaab8b3377b766334ebc62ecacdd9b4a`

**Implementation date:** 2026-09-21

## 1. Purpose

P78 identified:

`POST_RETROFIT_COMPONENT_U_VALUE_SURFACE_REQUIRED`.

P79 then supplied complete set-valued WBL/P21 coverage over the 23 Hungarian
synthetic building types.

P80 uses the same public Csoknyai 2022 source to materialize:

1. the 23-type historical baseline U-value matrix from Table 8.3;
2. the source-native reference-retrofit U-value requirements from Table 9.1;
3. explicit action-conditioned post-state semantics for the source's
   air-to-water heat-pump cases.

P80 does not turn the historical survey/model into a 2026 household observation.

## 2. Table 8.3 — historical baseline matrix

The source states that Table 8.3 summarizes average component U-values by
building type and separately treats renovated and unrenovated elements.

P80 materializes all 23 source type columns for:

- external wall;
- attic floor;
- flat roof;
- pitched roof enclosing a converted attic;
- basement ceiling;
- timber/PVC windows.

Where the source reports:

- `N/A`, P80 stores a missing value;
- `0.00`, P80 preserves the source-native raw zero but **does not admit it as
  a physical U-value**.

Canonical boundary:

`SOURCE ZERO / N-A != PHYSICAL ZERO`.

The matrix remains historical baseline/calibration evidence.

`TABLE 8.3 HISTORICAL BASELINE != 2026 CURRENT STOCK OBSERVATION`.

## 3. P79 set-valued crosswalk

P80 reuses the exact P79 candidate-type sets.

For any:

`WBL construction period × P21 building group`

the module can compute a min/max envelope over valid source-native candidate
type means.

These are:

`QUALIFIED_SET_VALUED_BASELINE_CALIBRATION`

or, where a candidate contains missing/nonphysical source values:

`PARTIAL_SET_VALUED_BASELINE_CALIBRATION`.

They are not household confidence intervals.

`KEOP23 TYPE MEAN != HOUSEHOLD U-VALUE`.

## 4. Table 9.1 — source-native reference-retrofit U requirements

The dissertation defines a reference structural renovation using the
cost-optimal requirement level and publishes the following component
requirements:

| Component | Source-native U upper bound |
| --- | ---: |
| External wall | **0.24 W/m²K** |
| Flat roof | **0.17 W/m²K** |
| Attic floor | **0.17 W/m²K** |
| Basement ceiling | **0.26 W/m²K** |
| Timber/PVC window | **1.15 W/m²K** |

P80 encodes these as **upper-bound constraints**, not realized point values.

`REFERENCE RETROFIT U-MAX != REALIZED U-VALUE POINT`.

The extracted Table 9.1 has no explicit separate row for the P80
`PITCHED_ROOF` component, so that component remains Q:

`TABLE_9_1_HAS_NO_EXPLICIT_PITCHED_ROOF_ROW`.

P80 does not silently substitute a generic roof value.

## 5. Source-native heat-pump transition cases

Section 9.2.4.2 explicitly evaluates two air-to-water heat-pump cases:

1. the building envelope remains unchanged and only the heat-pump heating/HMV
   system is introduced;
2. the building is first upgraded to the reference cost-optimal envelope state,
   then an air-to-water heat-pump system serves heating/HMV.

Therefore P80 can define:

### AIR_TO_WATER_HP_ONLY

Envelope state:

`UNCHANGED_FROM_CURRENT_PRE_STATE`.

But national 2026 current U-values are not materialized, so:

`AIR_TO_WATER_HP_ONLY -> CURRENT_NO_ACTION_BASELINE_U_SURFACE_REQUIRED`.

### REFERENCE_ENVELOPE_RETROFIT_PLUS_AWHP

For the explicit Table 9.1 components, the post-state U upper bounds are
qualified as a source-native **model transition state**.

This is not a national action frequency.

`ACTION-CONDITIONED MODEL STATE != NATIONAL ACTION ASSIGNMENT`.

## 6. Blocker effect

Previous:

`POST_RETROFIT_COMPONENT_U_VALUE_SURFACE_REQUIRED`.

P80:

`PARTIAL_RESOLVED_ACTION_CONDITIONED`.

The source-acquisition problem is substantially narrowed.

Current residual:

1. `NATIONAL_ENVELOPE_ACTION_ASSIGNMENT_REQUIRED`;
2. `CURRENT_NO_ACTION_BASELINE_U_SURFACE_REQUIRED`;
3. `TABLE_9_1_HAS_NO_EXPLICIT_PITCHED_ROOF_ROW`;
4. `COMPONENT_AREA_GEOMETRY_SURFACE_REQUIRED`.

The last item matters because B06 design load requires:

`U × component area × temperature difference`.

A U-value alone is not a design-load surface.

## 7. Relationship to other P78/P79 residuals

Still open:

- `WITHIN_TYPE_GEOMETRY_DISTRIBUTION_REQUIRED`;
- `COMPONENT_AREA_GEOMETRY_SURFACE_REQUIRED`;
- `GEOMETRY_INVARIANCE_BY_ACTION_REQUIRED`;
- `POST_RETROFIT_VENTILATION_SURFACE_REQUIRED`;
- `POST_RETROFIT_THERMAL_BRIDGE_SURFACE_REQUIRED`;
- `DESIGN_OUTDOOR_TEMPERATURE_MAPPING_REQUIRED`;
- `DESIGN_INDOOR_SERVICE_CONDITION_REQUIRED`;
- `NATIONAL_P65_SUPPLY_TEMPERATURE_SURFACE_REQUIRED`;
- B05 materialized design-point/product-domain gaps;
- remaining CAPEX/emitter/action residuals.

## 8. Non-claims

P80 does not claim:

- Table 8.3 describes the current 2026 Hungarian stock;
- the source mean is a household U-value;
- historical renovation shares are current renovation shares;
- a source-native zero is a physical zero heat-transfer coefficient;
- Table 9.1 is asserted as the current legal requirement;
- every programme dwelling receives the reference envelope retrofit;
- the reference-retrofit U-max is the exact achieved U-value;
- the pitched-roof post-state is identified;
- Q-B02-004 is closed.

B02 readiness remains **55%**.
