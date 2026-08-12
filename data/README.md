# Adatkezelés

A nagy vagy licenckorlátozott nyers adatok nem kerülnek automatikusan Gitbe.

A repository a következőket őrzi:

- forrás URL-je és lekérési dátuma;
- eredeti fájlnév és verzió;
- licenc vagy felhasználási korlát;
- SHA-256 lenyomat, ha helyi snapshot készült;
- reprodukálható letöltési és feldolgozási lépés;
- a feldolgozott adatkészlet sémája és minőségellenőrzése.

A `data/raw/` és `data/interim/` helyi munkaterület, ezért Git által figyelmen kívül hagyott. Publikálható, kisméretű eredményt csak licencellenőrzés után szabad verziókezelni.

A `data/processed/` kizárólag kis méretű, nyilvános licenc alatt újraközölhető és determinisztikusan regenerálható feldolgozott adatot tartalmazhat. Minden ilyen csomaghoz forrás-URL, lekérési dátum, forráslenyomat, generáló eszköz és visszaegyeztetési kontroll szükséges.
