# V1-018 — B14 dated KEHOP funding-rule reference

Research/readback date: **2026-10-01**. Admission: **bounded E1 reference only**.
Slice: B14-L01, with a limited original-envelope control relevant to B14-D01.
B14-D01 current balances and B14-D02 research-financing fit remain open. This does
not start B15, qualify a household, choose policy defaults or compute financing.

## What is admitted

Two explicit programme/scope references:

- KEHOP Plusz-4.1.7-24: outside-Budapest family-house rules
- KEHOP Plusz-4.1.8-24: Budapest family-house rules

Both current MFB pages show intake suspended for envelope exhaustion. Exact
one-page official notices preserve the last-submission **date**, through branch
closing: 2026-04-17 for Budapest and the 4.1.7 central/western bucket;
2026-04-23 for the four less-developed regions. No clock time is invented.

The official document lists currently select calls effective **2025-10-15**.
Their nominal 2027-03-30 submission deadline is subordinate to the later intake
suspension. A summary-page accordion containing March 31 is not used to override
the exact call. The 4.1.8 nominal dates are on II/4 p8; the 4.1.7 dates are p7.

The September 2026 operational FAQ establishes a dated uncertainty/processing
state: pre-suspension applicants may be approved, waitlisted or rejected;
waitlisting can reflect eligibility without resources at decision time; confirmed
information about extra funding and a successor is unavailable in that FAQ.
These are not zero balances, universal payment refusals, or a claim that no future
programme can exist. The PDF gives a month, not an exact effective day.

## Numerical and accounting boundaries

Every curated rule fact has a source ID, locator, unit and `POL` label. Literal
source caps are `POL`; the material-plus-labour cap sum is `DER`. Dated live intake
status is `OBS`. Unknown monetary quantities stay null with `Q`.

- Original finance envelopes: HUF66.82bn for 4.1.7 and HUF6.19bn for 4.1.8
- Financing bounds: HUF2.5m–10m combined grant plus loan
- Grant share: 50% **of financing**, not total project cost
- Minimum own-source share: 5% **of eligible project cost**; call example at
  maximum financing is HUF526,316
- HUF10m is not a universal eligible-total-cost ceiling. Additional eligible
  costs can require extra own funds; no universal total-cost number is invented
- Loan term is stored in source-native **15 years**, explicitly including
  availability and grace, rather than silently relabelling a conversion as OBS
- Execution is at most 24 months, with one justified extension up to six months;
  availability extension is also conditional. Final programme payment date is
  2029-11-30. These are terms, not forecast cash-flow dates

Remaining, application-reserved, committed, paid, confirmed-project-grant,
university/pilot and new national-allocation amounts remain separate nulls.
No method aggregates envelopes into available money or computes grant receipts.

The 39-row cap table applies only to the inspected **4.1.7** structural-rule
scope. Gross material/labour values preserve HUF/m2 versus HUF/set and the source
package/variant. These are eligible-unit-cost ceilings, not market prices,
expected CAPEX or national averages. They are not automatically transferable to
4.1.8. Appendix 1 pp21–23 was visually reviewed; all 39 component pairs/units were
also independently source-reviewed during preparation.

Preparation, HET, advice and other-cost limits are nested/overlapping, not
additive entitlements. The snapshot retains source-native denominator, maturity,
conditional-extension and nested-cap qualifications.

## Record-level boundaries retained

Applicant, occupied property, location, pre-2007 definition, HET/product/technical
compliance and cumulation require record-specific evidence. A structural scope
label is not household eligibility. No stock-wide eligibility percentage is
inferred. Household calls do not establish university/pilot or national-programme
funding.

Cumulation labels preserve prior-aid building/beneficiary restrictions and their
stated PV-only exception, same-cost-line EU aid prohibition, invoice endorsement,
optional written HEM compensation, no cash-plus-HEM for the same advice, and the
maximum one HEM-generation agreement. The procedure's invoice-endorsement locus
is section 10.8.2, **PDF p40 / printed p39**. Source locators and exact documents
remain necessary for any later record-level review.

## Source identity and rights

Eleven primary-source pins are in
`registry/b14_funding_reference_manifest.json`: two calls, common procedure,
September FAQ, two live MFB status pages, two current official document lists,
and three official suspension PDFs. Exact source bytes remain external-only.
The manifest contains public URLs, revision/date metadata and SHA-256; it does
not contain source text dumps, private paths or document bytes.

Preserved stable call IDs:

- `SRC-B06-HU-KEHOP-417-COMPLETION-2025`
- `SRC-B02-HU-KEHOP-418-COMPLETION-INDICATORS-2025`

The first also records the existing cost-source alias
`SRC-B02-HU-KEHOP-417-MAX-COST-2025`. Official bytes equal the historical mirror
bytes, so mirror-to-primary origin repair does not create independent samples or
erase lineage. Public redistribution/reuse clearance remains absent.

Official acquisition URLs:

- [4.1.7 call](https://www.palyazat.gov.hu/api/download/68ee54b32d31a0de426eb2d3)
- [4.1.8 call](https://www.palyazat.gov.hu/api/download/68ee51cc26c1f4c8b489352d)
- [Common procedure](https://www.palyazat.gov.hu/api/download/68ee54b3a98fefdd172249e0)
- [September operational FAQ](https://www.mfb.hu/backend/documents/KEHOP-PLUSZ-Otthonfelujitasi-Program-GYIK-20260901.pdf)

## Read-only consumer

`modules/B14/funding_reference.py` loads digest-bound curated JSON/CSV and returns
immutable references. Every read requires explicit programme, scope, exact
`as_of="2026-10-01"` and claim type. Numeric facts also require native units;
cap reads require gross VAT basis. Different/current/future dates, unknown
programme/scope, availability or award claims, cap-as-price, currency/unit
conversion and Budapest cap transfer are rejected.

Permitted operations are `read_programme`, `read_fact`, `read_intake`, and
`read_cap`. There is no household-approval method, financing calculation,
inflation/FX normalisation, adoption rule, grant default or national aggregation.

## Verification and reproducibility

Focused checks:

```sh
python -m unittest discover -s tests -p 'test_b14_funding_reference.py' -v
python tools/verify_b14_funding_reference.py
python -m compileall -q modules/B14 tools/verify_b14_funding_reference.py tests/test_b14_funding_reference.py
```

Result: **24 tests passed**. The no-source verifier validates the pinned curated
snapshot and explicitly reports external-source verification as **NOT_RUN**.

For full local source checking, pass all eleven explicit bindings:

```sh
python tools/verify_b14_funding_reference.py --source SOURCE_ID=/local/exact-source-file ...
```

The verifier performs no network I/O. In this preparation run, all eleven exact
external sources passed hash/byte-length verification plus **113** targeted
numeric/date/locator checks. Finance parsing checks source envelopes, financing
limits and ratio rules; 4.1.7 cap component amounts are checked in the appendix.
Source-table column/package interpretation is explicitly still manual review,
not something the presence-of-number check proves. The official document lists
are bound to the exact call download IDs/sizes/versions.

The tests cover scope/date/claim refusal, Q-null preservation, unsupported
numeric reads, denominator separation, nested caps, maturity and extension
qualifiers, source lineage/rights, immutable returned data, changed-file/content
bindings, malformed numbers, and rejecting semantic mutations even when record
bindings are recomputed. This focused pass is not a claim that the entire
repository test suite was run.

## Integration state

The shared source registry retains the three existing source pins and the
maximum-cost same-document alias. It now records exact official origins and
hashes while preserving historical mirror URLs, retrieval dates and source notes.
Eight genuinely new source pins are added; duplicate call copies are not counted
as independent evidence.

B14 now has a read-only reference README and an `IN_PROGRESS` module status,
with readiness unchanged at zero because no module-wide recalculation was
performed. B14-L01 is `INTEGRATING`, not accepted as complete: this intake covers
two household calls only. B14-D01 and B14-D02 remain open and B15 stays gated.

Independent review passed on the eight-file candidate: 24 focused tests, all
11 source hashes/lengths and 113 targeted checks. All 39 cap rows were separately
matched to visually inspected source pages. Final shared integration and full
repository verification are recorded in `V1_018_VERIFICATION.json`.

## Remaining concrete lead

A dated official financial reconciliation by programme/regional bucket is needed
for current allocation, application reservation, signed commitments, payments,
cancellations and residual. A project grant additionally needs its own decision,
contract and disbursement evidence. Official reopening/amendment or successor
calls would require a new reviewed snapshot. This reference cannot fill those
unknowns or relax any gate.

## Canonical-byte follow-up

The first publication exposed a CRLF/LF mismatch between the cap CSV's original
working bytes and the repository's canonical `.gitattributes` LF contract. The
39 parsed cap records were unchanged. The manifest now binds the canonical LF
bytes and a regression test checks the curated files' LF/hash contract. The
final focused suite has **25 tests**. Full verification requires the corrected
published head's hosted CI; earlier local aggregate runs were resource-killed,
not passing or failing assertions.
