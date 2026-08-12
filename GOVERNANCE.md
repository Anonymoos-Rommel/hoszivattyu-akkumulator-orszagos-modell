# Governance

## Tulajdonosi és döntési rend

Joseph a repository kizárólagos tulajdonosa és végső döntéshozója. Más természetes személy, csapat vagy külső közreműködő nem kap közvetlen írási jogosultságot a kanonikus repositoryhoz.

Aion és Codi Joseph technikai jogosultságával, kizárólag Joseph által meghatározott vagy jóváhagyott feladat keretében dolgozhat.

## Szerepek

- **Joseph:** cél, prioritás, szakpolitikai döntés, publikáció és merge jóváhagyása.
- **Aion:** architektúra, kutatási feladatkijelölés és módszertani kontroll.
- **Codi:** kutatás, adatfeldolgozás, modell, kód, tesztek, dokumentumok és alkalmazás végrehajtása.
- **Külső közreműködők:** Issue, Discussion, review vagy fork-alapú Pull Request útján javasolhatnak.

## Változtatási rend

Az induló bootstrap commit után a `main` ág közvetlen módosítása tilos. Érdemi változtatás csak külön ágon, ellenőrzött Pull Requesten keresztül kerülhet a kanonikus állapotba.

Minden Pull Requestnek rögzítenie kell:

- a feladat és az érintett modul azonosítóját;
- a megengedett hatókört;
- a felhasznált forrásokat és bizonyítékokat;
- a változó- és képlethatást;
- az elvégzett teszteket;
- a készítő szerepét;
- Joseph döntését az összeolvasztás előtt.

## Külső javaslatok

A külső Pull Request javaslat, nem automatikus változtatási jog. A repository tulajdonosa szabadon kérhet módosítást, utasíthat el vagy fogadhat el javaslatot. Elfogadás előtt Codi reprodukálhatja és ellenőrizheti a hozzájárulást.

## Automatizálási határ

A GitHub Actions ellenőrizhet és jelenthet, de alapértelmezetten nem írhat repository-tartalmat, nem hagyhat jóvá Pull Requestet és nem hajthat végre merge-et.
