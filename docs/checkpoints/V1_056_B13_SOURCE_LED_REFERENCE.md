# V1-056 — separately qualified source-led fiscal baseline

## What this handoff completes

The original B13-D01 requirement is a Hungarian central/general-government
baseline by year: HUF revenue/expenditure, GDP, debt, interest and relevant
energy-price compensation, with cash and accrual kept separate. All these
native fields are available in the **14 exact original artifacts already
selected by V1-026**. They have now been reacquired with every previous SHA-256
and byte-count pin intact. Their total size is 15,530,865 bytes.

The previous 33,870-byte normalized JSON and its private normalizer were not
recovered. Source hashes cannot reveal their missing text metadata or serialized
numeric lexemes. This revision therefore supplies a **new, separately identified
source-led reference**, not a claim to have recovered that old file or reproduced
all its old serialized values. At this first-stage boundary B13-D01 is
`REVIEW_REQUIRED`; acceptance requires exact independent consumer review and
actual hosted verification before the separately approved metadata step.

## Exact originals, new qualification

The sources are the Treasury closing statement and earlier monthly workbook;
KSH EDP workbook, detailed quarterly accounts, annual GDP, seasonally adjusted
GDP and inventory; official MVM ESEF archive and auditor statement; the pinned
budget annex and four quarterly compensation orders. The source IDs, original
URLs, byte identities and old retrieval lineage remain. Reacquisition dates and
new witness/normalization lineage are separately recorded.

The new private panel contains 51 records: 50 numeric values and one genuine
blank. Its identity is 47,934 bytes, SHA-256
`e61832ed2546175a93b4f63b3660887119ad96c244d42f2455a2733a3e27a5c7`.
The public manifest contains metadata, source locators and pins only; it does
not publish the numeric panel, raw originals or full source extracts.

The private deterministic normalizer rereads those exact originals. It extracts
PDF table glyphs at documented rows/columns, cached OOXML cell lexemes, logical
CSV records, the selected XHTML report member and dated decision clauses.
Quantity/normalization/notes are newly authored and explicitly described as
such. The normalizer's exact code and per-record derivation ledger are privately
preserved. The consumer never executes that external normalizer.

Independent extraction checks every record against the original sources.
All five author outputs reproduce byte-for-byte, and all 32 controls are
independently recomputed: 26 PASS, five retained diagnostics and one unresolved
recipient/order difference. These are accounting checks, not unit-test counts;
not all controls are asserted to equal zero. The unresolved difference does not
establish an available budget or one-HUF economic precision.

## Accounting, precision and source-role boundaries

- The legal central cash subsystem is distinct from consolidated ESA S.13 and
  its subsectors. Internal cash flows are not silently consolidated.
- Treasury original, modified and actual columns are separately witnessed.
  The closing statement is not presented as enacted final-account legislation;
  the earlier monthly workbook remains historical provisional evidence.
- EDP 2025 is half-finalized; the 2026 planned column remains excluded.
  Annual unadjusted GDP is the denominator reference; seasonally adjusted GDP
  is a separate diagnostic, not a substitute chosen to close a residual.
- Debt and accrued recipient assets remain stocks. Cash interest, ESA interest,
  appropriation instructions and recipient cash are different quantities.
- The actual public-utility-support aggregate is observed in the Treasury's
  closing column. The institutional reserve's blank remains Q/E3, not zero.
  Native EDP M and L flags retain distinct meanings and are never numeric fills.
- Source-led workbook values retain native Decimal values exactly. No Python
  float normalization is used. The legacy reader's serialization tolerance
  remains for the old reference; it cannot be used to approximate new direct
  source values. Native decimal tails do not imply extra economic precision.
- CSV rows 107–110 mean one-based logical CSV records, not physical text lines;
  the arithmetic consumer selects the four distinct 2025 quarters by labels.
- MVM's reported integer-million-HUF receipts and accrued assets are recipient
  corroboration. The rounding rule is unspecified. Quarterly orders are
  transfers/payment instructions, not proof of exhaustive actual payments.
  Their funds-availability and deadline conditions remain explicit.

## Budget-annex correction

The exact pinned annex visibly contains the reference-year table and its named
fund row, but its historical legal-effective/original-enacted revision is not
independently established. Its numerical agreement with another source would
not prove legal effectivity.

The new record is therefore `REZSI_ANNEX_PUBLISHED_ENVELOPE`, with
`pinned_annex_appropriation_context`, `DESCRIPTIVE_PINNED_ANNEX_CONTEXT` and an
explicit unverified legal-effectivity status. The old record ID is lineage only.
The operative source description and document-date field carry the same limit;
the old source descriptions are retained only as labelled history. The central
source register describes an observed pinned document, not an operative policy
entitlement. The legacy manifest itself is unchanged.

## Explicit selection, no silent legacy replacement

The new reference ID is
`B13-D01-FISCAL-BASELINE-REFERENCE-SOURCE-LED-20261003`.
`read_fiscal_reference(..., reference_id=...)` and the materializer's
`--reference-id` select it explicitly. Omission preserves the legacy V1 contract,
which still requires its own exact old panel and originals. A new panel does not
silently satisfy the legacy pin. Unknown selectors, changed manifests, source
bytes or panels fail closed. Results and receipts expose the selected identity.

The new entrypoint uses the same 32 accounting controls and storage boundary.
The canonical old manifest remains byte-identical. No actual headroom,
programme cashflow, fuel/household/VAT/service-year allocation, reinvestment
policy, grant award or B15 admission is added. B13-D02 and B13-P01 remain separate;
module status, readiness and dependencies are unchanged.

Example from the repository root, with the exact privately preserved inputs:

```sh
python tools/materialize_b13_fiscal_reference.py \
  --reference-id B13-D01-FISCAL-BASELINE-REFERENCE-SOURCE-LED-20261003 \
  --panel /private/b13/source_led_observations.json \
  --source-map /private/b13/source_paths.json \
  --output-dir data/interim/b13_source_led_reference
```

The output must be fresh, ignored and untracked in the intended checkout, or
properly isolated external storage. The existing symlink, other-checkout,
linked-worktree, Git-index and overwrite guards are unchanged. Originals and
numeric records remain private even when they are publicly reported statistics.
The original D01 criterion does not acquire a new requirement for exhaustive
recipient/fuel allocation or owner policy decisions; those remain explicit
limits on later programme claims.
