# B02-P106 — NON-EKR REPLACED-WINDOW PERFORMANCE CALIBRATION

## Result

P106 attacks `NON_EKR_REPLACED_WINDOW_UW_DISTRIBUTION_REQUIRED`.

No representative public Hungarian **replaced-window** Uw distribution was identified. P106 therefore does not invent one.

It does identify a materially better route.

## Public model surface

The 2026 TU Wien / Invert-EE-Lab EU27 dataset contains Hungary and 5-year stock states from 2020 to 2050. Each row is an archetype/year and includes:

- source-native name encoding building type, construction period and renovation generation;
- `areawindows`;
- `Htr_w`;
- `number_of_buildings`;
- `number_of_dwellings_per_building`.

The model therefore permits:

`U_eff = Htr_w / areawindows`

and dwelling-weighted aggregation by renovation generation.

Independent Invert/FLEX literature confirms that renovation generations denote renovated archetypes and higher generation numbers represent more recent renovation.

## Hard boundary

This is a **model-calibration route**, not observation.

`MODEL_EFFECTIVE_WINDOW_U != OBSERVED_REPLACED_WINDOW_UW`

`RENOVATION_GENERATION != WINDOW_REPLACEMENT_EVENT`

`MODEL_CALIBRATION != NATIONAL_COMPLIANCE_SHARE`

## Observed bridge

TARKI-REKK 2022 remains the national observed replacement-state calibration target. Its 52.7% window-replaced share can constrain a model-based route, but the label itself does not prove Uw.

KSH 2020 provides replacement extent and recency variables, but no public response distribution/frame/Uw surface was identified.

The BME 2026 Type-5 EPC distribution remains validation-only because it is full-window Type-5 stock, deliberately original/uninsulated, not a replaced-window subset.

## Blocker repair

Superseded:

`NON_EKR_REPLACED_WINDOW_UW_DISTRIBUTION_REQUIRED`

New primary residual:

`NON_EKR_REPLACED_WINDOW_PERFORMANCE_CALIBRATION_REQUIRED`

with exact sub-residuals:

1. `INVERT_HUN_RENOVATION_GENERATION_WINDOW_SURFACE_EXTRACT_REQUIRED`
2. `MODEL_TO_OBS_REPLACED_WINDOW_CALIBRATION_REQUIRED`
3. `NON_EKR_EKR1103_OVERLAP_BOUND_REQUIRED`

A direct representative Uw distribution remains an admissible alternative.

## Numeric effect

No calibrated HUN extract is yet materialized, therefore:

- calibrated retrofit floor remains **82.7861029945%**
- HP_ONLY lower remains **0%**
- HP_ONLY upper remains **17.2138970055%**

B02 remains 55%; PEAK_LOAD_EFFECT remains 50%.
