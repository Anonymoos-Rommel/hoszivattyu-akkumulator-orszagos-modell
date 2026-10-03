# V1 checkpoint 014: bounded outside-season H and B Alap cost consumers

This continues B04-D01 within the authorized V1 execution. It completes two rate consumers; the slice remains INTEGRATING because annual consumption, entitlement and settlement integration are not complete. No household eligibility, battery permission, national result or future tariff guarantee is asserted.

## Sources and derivation

The current MVM price page still supplies the [residential tariff table](https://www.mvmnext.hu/aram/servlet/download?id=16214&type=file), revision VE_Lakossági_Árak_2025/1. The table has not been relabelled as a newly issued 2026 document. It is used with the [M.1 annex effective 2026-03-01](https://www.mvmnext.hu/aram/servlet/download?id=16548&type=file) and the official [10/2024 MEKH regulation, consolidated 2026-08-30](https://njt.jog.gov.hu/jogszabaly/2024-10-20-5Z). Verification occurred on 2026-10-01. Stable source IDs, PDF hashes, scope and external-only handling remain in `registry/b04_tariff_source_verification.json`. Original PDF/text dumps are not republished.

For profiled low-voltage H connections, MEKH section 26(3) establishes the KIF I default and section 26(7) limits the KIF II base/volume exception to October 15–April 15. Section 14(1) specifies an annual base fee payable in monthly instalments. M.1 section 3.1 gives outside-season H energy prices matching A1. Their combination supports a DER rate mapping to the published A1 final and fixed rates outside the season. It is not a new observed H invoice. The scope is deliberately narrower than all smart-meter or time-series connections.

M.1 sections 2.2.4–2.2.5 establish outside-season discounted entitlement and describe day-prorating. The same downloaded annex bundle's M.2.2 section 6.10 requires distributor data for seasonal consumption splitting. This checkpoint does not implement an H-specific complete annual settlement or infer a full 2523-kWh or half-year allowance. The caller supplies the evidenced allocation and fee-period fractions.

## Numerical cost boundary

The source-native B Alap rates for Démász, E.ON/OPUS, ELMŰ and Émász are respectively 22.962, 23.520, 23.152 and 22.682 HUF/kWh gross. Excess consumption uses 60.935, not A1's 70.104. Its fixed charge is 50.165 HUF/month, charged once per declared connection-period, including zero-consumption periods. Annualized CSV fixed charges are DER, not separately observed annual invoices.

Outside-H discounted final rates are respectively 36.386, 35.293, 36.208 and 35.992 HUF/kWh gross; the mapped monthly fixed rate is 153.035. The excess rate applies only above the supplied discounted allocation. Published final prices are used directly, avoiding reconstruction from rounded gross energy components. Network and VAT are not added again.

Both consumers return `SCN_CONSTANT_2026_TARIFF_SNAPSHOT`. Dates select season membership only, including for historical/future SCN tests; they do not select historical tariff revisions. B requires a declared eligible controlled-load scope; outside-H requires the eligible thermal-load scope and `PROFILED_LOW_VOLTAGE`. These declarations enable conditional arithmetic and do not prove site permission or dispatch availability. Existing H battery/export gates remain Q.

## Verification and remaining handoff

The pinned-PDF verifier checks 56 numeric comparisons spanning B energy/network/final/fixed inputs and A1/outside-H rate controls. It does not pretend to automate the legal derivation. An independent review inspected the original tables and official legal clauses and found no blocking mapping defect. Regression tests cover all distributor groups, tier boundaries, zero consumption, fee fractions, season edges, frozen-snapshot labelling, invalid numbers, ambiguous/unadmitted rows and missing source authority. Registry and full-suite results, along with exact artifact hashes, are recorded in `V1_014_VERIFICATION.json`.

The full annual model still needs aligned circuit-consumption inputs, actual H entitlement/settlement allocation and a non-duplicated annual connection-fee ledger. Neither tariff prices nor a declared load type establish controlled-load operating availability. B04-L01, policy decisions and the proposed B07 state-coordinate adoption are unchanged.
