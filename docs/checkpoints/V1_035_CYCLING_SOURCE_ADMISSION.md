# V1-035: common physical cycling admission and unassessed readiness

2026-10-02. This checkpoint applies a common source-admission boundary to
WM50 and Dimplex and records the P59 current total as unassessed. The exact
author review used base `45758da67be7527423f06a0375c3dc858c7ea9ec`; integration
uses `249df54c15370c5fa2829f3159b9384d3076c4e7`, preserving the accepted B04-D01
handoff and all protected manufacturer and thermal-reference contracts.
B05-D03 moves to INTEGRATING for this partial method/admission work, with no
slice acceptance or national/runtime admission. The previous V1-034 CI receipt
describes its own verified head.

## Physical admission and preserved mathematics

Both WM50 P20/P22 and Dimplex P23/P42 lack source-bound certified test-water
conditions and an explicit Cdh-to-manufacturer-MIN join. Matching product,
outdoor bin and low-temperature application do not establish fixed W35 testing.
`evaluate_exact_cycling_point` therefore returns
`Q / SOURCE_BOUND_CYCLING_JOIN_REQUIRED` with null COP/input for these current
observations. The gate checks source, certification revision/component,
climate/application, model, outdoor temperature and coefficient, plus current
manufacturer source/revision and the missing test-water/MIN authority. Caller
booleans and asserted fixed W35 cannot qualify a physical point.

`evaluate_conditional_cycling_point` retains P18 mathematics under
`CONDITIONAL_STANDARD_METHOD_CALCULATION`. WM50 Qmin 1.80 kW, COPmin 5.46 and
required heat 0.90 kW yield COP 5.20 and conditional input 0.17307692307692307 kW
for Cdh .950; .980 yields COP 5.352941176470588 and input 0.16813186813186815 kW.
These are algebraic consequences of explicit inputs, not observed physical
performance, actual hourly electricity/SPF or national policy. Missing physical
outputs remain null and are never replaced by zero.

## Source findings at their actual scopes

The official rendered [KEYMARK WM50 record](https://www.heatpumpkeymark.com/en/nc/ps-keymark/certificate-holders/?cHash=0aecf6bcedcd369e5acf7a509916b562&tx_pskeymark_frontend%5Baction%5D=showSubtype&tx_pskeymark_frontend%5Bcontroller%5D=Frontend&tx_pskeymark_frontend%5Bsubtype%5D=4300),
standalone `PUZ-WM50VHA(-BS)`, Units Outdoor, registration `037-0032-20 / rev.2`,
certification date `19.12.2023`, was independently read on 2026-10-02. Warmer
+7°C Cdh low/medium is .980/.980; average is .950/.960. Average/low
−7/+2/+7/+12°C values are .990/.980/.950/.930.

P20's current .950 is explicitly average/low; its earlier warmer attribution and
runtime-ready claim remain in historical fields and the exact predecessor Git
objects. September 24 original bytes were not retained. Matching visible
registration/revision/date does not establish historical byte identity. The
historical cause remains unresolved; neither a proven transcription error nor
publisher change is claimed. The unavailable historical ERP URL does not erase
P22 values; current KEYMARK is separate corroboration, not recovered ERP bytes.

The separately observed [KEYMARK Dimplex record](https://www.heatpumpkeymark.com/en/?cHash=345ece1d2c6cfa3f7606958b884b4b37&tx_pskeymark_frontend%5Baction%5D=showSubtype&tx_pskeymark_frontend%5Bcontroller%5D=Frontend&tx_pskeymark_frontend%5Bsubtype%5D=6778&type=109126),
LA 2030CP, Units Outdoor, registration 40060852 and certification date
2025-08-29, corroborates average/low Cdh .990/.970/.953/.912 at the same four
outdoor bins. The inspected model fields provide neither test-water branch nor
MIN transfer authority. No absence is inferred about the underlying VDE report.

Current Dimplex manufacturer facts come from System C Version 03/2026, P42
rows D04–D07, [handbook](https://www.dimplex.eu/sites/g/files/emiian586/files/2026-03/Projektierungshandbuch%20System%20C%C2%AE-v15-20260319_150009_DE_final.pdf)
PDF/printed page 25, section 3.10.1. At A7/W35 it gives 7.72 kW / 1.41 kW /
COP 5.49; at A12/W35, 8.87 kW / 1.32 kW / COP 6.70. Those fixed-coordinate
facts and the full 30-point/18-cell P42 surface remain intact. P23 older values
remain historical and are not mixed with P42 current references.

Independently verified retained [CALCM:01 issue 1.2](https://www.ncm-pcdb.org.uk/sap/filelibrary/pdf/Calculation_Methodology/SAP_2012/CALCM-01---SAP-REVISED-HEAT-PUMP-PERFORMANCE-METHOD---V1.2.pdf),
05/09/2017, Appendix D/Table D1, PDF/printed page 62, distinguishes fixed and
variable test-water branches. At average +7°C, low fixed/variable is W35/W27,
medium W55/W36. It proves that application alone is insufficient; it does not
select either branch for these products.

The manifest uses stable source IDs and separate dated observation IDs, exact
component/revision locators, current manufacturer revision identities and explicit
null missing authorities. Rendered KEYMARK observations have no invented
original-byte hash or archive. Original PDF/HTML and inspection panels stay out
of the repository.

## Original P59 criterion and current readiness

The original eight-point `EN14825_STANDARD_BIN_CYCLING_METHOD` criterion remains:

> The to-water standard-bin cycling equation is executable with same-point COP/capacity and exact certified Cdh.

Its identity and weight are unchanged. Conditional formula capability does not
satisfy the original qualified-input execution criterion, and both cited product
joins are unqualified. Current earned credit is therefore unassessed/null, not
zero, eight, or an invented partial allocation. The current component total is
also Q/null. Eleven unaffected gates retain their existing credits, totaling
67 supported points. The unresolved gate weight is 8. These quantities are not
a newly assigned score of 67 or a range; historical P59 total 75 and gate credit
8 remain explicitly reviewable in `historical_earned` and the history record.

The executable readiness module, scorecard, shared current readiness row,
validator and genuinely dependent assertions reflect this distinction. The
shared CSV uses status Q and a blank `readiness_percent`; explicit metadata
binds historical score, supported subtotal, unresolved weight and gate identity.
Other B05 component scores still require valid bounded integers. Readiness tests
retain substantive physical assertions and replace only obsolete numeric-score
checks with explicit current-null/history/subtotal contracts.

B05 module readiness remains 64. No defined component-to-module aggregation rule
allows this finding to mechanically change it. Q-B05-004 remains the broader
OPEN/E2/VALIDATION_BLOCKER/MODEL_CONTINUE umbrella. Separate linked E3 admission
rows classify each missing physical join; they do not block independent
manufacturer or capacity-only work.

## Reopening, history and verification

Reopening requires each exact certified component/model, climate/application,
revision, actual test-water control/temperature and measured MIN co-location or
a named permissible transfer rule. A method transfer retains its method or
assumption status and cannot become a measured physical point. Reassessing the
original P59 gate requires evidence satisfying it or an explicit separately
reviewed scoring decision; this checkpoint invents neither.

Dated current notices supersede only the affected P20/P22/P23/P42/P27/P59
joining/readiness claims while preserving original accounts below. Shared
updates are applied only in this isolated candidate and supplied as row/field
operations so published V1-033 source appends and the separately accepted
V1-034 B04-D01 changes survive combined integration.

Manufacturer Vol.5.3 and Dimplex grids, bounded interpolation, native TABULA,
V1-033 thermal/capacity consumer, P18 formula and separate hourly method/policy
modules remain byte-identical. Focused tests cover both product families,
conditional arithmetic, source/revision/component/water-condition rejection,
historical-vs-current Dimplex separation, unassessed readiness and unchanged
scientific dependencies. The external review packet includes the exact original
rubric and both missing-join witnesses. The lead owns the full-suite aggregate,
combined exact acceptance and publication.
