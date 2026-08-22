# B04 – Villamosenergia-ár, tarifák és háztartási elektrifikációs árinterfész

Snapshot: 2026-08-22. Ez a dokumentum a háztartási villamosenergia-költség kanonikus árinterfésze; a B03 gáz- és OÉNY/P1K artefaktumokat nem módosítja.

## Rétegek

1. **WHOLESALE_ELECTRICITY** – HUPX day-ahead/forward benchmark EUR/MWh. A teljes 2015–2026 history és a 2026-08-22 forward görbe licencelt export hiányában Q. Egyetlen ellenőrző OBS pont a HUPX 2026. márciusi DAM baseload 103.52 EUR/MWh.
2. **REGULATED_RESIDENTIAL_ELECTRICITY** – A1/A2/B lakossági ársávok, mérőnként és felhasználási helyenként 2523 kWh/év küszöbbel, augusztus 1.–július 31. elszámolási évvel és 27% ÁFÁ-val. Az A1 current snapshot az MVM 2026. március 1-jén hatályos M.1 melléklete és a hivatalos területi díjtábla alapján készült.
3. **H_TARIFF** – külön mért, állandóan bekötött kéttarifás mérőkör; október 15.–április 15. idény, legalább 3.4 szezonális fűtési tényező, hőszivattyú/megújuló hőtermelő és közvetlenül kiszolgáló segédberendezések. Idényen kívül az A1 magasabb ára fut.
4. **MARKET_BASED_RESIDENTIAL_ELECTRICITY** – küszöb feletti lakossági végső ár. Nem azonos a HUPX nagykereskedelmi árral; az aktuális komponenshíd részleges/Q.
5. **DYNAMIC_ELECTRICITY** – HUPX spot elérhetősége nem bizonyít lakossági dinamikus terméket. Háztartási termék, jogi és mérési feltétel hiányában Q.

## 2026-08-22-i tarifakapuk

Az MVM M.1 nettó/bruttó energiaár-táblája szerint az A1 energia-komponens nettó/bruttó értékei elosztói területenként: MVM Démász 5.25/6.67; E.ON Dél/Észak és OPUS 4.39/5.58; ELMŰ 5.11/6.49; MVM Émász 4.94/6.27 Ft/kWh. A hivatalos területi díjtábla szerinti A1 kedvezményes végső bruttó árak: 36.386; 35.293; 36.208; 35.992 Ft/kWh. A küszöb feletti A1 lakossági piaci végső bruttó kontrollérték 70.104 Ft/kWh.

H idényben a végső bruttó területi értékek: 22.962; 23.520; 23.152; 22.682 Ft/kWh. Az H mérőkör idényen kívüli fogyasztása az A1 magasabb ársávja szerint fut. A fix díj, hálózati díj és adó külön komponensként szerepel; a 2026-os teljes jogi komponenshíd még nem tekinthető teljesen lezártnak.

## Kanonikus számlaképlet

```text
annual_bill =
  min(consumption_kwh, threshold_kwh) * discounted_gross_huf_per_kwh
  + max(consumption_kwh - threshold_kwh, 0) * higher_gross_huf_per_kwh
  + applicable_fixed_charge
```

Fix díj egyszer szerepel. A H idénybeli mennyiséget nem szabad automatikusan az A1 mérő 2523 kWh keretével összevonni; a mérőkör és az idény szerinti allokáció külön input. MWh → kWh átszámítás: `EUR/MWh × HUF/EUR / 1000 = HUF/kWh`.

## Akkumulátor és downstream használat

Az MVM-források H tarifára jogosult hőszivattyút/megújuló hőtermelőt és közvetlenül kiszolgáló készülékeket írnak le. Akkumulátortöltésre, export/VPP-re nincs explicit bizonyíték, ezért mindkettő **Q**, és az engine fail-closed. B05 csak a validált A1/H hőszivattyú inputokat használhatja; B07 nem tehet akkumulátort H mérőkörre. A HUPX érték nem bridge-elhető automatikusan lakossági végső árra.

## Források és fennmaradó Q-k

- MVM M.1 melléklet (hatály: 2026-03-01), MVM H tarifa FAQ, MVM lakossági díjtábla és számlamagyarázat: `registry/electricity_price_sources.csv`.
- HUPX DAM adatszolgáltatási specifikáció és licencelés: a teljes history/forward numerikus export Q.
- MEKH/NJT rendszerhasználati díjak: a jelenlegi 2026-os komponenshíd teljes táblázati kibontása Q/partial.
- Lakossági dinamikus termék, H akkumulátor/export szabály és wholesale → retail bridge: Q.

## Readiness

`REGULATED_RESIDENTIAL_ELECTRICITY=VALIDATED`; `H_TARIFF=PARTIAL`; `WHOLESALE_ELECTRICITY=Q`; `MARKET_BASED_RESIDENTIAL_ELECTRICITY=PARTIAL`; `DYNAMIC_ELECTRICITY=Q`; `BATTERY_TARIFF_INTERFACE=Q`. A teljes B04 státusza ezért `BLOCKED`; ez nem emeli a B03 vagy más modul státuszát.
