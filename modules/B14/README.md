# B14 — Dated funding-rule references

Status: **IN_PROGRESS; read-only named-programme references**. This package does
not calculate financing or qualify a household. B15 remains gated on completed
B12/B13/B14 output contracts.

`funding_reference.py` preserves the exact **2026-10-01** reference and adds a
separately sourced **2026-10-03** completion for the two KEHOP household calls.
Both dated observations show suspended intake. Original envelopes are neither
available balances nor confirmed grants. Loan/grant/own-source denominators,
conditional extensions, nested caps, HEM restrictions and record-level checks
remain explicit. Unknown financial quantities remain null/Q.

Permitted reads are `read_programme`, `read_fact`, `read_intake`, and `read_cap`.
Each requires programme, structural scope, exact admitted as-of and claim. Numeric
facts require native units; caps require gross VAT basis. Historical reads and
all three historical data/manifest files remain unchanged. The October 1 view
admits only its original 39 outside-Budapest cost-cap rows. The October 3 view
also admits 39 independently source-bound Budapest rows and returns detailed
issuer/cumulation/PV-exception/HEM conditions, fresh observation identities and
prior-review reliance. Programme-rule details are POL; the separately dated
observations are OBS. A row cannot transfer across programme, scope or date.

These are eligible-unit-cost ceilings, never market prices, financing results or
automatic eligibility. Current/future availability and award claims are refused.
Neither a PV-only prior-support exception nor an original programme envelope
admits a new funding source. No household approval method is implemented.

Historical provenance: [`b14_funding_reference_manifest.json`](../../registry/b14_funding_reference_manifest.json)
and [V1-018](../../docs/checkpoints/V1_018_B14_FUNDING_REFERENCE.md).
Completion bindings: [`b14_rule_completion_manifest.json`](../../registry/b14_rule_completion_manifest.json)
and [V1-054](../../docs/checkpoints/V1_054_B14_RULE_COMPLETION.md).
Raw originals remain external-only. Exact mirror equality is lineage, not a new
independent sample. The procedure and historical notice bytes were not freshly
recovered; those claims explicitly reuse V1-018 review, without inventing a new
all-eleven-source check. New observations do not establish individual eligibility.

## Verification

- `python -m unittest discover -s tests -p 'test_b14*.py' -v`
- `python tools/verify_b14_funding_reference.py` validates the historical reference;
  without all eleven exact old source bindings it reports external checking NOT_RUN.
- Completion loading verifies its own new file/source-record/cap bindings and
  unchanged historical file identities. Its source qualification is separate
  from consumer checks and hosted CI.

## Acceptance boundary

The V1-054 first-stage handoff records B14-L01 as REVIEW_REQUIRED. Any later
acceptance is recorded separately in the registry and, when executed,
`docs/checkpoints/V1_054_ACCEPTANCE.json`, bound to the actual reviewed commit.
The original named-rule fields are complete; the old generic broader-programme
interpretation is explicitly reconciled in V1-054. B14-D01 balances/assignments,
B14-D02 university/pilot fit, all individual approvals, later programme revisions,
whole B14 and B15 remain open. No module readiness increase is claimed.
