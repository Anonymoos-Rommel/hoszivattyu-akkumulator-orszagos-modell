# Project blocker re-audit — 2026-09-20

**Canonical basis:** population inference policy effective 2026-09-20  
**Repository base:** `a1f5daac96e264b1a47760cd64aedb13b5d72b1c`

## Audit rule

`NO FULL-POPULATION DATA != BLOCKER`

`NO DEFENSIBLE POPULATION INFERENCE == BLOCKER`

`POPULATION ESTIMATE != RECORD PASS/FAIL`

The audit re-checks every canonical question in `registry/open_questions.csv`. Historical source packs remain historical and are not rewritten as if later evidence existed at their original date.

## Result

Before this slice the registry contained 45 questions: 7 RESOLVED and 38 OPEN.

- all 7 existing RESOLVED questions remain correctly resolved;
- Q-B02-002 is closable from already-canonical evidence and is closed by B02-P50;
- the next upstream research target is Q-B02-004;
- several later questions need no web search yet because they are contract, policy or downstream-computation questions.

## Question-by-question audit

| ID | Module | Priority | Current status | Re-audit classification | Reason / next action |
|---|---|---|---|---|---|
| Q-B01-001 | B01 | CRITICAL | OPEN | DEPENDENCY_LATER | Depends on Q-B02-001 plus legal/programme eligibility; do not search target count before technical stock is bounded. |
| Q-B01-002 | B01 | HIGH | OPEN | CONTINUE_EXISTING_FIRST | B10 already has six-DSO territorial/spatial authority work; exact county/settlement-to-DSO operational crosswalk still needs completion. |
| Q-B08-001 | B08 | HIGH | OPEN | TARGETED_EXTERNAL_SEARCH | ENTSO-E national load semantics exist; reusable raw snapshot/licence and regional mapping remain external evidence gaps. |
| Q-B08-002 | B08 | HIGH | OPEN | CONTRACT_FROM_EXISTING | Primarily a calendar/season/peak definition contract; existing time-base and weather/load evidence can support a canonical methodology before more data search. |
| Q-B09-001 | B09 | HIGH | OPEN | TARGETED_EXTERNAL_SEARCH | A75 semantics exist; reusable numeric snapshot/licence and regional generation evidence remain external gaps. |
| Q-B09-002 | B09 | HIGH | OPEN | CONTRACT_FROM_EXISTING | System-storage/dispatch boundary can be specified from existing B07/B09 architecture before acquiring dispatch evidence. |
| Q-B02-001 | B02 | CRITICAL | OPEN | CONTINUE_AFTER_B02_004 | Building type/energy are admitted; national technical eligibility still needs emitter/temperature inference and explicit exclusion rules. |
| Q-B02-002 | B02 | CRITICAL | RESOLVED | CLOSE_FROM_EXISTING | P15 + contracted archetype dimensions + P21 APPROVED/JOSEPH/QUALIFIED calibrated linkage satisfy the new population-inference gate; closed by P50. |
| Q-B02-003 | B02 | HIGH | RESOLVED | KEEP_RESOLVED | Evidence-class separation is a lineage/semantics rule and remains valid. |
| Q-B02-004 | B02 | CRITICAL | OPEN | CONTINUE_EXISTING_FIRST | P39 gas-convector model plus P44-P49 radiator evidence and P65 temperature authority provide a strong base; missing defensible national emitter+temperature inference remains. |
| Q-B03-001 | B03 | CRITICAL | OPEN | TARGETED_EXTERNAL_SEARCH | Needs current/licensed TTF plus long-run fundamental scenario evidence. |
| Q-B03-002 | B03 | CRITICAL | OPEN | TARGETED_EXTERNAL_SEARCH | Needs actual reproducible/licensed EEX/ICE access terms and data channel. |
| Q-B03-003 | B03 | HIGH | OPEN | TARGETED_EXTERNAL_SEARCH | Needs current Hungarian component authorities beyond the existing regulated end-price layer. |
| Q-B03-004 | B03 | CRITICAL | OPEN | TARGETED_EXTERNAL_SEARCH | Needs licensed historical/forward numeric export and reproducible snapshot. |
| Q-B03-005 | B03 | CRITICAL | RESOLVED | KEEP_RESOLVED | Current MVM F.4 tariff authority is source-specific, not a population-coverage claim. |
| Q-B03-006 | B03 | HIGH | OPEN | TARGETED_EXTERNAL_SEARCH | Needs current Hungarian market-residential component bridge. |
| Q-B04-001 | B04 | CRITICAL | OPEN | TARGETED_EXTERNAL_SEARCH | Legal/metering separation of H tariff and battery/VPP requires current authoritative rules. |
| Q-B07-001 | B07 | CRITICAL | OPEN | TARGETED_EXTERNAL_SEARCH | Same legal/metering issue as Q-B04-001; should be researched as one joined evidence track. |
| Q-B07-002 | B07 | HIGH | OPEN | TARGETED_EXTERNAL_SEARCH | Requires manufacturer/supply-chain origin evidence. |
| Q-B07-003 | B07 | HIGH | OPEN | TARGETED_EXTERNAL_SEARCH | Requires product-specific one-way AC/DC efficiency evidence. |
| Q-B07-004 | B07 | MEDIUM | OPEN | TARGETED_EXTERNAL_SEARCH | Requires measured degradation data/model authority. |
| Q-B04-002 | B04 | CRITICAL | OPEN | CONTINUE_EXISTING_FIRST | Numerical 2026 M.1/MVM tariff evidence already exists; remaining legal component bridge should be completed from current official material. |
| Q-B04-003 | B04 | HIGH | OPEN | TARGETED_EXTERNAL_SEARCH | Requires current retail dynamic-tariff product and metering conditions. |
| Q-B05-001 | B05 | CRITICAL | OPEN | CONTINUE_EXISTING_FIRST | Several source-native product points already exist; first exhaust current product documentation, then search only missing W45/W55/cold-side points. |
| Q-B05-002 | B05 | CRITICAL | OPEN | CONTINUE_EXISTING_FIRST | Observed HungaroMet hourly panel and 72-hour cold spell already exist; return-period methodology can be attempted before new acquisition. |
| Q-B05-003 | B05 | HIGH | OPEN | TARGETED_EXTERNAL_SEARCH | Needs source-native test/defrost inclusion boundary or separate defrost measurement. |
| Q-B05-004 | B05 | HIGH | OPEN | TARGETED_EXTERNAL_SEARCH | Needs measured/source-native modulation and cycling/part-load evidence. |
| Q-B05-005 | B05 | HIGH | OPEN | TARGETED_EXTERNAL_SEARCH | Needs controller/DHW priority and high-supply operating-point evidence. |
| Q-B05-006 | B05 | MEDIUM | OPEN | TARGETED_EXTERNAL_SEARCH | Needs product grid with return-temperature/delta-T dimension. |
| Q-B06-006 | B06 | CRITICAL | RESOLVED | KEEP_RESOLVED | Resolved as linked annual/peak baseline source semantics; national prevalence was never claimed. |
| Q-B06-007 | B06 | HIGH | RESOLVED | KEEP_RESOLVED | Resolved as transferable physical-method contract; population coverage remains a separate input problem. |
| Q-B06-011 | B06 | HIGH | RESOLVED | KEEP_RESOLVED | Resolved as a bounded intervention-linked calibration/source question. |
| Q-B06-008 | B06 | HIGH | RESOLVED | KEEP_RESOLVED | Resolved as record-level emitter/temperature authority; population inference cannot replace per-building P65 evidence. |
| Q-B06-009 | B06 | HIGH | RESOLVED | KEEP_RESOLVED | Resolved as realised-completion authority and S1 handoff logic; not a national prevalence claim. |
| Q-B06-010 | B06 | MEDIUM | OPEN | TARGETED_EXTERNAL_SEARCH | Needs current official/market retrofit CAPEX and capacity evidence. |
| Q-B01-003 | B01 | HIGH | OPEN | LATER_MODEL_COMPUTE | Requires phased-vs-once physical/CAPEX/cash-flow comparison after upstream models are populated. |
| Q-B01-004 | B01 | HIGH | OPEN | LATER_MODEL_COMPUTE | Requires social/energy/health evidence and downstream outcome model; not a current blocker-search priority. |
| Q-B01-005 | B01 | MEDIUM | OPEN | LATER_MODEL_COMPUTE | Requires annual integrated readiness/CAPEX/system model. |
| Q-B10-001 | B10 | CRITICAL | OPEN | CONTINUE_EXISTING_FIRST | Attribution contract and baseline examples exist; real programme-demand mapping/reinforcement/CAPEX remains after upstream household allocation. |
| Q-B01-006 | B01 | CRITICAL | OPEN | OWNER_POLICY_DECISION | Objective function and hard minima are policy choices to be stress-tested, not facts to discover on the web. |
| Q-B12-001 | B12 | HIGH | OPEN | LATER_MODEL_COMPUTE | Needs archetype CAPEX, financing and cash-flow inputs from upstream modules. |
| Q-B10-002 | B10 | HIGH | OPEN | CONTINUE_EXISTING_FIRST | Timing contract and two real project examples exist; expand/validate cohort only after using current evidence. |
| Q-B06-001 | B06 | HIGH | OPEN | LATER_MODEL_COMPUTE | Lifecycle phase-order optimisation depends on B06 CAPEX plus B05/B12 inputs. |
| Q-B13-001 | B13 | CRITICAL | OPEN | LATER_MODEL_COMPUTE | Requires completed B12 and upstream price/physical ledgers. |
| Q-B01-007 | B01 | CRITICAL | OPEN | OWNER_POLICY_DECISION | Social minimum is a policy constraint informed by evidence, not an empirical value the model may choose autonomously. |

## Search queue

Questions classified `TARGETED_EXTERNAL_SEARCH` are the genuine evidence-search queue. They should not all be attacked at once; dependency order applies.

### Immediate upstream order

1. Q-B02-004 — first exhaust existing emitter/temperature evidence; then search only the residual gaps.
2. Q-B02-001 — compute national technical-suitability distribution after Q-B02-004 and exclusion rules.
3. Q-B01-001 — bind technical stock to legal/programme eligibility.
4. Complete remaining B03/B04/B05 upstream critical inputs.
5. Only then spend effort on B08-B10/B11 and later B12-B19 quantities that depend on them.

## Search consolidation

Some nominally separate questions should be researched as one evidence track:

- Q-B04-001 + Q-B07-001 — H-tariff/battery/VPP legal and metering boundary;
- Q-B03-002 + Q-B03-004 — licensed TTF data channel and actual numeric export;
- Q-B08-001 + Q-B09-001 — ENTSO-E reuse/snapshot/regionalisation boundary;
- Q-B02-004 + P42 radiator-stock chain — emitter prevalence, quantity/type and temperature distribution.

## Next action

B02-P50 closes Q-B02-002 from existing canonical evidence. The next active blocker is Q-B02-004 because it is CRITICAL, upstream of Q-B02-001, and already has substantial evidence in P39 and P44-P49 that can be re-used under the new population-inference policy before any new web search.
