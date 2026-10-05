# V1-054 — complete the two named B14-L01 rule references

The original B14-L01 fields are programme and issuer, version/geography,
eligible/excluded activity and cost, intensity/own-source denominator, cumulation,
and submission/execution deadlines. This change completes their source-to-consumer
binding for **KEHOP Plusz-4.1.7-24 and 4.1.8-24**, retaining the old reference and
adding a separately verified **2026-10-03** observation date. It does not implement
household eligibility, available funds, financing or a programme-wide census.
B14-L01 remains `REVIEW_REQUIRED` until the actual published implementation commit
has passed independent hosted verification and the approved acceptance step.

## Actual missing fields now supplied

The Budapest call's Annex 1, printed/PDF pages 21–24, supplies **39 own-source
cost-cap rows**. Its original 516,878-byte PDF matches the prior official pin
`359af1ee779eb13f64e266c79e6f91b9fae37164e69e55da9b308a7a1d178804`.
The values happen to equal the existing outside-Budapest rows, but were read from
the Budapest document, not transferred by assumption. Its source IDs, programme,
structural scope and page locators remain separate. There are four HUF/set rows
and 35 HUF/m² rows, including the explicit floor/ceiling overrides to the table's
header. Separate gross material/labour ceilings are POL; their sum is DER. These
are eligible-unit-cost limits, never a price estimate or additional entitlement.

The two exact calls now provide explicit issuer/financing-role, geography,
property/applicant-consent, activity/cost and cumulation conditions. MFB's identity
comes from the document and stated submission/credit roles, not the URL host.
Budapest II/4 spans page 7 (submission channel) and page 8 (nominal dates).

II/1 page 6 names the current call, RRF-REP-10.13.1-24, RRF-6.2.1 and the stated
class of EU-funded enterprise energy schemes for 2021–2027. The maximum is one
**supported** application for the same independent building unit **and/or** final
beneficiary. Both need not match; a merely submitted application is not an award.
Footnote 6's exception concerns investment **exclusively for PV installation**
in that stated prior-support context. It does not make a heating package with a
PV component equivalent, admit unlisted schemes, waive same-cost EU double
funding, or make PV/storage a listed eligible activity of these calls.

HEM compensation remains optional and source-conditional: a written agreement,
at most one generation agreement, proportionate services chosen by the borrower,
no cash-plus-HEM payment for the same advice/subactivity, and no additional adviser
fee including an advance under that agreement. These references are not an
automatic legal/eligibility decision engine. All record-specific gates remain.

## Two exact dates, no silent refresh

The three historical files are unchanged byte-for-byte:

- `data/processed/b14/funding_reference_snapshot.json`
- `data/processed/b14/eligible_cost_caps_417.csv`
- `registry/b14_funding_reference_manifest.json`

Existing explicit `as_of="2026-10-01"` reads preserve the old result and continue
to refuse Budapest caps at that historical admission boundary. New explicit
`as_of="2026-10-03"` reads use four separately hashed/retrieved official
observations. Both fresh FAIR indexes still select the same 2025-10-15 call and
procedure revisions, and both new MFB pages link the same exact September FAQ
and show suspended intake. The current indexes happen to match their old bytes;
the new MFB HTML does not, and is not misidentified as the old payload.

The existing read-only `FundingReference` is extended rather than wrapped in a
new calculation model. Its new programme view returns the source-bound details,
new observation identities and explicit prior-review reliance. Programme-rule details retain their explicit
POL classification; fresh source observations remain OBS. `read_cap`
enforces the requested row's own programme/scope, date, gross basis and unit.
Neither geography nor date is inferred. Unknown/current/future dates, awards,
eligibility, available funds, market-price and national-allocation claims remain
refused. Finance facts and their original denominators are unchanged. Original
envelopes do not become remaining money; Q/null funding amounts stay Q/null.

## Exact recovery and historical-review limits

Five historical payloads were recovered exactly: both calls, both official FAIR
indexes and the September FAQ. Calls came through their already-recorded public
mirrors because the portal download service returned HTTP 502. Exact official
hash agreement establishes one document lineage, not independent corroboration.
All original documents, page images and detailed extraction evidence stay private.
No security warning or access restriction was bypassed.

The common procedure and three historical suspension-notice PDFs were not
recovered in this pass. The two old MFB HTML payloads likewise were not recovered.
The procedure's invoice-endorsement clause (10.8.2, PDF p40 / printed p39) and
historical notice details explicitly retain the prior independently reviewed
V1-018 evidence. Index title/ID/size selection is not a new exact PDF-byte proof.
The prior all-eleven-source / 113-check pass is **not** claimed as rerun.
New qualification performs 148 checks, including 78 Budapest component-presence
checks and separate rendered-table interpretation; those are distinct evidence.

## Original acceptance scope and what remains

V1-018 deliberately admitted a bounded reference without accepting L01. The later
original-criterion audit found its missing Budapest cost and named-cumulation
bindings, now supplied here. It also found that an unbounded programme census,
individual record approval, remaining finances and university/pilot fit were not
additional original L01 field requirements. This checkpoint explicitly supersedes
that earlier broader unresolved-scope interpretation; it does not retroactively
claim that V1-018 accepted the task or that all funding programmes are covered.

Any eventual L01 acceptance is for the two named, dated rule handoffs. B14-D01
remaining/reserved/committed/paid/project funding, B14-D02 research/pilot fit,
individual legal decisions, later revisions, the whole B14 module and B15 remain
open. No readiness percentage, national eligibility fraction or grant default is
changed. The conditional metadata-only acceptance must name the real reviewed
implementation commit after its hosted checks pass, not this previous baseline.

Source origins and new observation hashes are in
`rule_completion_20261003.json`; historical pins remain in the original manifest.
The completion manifest binds old inputs, new data, all 39 Budapest rows and
rule/currentness records. Existing and new consumer tests distinguish the two
as-of dates and reject cross-programme transfer and broadened exception claims.
