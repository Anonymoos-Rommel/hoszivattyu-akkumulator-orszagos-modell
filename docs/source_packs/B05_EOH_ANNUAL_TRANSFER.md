# B05 annual EoH transfer — corrected research implementation

Revision REVIEW_CORRECTION_1, pinned base 6ae8a073635db0f3b4475a5a9b2baf618cb824b3.
Only the authorized six files change. The original review ZIP (SHA256
599bb6816945c54facbd022e3d7e3ee2b5c30ae80dcee30912c63136d6d86a44)
and its output directory remain unchanged. This revision supersedes the earlier
interpretation that the hourly near55-only matching failure establishes general
absence of an E2 transfer route.

## Stable input and target boundary

Every19 additive and33 original input file is verified against the pinned
manifests. Recovered weather is a separate DER research identity,
DER-B05-WEATHER-44527-UTC2025-RECOVERED-20261015, SHA256
2c4e2fd66391b2b72409e92815e95772af66bfcafba52f1528dea4073f6900ea,
838059bytes. All8760 station44527 physical UTC2025 hours are checked against
the included official history/recent snapshots. Semantic source lineage is
separate from snapshot identity. The old a213... weather manifest and canonical
runtime guard remain byte-identical. No private runtime seam or monkeypatch is
used to admit recovered bytes.

The public TABULA, WM50 map and existing E2 minimum-stage APIs independently
reproduce2472.633793065277kWh:2321.7472067406616 active rating,
68.77749841231555 inertia and82.10908791230001 nonoverlapping idle kWh.
The56m2 ambitious W55 target has5748.154431653909kWh useful SH heat plus302.4kWh
effective distribution heat, hence6050.554431653909kWh generator heat.
Its8760 rows retain actual reference stage_on_fraction and component energies.
No reference component is added twice. These are historical source/reference
quantities DER/E2, not measured2025 installed consumption.

## Split before aggregation and retain the complementary ledger

Only original adjacent120s matched H/E counter changes enter the energy ledger.
Signs, zero-heat electricity, missing CP/IH and year/month assignment are retained.
Before30/60-minute aggregation, each original interval is classified using BOTH
original ambient/heating-flow endpoints and all four ordered source modes.
Missing or unsupported endpoint classes split segments immediately. A bad
endpoint therefore cannot remove otherwise supported intervals from a whole
hour. Rejected intervals still contribute their signed H/E to separate segments
and the complete month/year ledger; gaps are never bridged.

A recovery audit independently reconstructs the previous whole-segment rejection
and reports supported positive two-minute intervals it had discarded. Detailed
compressed segment tables, class/reason summaries, four original counter masks,
45 original annual controls,1274 all-system monthly/year checks and416 EOH replay
checks remain. Calendar buckets, original service proxies and year/month
boundaries are explicit; partial segments remain. EoH recorded timezone is Q.
Target UTC is known, and the two clocks are not identified with one another.

## Three evaluated positive-load transfer routes

1. EOH_NEAR55_OBSERVED keeps the original both-endpoint53..57C observation slice
   as one sensitivity branch. That reporting envelope is NOT an exclusive gate.
2. EOH_ACTUAL_CONDITIONS_TO_W55 retains supported lower-flow and other native
   conditions. At the donor's observed ambient/flow and allocated load, it
   calculates the ordered paired-power plus existing minimum-stage reference.
   The observed/reference dimensionless ratio is then applied to target W55
   components at matched target ambient/load-minimum cells. No COP-mode selection,
   arbitrary deltaT, source-blank interpolation or extrapolation is introduced.
3. HYBRID_AGGREGATE_TO_W55 evaluates every documented hybrid window through the
   normalized5kW/nameplate load, with separate electrical/service alternatives.
   All4546 windows/96019 intervals and3334 boiler-positive windows remain in the
   source ledger. Above-MAX or missing reference windows remain in exclusions;
   boiler positivity alone is never an exclusion.

The actual-condition route assumes invariance of the installed/reference energy
relationship across supply temperature after manufacturer normalization, at
comparable service/load/duty. This is an explicit SCN engineering hypothesis,
not an observed W55 residual. Source-map temperature dependence justifies the
reference transformation; it does not by itself prove residual invariance.
All2/30/60-minute and shifted60-minute results, donor years and pooled years are
reported rather than selecting a favorable aggregation or annual COP.

For hybrids, four alternatives separate product-size and fixed/shared electricity:
LINEAR_ALL_E scales all observed electricity; RATING_IDLE_NONSCALING leaves the
reference idle component unscaled; CP_NONSCALING_RETAINED leaves measured CP
unscaled while scaling E-CP; BOILER_SHARED_CP_HEAT_SHARE additionally allocates
CP to HP/boiler according to their separately metered heat share. The latter
requires complete CP/boiler observations for that alternative, without deleting
the window from other alternatives. Boiler heat is not converted to electric
energy. CP residual is never called compressor input. These are evaluated
aggregate engineering sensitivities, not automatic nameplate equivalence.

## Service, IH and zero-state alternatives

Four EOH cases are calculated: heating-temperature-proxy whole E; all metered
service assigned to SH; mixed/incomplete temperature service split half to SH
(with DHW-only assigned zero); and heating proxy with IH excluded only on its
complete, aggregate-consistent common mask. Proportional mixed-service allocation
is a declared SCN bracket, not inferred telemetry.

IH electricity never becomes useful heat. Missing IH remains unknown, and
IH>E is neither clamped nor automatically subtracted. Per-aggregation boundary
tables retain complete-mask H/E/IH, IH>E counts and signed excess, CP overlap,
service proxies and zero/positive heat. Consistency of an aggregated IH counter
is necessary for that subtraction scenario, not proof of metering inclusion.

Zero-state target electricity uses measured ZERO-heat monthly E/time from broad
observed periods, with service/IH cases, donor hours and year support exposed.
It is separate from positive-load manufacturer normalization. The38-minute
near55 fragment and its former73.066kWh extrapolation are not a representative
annual base. Zero heat does not automatically prove standby, cycling or losses.
Hybrid active windows supply no annual zero-state rate; the hybrid alternative
explicitly uses the EOH monthly zero-state route and carries that product/service
transport assumption.

## Component closure, qualification and uncertainty

Each route is evaluated with TOTAL_REFERENCE_REPLACEMENT and
VARIABLE_REPLACEMENT_IDLE_ONCE. The first replaces the full target reference by
a donor total ratio. The second transfers observed-minus-reference-idle relative
to donor active+inertia, then includes target idle exactly once. No separate CP,
pump, controller, inertia or idle overhead is added afterwards. Negative cell
predictions remain visible and cannot qualify a complete physical annual point.

Target-cell tables partition time, generator heat and baseline electricity into
supported conditional and unidentified parts. Actual donor systems, years,
segment counts and hours remain; correlated intervals are not independent sample
units. Full conditional annual values are emitted only when the calculated
route covers all target cells without negative cell energy. Otherwise the known
contribution and complementary unknown baseline exposure remain separate.

route_qualification uses calculated coverage/physical closure and claim-specific
assumption evidence. It can return an E2_CANDIDATE when a documented justified
aggregate/calibrated mapping exists, including explicit validation debt; it does
not require component E1, a perfect donor year, boiler-off or mandatory holdout.
Current service/meter, residual-invariance and annual zero-state transport claims
are evaluated as conditional alternatives, with source IDs and reasons. The
selected central point is derived from eligible results and a predeclared route,
not hardcoded to zero support or an annual number. Conditional SCN results and
admissible E2 fields are separate. National/runtime/readiness admission stays
unchanged regardless of this research classification.

The envelope across years, service allocation, product/fixed-component handling,
accounting and aggregation is an empirical/engineering SCN envelope, not a
confidence interval. Between-window model ratios do not become WM50 calibration
without the named product/service/duty mapping.

## Reproduction and deliverables

Python3.12+, standard library only, from the detached research checkout:

    python -m tools.analyze_b05_eoh_annual_transfer --additive <additive> --handoff <original> --output <new-output>
    python -m unittest tests.test_b05_eoh_annual_transfer -v
    python -m tools.validate_registry

B05_ANNUAL_ADDITIVE and B05_ANNUAL_OUTPUT enable local-input integration tests.
Existing output directories are never overwritten. INPUT_CODE_OUTPUT_MANIFEST
binds original/additive inputs, research code/manifest, protected canonical files
and all output hashes. New outputs include donor route cells, evaluated target
cells and annual alternatives, service/IH/CP audit, split recovery and the derived
ANNUAL_TRANSFER_DECISION. The old near55 calculation is labeled a narrow
NEAR55_ONLY_DIAGNOSTIC, not the general transfer result.

Regression tests cover lower-flow retention, preaggregation endpoint splitting
and complementary energy closure, IH inconsistency, single-count fixed/idle
accounting, and conditional versus qualified results. Targeted/B05 and registry
checks are rerun. Previously demonstrated unchanged B11/Windows/full-suite /tmp
limitations are retained as limitations without repeatedly rerunning those
unrelated tests. No GitHub or Library write is part of this revision.

## Corrected numerical result

The split audit recovers exactly493 previously rejected segments containing6758
load-reference-supported positive two-minute intervals,594.518kWh heat and
165.109kWh electricity. An additional67 intervals (12.9kWh heat,3.792kWh E)
have native temperature support but not complete load-matched reference; they
remain separately visible. Thus the reported6825 temperature-supported intervals
are not mislabeled as6758 load-supported intervals.

The corrected calculation evaluates350 route/year/aggregation/accounting cases.
56 cover the full target conditionally. Their complete SCN annual envelope is
3918.9321200383024..4248.724432944618kWh, not a confidence interval or an admitted
E2 range. The pooled60min, variable-replacement-plus-idle-once comparisons are:

| Route/assumption | Supported target hours | Conditional annual E kWh | Known partial E kWh |
|---|---:|---:|---:|
| Actual-condition EOH, heating proxy, whole E | 8760 | 4003.394924 | 4003.394924 |
| Actual-condition EOH, aggregate-consistent IH exclusion | 8760 | 3962.331179 | 3962.331179 |
| Actual-condition EOH, all metered service as SH | 8760 | 4003.500845 | 4003.500845 |
| Actual-condition EOH, mixed service half SH | 8760 | 4003.386743 | 4003.386743 |
| Hybrid linear all-E scaling | 5346 | unidentified | 2396.875338 |
| Hybrid CP retained without size scaling | 5346 | unidentified | 2357.644266 |
| Hybrid boiler-shared CP heat allocation | 5346 | unidentified | 2221.612901 |

The broad heating-proxy zero-state pools contain15273.833333 hours from all three
donor years,732.672kWh observed E and16699 segments. Target-month weighting gives
63.8031037114kWh over2660 zero-heat target hours in the whole-E case. This remains
a conditional service/month transport, not a representative annual base asserted
from38minutes of near55 observations.

IH exceeds whole E in24868 of545125 complete two-minute segments, with244.017kWh
positive excess; at60min it occurs in207 of21449 segments, with223.908kWh excess.
Aggregation reduces count dramatically but does not remove the boundary issue;
this is why IH subtraction is an evaluated, masked alternative rather than an
automatic correction. The whole-E alternative retains those observations.

No E2 candidate is selected after the evaluated alternatives: service/electrical
boundary, residual invariance and zero-state target transport remain conditional
claim assessments. The rating normalization itself is source-supported. Numerical
coverage is now complete for multiple explicit SCN routes; lack of coverage in
the old near55 matcher is no longer presented as absence of all engineering
transfer possibilities. All original annual/monthly energy controls remain.


## Aggregate E2 applicability assessment, 2026-10-16

This revision is relative to main `cd176ed8f5b314525cf082bd2dd4d69c0348cea6`.
The six permitted files match its remote Git blobs before editing; the local
index tree is `aadf578dd32fcbffeba867749c8e3f8b8fd565df`. Local HEAD remains
its parent `6ae8a073635db0f3b4475a5a9b2baf618cb824b3`; the incremental review
patch is the unstaged diff against that verified index, not the HEAD diff.
No new repository archive was acquired. The whole-repository clone attempt was
rejected by automatic approval review; narrow remote-blob verification supplied
the baseline instead. No GitHub write is authorized or performed.

The designated route still covers **8760/8760 target hours**, 6050.554432 kWh
of generator heat, and 2472.633793 kWh of device-reference electricity. Its
conditional annual electricity is **4003.394924 kWh**. The remaining question
is whether one installed annual E2 base is defensible, not unidentified cells.

### Service and electricity reconciliation

Original signed H/E, H/E/CP, H/E/IH and H/E/CP/IH masks are tabulated by year,
month and service endpoint classification. No missing counter is imputed; no
negative increment is clipped. Whole E remains the whole-system meter boundary;
E minus CP is not compressor-only electricity. Stable SH/DHW endpoints, direct
SH-to-DHW transitions, both-channel ambiguity, absent modes and incomplete
boundaries are separately retained. Stable endpoints do not prove the mode was
unchanged throughout the two-minute interval.

The parent directly inspected the official dictionary and reports that Clean2min
rows16/18 and Raw22/24 record SH/DHW flow temperature only in the corresponding
valve-identified mode. They are documented mode indicators, not generic thermal
proxies. Return temperature has no such restriction. The legacy numerical
`temperature_proxy` strings are preserved solely to reproduce R1; new outputs
add `documented_mode_endpoints`. The full workbook is not locally verified:
normal sandbox download of the exact official URL failed network access on
`doc.ukdataservice.ac.uk:443`; the resulting empty local file is not input.
Expected workbook identity:165294 bytes,
`b0df7899064e0d33679d760b6bc2be52d06f1d3093d7b20aa283a632db4175f7`.
The seven original hash-verified energy/time extracts remain the directly read
local source. Parent-reported workbook interpretations are explicitly separate
from direct local workbook inspection. Planned MCS SH/DHW annual values are not
measured allocations; MCS flow is design temperature.

| Exact target-weighted case | Conditional annual E kWh |
|---|---:|
| Whole E, reference donor mask |4003.394924|
| Whole E, IH complete, including IH greater than E |3985.693633|
| Whole E, exact valid IH-pair mask |3996.765092|
| E minus IH, same exact valid pair mask |3962.331179|

The pure paired IH subtraction is **34.433913 kWh**. The original reference-to-
subtraction contrast is41.063745 kWh, including6.629832 kWh of mask selection.
These are accounting alternatives; a meter location description alone does not
justify component additivity or target attribution.

On the same531270 two-minute complete-hour HEI intervals, E=2465.057 kWh and
IH=279.712 kWh at every aggregation. Positive IH-over-E excess is243.536 kWh
at2min,220.226 at10min,208.831 at30min and188.837 at60min. This reduction is
not cohort loss. The complementary13855 HEI intervals retain152.835 kWh H,
70.394 kWh E and1.265 kWh IH. A separate common538314-centre lag cohort leaves
243.773 kWh excess at zero lag and202.391 at minus30min; no tested lag resolves
it. Lags are diagnostic only, never selected as a correction. Thus timing can
explain part of short-interval nonadditivity, but does not establish subtraction.

### Normalization, target exposure and E2 judgment

The emitted joint table conditions the dimensionless variable-energy residual
on donor year, actual flow, ambient/load cell and service. Target comparisons
reuse identical positive target cells, with target idle added once. They do not
claim causal flow or year effects. The source-supported SH segments
with mean flow53--57C in the60min replay comprise only13 segments,3.0 donor
hours,0.563 kWh H and0.065 kWh E. Their implied transfer differs
by723.887244 kWh from25--30C donors on1593 common target hours. That sparse
contrast is a warning about identification, not strong proof of a temperature
law. Low-flow25--30 versus30--35C donors differ by76.478037 kWh on5290 common
hours, while remaining within the observed low-temperature operating regime.

The earlier flow/ambient/load-conditioned2021/2023 contrast was
-452.972377 kWh on3173 target hours. **It confounds year with season**:
2021 donors in25--30C occur inOctober--December;2023 donors occur inJanuary--
April/September. There are no same-calendar-month2021/2023 donor matches in that
flow bin. That contrast cannot identify an isolated year or controller change.
The same caution applies to the earlier across-flow -838.770667 kWh contrast.
They remain reproducible diagnostics, superseded as applicability arguments by
the matched analysis below; neither is an annual error bound or causal estimate.

Broad SH-mode zero-heat month transport contributes63.803104 kWh over2660 target
hours.2022 independently covers those hours at62.143067 kWh.2021 covers only1044
and2023 covers2628; their partial totals are not annualized or compared as full
annual values. Outputs retain year/month/service power and hours. Zero measured
heat does not identify standby: storage, defrost, pumps, auxiliary power and
controller states can contribute. The target zero-state mix remains conditional.

The policy's eight conditions are evaluated separately for reference arithmetic,
service/electrical boundary, normalized transport, zero-state transport and the
installed annual claim (40 rows). Reference E2 is unchanged. Installed applicability
(condition4) and an invariant residual in the face of measured state variation
(condition5) are not sufficiently supported to select4003.394924 as one E2 base.
The remaining month/state-matched discrepancy and unsupported target state mix
are the identification gap, with the partial exposure quantified below;
it is not an unperformed analysis or a demand for E1 components, a perfect donor
year, independent holdout or direct full-year W55 measurement. The exact debt is
a target-relevant installation/controller calibration or defensible state mapping
for normalized positive energy and zero states. The workbook alone cannot supply
that calibration, although its local verification remains outstanding.

Qualification records bind route, product, service, accounting, donor scope,
aggregation and target. All eight criteria must be individually supported with
reasons and locators. Global JUSTIFIED flags, source IDs, full coverage or close
scenario totals cannot confer E2 or leak EOH support to hybrid systems. No runtime,
canonical reference, installed/national admission or readiness credit changes.

Reproduce with the portable Python and this repository first on sys.path:
`python -B -m tools.analyze_b05_eoh_annual_transfer --assessment-only --handoff
<original-extracted> --additive <additive-extracted> --prior-output
<hash-bound-R1-final> --output <new-separate-directory>`.
The CLI refuses an existing output and verifies every prior numerical output,
all52 inputs and protected runtime hashes before analysis.


### Verification of this revision

36 targeted tests including data-backed integration pass. All724 B05 tests pass
with the matching comparison-review, R1-final and aggregate-review output
identities; none are skipped. An initial broad data test used the earlier
comparison-final output manifest and correctly rejected its identity mismatch;
the matching comparison-review output resolves that fixture error. Registry
validation reports VALID. The six-file diff passes whitespace checking and the
incremental patch applies to unchanged merged-R1 file contents.

A complete repository-suite pass is **not claimed**. Prior paired baseline and
R1 evidence shows the same two B11 failures and two errors among169 tests on
Windows (POSIX path mock, unavailable os.O_DIRECTORY and symlink privilege).
The full-suite continuation blocks at B13's explicit `/tmp` fixture, resolving
to sandbox-inaccessible C:\tmp. Paired bounded traces in previous-environment-
evidence locate tempfile.mkdtemp; this unchanged environment issue was not
repeated in the current revision. Those logs are historical, not a fresh
candidate-wide successful run. No permissions, platform settings or unrelated
tests are changed to conceal it.

The review bundle contains the six candidate files, incremental patch, numerical
assessment, input/code/output manifest and raw verification logs. Original EOH
and R1 artifacts remain unchanged. Private Library upload of this new review ZIP
is authorized; GitHub publication and canonical admission remain outside scope.


## Review correction R2: season/state matching and derived admission gates

The previous329012-byte review ZIP is preserved unchanged (SHA256
`038f16f1676175b326cb308d182df59435a5e71f2bbfd466931a4d6924f60b3b`).
The new output is `output-aggregate-e2-assessment-r2`; no old numerical output
or published Library version is replaced.

All supported positive stable-SH60min source segments are inventoried by donor
year, calendar month and mean-flow bin. Comparisons hold the donor month and flow
bin fixed, then require common ambient/load cells. Five eligibility/standardization
levels are emitted: month/flow alone; at least45min observation duration; matched
15min-duration groups; duration plus5C return-temperature groups; and those plus
quarter-width reference-duty-fraction groups. Observation duration is valid
segment length, not measured compressor run time. Reference duty is the existing
rating/on-off model's stage_on_fraction, not independently measured compressor
state. Missing return temperatures are excluded from return-matched support,
never filled. The common donor hours and segment counts are emitted for both
sides; the inventory exposes which month/flow/year combinations have no support.

Within each ambient/load cell, common duration/return/duty groups receive the
same symmetric pooled donor-reference-energy shares on both sides. This is an
explicit conditional standardization, **not an observed target return-temperature
or controller mix**. Whole E and signed energy arithmetic remain unchanged.
Two exposure modes are kept separate:

- `TARGET_SAME_MONTH`: only positive target hours in that same calendar month.
- `ALL_TARGET_CELL_EXPOSURE_DIAGNOSTIC`: that donor-month mapping applied to all
  positive target hours in the common ambient/load cells. This is a diagnostic
  exposure, not a full-year prediction, and cannot be summed across donor months.

For every row the original pooled-year contrast is recalculated on exactly the
same eligible target hours. The decomposition closes algebraically:
original contrast = month-selection change + within-month eligibility/composition
change + remaining standardized contrast. These are descriptive composition
terms, not identified causal effects. Different matching levels can lose support;
their partial totals must not be compared as if their hours were identical.

Independent February2022/2023,25--30C calculation:

| Matching / exposure | Common target hours | Remaining difference kWh | Common donor hours2022 /2023 |
|---|---:|---:|---:|
| Month/flow, all-target-cell diagnostic |2962|-416.964383|91.1 /15.766667|
| At least45min, all-target-cell diagnostic |2962|-415.665501|70.7 /9.4|
| Duration + return + reference duty, diagnostic |2962|-415.665501|73.7 /11.166667|
| At least45min, target February only |229|-14.843381|70.7 /9.4|
| Duration + return + reference duty, target February only |229|-14.843381|73.7 /11.166667|

The original pooled-year contrast on those same2962 hours is-432.259309 kWh.
Month selection accounts for-15.294926 kWh of that contrast; the45min eligibility
change accounts for-1.298882 kWh, leaving-415.665501 kWh. The independent result
agrees with the reviewer's example, but it is neither extrapolated over unsupported
hours nor assigned to an isolated controller/year effect.

The strongest displayed same-target-month state matching spans January--April:

| Flow /2022 vs2023 | Common target hours | Target H kWh | Original contrast on same hours | Month-selection term | Within-month composition term | Remaining kWh |
|---|---:|---:|---:|---:|---:|---:|
|25--30C, duration/return/duty |685|851.774675|-42.682813|10.243290|-2.909916|-50.016188|
|30--35C, duration/return/duty |1088|1603.511237|-93.340684|-45.434245|-10.819595|-37.086843|

For comparison, month/flow alone covers685 hours at-52.926103 kWh in25--30C,
and1176 hours at-58.196785 kWh in30--35C. The latter support differs from the1088
state-matched hours; the decomposition row, rather than their raw difference,
is the valid same-exposure composition comparison. Flow alternatives overlap
in target cells and are not additive. No partial result is annualized.

This completes the previously available season, duration/load and return analysis.
The evidence now supports a narrower statement: measured residual discrepancies
remain on explicitly limited common support after these measured-state controls.
It does not identify their cause, or establish one annual installed correction.
The designated4003.394924 kWh route remains a complete conditional SCN; no E2
promotion follows from either coverage or the size of a diagnostic contrast.
An applicability judgment about a target-relevant state mapping is still needed;
this is not a request for data to replace an analysis left undone. The official
workbook's network restriction is unchanged and was not retried or bypassed.

Assessment completeness and physical validity are now derived from the actual
hourly predictions: every target timestamp must occur exactly once, all must be
supported with finite energy, energy must be nonnegative and positive when target
heat is positive. Missing values, duplicate/missing/wrong timestamps, unsupported
hours, negative energy, zero electricity with positive heat, infinity and NaN
cannot gain E2 even if a supplied eight-condition evidence record is otherwise
fully supportive. Current actual flags are complete=true, physical=true; the
claim-specific conditions still produce SCN_COMPLETE_CONDITIONAL.

R2 validation:38 targeted/adatintegration tests and726 B05 tests pass, none skipped;
registry VALID. Full-suite limitations remain as previously documented, without
claiming a new complete repository-suite pass. The new review package has a new
private Library identity; the previous package is retained.
