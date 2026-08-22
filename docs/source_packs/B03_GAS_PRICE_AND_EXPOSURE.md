# B03 – Gázár és földgáz-kitettség

## Cél és lezárási állapot

Ez a csomag a B03 kanonikus gázár-motort írja le. A három ár-réteg külön marad:

1. `WHOLESALE_IMPORT`: TTF/EEX/ICE vagy ACER nagykereskedelmi benchmark, EUR/MWh → EUR/HUF → HUF/m³; ez kizárólag a B11 importértékhez használható.
2. `MARKET_RESIDENTIAL_FINAL`: commodity + network + storage + commercial + tax/VAT/other komponensek; ez a B12 piaci lakossági cash-flow bemenet.
3. `REGULATED_RESIDENTIAL_TARIFF`: a hatályos egyetemes szolgáltatási, kedvezményes és küszöb feletti sáv; ez a B13 baseline.

Az adatcsomag **Q/OBS fail-closed** állapotban van: a forráskapuk, a sémák és a dimenzióbiztos képletek rögzítve vannak, de licencelt TTF-idősor, teljes komponenshíd és a hatályos MVM Ft/m³ tarifatáblázat helyi, reprodukálható snapshotja nélkül numerikus végárat nem állítunk elő.

## Forrás- és adatpolitika

- P1/P2 hivatalos vagy elsődleges piaci forrás; minden értékhez `source_id`, referencia-időszak, lekérési dátum és státusz tartozik.
- Hiányzó vagy licenckorlátos érték `Q`, nem helyettesíthető becsléssel.
- A 2026-08-22 közeli snapshot külön kezelendő a 2015–2026 historikus sortól.
- Forward zóna: hivatalos TTF forward görbe elérhető lejáratig. Long-run zóna: csak dokumentált scenario-paraméter, nem implicit extrapoláció.
- A `GAS-LOW`, `GAS-BASE`, `GAS-HIGH`, `GAS-STRESS` pályák nem adhatnak át retail komponenst wholesale változóként és fordítva.

## Kanonikus képletek

Ha `eur_per_mwh`, `eur_huf` és `heating_value_kwh_per_m3` mind ismert:

`wholesale_huf_per_m3 = eur_per_mwh * eur_huf * (heating_value_kwh_per_m3 / 1000)`

Az itteni registry-változó fűtőértéke `MJ/m³`, ezért az ekvivalens alak `eur_per_mwh * eur_huf * (heating_value_mj_per_m3 / 3600)`.

A piaci lakossági híd csak teljes komponenskészlettel számolható:

`market_residential_huf_per_m3 = commodity + network + storage + commercial + tax + vat + other`

A szabályozott éves költség:

`discounted_volume * discounted_price + max(0, annual_volume - threshold_volume) * above_threshold_price`

Ha bármely szükséges input hiányzik, a kimenet üres marad és `Q` státuszú marad. Nincs dupla felhasználás: wholesale/import és retail/final változó külön downstream interfész.

## Jelenlegi nyitott kapuk

1. Az ACER/EEX/ICE adatcsatorna licenc-, termékkód- és snapshot-szabálya.
2. A 2015–2026 TTF historikus és 2026-08-22 közeli forward numerikus export.
3. A pont- és időszakfüggő fűtőérték kWh/m³-ben.
4. A market-residential minden komponensének hatálynapos, magyar forrású értéke.
5. Az MVM aktuális kedvezményes és küszöb feletti Ft/m³ díja, a 63 645 MJ / legalább 1 729 m³ éves küszöb és az Aug 1–Jul 31 elszámolási év mellett.

## Downstream használat

- B11: csak `WHOLESALE_IMPORT`.
- B12: csak `MARKET_RESIDENTIAL_FINAL`.
- B13: csak `REGULATED_RESIDENTIAL_TARIFF`.
- B15/B16: csak a fenti rétegek explicit lineage-ével; egy réteg másik réteg hiányát nem pótolhatja.
