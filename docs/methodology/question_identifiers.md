# Nyitott kérdések azonosítása

A kanonikus kérdésazonosító formája: `Q-Bnn-nnn`.

- `Bnn` a kérdés elsődleges modulja;
- `nnn` a modulon belüli, nullákkal feltöltött sorszám;
- ugyanaz az azonosító nem használható újra más tartalomra;
- más modult érintő hatást a kérdés `decision_impact` mezője rögzíti, nem egy második azonosító.

Erre azért van szükség, mert a belső kiinduló kutatási brief különböző részei rövid `Q-01`, `Q-02` jelöléseket újrahasználtak. Ezek a rövid címkék nem kerülnek át a nyilvános kanonikus regiszterbe, mert nem biztosítanak globális egyediséget.

Lezárt kérdés azonosítója nem osztható ki újra. A válasz forrásait, döntési dátumát és a döntésre jogosult szereplőt a kérdés lezárásakor kell rögzíteni.

## V1.2 rövid címkék leképezése

A V1.2 belső brief rövid `H-12`–`H-15` és `Q-17`–`Q-22` címkéi nem kerülnek be változtatás nélkül a nyilvános regiszterbe. A `registry/open_questions.csv` globálisan egyedi rekordjai őrzik a tartalmi megfelelést:

| Belső címke | Nyilvános kérdésazonosító |
|---|---|
| H-12 | `Q-B01-003` |
| H-13 | `Q-B01-004` |
| H-14 | `Q-B01-005` |
| H-15 | `Q-B10-001` |
| Q-17 | `Q-B01-006` |
| Q-18 | `Q-B12-001` |
| Q-19 | `Q-B10-002` |
| Q-20 | `Q-B06-001` |
| Q-21 | `Q-B13-001` |
| Q-22 | `Q-B01-007` |

Ez a leképezés elsődleges modult rendel a kérdéshez; a downstream hatás a `decision_impact` mezőben marad. A rövid címke nem bizonyíték és nem válthatja ki a forrásolt választ.
