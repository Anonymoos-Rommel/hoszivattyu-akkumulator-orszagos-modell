# B03 – Gázár és földgáz-kitettség

## Cél

Időben változó, auditálható gázárpályák előállítása külön nagykereskedelmi/importérték- és lakossági végár-kimenettel.

## Bemeneti szerződés

- termék- és lejáratspecifikus TTF spot/forward ár, `EUR/MWh`;
- időben illesztett EUR/HUF árfolyam, `HUF/EUR`;
- hálózati pont- és időszakspecifikus alsó hőérték, `MJ/m3`;
- rendszerhasználati, tárolási, kereskedelmi, adó- és rezsivédelmi komponensek;
- importmix és hosszú távú fundamentális forgatókönyv.

## Kimeneti szerződés

- nagykereskedelmi/importérték-proxy, `HUF/m3`;
- teljes lakossági végár, `HUF/m3`;
- normalizált, 2026-08-12-i, geopolitikai stressz és egyedi árpálya;
- minden ponthoz termék-, dátum-, forrás- és státusz-lineage.

## Invariánsok

- a nagykereskedelmi proxy nem helyettesítheti a lakossági végárat;
- a forward görbe nem hosszabbítható automatikusan a teljes 15–20 éves horizontra;
- a konverzió mértékegysége és referenciaállapota explicit;
- időfüggő ár licenc és snapshot nélkül nem kanonikus megfigyelés.

## Állapot

`IN_PROGRESS` – a piaci, deviza- és gázminőségi forráskapuk rögzítve; numerikus árpálya és konverziós képlet még nincs validálva.
