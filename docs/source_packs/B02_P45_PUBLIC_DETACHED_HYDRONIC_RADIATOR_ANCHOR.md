# B02-P45 — PUBLIC DETACHED-HOUSE HYDRONIC RADIATOR ANCHOR

## Purpose

P45 continues public recovery after the P44 panel/district-heating branch and moves to the next material programme segment: non-district central-hydronic residential heating, primarily detached houses.

The programme question remains:

`HOW MANY + WHAT TYPE + KEEP/CHANGE + HOW MANY NEW UNITS -> B06`

The evidence rule remains:

`PUBLIC RECOVERY != DATA REQUEST`

and:

`HOUSEHOLD-LEVEL PUBLIC ANCHOR != NATIONAL P42 AUTHORITY`

Every P45 row therefore carries `p42_national_authority=NO`.

## Recovered household-level quantity anchors

P45 freezes several source-bounded examples instead of pretending that one dwelling is representative of the stock.

- Uri: 70 m2 detached house -> 4 radiators total, explicitly 3 Purmo radiators + 1 towel-rail radiator; 21 kW water-jacket fireplace.
- Jaszfenyszaru: 77 m2 detached house -> 6 radiators; solid-fuel boiler.
- Szentlorinckata: 86 m2 brick detached house -> 8 radiators; gas boiler, with a solid-fuel boiler also present but reported unused in recent years.
- Sopron implemented modernization: 1985-built 120 m2 detached house -> 7 actually replaced radiators, together with replacement of the old boiler by a condensing gas boiler.
- Nemetker: 150 m2 detached house -> current 22K panel-radiator type is explicit; radiator count is not published and is therefore not inferred.

These rows prove that the non-district hydronic branch is no longer empty at household level. They do not prove a national mean radiator count.

## Reuse/change engineering controls

The programme cannot equate `existing radiator` with either `KEEP` or `CHANGE`.

A current Hungarian engineering guidance source binds the decision to the room heat loss, emitter size, water temperature, hydraulics and building condition. It explicitly describes the practical retrofit pattern in which some existing emitters are retained and others are upsized so that a former roughly 65-70 C requirement can be driven toward roughly 45-55 C.

A public Mezőfalva residential energy handbook separately preserves the low-temperature control that conventional radiator use with heat pumps requires materially larger emitter surface; the handbook states at least roughly double surface in its generic explanation and gives a post-envelope 5.7 kW heating demand for its model Kadar-cube house.

Therefore:

`FUEL TYPE != RADIATOR REPLACEMENT DECISION`

`BUILDING AGE != RADIATOR REPLACEMENT DECISION`

`POST-ENVELOPE HEAT LOSS + EXISTING EMITTER OUTPUT AT TARGET WATER TEMPERATURE + HYDRAULICS -> KEEP / UPSIZE / CHANGE`

## Source-quality boundary

P45 intentionally distinguishes three source-quality classes:

- `PUBLIC_LISTING`: direct public household description; useful for bounded inventory/type anchors, not population inference;
- `IMPLEMENTED_REFERENCE`: a completed contractor reference with explicit replacement quantity;
- `ENGINEERING_GUIDANCE`: reusable technical decision logic, not a household quantity observation.

No row is silently upgraded because it is convenient.

## Programme boundary

P45 does **not**:

- estimate the national radiator stock;
- estimate a detached-house national radiators-per-dwelling mean;
- assign a national KEEP/CHANGE share;
- convert radiator counts into B06 procurement quantities;
- treat a property listing as a statistical sample;
- infer missing dimensions, models or counts;
- modify the five P42 national claims.

The five P42 national programme quantities remain `Q` and programme use remains prohibited until a separately defensible national authority or aggregation method exists.

## What P45 changes materially

Before P45, the non-district central-hydronic branch had a qualitative existence problem: we knew the segment existed but lacked source-bound household radiator inventories.

After P45 we have bounded examples tying together:

`floor area -> generator type -> radiator count and/or radiator type -> implemented replacement quantity -> engineering KEEP/CHANGE control`

That is real evidence progress, but still below national-authority level.
