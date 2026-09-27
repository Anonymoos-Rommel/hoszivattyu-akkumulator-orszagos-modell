# B05-P46 - Mitsubishi A-15/W50 source-native domain boundary

Date: 2026-09-27
Canonical base: `cf04aeae0d9979cccc62d959ab50b42ce4d534b7`

## Purpose

P46 attacks the last Mitsubishi coordinate-coverage residual inside Q-B05-004:

`MITSUBISHI_A_MINUS15_W50_MINIMUM_CLASSIFICATION_REQUIRED`

P26 correctly refused to digitize the manufacturer's maximum-outlet-temperature graph at the intermediate A-15 coordinate. P42 then confirmed that current Vol.6.0 still leaves A-15/W50 blank across all published performance levels.

P46 asks whether repeated manufacturer revisions or alternate official Mitsubishi publication surfaces now provide a source-native categorical or numeric answer.

## 1. Multi-revision performance-table persistence

The PUZ-WM50VHA(-BS) performance grid has now been checked across three manufacturer databook generations.

### Vol.5.3

At A-15:

- W35: populated;
- W40: populated;
- W45: populated;
- W50: blank;
- W55: blank;
- W60: blank.

The same pattern appears across Max, Nominal, Mid/part-load and Min levels.

At A-10, W50 and W55 are explicitly populated.

### Vol.5.9

Mitsubishi's current UK document library explicitly lists **Ecodan ATW Databook R32 Vol5.9** for PUZ-WM50VHA and PUZ-WM50VHA-BS.

A public manufacturer-authored copy of that exact artifact reproduces the same A-15 boundary:

- W35/W40/W45 populated;
- W50/W55/W60 blank;
- same pattern across Max/Nominal/Partload1/Partload2/Min;
- A-10/W50 and A-10/W55 populated.

The public-copy host is recorded as a mirror; it is not represented as Mitsubishi infrastructure.

### Vol.6.0

P42 already established that current Vol.6.0 preserves the A-15/W50 blank at every published performance level.

Therefore:

```
VOL5.3_BLANK
+ VOL5.9_BLANK
+ VOL6.0_BLANK
= PERSISTENT_SOURCE_AVAILABILITY_BOUNDARY
```

but **not**:

```
PERSISTENT_BLANK = PHYSICAL_IMPOSSIBILITY
```

## 2. Independent official manufacturer surfaces

### Mitsubishi Electric Sweden

The archived official PUZ-WM50VHA product page publishes exact low-ambient outputs:

- A-15/W35 = **3.9 kW**
- A-15/W45 = **3.9 kW**

It does not publish an A-15/W50 performance point.

### Mitsubishi Electric France - 2026 catalogue

The official 2026 Ecodan catalogue publishes for PUZ-WM50VHA:

- maximum capacity A-15/W35 = **3.90 kW**
- maximum capacity A-15/W45 = **3.90 kW**

Again, no A-15/W50 performance point is published.

These two surfaces independently corroborate that Mitsubishi's source-native low-ambient publication stops at W45 at A-15.

That remains a publication/evidence boundary, not an operating prohibition.

## 3. Why the 60 C specification does not close the cell

Mitsubishi material also publishes broader specifications such as:

- overall maximum outlet-water temperature;
- overall ambient heating operating range.

Those are not a two-dimensional operating-coordinate record.

The project therefore freezes:

```
MAX_OUTLET_TEMPERATURE_1D
+ AMBIENT_OPERATING_RANGE_1D
!=
A_MINUS15_W50_2D_ADMISSIBILITY
```

and:

```
A_MINUS15_W45_SUPPORTED
+ A_MINUS10_W50_SUPPORTED
!=
A_MINUS15_W50_SUPPORTED
```

No interpolation, diagonal inference, graph digitization or continuity assumption is allowed.

## 4. Exact admission path

A future A-15/W50 classification may be admitted only from source-native evidence that explicitly binds **both** coordinates to the exact PUZ-WM50VHA(-BS) product.

Accepted classes:

1. exact manufacturer/laboratory performance table at A-15/W50;
2. exact manufacturer tabular operating-domain statement covering A-15/W50;
3. exact manufacturer categorical statement that W50 at A-15 is supported or outside the operating envelope;
4. exact test report / selection report whose source-native input/output explicitly contains A-15 and W50 for the product.

Not accepted:

- blank-cell interpretation;
- visual graph digitization;
- interpolation between A-15/W45 and A-10/W50;
- overall 60 C maximum temperature combined with a separate -20 C ambient operating limit;
- reseller interpretation without underlying exact manufacturer authority.

## 5. Residual transition

Previous residual:

`MITSUBISHI_A_MINUS15_W50_MINIMUM_CLASSIFICATION_REQUIRED`

becomes:

`EXACT_SOURCE_NATIVE_A_MINUS15_W50_2D_OPERATING_OR_PERFORMANCE_RECORD_REQUIRED`

This is not a physical closure. It is a tighter acquisition object.

## 6. Readiness

No new capacity, COP or minimum-modulation point is admitted.

- PART_LOAD_MODULATION = **45%**
- B05 = **64%**

## Public sources

- Mitsubishi Electric R32 Data Book Vol.5.3:
  https://library.mitsubishielectric.co.uk/pdf/download_full/4099
- Mitsubishi Electric current databook directory listing Vol.5.9:
  https://library.mitsubishielectric.co.uk/pdf/directory/residential_heating/technical_documents/current/databook
- Public manufacturer-authored Vol.5.9 copy:
  https://www.nukumi.cz/data/files/14/databook-pro-tepelna-cerpadla-vzduch-voda-ecodan-r32-v5-9-1757076872.pdf?v=cf854bb1
- Mitsubishi Electric current Vol.6.0 document-library record:
  https://library.mitsubishielectric.co.uk/pdf/book/Ecodan_ATW_Databook_Vol.6_.0_.pdf
- Mitsubishi Electric Sweden PUZ-WM50VHA:
  https://mitsubishielectric.se/produkter/villa/luft-vatten/utgangna/ecodan-package-utomhusdel/puz-wm50vha
- Mitsubishi Electric France Ecodan 2026 catalogue:
  https://confort.mitsubishielectric.fr/sites/default/files/2025-10/ECODAN_CATALOGUE_INTERACTIF_2026_light.pdf
