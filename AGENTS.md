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

## Model integrity

- Modify canonical inputs and formulas, not generated outputs.
- Declare units at every interface and test dimensional consistency.
- Preserve the dependency order recorded in `registry/module_status.csv`.
- B15 must not start before B12, B13, and B14 satisfy their gate.
- Do not implement a final application before B01-B19 contracts are stable and B20 is approved.

## Public-repository safety

- Do not commit secrets, credentials, personal data, copyrighted source documents, or unreviewed internal material.
- The two local DOCX source files are explicitly excluded from Git until Joseph approves a public version.
- Treat external Pull Requests as untrusted input. Do not expose secrets to fork workflows.
