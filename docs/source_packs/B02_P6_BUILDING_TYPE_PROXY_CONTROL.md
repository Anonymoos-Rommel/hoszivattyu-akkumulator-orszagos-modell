# B02-P6 — KSH 2016 building-type proxy control boundary

**Status:** `HISTORICAL_NATIONAL_CONTROL_ADDED / Q-B02-002 REMAINS OPEN`

**Retrieved:** 2026-09-05

## Purpose

B02 currently has a reproducible 2022 WBL building-type proxy, but that proxy is still `ASS`: the 2022 `WBL011` / `WBL017` public flows do not expose a building-type dimension, so the P1-D transformation projects 2015 KSH settlement-type shares onto the 2022 occupied-dwelling universe.

B02-P6 asks a narrower question: is there a later official KSH source that can independently control the category semantics and national magnitude of that proxy without pretending to supply a 2022 WBL-joinable observation?

The canonical boundary is:

`2016 NATIONAL OBS CONTROL != 2022 SETTLEMENT-TYPE OBS != WBL SUBCELL JOINABILITY`

and therefore:

`CLOSE NATIONAL SHARE != CURRENT GRAIN AUTHORITY != PROXY PROMOTION`

## Sources

### 1. KSH Mikrocenzus 2016 questionnaire

Source ID: `SRC-B02-KSH-MICROCENSUS-TOPICS-2016`

Original source:
https://www.ksh.hu/docs/hun/xftp/idoszaki/mikrocenzus2016/mikrocenzus_2016_1.pdf

The source-native electronic housing questionnaire explicitly asks `Mi az épület típusa?` and separates:

- `családi ház, 1–3 lakásos lakóépület`;
- `négy- vagy többlakásos lakóépület`;
- holiday building;
- non-residential building.

This is an official semantic control for the `FAMILY_HOUSE` / `MULTI_DWELLING` split used by B02. It is not a 2022 dwelling-share observation and it is not a WBL join.

### 2. KSH 2.7.1 housing-structure indicator

Source ID: `SRC-B02-KSH-HOUSING-STRUCTURE-INDICATOR-2016`

Original source:
https://www.ksh.hu/thm/2/indi2_7_1.html

KSH defines the indicator as the share of occupied dwellings located in 1–3 dwelling buildings versus 4+ dwelling buildings. The published national values are:

| Reference year | 1–3 dwelling building | 4+ dwelling building | Evidence |
|---|---:|---:|---|
| 2015 | 60.1% | 39.9% | `OBS` source-native published indicator |
| 2016 | 62.0% | 38.0% | `OBS` source-native published indicator |

B02-P6 uses the **2016** row as the later independent national control. It does not invent a regional or settlement-type split that the indicator page does not publish.

### 3. Reuse authority

KSH states that content on `ksh.hu`, including tables, charts and infographics, is available under **CC BY 4.0**, with KSH attribution required:

https://www.ksh.hu/copyright

The provenance manifests therefore record `REPOSITORY_COPY_CLEARED_ATTRIBUTION_REQUIRED`. Exact source snapshots remain pending because the current connector cannot preserve the exact PDF/HTML bytes into the repository; no SHA-256 is fabricated and no base64 workaround is used.

## Comparison with the current P1-D proxy

The current 2022 WBL proxy remains:

- `FAMILY_HOUSE`: 2,423,136 / 4,008,541 = **60.4493255776%** — `ASS`;
- `MULTI_DWELLING`: 1,585,405 / 4,008,541 = **39.5506744224%** — `ASS`.

Against the 2016 national KSH observation:

- family-house diagnostic difference = **-1.5506744224 percentage points**;
- multi-dwelling diagnostic difference = **+1.5506744224 percentage points**.

These differences are **not `DER` truth upgrades**. Because one side of the comparison is an `ASS` 2022 proxy, the comparison itself remains `ASS` diagnostic context.

No arbitrary tolerance is introduced. B02-P6 therefore does not label the proxy `PASS`, `FAIL`, `VALIDATED`, `OBS`, or `DER` merely because the national shares are numerically close.

The machine-readable record is `registry/b02_building_type_proxy_control.csv`.

## What the 2016 evidence proves

It proves that:

1. KSH used the same basic 1–3 versus 4+ residential-building distinction in the 2016 Mikrocenzus questionnaire;
2. KSH published a 2016 national occupied-dwelling distribution of 62.0% / 38.0% for those categories;
3. a later official national observation is available as a magnitude control for the older 2015-based proxy.

## What it does not prove

It does **not** prove:

- the 2022 national building-type distribution;
- the 2022 distribution by `FV`, `MJV`, `EV`, or `K`;
- county × settlement-type building type;
- construction-period × building-type shares;
- wall, floor-area, comfort, heating-mode or fuel cross-distributions;
- any WBL011/WBL017 row-level or cell-level join;
- technical heat-pump eligibility;
- current emitter type, design temperature or hydraulic readiness.

A historical national control cannot be split into 2022 WBL cells by assumption and cannot upgrade an `ASS` proxy to `OBS`.

## Q-B02-002 effect

`Q-B02-002` remains **OPEN**.

The slice removes one ambiguity — the category split has later official KSH support and a later national magnitude control — but the canonical closure gate still requires a current/fresh administrative or statistical source at a grain that can actually support the chosen 2022 archetype linkage.

At minimum, closure requires one of:

1. a 2022/current source-native building-type distribution at the exact WBL-compatible settlement-type grain (or a finer grain that can be aggregated losslessly); or
2. an explicitly approved KSH/admin data acquisition that exposes a reproducible building-type × WBL-compatible key; or
3. a separately approved model contract that keeps the proxy `ASS` and propagates its uncertainty rather than pretending the join is observed.

## Other B02 gates

Unchanged:

- `Q-B02-001` — national technically suitable stock remains OPEN;
- `Q-B02-004` — emitter/design-temperature evidence remains OPEN;
- national technical eligible dwellings remain blank/Q;
- the 3,389,817 non-district-heated dwellings remain a DER physical screening reference only.

**No readiness uplift. B02 remains 55%.**
