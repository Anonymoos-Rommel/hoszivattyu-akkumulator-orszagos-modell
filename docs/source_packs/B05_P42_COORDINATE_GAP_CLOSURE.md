# B05-P42 - current-revision coordinate-gap closure

## Current-use qualification — 2026-10-02

Dimplex LA 2030CP exact fixed-W35 cycling joining is Q. The current KEYMARK
Outdoor record (registration 40060852, certification date 2025-08-29) separately
corroborates average/low Cdh at -7/+2/+7/+12 C: .990/.970/.953/.912. It does
not identify the fixed/variable test-water branch or authorize Cdh transfer to
manufacturer MIN points. The unchanged current P42 System C 03/2026 W35
minimum Q/P/COP facts remain source-native; P23 values remain historical and
are not mixed into the current revision. The exact-bin closure in the original
account below is retained as history and is superseded for physical admission.
See the [V1-035 current qualification](../checkpoints/V1_035_CYCLING_SOURCE_ADMISSION.md)
and `registry/b05_cycling_source_admission_manifest.json`. No runtime method,
actual hourly electricity/SPF or national policy is selected.


## Purpose

P42 freezes the independent S2125 defrost acquisition path while owner
responses are pending and returns to Q-B05-004.

The original targets were:

1. Dimplex LA 2030CP A-10 minimum-performance row;
2. Mitsubishi PUZ-WM50VHA(-BS) A-15/W50 applicability/minimum classification.

The Dimplex audit exposed a more important revision issue: the current detailed
System C Version 03/2026 tables not only populate A-10, but revise some values
published on the older summary surface used by P23. P42 therefore treats the
current detailed revision as one coherent current-use authority instead of
mixing generations.

No graph digitization, extrapolation, cross-product transfer, cross-version
mixing or silent blank-cell filling is allowed.

## 1. Dimplex current detailed revision

The current manufacturer System C planning manual, Version 03/2026, sections
3.10.1-3.10.3 publishes exact minimum heat output, minimum electrical input and
minimum-point COP at ten outdoor nodes for each of W35, W45 and W55.

Current grid:

- outdoor nodes: A-22, A-15, A-10, A-7, A2, A7, A12, A20, A30, A40;
- supply nodes: W35, W45, W55;
- 30 exact source-native minimum Qh/Pel/COP points;
- 18 complete adjacent rectangular cells.

The A-10 row is explicit:

| coordinate | Qh min kW | Pel min kW | COP min |
|---|---:|---:|---:|
| A-10/W35 | 9.10 | 2.77 | 3.28 |
| A-10/W45 | 8.73 | 3.36 | 2.60 |
| A-10/W55 | 8.51 | 4.03 | 2.11 |

Therefore:

`DIMPLEX_A_MINUS10_MINIMUM_ROW_CLASSIFICATION_REQUIRED`
->
`RESOLVED_BY_CURRENT_REVISION_FULL_SURFACE`.

## 2. Revision boundary versus P23

P23 correctly preserved the older public summary surface fail-closed and
inserted an A-10 barrier because that summary had no usable A-10 minimum row.

The current detailed Version 03/2026 surface is not identical to that older
summary at every coordinate. For example:

- older P23 summary A7/W35 minimum: 9.8 kW / COP 5.3;
- current detailed 03/2026 A7/W35 minimum: 7.72 kW / COP 5.49.

P42 does not splice the new A-10 row into the old P23 grid.

Instead:

`P23 DIMPLEX CURRENT-USE SURFACE`
->
`SUPERSEDED_BY_CURRENT_DETAILED_REVISION`.

P23 remains valid historical provenance for the source state it audited.
Current runtime/model use must use the coherent P42 03/2026 Dimplex grid.

## 3. Dimplex consequences

The current W35/W45/W55 floor surface contains 30 exact OBS points and 18
complete cells.

Canonical P9 mean-stress interval:

`-13.331944 .. -9.644444 C`.

The entire interval is inside complete current-revision Dimplex cells at W35,
W45 and W55.

The detailed W35 table also publishes exact minimum capacity/COP at the four
existing HP KEYMARK Cdh temperatures -7,+2,+7,+12 C. Therefore the current
Dimplex exact W35 cycling-ready bin count becomes four.

P42 does not interpolate Cdh between those bins and does not manufacture an
arbitrary-hour cycling penalty.

## 4. Mitsubishi A-15/W50 remains Q

A current official-document-library recheck of Ecodan ATW Databook R290/R32
Vol.6.0 preserves the key source pattern at PUZ-WM50VHA(-BS): A-15/W50 remains
blank across Max, Nominal, Mid and Min performance levels.

This strengthens the source-availability result but does not itself prove that
A-15/W50 is physically impossible.

The outlet-water operating-envelope graph remains non-tabular at this exact
intermediate threshold. P42 therefore does not digitize the graph and does not
convert the persistent blank into OUTSIDE_OPERATING_ENVELOPE.

Current status:

`MITSUBISHI_A_MINUS15_W50_MINIMUM_CLASSIFICATION_REQUIRED`
->
`OPEN_BOUNDED_PERSISTENT_ALL_LEVELS_BLANK`.

For model execution the coordinate remains fail-closed.

## 5. Q-B05-004 transition

Current umbrella state:

`OPEN_NARROWED_TO_SINGLE_MITSUBISHI_CELL_PLUS_OBS_TRANSIENT_FIDELITY`.

Residuals:

1. `MITSUBISHI_A_MINUS15_W50_MINIMUM_CLASSIFICATION_REQUIRED`;
2. `FANCOIL_OBS_EMITTER_RESPONSE_EVIDENCE_REQUIRED`;
3. `PRODUCT_OR_LAB_TRANSIENT_TEST_RECORD_REQUIRED`.

The HEM fan-coil document/code policy divergence remains resolved by P31
authority separation and is not reopened.

## 6. Readiness

PART_LOAD_MODULATION remains **45%**.

B05 remains **64%**.

The Dimplex current source surface is now materially stronger and internally
revision-coherent, but generic OBS hourly transient fidelity remains open.

## Sources

Dimplex System C planning manual Version 03/2026:
https://www.dimplex.eu/sites/g/files/emiian586/files/2026-03/Projektierungshandbuch%20System%20C%C2%AE-v15-20260319_150009_DE_final.pdf

Mitsubishi Electric current document library - Ecodan ATW Databook R290/R32
Vol.6.0:
https://library.mitsubishielectric.co.uk/pdf/book/Ecodan_ATW_Databook_Vol.6_.0_.pdf
