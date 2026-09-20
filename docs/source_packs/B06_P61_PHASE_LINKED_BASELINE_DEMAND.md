# B06-P61 — phase-linked Hungarian baseline annual + design-peak demand

**State:** `Q-B06-006 SOURCE/SEMANTICS RESOLVED / NATIONAL COVERAGE NOT CLAIMED`

**Canonical base:** `fdd3e295298616ecc910f0a5ef84f3874d1bd408`

**Implementation date:** 2026-09-20

## 1. Purpose

Q-B06-006 required a real baseline in which annual space-heating demand and
design peak heat load are attached to the same building/archetype record, the
same date/phase and an auditable evidence chain.

P61 establishes such a Hungarian residential record and adds an executable gate
for future records.

Core boundary:

`ANNUAL ENERGY != DESIGN PEAK`

`INSTALLED HEAT-SOURCE CAPACITY != DESIGN PEAK`

`ANNUAL ENERGY / FULL-LOAD-HOURS != DESIGN PEAK`

`SAME BUILDING + SAME PRE-INTERVENTION PHASE + INDEPENDENT EVIDENCE = ADMISSIBLE`

## 2. Bounded Hungarian paired record

Public source:

- **Hiteles Energetikai Tanúsítvány HET-00259140**
- Zalavár u. 4 társasház, Budapest XVI.
- source PDF: https://www.osszefog.hu/doc/6_melleklet_zalavar_u_4_hiteles_energetikai_tanusitvany.pdf
- certificate calculation date: 2015-04-21
- ZBR calculation explicitly states: **Felújítás előtti állapot**

The public document reports for the same pre-retrofit state:

- residential multi-family building;
- 19 dwellings;
- heated floor area: **1419.6 m2**;
- heated volume: **4174.5 m3**;
- design indoor temperature: **20.0 C**;
- design outdoor temperature: **-13.0 C**;
- winter air-change rate: **1.26 1/h**;
- specific transmission heat-loss coefficient: **0.52 W/m3K**;
- net annual heating demand: **qF = 145.9 kWh/m2a**;
- estimated heating design demand: **132.35 kW**.

The annual total stored by P61 is a transparent exact derivation:

`145.9 kWh/m2a × 1419.6 m2 = 207119.64 kWh/a`

The design peak is not derived from that annual value. It is copied as the
source-native **132.35 kW** result.

## 3. Evidence classification

Both annual and peak values are `DER`, not `OBS`.

Reason:

- they are engineering/certificate calculation outputs;
- the source is a real Hungarian residential building;
- the source itself labels the phase as pre-renovation;
- the calculation inputs and method context are exposed;
- no measured-meter interpretation is invented.

The record is therefore a **bounded calibration / authority precedent**, not a
national housing-stock estimate.

## 4. Current Hungarian annual-demand route

Current Hungarian energy-efficiency rules continue to recognise the building's
annual heating demand as a record-level quantity that may be supported by a
Hiteles Energetikai Tanúsítvány.

Current legal authority:

- 18/2025. (VII. 31.) EM rendelet, consolidated text:
  https://njt.hu/jogszabaly/2025-18-20-8Y
- current calculation method authority remains the 9/2023. (V. 25.) ÉKM
  building-energy method already registered in B06.

P61 does **not** claim that a current HET necessarily contains a source-native
design-peak kW field. If the current annual HET and peak calculation are separate
artifacts, they may only be joined when record ID and phase linkage are explicit.

## 5. Executable baseline gate

`modules/B06/baseline_demand_gate.py` admits a baseline only when:

- annual and peak evidence are OBS or DER;
- both refer to exactly the same record;
- both refer to exactly the same phase;
- both carry explicit source references;
- annual value is positive and method-bound;
- peak value is positive and method-bound;
- physical peak derivation has explicit design indoor/outdoor temperatures;
- repository binding is reproducible.

Explicitly prohibited:

- annual kWh -> peak kW inference;
- installed boiler/heat-pump capacity as design peak;
- full-load-hours proxy.

## 6. Search trail / reserve findings

A 2023 public Hungarian residential Auricon HET was also inspected. It contains
a source-native annual net heating value (`qf`) and detailed geometry/system
inputs, but the inspected artifact did not expose a direct source-native
design-peak kW field. Because that public document also contains personal
identifiers, P61 does not register or reproduce it in the public repository.

This negative/partial result is retained here so future research does not repeat
the same path.

## 7. Programme effect

P61 resolves Q-B06-006 as a **source and gate-contract question**:

- a real Hungarian same-record/same-phase annual+peak pair exists;
- a fail-closed reusable admission contract now exists.

P61 does **not** create:

- a national annual-demand distribution;
- a national design-peak distribution;
- an archetype-wide annual/peak ratio;
- a full-load-hours rule;
- a current-stock uplift from the 2015 building;
- any automatic B05 sizing for other dwellings.

Every new household/archetype baseline remains independently evidence-bound.
