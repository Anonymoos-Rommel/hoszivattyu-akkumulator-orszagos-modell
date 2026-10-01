# B14 — Funding-rule references

Status: **IN_PROGRESS, dated reference only**. This package does not calculate
financing or qualify a household. B15 remains dependent on completed B12/B13/B14
contracts; this reference does not release that gate.

`funding_reference.py` binds two KEHOP household programme rules to the exact
**2026-10-01** review date. Both intakes were suspended. Original envelopes are
not available balances or confirmed grants. Loan/grant/own-source denominators,
conditional extensions, nested caps, HEM restrictions and record-level checks
are retained. Unknown financial amounts remain null/Q.

Permitted reads are `read_programme`, `read_fact`, `read_intake`, and `read_cap`.
Every call requires programme, structural scope, exact as-of and claim. Numeric
facts require source-native units; caps require gross VAT basis. The 39 cost-cap
rows apply to inspected 4.1.7 scope only, never market prices or automatic
Budapest equivalents. Current/future availability or award claims are rejected.

Provenance: [`b14_funding_reference_manifest.json`](../../registry/b14_funding_reference_manifest.json).
Detailed boundaries, source links and reproducibility:
[`V1-018`](../../docs/checkpoints/V1_018_B14_FUNDING_REFERENCE.md).
Raw official documents remain external-only; official/mirror byte identity is
lineage, not separate corroboration.

## Verification

- `python -m unittest discover -s tests -p 'test_b14_funding_reference.py'`
- `python tools/verify_b14_funding_reference.py`
- Full source verification uses eleven explicit `--source SOURCE_ID=/local/file`
  bindings. Without them the verifier reports external checking as NOT_RUN.

## Still open

B14-L01 broader programme coverage; B14-D01 dated remaining, reserved, committed,
paid and project-confirmed quantities; B14-D02 university/pilot research fit.
No amount is silently inferred from a programme page, historical envelope or
suspended intake. A later source revision requires a new reviewed snapshot.
