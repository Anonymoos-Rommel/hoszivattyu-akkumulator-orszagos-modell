# V1-034 — accept the bounded B04-D01 tariff handoff

B04-D01 is accepted by verified reuse of the official household tariff table and its tested consumer. Its original approved scope asks for HUF/kWh and fixed charges, net/gross values, distributor area, H/A1/B circuit, effective date, season and threshold. It does not require an actual household annual invoice or a national annual cash-flow result to accept these source tables.

The independent source/consumer review targets commit `365a28433f5eda976fa00936282a1565922de45a`. All accepted tariff, engine and test bytes remain identical on integration base `45758da67be7527423f06a0375c3dc858c7ea9ec`; the B04 source rows are also unchanged. This checkpoint changes acceptance metadata only. It does not change a tariff, formula, scientific input, test implementation, module status or readiness score.

## Exact admitted source scope

- MVM M.1 effective 2026-03-01, retrieved 2026-10-01: `SRC-B04-MVM-M1-2026`
- MVM residential table revision VE_Lakossági_Árak_2025/1, verified against the official listing on 2026-10-01: `SRC-B04-MVM-RESIDENTIAL-TARIFF-2026`. The table is not relabelled as a new 2026 document
- Official 10/2024 MEKH consolidated regulation, version 2026-08-30, relevant mapping independently reread 2026-10-02: `SRC-B04-MEKH-SYSTEM-FEES-2024`

The admitted reference covers A1, B Alap and H within the existing connection/product boundaries, with profiled outside-H mapping labelled DER. It does not admit every commercial variant, non-profiled outside-H pricing or an individual household's eligibility. The consumer uses a constant 2026 snapshot labelled SCN; date inputs select season and do not establish historical invoices or future tariffs.

The two exact PDF hashes remain in `registry/b04_tariff_source_verification.json` and the verification receipt. The narrow live MVM-listing read on 2026-10-02 did not succeed, so currentness remains the explicitly frozen 2026-10-01 verification. The official MEKH reread succeeded. No original-byte hash is fabricated for rendered legal text, and no source PDFs are republished.

## Verification and acceptance record

The independent assessment reran 39 relevant B04 consumer/boundary tests and the genuine pinned-PDF verifier's 56 numeric comparisons. It additionally checked heating-H values and original seasonal/entitlement clauses. These are distinct from synthetic fixtures. It found no remaining criterion missing from the bounded D01 table/consumer contract.

The plan now records accepted artifact paths, consumer tests, the exact reviewed commit and retained validation debt. Its source IDs remain unchanged. The existing engine functions `price_a1`, `price_b_alap`, `price_h_heating` and `price_h_outside` remain byte-identical. Previous exact-head CI 1095 covered this same production code; fresh targeted metadata checks and exact-head hosted CI are recorded separately and are not confused with a new local aggregate.

## Retained limits

`Q-B04-002` stays open as the broader E2 effective-date component/tax bridge debt. The official current-tariff base may continue under that existing classification. B04-L01 / `Q-B04-001`, B07 topology/dispatch authority, B04-D02 wholesale/dynamic prices and B13 tax incidence remain separate.

Actual annual consumption per circuit, distributor seasonal splitting, evidenced discounted allocation/carryover, billed-month fractions and a nonduplicated annual connection ledger remain downstream inputs. No full 2523-kWh outside-H allowance, arbitrary half-year allocation or twelve months of the in-season H fixed fee is inferred. A fixed annualized source rate is not an observed H annual invoice.

This is one accepted work slice. It does not complete B04 or the national programme, increase readiness, select a household financial policy, publish private data or authorize a main merge.
