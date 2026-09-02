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

## Source-scoped legacy acceptance labels

A V1.1 brief a `Q-xx` rövid címkéket több fejezetben újrahasználja, ezért egy rövid címke önmagában továbbra sem lehet globális kérdésazonosító. Legacy acceptance-címke csak a következő négyes együttese alapján oldható fel:

1. forrásdokumentum;
2. forrásfejezet / szövegkörnyezet;
3. a kérdés pontos szemantikája;
4. az a consumer context, amely a legacy címkére hivatkozik.

A source-scoped mapping nem teszi a rövid címkét kanonikus azonosítóvá, és nem zárja le automatikusan az alatta maradó evidence-kapukat.

### Issue #10 — B10 legacy acceptance mapping

Forrás: `Hőszivattyú + akkumulátor országos program | Codex kutatási brief V1.1 | 2026-08-12`, a V1.2 kiegészítést is tartalmazó belső munkapéldány.

| Consumer context | Forráshely | Legacy címke | Forrás-szemantika | Kanonikus hivatkozások |
|---|---|---|---|---|
| GitHub Issue #10 — B10 | 6. fejezet, B08 csúcsterhelési modell | `Q-05` | Mekkora menedzselt országos csúcs mellett mekkora fizikai túlélőképességet kell kiépíteni; a válasz hálózati és N-1/N-2 rendszerbiztonsági elemzésből vezetendő le. | `B10-P10`; `NO_REAL_MANAGED_PEAK_SURVIVABILITY_STUDY` |
| GitHub Issue #10 — B10 | 23. fejezet, első körös kritikus kérdések | `Q-07` | Mekkora elosztói és átviteli hálózati beruházás kell regionálisan, és melyik évben válik bindinggá. | `Q-B01-002`; `Q-B10-001`; `Q-B10-002`; `B10-P11` |

Ez a két mapping kizárólag az Issue #10 consumer contextre érvényes. Különösen: a brief B14 finanszírozási fejezete szintén `Q-07` címkét használ a pályázati forrásból finanszírozható nemzeti programméret kérdésére; ez **nem** az Issue #10 B10-mappingje.
