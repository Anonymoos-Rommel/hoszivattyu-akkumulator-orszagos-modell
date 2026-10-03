# V1 checkpoint 003: public D-tariff source intake

Scope: B04-D02 research/integration. This optional tariff is not a new prerequisite for the core V1 and is not a dispatch optimizer.

## New source evidence

The official MVM [product page](https://www.mvmnext.hu/aram/pages/aloldal.jsp?id=16455187) now publishes a D-tariff contract, metering conditions and retrospective price data. It says application can start no earlier than 2027-01-01. Only eligible A1 general-consumption meters with the required remote-read monthly time-series settlement qualify; an actual customer's contract still requires the supplier's assessment. This does not authorize an H-meter battery or export.

The [detailed method](https://www.mvmnext.hu/aram/pages/aloldal.jsp?id=16455188) first weights the flexible net energy prices by **all** imported energy in the billing period, then applies that unit price to only the quantity above the discounted allocation. Assigning the allowance chronologically to individual cheap/expensive quarters would implement a different rule. The [merchant notice](https://www.mvmnext.hu/aram/servlet/download?id=16704&type=file) publishes net 13.70 HUF/kWh effective 2026-09-10, subject to change. The already combined published flexible series must not receive that spread a second time.

## Materialized external-only panel

The [public history PDF](https://www.mvmnext.hu/aram/servlet/download?type=file&id=16727) was downloaded and hash-pinned. Its 35,040 intervals cover 2025-09-01 through 2026-08-31 local civil dates. All source start and end clocks reconcile with continuous UTC quarters, including 100 rows on 2025-10-26 and 92 on 2026-03-29. Its 175 negative net price entries are retained. Representative first/DST table pages were visually checked.

These are publisher backcast prices, not a tariff that was available to households in 2025, not pure HUPX quotes and not a forecast. Before October 2025 the source explicitly repeats each hourly price into four quarters. The published net energy boundary includes a merchant spread but excludes network charges and VAT. The source's retrospective fee-date description is not used to reverse-engineer a wholesale series by subtracting today's fee. Display resolution is 0.01 HUF/kWh; this is not a claim about total model uncertainty.

The full PDF and derived numerical panel remain external-only/ignored. The public repository contains stable source IDs, URLs, digest, coverage diagnostics, parser and tests, not source bytes or a transformed raw-data dump. Source-series redistribution is not cleared by accessibility.

## Reproduction and consumer boundary

Obtain the exact public PDF from the manifest URL and run:

`python tools/materialize_b04_dynamic_tariff.py --pdf /path/to/the/downloaded.pdf`

The tool verifies its SHA-256 before conversion, validates every local interval against UTC, and writes only under ignored `data/interim`. A changed PDF requires source-revision review; it is not silently accepted. No API, account, fee or external contact is needed by this intake.

`price_dynamic_backcast_energy` calculates **net energy cost only** for one contiguous within-month interval using aligned nonnegative imported kWh. Export is not netted against import; negative prices are retained; the method does not invent tariff eligibility or entitlement. Network/fixed charges, VAT, dispatch feasibility, future price risk and actual household consumption remain separate.

The acquired rolling-year price panel is not silently paired with the existing calendar-2025 weather panel. Only matching observed windows or explicitly labelled, justified temporal scenarios may be joined. No independent source claim is made between MVM's HUPX-derived panel and HUPX itself.

## Status and integrity

B04-D02 stays INTEGRATING; Q-B04-003 and the canonical live household-price variable remain open. The acquisition resolves a concrete source lead but does not produce national savings or a complete bill. Next: select a claim-appropriate paired load/weather window and applicable network/tax/entitlement contract when this optional scenario is used.

Two pre-existing rows in `registry/sources.csv` contained unquoted commas in their final notes field. Their complete text is preserved with proper CSV quoting to prevent truncating provenance during programmatic reading. This is a structural correction, not a new Trane claim. Other registry-width issues are not claimed fixed here.
