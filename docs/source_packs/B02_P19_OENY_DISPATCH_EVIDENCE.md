# B02-P19 — OÉNY dispatch evidence correction

**Status:** `REQUEST_SENT / AWAITING_RESPONSE`

**Dispatch date:** 2026-08-22 10:31 Europe/Budapest

## Purpose

This source pack records a factual correction to the repository's current OÉNY request state. The P1L pre-send package and attached request letter are preserved as historical preparation-time artefacts; their embedded `NOT SENT` / `NEM KÜLDÖTT` labels describe their state before dispatch and are not rewritten retrospectively.

## Dispatch evidence

A complete `.eml` message exported from Outlook was supplied by Joseph and verified as the sent message object.

- recipient: `info@lechnerkozpont.hu`
- subject: `Kérelem legfeljebb 500 rekordos, anonimizált OÉNY energetikai pilot-adatkészlet megismerésére`
- message date header: `Sat, 22 Aug 2026 08:31:17 +0000`
- normalized local dispatch time: `2026-08-22 10:31:17 Europe/Budapest`
- attachment 1: `P1L_FINAL_OENY_REQUEST_LETTER.md`
- attachment 2: `P1L_FINAL_ATTACHMENT_1_REQUESTED_FIELDS.md`
- local EML SHA-256: `f8ae92f94ae37b7760a1770377eec08c2ec6bb2f14376cec8484a9d9454a3742`
- EML byte size: `24382`
- evidence class: `PRIVATE_EXTERNAL_EVIDENCE`
- public-repository storage: `NO`

The full EML is intentionally excluded from the public repository. It is stored separately in private user-controlled storage. The public repository keeps only the minimum metadata and cryptographic fingerprint required to support the dispatch fact.

## Canonical correction

`PRE-SEND ARTEFACT STATE != ACTUAL DISPATCH STATE`

The current OÉNY request state is therefore:

`REQUEST_SENT / AWAITING_RESPONSE`

This evidence proves dispatch of the email and attachments. It does **not** by itself prove delivery acceptance, case registration, processing, response, or data availability at Lechner.

## Scope discipline

No readiness evidence is promoted by this correction. No B02 eligibility/readiness blocker is closed. B02 readiness remains unchanged until an authoritative Lechner response or other admissible evidence is received.
