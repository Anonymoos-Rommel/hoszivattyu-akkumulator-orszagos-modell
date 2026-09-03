# B11-P5 — Programme-aligned gas-quality snapshot gate

## Core rule

`SOURCE ACCESS != TEMPORAL AUTHORITY != LOCATION MAPPING != REPOSITORY MATERIALIZATION`

B11-P4 made the GCV/LHV basis explicit. P5 adds the authority needed before a gas-quality pair can enter a real programme calculation.

## FGSZ evidence boundary

The currently applicable FGSZ quality-accounting rules are a strong primary source for gas-quality accounting and point-level GCV/NCV evidence. However, the document's validity period and the reference period of embedded statistics are separate facts. The inspected 2025-10-01 to 2026-09-30 revision contains historical 2024 point statistics; those values are not silently promoted to a 2026 programme snapshot.

FGSZ public web access also does not establish public-repository materialization authority. The public website terms/copyright boundary requires prior permission for reuse beyond personal use. Therefore this increment records source lineage and the gate, but does not copy the point-level numeric table into the public repository.

## Runtime contract

`modules/B11/gas_quality_snapshot_contract.py` requires all of the following before a GCV/LHV pair is authorized:

1. explicit gas-quality `point_id`;
2. explicit snapshot start/end period;
3. exact coverage of the programme calculation period;
4. explicit `MJ/m3_GCV` and `MJ/m3_LHV` evidence;
5. GCV > LHV;
6. exact participant/programme-scope to gas-quality-point mapping;
7. matching point IDs between snapshot and participant mapping;
8. source lineage.

Q, missing values, period mismatch, partial mapping or point mismatch fail closed.

## Materialization policy

`registry/b11_programme_gas_quality_snapshot.csv` is intentionally header-only. It is not a hidden zero dataset. It remains empty until reusable numeric point/period evidence and exact programme mapping are both established.

Public source access alone does not permit row materialization. Repository materialization authority is tracked independently from model-use/source authority.

## What P5 does not claim

P5 does **not** establish:

- a national constant gas heating value;
- a current 2026 programme-aligned point panel;
- a county-to-gas-quality-point proxy;
- a settlement-to-gas-quality-point proxy;
- an exact participant-to-point crosswalk;
- permission to republish FGSZ point-level values;
- real programme gas volume or bcm displacement;
- Hungarian in-use seasonal gas-appliance efficiency calibration;
- B03 wholesale import valuation.

Historical point evidence may later be used as historical validation or scenario evidence with explicit status, but not as current observed programme truth.

## Readiness effect

B11 readiness increases only for the executable temporal/spatial/materialization gate. The numeric programme gas-quality population remains Q, so P5 does not unlock real programme bcm.
