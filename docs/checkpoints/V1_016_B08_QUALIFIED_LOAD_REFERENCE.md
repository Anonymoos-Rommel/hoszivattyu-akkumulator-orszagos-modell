# V1 checkpoint 016: reproduce the qualified historical load baseline

Scope: B08-D01 reuse of the already admitted P5 external-only ENTSO-E source pair. No source-rights policy or XML/OBS parser gate changes. This materializes a historical Hungarian control-area baseline, not programme savings, regional headroom or a new national feasibility result.

## Existing authority and exact bytes

The two registered GUI exports listed in `registry/b08_b09_p5_entsoe_gui_export_acquisition.csv` are now available to the local consumer and match their full original byte counts and SHA-256 hashes. R01 is the 2025 UTC Actual Total Load panel; R02 is its complete 2024 companion. The existing P5 contract grants qualified E2 model use while keeping public raw reuse as validation debt. The reader checks those scope/admission fields and exact source bytes before parsing. It does not create an API request, retrieve new source data or invent a new revision.

The source workbook combines Actual Total Load and Day-ahead Forecast. Only the exact `Actual Total Load (MW)` column for `BZN|HU` is consumed. UTC time labels, period, complete row count and 15-minute intervals are independently checked. Forecast values never fill an actual value. Missing, duplicate, reordered, negative, nonfinite or formula-valued source cells fail closed.

A consequential source-format issue was reproduced: both workbooks declare a stale worksheet dimension of `A1:E19`, despite containing their complete annual rows. A default read-only spreadsheet iterator can therefore stop at row 19. The new standard-library XML reader traverses actual sheet rows and never trusts that dimension. An independent openpyxl check with `reset_dimensions()` reconciled the full source totals and peak; it did not edit or recalculate the workbooks.

## Exact time and energy handoff

The canonical 2025 Budapest civil year is 2024-12-31 23:00 UTC through 2025-12-31 23:00 UTC, end-exclusive. Four final 2024 intervals are joined to the first 35,036 intervals of the 2025 UTC source. No interpolation, averaging, downscaling or fabricated boundary values are used. Both whole source panels must pass their original acquisition contract before the stitch.

The output contains 35,040 quarter-hours. The 2025 spring transition contains 92 intervals and the autumn transition 100; repeated local 02:00 labels retain distinct UTC offsets. Power stays MW; interval energy is explicitly MW × 0.25 h. The existing complete-window seasonal consumer preserves tied peaks and rejects gaps or partial windows. A complete meteorological winter labelled 2025 is available from the same pair; winter 2026 remains incomplete and cannot pass as a whole-winter result.

Normalized records are `DER`, with the containing panel explicitly `E2_PROVISIONAL_BASE / QUALIFIED_E2_MODEL_USE`. Source-native numerical observations are not relabelled as newly cleared OBS records. Acquisition record IDs and exact source hashes remain attached. The older XML parser's separate `REUSE_CLEARED` requirement for OBS is unchanged.

## Reproduction and storage

Run:

`python tools/materialize_b08_gui_load_reference.py --source-2025 <exact-external-R01-XLSX> --source-2024 <exact-external-R02-XLSX>`

The full normalized panel and derived run receipt are written only beneath ignored `data/interim`. The materializer rejects output destinations outside that ignored boundary. No workbook bytes or full numeric panel enter the public repository. The receipt records source/output hashes, exact coverage, annual energy, peak and complete-winter controls. Runtime model use and raw redistribution remain different permissions.

Tests exercise source/forecast identity, hash-first rejection, stale dimensions, source-cell errors, complete-year and winter boundaries, DST, MW/MWh, E2/DER labels and rejection of scenario or reuse-status promotion. The public verification receipt records artifact hashes and actual checks without embedding source rows. B08-D01 advances to review; B08-D02 population/programme aggregation and B08-D03 regional mapping remain separate open work. Q-B08-001 remains the existing validation debt.
