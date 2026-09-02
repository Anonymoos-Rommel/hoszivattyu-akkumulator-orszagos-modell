# B10-P11 — Timed reinforcement / investment pathway integration gate

Canonical base: `d0695039b57b4808680a8cf54eb14dc8b51e0ab8`

## Core rule

`PROJECT / REINFORCEMENT AUTHORITY != PROGRAMME ATTRIBUTION != PROJECT DELIVERY DATE != PROGRAMME CAPEX AMOUNT != CAPEX CASH-FLOW PERIOD`

B10-P11 adds no new observed network project and no new numeric investment claim.
It is an integration/authority slice over the already canonical P3/P5/P6 gates.

## Existing canonical authorities

- B10-P3 owns the `WITHOUT_PROGRAM` / `WITH_PROGRAM` attribution decision.
- B10-P5 owns programme-specific reinforcement authority and numeric programme-
  incremental CAPEX authority. Published headroom remains screening only.
- B10-P6 owns project-delivery timing evidence. Planned/expected dates, verified
  ex-ante targets, actual completion and delivery probability remain separate.
- B10-P7 network-layer classification remains a separate authority dimension.
- B10-P10 managed peak / network survivability remains separate from investment
  timing and cannot mint a reinforcement project or CAPEX schedule.

## The missing boundary closed by P11

A completion date is not a spending date. Therefore:

`PROJECT DELIVERY DATE != CAPEX SPEND DATE != ANNUAL CASH-FLOW`

P11 never assigns a P5 programme-incremental CAPEX amount to the P6 target or
completion year merely because those dates exist. A project may therefore have:

- a proven programme-incremental CAPEX total;
- a proven expected/actual delivery date;
- but **no timed CAPEX rows**.

That state is canonical `Q_CAPEX_TIMING_UNRESOLVED`, not zero and not a default
cash-flow profile.

## Executable contract

`build_timed_investment_pathway()` consumes:

1. the original canonical `InfrastructureRecord`;
2. a `ReinforcementGateDecision` from P5;
3. source timing evidence used to re-run P6;
4. optional `CapexCashflowEvidence` rows.

P11 re-runs P5 from the original infrastructure record (ignoring only optional
headroom-screening context, which cannot affect reinforcement/CAPEX authority) and
rejects a supplied P5 decision if project, region, horizon, reinforcement flag,
attribution truth or programme-incremental CAPEX does not reproduce.

P11 also re-runs P6 from the supplied timing evidence. It preserves:

- `DELIVERY_EX_ANTE_TARGET`;
- `DELIVERY_CURRENT_TARGET_ONLY`;
- `DELIVERY_ACTUAL_OBSERVED`;
- schedule variance semantics;
- `Q_NO_CALIBRATED_DELIVERY_MODEL` completion-probability status.

It cannot create a completion probability.

## CAPEX cash-flow authority

A REAL timed programme-CAPEX schedule requires claim-specific evidence at authority
level 1–3 bound to all of:

- exact `PROJECT_ID`;
- exact `NETWORK_OPERATOR`;
- exact `REGION_ID`;
- `REGION_GRAIN:DSO_SUBSTATION`;
- exact P5 `COST_COMPONENT`;
- exact `SCHEDULE_ID`;
- exact period start/end;
- `PROGRAMME_INCREMENTAL_CAPEX_CASHFLOW`.

At least one row must also prove:

`COMPLETE_PROGRAMME_INCREMENTAL_CAPEX_SCHEDULE`

and the non-overlapping schedule total must reconcile to the P5 programme-
incremental CAPEX total. Otherwise the timed CAPEX result is Q and publishes no
numeric cash-flow rows.

An explicit SCN phasing may use the same binding/completeness contract without
source-authority promotion, but it remains `SCN_TIMED_PROGRAMME_CAPEX` and can never
become REAL/DER by arithmetic.

## Deliberate non-results

P11 does not publish or infer:

- a default annual expenditure profile;
- completion-year lump-sum spending;
- straight-line CAPEX phasing;
- delivery probability;
- network-layer classification;
- hosting capacity or network survivability;
- reinforcement from headroom alone;
- total project cost as programme-incremental cost;
- national/regional CAPEX by aggregation of unresolved projects;
- national DSO coverage;
- readiness uplift.

`regional_readiness.csv` and `incremental_capex_attribution.csv` remain unchanged.
B10 readiness remains 15%. Q-B01-002, Q-B10-001 and Q-B10-002 remain open/bounded.

## Acceptance contribution

P11 closes the **authority boundary** required before an “időzített beruházási
pálya” can be populated safely. It does not claim that the national timed investment
pathway is populated: there are currently no programme-specific reinforcement +
programme-incremental CAPEX + complete authoritative cash-flow schedules in the
canonical B10 ledger.
