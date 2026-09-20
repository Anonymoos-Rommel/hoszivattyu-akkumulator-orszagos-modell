# B02-P60 — Hungarian S1 demand-outcome authority and linked completion gate

**State:** `SOURCE/SEMANTICS BLOCKER RESOLVED / RECORD OUTCOMES REMAIN FAIL-CLOSED`

**Canonical base:** `ebe977833c7a075e157140c4b7146c2d9453f8c7`

**Implementation date:** 2026-09-20

## 1. Problem

The existing row `GAP-B02-S1-DEMAND-OUTCOME` described S1 as blocked because no
national source with phase-linked before/after evidence had been identified.

That wording mixed two different questions:

1. Does Hungary have an authoritative and executable way to prove a residential
   retrofit outcome?
2. Does every candidate dwelling already have its own completed before/after
   outcome?

P60 establishes that the answer to (1) is **yes** and keeps (2) fail-closed at
record/intervention grain.

Core boundary:

`NATIONAL OUTCOME DATASET != REQUIRED FOR EVERY RECORD`

`INTERVENTION COMPLETION != DEMAND REDUCTION PROVEN`

`MISSING OUTCOME != ZERO SAVING`

`PROGRAMME THRESHOLD != UNIVERSAL PHYSICAL EFFECT FACTOR`

## 2. Hungarian official gate authority

### 2.1 MFB RRF-REP-10.13.1-24 (2024)

The official Magyar Fejlesztési Bank programme publication requires at least
30% primary-energy reduction **relative to the initial pre-project state** as a
result of the financed energy retrofit, supported by a
`Hiteles Energetikai Tanúsítvány`.

Source:
`SRC-B06-HU-OFP-RRF-2024`

This proves a Hungarian record-level, documented before/after calculation route.
The 30% value is a programme threshold. P60 does not convert it into a generic
retrofit-effect assumption.

### 2.2 Current MFB KEHOP Plusz programme (2026)

The current MFB programme requires supported projects to demonstrably achieve
at least 30% primary-energy savings per building. The publication also states
that if the required saving is not achieved after implementation, the financing
amount is recovered.

Source:
`SRC-B06-HU-OFP-KEHOP-2026`

This confirms that outcome verification remains an operative completion
condition rather than an ex-ante modelling convenience.

## 3. P60 admissible S1 outcome paths

### A. MEASURED_USAGE / OBS

Requires:

- linked before and after values for the same record/intervention/phase;
- same metric, unit and method;
- source references for both sides;
- documented end-use scope;
- documented weather/operation normalization.

Raw bill or meter change without the normalization boundary remains `Q`.

### B. CERTIFIED_CALCULATION / DER

Requires:

- linked before and after values;
- same metric, unit and calculation method;
- explicit phase link;
- before and after source references;
- documented end-use scope.

The Hungarian pre/post HET route is an authority for this path.

### C. NOT_REQUIRED / OBS or DER

Allowed only when an explicit rule says demand reduction is not required for
that record/transition. A reason and authority reference are mandatory.
Missing evidence is never relabelled `NOT_REQUIRED`.

## 4. Block semantics

- missing/mismatched linked evidence -> `Q`;
- measured usage without normalization -> `Q`;
- after >= before where reduction is required -> `BLOCKED`;
- configured minimum reduction not achieved -> `BLOCKED`;
- admitted linked outcome -> `READY`.

A bare `completion_status` plus a source ID is no longer sufficient to open
`S1_DEMAND_REDUCED`.

## 5. Hungarian bounded calibration evidence

### Keszthely, 30-dwelling condominium

A public Budapest/RenoPont handbook reports:

- 1985 building;
- energy class F before, B after;
- reported energy-performance value: 220 -> 126-129 kWh/m2a;
- heat-centre settlement: 41-42.5% saving versus the 2017 base year.

The calculation pair is retained as bounded `DER` calibration. The measured
41-42.5% row remains `Q` for generic engine use because the public case does
not disclose the required weather/operation/end-use normalization.

Source:
`SRC-B06-HU-RENOPONT-KESZTHELY`

### Two-generation family house

A public Budapest/RenoPont handbook reports annual gas use falling from
3600 m3 to 1600 m3, stated as 56%, after a combined envelope retrofit.

The raw case is preserved but remains `Q` for generic engine use because the
public description does not establish weather normalization or DHW separation.

Source:
`SRC-B06-HU-RENOPONT-FAMILY-3600-1600`

## 6. Search trail / partial evidence retained

The RenoHUb Horizon 2020 project (CORDIS project 845652) was also investigated.
Its public results catalogue describes a pilot-project deliverable intended to
report achieved energy saving, and the final public project material documents
Hungarian pilot/good-practice cases.

The exact deliverable payload was not used as gate authority here because the
public fetch route did not expose a sufficiently stable field-level
before/after artifact during this audit.

Public trace:
`https://cordis.europa.eu/project/id/845652/results`

This is retained as a researched route, not silently discarded.

## 7. Architecture repair

The household state model already allows `OBS` or `DER` for S0->S1
completion. P60 aligns B06 with that contract.

Before P60, B06 could promote S1 from:

`completion_status == OBS + any completion_source_id`

After P60:

`linked outcome gate READY + matching OBS/DER completion status + source refs`

is required.

Thus:

`COMPLETION EVIDENCE != OUTCOME EVIDENCE`

## 8. Programme effect

P60 closes the **source/contract blocker** for
`GAP-B02-S1-DEMAND-OUTCOME`.

It does not create:

- a national completed-retrofit microdataset;
- a universal annual saving percentage;
- a national S1 population count;
- a design-peak reduction factor;
- automatic state promotion for any dwelling.

Each real S0->S1 transition remains `Q` until its own linked outcome or
explicit `NOT_REQUIRED` authority is present.

## P64 supersession note

P60 originally used a generic completion-status/source check beside the linked
outcome. P64 supersedes that completion-side contract.

Canonical S1 semantics from P64 onward:

`REALIZED COMPLETION OBS != OUTCOME OBS/DER`

and:

`P64 QUALIFIED + P60 READY -> S1`.

Therefore the historical P60 wording
`linked outcome gate READY + matching OBS/DER completion status + source refs`
must not be read as the current completion authority. The outcome gate remains
canonical; the completion-side authority is now
`modules/B06/realized_completion_gate.py`.

