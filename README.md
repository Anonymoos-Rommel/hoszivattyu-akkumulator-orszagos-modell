# Hőszivattyú + akkumulátor + Hőszigetelési országos modell

Nyilvános, forrásolt és reprodukálható kutatási projekt egy magyarországi, országos léptékű hőszigetelési, hőszivattyú- és háztartásiakkumulátor-program műszaki, hálózati, pénzügyi, fiskális, társadalmi és környezeti feltételeinek vizsgálatához.

## Jelenlegi állapot

**P0 — kutatási infrastruktúra.** A repository jelenleg a kutatás szerződését, modulstruktúráját, bizonyítási szabályait és géppel olvasható regisztereit tartalmazza. Még nem közöl végleges szakpolitikai következtetést vagy validált számszerű eredményt.

## Alapelv

Előbb a fizika és az adatok, utána a pénzügy. Előbb a kanonikus modell, utána a kommunikáció és az interaktív alkalmazás.

Minden érdemi számnak visszavezethetőnek kell lennie:

1. forrásra vagy explicit feltételezésre;
2. kanonikus változóazonosítóra;
3. mértékegységre;
4. képletre vagy transzformációra;
5. érvényességi tartományra;
6. az eredményt használó modulokra.

## Projektfelépítés

- `modules/` — a B01–B20 kutatási modulok szerződése és státusza;
- `registry/` — forrás-, változó-, képlet-, kérdés- és modulregiszter;
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
