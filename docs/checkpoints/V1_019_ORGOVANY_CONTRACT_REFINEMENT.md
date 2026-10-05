# V1-019 — Orgovány I signed-contract refinement

## Result and boundary

The existing B10-D02 observation `B10-REF-TED-438132-2026-LOT-0001`
now carries a reviewed supplement from the signed Orgovány I contract and
aggregate priced bill. There are still seven observations and four procurement
clusters. The supplement belongs only to `EKR001158812025`, LOT-0001, Orgovány I
piactér. It creates no additional independent sample and does not change other
lots' unknowns.

These observations alone do not populate an admissible national cost base;
national applicability remains insufficient. Existing Q-B10-001/Q-B10-002 and
the project's E2 representative-inference route retain their existing meaning.
No installed-total, programme-incremental, national-weighting, inflation or
actual-cashflow input is admitted.

## Reviewed facts

| Fact | Status | Value and source |
| --- | --- | --- |
| Base net lump sum | OBS | HUF 59,982,087; contract p4 IV.1, agrees with existing TED award |
| Reserve included in base | OBS | False; contract p4 IV.1 |
| Conditional reserve authorization | OBS | HUF 5,998,208, described as 10%; p5 IV.4 |
| Native `anyag` column total | OBS | HUF 42,667,980; priced bill pp1–3 |
| Native `díj` column total | OBS | HUF 17,314,107; priced bill pp1–3 |
| Priced-bill net total | OBS | HUF 59,982,087; priced bill pp1–3 |
| Latest visible signing date | OBS | 2026-06-10; contract p27; signature cryptography not tested |
| Handwritten bill cover date | OBS | 2025-12-02; priced bill p1 |
| A / B route headers | OBS | 147.62 m / 12 m; priced bill pp4–6 |

The two column totals reconcile exactly to the same base package (DER
addition). They are not additional costs. The printed reserve is preserved
exactly: multiplying the base by the printed percentage would not reproduce its
integer amount. No base-plus-reserve cost or spending forecast is exposed.

Reserve use requires necessary extra/variation work, technical-inspector
proposal, written justification, client consent, itemized settlement and a
separate invoice (VIII.7, pp12–13). The ministerial-opinion provision is marked
inapplicable by footnote 3 on p12; it is not an extra prerequisite.

The bill cover date is an observation. Calling it a preparation date would be
an interpretation; neither establishes the economic price-fixation date. June
2026 remains the nominal contract period, without a claim that all underlying
prices were freshly quoted then.

The `anyag` column also contains rental and supervision services. Neither native
column is a clean material/equipment/labour bucket for inflation adjustment.
Major hardware has positive contractor priced-bill allocations, but the complete
purchaser/free-issue responsibility schedule is unknown. The incorporated
technical specification was not acquired as a substantive document. A
crosshatched cell means no separately printed price; it proves neither zero cost
nor free-issued supply nor inapplicability.

The rounded TED cable length remains 148 m (OBS), with the bill route header
stored separately. Route, single-core installation, cable-pulling and equipment
cable quantities are different denominators. No generic per-metre or
three-phase conversion is permitted.

## Conditional timing and payment

Contractual observations are retained with their conditions and native units:

- Site handover within 5 working days of effectiveness; final deadline at most
  180 calendar days after handover (III.1 and VII.2–3, pp3 and 9)
- Telecontrol/protection/operational integration by 30 days before the final
  deadline (VII.3, p9)
- Effectiveness depends on the funding/notification alternatives in III.2,
  pp3–4; signing alone does not establish their fulfillment
- One base invoice after certified performance; base settlement is lump sum
  without later quantity/value remeasurement (VIII.1–2, p11)
- Advance may be requested after effectiveness and no later than handover;
  payment is due on the 30th day after request issuance, with final-invoice
  reconciliation. No numerical advance amount or actual advance is admitted
  (VIII.3, p11)
- Invoice issuance within 8 calendar days after the signed performance
  certificate (VIII.4, p11)
- The simple 30-day invoice-payment branch applies only without subcontractors.
  The contract identifies subcontractors and specifies a separate statutory
  branch (VIII.10, p13); no unconditional payment schedule is inferred

Economic price base, normalized costs, actual reserve use, advance, payments,
effectiveness, handover, completion, annual cashflow, complete free-issue
responsibility and national attribution remain null.

## Sources and public reuse

The original TED snapshot retains its own source identity. Supplement facts
carry separate source IDs and page/clause locators, using the public
[EKR contract record 1204237 / SZ0176453](https://ekr.gov.hu/ekr-szerzodestar/hu/szerzodes/1204237).
The manifest binds these external-only source hashes:

- `SRC-B10-V1-EKR-SZ0176453-CONTRACT-20260610`:
  `b8758ef8984a049d5278e4e4bef43796c6833d6c992a9e15cfdf867834314a35`
- `SRC-B10-V1-EKR-SZ0176453-ANNEX-BUNDLE-20260722`:
  `b4b36a93665d583abb63f8242f6724a6d22f9df5190c973ad603396d80f430a3`
- `SRC-B10-V1-EKR-SZ0176453-BOQ-20251202`:
  `c7d5321c1871ce74060e924fee522d6c95a93822f463a63b3e825a199b88d86b`

The public numeric facts are limited to independently reviewed nonpersonal
aggregates, conditions and scope cautions. No source PDF/ZIP bytes, signature,
contact, bank details, substantial annex copy or granular component-price table
is admitted. Granular offer-annex reuse awaits a separate publication decision;
this is not a blanket finding that all price facts are confidential. Source
availability alone was not treated as a republication license.

## Consumer and verification

`load_reference_catalog()` preserves the original `read()` and bounded `derive()`
contract. `supplement()` exposes immutable reviewed conditions for this lot only;
`read_supplement_fact()` requires the native unit and price basis and returns the
fact's own signed-contract or priced-bill source. Every new numeric fact is OBS.
Conditional reserve, date and column semantics are explicit. Other lots cannot
receive this supplement through a generic optional schema extension.

Validation binds the canonical LF data bytes, record digests, exact source set,
archive lineage, per-fact source/unit/role, null unknowns and bounded uses.

- `python -B -m unittest tests.test_b10_cost_reference -v`: 31 tests passed
- Four external TED PDFs: exact hashes and 12 numeric row checks passed
- Signed contract: exact hash, 3 printed-number checks and explicit reserve
  exclusion passed
- Annex archive and scanned bill: exact hashes and selected archive-member
  lineage passed; scanned aggregate values rely on prior visual source review,
  not a claimed automated OCR re-extraction
- Canonical LF bytes agree with Git filtering; manifest data digest verified
- No full-suite result is claimed for this checkpoint

The verifier's optional `--supplement-source SOURCE_ID=FILE_PATH` accepts the
three external source bindings together. It reads local bytes only and does not
acquire, publish or execute the supplied documents.
