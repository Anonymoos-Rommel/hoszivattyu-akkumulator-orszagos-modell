# B02-P21 — Public KSH calibrated archetype linkage

**Status:** `IMPLEMENTED / REPRODUCIBLE PUBLIC-DATA MODEL / APPROVED / QUALIFIED`

**Base:** `e89209507f5dbbe57c4f9e37d8b62c0363bee77b`

**Audit / implementation date:** 2026-09-06

**Joseph approval:** 2026-09-06 09:23 Europe/Budapest

## Purpose

P15 already materializes the complete 2022 occupied WBL011 full joint. P1-D already provides the canonical reproducible settlement-type building-type proxy. P17 already records the strongest public KSH primary-energy evidence.

P21 does **not** create a second building-type proxy and does not attempt to replay the unpublished KSH random forest. It binds the existing canonical public inputs into one repository-reproducible calibrated linkage at the exact P15 WBL cell grain.

Canonical boundaries:

`PUBLIC KSH CALIBRATION != DIRECT OBSERVATION`

`CALIBRATED WBL LINK != KSH INTERNAL DWELLING-LEVEL RANDOM-FOREST OUTPUT`

`MODELLED BUILDING-TYPE ASSOCIATION != OBSERVED BUILDING TYPE`

`AGE-SHAPED CENTRAL != FLAT STRUCTURAL SENSITIVITY`

`STRUCTURAL SCENARIO ENVELOPE != STATISTICAL CONFIDENCE INTERVAL`

## 1. Reused canonical inputs

P21 consumes existing committed sources and outputs only:

1. `data/processed/b02/ksh_wbl_joint_cells_2022.csv`
   - projection: `WBL011_FULL_STOCK_JOINT`;
   - rows: **116 452**;
   - occupied dwellings: **4 008 541**;
   - source evidence: `OBS`.

2. `data/processed/b02/ksh_building_type_proxy_2022.csv`
   - existing P1-D settlement-type proxy;
   - output evidence: `ASS`;
   - 2022 occupied family-house target: **2 423 136**;
   - 2022 occupied multi-dwelling target: **1 585 405**;
   - exact settlement margins:
     - `FV`: 144 423 / 655 915;
     - `MJV`: 307 566 / 559 563;
     - `EV`: 888 698 / 354 531;
     - `K`: 1 082 449 / 15 396.

3. `data/processed/b02/ksh_energy_archetype_benchmarks_2022.csv`
   - public KSH 2022 ÉKM building-type × construction-period means and published-bin modelled dwelling counts;
   - output evidence: `MODELLED`;
   - source: `SRC-B02-KSH-ENERGY-2025`.

4. P6 national control:
   - `SRC-B02-KSH-HOUSING-STRUCTURE-INDICATOR-2016`;
   - occupied 1–3 dwelling building share: 62.0%;
   - occupied 4+ dwelling building share: 38.0%;
   - used as a representativeness / validation diagnostic only, not as a 2022 WBL assignment.

The already dispatched KSH direct aggregate request remains a possible future evidence upgrade. P21 is not dependent on a response.

## 2. Building-type central linkage

The existing P1-D proxy gives the occupied 2022 building-type **margins by settlement type**, but does not provide WBL subcell structure.

P21 obtains the within-margin construction-period shape from the already public KSH 2022 energy publication. For every WBL construction-period band `a`:

`age_odds_ratio(a) = [F_KSH(a) / M_KSH(a)] / [F_KSH(all) / M_KSH(all)]`

where `F_KSH` and `M_KSH` are the KSH published modelled dwelling counts in the energy-distribution bins.

The KSH publication has two post-2010 periods (`2011–2015`, `2016–2022`) while WBL011 has `Y_GE2011`. P21 combines those two source rows by their published modelled dwelling counts. Earlier periods map one-to-one.

For settlement type `s`, one positive odds scale `lambda_s` is solved by deterministic bisection so that:

`p_family(i) = lambda_s * age_odds_ratio(a_i) / [1 + lambda_s * age_odds_ratio(a_i)]`

and exactly:

`SUM_i in s [dwelling_count(i) * p_family(i)] = P1D_family_target(s)`

Thus the central model changes the within-settlement age profile while preserving every existing P1-D occupied settlement margin.

No wall, floor-area, comfort, heating-mode or heating-fuel association is invented. Those WBL dimensions remain part of the exact cell key but receive no unsupported building-type coefficient.

## 3. Structural uncertainty / independence control

The explicit sensitivity scenario is:

`FLAT_WITHIN_SETTLEMENT`

For every cell in settlement type `s`:

`p_family_flat(i) = P1D_family_target(s) / P1D_occupied_total(s)`

This scenario preserves exactly the same settlement margins but removes the current KSH construction-period association.

For every WBL cell P21 publishes in-memory / regenerable values for:

- central family probability;
- flat family probability;
- minimum and maximum of the two;
- expected central family / multi dwelling counts.

This is an explicit structural sensitivity controlling the main otherwise-hidden independence assumption. It is **not** labelled as a probabilistic confidence interval.

The remaining conditional independence across wall, area, comfort, heating mode and fuel is explicit. No cell-level claim may reinterpret that lack of variation as source evidence.

## 4. Primary-energy WBL linkage

P21 does not reproduce the KSH random forest. It uses only the public 2022 KSH building-type × construction-period ÉKM means already materialized in the repository.

For each WBL period `a` the public means are `E_F(a)` and `E_M(a)`. The cell expected primary-energy value is:

`E_central(i) = p_family(i) * E_F(a_i) + [1 - p_family(i)] * E_M(a_i)`

and the structural sensitivity is:

`E_flat(i) = p_family_flat(i) * E_F(a_i) + [1 - p_family_flat(i)] * E_M(a_i)`

The per-cell propagated structural envelope is:

`E_low(i) = min(E_central(i), E_flat(i))`

`E_high(i) = max(E_central(i), E_flat(i))`

For `Y_GE2011`, family and multi energy means are separately count-weighted from the KSH `2011–2015` and `2016–2022` source rows before mixing building types.

Output semantics remain:

- building type: `ASS`;
- primary energy: `MODELLED`.

No P21 output may be promoted to `OBS` or `DER`.

## 5. Validation and representativeness controls

### Building type

P21 retains the already audited P6 external national magnitude control:

- KSH 2016 occupied family / multi: **62.0% / 38.0%** (`OBS`);
- P1-D 2022 occupied proxy: **60.4493% / 39.5507%** (`ASS`);
- family-share delta: **-1.5507 percentage points**.

No arbitrary pass/fail tolerance is introduced. This is a bounded diagnostic, not direct 2022 validation.

The executable P21 model additionally requires exact zero-residual reconciliation to each P1-D settlement margin (floating tolerance only for numerical bisection).

### Primary energy

The KSH methodology already supplies model-fit / cross-validation and territorial validation diagnostics for the underlying public energy model. P21 consumes only published grouped means and does not increase their evidence status.

## 6. Executable implementation

Canonical implementation:

`modules/B02/calibrated_archetype_linkage.py`

Default inputs are all committed repository files; no network access is required.

The module can deterministically materialize:

- `data/processed/b02/b02_calibrated_archetype_linkage_2022.csv`;
- `data/processed/b02/b02_calibrated_archetype_linkage_summary_2022.json`.

The generated cell CSV is not required to be committed for P21 admission because the exact committed `cell_id` binding, source inputs and deterministic model are repository-reproducible. P21's regression test executes the full **116 452-row / 4 008 541-dwelling** binding from the committed inputs.

## 7. P12 model admission

P21 registers two current models:

- `B02-P21-PUBLIC-KSH-BUILDING-TYPE-LINKAGE`;
- `B02-P21-PUBLIC-KSH-PRIMARY-ENERGY-LINKAGE`.

For both models the repository provides:

- calibration sources;
- explicit 2022 target/reference period;
- exact WBL full-joint target binding;
- representativeness diagnostics;
- validation metrics;
- exact marginal reconciliation;
- explicit structural uncertainty method;
- mandatory uncertainty propagation into primary energy;
- explicit control of the age-association versus flat-independence assumption;
- correct `ASS` / `MODELLED` output semantics.

Joseph explicitly approved both calibrated models on **2026-09-06 09:23 Europe/Budapest**.

The P12 state is therefore:

`APPROVED / JOSEPH / QUALIFIED`

The former `NO_JOSEPH_APPROVAL` blocker is closed. Approval changes model-admission authority only; it does not change the evidence class of the generated values.

## 8. Current B02 effect after approval

After explicit approval:

- calibrated building-type linkage: **QUALIFIED**;
- calibrated primary-energy linkage: **QUALIFIED**;
- `CURRENT_STOCK_ARCHETYPE_ASSIGNMENT`: **QUALIFIED**;
- `NO_CURRENT_BUILDING_TYPE_LINK_AUTHORITY`: **CLOSED by approved calibrated-model path**;
- `NO_PRIMARY_ENERGY_TO_WBL_LINK_AUTHORITY`: **CLOSED by approved calibrated-model path**;
- technical-readiness archetype: `Q` only because current heat-emitter and current design-temperature evidence are still missing;
- `Q-B02-001`: OPEN;
- `Q-B02-002`: OPEN;
- `Q-B02-004`: OPEN;
- national technical/final eligible count: blank / `Q`;
- B02 readiness: **55%**; no arbitrary percentage uplift is minted from model approval alone;
- KSH direct building-type request: `REQUEST_SENT / AWAITING_RESPONSE`;
- OÉNY readiness request: `REQUEST_SENT / AWAITING_RESPONSE`.

The approved model therefore makes the current-stock archetype executable and admissible while preserving the remaining technical-readiness evidence gap exactly where it belongs.
