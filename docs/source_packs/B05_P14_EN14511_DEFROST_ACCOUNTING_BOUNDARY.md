# B05-P14 - EN 14511 defrost accounting boundary

## Purpose

B05-P14 separates two questions that P6 previously kept together:

1. how defrost is accounted inside an EN 14511 operating-point measurement;
2. whether B05 has an evidence-backed weather-driven defrost runtime model.

P14 resolves the first for explicitly EN 14511-tagged performance points and
leaves the second open.

Core boundaries:

`EN 14511 POINT ACCOUNTING != WEATHER-DRIVEN DEFROST RUNTIME MODEL`

`DEFROST INCLUDED IF IT OCCURS IN THE RATING INTERVAL != DEFROST OCCURS AT EVERY RATING POINT`

`NO EXTRA UNIVERSAL PENALTY != ZERO REAL-WORLD DEFROST LOSS`

`MANUFACTURER DESIGN ALLOWANCE != HUNGARIAN RUNTIME OBSERVATION`

`EXPLICIT DEFROST-EXCLUDED CURVE != EN 14511 DEFROST-INCLUSIVE POINT`

## 1. EN 14511 accounting semantics

Current EN 14511-1:2022 defines effective power input as the average electrical
power input over the defined interval and explicitly includes any power input
for defrosting.

The same EN 14511 family defines heating capacity so that heat removed from the
indoor heat exchanger for defrosting is taken into account.

COP is defined as heating capacity divided by effective power input.

Therefore, for a performance point explicitly identified by its source as
EN 14511:

- defrost electrical consumption that occurs inside the rating interval belongs
  inside effective power input;
- heat removed from the indoor side for defrosting belongs inside the heating
  capacity accounting;
- a second generic additive/multiplicative defrost penalty would risk double
  counting.

This is a method boundary, not a claim that every EN 14511 rating point
necessarily experienced a defrost event during the actual test.

Canonical policy:

`EN14511_RATED_POINT -> NO_EXTRA_UNIVERSAL_DEFROST_PENALTY`.

## 2. Heat Pump KEYMARK corroboration

The current Heat Pump KEYMARK Annex A requires space-heating performance tests
at specified conditions according to EN 14511-2 and, for outdoor-air units,
requires the EN 14511-4 defrost test.

This corroborates that defrost is a defined part of the certification/test
framework rather than an unrelated post-processing factor.

P14 does not infer a product-specific defrost frequency from a passed KEYMARK
defrost test.

## 3. Current canonical point applicability

The current B05 performance-point table contains **36 canonical points** whose
`test_standard` field explicitly identifies EN 14511:

- Vaillant aroTHERM Split: 12;
- Vaillant aroTHERM plus: 5;
- STIEBEL HPA-O base map: 14;
- STIEBEL HPA-O P4 cold extension: 2;
- WAMAK AWK 35 EVI: 3.

For these points P14 qualifies the EN 14511 accounting boundary.

This does not rewrite their source values or evidence class.

## 4. Non-EN-14511 / source-specific cases

### NIBE P10 continuous capacity curves

The official NIBE S2125 source explicitly states that its continuous capacity
curves exclude defrost.

Therefore those curves are **not** promoted into the EN 14511 accounting
policy. Their defrost boundary remains source-specific:

`NIBE CONTINUOUS CAPACITY CURVE -> DEFROST EXCLUDED`.

### Tekno Point P11 and EC POWER P12

The current canonical P11/P12 source rows do not carry an explicit EN 14511
test-standard tag.

P14 therefore does not retroactively promote their point-level defrost
accounting boundary.

Their physical performance values remain usable under their existing source
contracts, but a separate extra defrost penalty is still not invented.

## 5. Vaillant UK design allowance is not a Hungarian runtime model

Current Vaillant aroTHERM Split product guidance states that local climate and
humidity can trigger defrost cycles and gives a 12-15% output-drop design
allowance as suitable for most parts of the UK.

P14 records this only as manufacturer design-context evidence.

It is forbidden to transfer that 12-15% value directly into the Hungarian
national model because:

- it is explicitly contextual to most parts of the UK;
- it is a design allowance, not a measured Hungarian hourly defrost series;
- it does not provide temperature/humidity/control-dependent event frequency.

## 6. Remaining runtime gap

The following remain Q:

- defrost event frequency by outdoor temperature and humidity;
- duration of defrost events;
- product-specific heat removed per event;
- product-specific extra electrical energy per event outside an already
  inclusive EN 14511 rating interval;
- interaction with auxiliary heater activation;
- Hungarian weather-weighted annual/peak defrost effect.

Therefore Q-B05-003 becomes:

`OPEN_NARROWED_TO_WEATHER_DRIVEN_RUNTIME_MODEL`.

## 7. Engine consequence

The current B05 engine already applies no hidden defrost penalty.

P14 confirms that this is the correct fail-closed behavior for EN 14511-tagged
points unless a separate evidence-backed runtime model is later introduced.

No engine energy formula is changed.

## 8. Readiness

B05 remains **64%**.

DEFROST remains **Q / 5%** because the runtime model is still missing.

P14 resolves semantic/accounting ambiguity without manufacturing a readiness
uplift.

## Sources

### SRC-B05-EN14511-1-DEFROST-2022

SIST / CEN, EN 14511-1:2022 public standard preview.

https://preview.sist.si/sist-preview/70163/c077a942ea724977b9d7f3dda0be98c7/SIST-EN-14511-1-2022.pdf

Role:
- effective power input includes any power input for defrosting;
- COP = heating capacity / effective power input;
- current EN 14511 definitions and terminology.

### SRC-B05-EN14511-1-DEFROST-2011

SIST / CEN, EN 14511-1:2011 public standard preview.

https://preview.sist.si/sist-preview/33312/068233ce44e141f1bc8238714ea5528e/SIST-EN-14511-1-2012.pdf

Role:
- heating-capacity definition explicitly states that heat removed from the
  indoor heat exchanger for defrosting is taken into account;
- effective power input includes defrost power.

### SRC-B05-HPKEYMARK-ANNEXA-2026

Heat Pump KEYMARK, Annex A KEYMARK Requirements V2.

https://www.heatpumpkeymark.com/fileadmin/user_upload/documents/2HPK_Annex_A_KEYMARK_Requirements_V2.pdf

Role:
- EN 14511-2 performance-test framework;
- EN 14511-4 defrost test required for outdoor-air units.

### SRC-B05-VAILLANT-SPLIT-DEFROST-DESIGN-2026

Vaillant current aroTHERM Split product guidance.

https://professional.vaillant.co.uk/for-installers/products/arotherm-split-heat-pump-7kw-145985.html

Role:
- manufacturer design-context evidence that defrost depends on colder
  temperature/humidity/local climate;
- UK-specific 12-15% design allowance is recorded as non-transferable context,
  not Hungarian runtime evidence.
