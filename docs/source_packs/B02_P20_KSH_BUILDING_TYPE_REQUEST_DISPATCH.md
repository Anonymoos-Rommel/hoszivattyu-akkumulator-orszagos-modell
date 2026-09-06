# B02-P20 — KSH building-type data request dispatch

**Status:** `REQUEST_SENT / AWAITING_RESPONSE`

**Dispatch date:** 2026-09-06 08:48:17 Europe/Budapest

## Purpose

This source pack records the dispatch of the targeted KSH request defined by the B02-P16 direct closure path for current building-type authority.

The request asks KSH for an anonymized / disclosure-controlled aggregate based on the 2022 Census occupied-dwelling stock, with building type jointly tabulated with the WBL-compatible housing dimensions already used by B02.

## Dispatch evidence

A complete `.eml` message exported from Outlook was supplied by Joseph and verified as the sent message object.

- recipient: `nepszamlalas@ksh.hu`
- cc: `tajekoztatas@ksh.hu`
- subject: `2022. évi népszámlálás – egyedi aggregált lakásállományi adatösszeállítás iránti igény`
- message date header: `Sun, 6 Sep 2026 06:48:17 +0000`
- normalized local dispatch time: `2026-09-06 08:48:17 Europe/Budapest`
- local EML SHA-256: `657380dcfa2f367f2cbcef67c2467f255636b21a1ebb2aa7d76d220cc6697d11`
- EML byte size: `21131`
- evidence class: `PRIVATE_EXTERNAL_EVIDENCE`
- public-repository storage: `NO`

The complete EML is intentionally excluded from the public repository and stored separately in private user-controlled storage. Only the minimum dispatch metadata and cryptographic fingerprint are recorded here.

## Requested aggregate

Requested reference year: `2022`.

Requested universe: occupied dwellings, using the appropriate 2022 Census occupied-dwelling filter.

Requested joint dimensions:

1. county / Budapest;
2. settlement type;
3. construction year or construction period;
4. wall material;
5. floor area / floor-area category;
6. comfort category;
7. heating mode;
8. heating energy carrier / fuel;
9. building type.

Requested measure: dwelling count.

For building type, the minimum useful distinction is a reproducible split between dwellings in family houses and dwellings in multi-dwelling / condominium buildings; a more detailed source-native KSH taxonomy is also acceptable.

The request also asks for variable names, category codes, suppression/aggregation methodology, delivery format, price if applicable, reuse/attribution terms, and explicit clarification on whether the delivered aggregate may be included in a public reproducible GitHub research repository.

## Canonical effect

`REQUEST DISPATCH != DATA RECEIPT != DIRECT-LINK AUTHORITY`

The request directly targets the current blocker:

`NO_CURRENT_BUILDING_TYPE_LINK_AUTHORITY`

but does not close it. Until KSH returns an admissible aggregate or other qualifying evidence, the current-stock archetype remains `Q`.

OÉNY remains separately `REQUEST_SENT / AWAITING_RESPONSE` under B02-P19.

## Current state

- `Q-B02-001`: OPEN;
- `Q-B02-002`: OPEN;
- `Q-B02-004`: OPEN;
- current-stock archetype: `Q`;
- technical-readiness archetype: `Q`;
- national technical/final eligible count: blank / `Q`;
- B02 readiness: **55%**;
- no readiness uplift.
