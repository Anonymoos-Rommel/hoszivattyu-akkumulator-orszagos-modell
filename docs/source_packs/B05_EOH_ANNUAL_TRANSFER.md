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


## Target-month and modeled-reference-duty response family, 2026-10-16

Starting main: `c3adf1ee27faf27692468cfbbb91f670e0d52bbf` (PR331).
All six starting files match both the preserved R2 ZIP and remote main byte for
byte. The exact local index tree is `e2098e64e01d79746692616ee65621ed9066cc86`;
local HEAD remains the earlier ancestor. The review patch compares the frozen
merged-main index to current work, not HEAD. No new network source was needed,
no denied download retried, and all old packages/outputs remain unchanged.

The target is the existing56m2 named house, WM50 nominalW55 SH reference under
UTC2025 weather:6050.554432 kWh generator heat, including302.4 kWh distribution.
The desired electricity boundary is the SH heat-pump whole system, including
SH-attributable circulation, excluding DHW service. Resistance heating and shared
circulation attribution are explicit accounting alternatives, not silently
identified components. W55 is the declared reference supply; achieved target
flow, return, controller state and auxiliary-pump configuration are not observed.
The existing active2321.747207 + inertia68.777498 + nonoverlapping idle82.109088
= **2472.633793 kWh** reference is retained exactly once.

### Weighting and support

The target's actual monthly heat-demand/reference-energy exposure weights source
observations within ambient, reference load-over-min and modeled reference
stage_on_fraction cells. The latter two are model outputs, not measured cycling
or controller duty. Manufacturer interpolation at source conditions supplies a
reference denominator, not evidence that an installed residual is W55-invariant.

2528 positive, stable-SH-endpoint, source-supported60min segments enter the
positive-load donor frame. Signed negative/zero heat, unsupported references and
other service endpoints remain in the separately hash-bound prior ledgers; they
are not clipped into this estimator. Source electric component availability is
not imputed. H/E-only and a separately identified joint-valid H/E/IH/CP cohort
are compared; the latter requires complete nonnegative aggregate components
whose sum does not exceed whole E. This is arithmetic consistency, not proof of
meter nesting or of attribution to the target.

For target month m and donor month n, the conditional kernel is
`exp(-0.5*(cyclic_month_distance(m,n)/h)^2)` within the same ambient/load/reference-
duty cell. h=0 is exact-month support diagnostic; h=1, h=3 and all-month pooling
are tested conditional marginalizations. Thermal/load/duty conditioning supplies
the comparability basis; the bandwidth and donor state weights remain ASS.
They are not a claim that source-month or source-year frequencies equal target
installation-state shares. The full observed joint donor year/month/flow/return/
observation-duration shares, and their target-variable-energy exposure, are
emitted instead of multiplying independent marginals.

| Month pooling, all supported source flows | Positive target hours | Conditional annual E kWh |
|---|---:|---:|
| Exact month only |5043 of6100|not annualized|
| Cyclic h=1 month |6100|3994.708794|
| Cyclic h=3 months |6100|3998.163365|
| All months |6100|4003.394924|

Exact-month support contains5487.892711 kWh of the6050.554432 target heat. It is
not an exclusion gate for the full calculation. Positive bandwidths pool across
comparable measured-condition cells and cover all6100 positive target hours;
2660 zero-heat target hours are handled separately. The old4003.394924 route is
also reproduced by the all-month weighting and remains unchanged. Restricting
donor mean flow to25--35C leaves5290 supported positive target hours; restricting
to53--57C leaves2403. These conditional partial totals are not annual estimates.

The new h=1 conditional anchor is **3994.708794 kWh**, comprising3930.905690 kWh
positive-period electricity and63.803104 kWh observed-month zero-heat transport.
The reference positive/zero parts are2432.733793/39.9 kWh, so the increments are
**1498.171897/23.903104 kWh**. Monthly target heat and positive energy close to
the annual controls. Source reference idle is removed before normalization,
then target idle is retained once:42.209088 kWh on positive target hours plus
39.9 kWh on zero-heat hours. No overhead is added twice. Zero measured heat is
not assumed to mean pure standby.

### Explicit conditional family and identification

For the H/E cohort, the annual response is

`E =2472.633793 +theta*[1498.171897 -3961.457029*(1-s)] +23.903104*z` kWh.

Here s in[0,1] is the SH-attributable share of donor whole-meter electricity;
theta is the unidentified **annual** positive-period installed-excess transfer
to the target, and z transfers the zero-heat excess. These are aggregate response
parameters, not an admitted common hourly multiplier or installed hourly shape.
Their physical check concerns the annual positive-period and zero-period energy
balances only. theta=1,s=1,z=1 gives the3994.708794 conditional anchor; this is
not evidence selecting a central E2 value. theta=0 retains only the reference
positive energy; theta=1.1 adds149.817190 kWh relative to theta=1. A one-percentage-
point decrease in s changes energy by-39.614570 kWh at theta=1. z changing by one
changes energy by23.903104 kWh. No evidence-supported finite upper bound for
theta or z is established. These probes are not endpoints of a finite uncertainty
interval. A positive annual response is not permission for a household or hourly
installed claim.

On the **same joint-valid component cohort**, the response instead uses

`D =s*3952.038087 -alpha*28.022451 -beta*1236.134398 -72.718407 -2390.524705`,
`E =2472.633793 +theta*D +23.903104*z` kWh.

alpha and beta in[0,1] exclude IH and circulation accounting shares respectively.
The domain excludes mixed service/component allocation: if s<1, alpha=beta=0;
positive component exclusions require s=1. The formula does not define whether
a component was already removed by service allocation, so that mixture is rejected.
Component shares cannot be applied to the H/E-only cohort. Joint-cohort whole E
is3985.331872 kWh,9.376921 below the primary anchor due to mask selection; pure
IH exclusion is28.022451 kWh **within that same cohort**, not37.399373 kWh across
cohorts. Full CP exclusion changes the joint-cohort result by1236.134398 kWh.
It is a boundary sensitivity, not a finding that this is compressor-only energy
or that CP causes that amount of inefficiency. The electricity/heat metering
boundary and pump mixture must support any attribution.

A fixed-power pump alternative removes the normalized **positive-period** CP term once and then
replaces it with observed donor CP power times a declared target exposure:

| Same joint mask, theta=s=z=1, alpha=0 | Annual response kWh |
|---|---:|
| Whole E, CP normalized with variable reference |3985.331872|
| CP removed once |2749.197474|
| CP removed, then source aggregate pump power on modeled reference-on hours, p=1 |3251.062078|
| CP removed, then source aggregate pump power on all positive target hours, p=1 |3538.209282|

The conditional replacement families are `2749.197474+p*501.864604` or
`2749.197474+p*789.011808` kWh, with p the unobserved target/source aggregate
pump-power ratio. p>=0 has no evidence-backed finite upper bound here. p=1 is an
explicit hypothesis, not target pump evidence. Modeled reference-on hours are
not measured pump run time; shared/DHW pumps in the source may not belong to the
target system. This large accounting sensitivity is why target hydraulic/pump
and service mapping matters more than merely selecting a month bandwidth.
Neither excluding all source CP nor transporting all CP as proportional to heat
is silently chosen as the central target model.

### Quantitative uncertainty with its scope preserved

For the h=1,s=theta=z=1 conditional mapping, positive calendar-block multipliers
reweight the one installation's episodes. Exponential weights preserve the
observed support.100 deterministic replicates at each of14/28/56day block sizes
have full support; they do not generate new installations, repair representation
bias or define a population confidence interval.

| Block days | Conditional q05 | Conditional median | Conditional q95 kWh |
|---|---:|---:|---:|
|14|3945.822586|3990.381402|4019.015674|
|28|3935.475569|3986.391900|4037.321972|
|56|3906.660953|3983.534290|4022.370723|

These are within-donor reweighting quantiles **conditional on the declared
service/state/W55 mapping**, not bounds on total uncertainty. Leaving each donor
year out gives3829.424154,3595.579303 and4048.689764 kWh (excluding2021,2022,2023
respectively), each with6100 positive hours. This is a temporal-composition
sensitivity, not three independent installations or a mandatory holdout gate.
The bandwidth sensitivity is small compared with the year/state and CP mapping
sensitivities, but small bandwidth sensitivity cannot prove residual invariance.

There is no identified central E2 installed annual value in this deliverable.
The useful result is the supported response family and its numerical derivatives.
The missing relationship is specifically how a target SH installation's pump/
service/operating state maps the manufacturer's normalized donor positive-energy
excess to nominalW55. Target flow/return/controller state and electrical service
shares have explicit conditional mappings above; none is filled from donor
shares as an observed target value. This conclusion follows the completed
weighting and component analyses. It does not impose a perfect donor year,
mandatory holdout, full-year directW55 measurement or component-E1 prerequisite.
The existing reference E2, canonical runtime/admission/readiness and national
outputs remain unchanged.

Reproduce with `--weighted-only --prior-output <R1-final> --prior-assessment
<R2-output> --handoff <verified-original> --additive <verified-additive> --output
<fresh-separate-directory>`. Exact52 input hashes, every R1/R2 output hash and
protected runtime hashes are checked before analysis. Sampling seed20261016 and
100 replicates are pinned. The official workbook restriction remains explicit;
no retry or alternative access was attempted.


### Verification of target weighting

44 targeted tests, including the local hash-bound integrations, and732 B05 tests
pass with no skips when inputs are explicitly supplied. Registry validation is
VALID. New regressions cover target-month kernel behavior, modeled-duty mismatch,
partial support without annualization, one-time idle and component arithmetic,
CP fixed-power units, explicit unknown component shares, unbounded annual
transfer responses and nonphysical annual balances. The old R1/R2 integrations
verify the pinned prior manifests instead of misidentifying those old outputs
as outputs of the new code.

The configured `unittest discover -s tests -v` collection was attempted on both
verified merged-main source contents and the candidate, with a45second per-test
bound and durable per-test outcomes. Both terminate in the same B13 test:
`FiscalOutputIndexTests.test_controlled_external_directory_still_reaches_first_fiscal_source_read`.
Its explicit`/tmp` fixture resolves to C:\tmp outside writable roots; the saved
stack traces are in tempfile.mkdtemp. Permissions and test behavior were not
changed to evade the restriction. Counts at bounded termination:

| Run | Collected | Passed | Failed | Errors | Skipped by configured suite | Blocked timeout | Not started |
|---|---:|---:|---:|---:|---:|---:|---:|
| Verified merged R2 baseline |4171|3747|5|12|14|1|392|
| Candidate before response safeguards |4177|3750|5|12|17|1|392|

All17 failing/error test IDs are identical on the two sides. The issues comprise
POSIX path strings versus Windows separators (including B14's data-identity path
comparison), unavailable os.O_NOFOLLOW/os.O_DIRECTORY and WinError1314 symlink
privilege. The candidate adds three passed unit tests and three configured
external-output skips; those skipped integrations pass in the separate44/732
local-data runs. The392 unstarted tests are **not** counted as skipped or passed.
This is not a complete successful repository-suite result. One preliminary45s
overall-bound run stopped during legitimate B02 computation; it was replaced by
the per-test-bound run and is not used as environment-failure evidence.

The fresh private review bundle includes all six candidate files with SHA256,
the exact input/prior-output bindings, new numerical tables and conditional
sampling results, targeted/B05/registry logs, both full-suite partial event logs
and paired baseline proof. The small human-readable patch preserves the source
file line endings and applies to the verified merged-R2 contents. Previous ZIPs
and output directories are unchanged. No GitHub write or model-value acceptance
is part of this work.


## Conditional-response safeguards correction

The first target-weighted package (682076bytes, SHA256
`899ae33fcd91400cef9d5425215a2d087bd5b881f4b68dd56358e8b01504fe55`) and all
its historical outputs remain unchanged. Independent review reconstructed the
anchor and40 declared variants,434 numeric checks with maximum error3.64e-12.
This correction changes admissible parameter combinations and numerical safety;
it does not change the delivered conditional anchor or empirical estimates.

Service-only allocation and component-only exclusions are separate sensitivities.
`service_share<1` together with positive IH or CP exclusion now raises ValueError,
including combinations with both components. Component exclusions remain allowed
on the exact joint-valid mask when service_share=1; service-only sensitivity
remains allowed with both exclusion shares zero. This prevents silently removing
a component twice or guessing whether its share was already allocated away.
For example, E=.9, CP=.2, service_share=.5, CP_excluded=1 does not have an accepted
response: whole-meter allocation then full CP subtraction gives a different
answer from proportional allocation of CP. Neither convention is silently chosen.

Finite parameters do not guarantee finite energy arithmetic. The code checks the
derived excess coefficients, positive/zero adjustments, positive/zero balances
and total energy before labelling physical validity or emitting a response.
Any nonfinite derived energy raises ValueError. Regressions exercise overflowing
delta, positive adjustment/balance, zero coefficient/adjustment and total balance,
including theta=1e308 on the actual1498.171897kWh anchor coefficient. Large finite
responses remain legal when every derived energy remains finite and the declared
annual energy balances are physical; no arbitrary transfer upper bound is added.

The CP replacement families remove/replace **positive-period CP only**. Their
full-year totals still include the separately handled zero-period power with z=1
in the displayed examples. Changing z changes that separate zero-period excess;
it does not change the CP replacement coefficient. These families are not a
replacement of all-year pump power and do not double-add a zero-period CP term.
The output carries the explicit scope marker
`POSITIVE_PERIOD_ONLY_ZERO_PERIOD_POWER_SEPARATELY_HANDLED_BY_Z`.

Post-correction verification uses46 targeted/data tests and734 B05 tests with no
skips, plus registry validation. The previous paired full-Windows run and its
exact counts above are retained as historical evidence, not relabelled as a new
complete run. Post-edit discovery and coverage are separately recorded; the two
new negative regressions and all affected B05 tests run on the corrected source.
No permissions, downloads, unrelated platform tests or model-admission flags are
changed. A new private review package preserves the first package and identities.


## Circulation energy identification from full EOH2074 telemetry

This separate local slice starts from reviewed PR332 head
`6c72f1aa4988ea645bf16f129fbc7c7db5c27175`, tree
`b4d56a129b2cc39822579bf4a0a0693a1988d75b`. All six reviewed files exactly match
the preserved corrected package bytes. Both the six-file checkpoint ZIP and a
separate copy of the unchanged696994byte/a607af1b... reviewed package are retained
outside this repository. The previous working folder and PR branch/package are
not edited. Only the same six research files change in a new detached local
working folder. No publication, new model-value admission or source download is
part of the slice.

### Equipment and metering boundary

Locally read registered PDI fields identify donor EOH2074 as Mitsubishi
PUZ-WM50VHA-BS,5kW,R32,design flow45C,one control zone and150L Water_New store.
The indoor unit, controller, hydraulic role of the store and individual pumps
are not identified. The named WM50+EHPT20X-MHEDW/FTC6,200L candidate remains a
candidate only. A product-family pairing document does not assign it to this
donor or to the target;150L versus200L is not used to infer another hidden
configuration. The56m2 nominalW55 SH target reference specifies thermal demand
and a device reference, not an installed external-pump circuit or runtime rule.

Existing local channel-definition extracts bind CP to the circulation meter
covering multiple pumps, H to the heat meter near HP primary flow/return, E to
the whole-system electrical meter and IH to immersion electricity associated
with primary thermal storage. Project-class wiring definitions do not prove the
home-specific meter nesting or service/control history. The source facts supplied
by the parent's fresh official review are attributed separately:

- SRC-B05-DESNZ-EOH-MONITORING-2024,Table4.1 printed26/PDF28: CP covers multiple
  circulation pumps.
- Same report section7.3 printed57/PDF59: auxiliaries and pumps inside the HP were
  not separately monitored.
- Same report section6.6.2 printed53/PDF55: cleansed two-minute alignment can
  distort instantaneous power.

Official report URL:
https://esc-production-2021.s3.eu-west-2.amazonaws.com/wp-content/uploads/2024/12/18093557/EoH-Heat-Pump-Performance-Data-Analysis-Report.pdf

These are parent-verified source facts; no local PDF inspection/hash is claimed.
No dictionary download was retried. The existing hash-verified channel extracts,
registered PDI snapshot and full telemetry supply this analysis. CP is measured
aggregate external circulation for this project boundary; it is not identified
with compressor electricity or an internal primary pump.

The locally read WM50 full-grid manifest states the EN14511-2013 total-unit
operating-point reference. Its nominal table explicitly includes standard pump
correction in input/COP. That declared reference therefore cannot be treated as
a compressor-only baseline and then augmented with every pump/controller term.
The numerical standard pump allowance at the observed/target operating states
is not separately identified. No original manufacturer PDF reacquisition is
claimed; the already registered source/locators and manifest are reused.

### Complete masks, accumulated blocks and signed missingness

All546896 source rows are scanned. Original adjacent120second differences define
independent H,E,CP,IH masks. The all-four intersection contains **544833 intervals,
18161.1 observed hours**,5138.530kWh H,2533.961kWh E,**795.140kWh CP** and280.947kWh
IH. Negative changes are never clipped; this particular common mask contains
60861 positive-heat and483972 zero-with1e-8tolerance intervals, with zero observed
negative-heat intervals. Synthetic tests retain negative states and residuals.

Three timestamp gaps account for1449 missing two-minute grid positions. Each
channel's known change between nonadjacent valid counter endpoints is saved as
an **unallocated signed span**, not assigned to an operating state or fitted as
observed runtime. For CP the exact ledger is:

`797.601 first-to-last change =795.140 all-four common +1.934 other adjacent
valid CP energy +0.527 unallocated nonadjacent endpoint-span energy` kWh.

The analogous H/E/IH closures are saved. Missing samples are not zero; known span
energy is not lost or silently spread over missing timestamps.545593 H/E intervals
are independently joined to the hash-bound R1 two-minute source reference; H/E
increments match within1e-9kWh. No new rating interpolation or altered historical
reference is introduced.

Contiguous all-four-mask parent blocks end at a gap, recorded month boundary or
30/60/180/1440minute clock edge; the60min clock is also shifted30min. Parent
span seconds must equal120 times observed steps. Within each parent, disjoint
service/heat/reference-availability subledgers preserve SH,DHW,transitions,both,
missing and incomplete modes. A state subledger can contain several state runs
inside the contiguous parent; it is not falsely described as a continuous pump
run. Unknown reference components remain blank, never zero-filled. Fits operate
on accumulated energy over those subledgers, not instantaneous two-minute power.
The primary180min comparison requires at least30 accumulated minutes in the
component; all durations and other aggregations are separately retained as
sensitivity/support diagnostics.

Two-minute CP exceeds E in211 common intervals, with0.213kWh positive excess.
After accumulation, **no30/60/180/1440minute contiguous parent** exceeds E by more
than1e-8kWh in CP alone. This supports using energy blocks for CP reconciliation.
CP+IH versus E is different:180min parents still have79 excess cases totaling
184.184kWh; daily parents have43 totaling130.484kWh. Thus this slice does not
claim that temporal aggregation repairs all IH/meter-boundary inconsistencies.
No automatic IH subtraction or nonnegative residual clipping is performed.

### Blocked predictive test of time versus reference energy

For each service/heat state, through-origin energy least squares fits either
`CP_kWh=P_state_kW*elapsed_state_hours` or
`CP_kWh=k_state*source_reference_kWh`. A nonnegative two-feature time+reference
fit is an additional nested diagnostic; a nearly rank-deficient design is
reported, not interpreted as identified components. Source reference includes
the preserved active/inertia/nonoverlapping-idle terms; it is a modeled reference,
not measured pump runtime. Time-only fits also use the full common-mask frame
where a source reference is unavailable. Time/reference comparisons use exactly
the same reference-compatible measured components and held-out support.

Recorded year and recorded year-month folds are held out in full. No random
interval split or perfect-year gate is used. Unsupported training states remain
unpredicted with their observed energy/support visible. This is within-one-
installation prediction, not a population confidence interval or target control
validation. The several aggregations reuse observations and are not independent
replications.

Primary positive SH results (180min parents,component>=30min):

| Held-out blocks | Model | Test components | Test hours | Observed CP kWh | Bias kWh | RMSE/component kWh | WAPE |
|---|---|---:|---:|---:|---:|---:|---:|
| Recorded year |Elapsed state time|912|1509.033333|243.039|0.160232|0.002326|0.642099%|
| Recorded year |Proportional reference|912|1509.033333|243.039|-21.247619|0.087986|24.594062%|
| Recorded year-month |Elapsed state time|912|1509.033333|243.039|0.147529|0.002222|0.609891%|
| Recorded year-month |Proportional reference|912|1509.033333|243.039|-19.132962|0.082428|23.106447%|

The full reference-compatible time fit is0.161174kW; the combined nonnegative fit
selects the same time coefficient and zero reference coefficient. In the full
common-mask positive SH frame,1639.6h carries263.619kWh CP, mean**160.783W**.
The all-reference-status time-only year test covers1590.5h/256.300kWh with0.658392%
WAPE, so the good time relationship is not created only by reference selection.
These are effective aggregate donor power relationships, not the nameplate or
identity of one pump.

Aggregation sensitivity on matched positive SH components:

| Parent clock | Common test hours | Time WAPE | Reference WAPE |
|---|---:|---:|---:|
|30min|632.5|0.769037%|26.105340%|
|60min|1296.7|0.694649%|25.709224%|
|60min shifted30|1287.3|0.665434%|25.867893%|
|180min|1509.033333|0.642099%|24.594062%|
|1440min|1545.666667|0.517158%|23.253514%|

Support changes with aggregation; partial totals are not treated as annual
estimates or compared as if their hours were identical. A fixed539566-centre
cohort with11 consecutive complete intervals and no month-crossing lag window
also tests CP shifts-10,-2,0,+2,+10min on identical H/E/IH support. Positive SH
comparison support is1489.7h. Time WAPE ranges0.499593..1.937413%, versus reference
24.534356..24.697661%; at zero shift it is0.638168% versus24.578080%. No lag is
selected as a data correction. All lagged ledgers are diagnostic and separate
from the original signed counter balances.

### Zero heat is a distinct unresolved control mixture

The full common mask has16092.733333h of SH-mode zero HP heat,472.616kWh CP,
864.569kWh whole E and270.457kWh IH. The source CP mean is29.368W, but its
variation is poorly predicted by a constant state-time rate. The full-mask
>=30min year test covers16007.966667h/465.554kWh CP and has**155.009290% WAPE**;
month-block prediction has157.600813%. A calendar-month-specific time model
reduces it to101.703797% on the same support, still inadequate. An ancillary
nonnegative time+measured-IH-energy predictor gives155.024419% year WAPE and
adds no useful explanation. These measured-state checks are reproducible in the
review metrics helper; they are not extra target pump defaults.

The smaller reference-compatible zero frame has1635.133333h/68.540kWh test CP.
Its time and reference models are exactly equivalent because the zero reference
is0.015kWh per hour: the joint design cannot identify two separate terms.
Year WAPE127.513707% is not evidence of an independent reference-energy effect.
The full-mask time result above avoids hiding most zero-state observations
behind reference-domain availability.

Substantial circulation when HP heat is zero means source positive heat time
or modeled stage_on_fraction cannot stand in for pump runtime. The weak zero-
state prediction remains a control/runtime-mixture question; neither a pure
standby interpretation nor an inferred pump-off state is assigned. DHW-positive
observations are separately368.933333h/54.525kWh CP,mean147.791W. Ambiguous and
transition balances are retained, not half-allocated into SH or DHW.

### CP-removed residual and the standard-pump overlap

On the exact same reference-compatible positive SH mask (1552.233333h), the
observed/reference energy ledger is:

| Quantity | kWh |
|---|---:|
| Whole E |1029.675|
| CP |249.545|
| IH |5.215|
| E minus CP |780.130|
| Reference active |711.515027|
| Reference inertia |6.374200|
| Reference nonoverlapping idle |3.733691|
| Complete reference R |721.622917|
| E minus CP minus R |**58.507083**|

The source whole-reference excess is308.052083kWh; its algebraic CP term is
249.545kWh and the remaining signed term58.507083kWh. This is a measured same-mask
reconciliation, not a target annual adjustment or compressor-only identification.
Subtracting IH as well is a separately labelled accounting diagnostic; no mixed
service-allocation/component exclusion is permitted by the retained API guards.
On reference-compatible zero SH, E-CP-IH is-142.354kWh and is explicitly retained.

Let A_std be the unknown applicable standard-pump contribution already embedded
in R. The non-pump residual relative to R-A_std is
`E-CP-(R-A_std)=(E-CP-R)+A_std`. It is not separately identified merely by measuring
external CP. For a component-based target reconciliation, the compatible form is
`E_target=(R_target-A_std_target)+C_external_target+Delta_remaining_target`.
Changing the applicable allowance by1kWh changes that accounting by-1kWh when
other terms are held fixed. Neither A_std nor Delta_remaining is defaulted to
zero. Internal auxiliaries remain in E-CP; the report says they were not
separately monitored. Therefore adding all external CP or generic internal
auxiliaries to R without the corresponding allowance/residual reconciliation can
overlap the standard reference. Existing reference idle is not added or
subtracted a second time, and positive/zero balances remain separate.

### Target applicability and verification

The useful identification is the donor's approximately161W positive-SH aggregate
circulation relationship and its low blocked prediction error, together with the
separately weak zero-state rule and preserved signed energy ledger. It does not
identify individual pump hardware or a transferable target annual circulation
value. That target requires an explicit hydraulic/electrical pump boundary and
`C_target=integral(P_target(flow,head,control,state)*dt)` under a stated actual
runtime rule, reconciled with the reference allowance and SH/DHW allocation.
A functional equivalent aggregate/calibrated mapping can qualify without exact
OEM identity or a universal component-E1 requirement; no such target mapping is
supplied in this slice. The donor power is not installed as a target default.
Target annual pump kWh, indoor/controller and internal-primary-pump identity
remain null/unassigned. Historical2472.633793,4003.394924 and3994.708794kWh results
and their hash-bound input/output identities remain unchanged.

54 targeted/data tests and742 B05 tests pass with no skips; registry VALID. New
regressions cover gaps, signed negative states, unknown reference subsets,
counter-span closure without time imputation, blocked-year training leakage,
unpredicted state support, reference/time collinearity, all-aggregation energy
closure, timing-cohort consistency and prohibition on target/internal-pump
assignment. Post-edit full discovery and coverage are recorded separately.
The precise earlier paired Windows limitations (same5failures/12errors and B13
external/tmp timeout,392not started) remain historical; a fresh successful full
suite is not claimed and no permission or unrelated test is changed to bypass it.

CLI: `--cp-only --prior-output <R1-final> --prior-weighted <corrected-weighted>
--handoff <original> --additive <additive> --output <new-separate-directory>`.
Inputs and prior numerical files are fully hash-checked before block construction.
The review package includes source, data-backed tests, derived block tables,
predictive errors, topology/source attribution, readable patches and exact hashes.


After this analysis the parent confirmed PR332 merged as
`c040c13f83077cc20e85d61d042bc5a6a09b89c8`, with the identical reviewed tree
`b4d56a129b2cc39822579bf4a0a0693a1988d75b`. That merge is the content-equivalent
base for this separate circulation slice. The reported4162passed/17skipped Linux
CI belongs to PR332, not to these new circulation edits. The frozen reviewed
head/tree and original package checkpoint remain intact; no branch or publication
change is made for this slice.
