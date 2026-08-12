# Nyitott kérdések azonosítása

A kanonikus kérdésazonosító formája: `Q-Bnn-nnn`.

- `Bnn` a kérdés elsődleges modulja;
- `nnn` a modulon belüli, nullákkal feltöltött sorszám;
- ugyanaz az azonosító nem használható újra más tartalomra;
- más modult érintő hatást a kérdés `decision_impact` mezője rögzíti, nem egy második azonosító.

Erre azért van szükség, mert a belső kiinduló kutatási brief különböző részei rövid `Q-01`, `Q-02` jelöléseket újrahasználtak. Ezek a rövid címkék nem kerülnek át a nyilvános kanonikus regiszterbe, mert nem biztosítanak globális egyediséget.

Lezárt kérdés azonosítója nem osztható ki újra. A válasz forrásait, döntési dátumát és a döntésre jogosult szereplőt a kérdés lezárásakor kell rögzíteni.
