# V1-046 – A qualified WM50 lifecycle subinput

One missing B06→B12 input is now populated: **17 years as an ASS/E2 provisional modeled reference service life** for the named Hungarian heat-only WM50 reference. This is a single qualified base subinput with explicit validation debt. It is not observed survival, warranty duration, complete installed-system life, an automatic replacement date or a household financial result.

## Reuse of exact product evidence

The existing canonical source `SRC-B05-MITSUBISHI-WM50-FTC6-BINDING-2026` is reused, rather than creating a duplicate. The manufacturer/BRE-verified EPD000522 Issue01 explicitly covers PUZ-WM50VHA(-BS) with EHPT20X-MHEDW FTC6 packaged cylinder. Its cover states issue 14 August 2023 and expiry 13 July 2028; source manufacturing data cover 1 April 2021 through 31 March 2022. These dates are documentary boundaries, not commissioning or price-validity dates for a Hungarian household.

The EPD states a modeled 17-year reference life under proper installation and annual maintenance. Its original system-binding observation remains OBS in the source registry. The additional lifecycle transfer has its own ASS/E2 label in `registry/b06_cost_lifecycle_handoff.json`; the source registry's OBS label does not turn modeled life into a survival observation.

Only the reference-life scalar and its maintenance condition are reused. The EPD's UK/Ireland heating-plus-DHW operational energy, water, refrigerant, repair-material and end-of-life scenarios are not transferred into Hungarian household accounts.

## Explicit transfer debt

The handoff records four material debts: source controller/hydraulic package versus target system boundary; proper installation and maintenance; Hungarian climate and W55 load/cycling/defrost duty; and heating-plus-DHW versus heat-only service. These are finalization blockers for a validated physical-lifetime claim, not blockers to the scoped E2 reference model. A defensible manufacturer or representative cohort/calibration route can upgrade them; exact household observations are not made a universal E2 prerequisite.

All four debts are registered in the existing central blocker-evidence audit as
E2 VALIDATION_BLOCKER with model continuation allowed and finalization blocked.
Both B06-D02 and B12-D01 link their exact identifiers for the eventual upgrade.

No evidence supplies a directional adjustment to 17 years, so none is invented. The EPD condition is one maintenance cycle per year. It does not establish one paid supplier visit per year, zero maintenance cost or zero repairs. Supplier visit prices from other equipment families cannot be multiplied by that cycle frequency to produce WM50 annual O&M.

## Existing consumer, no new engine

B12's existing `Scalar` can represent this input as 17 year, ASS, E2, the named source and explicit assumption/admission references. `Asset.life_definition` remains `EXPLICIT_SCENARIO_LIFE`. Its commissioning date, asset generation, operating-coverage evidence, replacement dates and amounts, residual/disposal value and evaluation horizon must still be supplied independently.

The handoff is listed in B12's `current_source_admissions`, and the existing `assets` inventory points to it. Full `assets` and `costs` remain null/Q because their other required components are absent. The current B12 contract has no replacement scheduler and still refuses external numerical arithmetic: structural acceptance of the life scalar is not an executed lifecycle cash flow. No new generic admission resolver, quote accessor, financial engine or runtime gate is introduced.

## Cost research outcome

Public Hungarian installer component offers, supplier service prices and historical cost-optimal data were checked separately. They have distinct technical boundaries, equipment, periods, tax information and existing-system prerequisites. The investigation did not establish a complete comparable WM50 installed price or a national mean. Funding ceilings do not supply procurement costs, and unlike packages are not low/base/high cases to average.

Those source-scoped quotes remain research evidence for selecting a later engineering-matched procurement scope. This checkpoint does not choose an installation package or populate monetary O&M. Complete payable cost, installed-system life and financial results remain unresolved. B06-D02 and B12-D01 stay INTEGRATING; B15 stays blocked.

## Verification boundary

Independent source review checked the original EPD, all 13 retained source hashes and the corrected cost packet. Focused integration tests bind the17-year value and debt to the existing input structures, preserve cycle/paid-visit separation, resolve the canonical source identity and retain Q for complete external outputs. Exact-content review, aggregate regression and hosted CI are separate requirements for publication. Source originals remain external-only; this patch contains factual provenance and project-authored records, not source-document copies.
