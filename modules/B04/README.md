# B04 – Villamosenergia-ár és tarifák

## Cél

Háztartási hőszivattyú- és akkumulátortöltési költség előállítása tarifánként, elosztói területenként és hatályidő szerint.

## Bemeneti szerződés

- A1, A2, H és ténylegesen elérhető dinamikus tarifa energiaára;
- rendszerhasználati díjelemek;
- adók és ársávok;
- elosztói terület, mérőtípus, jogosultság és hatályidő;
- fogyasztás időprofilja és mérőkör-hozzárendelése.

## Kimeneti szerződés

- hőszivattyú teljes villamosenergia-költsége, `HUF/year`;
- akkumulátortöltés teljes költsége, `HUF/year`;
- tarifa- és díjkomponensenkénti bontás;
- H tarifás és normál mérőkör fogyasztásának külön kimutatása.

## Invariánsok

- H tarifás fogyasztás csak a jogosult időszakra és mérőkörre számolható;
- energiaár, rendszerhasználati díj és adó külön tétel;
- az elosztói terület és hatálynap kötelező dimenzió;
- akkumulátoros/VPP töltés nem rendelhető H tarifához elfogadott jogi-műszaki szabály nélkül.

## Állapot

`IN_PROGRESS` – a tarifa- és jogi forráskapuk rögzítve; a teljes hatálynapos díjtábla és az akkumulátoros mérőkör szabálya még nincs lezárva.
