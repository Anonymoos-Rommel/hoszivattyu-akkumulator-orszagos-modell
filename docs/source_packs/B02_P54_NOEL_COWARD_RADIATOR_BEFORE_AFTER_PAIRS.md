# B02-P54 — Noel Coward House residential radiator before/after pairs

**State:** `ROOM-GRAIN EXISTING->PROPOSED RADIATOR PAIRS RECOVERED / LOWER-TEMPERATURE REDESIGN PROVEN / DESIGN PRECEDENT ONLY / NOT HEAT-PUMP IMPLEMENTATION / NOT HUNGARIAN OR NATIONAL STOCK AUTHORITY`

**Canonical base:** `d631233439ab6a76d20e4f2c23c71538addd8167`

**Implementation date:** 2026-09-17

## 1. Purpose

P54 closes the specific evidence-recovery target left open by P53:

`SAME DWELLING + SAME ROOM + EXISTING EMITTER + PROPOSED EMITTER + TYPE/SIZE + TEMPERATURE BASIS + CAPACITY`

The recovered source is an official Westminster City Council / AECOM engineering report for Noel Coward House within the Pimlico District Heating Undertaking (PDHU).

Primary source:

`https://www.westminster.gov.uk/sites/default/files/media/documents/secondary-and-tertiary-heating-systems-report-noel-coward-house.pdf`

The source contains both:

- **Table 4 — Existing Radiator Schedule**; and
- **Table 5 — Proposed Radiator Schedule**.

Both tables use apartment number and room location, allowing exact room-grain joins without inference across buildings or archetypes.

## 2. Why this source qualifies as the primary pair-table evidence

The source satisfies the evidence target on the dimensions that mattered:

1. residential apartments are explicitly identified;
2. the same apartment and room occur in the existing and proposed schedules;
3. existing radiator physical type and observed size are published;
4. an existing sample manufacturer/model and sample size are published for capacity estimation;
5. existing LTHW flow/return/mean temperatures are explicit;
6. existing estimated capacities are numeric;
7. proposed radiator model, size and quantity are explicit;
8. proposed mean/flow/return temperatures are explicit;
9. proposed required capacity is bound to the same room;
10. proposed estimated capacity is published for five of six rows without unit ambiguity.

This is materially stronger than a blank template, aggregate retrofit count, procurement schedule, or a room-level heat-loss report that omits the old radiator dimensions.

## 3. Existing schedule — Table 4

The report publishes the following six residential room rows used by P54:

| Apartment | Room | Existing type | Observed existing size | Existing sample model | Sample size | Flow / return / mean | Estimated capacity |
|---|---|---|---|---|---|---|---:|
| 18 | Bedroom 1 | Double Panel | 800 x 600 | Stelrad Classic Compact K2 | 800 x 600 | 80 / 60 / 70 °C | 1.385 kW |
| 18 | Living Room | Double Panel | 1600 x 450 | Stelrad Classic Compact K2 | 1600 x 450 | 80 / 60 / 70 °C | 2.193 kW |
| 18 | Bathroom | Double Panel | 500 x 500 | Stelrad Classic Compact P+ | 500 x 600 | 80 / 60 / 70 °C | 0.673 kW |
| 11 | Bedroom | Double Panel | 1110 x 600 | Stelrad Classic Compact K2 | 1100 x 600 | 80 / 60 / 70 °C | 1.905 kW |
| 11 | Living Room | Double Panel | 1210 x 600 | Stelrad Classic Compact K2 | 1200 x 600 | 80 / 60 / 70 °C | 2.078 kW |
| 11 | Bathroom | Single Panel | 410 x 450 | Stelrad Classic Compact K1 | 400 x 450 | 80 / 60 / 70 °C | 0.302 kW |

### Existing-model semantic boundary

Table 4 labels the manufacturer/model column as **Sample Manufacturer / Model** and separately publishes the observed radiator size and a sample size.

Therefore P54 freezes:

`OBSERVED EXISTING TYPE/SIZE != EXACT INSTALLED MANUFACTURER/SKU IDENTITY`

and:

`SAMPLE MODEL/SIZE -> CAPACITY REFERENCE`

but not:

`SAMPLE MODEL/SIZE -> PROVEN INSTALLED SKU`.

The bathroom and two Flat 11 rows make this distinction visible because observed dimensions differ from the sample catalogue dimensions.

## 4. Proposed schedule — Table 5

The proposed schedule lowers the common mean water temperature from 70 °C to 50 °C and publishes a 65/35 °C flow/return basis.

| Apartment | Room | Required capacity | Proposed model | Proposed size | Qty | Mean / flow / return | Estimated capacity |
|---|---|---:|---|---|---:|---|---:|
| 18 | Bedroom 1 | >= 1.385 kW | Stelrad Classic Compact K2 | 1600 x 600 | 1 | 50 / 65 / 35 °C | 1.421 kW |
| 18 | Living Room | >= 2.193 kW | Stelrad Classic Compact K2 | 1600 x 450 | 2 | 50 / 65 / 35 °C | source token `2250`* |
| 18 | Bathroom | >= 0.673 kW | Compact Vertical K2 | 500 x 1800 | 1 | 50 / 65 / 35 °C | 1.015 kW |
| 11 | Bedroom | >= 1.905 kW | Stelrad Classic Compact K2 | 2200 x 600 | 1 | 50 / 65 / 35 °C | 1.956 kW |
| 11 | Living Room | >= 2.078 kW | Stelrad Classic Compact K2 | 2400 x 600 | 1 | 50 / 65 / 35 °C | 2.134 kW |
| 11 | Bathroom | >= 0.302 kW | Stelrad Caliente Rail (Straight Single) | 450 x 1199 | 1 | 50 / 65 / 35 °C | 0.315 kW |

`*` The column is labelled kW, but the Flat 18 living-room source token is rendered as `2250` rather than a decimal kW value. P54 does **not** silently convert this to `2.250 kW`. The raw token is retained and numeric proposed-capacity materialization for that one row is blocked.

Hard boundary:

`SOURCE TOKEN 2250 UNDER kW HEADER != SILENTLY NORMALIZED 2.250 kW`

unless an authoritative corrected source or explicit unit clarification is recovered.

## 5. Exact old -> new room pairs

P54 can therefore materialize six explicit room-grain engineering pairs.

Examples:

### Flat 18 — Bedroom 1

`Double Panel 800x600 @ 80/60 °C; estimated 1.385 kW`

`->`

`Stelrad Classic Compact K2 1600x600 x1 @ 65/35 °C; estimated 1.421 kW`

### Flat 11 — Bedroom

`Double Panel 1110x600 @ 80/60 °C; estimated 1.905 kW`

`->`

`Stelrad Classic Compact K2 2200x600 x1 @ 65/35 °C; estimated 1.956 kW`

### Flat 11 — Bathroom

`Single Panel 410x450 @ 80/60 °C; estimated 0.302 kW`

`->`

`Stelrad Caliente Rail 450x1199 x1 @ 65/35 °C; estimated 0.315 kW`

This directly demonstrates the programme-relevant engineering mechanism:

`LOWER WATER TEMPERATURE -> EMITTER RESIZING / TYPE CHANGE WHILE PRESERVING REQUIRED ROOM CAPACITY`.

## 6. Bounded quantitative result

Within this recovered pair table:

- apartments represented: **2**;
- paired room positions: **6**;
- existing radiator positions: **6**;
- proposed radiator units: **7**;
- existing common flow/return: **80/60 °C**;
- existing mean water temperature: **70 °C**;
- proposed common flow/return: **65/35 °C**;
- proposed mean water temperature: **50 °C**;
- mean-water-temperature reduction: **20 °C**;
- proposed-capacity rows with clean numeric values: **5**;
- source-unit-anomaly rows: **1**.

These numbers are valid only inside the six-row source cohort.

## 7. Critical scope boundaries

The source is technically strong but must not be promoted beyond what it proves.

Canonical non-equivalences:

`UK RESIDENTIAL ENGINEERING PAIR TABLE != HUNGARIAN RESIDENTIAL STOCK`

`TWO APARTMENTS != REPRESENTATIVE POPULATION SAMPLE`

`PROPOSED SCHEDULE != IMPLEMENTED / COMMISSIONED OUTCOME`

`DISTRICT-HEATING RETROFIT DESIGN != HEAT-PUMP RETROFIT EVIDENCE`

`LOWER-TEMPERATURE EMITTER RESIZING PRECEDENT != NATIONAL REPLACEMENT FRACTION`

`SAMPLE EXISTING MANUFACTURER/MODEL != EXACT INSTALLED SKU IDENTITY`

`SIX EXISTING POSITIONS -> SEVEN PROPOSED UNITS != NATIONAL UNIT MULTIPLIER`

All five P42 national radiator claims therefore remain `Q / programme_use_allowed=NO`.

## 8. Why this still matters to the original programme

P54 is not a Hungarian stock weight. Its value is different and narrower.

It proves with an official residential engineering report that a lower-temperature redesign can be represented as an explicit, auditable mapping:

`dwelling + room + existing type/size + existing temperature/output`

`->`

`required capacity + proposed type/size/count + proposed temperature/output`.

That is exactly the data shape needed later for the programme's per-dwelling emitter decision engine:

`POST-ENVELOPE ROOM HEAT LOSS`

`+ EXISTING EMITTER IDENTITY/SIZE`

`+ TARGET WATER TEMPERATURE`

`-> KEEP / UPSIZE / CHANGE`

`-> REQUIRED NEW EMITTER OUTPUT/SIZE`.

P54 therefore supplies a real pair-table precedent for the transformation logic while leaving population weighting and Hungarian stock calibration to separate evidence.

## 9. Reserve findings retained, not promoted

The search also found several useful but incomplete sources. They are retained here as reserve discovery paths rather than primary P54 authority.

### Reserve A — Cozy Energy, 86 Byne Road, London

`https://docs.planning.org.uk/20250317/108/SQ3390BTLMA00/6el06lm8uqcpbkql.pdf`

Residential ASHP proposal; 50 °C proposed flow temperature; room-level existing radiator outputs; exact proposed Type 22 sizes and outputs. Rejected as primary pair-table source because existing radiator physical type/size is not published in the same schedule.

### Reserve B — 21 Highfield Road, Bromley / EF1313

`https://docs.planning.org.uk/20230522/108/RUW3G6BTMQ900/n3gp93r3dnhwaamm.pdf`

Residential ASHP retrofit requirements with an explicit existing-radiator schedule containing room, width, height and panel/fins type. Rejected as primary pair-table source because the final proposed radiator design is left to the contractor and is not published as a filled new-emitter schedule.

### Reserve C — ECO4 Daikin EDLA08 installation design assessment

`https://docs.planning.org.uk/20240321/87/S9OIB9GDGQN00/yl75wrr75j1a2c82.pdf`

Residential ASHP design at 45 °C flow with room-level existing-radiator performance percentages and exact proposed K3 sizes/outputs. Rejected as primary pair-table source because the old radiator type/size is absent from the radiator report.

These reserves remain useful for later heat-pump-specific triangulation, but none is allowed to overwrite the stronger old/new dimensional pair authority recovered from Noel Coward House.

## 10. Repository contract

`modules/B02/low_temp_radiator_before_after_pairs.py` provides:

- `RadiatorBeforeAfterPair`;
- `RadiatorPairSummary`;
- `validate_radiator_before_after_pair()`;
- `summarize_radiator_before_after_pairs()`;
- explicit non-promotion functions for implementation, heat-pump, Hungarian-stock and national-P42 authority.

`registry/b02_p54_noel_coward_radiator_before_after_pairs.csv` materializes exactly the six matched apartment-room pairs.

No external source binary is committed.
