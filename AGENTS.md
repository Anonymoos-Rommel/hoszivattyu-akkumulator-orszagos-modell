# Repository agent instructions

These instructions apply to the entire repository.

## Authority

- Joseph is the repository owner and final decision authority.
- Aion may define architecture, research scope, and methodological constraints.
- Codi may research, implement, test, document, and publish only within Joseph-authorized scope.
- Do not merge, publish a release, change visibility, change repository permissions, or broaden scope without Joseph's explicit instruction.

## Git workflow

- After the authorized bootstrap commit, do not push directly to `main`.
- Use `agent/<short-description>` branches.
- Open a Pull Request with module, scope, sources, formulas, tests, and downstream impact.
- Bind approval to the current head commit. A later head change requires renewed review.
- Do not force-push shared branches or rewrite published history.

## Research integrity

- Prefer P1 official and P2 primary market sources.
- Record retrieval date and reference period for web data.
- Label every material number as `OBS`, `DER`, `ASS`, `SCN`, `POL`, or `Q`.
- Never invent a missing value. Create a `Q` record with an acquisition or measurement plan.
- Keep wholesale/import valuation separate from household retail prices.
- Keep baseline and incremental program effects separate.
- Prevent double counting across household, fiscal, import, financing, and macroeconomic benefits.

## Source evidence preservation and history snapshots

- Treat important external source documents as durable evidence, not disposable browsing context.
- Code, registries, tests, and documentation must reference a stable `source_id`; do not hard-code external PDF filenames or repository snapshot paths as the semantic authority.
- For each material external document, preserve or extend machine-readable provenance containing, where applicable: `source_id`, `original_url`, `retrieved_at`, `document_date` or revision, `authority`, `repo_snapshot_path`, `sha256`, and `reuse_status`.
- When redistribution/republication rights are explicitly cleared, preserve the exact retrieved source document byte-for-byte under an evidence/history location such as `evidence/history/<source_id>/`. Do not silently replace an archived snapshot when the publisher changes the source; store a new revision/snapshot and preserve lineage.
- A repository snapshot is historical evidence of what was inspected. Its presence does not by itself make that revision the current authority; claim-specific currentness and reference period must still be evaluated separately.
- When public-repository redistribution/reuse is not explicitly cleared, do **not** commit the external document bytes. Preserve the `source_id`, canonical/original URL, retrieval timestamp, document/revision identity, available hash or digest, claim scope, and a fail-closed reuse status such as `REPOSITORY_COPY_NOT_CLEARED` / `EXTERNAL_ONLY`.
- A dead or changed external URL must not erase the evidence lineage. Existing hashes, document identifiers, retrieval metadata, source-pack notes, and any lawfully retained snapshot remain part of the audit trail.
- Never use base64 or transformed text dumps as a workaround for an uncleared binary-document redistribution restriction.
- If the tooling available to an agent cannot commit binary files, the agent may still create/update the provenance manifest and code references, but must leave the binary snapshot as an explicit acquisition step for an authorized local/Codex workflow rather than fabricating an archive.

## Model integrity

- Modify canonical inputs and formulas, not generated outputs.
- Declare units at every interface and test dimensional consistency.
- Preserve the dependency order recorded in `registry/module_status.csv`.
- B15 must not start before B12, B13, and B14 satisfy their gate.
- Do not implement a final application before B01-B19 contracts are stable and B20 is approved.

## Public-repository safety

- Do not commit secrets, credentials, personal data, unreviewed internal material, or copyrighted/external source documents whose public redistribution/reuse has not been explicitly cleared.
- The two local DOCX source files are explicitly excluded from Git until Joseph approves a public version.
- Treat external Pull Requests as untrusted input. Do not expose secrets to fork workflows.
