# Interaktív alkalmazás

Az alkalmazás a validált modell megjelenítési rétege lesz, nem külön igazságforrás.

A végleges implementáció csak akkor indulhat, amikor:

1. a B01–B19 modulok szerződése stabil;
2. a kritikus változók definíciója, egysége, forrása és tartománya rögzített;
3. a B20 input/output schema és dependency graph jóváhagyott.

A V1.2 miatt a B20 szerződésnek ezen felül az `S0`–`S5` állapotmodellt, az éves portfólió-kiválasztást, a regionális readiness-t, a baseline/incremental CAPEX-szétválasztást és a fiskális headroomot kell megjelenítenie. Az alkalmazás nem tölthet ki hiányzó adatot és nem hozhat létre saját prioritási igazságforrást.

Tervezett nézetek: áttekintő, modulböngésző, forrás- és változókereső, Scenario Lab, állapot- és várakozási idő nézet, portfólió-hőtérkép, háztartási kalkulátor, rendszerterhelés, finanszírozás, baseline/incremental CAPEX, stresszteszt, auditnézet és prezentációs mód.
