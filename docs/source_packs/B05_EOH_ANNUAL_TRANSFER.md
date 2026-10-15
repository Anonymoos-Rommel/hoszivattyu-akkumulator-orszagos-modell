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
