# B02-P74 — Hungarian reuse/nonreuse path outcome authority

**State:** `GENERIC PATH-OUTCOME BLOCKER NARROWED / NO FALSE EKR→AWHP TRANSFER`

**Canonical base:** `b839bb64266922e4848bbf8bff608cea5d729b73`

**Implementation date:** 2026-09-21

## 1. Purpose

P73 removed the need to invent a point value for the CENTRAL_HEATING reuse /
nonreuse split.

The remaining question is therefore not:

> What percentage is reuse?

It is:

> For each admissible distribution path, what outcome authority is actually
> available?

P74 audits two Hungarian evidence surfaces:

1. current EKR 2.11 secondary-side heating reconstruction;
2. the already-admitted KEHOP Plusz-4.1.7-24 maximum-cost package.

## 2. EKR 2.11 — what it proves

Current legal source:

- **18/2025. (VII. 31.) EM rendelet**, current consolidated text;
- section **2.11 Szekunder oldali fűtés rekonstrukció**;
- official legal source:
  `https://njt.hu/jogszabaly/2025-18-20-8Y`.

Within its stated scope the measure identifies concrete secondary-side actions,
including:

- one-pipe distribution conversion to two-pipe or at least bypassed one-pipe;
- individual emitter-control valves/actuators;
- hydraulic balancing using a balancing plan;
- conditional replacement of large-water-volume sectional cast-iron
  radiators;
- heat-cost allocation for covered residential cases;
- conditional heat-reflector installation.

This is strong Hungarian evidence that these are real, recognized secondary
heating-system interventions.

Canonical use:

`EKR 2.11 -> SCOPE-LIMITED HUNGARIAN TECHNICAL ACTION AUTHORITY`.

It does not identify how often each action occurs in the national dwelling
stock.

## 3. Scope boundary

The current EKR 2.11 application scope covers own-central-heat or
district-heated multi-dwelling buildings / cooperative buildings and public
buildings as stated by the source.

P74 therefore does not silently extend that authority to all family houses.

`EKR COVERED BUILDING SCOPE != FULL NATIONAL REUSE PATH`.

This leaves a specific residual:

`REUSE_FAMILY_HOUSE_OR_FULL_NATIONAL_SCOPE_ACTION_AUTHORITY_REQUIRED`.

## 4. Source-native EKR response values

The current 2.11 detailed calculation table contains source-native accounting
cases of:

- **10%**;
- **6%**;
- **4%**;

plus conditional:

- **+3%** where all large-water-volume cast-iron sectional radiators are
  replaced and the heating-system supply-water temperature is reduced by at
  least **7 C**;
- **+1%** for the defined heat-reflector case.

The resulting source-native table cases reach **14%, 10%, 8%**.

These values are retained only as EKR accounting references.

## 5. Critical AWHP boundary

The same current EKR 2.11 measure lists as an exclusion case that a **new
energy carrier is introduced into heating**.

The national programme route being modelled can replace a fossil or other
existing heat source with an electric air-to-water heat pump.

Therefore:

`EKR SOURCE-NATIVE SAVING % != AWHP PROGRAMME SAVING %`.

And:

`EKR 7 C CONDITION != AWHP DESIGN FLOW TEMPERATURE`.

P74 explicitly blocks both transfers.

The EKR source remains useful for:

- technical action taxonomy;
- hydraulic/balancing requirements;
- lower-temperature retrofit validation;
- record/archetype evidence design.

It is not the missing AWHP response envelope.

## 6. KEHOP nonreuse package authority

P67 already admitted the official programme maximum-cost authority:

**Hőleadók cseréje komplett szekunder körrel**

- material maximum: **1,422,400 HUF/set**;
- labour maximum: **2,133,600 HUF/set**;
- total maximum: **3,556,000 HUF/set**.

The source-defined package includes new emitters, secondary heating circuit,
HMV tank, controls, modern pipework, required materials/installation and
removal of existing emitters/pipes.

P74 binds this specifically to the broad
`NEW_OR_REPLACE_DISTRIBUTION_REQUIRED` path as an **official maximum-cost
authority**.

But:

`OFFICIAL MAXIMUM != MARKET-TYPICAL COST`

and:

`KEHOP ELIGIBLE PROJECT SET != ALL NATIONAL NONREUSE DWELLINGS`.

The current official MFB programme page also confirms that KEHOP Plusz-4.1.7-24
is a residential renovation programme with a defined eligible family-house
scope. That scope cannot be silently promoted to all P73 nonreuse dwellings.

## 7. What P74 resolves

Resolved/narrowed:

- generic search for a Hungarian nonreuse package price authority;
- generic search for recognized Hungarian secondary-side intervention actions;
- EKR-saving-percentage transfer ambiguity.

Machine-readable status:

`NONREUSE_PATH_CAPEX_UPPER_AUTHORITY = PARTIAL_RESOLVED_SCOPE_LIMITED`

`REUSE_PATH_OUTCOME_AUTHORITY = PARTIAL_TECHNICAL_ONLY`.

## 8. Current distribution-path residual

After P74 the useful blockers are no longer the generic:

`REUSE_PATH_OUTCOME_BOUNDS + NONREUSE_PATH_OUTCOME_BOUNDS`.

They are:

- `REUSE_PATH_CAPEX_BOUND_REQUIRED`;
- `REUSE_FAMILY_HOUSE_OR_FULL_NATIONAL_SCOPE_ACTION_AUTHORITY_REQUIRED`;
- `NONREUSE_KEHOP_SCOPE_CROSSWALK_REQUIRED`;
- `AWHP_PATH_RESPONSE_AUTHORITY_REQUIRED`.

Other Q-B02-004 residuals remain:

- `NON_GAS_CONVECTOR_EMITTER_INTERVENTION_ASSIGNMENT`;
- `ROOM_GRAIN_ACTION_DISTRIBUTION`;
- `MARKET_REALIZED_COST_DISTRIBUTION` only if a central/expected monetary
  estimate is required.

## 9. Non-claims

P74 does not claim:

- EKR 4–14% is heat-pump programme saving;
- 7 C is a national AWHP design-temperature rule;
- all CENTRAL_HEATING systems are EKR-covered;
- all family houses are EKR 2.11-covered;
- every nonreuse dwelling consumes one KEHOP package;
- 3,556,000 HUF is a market average;
- Q-B02-004 is resolved.

B02 readiness remains **55%**.
