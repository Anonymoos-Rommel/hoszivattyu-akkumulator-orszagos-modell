# PROJECT-P49 — Evidence-tier and blocker-class re-audit

**Date:** 2026-09-27  
**Canonical parent:** `33c70de5b19b4673a934ebe01affa3be1079281a`

## Purpose

This slice changes the project-wide handling of missing or non-public evidence.

The previous fail-closed discipline remains for cases where no defensible base exists, for legal/permission questions and for exact record/project claims. It is no longer correct to stop the central model merely because an exact primary report or private dataset is unavailable when existing evidence already supports one defensible provisional base.

Canonical policy:

`E1 = VERIFIED / AUTHORITATIVE`

`E2 = PROVISIONAL_BASE / VALIDATION_DEBT`

`E3 = ASSUMPTION_ONLY / INSUFFICIENT_EVIDENCE`

and:

`ONE CANONICAL VALUE PER MODEL VARIABLE`

`NO AUTOMATIC LOW/BASE/HIGH CARTESIAN PRODUCT FOR SOURCE GAPS`

## Audit scope

The live audit covers every current `OPEN` row in `registry/open_questions.csv` plus every current readiness component whose status is `Q`.

The historical `project_blocker_reaudit_2026_09_22.csv` is retained unchanged as history.

## Material reclassifications

### E2 / VALIDATION_BLOCKER — model may continue

The following current tracks have enough qualified evidence to permit a single provisional central base while exact evidence remains validation debt:

- Q-B02-004 — national physical-response / retrofit-action evidence;
- Q-B07-002 — supply-chain origin for procurement claims only;
- Q-B07-003 — battery efficiency, after one consistent system boundary is selected;
- Q-B04-002 — current 2026 H/A1 tariff base;
- Q-B05-003 — defrost accounting;
- Q-B05-004 — product transient/cycling evidence, including Mitsubishi/SZU and Dimplex/VDE acquisition debt;
- Q-B05-005 — DHW controller/high-temperature runtime coverage;
- Q-B06-010 — downstream CAPEX when monetary outputs are activated;
- Q-B10-001 — national expected network reinforcement/incremental-CAPEX inference.

These are not promoted to E1. Material exact evidence remains required for final decision-grade closure.

### E3 — still a real blocker

No provisional base is authorized where the repository still lacks a defensible central artifact or where inference is legally invalid. Examples include:

- B08 real A65 load panel;
- B09 real A75 generation panel;
- B02 national terminal technical-eligibility distribution;
- B03 market gas price/feed/retail bridge;
- H-tariff battery legal permissions;
- B10 national reinforcement-delivery timing calibration.

### Not evidence blockers

Several open items are downstream calculations or owner policy choices, not missing-source problems. They are explicitly classified as `EXECUTION_DEPENDENCY` or `POLICY_DECISION`.

B05 `PRODUCT_SCALING` is reinterpreted as a `CONTRACT_BOUNDARY`: universal linear scaling remains forbidden and does not need to be "solved".

## Single-base rule

For evidence-gap variables, a provisional central model input is a single `X_base`, selected from the strongest applicable evidence and documented with validation debt.

A missing report is not converted into independent `X_low/X_base/X_high` inputs. Genuine statistical uncertainty or source-native distributions may still be reported, but they are distinct from evidence-gap substitutions and are not automatically cross-multiplied across variables.

## Persistence

The canonical policy is `docs/methodology/evidence_tier_and_validation_debt_policy.md`.

The machine-readable current audit is `registry/project_blocker_evidence_audit.csv`.

Repository tests require all current OPEN questions and all readiness-Q components to appear in the audit with a valid E1/E2/E3 tier, preventing a future chat/window change from silently reverting the methodology.
