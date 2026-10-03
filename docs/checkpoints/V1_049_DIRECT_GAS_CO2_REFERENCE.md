# V1-049: named gas-source direct-combustion CO2 reference

This is the first B11-to-B17 numerical activity handoff. It combines two already
identified quantities at compatible boundaries: the three V1-045 named TABULA
natural-gas heating cases, expressed in source-convention NCV energy, and one
separately qualified IPCC residential natural-gas CO2 method factor.
It does not close B17-D01, increase readiness or establish programme emissions.

## Exact source and applicability

The original [2006 IPCC Volume2 Chapter2](https://www.ipcc-nggip.iges.or.jp/public/2006gl/pdf/2_Volume2/V2_2_Ch2_Stationary_Combustion.pdf)
has been reacquired with the same previously registered SHA-256 and byte count.
Table2.5, printed/PDF page2.23/23, gives Natural Gas CO2 at 56,100 kg/TJ NCV,
with native lower/upper limits 54,300 and 58,300. These are official-method ASS
defaults, not observations of Hungarian household emissions. The one selected
default supports an E2 conditional source reference. The original document,
later refinement and exact attribution remain in the public manifest; original
PDFs stay external.

The original TABULA workbook explicitly maps `Gas` to natural gas, type unknown.
The same code occurs in system rows3390/3391/3392 for the original, standard and
ambitious variants. V1-045 already derives their heating-only NCV input through
the workbook's0.92 NCV/GCV convention. The consumer reuses those quantities;
it does not recompute a gas volume, add DHW/cooking or invent a current measured
Hungarian fuel composition. The actual-gas and population-transfer debt remains.

The IPCC oxidation factor1 is already included. It is not multiplied a second
time. The Tier1 inventory method expresses total fuel carbon as CO2, including
the very small carbon fraction emitted in non-CO2 species. Thus these results
are direct-combustion **inventory-method references**, not exact measured stack
CO2. Upstream methane, CH4/N2O/GWP, refrigerants, electricity and lifecycle
effects are outside this calculation, not observed zero.

## Reproducible calculation

`calculate_reference(package=...)` requires one named package, with no default.
For each case, `kg_CO2 = MJ_NCV / 1,000,000 × kg_CO2_per_TJ_NCV`.
The existing source activity, source row/variant identity and factor lineage
remain visible. Decimal arithmetic is isolated from the caller's context.

| Named gas source case | Source-convention MJ_NCV/year | Central inventory kg_CO2/year |
|---|---:|---:|
| Original | 69835.4020929897739008 | 3917.76605741672631583488 |
| Standard | 29448.91917800972092800 | 1652.084365886345344060800 |
| Ambitious | 21041.40809151963695232 | 1180.422993934251633025152 |

Displayed digits preserve source serialization and arithmetic, not empirical
measurement precision. Each row is a separate historical source-model variant.
These are not actual household emissions or a heat-pump programme comparison.

`compare_reference(from_package=..., to_package=...)` returns a signed
source-case difference. Positive means the from-case exceeds the to-case.
It applies **one common factor** to the difference in source NCV activities.
It does not independently subtract opposite ends of two factor intervals or
invent separate carbon-factor draws for the same fuel convention. Reversing
the comparison reverses the interval endpoints; comparing a case with itself
returns exact zero. This is not an observed or causal retrofit saving.

## Uncertainty and scope

IPCC Chapter2 describes the default-factor limits as95% confidence intervals.
Chapter1 describes their2.5/97.5 percentiles and three-significant-digit rounding,
derived from its source uncertainty method. The consumer retains the published
factor and limits; it does not fit, sample or choose a runtime distribution.
The reported mass interval is solely the factor interval mapped at fixed
source-convention activity. It is neither a hard support bound nor a95%
confidence interval for full model error. Source activity, physical gas,
calorimetry, country transfer and inventory-to-stack differences are not covered
by those limits or assumed absent.

The2019 refinement does not replace this residential natural-gas default.
This version/currentness check does not make the generic method a current
Hungarian measured coefficient. Country-specific or case-specific authority
must be considered if that stronger target is later claimed.

V1-029's complete external factor panel and its prior exact-byte contract are
unchanged and are not claimed recovered. V1-049 qualifies only this one factor
and its three scalar source values. No national activity weights, heat-pump
electricity offset, net climate gain, exposure, health or monetary output is
admitted. All eight E2 acceptance criteria and the upgrade evidence are recorded
in the pinned applicability manifest.

## Verification

Source qualification independently checks original IPCC and TABULA evidence.
Implementation tests check rational unit arithmetic, source identities, scope
rejection, shared-factor dependence, reversed/zero differences, mandatory case
selection, source changes and ambient arithmetic settings. Exact-content
independent review and the canonical aggregate run are recorded in the separate
verification receipt. Hosted CI and publication are not implied by local checks.
