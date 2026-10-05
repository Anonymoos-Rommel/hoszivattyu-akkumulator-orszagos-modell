# V1 checkpoint 015: bounded B10 network-cost reference intake

Date: 2026-10-01. Scope: approved B10-D02 routine evidence/consumer integration. This checkpoint admits seven source-backed procurement references, with four correlated procurement families. B10-D02 remains **INTEGRATING**; the representative reinforcement-cost cohort and national programme-incremental cost calculation remain incomplete. No policy, module-readiness score or national-result status changes here.

## Admitted evidence and its exact boundary

All monetary amounts below are **OBS**, in the native currency, VAT and contract/allocation basis. Ratios explicitly labelled **DER** are within the cited lot only.

| Source / record | Literal monetary fact | Boundary |
|---|---:|---|
| [TED 777208-2025](https://ted.europa.eu/hu/notice/777208-2025/pdf), LOT-0001 | EUR 1,119,836.62 | One 126/22 kV, 40 MVA transformer supplied to Miskolc warehouse |
| Same source, LOT-0002 | EUR 2,231,873.24 | Two equivalent-rating transformers supplied to Gyöngyös warehouse |
| [TED 438132-2026](https://ted.europa.eu/hu/notice/438132-2026/pdf), LOT-0001 | Net HUF 59,982,087 | Orgovány I storage-network connection works package |
| Same source, LOT-0002 | Net HUF 121,995,641 | Orgovány II storage-network connection works package |
| Same source, LOT-0003 | Net HUF 303,985,846 | Bugac storage-network connection works package |
| [TED 761369-2025](https://ted.europa.eu/hu/notice/761369-2025/pdf), LOT-0001 | Net HUF 1,394,532,243 | Mosonmagyaróvár existing 132/22/11 kV substation extension/reconstruction works |
| [TED 373350-2026](https://ted.europa.eu/hu/notice/373350-2026/pdf), item 122236 | HUF 32,640 per bill-item metre; 700 m; HUF 22,848,000 | Amended 10 kV utility-relocation bill allocation within a railway project |

The transformer contracts are dated 2025-09-10. DER supply prices per transformer are EUR 1,119,836.62 and EUR 1,115,936.62; DER prices per **nameplate** MVA are EUR 27,995.9155 and EUR 27,898.4155. These are supply descriptors, with no installed-total or usable-MW interpretation. Lifecycle bid scores are excluded. Two lots retain one family, `EKR001295922025`.

The storage-connection contracts are dated 2026-06-10. Native nominal June-2026 HUF is retained without conversion to an annual-average or constant-price basis. Each package has associated storage and transformer/cable quantities, but these are not denominators for generic component prices. The battery equipment is outside the described network-works scope; the exact purchased/free-issued asset boundary still needs the annex. Bugac's 4.66 km quantity retains the source's three-conductor scope, without route-km conversion. The source-native HU333 geographical label is retained with a reconciliation warning, and cannot become a weighting stratum. Three lots retain one family, `EKR001158812025`.

The E.ON contract is dated 2025-11-03. Its net-HUF basis is supported by section 5.1.10's monetary criterion and the winner in section 6.1.2. Scope combines existing-station extension, renewal, switchgear, building and transformer-installation work; exact equipment-supply responsibilities are unknown. It is not an installed cost per added MW.

The railway item belongs to a contract originally signed 2022-11-04 and amended 2026-04-30. Its item/allocation basis follows the net construction-contract context. The amendment does not establish a 2026 economic price vintage. The DER calculation 700 × 32,640 = 22,848,000 is only a reconciliation of the exact OBS columns. The redesigned crossing retains a fixed total allocation; this is not an independently repriced market cable rate.

## Consumer and provenance

`modules/B10/cost_reference.py` loads the exact data revision pinned by `registry/b10_cost_reference_manifest.json`. The manifest also pins each record and the four reviewed Hungarian TED PDF renditions. Stable source IDs, original URLs, document/retrieval dates, revisions, SHA256 hashes, source authority and external-only reuse handling remain in the manifest. Source filenames have no semantic role.

`load_reference_catalog()` returns an immutable reference catalog. `read()` requires the exact observation/fact identity, source-native unit and price-basis identifier. `derive()` allows only `SUPPLY_PER_TRANSFORMER`, `SUPPLY_PER_NAMEPLATE_MVA`, or the exact `BILL_LINE_RECONCILIATION`, for their applicable record kind. Each result carries OBS/DER, input fact names, full scope metadata, source identity/hash and correlation cluster. It returns no unqualified scalar national cost.

There are four admitted price kinds across the seven records: awarded transformer supply; awarded storage-connection works package; awarded substation works package; amended bill-item allocation. Three inspected but unadmitted kinds are explicitly rejected: framework maximum ceilings, lifecycle bid scores and unresolved reserve fields. Ceiling/quantity division, package/MW or package/metre division, reserve addition, cross-currency conversion, VAT conversion, inflation adjustment and nameplate-to-usable-capacity conversion are unsupported.

Every record keeps programme CAPEX, installed project total, actual paid amount, actual completion, annual cashflow, common-2026 normalized value, economic base date, purchased/free-issued boundary, reserve inclusion, exact electrical node and representative cohort weight explicitly null. Planned durations remain source-native planned facts. A date or planned duration supplies no completion probability or annual payment allocation.

The illustrative MNB FX bridge and candidate KSH indices remain outside canonical data. The EKR public reserve/deadline record and unacquired annex do not enter this seven-record intake. The listed signed agreement and annex are promising next sources for equipment scope, reserve treatment and payment milestones; their CAPTCHA remains unresolved and was not attempted.

## Downstream and remaining debt

- P3 baseline infrastructure is not populated with converted/installed totals
- P5/P32 exact programme-attributable costs and P11 timed cashflows remain unpopulated by this adapter
- P67 national inference remains Q without representative demand/headroom/reinforcement, programme attribution, population calibration, timing, survivability and joint uncertainty
- A complete national node inventory is not required for a defensible national inference, but these convenience-selected procurement examples do not supply the missing representative cohort
- B12 household charges, B13 fiscal transfers and system resource costs require their own attribution; a DSO contract price is not automatically all three

Concrete remaining gaps, tracked under the existing Q-B10-001 and Q-B10-002 boundaries:

1. representative DSO/voltage/network-type frame, harmonized scope, no-reinforcement cases, weights and coverage residuals
2. matched WITH_PROGRAM/WITHOUT_PROGRAM intervention quantities, baseline renewals/development, acceleration/upsizing and joint uncertainty
3. common explicit subperiod and component-compatible normalization, with supply/installation/free-issue/VAT boundaries
4. actual delivery/payment evidence and independently supported schedules; planned duration alone is insufficient

These observations alone do not populate an admissible national programme-cost base. Reference E1 status is claim-specific and does not upgrade national applicability to E2. The existing Q-B10-001 representative-inference E2 route remains authorized and unchanged; its numerical cohort still needs to be constructed. Q-B10-002 timing evidence also remains open.

## Verification

- `python -B -m unittest tests.test_b10_cost_reference -v`: 23 tests passed
- Targeted regression run including B10 baseline/P4/P5/P6/P11/P32/P67: 131 tests passed
- `python -B tools/verify_b10_cost_reference.py`: catalog verification passed; without source arguments it explicitly reports source verification **NOT_RUN**
- With four `--source SOURCE_ID=/external/local.pdf` bindings: four pinned PDF SHA256 checks and 12 numeric row checks passed. The latter cover six winning award/currency/contract-date rows, three notice-total reconciliations and three amended bill-item columns. Losing bids and lifecycle scores are excluded by section selection
- The external verifier does not claim automated interpretation of technical scope, VAT or quantity semantics. Those were manually reviewed against the cited source locations and rendered PDF pages
- Mutation tests reject unsupported units, periods, kinds, promotions, zero-filled unknowns, additional normalization fields, broken source/record identity and inappropriate arithmetic
- Exact combined full-suite results and final artifact hashes are recorded in `V1_015_VERIFICATION.json`

Independent review found and corrected a reproducibility defect: caller Decimal precision could cause a false bill-item reconciliation failure. Validation, derivation and verifier arithmetic now use a private precision-40 context, with a low-caller-precision regression test.

An initial targeted command referenced two nonexistent test modules. The corrected eight-module command passed all 131 tests after the additional precision regression. This was a command-name correction, not a suppressed test failure. No source PDFs or raw extraction dumps are included. No CAPTCHA or external contact was used.


The four source rows are registered in `registry/sources.csv`; their exact renditions are pinned by the B10 reference manifest. The research plan records B10-D02 as INTEGRATING with the existing Q-B10-001/Q-B10-002 references.
