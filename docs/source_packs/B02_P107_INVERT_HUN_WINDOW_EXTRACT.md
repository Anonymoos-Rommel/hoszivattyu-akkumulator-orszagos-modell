# B02-P107 — HUN 2025 INVERT WINDOW SURFACE EXTRACT

## Goal

Execute the P106 numeric blocker:

`INVERT_HUN_RENOVATION_GENERATION_WINDOW_SURFACE_EXTRACT_REQUIRED`

against the public TU Wien / Invert-EE-Lab EU27 Parquet dataset.

## Source integrity

- Zenodo record: `10.5281/zenodo.19599551`
- file: `INVERT_EU27_building_stock.parquet`
- source rows: **980,730**
- source MD5: **71e630ff7c575507d385208ba832513a**
- raw Parquet committed to repository: **NO**
- only derived HUN 2025 CSVs are committed.

The extraction was executed on a GitHub-hosted runner because the local
container cannot fetch the external 46 MB binary directly.

## Exact HUN 2025 extract

- archetype rows: **1,358**
- model dwelling weight: **3,515,973**
- canonical B02 occupied dwelling universe: **4,008,541**
- model/canonical ratio: **87.7120378711%**

The Invert model weight is therefore not silently treated as the canonical B02
population denominator.

## Source-native generation structure

The HUN 2025 names contain only:

- no explicit generation suffix: **BASE_GENERATION**
- explicit `_gen2`

There are no `_gen3` or `_gen4` rows in HUN 2025.

Independent Invert/FLEX documentation states that gen2/gen3/gen4 designate
renovated generations and higher numbers indicate more recent renovation.
Therefore no-suffix rows are retained as **BASE_GENERATION**, not silently
renamed to a renovated class.

### BASE_GENERATION

- rows: **1,002**
- model dwelling weight: **2,744,573.5**
- share of HUN 2025 model dwelling weight: **78.0601441860%**
- dwelling-weighted mean effective window coefficient:
  **3.95483899117 W/m2K**
- stock-window-area-weighted mean:
  **4.00931835175 W/m2K**
- range:
  **1.06135690212–5.09236001968 W/m2K**

### gen2

- rows: **356**
- model dwelling weight: **771,399**
- share: **21.9398438931%**
- dwelling-weighted mean effective window coefficient:
  **4.2734375 W/m2K**
- stock-window-area-weighted mean:
  **4.32524347305 W/m2K**
- range:
  **1.41864013672–5.09236001968 W/m2K**

The gen2 dwelling-weighted mean is **0.31859850883 W/m2K higher** than the
base-generation mean.

Therefore renovation generation cannot be treated as a monotonic
window-performance proxy.

## Current 1.10 W/m2K audit

Only **3** HUN 2025 archetype rows satisfy:

`U_eff = Htr_w / areawindows <= 1.10 W/m2K`.

All three are source-native:

`New_MFH_1_MFH`

with construction years:

- 2020
- 2022
- 2025

Combined model dwelling weight:

**964.809265137**

Share of the HUN 2025 Invert model dwelling weight:

**0.0274407473%**

The explicit gen2 group has:

**0 qualifying rows**.

Thus the <=1.10 rows are current/new-construction archetypes, not evidence that
renovation generation identifies window replacement.

## Evidence decision

P107 closes the numeric extract blocker:

`INVERT_HUN_RENOVATION_GENERATION_WINDOW_SURFACE_EXTRACT_REQUIRED`

as:

`RESOLVED_EXECUTABLE_NUMERIC_EXTRACT`.

But it rejects the proposed direct calibration route:

`MODEL_TO_OBS_REPLACED_WINDOW_CALIBRATION_REQUIRED`

because:

`WHOLE-BUILDING RENOVATION GENERATION != COMPONENT-SPECIFIC WINDOW REPLACEMENT`.

The TARKI-REKK 52.7% observed WINDOW_REPLACED share therefore cannot be mapped
directly onto BASE_GENERATION/gen2.

The new exact residual is:

`COMPONENT_SPECIFIC_WINDOW_REPLACEMENT_PERFORMANCE_BRIDGE_REQUIRED`.

A direct representative Hungarian replaced-window Uw distribution remains an
alternative closure route.

## National numeric effect

P107 produces a real HUN numeric surface, but does **not** produce a defensible
national replaced-window compliance share.

Therefore the P102 programme-action bounds remain unchanged:

- calibrated retrofit floor: **82.7861029945%**
- HP_ONLY lower: **0%**
- HP_ONLY upper: **17.2138970055%**

## Canonical boundaries

`BASE_GENERATION != REPLACED_WINDOW_CLASS`

`GEN2 != WINDOW_REPLACEMENT_EVENT`

`MODEL U_eff != OBSERVED PRODUCT Uw`

`NEW-CONSTRUCTION <=1.10 ROWS != REPLACED-WINDOW EVIDENCE`

`INVERT MODEL WEIGHT != CANONICAL B02 POPULATION WEIGHT`

`TARKI WINDOW_REPLACED SHARE != DIRECT INVERT GENERATION WEIGHT`
