# B02-P51 — legacy RADAL replacement gate

**State:** `LEGACY TYPE-SIZE MATRIX + CURRENT PRODUCT PERFORMANCE MATERIALIZED / NONRES KEEP PRECEDENT MATERIALIZED / NATIONAL P42 STILL Q`

**Canonical base:** `d08d812011db9d886a5e0c5ed3e6c0f5e3af1b75`

**Implementation date:** 2026-09-07

## 1. Purpose

P51 advances the original programme chain:

`EXISTING RADIATOR TYPE/SIZE -> OLD OUTPUT BASIS -> TARGET TEMPERATURE -> KEEP / UPSIZE / CHANGE -> REPLACEMENT PERFORMANCE -> B06 PRODUCT/CAPEX`

P50 proved bounded residential type/size examples and a 55 C panel-engineering case. P51 now makes a legacy RADAL type/size/output/count matrix and a current LEHEL Viking 600 product-performance table machine-readable, while enforcing the engineering boundary that physical similarity or manufacturer interchangeability is not an exact replacement decision.

Hard boundaries:

`HISTORICAL HEATING SURFACE M2 != PHYSICAL RADIATOR UNIT COUNT`

`HISTORICAL INSTALLED MAGNITUDE != CURRENT SURVIVING STOCK`

`NON-RESIDENTIAL LEGACY MATRIX != RESIDENTIAL STOCK WEIGHT`

`PRE=POST RADAL MATRIX IN ONE NONRES HP PROJECT != NATIONAL/RESIDENTIAL KEEP SHARE`

`SYSTEM 70/55 C != NOMINAL TABLE OUTPUT BASIS`

`SAME TYPE/SIZE TOKEN != SAME HEAT OUTPUT`

`MANUFACTURER FAMILY INTERCHANGEABILITY != EXACT REPLACEMENT SKU AUTHORITY`

`OUTPUT COMPARISON != HYDRAULIC SUITABILITY != ROOM-LEVEL KEEP/CHANGE DECISION`

`B02 REPLACEMENT NEED/COMPARISON != B06 PRODUCT/CAPEX SELECTION`

All five P42 national claims remain `Q / programme_use_allowed=NO`.

## 2. Historical RADAL magnitude — useful scale, not pieces

Current LEHEL technical catalogue:

`https://alurad.hu/_user/page/webshop/12/documents/lehel_muszaki_katalogus_2023.pdf`

The brand-history section states that RADAL production started in 1970 and that roughly `30 million m2` of RADAL heating surface was installed in Hungary, with additional export volume. The same catalogue states that dwellings built by the house-factory system in the 1960s-1990s predominantly received Alutherm and RADAL radiators.

P51 materializes only:

`historical installed RADAL heating surface ~= 30,000,000 m2`

with `magnitude_precision=APPROXIMATE`.

An older public project source reports a lower historical magnitude of roughly `20 million m2`. P51 therefore treats the 30 million figure as a source-version magnitude claim, not an exact invariant.

No conversion to physical radiator pieces is allowed because installed heating surface requires a representative section/type/geometry distribution and surviving-stock model that are not present.

Therefore:

`30,000,000 m2 != 30,000,000 radiators`

and:

`HISTORICAL INSTALLED RADAL SURFACE != CURRENT RADAL STOCK`

The executable contract raises `HEATING_SURFACE_M2_TO_PHYSICAL_RADIATOR_PIECES_FORBIDDEN` if such a conversion is attempted.

## 3. Jászapáti — exact legacy RADAL 600 matrix

Official municipal project plan:

`https://www.jaszapati.hu/index.php/kozbeszerzesek/send/256-top-napelem/4749-projekt-terv-varosuzemelteto.html`

The pre-development emitter table for a municipal office/workshop publishes exact RADAL 600 rows:

| Variant | Source size token | Nominal output | Count |
|---|---:|---:|---:|
| RADAL 600 6 tagos | 485 mm | 1.067 kW | 1 |
| RADAL 600 8 tagos | 710 mm | 1.423 kW | 1 |
| RADAL 600 10 tagos | 860 mm | 1.779 kW | 4 |
| RADAL 600 15 tagos | 1310 mm | 2.669 kW | 4 |
| RADAL 600 16 tagos | 1385 mm | 2.846 kW | 6 |
| RADAL 600 22 tagos | 1835 mm | 3.914 kW | 2 |

Total documented legacy units in this bounded project table:

`1 + 1 + 4 + 4 + 6 + 2 = 18 radiators`.

The project text describes the pre-existing central-heating system as a partly renovated two-pipe `70/55 C` system with RADAL aluminium radiators.

P51 deliberately stores each radiator-table output basis as:

`SOURCE_NOMINAL_UNSPECIFIED_TEMP`

because the source does not explicitly state that the nominal kW column is rated at `70/55/20`, `75/65/20`, `78/62/20`, or another test basis.

This is a critical non-equivalence:

`SURROUNDING SYSTEM OPERATING TEMPERATURE = 70/55 C`

`DOES NOT PROVE`

`NOMINAL RADIATOR TABLE OUTPUT BASIS = 70/55/20 C`.

Consequently these old kW values cannot yet be directly compared with the modern Viking catalogue at 78/62/20 or 55/45/20.

## 4. Jászapáti — bounded KEEP precedent through envelope + heat pump retrofit

The same official project plan publishes the post-development emitter table. It repeats the same six RADAL 600 variant/count rows while the project also includes envelope insulation, window replacement and an air-water heat pump.

The pre-development annual heating-energy demand is stated as `65.67 MWh/a`; after the envelope measures the document gives `19.34 MWh/a` before the heat-pump conversion step.

P51 therefore materializes a bounded technical precedent:

`SAME DOCUMENTED RADAL EMITTER MATRIX PRE-DEVELOPMENT`

`+ ENVELOPE RETROFIT`

`+ AIR-WATER HEAT PUMP`

`-> SAME DOCUMENTED RADAL EMITTER MATRIX POST-DEVELOPMENT`.

This is materially useful: it proves that legacy RADAL radiators can remain in at least one documented heat-pump retrofit rather than requiring universal replacement.

But the project is non-residential and the source does not publish a post-heat-pump room-level emitter operating-temperature/output sufficiency proof. Therefore it cannot create:

- a residential KEEP percentage;
- a national KEEP percentage;
- a P42 reuse/upgrade classification;
- a residential radiator-stock weight.

Hard boundary:

`ONE NONRES HEAT-PUMP REUSE PRECEDENT != RESIDENTIAL/NATIONAL KEEP SHARE`.

## 5. Current LEHEL Viking 600 product-performance surface

Primary source:

`https://alurad.hu/_user/page/webshop/12/documents/lehel_muszaki_katalogus_2023.pdf`

The current technical catalogue publishes a full 600 mm connection-distance table with element count, radiator length and heat output at two explicit conditions relevant to the programme:

- `78/62/20 C`;
- `55/45/20 C`.

P51 materializes all 23 rows from 3 to 25 elements:

| Elements | Length mm | W @ 78/62/20 | W @ 55/45/20 |
|---:|---:|---:|---:|
| 3 | 187 | 273 | 140 |
| 4 | 262 | 406 | 208 |
| 5 | 337 | 537 | 275 |
| 6 | 412 | 668 | 342 |
| 7 | 487 | 797 | 408 |
| 8 | 562 | 926 | 474 |
| 9 | 637 | 1055 | 540 |
| 10 | 712 | 1184 | 607 |
| 11 | 787 | 1315 | 673 |
| 12 | 862 | 1445 | 740 |
| 13 | 937 | 1574 | 806 |
| 14 | 1012 | 1704 | 873 |
| 15 | 1087 | 1833 | 939 |
| 16 | 1162 | 1962 | 1005 |
| 17 | 1237 | 2091 | 1071 |
| 18 | 1312 | 2219 | 1137 |
| 19 | 1387 | 2348 | 1202 |
| 20 | 1462 | 2476 | 1268 |
| 21 | 1537 | 2603 | 1333 |
| 22 | 1612 | 2730 | 1398 |
| 23 | 1687 | 2858 | 1464 |
| 24 | 1762 | 2984 | 1528 |
| 25 | 1837 | 3111 | 1593 |

For every row, 55/45 output is lower than 78/62 output. P51 validates this instead of silently extrapolating a correction factor.

The same catalogue provides installation/hydraulic cautions. In particular, connection arrangement can materially change delivered output; the catalogue states substantial penalties for reverse-side connection and a roughly 10% nominal-output reduction for saddle connection. These are system-design controls, not stock-distribution evidence.

## 6. Family interchangeability is not exact SKU equivalence

LEHEL manufacturer material describes Viking as a successor/replacement family for legacy ALUTHERM/RADAL and states dimensional interchangeability at family level.

P51 records:

`manufacturer_family_interchangeable_with_radal=YES`

for the current Viking product-reference rows.

But this is not enough for an exact replacement decision because the programme must still prove:

1. old radiator's exact existing type/size;
2. old radiator output on an explicit comparable temperature basis;
3. post-envelope room heat loss;
4. target supply/return temperature;
5. required replacement output;
6. connection geometry and hydraulic resistance/flow suitability;
7. B06 product and CAPEX authority.

Thus:

`FAMILY INTERCHANGEABILITY -> CANDIDATE REPLACEMENT FAMILY`

but not:

`FAMILY INTERCHANGEABILITY -> EXACT REPLACEMENT SKU`.

## 7. Deákvár residential engineering rule

Public technical guidance from Deákvári Lakásfenntartó Szövetkezet:

`https://dlszvac.hu/2020/08/23/egycsoves-futesi-rendszerek-szabalyozhatova-tetele/`

The guidance describes the local legacy stock as generally RADAL room radiators with bathroom pipe registers and emphasizes that replacement must preserve both heat-output and hydraulic behaviour on a comparable temperature basis.

It explicitly warns against assuming that a different radiator of the same physical size has the same performance, and directs sizing to manufacturer performance tables rather than simple room-area or room-volume rules.

This directly supports the executable P51 comparison gate:

`SAME LENGTH / CONNECTION DISTANCE != SAME OUTPUT`

and:

`COMMON TEMPERATURE BASIS + HYDRAULICS REQUIRED`.

The guidance recommends Viking for RADAL replacement, but this remains a family-level engineering candidate rather than an automatic product selection.

## 8. Executable contract

`modules/B02/legacy_radal_replacement_gate.py` provides:

- `HistoricalInstalledSurfaceReference`;
- `assess_historical_installed_surface()`;
- `LegacyRadiatorReference`;
- `assess_legacy_radiator()`;
- `ReplacementProductReference`;
- `assess_replacement_product()`;
- `compare_legacy_to_replacement()`;
- `forbid_surface_to_piece_conversion()`.

### Historical surface gate

A qualified historical surface magnitude still always returns:

- `physical_piece_count=None`;
- `current_stock_authority=False`;
- `p42_national_authority=False`.

### Legacy-reference gate

Exact type/size/output/count rows can become technical references, but they never receive stock weighting automatically. `residential_stock_weight_allowed=False` is unconditional in P51 because representativeness requires a separate population-weight authority.

### Product-reference gate

A current product row requires valid dimensions and positive outputs at both explicit temperature bases; 55/45 output must be below 78/62 output. Qualification still returns:

`exact_replacement_selection_authorized=False`.

### Old-vs-new output comparison

A numeric comparison is allowed only when:

- both technical references qualify;
- connection distance matches;
- the legacy output has the exact same explicit temperature basis as the requested comparison basis.

The real Jászapáti old rows intentionally fail this comparison because their nominal-output basis is unspecified.

A hypothetical/future old reference with explicit `78_62_20` or `55_45_20` basis can produce a numeric output delta, but even that remains `QUALIFIED_OUTPUT_COMPARISON_ONLY`, never an exact replacement selection.

## 9. Effect on the programme

P51 advances the practical replacement problem in four ways:

1. an exact legacy RADAL 600 variant/size/output/count matrix is machine-readable;
2. one bounded envelope + air-water-heat-pump project proves that legacy RADAL emitters can be retained rather than universally replaced;
3. the current Viking 600 catalogue provides an explicit low-temperature replacement-product performance surface at 55/45/20;
4. the executable gate prevents unsupported old-vs-new output comparisons and prevents family-level interchangeability from becoming a product-selection shortcut.

What is still missing for national P42 closure:

- current radiator-heated dwelling count;
- current installed radiator-unit count;
- representative national type/material/configuration/size weights;
- a stock-level mapping from post-envelope heat loss + existing output + hydraulics to KEEP/UPSIZE/CHANGE;
- national replacement quantity/output bands.

Therefore all five P42 claims remain `Q / programme_use_allowed=NO`.

No external source binary is committed. No request, email, purchase, product price or CAPEX value is created in P51.
