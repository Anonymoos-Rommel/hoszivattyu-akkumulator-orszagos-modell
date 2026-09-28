# B05-P57 — FCC06 direct runtime and water-content lineage

**Date:** 2026-09-28  
**Canonical parent main:** `099b595344e0a955d27a446b3a7ef943b69be0d4`

## Purpose

P56 left two coupled FCC06 residuals:

1. `EXACT_FCC06_WATER_MASS_OR_SOURCE_REPORTED_SCALAR_RESPONSE_TIME_REQUIRED`;
2. `STATE_DEPENDENT_FCU_RESPONSE_TO_HEM_TAU_OUT_MAPPING_OR_DIRECT_RUNTIME_PATH_REQUIRED`.

P57 resolves the second fork by implementing the peer-reviewed FCC06
water-side ODE directly. It simultaneously audits the manufacturer-catalogue
lineage for the water-mass input.

Core boundaries:

```
DIRECT FCC06 PHYSICAL RUNTIME != HEM TAU_OUT MAPPING
CROSS-REVISION 1.7 L != EXACT 2010 STUDY WATER MASS
WATER CONTENT [L] != WATER MASS [kg] WITHOUT DENSITY
0.29 L FOUR-PIPE HEATING COIL != TWO-PIPE STUDY COIL
```

## 1. Cited catalogue identity

The 2019 FCC06 paper states that `m_w`, the mass of water inside the FCU, is
available from the manufacturer's catalogue.

Its exact reference [44] is:

- Trane, *UniTrane fan coil units*;
- document `UNT-PRC006-E4`;
- 2010.

A public Yumpu mirror independently exposes the exact document title, the
size list including 06, the copyright line `© Trane 2010 UNT-PRC006-E4`,
and an index showing **Table 3 — General data** on page 16.

The currently indexed text layer does not expose the numeric cells of that
page. P57 therefore does not invent the exact cited-edition water content.

## 2. Cross-revision manufacturer evidence

A separate Trane product guide, `PROD-PRC014-E4`, exposes UniTrane
FCC/FCK/FVC general data with size 06.

For the size-06 branch it reports:

- 2-pipe / 3-row coil water content: **1.7 L**;
- separate 4-pipe / 1-row heating-coil water content: **0.29 L**.

The same guide identifies the high-speed size-06 airflow as 762 m3/h and
publishes the 2-pipe/3-row versus 4-pipe/1-row topology split.

The FCC06 study explicitly uses a **two-pipe system for seasonal heating and
cooling**. Therefore the 0.29 L four-pipe heating-coil branch is not the study
topology.

P57 admits 1.7 L only as:

`CROSS_REVISION_FCC06_2PIPE_3ROW_WATER_CONTENT_CANDIDATE`.

It is strong corroborating product evidence, not the exact 2010 study-unit
mass.

## 3. Volume is not mass

The paper's state equation uses `m_w [kg]`.

The product guide exposes water content in litres.

P57 therefore freezes:

`1.7 L != 1.7 kg`

unless an explicit working-medium density is supplied.

This matters because the paper itself notes that hydronic systems may use
softened tap water or water-glycol mixtures and treats fluid thermal properties
as an empirical identification problem.

## 4. Source-specific heat capacity

The paper identifies working-medium heat capacity experimentally.

Figure 11 reports a mean identified value of:

**4504 J/(kg K)**

and separately shows **4180 J/(kg K)** as the nominal clear-water value used
by the calorimeter.

P57 therefore admits 4504 J/(kg K) only for source-system reproduction.

It does not redefine a universal water heat capacity.

## 5. Direct state-dependent runtime

P56 already implemented the source's heating heat-transfer surface
`U_o(x,q_w)`.

P57 now implements the full constant-input water-state step directly from the
published equation:

`m_w c_w dT_out/dt = q_w c_w (T_in-T_out) - U_o(0.5(T_in+T_out)-T_a)`.

Writing

`dT_out/dt = -a T_out + b`

gives:

`a = q_w/m_w + U_o/(2 m_w c_w)`

and P57 uses the analytical update:

`T_out(t+dt) = T_ss + (T_out(t)-T_ss) exp(-a dt)`.

The transmitted thermal power is then evaluated from the model's mean-water
temperature approximation.

This path requires:

- explicit fan state;
- water mass flow;
- exact study-compatible water mass;
- medium heat capacity;
- inlet/zone/outlet temperatures;
- timestep.

It does **not** require one HEM `tau_out`.

Therefore:

`STATE_DEPENDENT_FCU_RESPONSE_TO_HEM_TAU_OUT_MAPPING_OR_DIRECT_RUNTIME_PATH_REQUIRED`

->
`RESOLVED_BY_DIRECT_STATE_DEPENDENT_FCC06_RUNTIME_PATH`.

The existing HEM scalar method remains available as a separate POL/default
branch. P57 does not claim that the physical water-state time constant equals
the HEM emitter-class scalar.

## 6. Remaining FCC06 blocker

The remaining numeric exact-system blocker is now:

`EXACT_CITED_EDITION_FCC06_WATER_CONTENT_OR_DIRECT_WATER_MASS_REQUIRED`

plus, if source-native volume is used:

`EXPLICIT_MEDIUM_DENSITY_REQUIRED_IF_VOLUME_IS_USED`.

A future exact page-16 recovery from `UNT-PRC006-E4`, or an authoritative
direct FCC06 water-mass record, can close the first part.

## 7. Q-B05-004

Independent residuals remain:

- `EXACT_SOURCE_NATIVE_A_MINUS15_W50_2D_OPERATING_OR_PERFORMANCE_RECORD_REQUIRED`;
- `EXACT_VDE_328782_TL2_1_REPORT_CONTENT_OR_SOURCE_NATIVE_TRANSIENT_EXCERPT_REQUIRED`;
- `EXACT_PUZ_WM50_TESTED_SPECIMEN_BINDING_AND_SZU_REPORT_OR_SOURCE_NATIVE_TRANSIENT_RECORD_REQUIRED`;
- exact FCC06 water-mass lineage above.

Q-B05-004 remains OPEN / E2 / MODEL_CONTINUE.

## 8. Readiness

No mechanical uplift:

- PART_LOAD_MODULATION = **45%**
- B05 = **64%**

The direct runtime architecture advances materially, but the exact numeric
water-mass input remains fail-closed.

## Public sources

- FCC06 peer-reviewed author manuscript:
  https://www.lares.fer.hr/_news/86201/CONPRA_4100.pdf
- Exact cited Trane catalogue identity mirror:
  https://www.yumpu.com/en/document/view/8519587/unitranetm-fan-coil-units
- Cross-revision Trane product-guide public mirror:
  https://www.scribd.com/doc/159113259/Trane-Product-Guide

No copyrighted catalogue or article PDF is stored in the public repository.
