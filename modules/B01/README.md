# B01 – Programterjedelem és penetráció

## Cél

Éves háztartási állapotállomány és országos projektportfólió-pálya előállítása országos és területi bontásban. A modul nem tekinti a programot egyszeri, azonos csomagú telepítési kampánynak.

## Bemeneti szerződés

- célháztartások száma (`VAR-B01-TARGET-HOUSEHOLDS`);
- programhorizont (`VAR-B01-HORIZON-YEARS`);
- felfutási profil (`VAR-B01-RAMP-PROFILE`);
- területi felbontás (`VAR-B01-REGIONAL-RESOLUTION`);
- B02 technikailag alkalmas állománykorlátja;
- később B18 éves kivitelezési kapacitása.
- háztartási állapotgép és az előző fázis bizonyítéka;
- beavatkozási katalógus és prioritási komponensek;
- éves közpénz-, társadalmi minimum-, hálózati- és regionális korlátok.

## Kimeneti szerződés

- éves új telepítések, `household/year`;
- év végi kumulált állomány, `household`;
- éves S0–S5 állapotállomány és fázisátmeneti darabszám;
- jelölt és kiválasztott beavatkozások, várakozási idő és kötő korlát;
- minden kiválasztáshoz „miért most / miért itt / mi hiányzik” magyarázat;
- régiónkénti éves és kumulált állomány;
- kielégítetlen szakpolitikai cél kapacitáskorlát esetén.

## Invariánsok

- a kumulált állomány nem csökkenhet;
- nem haladhatja meg sem a szakpolitikai célt, sem a B02 alkalmas állományát;
- az országos érték a területi értékek összege;
- minden pálya ugyanazon kezdő- és záródefinícióval hasonlítható össze.
- az állapotátmenet csak bizonyított kapu után haladhat előre;
- egyetlen éves kiválasztási súly vagy hard minimum sem lehet rejtett konstans;
- az országos portfólió kiválasztott darabszáma nem haladhatja meg az éves pénz-, FTE-, beszállítói-, engedélyezési- vagy hálózati korlátot.

## Canonical component assessment

`engine.assess_household_capabilities(CapabilitySnapshot(...))` evaluates the
versioned `registry/household_capability_contract.json` contract. Installation
order is not evidence of a physical component. A battery, qualified existing
insulation/envelope or heat pump may be recorded independently; a proposed heat
pump still needs its own building-specific sizing, emitter, hydraulic,
electrical and site prerequisites.

The returned assessment separates:

- historical accepted component completion and current dated availability;
- technical prerequisites and programme preconditions for proposed actions;
- the technically accepted complete heat-pump + battery + insulation package;
- subsidy-exit conditions, including the separate total-bill, full household
  cashflow, programme eligibility and exact applicable subsidy/timing claims;
- grid charge, household discharge, export and state/aggregator-service
  permission conditions and separate programme-operation preconditions. One
  operation's permission does not imply another's; a valid right cannot bypass
  the household floor when programme operation is assessed.

`PASS` is an assessment of supplied qualified record evidence. It does not
verify the underlying source, calculate B12 cashflows, grant a permission,
select an intervention, spend money or schedule work. Passed action
prerequisites do not create completed equipment and do not imply a need to
repeat an already completed action. No own PV is required.

Every fact has a household, site, comparison/configuration basis, truth
context and evidence lineage. Current assertions use explicit half-open date
intervals; expiry or withdrawal can disable current capability/rights while
retaining completion history. Population estimates cannot certify an individual
record. `SCN` remains a scenario, missing facts remain `UNKNOWN`, and an explicit
negative condition remains `FAIL`. A missing financial condition does not erase
an observed installed asset.

Shared programme-eligibility and cashflow assertions carry an explicit
`applies_to` set of action, operation or subsidy-exit subjects. HP-only evidence
cannot qualify a battery action. Package-wide evidence must name every covered
subject; an omitted scope or an `ALL` wildcard cannot widen it. For state
service, the full household comparison includes foregone arbitrage, losses,
wear and assigned replacement costs. The strict JSON decoder rejects unknown
fields instead of silently dropping a conflicting scope or legacy record.

The executable demonstration is
`engine.run_capability_fixture("data/fixtures/b01_capability_scn.json")`.
It shows a synthetic battery-first record with unknown HP/envelope, programme
completion, subsidy exit and operation rights. It contains no real household,
price, national weight, dispatch quantity or funded selection.

`engine.migrate_legacy_capability_record(...)` preserves a valid legacy record
as versioned provenance. It creates no component or condition assertion from
S1, S4 or S5. New claim-specific evidence must be supplied independently.

See [V1-062 boundaries and migration](../../docs/checkpoints/V1_062_B01_CAPABILITY_CONTRACT.md).

## Executable B01-P1 compatibility contract

`registry/household_state_model.json` a történeti S0–S5 state-record,
transition-, policy- és capacity-contract kompatibilitási változata. A régi
`modules/B01/engine.py` függvények ezt töltik be, változatlan eredményekkel.
A lineáris állapotcímkék nem a fenti komponens-, támogatáskilépési vagy
jogosultsági állítások bizonyítékai. A régi éves kiválasztás háztartásonként
egyetlen szomszédos átmenetet kezel; az éven belüli többfázisú ütemezés és
közös éves erőforráskeret külön, még nyitott auditfeladat.

- `HouseholdStateRecord` csak explicit state-as-of, owner, next gate,
  eligibility és transition evidence mellett értékelhető.
- `OBS`/`DER` gate evidence nélkül az átmenet `BLOCKED/Q`; `ASS`, `SCN` és
  `Q` nem teljesíthet egy observed household transitiont.
- A meglévő hőszivattyú-jelző, fogyasztás, épületkor, tarifa vagy archetípus-
  becslés önmagában nem emel állapotot.
- A kiléptetett állapot csak monotónusan változhat; a kihagyás explicit,
  már teljesült exit-gate evidence nélkül tiltott.
- A candidate intervention a state predecessorhez, gate evidence-hez,
  kilenc V1.2 komponenshez és explicit resource-needs mezőkhöz kötött.
- MCDA, lexikografikus és capacity-limited ordering csak teljes, explicit
  `POL`/`SCN`/`DER`/`OBS` policy-paraméterekkel fut; hiányzó érték nem nulla.
- A state-stock aggregáció konzervál, régiós összeget képez, és csak `SCN`
  outputot ad. A bounded fixture nem országos eligible-stock vagy rollout
  eredmény.

Bounded fixture: `data/fixtures/b01_state_stock_scn.json`.

## Executable B01-P2 national rollout pathway

`modules/B01/national_rollout_pathway.py` a nemzeti rollout matematikát teszi
gépileg végrehajthatóvá, de **nem tart fenn fix országos programme targetet**.

A korábbi `2 000 000` érték csak a kezdeti, 2026. augusztusi munkahipotézis;
nem current baseline és nem programme ceiling.

A programme target explicit `POL`/`SCN` input marad. A profil-contract:

- `LINEAR`;
- `LOGISTIC` — explicit midpoint és steepness nélkül fail-closed;
- `CAPACITY_LIMITED` — minden tervévre explicit kapacitásérték szükséges;
- horizon: 8–25 év;
- report points: 12 / 15 / 20 év.

Minden generált pathway `SCN`. A `NationalSelectionGate` csak akkor nyithat real
national selectiont, ha a B02 eligible stock, a valós éves capacity path és a
célháztartás jogi/műszaki definíciója is OBS/DER authorityval rendelkezik.

Registry: `registry/b01_national_rollout_policy_contract.csv`.

## B01-P3 exact non-district-heated population base

`modules/B01/non_district_population.py` kizárólag a commitolt
`WBL011_HEATING_FUEL` OBS projekció 7 682 celláját aggregálja. A KSH diszjunkt
fűtési mód-partíciójában `HEAT12` a távfűtés.

A kanonikus 2022-es fizikai bázis:

- lakott lakások: **4 008 541**;
- távfűtött lakott lakások: **618 724**;
- **nem távfűtött lakott lakások: 3 389 817**.

A P2-ben ideiglenesen használt **3 403 746** kerekített-share becslést P3
felülírja; az csak történeti auditérték marad. A P3-registry húsz
vármegye/Budapest DER sort és egy országos kontrollsort materializál:
`registry/b01_non_district_heated_population_2022.csv`.

A 3 389 817-es állomány programme-releváns fizikai kiinduló univerzum, de
**nem B02 technikai alkalmasság**, nem programme target és nem kiválasztott
háztartás. Utility customer count továbbra sem használható ház-/lakásszámként.

## B01-P4 canonical target variable harmonization

A globális `registry/variables.csv` most már ugyanazt a target-szemantikát
követi, mint P2/P3. A `VAR-B01-TARGET-HOUSEHOLDS` numerikus `default_value` és
`max_value` nélkül, `Q` státuszban áll.

A korábbi 2 000 000 default és 2 500 000 ceiling csak legacy auditkontextus;
egyik sem használható automatikus targetként vagy population ceilingként. A
3 389 817 exact nem-távfűtött fizikai állomány szintén nem programme target és
nem B02 eligibility.

Minden rollout futásnak explicit `POL`/`SCN` targetet kell megadnia, és ha a
futtatás population reference-et használ, annak értéke, státusza és szemantikája
külön explicit input.

## Állapot

`IN_PROGRESS` – a B01-P1 state/portfolio contract és a B01-P2 rollout matematika
gépileg végrehajtható; B01-P3 az országos és vármegyei nem-távfűtött lakott
lakásbázist exact WBL011 cellákból rögzíti; B01-P4 eltávolítja a legacy 2M/2.5M
aktív target/default szemantikát a globális variable registryből. A canonical
programme target továbbra is `Q`; a Q-B01-001 célháztartás-definíció, a B02
national eligible stock, a valós éves capacity path, valamint a tényleges
regional/settlement household allocation továbbra sincs lezárva.

## V1 public stock-flow controls

The [public KSH stock-flow handoff](../../docs/checkpoints/V1_004_B01_PUBLIC_STOCK_FLOW.md) reconciles total county stock across 2023–2025. It does not replace the 2022 occupied/non-district programme denominator or infer eligibility. The 2022 source reference is October 1; later stock dates are January 1.

## V1 conditional national accounting screens

[National count and source-accounting bounds](../../docs/checkpoints/V1_047_NATIONAL_ACCOUNTING_BOUNDS.md)
combine native 2022 census group counts and the admitted JRC ledger in a
parametric necessary-condition screen. Above-cap requirements are excluded
within their stated boundaries; other requirements remain INCONCLUSIVE.
The gas ledger includes natural gas and biogas. Nonempty selected groups
retain the whole ledger cap, with no proportional heat assignment. Central
heat allocation, eligibility and national feasibility remain unresolved.
