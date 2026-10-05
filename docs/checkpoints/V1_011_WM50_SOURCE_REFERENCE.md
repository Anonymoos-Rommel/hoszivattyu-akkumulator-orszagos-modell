# V1 checkpoint 011: source-complete WM50 operating-point reference

The Mitsubishi Ecodan R32 Data Book Vol.5.3, issued December 2020, provides four separate compressor-frequency modes for PUZ-WM50VHA(-BS). The pinned [manufacturer document](https://library.mitsubishielectric.co.uk/pdf/download_full/4099), PDF page 60 / printed A-56, contains 252 coordinates: 208 capacity/COP pairs and 44 explicit blanks. All 40 previously extracted minimum-mode points agree exactly. This is additional coverage of the same manufacturer document, not independent corroboration or a national product cohort.

## Source and physical boundaries

The manifest preserves the exact document hash, mode definitions, units, cell availability and annotation. Electrical input is Q/COP, labelled DER; the published capacity/COP pair remains OBS. The nominal table on PDF page 19 / A-15 explicitly includes the EN14511 pump correction in its input/COP boundary. This is a standard-condition total-unit reference, not whole-house electricity or an arbitrary external pump allowance.

The method notes on PDF page 57 / A-53 distinguish maximum, nominal, medium (80% of nominal frequency), and minimum frequency. Twenty-one grey capacity/COP pairs, A2 in MAX/NOMINAL/MID, include integrated defrost. MIN A2 is unshaded. Unshaded does not mean zero defrost. The source's A7 dry/wet-bulb 7/6 and A2 2/1 examples and 5 K water difference concern the stated nominal conditions; no universal return temperature is inferred.

Only the attributed numeric facts and source-cell labels are published. Redistribution of the original PDF or image is not cleared. The source registry uses an undated publication-day field with December 2020 in the reference period; the older minimum-grid entry's unsupported January 1 date is corrected.

## Consumer and tests

`load_wm50_reference` requires an explicit mode. The existing performance engine derives input and interpolates capacity/input consistently, preserving Q=P×COP. Missing two-dimensional corners and extrapolation remain unavailable. A separately requested fixed native water-temperature column is a one-dimensional reference with no internal blank bridging. An entirely blank column raises an explicit source-unavailable error.

W35 has all nine native outdoor points from −20 to +20°C; W45 begins at −15°C, W50/55 at −10°C and W60 at +2°C. Source blanks are not a manufacturer declaration of physical impossibility. Fixed W35 does not imply a weather-compensation curve or design suitability for every building. A full two-dimensional interpolation can remain unavailable where its corner rectangle includes a blank, even when a fixed-column reference is available.

The new reference does not replace the existing P22 dispatch/minimum-point surface, select a mode automatically, add a defrost penalty, or infer annual electricity from mean temperature. It does not promote B05 readiness or close B05-D02. The next material integration is a populated thermal-demand and supply-temperature handoff, followed by explicit runtime energy balance and boundary checks.

Five targeted tests cover all 208 source pairs, the prior 40 points, Q/P identity, blank and domain rejection, explicit fixed-supply selection, all-blank columns, shading scope and extract hash protection. The extractor reproduces the curated CSV byte-for-byte from the pinned PDF using existing PyMuPDF; no PDF software or macros are executed. Narrow independent review covered consumer boundaries and the all-blank guard. The author checked source pages and extraction; this is not full independent scientific validation.
