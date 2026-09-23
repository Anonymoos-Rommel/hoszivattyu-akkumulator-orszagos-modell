# B02-P99 — FRESH MULTI-SOURCE ENVELOPE-ACTION EVIDENCE

## Goal

Audit and materially narrow:

`FRESH_MULTI_SOURCE_ENVELOPE_ACTION_EVIDENCE_REQUIRED`

without converting unrelated renovation statistics into the future
`AIR_TO_WATER_HP_ONLY` versus
`REFERENCE_ENVELOPE_RETROFIT_PLUS_AWHP` programme split.

Base:

`f4335b456f1e2504b55cb35fe8c21f350bceb01f`

## P81 rule preserved

P81 already established:

`FULL HOUSEHOLD ACTION IDENTIFICATION != REQUIRED`

and:

`REPRESENTATIVE PUBLIC EVIDENCE -> MULTI-SOURCE CALIBRATION -> BOUNDED POPULATION INFERENCE -> UNCERTAINTY PROPAGATION`

It also requires semantic compatibility, source independence and an explicit
freshness floor.

P99 uses a freshness floor of **2021**.

## 1. Binding national direct evidence — TARKI-REKK 2022

Source:

`SRC-B02-HU-REKK-TARKI-ENVELOPE-2022`

The REKK study documents that TARKI performed a **1000-person in-person
household survey in October-November 2022**. In the building-model appendix the
final database is described as weighted using KSH data and representative along
region and building-type dimensions.

The source explicitly states that the renovation statistics used in the model
were corrected weighted averages by building type.

### 2022 current stock calibration

The source comparison table reports for TARKI-REKK 2022:

- insulated facade: **35.0%**;
- insulated attic/ceiling: **29.7%**;
- window replacement: **52.7%**.

These are survey/state concepts.

They are **not**:

- current legal U-value compliance;
- proof of reference-retrofit quality;
- future programme action assignments.

Boundary:

`SURVEY INSULATED/REPLACED STATE != REFERENCE U COMPLIANCE`.

The report also notes an average self-reported insulation thickness of about
**9.6 cm**, while explicitly warning that resident-reported thickness has
reliability limitations. P99 does not convert this average into a U-value.

### Previous 12-month realized action shares

Table 40 reports the following actions in the previous 12 months relative to
October 2022:

- facade insulation: **3.7%**;
- roof insulation: **2.4%**;
- attic-floor insulation: **4.1%**;
- window replacement: **8.2%**.

These are the first direct, fresh, representative national envelope-action
rates admitted by P99.

## 2. Unknown action overlap — bounded, not summed

The source does not publish whether the same household carried out more than
one of those envelope measures.

Let the four marginal shares be:

`(0.037, 0.024, 0.041, 0.082)`.

For the union "at least one of the four major envelope actions", with no
additional dependence assumption, the generic sharp bounds are:

`lower = max(marginals) = 0.082`

`upper = min(1, sum(marginals)) = 0.184`

Therefore:

`ANY_MAJOR_ENVELOPE_ACTION_LAST_12_MONTHS in [8.2%, 18.4%]`.

This is deliberately conservative.

P99 forbids:

`3.7 + 2.4 + 4.1 + 8.2 = 18.4%`

being treated as a point renovation rate.

Canonical boundary:

`SUM OF COMPONENT ACTION RATES != ANY-ACTION POINT RATE`.

No midpoint and no independence assumption are introduced.

## 3. Independent regional validation — Budapest CARES 2023

Source:

`SRC-B02-BUDAPEST-CARES-HOUSEHOLD-SURVEY-2023`

The Metropolitan Research Institute study is based on an in-person survey of
**2009 owner households in Budapest**, carried out from 13 October to
7 November 2023 and designed to be representative of Budapest housing stock.

For family houses, its last-10-year intervention list includes:

- window/door change: **94 mentions**;
- partial/full external-wall insulation: **47 mentions**.

The study further reports that insulation and window change are especially
important needs for family houses built before 1991.

P99 uses this only as an **independent structural/regional validation** that:

- envelope actions remain active;
- window and wall actions coexist in the renovation system;
- building age materially structures envelope need/action.

It is not converted to a national share.

Boundary:

`BUDAPEST REPRESENTATIVE != HUNGARY REPRESENTATIVE`.

## 4. Current realized programme validation — EKR 2025-26

Source:

`SRC-B02-HU-EKR-ATTIC-IMPLEMENTATION-2026`

The official 4 February 2026 government statement reports that under EKR:

**50,000 properties received free attic-floor insulation.**

The current Takarékos Otthon Programme is nationwide and includes attic-floor
insulation, facade insulation and window replacement among the available
measures.

P99 uses the 50,000 figure as:

`RECENT_REALIZED_IMPLEMENTATION_VALIDATION`.

It proves that the envelope-action pathway is not merely historical or
theoretical.

It is not divided by the B02 population to create a rate because:

- the source period and programme denominator are not identical to the TARKI
  national survey estimand;
- programme participants are not automatically the B02 physical-screening
  denominator;
- the statement is a programme implementation count, not a stock survey.

Boundary:

`REALIZED EKR ACTION VOLUME != NATIONAL ANNUAL ACTION RATE`.

## 5. Current monitoring limitation — MEHI 2025/26

Source:

`SRC-B02-HU-MEHI-RENOVATION-DATA-GAPS-2025`

MEHI's current data-gap analysis states that the planned Building Renovation
Monitoring System has not yet been implemented and that Hungarian building
energy/renovation data are fragmented in collection frequency and quality.

The analysis explicitly links the missing unified database to the inability to
track renovation numbers, types, depth, effects and a reliable annual
renovation rate.

This is important negative evidence.

P99 therefore does **not** manufacture a 2026 stock-wide point update from:

- programme counts;
- publication dates;
- regional samples;
- old renovation-rate extrapolations.

Boundary:

`PUBLICATION YEAR != OBSERVATION YEAR`.

## 6. Why the 2022 evidence is still admitted as fresh

P81 requires an explicit freshness floor rather than a hidden "latest
publication" heuristic.

For P99:

`freshness_floor_year = 2021`.

The TARKI-REKK observation year is **2022**, so it is admitted as fresh under
the existing P81 contract.

This does not mean it is an exact 2026 point rate.

Status:

`FRESH NATIONAL DIRECT ACTION EVIDENCE = AVAILABLE`

but:

`2026 POINT ACTION RATE = NOT IDENTIFIED`.

## 7. What P99 resolves

The former generic statement:

`FRESH_MULTI_SOURCE_ENVELOPE_ACTION_EVIDENCE_REQUIRED`

is no longer an accurate description of the evidence state.

P99 now has:

1. fresh representative national direct action-rate evidence;
2. independent 2023 regional/structural validation;
3. recent 2025-26 realized nationwide programme implementation validation;
4. explicit current negative evidence explaining why a 2026 point rate cannot
   honestly be produced.

Current evidence status:

`PARTIAL_RESOLVED_FRESH_MULTI_SOURCE_ACTION_EVIDENCE`.

## 8. What P99 does NOT resolve

The TARKI-REKK observed renovation activity does not identify which dwellings
in a future national heat-pump programme should receive:

- `AIR_TO_WATER_HP_ONLY`; or
- `REFERENCE_ENVELOPE_RETROFIT_PLUS_AWHP`.

Similarly:

- "insulated facade" does not prove P80/P96 reference U compliance;
- "window replaced" does not identify window U;
- a recent annual renovation rate is not a future programme selection share.

Therefore the generic fresh-evidence blocker is superseded by the sharper
model/evidence problem:

`REFERENCE_PROGRAMME_ENVELOPE_ACTION_SELECTION_CROSSWALK_REQUIRED`.

That crosswalk must connect admitted current envelope state/deficit evidence
to the explicit prospective reference-retrofit post-state, preserving
uncertainty.

## 9. Q-B02-004 effect

Previous current reference-programme evidence residual after P98:

`FRESH_MULTI_SOURCE_ENVELOPE_ACTION_EVIDENCE_REQUIRED`.

P99:

`FRESH_MULTI_SOURCE_ENVELOPE_ACTION_EVIDENCE_REQUIRED`

->

`PARTIAL_RESOLVED_FRESH_MULTI_SOURCE_ACTION_EVIDENCE`.

New exact residual:

`REFERENCE_PROGRAMME_ENVELOPE_ACTION_SELECTION_CROSSWALK_REQUIRED`.

Q-B02-004 remains `OPEN_NARROWED`.

Independent B05 product-map gaps remain separate and are not affected by P99.

## 10. Provenance for later study/reporting

P99 records separately:

- the source-native component action rates;
- the derived union bound and its formula;
- source observation year;
- source population scope;
- validation-only sources;
- current negative-data boundary;
- forbidden promotions.

This is intentional: the later study must be able to distinguish a direct
source observation from a derived model quantity.

## 11. Frozen boundaries

`OBSERVED RECENT ENVELOPE ACTION RATE != REFERENCE PROGRAMME ACTION SHARE`

`SUM OF COMPONENT ACTION RATES != ANY-ACTION POINT RATE`

`BUDAPEST REPRESENTATIVE != HUNGARY REPRESENTATIVE`

`REALIZED EKR ACTION VOLUME != NATIONAL ANNUAL RATE`

`PUBLICATION YEAR != OBSERVATION YEAR`

`FRESH ACTION EVIDENCE != REFERENCE U COMPLIANCE`

## 12. Readiness

- B02 remains **55%**
- B06 `PEAK_LOAD_EFFECT` remains **50%**

P99 improves action-evidence provenance and materially narrows the blocker, but
does not mint an action-selection pass or a readiness uplift.
