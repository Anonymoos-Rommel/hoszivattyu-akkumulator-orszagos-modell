# B02-P12 — Calibrated linkage model admission

Állapot: **CONTRACT DEFINED / NO MODEL APPROVED**

Kapcsolódó kérdések: `Q-B02-001`, `Q-B02-002`, `Q-B02-004`

Ellenőrzés napja: **2026-09-05**

## Cél

A P1-G és P8/P9 által megengedett, de külön még nem formalizált statisztikai összekapcsolási út fail-closed admission contractja.

P12 **nem** választ modellt, nem kalibrál modellt, nem állít elő új cellaeloszlást és nem fogad el új függetlenségi vagy reprezentativitási feltételezést. A cél kizárólag annak meghatározása, hogy milyen minimális bizonyíték és governance kell ahhoz, hogy egy későbbi calibrated linkage model a P9 stock-archetype gate-ben felhasználható legyen.

## Kanonikus határok

`OBSERVED MARGINS != JOINT DISTRIBUTION != CALIBRATED LINKAGE MODEL`

`MODEL STATUS TOKEN != MODEL APPROVAL`

`CALIBRATION CONTROL != EVIDENCE PROMOTION`

`MATCHED TOTALS != REPRESENTATIVENESS != CELL-LEVEL VALIDITY`

`MODEL OUTPUT != OBS`

`MODEL QUALIFIED != CURRENT STOCK ARCHETYPE QUALIFIED`

Az utolsó határ különösen fontos: egy P12 szerint kvalifikált linkage model csak egyetlen P9 input-authorityt képes teljesíteni. A complete WBL joint, a másik linkage authority és a technical-readiness evidence ettől még külön kapu marad.

## Miért szükséges P12?

A P9 `archetype_admission_gate.py` korábban elfogadta az `APPROVED_CALIBRATED_MODEL` és `MODELLED_LINKED` státuszokat mint lehetséges authority-tokeneket, de nem volt külön végrehajtható szerződés arra, hogy ezeket mikor szabad kiadni.

P12 ezt zárja le. A P9 most csak akkor fogad el:

- `APPROVED_CALIBRATED_MODEL` building-type linket, ha a hozzá tartozó P12 model-admission státusz `QUALIFIED`;
- `MODELLED_LINKED` primary-energy linket, ha a hozzá tartozó P12 model-admission státusz `QUALIFIED`.

Egy string tehát többé nem tudja saját magát jóváhagyni.

## Admission contract

A `modules/B02/calibrated_linkage_admission.py` minden következő feltételt kötelezővé tesz:

1. explicit `model_id`;
2. explicit `APPROVED` státusz és `JOSEPH` approval authority;
3. legalább egy azonosított calibration source;
4. explicit calibration reference period;
5. WBL-kompatibilis target grain;
6. reprezentativitási diagnosztika;
7. dokumentált validation metrics;
8. marginal reconciliation;
9. explicit uncertainty method;
10. downstream uncertainty propagation kötelezővé tétele;
11. a függetlenségi feltételezések explicit kontrollja;
12. a modell output evidence státusza csak `ASS` vagy `MODELLED` lehet.

Bármely hiányzó feltétel esetén a döntés `Q`.

## Evidence semantics

A kalibrációhoz használt `OBS` vagy `DER` marginok nem teszik a modellből előállított joint cellákat `OBS`-szá.

A modell output:

- `ASS`, ha a felosztás dominánsan feltételezési szerződés;
- `MODELLED`, ha dokumentált kalibrált statisztikai modell állítja elő.

A P12 gate ezért kifejezetten elutasítja az `OBS` output státuszt.

Ha később egy determinisztikus repo-transzformáció MODELLED outputból új aggregátumot képez, annak lineage-ében a MODELLED eredet továbbra is megőrzendő; a DER címke nem törölheti a modell eredetét.

## P17 — KSH random-forest primary-energy candidate audit

P17 azonosítja a jelenleg legerősebb konkrét primary-energy linkage jelöltet:

`KSH-RF-2022-PRIMARY-ENERGY`

Forrásai:

- `SRC-B02-KSH-ENERGY-METHOD-2025`;
- `SRC-B02-KSH-ENERGY-2025`.

A KSH módszertan szerint a random-forest modell a 2022-es népszámlálási lakásállomány jellemzőiből becsüli a fajlagos primerenergia-igényt, és a végleges modellt a teljes census housing stockra alkalmazták. A publikáció reprezentativitási kontrollokat, keresztvalidációs/validation információt és aggregált megfigyelt-vs-becsült összevetéseket is közöl.

Ezért a machine-readable P12 registry P17 után már nem azt állítja, hogy primary-energy oldalon nincs azonosítható model candidate. A jelölt explicit módon regisztrált, de továbbra is **NOT_APPROVED / Q**.

A jelenlegi pozitív candidate-evidence:

- model ID: van;
- calibration sources: vannak;
- reference period: definiált;
- representativeness diagnostics: van;
- validation metrics: van;
- output evidence: `MODELLED`.

A jelenlegi blockers:

- `NO_JOSEPH_APPROVAL`;
- `TARGET_GRAIN_NOT_WBL_COMPATIBLE` — a nyilvános anyag nem ad repo-szinten reprodukálható record-level WBL bindingot;
- `NO_MARGINAL_RECONCILIATION` — nincs teljes WBL cellaszintű reconciliation contract;
- `NO_UNCERTAINTY_METHOD`;
- `NO_UNCERTAINTY_PROPAGATION`;
- `UNCONTROLLED_INDEPENDENCE_ASSUMPTION` — a repository linkage use-ra nincs külön explicit kontrollszerződés.

P17 tehát candidate discovery és governance-pontosítás, **nem Joseph approval** és nem model admission.

## Jelenlegi állapot

Jelenleg nincs Joseph által jóváhagyott calibrated linkage model sem:

- current building-type WBL linkage-re;
- current primary-energy-to-WBL linkage-re.

A building-type P12 claim továbbra is model candidate nélkül `Q`. A primary-energy P12 claim P17 után az azonosított `KSH-RF-2022-PRIMARY-ENERGY` jelöltet tartja nyilván, de `NOT_APPROVED / Q` státuszban.

Ez nem azt jelenti, hogy később modellezés tilos. Azt jelenti, hogy modellezés csak külön, explicit Joseph approval után léphet authority státuszba, és az approval önmagában sem helyettesíti a többi P12 gate-et.

## Tiltott következtetések

- Külön margókból nem készíthető automatikus cross-product.
- Egyező országos totalszám nem bizonyít reprezentativitást.
- A 2015/2022 building-type `ASS` proxy önmagában nem calibration authority.
- A KSH 944 MODELLED primerenergia-bin önmagában nem WBL-subcell link.
- A 279 020 kapcsolt energiatanúsítvány OBS darabszáma nem teszi a teljes 4,58 milliós modellkimenetet OBS-szá.
- A KSH random-forest belső dwelling-level alkalmazása nem azonos public repository-reproducible dwelling-level outputtal.
- Egy model-fit vagy backtest önmagában nem helyettesíti az uncertainty propagationt.
- P12 qualification önmagában nem zárja `Q-B02-001`, `Q-B02-002` vagy `Q-B02-004` kérdést.

## Hatás a B02 állapotára

- `Q-B02-001`: **OPEN**;
- `Q-B02-002`: **OPEN**;
- `Q-B02-004`: **OPEN**;
- current-stock archetype: **Q**;
- technical-readiness archetype: **Q**;
- national technical/final eligible count: **blank/Q**;
- B02 readiness: változatlanul **55%**;
- OÉNY adatkérés: **nem került elküldésre és P12/P17 nem ad küldési jóváhagyást**.

P12/P17 tehát governance- és admission-hardening, nem modellbevezetés és nem readiness-uplift.
