# B13 — fiscal baseline references

The fiscal reader supplies dated, source-specific baseline observations and
accounting controls. It does not implement programme cashflows, available
headroom, fiscal policy or B15 admission.

## Preserved legacy reference

`fiscal_reference.py` defaults to
`B13-D01-FISCAL-BASELINE-REFERENCE-V1`. Its canonical manifest and exact old-panel
pin remain unchanged. The old private normalized JSON is currently unrecovered;
source hashes alone cannot recreate it. See [V1-026](../../docs/checkpoints/V1_026_B13_FISCAL_REFERENCE.md).

## Source-led reference dated 2026-10-03

The explicit selector
`B13-D01-FISCAL-BASELINE-REFERENCE-SOURCE-LED-20261003` uses a newly qualified
private 51-record panel and all 14 byte-exact recovered originals. Native Decimal
values, the genuine blank, M/L flags, cash/accrual, stock/flow, actual/appropriation
and vintage roles remain distinct. The pinned annex is descriptive context with
unverified legal effectivity, not proof of an original enacted appropriation.

Use `read_fiscal_reference(..., reference_id=...)` or the materializer's
`--reference-id`. Omission never silently selects the new revision. Output stays
in fresh protected private storage; raw sources and numeric panels are not public
fixtures. The consumer does not execute the external normalizer. See
[V1-056](../../docs/checkpoints/V1_056_B13_SOURCE_LED_REFERENCE.md).

The 32 controls include retained diagnostics and an unresolved recipient/order
difference; they are not all zero-result assertions. B13-D01 handoff acceptance,
B13-D02 programme flows and B13-P01 owner policy are separate decisions. Module
readiness and downstream gates do not rise merely because source inputs exist.
