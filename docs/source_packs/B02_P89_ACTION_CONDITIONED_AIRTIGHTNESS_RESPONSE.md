# B02-P89 — ACTION-CONDITIONED POST-RETROFIT AIRTIGHTNESS RESPONSE

## Goal

Resolve the P88 residual as far as the available measured evidence honestly allows:

`ACTION_CONDITIONED_POST_RETROFIT_INFILTRATION_REQUIRED`

P89 does **not** assign one national post-retrofit infiltration value.

It establishes:

1. measured retrofit airtightness response evidence;
2. a Hungarian pressure-transfer calibration from `n50` to a 4 Pa ACH state;
3. an executable same-metric response engine;
4. the exact remaining blocker needed for an absolute post-retrofit infiltration state.

Base:
`d1d3159326ea152140695b1ae035c5d7c157a6a1`

## Evidence admitted

### 1. Hungarian PTE / AIVC field campaign

Source:
`SRC-B02-HU-PTE-AIRTIGHTNESS-2014`

The University of Pécs / Croatian-Hungarian border campaign reports:

- **33 Hungarian field locations**;
- 19 in Pécs and 14 in smaller settlements;
- mostly residential houses/apartments, with some non-residential cases;
- both Type-A ACH and Type-B airtightness testing on the Hungarian side;
- most old buildings in the tested stock were refurbished.

Critical source semantics:

- Type A leaves purposeful envelope openings such as vents/chimneys in their normal state;
- Type B seals purposeful openings and tests envelope airtightness;
- therefore `TYPE_A_N50 != TYPE_B_N50`.

For seven published traditional-brick examples:

- `n50 = 1.86 ... 8.28 1/h`
- flow exponent `n = 0.566 ... 0.689`
- calculated `n4 = 0.36 ... 1.52 1/h`

The paper uses **4 Pa** as the Hungarian annual-average natural pressure-difference basis and reports `R2=0.9819` for its measured-`n50` / calculated-`n4` relation.

P89 uses this as **Hungarian pressure-transfer/current-stock calibration only**.

It is not a paired retrofit-effect dataset and is not promoted to a national post-retrofit distribution.

## 2. Window-replacement paired field evidence

Source:
`SRC-B02-US-WINDOW-AIRTIGHTNESS-2026`

The 2026 field study contains:

- **20 occupied homes**
- **40 blower-door tests**
- before and after window replacement
- ACH50 / n50-type response

Admitted values:

- mean ACH50 reduction: **6.1%**
- maximum reported improvement: **19.3%**

The search-visible source text is internally inconsistent on the minimum response:

- highlights: **0.3%**
- abstract: **0.5%**

Therefore P89 deliberately creates **no positive minimum reduction floor**.

This is important: window replacement cannot be modelled as a guaranteed 10–20% airtightness improvement.

## 3. Whole-house retrofit paired evidence

Source:
`SRC-B02-UK-RFTF-AIRTIGHTNESS-2013`

The Retrofit for the Future report has comparable pre/post airtightness results for **87 properties**.

Source-native `q50` evidence:

- most frequent pre-retrofit result: approximately **8 m3/h/m2 @50Pa**
- most frequent post-retrofit result: approximately **4 m3/h/m2 @50Pa**
- below 5 before retrofit: **2 properties**
- below 5 after retrofit: **39 properties**
- below 1 after retrofit: **5 properties**

This is strong evidence that a whole-house retrofit can materially alter airtightness.

But:

`q50 != n50`

Without envelope geometry / volume crosswalk, these values cannot be inserted as `n50` or Hungarian `n_filt`.

## 4. Airtightness durability

Source:
`SRC-B02-UK-AIRTIGHTNESS-DURABILITY-2025`

Immediate pre/post evidence:

- all **4** cases with comparable pre/post tests became more airtight.

Ten-year revisit:

- **7/10** dwellings became less airtight;
- mean air-permeability increase: **0.52 m3/h/m2 @50Pa**
- observed change range: **-1.41 ... +2.58 m3/h/m2 @50Pa**

Therefore:

`IMMEDIATE POST-RETROFIT AIRTIGHTNESS != LIFETIME AIRTIGHTNESS`

A later lifecycle model must include commissioning/maintenance/degradation semantics.

## Executable P89 response

### Same-metric relative response

For a measured or scenario reduction fraction `r`:

`post_metric = baseline_metric * (1-r)`

The metric must remain unchanged:

- n50 → n50
- q50 → q50

No hidden q50↔n50 conversion is permitted.

### Hungarian pressure transfer

For explicit n50 and flow exponent `n`:

`n4 = n50 * (4/50)^n`

Using the PTE source-native exponent envelope:

`n = 0.566 ... 0.689`

the n50→n4 multiplier is approximately:

**0.1754806 ... 0.2394137**

This means an explicit **scenario/project** upper target could be propagated.

Example only:

- if a programme/project explicitly requires `n50 <= 3.0 1/h`
- P89 yields a 4 Pa upper-bound band of approximately
  **0.5264 ... 0.7182 1/h**

This is **not** a P89 recommendation and **not** a Hungarian national post-retrofit default.

No `n50=3` target is assigned by this slice.

## Blocker result

Previous:

`ACTION_CONDITIONED_POST_RETROFIT_INFILTRATION_REQUIRED`

P89 status:

`PARTIAL_RESOLVED_MEASURED_AIRTIGHTNESS_RESPONSE`

The response physics/evidence and Hungarian pressure-transfer route now exist.

Remaining exact blocker:

`POST_RETROFIT_ABSOLUTE_AIRTIGHTNESS_STATE_OR_PROGRAMME_TARGET_REQUIRED`

Why it remains:

A relative action response cannot produce an absolute post-state without at least one of:

1. a representative/calibrated Hungarian same-metric baseline + action assignment;
2. an explicit programme airtightness target;
3. project-level post-retrofit blower-door/commissioning evidence.

## Non-promotion boundaries

`Q50 != N50`

`PRESSURE-TEST AIRTIGHTNESS != NATURAL INFILTRATION`

`TYPE-A N50 INCLUDES INTENTIONAL OPENINGS`

`FOREIGN RETROFIT RESPONSE != HUNGARIAN POPULATION WEIGHT`

`WINDOW REPLACEMENT RESPONSE != WHOLE-HOUSE RESPONSE`

`RELATIVE RESPONSE REQUIRES SAME-METRIC BASELINE`

`IMMEDIATE POST-RETROFIT AIRTIGHTNESS != LONG-TERM DURABILITY`

`N4 PRESSURE TRANSFER != CURRENT-METHOD NFILT CLASSIFICATION`

## Readiness

- B02 remains **55%**
- B06 `PEAK_LOAD_EFFECT` remains **50%**
- `Q-B02-004` remains **OPEN_NARROWED**

P89 is a real evidence gain, but no readiness percentage is increased until the absolute national/programme post-state is defensibly bound.
