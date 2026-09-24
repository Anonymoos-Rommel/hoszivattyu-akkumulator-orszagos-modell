# B05-P26 - product-domain classification closure

## Purpose

P25 left two questions that mixed two different ideas:

1. is the operating point supported by the product?
2. is minimum-modulation performance published at that point?

P26 separates them with source-native manufacturer operating envelopes.

## Mitsubishi PUZ-WM50VHA(-BS)

The official Mitsubishi Data Book states:

- guaranteed outdoor heating range: **-20..+24 C**;
- maximum heating outlet-water temperature: **60 C**.

Therefore cold/high-supply points such as A-15/W55 are inside the product's
stated heating operating envelope.

The blank **Min** cells in the Data Book cannot be treated as evidence that the
operating combination is unsupported.

They mean only that P22 has no source-native minimum-capacity/COP value there.

Transition:

`MITSUBISHI_COLD_HIGH_SUPPLY_DOMAIN_CLASSIFICATION_REQUIRED`
->
`RESOLVED_SUPPORTED_OPERATION_MINIMUM_POINT_UNPUBLISHED`.

New residual:

`MITSUBISHI_COLD_HIGH_SUPPLY_MINIMUM_POINT_EVIDENCE_REQUIRED`.

This does **not** extend the modulation-floor surface.

## Dimplex LA 2030CP

The current official Dimplex technical page states:

- heating-air operating range: **-22..+40 C**;
- heating-water flow temperature: **up to 70 C**.

Therefore A-10/W35, A-10/W45 and A-10/W55 are all inside the stated product
operating envelope.

The fact that the minimum-output table has no usable A-10 minimum row is not
evidence that A-10 operation is unsupported.

Transition:

`DIMPLEX_A_MINUS10_MINIMUM_ROW_CLASSIFICATION_REQUIRED`
->
`RESOLVED_SUPPORTED_OPERATION_MINIMUM_POINT_UNPUBLISHED`.

New residual:

`DIMPLEX_A_MINUS10_MINIMUM_POINT_EVIDENCE_REQUIRED`.

The P23 interpolation barrier remains, because operating support is not a
numeric minimum-output value.

## P9 stress consequence

For both products, the canonical P9 mean-stress envelope
`-13.331944..-9.644444 C` is inside the stated heating operating range.

That resolves **operation-domain support**.

It does not resolve **minimum-modulation floor coverage** where source-native
minimum values are missing.

## Q-B05-004

Current state:

`OPEN_NARROWED_TO_MINIMUM_POINT_GAPS_FANCOIL_AND_PRODUCT_TAU_EQ`.

Remaining residuals:

- `MITSUBISHI_COLD_HIGH_SUPPLY_MINIMUM_POINT_EVIDENCE_REQUIRED`;
- `DIMPLEX_A_MINUS10_MINIMUM_POINT_EVIDENCE_REQUIRED`;
- `HEM_FANCOIL_EMITTER_TIME_DOC_CODE_DIVERGENCE_REQUIRED`;
- `PRODUCT_SPECIFIC_TAU_EQ_EVIDENCE_REQUIRED_FOR_OBS_RUNTIME`.

## Readiness

PART_LOAD_MODULATION remains **45%**.

B05 remains **64%**.

P26 removes classification ambiguity but does not create missing minimum-point
measurements.

## Sources

Mitsubishi Electric Data Book Vol.5.3:
https://library.mitsubishielectric.co.uk/pdf/download_full/4099

Dimplex LA 2030CP technical product information:
https://dimplex.atlassian.net/wiki/spaces/PRO/pages/3902636350/Technische+Produktinformationen+LA+2030CP
