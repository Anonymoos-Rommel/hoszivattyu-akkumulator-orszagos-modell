# B10-P36 — MVM ÉMÁSZ / KSH service-area crosswalk expansion

Canonical base: `c950050a3986fcd8483861daf4a47d68c585dda6`

## Scope

P36 is an **evidence/data slice**. It adds bounded MVM Émász whole-settlement service-area evidence to the existing P15/P20/P21 crosswalk semantics. It introduces no new semantic contract and does not claim a complete MVM Émász or national inventory.

## Core boundaries

`SETTLEMENT NAME != KSH SETTLEMENT ID`

`KSH SETTLEMENT ID != DSO SERVICE-AREA MEMBERSHIP`

`WHOLE SETTLEMENT != NAMED SUBSETTLEMENT`

`DSO SERVICE-AREA MEMBERSHIP != EXACT DSO NODE`

`PUBLIC FACT USE != SOURCE-DOCUMENT REPUBLICATION != BULK DATABASE RECONSTRUCTION`

`PRIMARY KSH LOCATOR + DERIVED MACHINE LOCATOR != DIRECT PRIMARY ROW OBSERVATION`

These boundaries are fail-closed. A settlement name in the M1 does not create a KSH identity by itself, and a KSH identity does not prove DSO membership without the DSO authority.

## Authority chain

### MVM Émász membership authority

Existing source ID:

`SRC-B10-MVM-EMASZ-M1-2026`

The current official MVM Émász business-rule landing exposes the `2026.05.26-tól` package. Its official M1 attachment is titled **“Az MVM Émász Áramhálózati Kft. területi illetékessége”** and directly lists the service-area names used by P36.

Current verification locators:

- landing: `https://mvmemaszhalozat.hu/tarsasagunk/jogszabalyok-szabalyzatok/uzletszabalyzat`
- current M1 attachment: `https://mvmemaszhalozat.hu/-/media/emaszhalozat/emasz-halozat-uzletszabalyzat-szabalyzatok/uzletszabalyzat-20260526/msz_uzletszabalyzat_melleklet_2025_i_md_2025_1022.ashx?hash=EB463FF2F46DD05995991DD2B7C06AEA4AAC0195&la=hu-hu`

The M1 mixes whole settlements and named settlement-parts. P36 therefore does not treat every comma-separated name as an independent KSH settlement.

### KSH identity authority and locator

Primary authority locator:

`SRC-B10-KSH-HNT-2025-SETTLEMENT-IDS`

`https://www.ksh.hu/docs/helysegnevtar/hnt_letoltes_2025.xlsx`

Reproducible machine-readable derivation helper:

`SRC-B10-KSH-HNT-2025-IRSZHNK-DERIVATION-2026`

`https://github.com/ferenci-tamas/IrszHnk/blob/master/IrszHnk.csv`

The derived CSV is used only to locate exact name/code pairs whose `Településrész` field is empty. It is not promoted to primary statistical authority. Because the binary KSH XLSX rows are not directly materialized in this workflow, every new P36 row remains **DER**, not OBS.

## P36 bounded materialization

P36 adds **40 additional** MVM Émász whole-settlement rows:

| KSH code | Settlement |
|---|---|
| `15662` | Abaújalpár |
| `26718` | Abaújkér |
| `02820` | Abaújlak |
| `03595` | Abaújszántó |
| `26338` | Abaújszolnok |
| `02273` | Abaújvár |
| `10357` | Abod |
| `33093` | Alacska |
| `20482` | Alsóberecki |
| `19664` | Alsódobsza |
| `14429` | Alsógagy |
| `16425` | Alsópetény |
| `23223` | Alsóregmec |
| `28839` | Alsószuha |
| `08217` | Alsótelekes |
| `07621` | Alsótold |
| `29814` | Alsóvadász |
| `21032` | Alsózsolca |
| `17987` | Andornaktálya |
| `07241` | Apc |
| `26198` | Arka |
| `14331` | Arló |
| `03771` | Arnót |
| `03823` | Ároktő |
| `04233` | Aszaló |
| `16188` | Aszód |
| `06503` | Átány |
| `16090` | Atkár |
| `09131` | Bag |
| `18184` | Baktakék |
| `22521` | Balajt |
| `13657` | Balassagyarmat |
| `11527` | Balaton |
| `25159` | Bánhorváti |
| `24341` | Bánk |
| `21953` | Bánréve |
| `20048` | Bárna |
| `08846` | Baskó |
| `33534` | Bátonyterenye |
| `24022` | Bátor |

For every new row:

- `operator_id = MVM_EMASZ`
- `service_area_id = MVM_EMASZ:SERVICE_AREA`
- `coverage_scope = WHOLE_SETTLEMENT`
- `usage_location_requirement = NONE`
- `evidence_status = DER`
- `status = WHOLE_SETTLEMENT_MEMBERSHIP_PROVEN`
- source chain = MVM Émász M1 + primary KSH locator + reproducible KSH-derived locator.

The five historical P21 MVM Émász rows remain unchanged **OBS** observations. Therefore the bounded MVM Émász tranche state after P36 is **45 materialized rows = 5 historical OBS + 40 P36 DER**. This number describes the P36 state; it is not a national-completeness claim or a permanent registry-size invariant.

## Named subsettlements excluded

The current M1 explicitly contains named settlement-parts such as:

- `Abaújdevecser (Encs)`;
- `Alatka (Heves)`;
- `Aranyospuszta (Abaújkér)`;
- `Baglyasalja (Salgótarján)`;
- `Bagolyírtás (Mátraszentimre)`;
- `Bánszállás (Ózd)`;
- `Benczúrfalva (Szécsény)`;
- `Bükkszentlászló (Miskolc)`.

P36 does not strip the parent settlement and promote these names into independent whole-settlement membership. Usage-location or settlement-part resolution remains outside this slice.

## Completeness boundary

The canonical national registry:

`registry/dso_service_area_membership_crosswalk.csv`

remains **header-only**.

P36 does not prove:

- a complete normalized MVM Émász settlement inventory;
- a complete national KSH-to-DSO membership crosswalk;
- usage-location resolution for named or partial settlements;
- exact DSO node identity;
- headroom, limiting node, reinforcement, reinforcement cost or programme-incremental CAPEX.

The blockers remain active, including:

- `NO_COMPLETE_KSH_DSO_MEMBERSHIP_CROSSWALK`
- `PARTIAL_SETTLEMENT_USAGE_LOCATION_RESOLUTION_REQUIRED`
- `NO_COMPLETE_NATIONAL_DSO_NODE_INVENTORY`
- `NO_REAL_PROGRAMME_NODE_PANEL`
- `INCREMENTAL_CAPEX_ATTRIBUTION_HEADER_ONLY`

B10 readiness remains **15%**.
