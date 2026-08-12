# B02 feldolgozott KSH energetikai kivonat

Forrás: KSH, *A magyar lakásállomány primerenergia-igényének becslése*, 2025-11-14.

## Fájlok

- `ksh_energy_archetype_benchmarks_2022.csv`: 16 épülettípus × építési időszak benchmark;
- `ksh_energy_distribution_2022.csv`: 944 publikált épülettípus × építési időszak × energiaigény-bin;
- `ksh_energy_class_distribution_2022.csv`: TNM és ÉKM országos osztálymegoszlás;
- `ksh_energy_coverage_2022.csv`: megfigyelt, modellezett és levezetett lefedettségi kontrollok;
- `ksh_energy_extract_manifest.json`: forrás-URL-ek, SHA-256 lenyomatok és kötelező sor-/összegkontrollok.

## Újragenerálás

```powershell
node tools/extract_b02_ksh_energy.mjs --output-dir data/processed/b02 --retrieved-at 2026-08-12
```

A kivonó nem hajt végre távoli JavaScriptet. Csak a KSH HTML-ben publikált, korlátozott karakterlánc- és numerikus tömbszerkezeteket fogadja el, és alakeltérés esetén hibával leáll.

## Bizonyítékstátusz

- a módszertani lakásuniverzum és a kapcsolt tanúsítványszám `OBS`;
- a random-forest energiaigény és a teljes állományra vetített eloszlás `MODELLED`;
- az összegek, maradék és arányok `DER`.

A 99,896%-os publikált-bin lefedettség nem tanúsítvány-mérési lefedettség. A tanúsítvánnyal összekapcsolt lakások publikált aránya 6,1%; a többi lakás energiaigénye modellbecslés.
