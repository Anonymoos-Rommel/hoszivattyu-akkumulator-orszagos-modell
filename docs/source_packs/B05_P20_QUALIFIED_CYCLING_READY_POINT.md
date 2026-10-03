# B05-P20 - first qualified cycling-ready exact product point

## Current-use qualification — 2026-10-02

The original account below is retained as historical claim lineage. Its WM50
exact cycling-ready co-location conclusion is superseded for current use by
`registry/b05_cycling_source_admission_manifest.json` and
`docs/checkpoints/V1_035_CYCLING_SOURCE_ADMISSION.md` .

The presently readable standalone KEYMARK `PUZ-WM50VHA(-BS)`, Units Outdoor,
registration `037-0032-20 / rev.2`, certification date `19.12.2023`, reports
warmer +7 C Cdh low/medium **0.980/0.980** and average **0.950/0.960**. The prior
P20 warmer 0.950 attribution lacks current corroboration. Original September 24
bytes were not retained; historical cause is unresolved. No old transcription
error or publisher revision is asserted.

The source-native manufacturer minimum Q/input/COP pairs remain qualified at
their fixed water coordinates. Published Cdh remains an observation at its own
climate/application/bin scope. CALCM:01 issue 1.2 Appendix D / Table D1 (page 62)
distinguishes fixed and variable test-water branches; an application label does
not identify the selected branch. P20/P22 exact fixed-W35 joining therefore
remains Q pending source-bound test conditions or a named permissible transfer
rule. Neither branch is assumed for WM50. Swapping 0.950 for 0.980 cannot close
this gap.

P18 arithmetic remains valid conditionally. `evaluate_conditional_cycling_point`
returns `CONDITIONAL_STANDARD_METHOD_CALCULATION`; the existing source-qualified
entry point returns Q and null COP/input while authority is absent. No actual
hourly electricity/SPF or national policy follows. Manufacturer grids,
interpolation and independent evidence gates are unchanged. The original P59
eight-point exact execution gate is now unresolved for both product families;
current total readiness is Q/null with 67 supported points and 8 unresolved
weight. Historical 75 and independent B05 module 64 remain explicit.


## Purpose

P19 narrowed Q-B05-004 to:

- `POINT_PAIRED_MINIMUM_CAPACITY_COP_REQUIRED`;
- `MODULATION_FLOOR_SURFACE_OR_INTERPOLATION_CONTRACT_REQUIRED`.

P20 closes the first residual for one exact, current product point without
changing the B05 engine's generic hourly energy formula.

## 1. Manufacturer point-pair authority

Mitsubishi Electric's PUZ-WM technical sheet publishes for `PUZ-WM50VHA`
at A7/W35, with explicit `Min / Nom / Max` positional semantics:

| quantity | Min | Nom | Max |
|---|---:|---:|---:|
| heating capacity | 1.80 kW | 5.00 kW | 5.60 kW |
| absorbed power | 0.33 kW | 1.00 kW | 1.16 kW |
| COP | 5.46 | 5.00 | 4.82 |

Therefore the minimum point is source-native and point-paired:

`1.80 kW heat <-> 0.33 kW input <-> COP 5.46`.

Internal consistency:

`1.80 / 0.33 = 5.454545...`

which is within the canonical 0.05 COP rounding tolerance of the declared 5.46.

This is categorically different from the P19 Amitime range case because the
Mitsubishi source explicitly labels all three rows with the same positional
`Min / Nom / Max` structure.

## 2. Product identity bridge

The Italian manufacturer sheet uses:

`PUZ-WM50VHA`.

Mitsubishi's own UK product information uses:

`PUZ-WM50VHA(-BS)`.

The current HP KEYMARK certification uses the same:

`PUZ-WM50VHA(-BS)`.

P20 uses this manufacturer-corroborated optional-suffix notation as the bounded
identity bridge. It does not generalize across another Mitsubishi model.

## 3. Current certified Cdh

Current HP KEYMARK subtype:

- Ecodan Power Inverter 5-200D Packaged;
- registration `037-0032-20 / rev. 2`;
- certificate holder Mitsubishi Electric Air Conditioning Systems Europe LTD;
- testing laboratory SZU Brno.

The outdoor-only `PUZ-WM50VHA(-BS)` record publishes warmer-climate,
low-temperature EN14825 values including:

- at +7 C, Cdh = **0.950**.

This is non-default and therefore fits the existing P15 measurement-determined
classification rule.

## 4. First full co-location

At exact product-coordinate:

`PUZ-WM50VHA @ A7/W35`

P20 now has all inputs required by P18/P19:

1. exact minimum capacity = 1.80 kW;
2. exact point-paired minimum COPd = 5.46;
3. certified measurement-determined Cdh = 0.950.

Therefore:

`CYCLING_INPUT_COLOCATION_GATE`
->
`RESOLVED_FOR_ONE_EXACT_CURRENT_PRODUCT_POINT`.

And:

`POINT_PAIRED_MINIMUM_CAPACITY_COP_REQUIRED`
->
`RESOLVED_FOR_QUALIFIED_MITSUBISHI_A7_W35_POINT`.

## 5. Executable cycling calculation

For any positive heat requirement below 1.80 kW **at this exact A7/W35 point**:

`CR = required_heat / 1.80`

then P18 applies:

`COPbin = 5.46 * CR / (0.950 * CR + (1 - 0.950))`.

Example only for contract verification:

- required heat = 0.90 kW;
- CR = 0.5;
- COPbin = 5.20;
- heat-pump electrical input = 0.90 / 5.20 = 0.1730769 kW.

The example is a deterministic consequence of the qualified inputs and P18
method. It is not a national weighting or product-market claim.

## 6. Q-B05-004 after P20

New state:

`OPEN_NARROWED_TO_MODULATION_FLOOR_SURFACE_ONLY`.

Only residual:

`MODULATION_FLOOR_SURFACE_OR_INTERPOLATION_CONTRACT_REQUIRED`.

P20 does not claim that the 1.80 kW minimum floor is valid at A2/W35,
A-7/W35, W45, W55 or any other coordinate.

## 7. Readiness

PART_LOAD_MODULATION remains **45%**.

B05 remains **64%**.

No readiness uplift is minted because one exact cycling-ready product point is
not yet an hourly modulation-floor surface.

## Sources

Mitsubishi Electric Italian technical sheet:
https://climatizzazione.mitsubishielectric.it/sites/default/files/2024-07/Scheda%20Tecnica%20PUZ-WM%20-%20rev.1.pdf

Mitsubishi Electric UK product identity sheet:
https://library.mitsubishielectric.co.uk/pdf/download_full/4144

Current HP KEYMARK subtype:
https://www.heatpumpkeymark.com/en/nc/ps-keymark/certificate-holders/?cHash=0aecf6bcedcd369e5acf7a509916b562&tx_pskeymark_frontend%5Baction%5D=showSubtype&tx_pskeymark_frontend%5Bcontroller%5D=Frontend&tx_pskeymark_frontend%5Bsubtype%5D=4300
