# B02 feldolgozott KSH adatcsomag

Források: KSH, *A magyar lakásállomány primerenergia-igényének becslése* (2025), valamint *Miben élünk? – A 2015. évi lakásfelmérés főbb eredményei*.

## Fájlok

- `ksh_energy_archetype_benchmarks_2022.csv`: 16 épülettípus × építési időszak benchmark;
- `ksh_energy_distribution_2022.csv`: 944 publikált épülettípus × építési időszak × energiaigény-bin;
- `ksh_energy_class_distribution_2022.csv`: TNM és ÉKM országos osztálymegoszlás;
- `ksh_energy_coverage_2022.csv`: megfigyelt, modellezett és levezetett lefedettségi kontrollok;
- `ksh_energy_extract_manifest.json`: forrás-URL-ek, SHA-256 lenyomatok és kötelező sor-/összegkontrollok.
- `ksh_building_type_source_2015.csv`: a KSH 2015 felmérés 1. táblájának 40 megőrzött lakásszáma;
- `ksh_building_type_proxy_2022.csv`: nyolc településtípus × épülettípus `ASS` proxyrekord;
- `ksh_building_type_proxy_manifest.json`: PDF- és API-hash-ek, kerekítési kontrollok és módszertani korlátok.

## Újragenerálás

```powershell
python -m pip install -r requirements-research.txt
node tools/extract_b02_ksh_energy.mjs --output-dir data/processed/b02 --retrieved-at 2026-08-12
python tools/build_b02_building_type_proxy.py --output-dir data/processed/b02 --retrieved-at 2026-08-12
```

A kivonó nem hajt végre távoli JavaScriptet. Csak a KSH HTML-ben publikált, korlátozott karakterlánc- és numerikus tömbszerkezeteket fogadja el, és alakeltérés esetén hibával leáll.

## Bizonyítékstátusz

- a módszertani lakásuniverzum és a kapcsolt tanúsítványszám `OBS`;
- a random-forest energiaigény és a teljes állományra vetített eloszlás `MODELLED`;
- az összegek, maradék és arányok `DER`.

A 99,896%-os publikált-bin lefedettség nem tanúsítvány-mérési lefedettség. A tanúsítvánnyal összekapcsolt lakások publikált aránya 6,1%; a többi lakás energiaigénye modellbecslés.

A 2015-ös KSH táblasorok `OBS` felmérési becslések. A 2015-ös településtípus-arányok 2022-es WBL lakásszámokra vetített eredménye `ASS`: nem közvetlen népszámlálási épülettípus-megfigyelés. A 2015-ös kerekített részösszegek 100 lakással eltérnek a közölt országos összesentől; ezt a manifest külön maradványként őrzi.
