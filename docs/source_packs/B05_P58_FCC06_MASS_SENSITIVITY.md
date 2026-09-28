# B05-P58 — FCC06 cross-revision water-content stability and normalized mass sensitivity

**Date:** 2026-09-28  
**Canonical parent main:** `366b3823ee2fbc32c47d7b569e5154855e8ab93b`

## Purpose

P57 made the exact FCC06 direct physical runtime executable but left the
numeric transient path fail-closed on study-compatible in-coil water mass.

P58 asks two narrower questions:

1. how strong is the public manufacturer evidence that the FCC06 2-pipe /
   3-row water content is 1.7 L?
2. exactly which parts of the FCC06 runtime are actually blocked by unknown
   `m_w`?

The answer is materially narrower than the P57 blocker.

## 1. Cross-revision manufacturer stability

A 2004 Trane general catalogue, `PROD-PRC011-E4`, identifies the
UniTrane FCC-FCK-FVC family and the FCC size series including size 06.
Its general-data layer publishes **1.7 L** for the size-06 2-pipe /
3-row water-content branch.

A separate 2006 Trane product guide, `PROD-PRC014-E4`, independently
publishes the same **1.7 L** value for size 06 / 2-pipe / 3-row.

The exact catalogue cited by the FCC06 experiment remains:

`UNT-PRC006-E4` — Trane, 2010.

Its public mirror confirms:

- exact document code;
- Trane 2010 identity;
- FCC size 06 in scope;
- `Table 3 - General data` on page 16.

The current indexed text surface still does not expose the page-16 numeric
cell.

Therefore P58 admits:

`CROSS_REVISION_FCC06_2PIPE_3ROW_WATER_CONTENT = 1.7 L`

for **sensitivity analysis only**.

It does not admit:

`EXACT_2010_STUDY_WATER_CONTENT = 1.7 L`.

## 2. Why the repeated value matters

P57 had one cross-revision 1.7 L observation.

P58 now has two manufacturer revisions:

- 2004 -> 1.7 L;
- 2006 -> 1.7 L.

This establishes pre-2010 revision stability for the exact product size and
coil topology.

It is stronger than a single later catalogue value, but still not a substitute
for source-native recovery of the 2010 cell.

Core rule:

`REPEATED_MANUFACTURER_VALUE != EXACT_STUDY_EDITION_VALUE`.

## 3. Steady-state mass cancellation

The P56/P57 source ODE is:

`m_w c_w dT_out/dt = q_w c_w(T_in-T_out) - U_o(0.5(T_in+T_out)-T_a)`.

At steady state, `dT_out/dt = 0`.

After division, the entire equation contains no `m_w`.

Therefore the exact FCC06 steady-state outlet temperature and transmitted
power under this source model do **not** require the in-coil water mass.

P58 makes that path executable explicitly.

This is not an approximation. It is an algebraic property of the published
model.

Thus:

`EXACT_M_W_REQUIRED_FOR_FCC06_STEADY_STATE`

is false within the source ODE.

## 4. Transient mass dependence

For the first-order water state:

`tau = m_w / (q_w + U_o/(2 c_w))`.

Therefore:

`tau / m_w = 1 / (q_w + U_o/(2 c_w))`.

P58 implements `tau/m_w` directly.

This means the missing mass uncertainty is now structurally isolated:

- steady-state output: independent of `m_w`;
- transient time constant: linear in `m_w`;
- normalized transient sensitivity: executable without exact `m_w`.

The missing exact mass is therefore no longer a generic FCC06 runtime blocker.

It is specifically an **OBS transient-validation input blocker**.

## 5. Cross-revision sensitivity path

P58 permits the repeated 1.7 L value to enter only an explicit:

`ASS / CROSS_REVISION_FCC06_WATER_MASS_SENSITIVITY`

branch.

Even there, litres are not kilograms.

The caller must provide explicit working-medium density.

The sensitivity result cannot be relabeled OBS and cannot close the exact
2010 study-mass residual.

## 6. Residual transition

P57 residual:

`EXACT_CITED_EDITION_FCC06_WATER_CONTENT_OR_DIRECT_WATER_MASS_REQUIRED`

is narrowed semantically to:

`EXACT_CITED_EDITION_FCC06_WATER_CONTENT_OR_DIRECT_WATER_MASS_REQUIRED_FOR_OBS_TRANSIENT_VALIDATION`.

The density residual remains conditional:

`EXPLICIT_MEDIUM_DENSITY_REQUIRED_IF_VOLUME_IS_USED`.

The important change is that these no longer block:

- FCC06 steady-state direct physics;
- normalized transient sensitivity;
- explicit ASS sensitivity scenarios.

They still block exact source-bound transient validation.

## 7. Q-B05-004

Independent residuals remain unchanged:

- Mitsubishi A-15/W50 exact two-dimensional authority;
- Dimplex exact VDE transient content;
- Mitsubishi tested-specimen/SZU transient record.

Q-B05-004 remains OPEN / E2 / MODEL_CONTINUE.

## 8. Readiness

No mechanical uplift:

- PART_LOAD_MODULATION = **45%**
- B05 = **64%**

P58 materially reduces blocker scope but does not provide the missing exact
study-edition mass or the Mitsubishi/Dimplex product transient records.

## Public sources

- 2004 Trane general catalogue `PROD-PRC011-E4` public mirror:
  https://pdfcoffee.com/tong-hop-trane-pdf-pdf-free.html
- 2006 Trane product guide `PROD-PRC014-E4` public mirror:
  https://www.scribd.com/doc/159113259/Trane-Product-Guide
- Exact study-cited 2010 Trane catalogue identity:
  https://www.yumpu.com/en/document/view/8519587/unitranetm-fan-coil-units
- FCC06 peer-reviewed dynamic model:
  https://doi.org/10.1016/j.conengprac.2019.07.018

No copyrighted catalogue or article bytes are committed.
