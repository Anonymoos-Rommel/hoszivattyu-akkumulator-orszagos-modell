# B05-P21 - bounded PUZ-WM50VHA modulation-floor surface

## Purpose

P20 left one Q-B05-004 residual:

`MODULATION_FLOOR_SURFACE_OR_INTERPOLATION_CONTRACT_REQUIRED`.

P21 resolves that residual only for a bounded same-product rectangle. It does
not create a universal heat-pump floor surface.

Core rule:

`SOURCE-NATIVE CORNERS -> BOUNDED BILINEAR DERIVATION`

`ONE BOUNDED RECTANGLE != GLOBAL PRODUCT SURFACE`

`MANUFACTURER MIN-CURVE GRAPH != DIGITIZED NUMERIC DATA`

## Source-native corners

Exact outdoor unit:

`PUZ-WM50VHA`.

| outdoor / supply | minimum heating output | status |
|---|---:|---|
| A2/W35 | 2.50 kW | OBS |
| A2/W45 | 2.50 kW | OBS |
| A7/W35 | 1.80 kW | OBS |
| A7/W45 | 1.30 kW | OBS |

### A2 row

The Mitsubishi Ecodan planning handbook publishes for PUZ-WM50VHA:

- A2/W35 minimum-maximum heating output: 2.5..5.5 kW;
- A2/W45 minimum-maximum heating output: 2.5..5.1 kW;
- A2/W55 minimum-maximum heating output: 2.3..5.0 kW.

P21 uses only the W35 and W45 table values needed for the complete rectangle.
The manufacturer-authored PDF is public via a mirror. The browser PDF renderer
cannot load the roughly 24 MB file; the indexed exact table fields are
reproducible. The handbook's plotted minimum curves are semantic corroboration
only and are not numerically digitized.

### A7/W35

P20 already qualified manufacturer Min/Nom/Max data:

- minimum heating output = 1.80 kW.

### A7/W45

The official Mitsubishi Electric Sweden archived product page publishes:

- minimum heating output = 1.3 kW;
- nominal = 5.0 kW;
- maximum = 5.4 kW.

The page notes that detailed specifications apply in combination with
EHPT20X-YM9D. P21 uses the value only as the exact PUZ-WM50VHA outdoor-unit
floor corner.

## Interpolation contract

B05 has already used a deterministic complete-rectangle rule for physical
performance surfaces since P11:

- exact source corners remain OBS;
- interior values are DER;
- interpolation is bounded;
- missing corners fail closed;
- extrapolation is forbidden.

P21 applies the same project method explicitly to the minimum-modulation field.

For outdoor coordinate `o` in 2..7 C and supply coordinate `s` in 35..45 C,
the four exact source-native corners are bilinearly weighted.

Example at A3/W40:

- outdoor weight = (3-2)/(7-2) = 0.2;
- supply weight = (40-35)/(45-35) = 0.5;
- W35 floor at A3 = 2.50 + 0.2*(1.80-2.50) = 2.36 kW;
- W45 floor at A3 = 2.50 + 0.2*(1.30-2.50) = 2.26 kW;
- bounded bilinear floor = 2.31 kW.

This is DER, not a manufacturer observation.

## Engine correction

Before P21, `PerformanceMap.evaluate()` handled interpolated
`min_modulation_kw` differently from all other physical values: if four
corner floors existed it returned their simple arithmetic mean, independent of
the requested operating coordinate.

That is incorrect for a coordinate-dependent surface.

P21 repairs:

- the cold-boundary two-point path to coordinate-weighted linear floor
  interpolation;
- the complete-rectangle path to coordinate-weighted bilinear floor
  interpolation.

If any required floor corner is absent, `min_modulation_kw` remains unknown.

The engine still does not apply a cycling energy penalty by itself; P18/P20
contracts remain the numeric cycling-method authority.

## Residual transition

`MODULATION_FLOOR_SURFACE_OR_INTERPOLATION_CONTRACT_REQUIRED`
->
`RESOLVED_FOR_BOUNDED_MITSUBISHI_A2_A7_W35_W45_RECTANGLE`.

Q-B05-004 becomes:

`OPEN_NARROWED_TO_OUTSIDE_BOUNDED_MODULATION_FLOOR_COVERAGE`.

New residual:

`MODULATION_FLOOR_COVERAGE_OUTSIDE_MITSUBISHI_A2_A7_W35_W45_REQUIRED`.

No value is inferred below A2, above A7, below W35 or above W45.

## Readiness

PART_LOAD_MODULATION remains **45%**.

B05 remains **64%**.

No uplift is minted. P21 closes the method/surface blocker for one bounded
mild-temperature rectangle, but it does not cover the full Hungarian hourly
weather/supply domain or a representative product cohort.

## Sources

Mitsubishi Ecodan planning handbook 2021:
https://files.ecohandel.ch/documents/manuals/mitsubishi/Planungshandbuch_Ecodan_2021.pdf

Mitsubishi Electric Sweden PUZ-WM50VHA archived product page:
https://mitsubishielectric.se/produkter/villa/luft-vatten/utgangna/ecodan-package-utomhusdel/puz-wm50vha

P20 A7/W35 manufacturer source:
https://climatizzazione.mitsubishielectric.it/sites/default/files/2024-07/Scheda%20Tecnica%20PUZ-WM%20-%20rev.1.pdf
