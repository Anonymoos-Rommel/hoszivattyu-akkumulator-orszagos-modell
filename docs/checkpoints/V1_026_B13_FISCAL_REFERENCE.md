# B13-D01 published fiscal baseline reference

This checkpoint adds a source-specific consumer for the independently reviewed
2025 fiscal baseline. It reads an exact external 51-record panel, verifies 14
selected original artifacts, and recomputes 32 arithmetic or diagnostic
controls. It is a baseline-reference handoff, not a programme fiscal engine or
a claim that B13-D02, B13-P01 or the B15 gate is complete.

## Public contract and external evidence

- `modules/B13/fiscal_reference.py` provides the strict reader, immutable
  records and reconciliation results
- `registry/b13_fiscal_reference_manifest.json` contains source IDs, original
  URLs, retrieval dates, document vintages, SHA-256/size pins, record metadata
  and interpretation boundaries; it contains no numeric observation panel
- `tools/materialize_b13_fiscal_reference.py` writes the reference and receipt
  only into fresh external storage outside Git or ignored, untracked
  `data/interim`; it refuses public repository paths, other Git checkouts,
  symlinked output and overwriting existing outputs
- `tests/test_b13_fiscal_reference.py` uses synthetic values and synthetic
  workbooks, including a complete synthetic entrypoint materialization

The reviewed external panel has SHA-256
`afa957ba0d52d78e7fa04995b87f0fbbb3bada18015edc2737895c91a6e1832a`.
The independent source review is bound by SHA-256
`70048cca66c2a44412a2985bad577432f93e1a6b3358b6306d31585981b71add`.
The external normalizer is separately pinned for lineage; the consumer does
not execute it or trust its precomputed validation file. Exact original bytes
and the exact reviewed panel are required before any output is written.

The 14 selected artifacts comprise the Treasury closing statement and earlier
monthly workbook; KSH EDP workbook, quarterly detailed accounts, annual GDP,
seasonally adjusted GDP series and EDP inventory; official MVM ESEF archive
and corresponding auditor statement; Budget Act Annex 1 and four quarterly
provider-compensation orders. Stable research source IDs already use the
`SRC-B13-` namespace and are preserved without renaming. Other acquired
sources are not silently admitted by their presence in an acquisition map.

Originals, full source extracts, the research normalizer's numeric literals,
the full normalized panel and genuine materializations remain external or
ignored. `REPOSITORY_COPY_NOT_CLEARED` describes public copying, while model
admission is explicitly limited to the bounded published-statistic reference.
This is not authorization for broader source reuse or policy conclusions.

## Values, missingness and precision

Each record retains its source IDs/hashes/document dates, original locator,
unit, nominal price basis, accounting basis, population boundary, OBS/DER/Q
status, source precision, vintage role and stock/flow/appropriation kind.
The original reviewed normalized numeric lexeme is exposed as
`normalized_value`. `value` is the exact source-native Decimal when the source
is an XLSX workbook, otherwise the pinned reviewed observation.
`native_minus_normalized` makes serialization discrepancies explicit.

No Python float conversion or source recalculation is used. XLSX cached XML
values are read as Decimal, including tiny binary-derived decimal tails in
the publisher's file. Four genuine normalized lexemes differ slightly from
native XML: provisional revenue, provisional balance, ESA S.13 B.9 and ESA
S.1311 B.9. Both representations survive materialization. These differences
are within `1e-8` million HUF, a serialization comparison tolerance rather
than claimed economic precision or a change to reviewed evidence.

The institutional reserve's actual field remains blank, with Q/E3 and no
numeric precision. An observed zero remains OBS/E1. EDP `M` (not applicable)
and `L` (unavailable) are preserved separately; no generic missing-to-zero
rule is provided. The output uses decimal strings and JSON null, so it does
not reintroduce floating-point loss or silently fill a blank.

## Accounting and vintage boundaries

The legal central cash subsystem comprises the central budget, separate
state funds and social-security funds. Its internal flows and population
cannot be treated as consolidated ESA S.13. Original and modified
appropriations, closing actuals and earlier provisional history remain
distinct even when their reference year is the same.

The October EDP workbook explicitly labels 2025 half-finalized and 2026
planned; the reader verifies both statuses and includes no 2026 planned
observation. S.1311, S.1313 and S.1314 remain distinct from their S.13 sum.
Cash interest and consolidated ESA interest are different measures. Annual
unadjusted GDP matches the independent annual source; the seasonally
adjusted GDP comparison is a retained diagnostic, never a replacement
denominator. Nominal debt and recipient accrued assets are stocks, not
programme cash expenses.

Reconciliation uses source-native bridge cells and explicit arithmetic.
Cash identities close at the displayed precision. Treasury-to-EDP working
balance differences remain visible, as do the quarterly rounding residuals
and tiny native-XML residuals; none are overwritten with zero. The maximum
rounding checks allow four million HUF for eight rounded revenue/expenditure
inputs and two million for four rounded balance inputs. Those are arithmetic
bounds, not corrections to the observations.

Quarterly compensation orders are appropriation transfers/payment
instructions. They do not establish exhaustive actual payments. MVM
consolidated IFRS receipts corroborate the recipient side, and are not an
additional government expense. A closing accrual is not added to receipts
to invent an annual ESA expense.

The published-figure receipt/order difference remains unresolved at
approximately HUF 4.593 billion. Its exact arithmetic result in the private
receipt does not establish one-HUF cash precision: MVM reports integer
million HUF, with no rounding rule inferred here. No fuel, household, VAT,
legal-recipient, service-year or prior-settlement allocation is made. No
programme savings, available headroom, reinvestment default, grant award or
B15 result is returned.

## Reproduction and verification

From the repository root, supply the exact external panel and an explicit
source-ID/path JSON object. An external acquisition manifest list with
`source_id` and `local_snapshot_path` also works; only selected IDs are used.
File basenames do not determine source identity.

Storage admission also rejects repositories and linked worktrees nested inside
the intended checkout's ignored directory. It checks `.git` metadata ancestry
and resolves the effective Git root from the nearest existing output ancestor,
so a nonexistent output tail cannot bypass the check. Outer ignore rules do
not authorize writing into another checkout, even if that checkout also has
ignore rules. Legitimate ignored storage in the intended checkout remains
valid. `reference_summary` serializes trusted reader results; callers must use
`read_fiscal_reference` for source admission rather than constructing a result
dataclass themselves.

```sh
python tools/materialize_b13_fiscal_reference.py \
  --panel /private/b13/normalized_observations.json \
  --source-map /private/b13/usable_sources.json \
  --output-dir data/interim/b13_fiscal_reference
python -m unittest tests.test_b13_fiscal_reference -v
python tools/validate_registry.py
python -m unittest tests.test_registry_contract -v
```

Focused verification passed: 33 synthetic tests, 15 shared registry-contract
tests and registry validation. Genuine materialization verified 51 records
(50 numeric and one blank), 14 selected source hashes, four retained native
lexeme differences and 32 reconciliation/diagnostic controls. The source
review independently reproduced the broader research pack's 30 raw hashes
and 24 source controls; those review counts are not presented as consumer
test counts. No full aggregate suite was run in this isolated checkout.

Revision 2 additionally passes all 12 cases of the independent storage-boundary
reproducer, including nested `.git` directories and genuine linked-worktree
`.git` files, deep nonexistent paths, symlink parents, public traversal,
external checkouts, existing outputs and legitimate ignored outputs. Public
source pins and numeric interpretation are unchanged from revision 1.

Shared sources, module status and research-plan registries are left for lead
integration. This checkpoint supplies no automatic promotion of D01 status
and changes no downstream gate.
