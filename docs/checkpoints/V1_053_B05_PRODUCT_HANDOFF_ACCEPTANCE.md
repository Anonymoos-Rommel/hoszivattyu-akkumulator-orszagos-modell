# V1-053 — accept the named B05-D02 product handoff by verified reuse

B05-D02 is accepted at the **PUZ-WM50VHA(-BS), Ecodan Vol.5.3 December 2020**
source-product handoff boundary. The independently reviewed source and consumer
commit is `ce641bea8082ce3e49d78f75b9f178232f91ec3b`. All accepted scientific
artifacts, code, controls and tests remain byte-identical to that commit. This
checkpoint adds acceptance metadata and documentation only; no new helper,
wrapper, numerical model, performance point or default is needed.

The original task asks for exact product/revision, outdoor/water coordinates,
Qh/Pel/COP, minimum performance, operating limits, supplementary heat and source
lineage. It does not require a national market-share mix before a named product
map can be accepted. The source/claim-to-artifact map in `V1_053_ACCEPTANCE.json`
records every original criterion and the existing consumer that uses or enforces it.

## Exact source and unchanged numerical facts

The manufacturer original was recovered against its existing SHA-256:
`e7212300cb49ad561db56e974cc9945655943bfb0dd8309610a400fba65919ab`.
It is 73,771,982 bytes and 442 PDF pages. Independent visual/source inspection
covered pages 1, 6, 19, 30, 32, 57, 60 and 442. Page 60 / printed A-56 reproduces
all **252** existing coordinates: **208** Q/COP pairs, **44** explicit blanks and
**21** grey integrated-defrost pairs. No source value changed. Electrical input
remains DER = Qh/COP; interpolation retains paired Q/P and derives COP from them.
MIN/MID/NOMINAL/MAX remain distinct source modes, without automatic policy selection.

The source's scalar limits, outlet-envelope graph and hydraulic/defrost context
are different kinds of evidence. They do not authorize a new two-dimensional
point by combining one-dimensional limits. Existing P26/P46 classifications,
including the A−15/W50 unknown, remain intact. Source blanks are neither zero
capacity nor measured equipment failure. No graph threshold is digitized or
interpolated, and unsupported numerical coordinates remain refused.

The nominal table's 10 W pump allowance is not a new fixed whole-grid or installed
pump debit. Source-grey defrost markings are preserved; an unmarked point is not
authority for zero defrost or a universal extra penalty.

## Supplementary heat and source lineage

The existing annual manifest already identifies the exact Outdoor KEYMARK record,
certificate 037-0032-20 rev.2 dated 2023-12-19, average-climate/EN14825 medium
application, and its reported electric supplementary-heater PSUP of **0.81 kW**.
That value and the existing nonactive fields were independently reread through
the official page rendering. PSUP is a certification-context field; it is not an
installed heater rating, a selected efficiency or an hourly dispatch instruction.
No backup is inferred from it.

The rendered source was labelled cached/crawled last month. Normal raw retrieval
and cloud-browser navigation timed out. Original KEYMARK response bytes, their
hash, historical byte identity and fresh live validity were **not** established.
Those limitations remain explicit. The manufacturer original is fully preserved;
no analogous original KEYMARK archive is invented. Manufacturer EN14511-2013 and
certificate EN14511/EN14825-2018 bases remain separate. A common outdoor model
label does not establish identical test conditions or a shared tested specimen.
No withdrawn Cdh/MIN join is restored, and EPREL is not treated as a mandatory
independent extra copy of manufacturer evidence.

## Actual consumers and remaining scope

Existing source maps and the annual manifest enforce their pinned identities.
The 26,280-hour original/standard/ambitious reference family and the historical
cold checks already consume these maps. The declared standard and ambitious
source cases meet their generator demand without selecting backup. The original
case's capacity shortfall remains visible and its complete annual device total
remains null. Cold numerical noncoverage does not become a thermal deficit,
physical failure or inferred heater size.

The existing producer `whole_slice_complete=false` flags describe their broader
annual/cold/system scopes. They are unchanged; this acceptance record identifies
the narrower registry B05-D02 source-product task. B05-D01 hourly SH/DHW inputs,
B05-D03 combined SH/DHW/correction integration, whole B05, installed-system
performance, activated backup-enabled configurations and national selection
remain open. Q-B05-003 and Q-B05-004, the exact A−15/W50 question, hydraulic and
outside-unit applicability limits remain. No module readiness score increases.

## Verification and publication boundary

The independent source/consumer recommendation and exact metadata review are
separate from original laboratory measurement, installed validation and hosted
CI. Local canonical results and exact changed-file hashes are recorded in
`V1_053_VERIFICATION.json` after the metadata review. Future publication requires
approval for this exact packet and verification of its actual hosted run.

The original PDF, page images and detailed qualification evidence remain private.
Only public-safe acceptance records, source identifiers/hashes and documentation
are proposed for the repository. The prior V16 published recovery remains intact.
