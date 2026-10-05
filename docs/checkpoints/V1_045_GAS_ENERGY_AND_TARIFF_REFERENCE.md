# V1-045 – Gas source-energy convention and conditional tariff reference

This checkpoint connects existing annual heating-only TABULA gas references to their own source energy convention. A separate monetary consumer evaluates explicitly declared scenarios using the existing regulated residential tariff. It does not supply actual billing energy, household savings, wholesale/import valuation, B12 cash flow or national weights.

## Source energy, not a measured Hungarian gas constant

TABULA's method defines delivered energy on gross calorific value (GCV). The original workbook's natural-gas conversion cells `Calc.Set.BuildingStock!II4/QI4/RM4` equal0.92, and the associated formulas establish NCV=GCV×0.92. This is an observed workbook convention. Applying it to the named historical Gas cases is a derived E2 source-reference quantity, not an observed property of gas supplied to a Hungarian household.

`modules.B11.calorific_reference.calculate_reference(package=...)` accepts the existing original, standard and ambitious packages. Original workbook system rows3390/3391/3392 identify the same named variants,56m² and Gas fuel, with distinct existing source heating consumption. It preserves native GCV and derives MJ_NCV using3.6MJ/kWh and0.92. DHW, cooking, gas auxiliary electricity and hypothetical gas volume are excluded.

| Source package | Existing serialized annual kWh_GCV | Derived source-convention MJ_NCV |
|---|---:|---:|
| Original | 21085.5682647915984 | 69835.4020929897739008 |
| Standard | 8891.58187741839400 | 29448.91917800972092800 |
| Ambitious | 6353.08215323660536 | 21041.40809151963695232 |

Digits show reproducible arithmetic, not measurement precision. Original workbook CI3390 is376.52800472842142kWh_GCV/m²; the pre-existing admitted registry serializes it as376.5280047284214. This checkpoint preserves that registry rather than silently rewriting previous calculations. The2×10⁻¹⁴kWh/m² serialization difference is not a physical uncertainty estimate.

IEA/Eurostat's2004 manual, TableA3.12, uses the distinct general statistical convention0.90. It is retained as a disagreement diagnostic, not averaged, adopted as a second canonical case, or used as a confidence interval. For the ambitious reference the0.92-versus0.90 difference is457.421915MJ, or2.173913% relative to the0.92 result. That percentage does not bound actual gas-composition/calorimetric mismatch or household cost uncertainty.

The physical Hungarian and actual MVM billing equivalences remain validation debt. Their calorimetric reference temperatures and applicable gas composition/period must be compatible before such a claim. MVM's15°C normal-volume reference is not proof of matching combustion/calorimetric temperature. No mismatch is assumed zero. The manifest records the upgrade evidence; no new duplicate validation-debt mechanism is introduced.

## Fixed-fee tax-basis repair

The existing MVM F.4 source gives9192HUF/year as NET. The rulebook's price description and explicit net-plus-VAT fee field corroborate the basis. The legacy value remains intact, with an explicit NET tag and separate DER gross value11673.84HUF/year at27% VAT. This is unrounded arithmetic, not a rounded observed invoice.

The canonical annual regulated-charge formula now uses the separately named gross applicable fixed charge. VAT must not be added again, and the higher tariff band cannot introduce a second fee. This corrects a material ambiguity in combining the previous generic9192 value with gross variable rates. It does not imply that the fee is avoidable, attributable to heating or applicable to an actual connection.

## Explicitly conditional monetary consumer

`modules.B03.regulated_reference.price_reference` requires all of:

- A named source package.
- `TABULA_NCV_AS_TARIFF_FUTOERTEK_REFERENCE_SCN`, explicitly declaring hypothetical source-convention energy in the tariff denominator; this is not proof of equivalence.
- `ONE_ABSTRACT_COMPLETE_AUG_JUL_SETTLEMENT_YEAR_SCN`, representing one complete abstract settlement year rather than inventing a Jan–Dec split or hourly gas profile.
- A caller-supplied discounted MJ allocation after other retained gas uses, between0 and the source's63645MJ normal reference allowance. No allowance is selected by default or entitlement inferred.
- A connection identity and supplied fraction between0 and1 of one annual connection fee. This is a declared scenario connection charge, not automatically an end-use allocation or saving.

For source quantityq and supplied allocationa, consumption arithmetic is `min(q,a)×2.86512 + max(q−a,0)×22.002` gross nominal HUF at the frozen2026 tariff snapshot. Declared connection charge is reported separately as `fraction×11673.84`. The combined output remains a scenario reference-plus-connection expression. Each call represents one alternative, and alternatives must not be added together. The annual source does not establish actual settlement chronology or billing-year demand.

For illustration only, full63645MJ allocation yields consumption charges318551.789250HUF for original,84374.687315HUF for standard,60286.159151HUF for ambitious. A separately declared full connection adds11673.84HUF. These displayed values do not select a household allowance, prove eligibility, establish complete before/after service, or imply savings. In particular, the original heat-pump package still lacks full annual service; its complete gas-source arithmetic does not repair that limitation.

The regulated layer remains a B13 baseline reference only, with fiscal compensation unknown. No B03-to-B12 or wholesale/import route is opened. Source-consumption, tax basis, conditional settlement, retained uses, connection attribution and physical billing compatibility remain separate concepts.

## Evidence and verification

Exact source originals are retained privately with hashes and external-only provenance. No workbook, rulebook, raw profile or uncleared document bytes are published. The prior independent source-admission review and subsequent implementation review are separate: the former admitted a named ambitious energy-only reference and flagged the fixed-fee defect; it did not itself approve a monetary consumer or all three cases.

Tests cover source identity, gas-only units, unsupported outputs, ambient decimal precision, supplied-allocation boundaries, VAT reconciliation, fee separation, absent/malformed arguments and changed dependencies. Registry validation, full configured suite, exact-content independent review and exact-head hosted CI are required for checkpoint closure. Software tests and arithmetic do not replace empirical validation or complete the underlying B03/B11 slices.
