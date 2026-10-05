# V1-030 — Prospective design and capacity reference

## Scope and status

This checkpoint executes one populated conditional physical diagnostic at
`Y_LT1919 / FAMILY_HOUSE`, from the existing B02 upper component surfaces,
through canonical `B06.calculate_design_heat_load`, into the existing B05 WM50
manufacturer consumer. The physical state and capacity comparisons remain
**SCN**. The existing design helper's arithmetic **DER** result is retained
separately and is not physical-state or admission promotion.

Implementation base: `a43327e1239ddc6f3ec9dff217cbc3d86c4342c1`.
The candidate requires exact-content independent review and combined checks;
this document does not mark the wider physical package or B02/B05/B06 slice
complete. No readiness or shared-registry change is made here.

The four-file implementation is:

- `modules/B06/prospective_capacity_reference.py`
- `registry/b06_prospective_capacity_reference_manifest.json`
- `tests/test_b06_prospective_capacity_reference.py`
- this checkpoint

The public entry point is
`modules.B06.prospective_capacity_reference.calculate_reference()`.
It is a read-only calculation returning a serializable result. No CLI, source
acquisition, annual simulation, hourly simulation, or old-engine edit is added.

## Physical interpretation

The sum of component/stratum maxima is an **outer model-envelope stress
bound**, not an observed, expected, weighted, or necessarily jointly attainable
building. It is not a national statistical upper confidence bound. Component
geometry proxies and U bounds remain conditional prospective inputs; none is
an as-built measurement.

P95 replaces the historical bbox facade route. The net wall and aggregate
opening partition uses the same gross facade upper and opening share; openings
include doors, so the P92 aggregate 1.40 W/m²K upper is used rather than a
window-only value. Materialized area precision is retained and the partition
is checked against gross area × share. P91 corrected wall U is 0.336 W/m²K.

P96 supplies the 0.204 W/m²K corrected upper for the explicitly declared heated
attic enclosing structure. P94 provides only bottom area. The present case
explicitly declares a **basement ceiling technical SCN** with base U=0.26
W/m²K, zeta=0.20 and design boundary correction=1. The U/zeta values are checked
against the applicable P91 row. Boundary correction=1 is a declared stress
assumption, recorded under a local SCN identity; it is not claimed to be a
measured basement temperature or a seasonal TABULA ground reduction factor.
A ground-contact branch is unsupported by this entry point.

Corrected U includes simplified thermal bridges once. Additional separate
bridge H is explicitly zero for this accounting treatment, not a declaration
that physical bridges vanish. Internal insulation and detailed psi/chi routes
are outside this case.

Natural ventilation explicitly uses 0.35 Wh/m³K × (0.5 + 0.06) h⁻¹ × 301.28 m³.
The 0.5 h⁻¹ and 0.35 Wh/m³K method references are separately labelled POL; the
prospective infiltration/volume selection and complete physical state are SCN.
Zero heat recovery is an explicit natural-ventilation path declaration.

Ti=20°C and Tout=−12°C are the declared engineering reference and one P97 zone
coordinate, not observed setpoints, a location assignment, or a national
comfort objective. Design heat loss does not calculate annual gains; this is
not a silently zero-gain annual calculation.

## Genuine populated result

Executed from the pinned source rows and actual consumers, with no mocked
positive result:

| Conditional quantity | Value | Evidence |
|---|---:|---|
| Net external wall H | 54.049706666667 W/K | SCN |
| Aggregate openings including doors H | 28.150888888889 W/K | SCN |
| Facade subtotal H | 82.200595555556 W/K | SCN |
| Top H | 18.438336 W/K | SCN |
| Basement-ceiling scenario H | 26.856960 W/K | SCN |
| Natural ventilation H | 59.050880 W/K | SCN |
| Total H | 186.546771555556 W/K | SCN |
| Design temperature difference | 32 K | SCN |
| Design heat Q | 5.969496689778 kW | SCN |

The facade subtotal is a reporting subtotal, not another term in the total.
The total is the four non-overlapping envelope components plus ventilation;
`Q_design = H_total × 32 / 1000`. Component arithmetic reproduces the separately
materialized P95/P96/P90 H quantities within CSV precision.

The exact manufacturer product is `PUZ-WM50VHA(-BS)`, source
`SRC-B05-MITSUBISHI-DATABOOK-WM50-FULL-GRID-2020`, MAX compressor frequency.
MAX is a capacity probe, not a runtime dispatch or modulation rule.

| Fixed manufacturer probe at −12°C | Capacity kW | Input kW | COP | Signed capacity margin kW |
|---|---:|---:|---:|---:|
| W35 | 4.38 | 1.5690721649484536 | 2.7914586070959264 | −1.589496689777785 |
| W45 | 4.26 | 1.7878264623354199 | 2.38278160086925 | −1.709496689777785 |
| W55 | Q | Q | Q | Q |

Signed margin is **available capacity minus conditional design heat**. A
negative margin against this outer stress load does not establish failure of
any real building or a backup size/requirement.

B05 interpolates paired extensive powers Q and P between A−15 and A−10 and
derives COP=Q/P. Source capacity/COP pairs remain OBS, derived source input and
interpolated complete performance are DER, and the comparison to the physical
SCN stays SCN. Unit and Q=P×COP checks run in the wrapper and tests.

A−15/W55 is a retained source blank; the fixed W55 map begins at A−10. The
A−12/W55 result is `Q / OUT_OF_PERFORMANCE_DOMAIN`, with null capacity,
electrical input, COP and margin. It is not zero electricity, a filled corner,
or a failed design-load calculation. The result preserves the source support
cells, their OBS/DER/Q statuses, and their exact defrost annotations.

The A−15/A−10 support cells are unshaded/not explicitly integrated-labelled.
That does **not** prove zero defrost, authorize an added penalty, or supply
weather-realized/seasonal efficiency. There is no interpolated defrost label
invented at A−12.

W35/W45/W55 are separate manufacturer-coordinate probes. No emitter-required
flow temperature is generated. P98 supplies the audit category anchors and no
population weights. Required emitter supply remains null and
`Q / P65_NOT_ASSESSED` for every probe.

## Input and claim integrity

The manifest pins 22 existing source extracts, contracts, authority records and
consumer/method files by SHA-256. Stable source IDs remain semantic authority;
hashes identify reviewed bytes. Additional method/authority pins bind the
existing 1.40 opening upper and the 0.35/0.5 ventilation constants. All 26
original planning pins were also independently checked unchanged at execution.
No external document bytes are included.

The wrapper validates exact row identity, one-to-one stratum joins, candidate
type identity, source status, boundary declarations, units and scenario/source
lineage. Numeric values labelled Q, missing evidence, nonfinite/boolean inputs,
dropped SCN, bridge double counts, changed pins, wrong products/modes, and
unsupported admission fields are rejected before the canonical design call
where applicable. The pin set itself is bound to a code digest, so silently
rewriting a source hash in the manifest is not accepted. Scope/annual-lineage
metadata is separately bound to prevent altering the report into a broader
claim.

The result explicitly leaves these Q/not assessed or unpopulated:

- P65 emitter authority, real-record eligibility and realized completion
- hourly heat/gain states, thermal mass, emitter inventory and return path
- runtime/controller, numeric cycling, additional dynamic defrost and external auxiliaries
- DHW duty, annual electricity, SPF and national programme result
- wider physical-slice completion and readiness uplift

No national comfort/2M/B07 runtime policy, backup/procurement choice, annual
savings, or source-year weather reconciliation is selected.

## Native annual regression is separate

The nine historical TABULA Refurbishment variants are rerun under their native
source service, area and climate. Their annual useful space heat reproduces
its source values and remains DER. This retains V1-012 regression evidence; it
is not new programme before/after evidence and is not a design-peak input.
Uniform-service SCN remains a separate pre-existing API option, unused here.

## Verification

Author checks against the final candidate:

- 21 new focused tests pass, including an independent Decimal sum and source
  Q/P interpolation, genuine canonical calls, null W55 and missing-corner
  outputs, numeric-but-Q inputs, SCN loss, boundary/source drift, doubled
  bridges, incorrect mode/product and false admission attempts
- 57 existing relevant B05/B06 tests pass: design load, P65 emitter/registry
  gates, TABULA annual reference, retrofit engine, complete WM50 consumer,
  interpolation consistency and cold-performance domain tests
- All 26 planning input pins match; genuine execution JSON and exact author
  logs are retained outside the repository for independent review

Commands:

```sh
python -m unittest tests.test_b06_prospective_capacity_reference -v
python -m unittest tests.test_b06_p3_design_load tests.test_b06_p65_emitter_temperature_gate tests.test_b06_p65_registry_contract tests.test_b06_tabula_seasonal_reference tests.test_b06_retrofit_engine tests.test_b05_manufacturer_wm50_reference tests.test_b05_interpolation_energy_consistency tests.test_b05_p4_cold_performance -v
```

The parent integration/review step owns aggregate verification and any combined
metadata. No aggregate suite, commit or push is performed by this checkpoint's
author.
