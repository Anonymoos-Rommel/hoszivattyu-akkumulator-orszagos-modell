# V1-042: current occupied-dwelling area constraints

The existing historical type experiment cannot be transferred unchanged as the 2022 occupied-stock floor-area exposure. The four V1-009 ALL-stock means are 79.065–79.894 m²; KSH reports 82 m² for occupied dwellings in 2022. The historical source remains valid in its own scope. This checkpoint does not replace its type weights or apply a national multiplier.

## Source and population

[KSH's current census page](https://www.ksh.gov.hu/nepszamlalasok) reports the occupied-dwelling mean at whole-m² publication precision. Its room-area definition is not a measured heated-area definition. The [census definitions](https://nepszamlalas2022.ksh.hu/fogalmak) distinguish dwellings from other inhabited units and define the included rooms/areas. The [final table 1.3.3](https://nepszamlalas2022.ksh.hu/eredmenyek/vegleges-adatok/tablazatok/nsz2022-1.3.3.xlsx), `Országos!A8/F8`, confirms 2022 and 4,008,541 occupied dwellings. Despite its broad title, that workbook contains room counts, not area or a more precise mean.

Exact external-source identities and locators are in `registry/b02_current_area_reference_manifest.json`. Raw HTML/workbook bytes remain external. The original observed WBL011 joint is reused directly: 116,452 returned cells, 4,008,541 occupied dwellings, including 618,724 district-heated and 3,389,817 non-district dwellings. No missing combination is filled as zero and no different projection is multiplied into a synthetic joint.

## One control and explicit precision assumptions

The source-native observation is the reported 82 m², not an exact unrounded mean. The canonical nearest-whole interpretation is explicitly `ASS`: closed [81.5,82.5] m². Closed endpoints conservatively avoid asserting a tie rule. One coherent wider sensitivity, [81,83] m², covers ordinary nearest/floor/ceiling interpretations. Neither interval is source-observed, a confidence interval, or a universal guarantee against every possible source-processing error. The derived area reference is `DER / E2_PROVISIONAL_BASE` with the exact mean and publication-rounding metadata retained as validation debt. This debt does not block the named area computation.

For each disjoint subgroup and its complement, count × source-band endpoints supplies area bounds. The ≥120 m² band has no invented upper edge; even district heating includes 945 such dwellings. The <30 m² band's conservative lower enclosure is zero, not an asserted zero-area occupied dwelling. Closed upper edges are conservative enclosures, not observed maxima.

For total area T and subgroup S/complement C, the projection is:

- lower(S) = max(L(S), lower(T) − U(C))
- upper(S) = min(U(S), upper(T) − L(C))

Infinite band upper limits are preserved until applying the national area budget. All subgroup bounds share that budget, so their extreme values cannot be chosen independently. There is no midpoint, equal-mean, conditional-independence or within-cell household reconstruction.

## Executable result

`modules.B02.current_area_reference.calculate_reference()` computes:

| Interpretation | National dwelling area, m² | Non-district mean dwelling area, m² |
|---|---:|---:|
| Nearest-whole ASS | [326,696,091.5; 330,704,632.5] | [76.418538; 88.775870] |
| Wider rounding sensitivity | [324,691,821; 332,708,903] | [76.418538; 89.367132] |

The gas-only census subgroup has 1,788,022 dwellings; the other non-district subgroup has 1,601,795. The output also returns their conditional area enclosures. These fuel labels and counts do not establish a gas-consumption or programme cohort.

All four preserved historical area transfers are below even the wider national set. The reference experiment's 318,597,109.6012799 m² exposure is short by 6,094,711.3987201 m² against its lower edge. Its non-district mean falling inside a subgroup interval does not validate the whole transferred joint. The author's separate full-heating factor and prototype geometry must not be used to erase the census-area mismatch. Existing V1-009 bytes remain unchanged.

## What remains unresolved

This is an area compatibility diagnostic. Heated area, current cell means, useful heat and participant allocation stay unknown. Even a two-group heat model still needs a qualified annual useful-heat contrast or bound between compatible groups, together with the JRC-household/occupied-dwelling energy-universe bridge. Separate means of area, heated fraction and temperature do not supply their thermal cross-moment. Representative or calibrated aggregate evidence may suffice; individual household measurements and 23 separate type means are not universal prerequisites.

No B01 count/rollout policy, comfort objective, physical system choice, national heat allocation, readiness, accepted slice or existing gate changes. The signed installed-minus-rating electricity residual remains a separate downstream boundary.

Verification binds the original full joint and historical output by hash, exercises finite and open-tail projections, empty/infeasible sets, source substitution and unknown propagation, and compares all four unchanged historical experiments. Exact review and configured-suite results are recorded separately; software checks do not constitute empirical heat validation.
