# Project blocker re-audit — 2026-09-22

**Repository base:** `fb65c0327f2d143038b7c6b77dcfcaab012b7f89`  
**Canonical population-inference policy:** effective 2026-09-20  
**Machine-readable matrix:** `registry/project_blocker_reaudit_2026_09_22.csv`

## 1. Audit rule

The project remains governed by:

`NO FULL-POPULATION DATA != BLOCKER`

`NO DEFENSIBLE POPULATION INFERENCE == BLOCKER`

`POPULATION ESTIMATE != RECORD PASS/FAIL`

Additional layer rules established since the 2026-09-20 audit:

`NATIONAL CONTROL-AREA BASELINE != REGIONAL DSO/COUNTY BASELINE`

`NATIONAL NETWORK ESTIMATE != SPECIFIC NODE PASS/FAIL`

`NATIONAL GAS QUALITY DISTRIBUTION != PARTICIPANT GAS-QUALITY POINT`

`PRODUCT COHORT != PRODUCT-SPECIFIC RUNTIME`

`PUBLIC REPOSITORY MATERIALIZATION != MODEL-USE AUTHORITY`

## 2. Current registry state

`registry/open_questions.csv` currently contains:

- **45 total questions**
- **35 OPEN**
- **10 RESOLVED**

The 35 OPEN questions are classified exhaustively in the machine-readable matrix.

### Re-audit classes

| Classification | Count | Meaning |
|---|---:|---|
| ACTIVE_EXISTING_COMPUTE | 2 | Can be attacked now primarily from existing canonical data/models. |
| ACTIVE_EXISTING_THEN_EXTERNAL | 5 | Exhaust current repository evidence first, then acquire only residual evidence. |
| ACTIVE_EXTERNAL_ACQUISITION | 2 | Real numeric source acquisition/use authority is the blocker. |
| ACTIVE_EXTERNAL_MARKET | 5 | Current/licensed market-price or price-component evidence required. |
| ACTIVE_EXTERNAL_LEGAL | 2 | Exact current legal/metering authority required. |
| ACTIVE_EXTERNAL_PRODUCT | 5 | Product-specific runtime evidence required. |
| CONTRACT_FROM_EXISTING | 1 | Can be resolved architecturally without new external evidence. |
| CONDITIONAL_CLAIM_ONLY | 1 | Not a universal model blocker; required only for claims that need the dimension. |
| NONBLOCKING_PROCUREMENT | 1 | Procurement/strategic-risk evidence, not core physical-model evidence. |
| DOWNSTREAM_EXTERNAL | 2 | External evidence needed later, but not a current upstream blocker. |
| DOWNSTREAM_MODEL_COMPUTE | 6 | Derived only after upstream modules are populated. |
| OWNER_POLICY_DECISION | 2 | Normative decision; the model may stress-test but may not invent it. |
| DEPENDENCY_AFTER_UPSTREAM | 1 | Must wait for a specified upstream result. |

**Global blocker flag:** 21 yes / 14 no.

This does not mean all 21 should be attacked now. Dependency and impact order still apply.

## 3. Material changes since the 2026-09-20 audit

### 3.1 B08 seasonal methodology is no longer open

B08-P3 resolved Q-B08-002.

The project now has an executable:

- Europe/Budapest calendar-year contract;
- December-February winter reporting contract;
- half-open interval semantics;
- UTC alignment;
- complete-window/no-gap seasonal peak rule.

The remaining B08 national blocker is real A65 numeric acquisition/use authority/provenance, not regionalisation.

### 3.2 B09 dispatch/storage architecture is no longer open

B09-P3 resolved Q-B09-002.

Canonical boundary:

`B07 household battery -> already reflected in B08 load -> must not be dispatched again in B09`

B09 physical adequacy is a valid `NO_DISPATCH` baseline.

Optional system storage requires a separate asset/SOC/efficiency/schedule authority.

The remaining B09 national blocker is real A75 numeric acquisition/use authority/provenance plus production-type manifest, not regionalisation.

### 3.3 B10 no longer requires a complete national node inventory

B10-P67 retired the complete national node inventory and complete entity-to-node panel as prerequisites for national expected-impact estimation.

National B10 now needs representative/calibrated:

- programme-demand distribution by DSO/network stratum;
- numeric headroom cohort;
- reinforcement/project cohort;
- programme-incremental CAPEX distribution;
- delivery-timing distribution;
- survivability evidence;
- calibration and explicit uncertainty.

Exact node/project claims remain exact.

### 3.4 B11 no longer requires exact participant-to-FGSZ-point mapping for national bcm

B11-P6 separated national gas-displacement inference from exact participant/billing claims.

It also materialised the weighted Hungarian gas-heating appliance-class control:

- traditional gas boiler: 26.66%;
- condensing gas boiler: 32.73%;
- gas convector: 40.61%;
- weighted gas-heating subsample N=657.

National bcm inference still requires class-specific seasonal-efficiency bounds and a temporally aligned bounded GCV/LHV distribution, among other residuals.

### 3.5 B07 supply-chain origin is no longer SOC physics

B07-P3 correctly separates cell/inverter/upstream origin from the physical SOC engine.

Q-B07-002 remains relevant for procurement/strategic-dependency claims, but it is not a core physical blocker.

### 3.6 B05 no longer requires one universal reference heat-pump model

B05-P7 materialised product-cohort envelopes at eight exact common coordinates, including five cross-manufacturer coordinates.

The residual product-domain problem is now specifically:

- cold W45 cross-manufacturer coverage;
- continuous W55 coverage;
- below -15 C W35 coverage if the extreme domain is retained.

## 4. Critical correction to the old queue

The 2026-09-20 audit put Q-B02-004 before Q-B02-001.

That order is now obsolete.

B02-P61 explicitly established that current-stock emitter/hydraulic/electrical readiness and Q-B02-004 emitter-mix closure are **not aggregate technical-eligibility prerequisites**.

Therefore:

`Q-B02-004 NOT RESOLVED != Q-B02-001 BLOCKED`

Q-B02-001 now asks for a defensible national inference over the terminal outcomes of the already-defined transition paths.

This can be attacked directly from existing canonical transition gates and population controls.

## 5. New impact-ordered active queue

### Priority 1 — Q-B02-001: national technical-eligibility inference

**Classification:** ACTIVE_EXISTING_COMPUTE  
**Priority:** CRITICAL

Goal:

materialise a bounded national distribution of terminal technical outcomes after allowed reuse/upgrade/replace transitions.

This is now the highest-impact task because it directly constrains:

- B01 programme ceiling;
- B05/B06 national physical deployment;
- B11 gas displacement;
- B12 household economics;
- later fiscal/macro modules.

It must preserve:

`MISSING RECORD EVIDENCE != RECORD PASS`

while permitting:

`DEFENSIBLE POPULATION INFERENCE -> NATIONAL BOUNDED ELIGIBILITY`

### Priority 2 — Q-B05-002: extreme-weather return-period model

**Classification:** ACTIVE_EXISTING_COMPUTE  
**Priority:** CRITICAL

The repository already has:

- observed HungaroMet hourly data;
- a materialised 72-hour observed extreme-cold event.

Next action:

derive a transparent statistical stress/return-period distribution with uncertainty.

Important semantic boundary:

the result may be a project-derived statistical return-period scenario; it must **not** be labelled an official HungaroMet "1-in-10 winter" unless such an authority is actually found.

### Priority 3 — Q-B02-004: bounded physical-response completion

**Classification:** ACTIVE_EXISTING_THEN_EXTERNAL  
**Priority:** CRITICAL

P83 already gives the first bounded national-stratum post-state surface.

Continue existing evidence first for:

- component-area geometry inference;
- pitched-roof U;
- ventilation;
- thermal-bridge correction;
- design-outdoor mapping;
- current HP-only baseline U;
- national P65 supply-temperature inference;
- action-frequency evidence.

This blocks programme COP/CAPEX/procurement uncertainty, but no longer blocks aggregate technical eligibility.

### Priority 4 — Q-B05-001: residual product operating domain

**Classification:** ACTIVE_EXISTING_THEN_EXTERNAL  
**Priority:** CRITICAL

Exhaust current Vaillant/STIEBEL and registered product documentation first.

Search externally only for the exact residual coordinates/domain segments not already covered.

### Priority 5 — B11 national bcm residuals

No dedicated OPEN question currently represents all B11-P6 residuals, so the module-level blocker set must remain visible:

- class-specific seasonal gas-efficiency bounds;
- temporally aligned bounded GCV/LHV distribution;
- multi-fuel gas-share decomposition;
- DHW/cooking end-use boundary;
- rebound bound;
- observed gas-sales calibration;
- explicit uncertainty.

The appliance-class weights are already materialised; the next strong B11 evidence task is class-specific seasonal-efficiency bounds.

### Priority 6 — B10 representative network-impact cohorts

Q-B10-001 and Q-B10-002 remain genuine, but now as population-inference tasks rather than national-digital-twin tasks.

First use current project/node/headroom evidence; expand externally only when cohort representativeness remains insufficient.

### Priority 7 — combined ENTSO-E numeric acquisition track

Research/acquire together:

- Q-B08-001: A65 load;
- Q-B09-001: A75 generation.

Both already have source semantics, parser boundaries and national grain.

The remaining problem is acquisition-specific numeric evidence, model-use authority, provenance and—in B09—the production-type manifest.

### Priority 8 — joined H-tariff / battery legal track

Research together:

- Q-B04-001;
- Q-B07-001.

This requires current authoritative legal/metering evidence and cannot be solved by statistical inference.

### Priority 9 — B03/B04 market-price tracks

These are genuine blockers for economic outputs, but they should not interrupt current physical-model closure.

Consolidated tracks:

- Q-B03-001 + Q-B03-002 + Q-B03-004: licensed TTF market-data channel;
- Q-B03-003 + Q-B03-006: gas final-price component bridge;
- Q-B04-002: finish current electricity component bridge from existing official material first.

## 6. Questions that should not consume current search effort

### Q-B01-002 — geography choice

Classification: `CONTRACT_FROM_EXISTING`.

The architecture can retain two canonical grains:

- county/statistical grain for population evidence;
- DSO/network grain for network authority.

The handoff/crosswalk is explicit where an inter-module claim needs it.

A single universal canonical geography is not required.

### Q-B05-006 — return temperature / delta-T

Classification: `CONDITIONAL_CLAIM_ONLY`.

The current outdoor × supply grid is valid for claims whose source/test boundary supports it.

Return/delta-T should be required only for claims materially dependent on that dimension.

It should not remain a universal B05 blocker.

### Q-B07-002 — upstream battery origin

Classification: `NONBLOCKING_PROCUREMENT`.

Keep open for procurement/industrial-policy analysis, not SOC physics.

### Q-B06-010 — CAPEX

Monetary CAPEX evidence belongs to the cost/procurement layer when monetary outputs are requested.

Its absence does not invalidate the B06 physical runtime.

### B01/B06/B12/B13 downstream questions

Q-B01-003/004/005, Q-B06-001, Q-B12-001 and Q-B13-001 are downstream computations, not present evidence-search priorities.

### Policy decisions

Q-B01-006 and Q-B01-007 require owner/policy decisions.

The model can expose sensitivity and trade-offs; it must not autonomously choose normative minima or objective weights.

## 7. Consolidated evidence tracks

To avoid duplicated research:

1. **ENTSO-E numeric acquisition**
   - Q-B08-001
   - Q-B09-001

2. **H-tariff / battery legal**
   - Q-B04-001
   - Q-B07-001

3. **TTF licensed market data**
   - Q-B03-001
   - Q-B03-002
   - Q-B03-004

4. **Gas final-price bridge**
   - Q-B03-003
   - Q-B03-006

5. **B05 product runtime**
   - Q-B05-003
   - Q-B05-004
   - Q-B05-005

6. **Battery runtime physics**
   - Q-B07-003
   - Q-B07-004

7. **B10 network population inference**
   - Q-B10-001
   - Q-B10-002

## 8. Immediate next slice

The next slice should be:

**B02 — national terminal technical-eligibility population inference**

Reason:

- CRITICAL;
- highest downstream fan-out;
- no new web search is required to begin;
- Q-B02-004 is no longer a prerequisite;
- existing P57/P58/P59/P61/P65 transition contracts and KSH/P21 population controls should be exhausted before purchasing or requesting more data.

The slice must not manufacture household PASS/FAIL records.

Its target is a bounded national population result with explicit uncertainty and explicit exclusion/unknown handling.

## 9. Readiness policy

This re-audit does **not** change module readiness percentages.

A reclassification of a blocker is not by itself a physical/data completion event.

Readiness should move only when a subsequent slice materialises an admissible output or closes a substantive evidence requirement.
