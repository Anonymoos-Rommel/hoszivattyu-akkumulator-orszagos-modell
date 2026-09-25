# B05-P26 - Mitsubishi cold/high-supply classification

## Goal

P22 left five blank PUZ-WM50VHA(-BS) minimum-performance cells at the cold/high-supply edge.

Those blanks were previously treated conservatively as an unresolved question:

`MITSUBISHI_COLD_HIGH_SUPPLY_DOMAIN_CLASSIFICATION_REQUIRED`.

P26 asks a simpler question:

**is a blank cell missing minimum-performance data, or is the requested operating point outside the product envelope?**

## Manufacturer operating envelope

Mitsubishi publishes a maximum outlet-water-temperature versus ambient-temperature curve for PUZ-WM50VHA.

The curve is roughly at W40 at A-20 and reaches W55 at A-10.

P26 uses this graph only as a classification boundary.

It does **not** digitize an intermediate numeric curve and does not add synthetic performance points.

## Reclassification

P22 blank Min cells:

| coordinate | P26 classification |
|---|---|
| A-20/W45 | OUTSIDE_OPERATING_ENVELOPE |
| A-20/W50 | OUTSIDE_OPERATING_ENVELOPE |
| A-20/W55 | OUTSIDE_OPERATING_ENVELOPE |
| A-15/W55 | OUTSIDE_OPERATING_ENVELOPE |
| A-15/W50 | Q_THRESHOLD_NOT_EXACT |

The first four are no longer missing modulation-floor data.

They are product-applicability exclusions.

A-15/W50 remains Q because P26 will not infer an exact threshold from a plotted line.

## P9 consequence

The canonical P9 mean-stress interval is:

`-13.331944 .. -9.644444 C`.

At W55, the colder part below approximately A-10 is outside the WM50 outlet-water envelope.

Therefore the correct interpretation is:

`PRODUCT_NOT_APPLICABLE_AT_REQUIRED_SUPPLY`

not:

`MISSING_MODULATION_FLOOR_DATA`.

That distinction matters for product selection in the national model.

## Dimplex re-check

P26 also re-checked the current 2026 Dimplex System C handbook before attempting the previously planned A-10 closure.

The source still shows:

`A-10/W35 min = -`.

The adjacent:

`19.8 / 2.8`

pair is in the **max** column.

Therefore no Dimplex A-10 minimum point is admitted.

## Residual transition

`MITSUBISHI_COLD_HIGH_SUPPLY_DOMAIN_CLASSIFICATION_REQUIRED`

->
`PARTIAL_RESOLVED_NARROWED_TO_A_MINUS15_W50`.

New exact residual:

`MITSUBISHI_A_MINUS15_W50_MINIMUM_CLASSIFICATION_REQUIRED`.

Q-B05-004 becomes:

`OPEN_NARROWED_TO_SINGLE_MITSUBISHI_CELL_PLUS_DIMPLEX_FANCOIL_TAU_EQ`.

Other residuals remain unchanged:

- `DIMPLEX_A_MINUS10_MINIMUM_ROW_CLASSIFICATION_REQUIRED`;
- `HEM_FANCOIL_EMITTER_TIME_DOC_CODE_DIVERGENCE_REQUIRED`;
- `PRODUCT_SPECIFIC_TAU_EQ_EVIDENCE_REQUIRED_FOR_OBS_RUNTIME`.

## Readiness

PART_LOAD_MODULATION remains **45%**.

B05 remains **64%**.

No readiness uplift is created simply by reclassifying product-inapplicable points.

## Sources

Mitsubishi Electric Ecodan 2025 practical guide:
https://climatizzazione.mitsubishielectric.it/sites/default/files/2025-09/Guida%20Ecodan_2025_web%20%281%29.pdf

Mitsubishi Electric R32 Data Book:
https://library.mitsubishielectric.co.uk/pdf/download_full/4099

Dimplex System C 2026 planning handbook:
https://www.dimplex.eu/sites/g/files/emiian586/files/2026-05/Projektierungshandbuch%20System%20C%C2%AE-v15-20260319_150009__EN_V2_final.pdf
