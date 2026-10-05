# V1 checkpoint 002: canonical A1/H tariff consumption

Scope: partial B04-D01 integration. No dynamic-price simulation, H-battery permission or national saving is asserted.

## Current source verification

On 2026-10-01 the [MVM current price page](https://www.mvmnext.hu/aram/Arak) still linked the [residential tariff table](https://www.mvmnext.hu/aram/servlet/download?id=16214&type=file), revision VE_Lakossági_Árak_2025/1. Its four distributor groups were visually checked. The separate [M.1 tariff annex](https://www.mvmnext.hu/aram/servlet/download?id=16548&type=file), effective 2026-03-01, was read at sections 2.2.4, 2.2.5 and 3.1. These are existing canonical source IDs; verification digests and boundaries are in `registry/b04_tariff_source_verification.json`. No external PDF bytes are committed.

## Corrected boundaries

- The H schedule's legacy net/gross columns are energy components, not final household rates. New explicitly named final-rate and monthly fixed-charge columns prevent a consumer from treating the energy-only 2.41 HUF/kWh Démász value as the 22.962 HUF/kWh final variable charge.
- The Démász H bridge previously held net network 20.10 HUF/kWh, inconsistent with its other entries. The published tariff table supplies 16.18; adding net energy 1.90 and applying 27% VAT reconciles the published final rate within displayed rounding. Annual fixed charge remains the derived 12 × 50.165 HUF.
- M.1 establishes discounted entitlement outside the H heating season. The old unconditional `A1 higher` fallback is retired. Four source-native outside-season discounted energy components are preserved; their full-rate/network/period handoff is still explicitly Q. No disputed full invoice is inferred from FAQ shorthand.

## Actual consumer and tests

`modules/B04/engine.py` loads canonical CSV values and explicitly returns SCN_CONSTANT_2026_TARIFF_SNAPSHOT, not a historical or future invoice validation. A1 pricing consumes an explicit discounted allocation and billed-month quantity, with the higher rate only on excess and the fixed fee once. H pricing uses final rates only, requires an entirely in-season interval and the declared eligible thermal-load scope, and does not apply a heating-season consumption cap. Negative/nonfinite quantities, unknown areas, outside-season H intervals and H battery/general/export loads are rejected.

The declared load scope is a conditional calculation input, not proof of any individual site's permission. Eligibility and any site claim still require actual authority. Rates are frozen at the 2026-10-01 verification snapshot. Historical replay and future use are explicit constant-policy SCN costs, not observed invoices or price forecasts. H date inputs determine season membership only; they do not select historical tariff revisions. The helper does not allocate annual entitlement to actual invoice periods or infer monthly fees from dates. Export remuneration is outside this import ledger. The source network table is scoped to profiled low-voltage KIF I/II and smart-meter time-series KIF IV connections; non-smart-meter time-series and other connection classes are not covered by these fixed snapshot costs.

Prior B04 arithmetic tests used only functions defined inside the test file. They now call the canonical-data consumer. Additional tests cover all A1 area rates, H final-price identity, nonfinite/negative data, invalid scope/season, component reconciliation and retained outside-season Qs.

## Remaining work

B04-D01 stays INTEGRATING: outside-season H complete accounting, B tariff consumer, exact period allocation and the annual downstream handoff remain open. B04-L01 authority is unchanged. The separately discovered MVM D-tariff documents have not been silently admitted by this checkpoint.
