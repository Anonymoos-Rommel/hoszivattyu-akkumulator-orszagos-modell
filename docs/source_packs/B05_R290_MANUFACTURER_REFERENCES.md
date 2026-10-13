# B05 R290 manufacturer references

V1-070 is a source-only inventory dated 2026-10-05. It adds no runtime
consumer or numerical method. The previously accepted WM50 reference, B05
slice status, reviewed commit, formulas, readiness and downstream gates remain
unchanged. `registry/b05_r290_reference_manifest.json` is the machine-readable
provenance and qualification record, not an admitted product/default.

## Source identity and reuse

- `SRC-B05-MITSUBISHI-WZ-DATABOOK-2025`: [Mitsubishi WZ Vol.1.0](https://library.mitsubishielectric.co.uk/pdf/download_full/5483), issued May 2025, M-E0977 SIZ2025. PDF creation/modification metadata are separate dates.
- `SRC-B05-MITSUBISHI-WZ50-PI-2025`: [UK/Ireland WZ50 product sheet](https://library.mitsubishielectric.co.uk/pdf/download_full/4927), effective January 2025, despite February 2026 PDF metadata.
- `SRC-B05-MITSUBISHI-FTC7-MANUAL-2024`: [FTC7 installation manual](https://library.mitsubishielectric.co.uk/pdf/download_full/4950), DG79H200H02. April 2024 PDF metadata does not establish an exact issue date.
- `SRC-B05-MITSUBISHI-HU-CATALOGUE-2024`: [manufacturer-authored Hungarian catalogue](https://mklima.hu/storage/app/uploads/public/689/995/2d6/6899952d6676a549765922.pdf), HU-00386, December 2024, hosted by a distributor. The August 2025 hosting date is not the issue date. This is supplementary naming evidence, not independent performance replication.

Exact retrieval timestamps, byte counts and SHA-256 identities are in the
manifest. Original documents, extracted text and page images are external-only;
repository republication has not been cleared. Only necessary attributed facts
and qualification metadata are retained. Stable source IDs are the authority;
page references below identify the inspected locations.

`OBS` here means a source-reported declaration, not an independently measured
field result. The manufacturer grid can itself contain interpolation or
calculation. `SCN` applies only to the separately described service-use cases.
Document issue/effective roles remain distinct from PDF and hosting dates.
Units, method, model, mode and conditions accompany each numeric reference;
unknown values remain null. Dates and source/page/model identifiers are metadata.

## Six heating anchors, with separate labels

| Source and locator | Source condition and label | Output, kW | COP, ratio | Declared input, kW |
| --- | --- | ---: | ---: | ---: |
| WZ databook PDF p11 / A-7 | A7/W35, capacity table | 4.00 | 5.10 | 0.78 |
| WZ databook PDF p11 / A-7 | A2/W35, capacity table | 5.00 | 3.15 | 1.59 |
| WZ databook PDF p40 / A-36 | A-7/W35, Partload1 | 5.0 | 2.70 | not tabulated |
| WZ databook PDF p40 / A-36 | A-7/W35, Max | 5.2 | 2.68 | not tabulated |
| WZ50 sheet PDF p2, note 2 | A-7/W35, normal heating conditions | 5.2 | 2.68 | 1.94 |
| WZ databook PDF p40 / A-36 | A-25/W35, Max | 3.2 | 1.85 | not tabulated |

All values in the table are OBS source declarations. Inputs not tabulated are
not filled using output/COP. Published rounded triples need not divide exactly.
The two p11 rows use EN14511 parts 1–4:2018 and include the standard pump input
in COP/electrical input. Their respective OBS test flows are 11.5 and 14.3 L/min.
The lower 2022 standard heading on p11 belongs to different models.

The p38 / A-34 grid notes cite EN14511 without a year, permit manufacturer
interpolation/calculation and mark defrost-inclusive cells in grey. At p40 /
A-36, the WZ50 A-7/W35 Partload1 and Max capacity/COP cells are not grey;
the A2 Partload1 cross-reference is grey. Not-grey is not proof of zero
defrost. The p11 values agree numerically with p40 Partload1,
without changing their capacity-table labels. No additional points are admitted.

The product sheet explicitly states OBS dry/wet bulb temperatures of -7/-8°C
and outlet/inlet water temperatures of 35/30°C. Its values match the databook's
Max row numerically, but the sheet does not call them Max. These method/condition
boundaries are not inferred for other rows. Finite anchors establish neither
annual SPF/SCOP nor a runtime interpolation, dispatch or correction method.

The separate ErP reference is OBS 5.0 kW rated heat output for WZ50 + ERPX-VM2E,
medium-temperature average climate, databook p13 / A-9. It is not a legal
maximum-rated-capacity determination, field load or constant output guarantee.

## Exact configuration relationships

The p6 / A-2 WZ50(-BS) specification is a water-connected R290 monoblock with
built-in outdoor refrigerant/water exchanger, OBS 0.6 kg charge and OBS
single-phase 230 V / 50 Hz supply. The base PUZ-WZ50VAA and -BS commercial
variant are not assumed to have interchangeable price, warranty or contents.
“Hydro-Split” does not imply a field refrigerant-pipe connection.

- PUZ-WZ50VAA + ERPX-VM2E: compatibility p68 / B-2; specifications p72 / B-6;
  combination performance p73 / B-7; components pp152–153 / B-86–B-87. This
  reversible indoor hydrobox can serve the separately labelled heating-only
  SCN. It includes control/main remote, circulation pump, flow sensor, expansion
  vessel, booster and magnetic filter. OBS booster/vessel/internal heating water
  are 2 kW / 10 L / 4.5 L. There is no DHW cylinder. A standalone controller is
  not automatically added or charged again.
- PUZ-WZ50VAA + ERPT20X-VM2E: separately compatible at pp68,70,73. This reversible
  cylinder route has an OBS 200 L DHW cylinder, 2 kW booster and 12 L vessel.
  It replaces the ERPX route. The UK sheet's EHPT20X-MEHEW is a distinct model;
  its DHW rating cannot be transferred to this route.
- PUZ-WZ50VAA(-BS) + PAC-IF081B-E + mandatory PAC-FS01-E: databook p187 / C-3.
  Manual pp3,6–8 distinguishes supplied remote/thermistors from locally supplied
  pump, protection, hydraulic circuit and conditional DHW tank/valve. This is an
  alternative controller architecture, not a complete hydraulic module.

FTC7 family naming is supplementary HU catalogue pp8,30 evidence. Exact
compatibility comes from the databook, not a generic controller-generation name.

## Source contradictions and conditional boundaries

All readings below remain OBS declarations; no source is silently repaired and
no harmonised numeric default is chosen.

The databook p6 and manual p7 / printed p6, Table 3.4.1 report an OBS
6.5–14.3 L/min flow range. Separately, the product sheet p2 WATER DATA reports
OBS pipework size 22 mm, flow rate 14 L/min and water pressure drop 18.16 kPa.
It has no Min/Max flow labels. An earlier qualification misread pipework size
as a flow minimum and invented a maximum label; that conclusion is withdrawn.
This was a reading error, not a manufacturer discrepancy. The corrected
source-native rows retain their distinct units and roles. No test condition,
minimum/maximum, rounding reconciliation or hydraulic default is inferred.

The following four source differences remain unresolved:

- GWP: databook p6 gives R290 (3). The sheet gives 0.02/IPCC6 yet 0.0018 tCO2eq
  for 0.6 kg. The CO2eq is consistent with the former GWP, not the latter.
  No emissions or procurement-eligibility default follows.
- Cooling input at A35/W18: databook p11 gives 0.35 kW; combination p73 gives
  1.31 kW. Neither is used for a cooling scenario or energy calculation.
- EHPT20X-MEHEW DHW efficiency: databook p13 gives 134%; product sheet gives
  143%. No transfer to ERPT20X-VM2E, ERPX or annual DHW performance.
- Product-specific ERPX heating water is 4.5 L; generic hydraulic table p158 /
  B-92 uses an indoor 5 L reference and additional 2 L for average/warmer or
  24 L for colder climate. These are not a universal buffer specification.
  Circuit division, pump interlock, bypass, climate and actual volume matter;
  a buffer addresses insufficient required volume.

Separate OBS ambient limits at p6 are heating -25 to +24°C, DHW -25 to +46°C,
and cooling +10 to +46°C. At p26 / A-22, OBS maximum outlet references are 65°C
at ambient -25°C and 75°C at -15°C. These limits do not guarantee simultaneous
rated output. Return-temperature admissibility depends on water volume (p27).
R290 siting/fire-safety and hydraulics (pp62–66,153) still need site-specific
qualification. No site-safe design is certified.

## Non-admission and verification

There is no product choice, complete current Hungarian equipment price,
installed cost, 2028 procurement legality/current-default, WM50 replacement,
annual field result, runtime admission, scenario widening or readiness/task
closure. Installation scope remains unpriced. Historical source revision,
retrieval date and future procurement date are separate.

The registry validator and `tests/test_b05_r290_references.py` check original
identities, six native values, units/truth/method/conditions, distinct controller
and DHW routes, literal contradictions and fail-closed non-admission. Mutations
cover plausible-but-wrong values and semantic promotion, including mutations
with a recomputed anchor digest. Revision/date roles, exact source/page/model
relationships, reference cardinality, integrated versus standalone components
and generic versus actual water-volume scope are checked directly. Existing
physics/formula gates are unchanged.
