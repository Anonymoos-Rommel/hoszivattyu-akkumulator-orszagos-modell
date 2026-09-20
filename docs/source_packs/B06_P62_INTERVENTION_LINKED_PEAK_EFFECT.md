# B06-P62 — intervention-linked Hungarian annual + design-peak calibration

**State:** `Q-B06-011 RESOLVED / ONE BOUNDED HUNGARIAN DER CALIBRATION / NO NATIONAL EFFECT SURFACE`

**Canonical base:** `f60e751ba829065a47a602172364eb46da181e16`

**Implementation date:** 2026-09-20

## 1. Purpose

Q-B06-011 required an intervention-linked case with **separate annual and
design-peak before/after evidence**, explicit design conditions, intervention
scope and DHW boundary.

P62 resolves that source/semantics blocker with one real Hungarian residential
project and makes the evidence contract executable.

Core boundaries:

`ANNUAL REDUCTION != PEAK REDUCTION`

`ANNUAL PERCENTAGE != PEAK PERCENTAGE`

`PLANNED DESIGN DER != REALIZED COMPLETION OBS`

`SAME BUILDING + SAME METHOD + SAME DESIGN CONDITIONS + LINKED INTERVENTION = ADMISSIBLE`

## 2. Building and project

The bounded case is the same real Hungarian building already used by P61:

- Budapest XVI., Zalavár utca 4.;
- 19 dwellings;
- heated floor area: 1419.63 m2;
- heated volume: 4174.5 m3;
- ZFR-TH/15 project;
- KESZ ZBR EH 09-3 calculation family.

The project scope is independently documented and includes:

- facade insulation;
- roof insulation;
- basement-ceiling insulation;
- window replacement;
- air-inlet installation.

Scope source:
`SRC-B06-HU-ZALAVAR-SCOPE-2015`

This proves the intervention package identity. It is not a completion record.

## 3. Pre-retrofit state

Source:
`SRC-B06-HU-ZALAVAR-ZBR-PRE-2015`

The public calculation explicitly identifies the **existing / pre-renovation
state** and reports:

- annual net space-heating demand: **207172 kWh/a**;
- estimated design heat demand: **132.35 kW**;
- design indoor temperature: **20 C**;
- design outdoor temperature: **-13 C**;
- heated floor area: **1419.63 m2**;
- heated volume: **4174.5 m3**;
- winter air-change rate: **1.26 1/h**;
- specific transmission heat-loss coefficient: **0.52 W/m3K**.

Both annual and peak values are engineering calculation outputs, therefore
`DER`.

## 4. Planned post-retrofit state

Source:
`SRC-B06-HU-ZALAVAR-ZBR-POST-2015`

The paired public calculation explicitly identifies the
**planned post-renovation state** and uses the same building and calculation
method. It reports:

- annual net space-heating demand: **36687 kWh/a**;
- estimated design heat demand: **46.47 kW**;
- design indoor temperature: **20 C**;
- design outdoor temperature: **-13 C**;
- heated floor area: **1419.63 m2**;
- heated volume: **4174.5 m3**;
- winter air-change rate: **0.5 1/h**;
- post specific heat-loss value: **0.08 W/m3K**.

The document keeps space heating and domestic hot water as separate calculation
sections, so the P62 space-heating comparison does not import DHW into the peak
effect.

The post state is `POST_RETROFIT_PLANNED / PLANNED_DESIGN`, hence `DER`.
It is **not** claimed as realized `OBS` completion.

## 5. Independent annual and peak effects

Source-native annual pair:

`207172 -> 36687 kWh/a`

Derived annual reduction:

`170485 kWh/a`

`annual_reduction_fraction = 0.8229152588187593`

Source-native design-peak pair:

`132.35 -> 46.47 kW`

Derived peak reduction:

`85.88 kW`

`peak_reduction_fraction = 0.6488855307895731`

Therefore:

`82.29% annual reduction != 64.89% peak reduction`

This is direct empirical support for B06's long-standing rule that annual and
peak effects are separate dimensions.

## 6. Executable P62 gate

`modules/B06/peak_effect_gate.py` requires:

- same record;
- explicit intervention ID;
- distinct before/after phases;
- same calculation method;
- matching design indoor/outdoor temperatures;
- independent annual before/after values;
- independent peak before/after values;
- before/after source references;
- documented intervention scope;
- explicit DHW/space-heating boundary;
- reproducible repository binding.

It prohibits:

- deriving peak reduction from annual reduction;
- using installed equipment capacity as peak;
- cross-building before/after pairing.

For real `OBS/DER` intervention effects, `modules/B06/engine.py` now requires
this linked evidence and verifies that supplied annual and peak fractions exactly
match the P62 calculation.

## 7. P61 source-precedence correction

P61 originally materialized the pre annual total by multiplying rounded
source values:

`145.9 kWh/m2a × 1419.6 m2 = 207119.64 kWh/a`

P62 found the direct source-native annual total in the same calculation:

`QF,1 = 207172 kWh/a`

The source-native value is now canonical. Rounded secondary fields may not
override a direct source-native total.

## 8. Search trail retained

Public searches were also performed for a **realized post-completion design
peak** for the same building. No exact public source-native realized post
design-peak record was identified.

That negative result does not block Q-B06-011 because the question asks for
intervention-linked calibration of annual and design-peak effects, and the
same-method PRE + planned-POST engineering pair satisfies that calibration
purpose.

However:

`PLANNED POST DER != REALIZED COMPLETION OBS`

Therefore P62 does not close Q-B06-009 and does not promote the building to S1
on completion evidence.

## 9. Programme effect

P62 resolves **Q-B06-011**.

It does **not** create:

- a national retrofit peak-effect factor;
- an archetype-wide annual/peak ratio;
- a realized savings claim for Zalavár u. 4.;
- automatic S1 completion;
- a generic intervention surface for all Hungarian buildings.

Q-B06-007 remains open because a building-type/state-dependent transferable
effect surface needs more than one bounded case.
