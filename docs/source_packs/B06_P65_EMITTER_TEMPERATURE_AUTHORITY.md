# B06-P65 — Post-retrofit emitter-temperature authority

## Purpose

Resolve **Q-B06-008** at blocker level without turning a generic heat-pump
temperature band, a boiler setpoint, a HET reference system, or an emitter type
name into a building-specific post-retrofit supply temperature.

P4 already provides the bounded emitter-output calculation.  P65 closes the
missing **record-level authority** around that calculation and around direct
building design / measurement evidence.

## Core non-equivalence

```text
HEAT-PUMP W35/W45/W55 PERFORMANCE POINT
!= BUILDING REQUIRED SUPPLY TEMPERATURE

REFERENCE 55/45 C
!= OBSERVED OR DESIGNED BUILDING 55/45 C

EXISTING BOILER SETPOINT
!= POST-RETROFIT DESIGN POINT

FINAL HET
!= EMITTER INVENTORY

BUILDING-AVERAGE EMITTER CAPACITY
!= ALL-ROOM ADEQUACY
```

A numeric post-retrofit supply temperature can enter the B06 -> B05 bridge only
through one of the P65 routes below.

## Route A — room-by-room emitter design

Required for every heated room:

- explicit post-state design heat load;
- exact emitter identity / dimensions / quantity;
- source-native emitter nominal output and correction method;
- explicit flow / return / room-temperature operating points;
- source references for the room load and emitter inventory.

The existing P4 emitter equation is then evaluated for every room.  The common
building supply temperature is the **maximum room requirement**.  Averaging room
requirements is forbidden because that can under-serve the critical room.

Missing one heated room keeps the building result Q.

## Route B — signed post-retrofit MEP design

A direct building design point is admissible only when the same evidence packet
contains or binds:

- explicit design supply and return temperatures;
- design outdoor and indoor temperatures;
- complete room heat-loss basis;
- complete emitter schedule;
- hydraulic design / balancing basis;
- exact record and intervention linkage.

The route admits source-native design output; it does not reconstruct missing
design inputs from national averages.

## Route C — measured post-retrofit design point

A measured temperature can independently mint the design point only when:

- the record is in a realized post-retrofit phase;
- supply and return are observed;
- all heated rooms are covered and the minimum observed room temperature meets
  the design indoor setpoint;
- the measured outdoor temperature is at or colder than the design outdoor
  condition.

A mild-weather measurement cannot be extrapolated to the design point by P65.

## External method authority

### MCS 021 Issue 2.1

The MCS Heat Emitter Guide is dwelling-specific and requires the emitter
selection process to be repeated for all heated rooms.  Its worked examples
explicitly combine room heat loss with emitter rated output to determine the
required radiator flow temperature.  This is used as method-shape authority,
not as a Hungarian stock factor and not as a replacement for the source-native
Purmo curve already used by P4.

Source: `SRC-B06-MCS-021-2-1-2015`.

## Hungarian residential validation

A public 2024 mechanical design for a **12-dwelling residential building at
1181 Budapest, Üllői út 411** provides a real Hungarian design chain:

- design outdoor temperature: **-13 C**;
- building design heat loss: **47.3 kW**;
- four Mitsubishi Zubadan air-to-water heat pumps;
- heat-pump rating point: **45/40 C** at -15 C;
- apartment underfloor-heating design step: **40/35 C**;
- dynamic hydraulic balancing is explicitly described.

This is valuable validation that Hungarian residential MEP practice publishes
the exact quantities P65 requires.  It is **not** a retrofit microrecord and is
therefore `usable_for_engine = NO` as an intervention effect.  It does not
create a 45/40 C default for any other building.

Source: `SRC-B06-HU-ULLOI411-MEP-2024`.

## Runtime enforcement

`RetrofitIntervention.supply_temperature_after_c` is no longer an unguarded
numeric override.

If an intervention attempts to change post-retrofit supply temperature:

1. P65 evidence is mandatory;
2. the evidence decision must be `QUALIFIED`;
3. the evidence intervention ID must match the runtime intervention;
4. if a numeric supply claim is also supplied, it must exactly match the P65
   decision;
5. otherwise B06 returns Q and emits no B05 sizing input.

P65 evidence may also provide the temperature directly, avoiding a duplicated
manual number.

## Scope boundary

P65 resolves the **authority and calculation blocker**.  It does not claim that
Hungary already has national household-level emitter inventories or measured
post-retrofit supply/return coverage.  Each real building remains Q until one of
the three admissible routes is actually populated for that record.

Therefore:

```text
Q-B06-008 -> RESOLVED

authority contract -> CLOSED
arbitrary numeric supply override -> CLOSED
room aggregation rule -> CLOSED
national household emitter coverage -> NOT CLAIMED
individual record with missing evidence -> Q
```
