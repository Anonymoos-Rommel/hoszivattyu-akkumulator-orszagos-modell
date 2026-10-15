# B05 EOH comparison support

Local research candidate, 2026-10-15. Base commit
`ed528c692abb14b992e9b64be9ab5fc6acc53a87`, tree
`c4517c3076d595f9cbbbb7bddaf8a520e19774a1`.
Semantic authority and exact input/protected-file hashes:
`registry/b05_eoh_comparison_support_manifest.json`. Source IDs reuse
`SRC-B05-DESNZ-EOH-CLEANSED-2MIN-9050`,
`SRC-B05-EOH-ALL-YEARS-EVIDENCE-2026`,
`SRC-B05-DESNZ-EOH-DICTIONARY-V2`, `SRC-B02-DESNZ-EOH-PDI-2024`, and
`SRC-B05-MITSUBISHI-DATABOOK-WM50-FULL-GRID-2020`.
External evidence remains local; no input source bytes are added to the repository.

## Reproduce

Use Python 3.12 or later, standard library only, from the repository root:

```text
python -m tools.analyze_b05_eoh_comparison_support --handoff <extracted-handoff> --output <new-output-outside-repository-and-handoff>
python -m unittest tests.test_b05_eoh_comparison_support -v
python -m tools.validate_registry
```

Set `B05_EOH_HANDOFF` and `B05_EOH_OUTPUT` to enable the five local-input
integration tests. No network, source acquisition or full archive scan occurs in
the analyzer. It verifies the exact HANDOFF_MANIFEST hash, every listed input's
size/hash and unique contained paths before reading measurements. It requires a
new output directory and never overwrites an existing result directory.
The older DELIVERABLE_MANIFEST describes the broader historical research, not
this 33-file handoff. Output provenance binds every numerical/source table to
both the handoff and comparison manifest hashes and the analyzer code hash.

## DER measurement and reference definitions

All numerical comparison results are **DER**, from hash-verified observed/source
data. Applicability remains **Q**. Counter units are cumulative kWh. Only
original adjacent rows exactly 120 seconds apart can contribute energy. Missing
counter endpoints are unknown; signed changes remain signed. No gap is bridged,
no energy is spread over missing periods and no partial year is annualized.
Calendar assignment is the current endpoint's recorded year, including a
cross-year two-minute interval. Timestamp timezone is Q: recorded hour is neither
asserted UTC nor Hungarian grid time.

Four distinct masks require both endpoints of every named energy channel:

| Mask | Counters required | Meaning |
|---|---|---|
| HP_E | HP heat, whole-system electricity | Original H/E ledger |
| HP_E_CP | HP heat, whole E, CP electricity | Original H/E/CP ledger and same-mask E minus CP |
| HP_E_IH | HP heat, whole E, IH electricity | Newly computed H/E/IH intersection |
| HP_E_CP_IH | All four | Additional explicit intersection |

CP/IH are null outside masks requiring them. E minus CP uses exactly the heat/E/CP
mask and is an electrical residual, not automatically compressor electricity or
pure SH. IH electricity is reported separately and is never added to useful
heat. All electricity when dH <= 1e-8 kWh remains in the ledger; it is not
automatically called standby, cycling or loss. The original header has no backup
column; this does not establish physical absence. Missing individual-channel
coverage and excluded gaps are separately reported.

The sole supply input is **Heat_Pump_Heating_Flow_Temperature**. HW flow never
substitutes for it. Measured return temperature is contextual and is not converted
to supply with an invented deltaT. Heating/HW presence at both endpoints defines
explicit temperature proxies; these are not service-mode telemetry. All proxy
classes, including mixed/incomplete conditions, remain. Condition tables use
year, proxy, current ambient, heating-flow and return bins. Their masks partition
the same yearly balances; no condition group is selected for a better result.

For each mask, all four source modes MAX/NOMINAL/MID/MIN are evaluated separately
at both observed endpoint ambient/heating-flow pairs. No frequency is inferred
and no best-COP mode is chosen. Native water columns are 25,35,40,45,50,55,60 C;
there is no generic 30 C cutoff. Actual native source blanks and outer-domain
limits fail closed before the unchanged engine evaluates the coordinate. The
unchanged engine can reject an edge where its rectangular interpolation asks
for another missing corner; that disposition is retained and labeled separately.
No interpolation crosses a native blank and no extrapolation occurs.

Support means **both endpoint coordinates** pass, in addition to the exact energy
mask. Supported and each unsupported reason retain measured H, E, relevant CP/IH,
time and zero/negative-heat electricity on that exact subset, for every year and
condition. Previous/current reference Qh[kW], Pel[kW], COP means are computed from
actual engine evaluations on that same supported subset. They are endpoint
sample statistics. The two-minute energy differences yield observed interval
mean H and E powers; the rating endpoint powers are **not proven interval means
or quasi-stationary operation**. They are not integrated into a reference kWh
ledger, installed residual or correction. Mean endpoint COP is not a ratio of
mean powers or an annual SPF. Metered whole-system E and rated total-unit Pel
have an unresolved physical boundary overlap.

## Separate heterogeneous SH description

All 33 documented separate-meter hybrid SH systems, 4,546 windows and 96,019
intervals remain. Category is exactly `documented_separate_meter_hybrid_SH`.
Boiler-positive windows remain. All 13 comparison source tables are copied
byte-identically, including other-category rows in original tables. Six complete
condition/system/year/clock tables are also emitted with the explicit primary
category filter. The original full primary window table retains every identity,
month, recorded clock, source and technical field.

Pooled ratio is sum(H)/sum(E); home-balanced ratio is the mean of each home's
sum(H)/sum(E), with equal home weights. These describe heterogeneous systems and
repeated correlated observations; they are neither WM50 calibration nor
independent model validation. Window energy is grouped by **window start year**;
the exact clock table counts intervals by their **current endpoint year**. A
cross-year window is retained without distributing its energy between years.

## Policy and remaining applicability Q

The original A-slice manifest and its historical NOT_COMPUTED IH statement stay
unchanged; this new computation has a separate manifest. B05/B11 runtime,
manufacturer grid, installed-boundary evidence, annual correction and signed
installed residual remain unchanged. Canonical E2 permits later defensible
equivalent aggregate or calibrated transfer with explicit target, boundaries,
coverage and uncertainty. This comparison introduces no component-E1,
perfect-year, boiler-free or mandatory holdout prerequisite.

**Q:** Can a same-SH-service installed/rating electrical, thermal and duty boundary
be defended for a declared target through such a qualified aggregate or
calibrated transfer? EOH2074 mixed SH/DHW, measured IH electricity, unknown
controller/frequency and timing do not yet provide that mapping. The hybrid
ratios supply a separate descriptive context. No annual/hourly installed,
W55-transfer, national, task/readiness or model-default admission is claimed.

## Local verification

The completed local run produced 13,872 comparison rows. All 45 original annual
numeric controls (including the two original ratios each year) passed. The
following **DER** tables give compact checks; full-precision outputs retain all
four masks, modes, unsupported reasons, conditions and channel/gap coverage.

| Recorded year | HP/E steps | HP heat kWh | Whole E kWh | HP/E/IH steps (new) | H kWh on HP/E/IH | E kWh on HP/E/IH | IH kWh on HP/E/IH |
|---|---:|---:|---:|---:|---:|---:|---:|
| 2021 | 90,263 | 1,081.474 | 508.244 | 90,181 | 1,080.871 | 507.741 | 46.661 |
| 2022 | 261,997 | 2,515.232 | 1,272.327 | 261,779 | 2,512.901 | 1,271.299 | 131.159 |
| 2023 | 193,333 | 1,549.344 | 757.023 | 193,165 | 1,547.956 | 756.411 | 103.157 |

All four modes share these HP/E support counts for this particular source grid;
their reference values differ. Support fractions use the original HP/E mask as
denominator, not all calendar time. Unsupported energy remains in the full tables.

| Recorded year | Supported steps | Supported H kWh | Supported E kWh | Time share % | H share % | E share % |
|---|---:|---:|---:|---:|---:|---:|
| 2021 | 20,657 | 731.081 | 265.053 | 22.885 | 67.600 | 52.151 |
| 2022 | 55,233 | 1,619.560 | 617.318 | 21.082 | 64.390 | 48.519 |
| 2023 | 23,359 | 930.778 | 277.059 | 12.082 | 60.076 | 36.598 |

Current-endpoint reference arithmetic means on those exact supported HP/E masks:

| Recorded year | Fixed mode | Qh kW | Pel kW | Mean endpoint COP |
|---|---|---:|---:|---:|
| 2021 | MAX | 5.821892 | 1.185209 | 5.100548 |
| 2021 | NOMINAL | 4.999060 | 0.991050 | 5.256302 |
| 2021 | MID | 4.000000 | 0.769145 | 5.449660 |
| 2021 | MIN | 2.053379 | 0.419160 | 5.354835 |
| 2022 | MAX | 5.844194 | 1.145207 | 5.323171 |
| 2022 | NOMINAL | 4.998264 | 0.960651 | 5.441110 |
| 2022 | MID | 3.999560 | 0.742798 | 5.660299 |
| 2022 | MIN | 2.070145 | 0.402940 | 5.590878 |
| 2023 | MAX | 5.864875 | 1.181283 | 5.177163 |
| 2023 | NOMINAL | 4.999000 | 0.986588 | 5.312576 |
| 2023 | MID | 3.999853 | 0.765158 | 5.503666 |
| 2023 | MIN | 2.053519 | 0.412322 | 5.417912 |

For the separate heterogeneous hybrid population, **DER** pooled H/E is
2.584880514 and equal-home mean H/E is 2.448452804; 3,334 boiler-positive windows
and the one 98-interval cross-year window remain. These are descriptive ratios,
not any of the WM50 endpoint reference values above.

The analyzer checks all original annual H/E and H/E/CP counts, signed sums,
negative/zero-heat counters and the original ratios, at abs tolerance 1e-8 and
relative tolerance 1e-11. Tests cover differing masks, missing channels, signs,
gaps, source blanks/range, year boundary, retained boiler-positive windows,
explicit modes and unchanged admission. The local review bundle contains raw
command logs, numerical tables, a six-file patch and file hashes. Full hosted
GitHub testing and publication require a later decision.

The portable Windows Python 3.12.10 initially lacked IANA data; local tzdata
2025.2 restored those surrounding tests without project/runtime source changes.
The B11 suite has four failures reproduced with identical test names and causes
on the untouched pinned base: two fault-injection mocks use POSIX slash suffixes
on Windows paths, one fixture calls unavailable `os.O_DIRECTORY`, and one fixture
requires ungranted Windows symlink privilege (WinError 1314). No permissions or
security settings were changed to bypass these limits. Paired baseline/candidate
raw logs are in the local review bundle.
