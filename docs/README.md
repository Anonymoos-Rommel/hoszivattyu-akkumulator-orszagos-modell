# Dokumentáció

Az itt található dokumentumok a kanonikus regiszterekből és számítási eredményekből készülnek.

- `methodology/` — bizonyítási, modellezési és auditmódszerek;
- `source_packs/` — modulonként lezárt vagy folyamatban lévő forrásfeltárási csomagok;
- `generated_reports/` — később automatikusan előállított tanulmányok.
- `methodology/v12_portfolio_transition_contract.md` — a V1.2 állapotgép-, portfólió-, baseline- és fiskális szerződése.

A generált jelentés nem írhatja felül a kanonikus adatot vagy képletet.

## V1.2 gépi szerződés

A `registry/household_state_model.json` és az üres, fejléc-szinten szerződött portfólió-regiszterek a modell bővítési keretét adják. Üres állományba nem töltünk becslést: rekord csak lezárt forrás-, képlet- vagy szakpolitikai kapu után kerülhet.

## Első kutatási csomag

- [P1-A: B01–B04 alapok](source_packs/P1A_B01_B04.md) — hivatalos forráskapuk, változószerződések és kritikus nyitott kérdések; számszerű modellkapu még nincs lezárva.
- [P1-I: B02 V1.2 readiness-híd](source_packs/P1I_B02_V12_READINESS_BRIDGE.md) — a meglévő B02-kimenetek és az S0–S2 állapotkapuk tételes átadási és hiánytérképe.
- [P1-J: B02 S0–S2 Evidence Gap Matrix](source_packs/P1J_B02_S0_S2_EVIDENCE_GAP_MATRIX.md) — mezőnkénti forrásfedés, OÉNY-pilot-határ és az OÉNY után is fennmaradó bizonytalanságok.
- [P1-K: OÉNY Pilot Acceptance Contract](source_packs/P1K_OENY_PILOT_ACCEPTANCE_CONTRACT.md) — minden pilotmező elfogadási minimuma, tiltott következtetése és a P1-F adatigénylési tervezet readiness-döntése.
- [P1-L: OÉNY Data Request Release Gate](data_requests/P1L_OENY_DATA_REQUEST_RELEASE_PACKAGE.md) — végleges, de nem küldött levél, Joseph approval sheet, field manifest, jogi/adatvédelmi checklist és címzett/csatorna-javaslat.
- [P1-M: OÉNY Public Machine Access Audit](source_packs/P1M_OENY_PUBLIC_MACHINE_ACCESS_AUDIT.md) — a nyilvános UI/XHR audit, 22 mezős visszamappelés, incremental feasibility és a PATH_B_HYBRID döntés.
- [B02-P2: Technical Eligibility Admission Gate](source_packs/B02_P2_TECHNICAL_ELIGIBILITY_ADMISSION_GATE.md) — végrehajtható fail-closed szeparáció a fizikai screening, technikai eligibility, S2 transition readiness és programjogosultság között; a national eligible count továbbra is Q.
- [P1L-FINAL-R1: OÉNY pilot adatigénylés](data_requests/P1L_FINAL_OENY_REQUEST_LETTER.md) — emberi átnézésre kész, továbbra is nem küldött hivatalos levél és source-native/derived mellékletcsomag.