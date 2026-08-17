# Hőszigetelés + hőszivattyú + akkumulátor országos modell

Nyilvános, forrásolt és reprodukálható kutatási projekt egy magyarországi, országos léptékű hőszigetelési, hőszivattyú- és háztartásiakkumulátor-program műszaki, hálózati, pénzügyi, fiskális, társadalmi és környezeti feltételeinek vizsgálatához.

## Jelenlegi állapot

**P0 — kutatási infrastruktúra és V1.2-szerződés.** A repository a kutatás szerződését, modulstruktúráját, bizonyítási szabályait, a B02 reprodukálható adat-alapját és a lépcsőzetes országos projektportfólió gépi szerződésének üres vázát tartalmazza. Még nem közöl végleges szakpolitikai következtetést vagy validált országos portfóliószámot.

## Alapelv

Előbb a fizika és az adatok, utána a pénzügy. Előbb a kanonikus modell, utána a kommunikáció és az interaktív alkalmazás.

A jelenlegi program-egység egy fázisokon átvezetett háztartási beavatkozás az éves portfólióban, nem egyszeri telepítés. Az állapotgép és a portfólió-kapuk szerződése: [`docs/methodology/v12_portfolio_transition_contract.md`](docs/methodology/v12_portfolio_transition_contract.md).

Minden érdemi számnak visszavezethetőnek kell lennie:

1. forrásra vagy explicit feltételezésre;
2. kanonikus változóazonosítóra;
3. mértékegységre;
4. képletre vagy transzformációra;
5. érvényességi tartományra;
6. az eredményt használó modulokra.

## Projektfelépítés

- `modules/` — a B01–B20 kutatási modulok szerződése és státusza;
- `registry/` — forrás-, adatkészlet-, archetípusdimenzió-, változó-, képlet-, kérdés- és modulregiszter;
- `registry/` — a V1.2 állapot-, beavatkozás-, prioritás-, portfólió-, readiness-, baseline-, inkrementális CAPEX- és fiskális headroom-sablonok;
- `data/` — adatkezelési és reprodukciós szabályok;
- `model/` — a későbbi számítási motor;
- `scenarios/` — forgatókönyvek és stressztesztek;
- `docs/` — módszertan és generált jelentések;
- `app/` — a B20 lezárása után elkészülő alkalmazás;
- `tests/` és `tools/` — automatikus szerződés- és minőségellenőrzés.

## Közreműködés

A repository nyilvánosan olvasható. Külső közreműködők Issue, Discussion vagy forkból indított Pull Request formájában tehetnek javaslatot. A kanonikus repository írási és merge-jogosultságát Joseph gyakorolja; Aion és Codi kizárólag Joseph felhatalmazásával dolgozik. Részletek: [GOVERNANCE.md](GOVERNANCE.md) és [CONTRIBUTING.md](CONTRIBUTING.md).

## Publikációs megjegyzés

A belső kiinduló dokumentumok nem részei az első nyilvános kiadásnak. Publikálásuk csak külön tartalmi, adatvédelmi és licencellenőrzés után történhet.
