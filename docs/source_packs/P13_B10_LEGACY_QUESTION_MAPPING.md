# B10-P13 — Issue #10 legacy question mapping

Canonical base: `777bca6e93aefbe97486d1cd40387df32dc41f9d`

## Purpose

B10-P12 correctly failed closed on the Issue #10 acceptance text `Q-05 és Q-07 kezelve`, because the repository methodology does not allow ambiguous short `Q-xx` labels to become global canonical IDs by guesswork.

P13 resolves only that **identifier/context ambiguity**. It does not resolve the underlying network evidence questions and does not raise B10 readiness.

Core rule:

`SHORT LEGACY LABEL != GLOBAL QUESTION ID`

A legacy acceptance label is usable only when bound to:

1. the exact source document;
2. the exact source section/context;
3. the exact question semantics;
4. the exact consumer context that cites the legacy label.

## Retained source document

Internal source reviewed for P13:

`Hőszivattyú + akkumulátor országos program | Codex kutatási brief V1.1 | 2026-08-12`

The retained working document also contains the V1.2 addition dated 2026-08-16. The document explicitly reuses short `Q-xx` labels in different sections, which is why no global short-label mapping is created.

This source is used only to recover the intended semantics of the legacy acceptance labels. It adds no external numeric network fact and no OBS/DER network evidence.

## Issue #10 / Q-05

Consumer context:

`GitHub Issue #10 — [B10] Hálózatfejlesztés`

Source locator:

`V1.1 section 6 — B08 kötelező téli és nyári csúcsterhelési modell`

The local `Q-05 / VIZSGÁLANDÓ` asks what national physical peak capability should be built when the managed peak is lower, and states that the answer must be derived from network and N-1/N-2 system-security analysis.

Canonical B10 interpretation:

- `B10-P10` owns the separation between managed peak and physical network survivability;
- `NO_REAL_MANAGED_PEAK_SURVIVABILITY_STUDY` remains the substantive blocker.

Therefore Issue #10 Q-05 is **mapped**, but its underlying physical-survivability evidence is not resolved.

## Issue #10 / Q-07

Consumer context:

`GitHub Issue #10 — [B10] Hálózatfejlesztés`

Source locator:

`V1.1 section 23 — Első körös kritikus kérdések Codex számára`

That `Q-07` asks how much distribution and transmission grid investment is required regionally and in which year it becomes binding.

The canonical repository already decomposes that compound question rather than minting a duplicate B10 question:

- `Q-B01-002` — canonical regional / DSO spatial grain;
- `Q-B10-001` — baseline vs programme-incremental infrastructure and CAPEX;
- `Q-B10-002` — timing / fulfilment evidence;
- `B10-P11` — delivery milestone vs CAPEX cash-flow timing boundary.

All three canonical questions remain OPEN. P13 therefore resolves the legacy identifier mapping, not the regional investment result.

## Explicit conflict exclusion

The same V1.1 document later reuses `Q-07` in the B14 financing section for a different question: how much national programme size can actually be financed from grant sources without counting already committed or ineligible funds.

That B14-local `Q-07` is explicitly **not** the Issue #10 mapping.

This conflict is the reason the repository must never use a global dictionary such as `Q-07 -> one canonical question`.

## P12 closure effect

After P13:

- Issue #10 `Q-05/Q-07 handling` may be `ACCEPTANCE_SATISFIED` as an identifier-handling criterion;
- `LEGACY:Q-05` and `LEGACY:Q-07` are removed from the closure blocker list;
- the substantive blockers remain in their existing canonical gates;
- B10 remains `B10_CLOSURE_BLOCKED`;
- B10 remains `IN_PROGRESS` at readiness 15;
- Issue #10 remains open.

## Explicit non-results

P13 does not create or infer:

- a national managed-peak target;
- a physical survivability MW target;
- N-1 or N-2 compliance;
- a regional reinforcement inventory;
- regional programme CAPEX;
- a binding-node inventory;
- a timed programme investment path;
- national DSO coverage;
- completion probabilities;
- readiness uplift.
