"""Source-native 2022 heating-system assignment for B02 occupied dwellings.

B02-P22 consumes the already-materialized WBL011 full occupied-stock joint.
It classifies only the heating-system topology that the Census FUTES_TOH code
actually supports.  It does not infer radiator, convector, floor heating or
current design temperatures.
"""

from __future__ import annotations

import argparse
import csv
import json
from dataclasses import dataclass
from pathlib import Path

from modules.B02.calibrated_archetype_linkage import (
    DEFAULT_WBL,
    EXPECTED_OCCUPIED_DWELLINGS,
    EXPECTED_WBL_ROWS,
    FULL_PROJECTION,
)

ASSIGNMENT_ID = "B02-P22-KSH-CURRENT-HEATING-SYSTEM-ASSIGNMENT"
SOURCE_ID = "SRC-B02-KSH-CENSUS-API-2022"
HEATING_SYSTEM_EVIDENCE_STATUS = "DER"
EMITTER_EVIDENCE_STATUS = "Q"
DESIGN_TEMPERATURE_EVIDENCE_STATUS = "Q"

# HEAT12 is already canonical in B01 as district heating.  HEAT111 and
# HEAT112 are kept together as CENTRAL_HEATING here: P22 deliberately avoids
# inventing a finer semantic distinction when it is not required for the
# current-system claim.  NHEAT is the source-native room-by-room/no-heating
# branch documented by KSH definitions.
HEATING_SYSTEM_CLASS = {
    "HEAT111": "CENTRAL_HEATING",
    "HEAT112": "CENTRAL_HEATING",
    "HEAT12": "DISTRICT_HEATING",
    "NHEAT": "ROOM_BY_ROOM_OR_NO_HEAT",
}


@dataclass(frozen=True)
class HeatingSystemSummary:
    row_count: int
    occupied_dwellings: int
    central_heating_dwellings: int
    district_heating_dwellings: int
    room_by_room_or_no_heat_dwellings: int

    def as_dict(self) -> dict[str, object]:
        return {
            "assignment_id": ASSIGNMENT_ID,
            "source_id": SOURCE_ID,
            "row_count": self.row_count,
            "occupied_dwellings": self.occupied_dwellings,
            "central_heating_dwellings": self.central_heating_dwellings,
            "district_heating_dwellings": self.district_heating_dwellings,
            "room_by_room_or_no_heat_dwellings": self.room_by_room_or_no_heat_dwellings,
            "heating_system_evidence_status": HEATING_SYSTEM_EVIDENCE_STATUS,
            "heat_emitter_evidence_status": EMITTER_EVIDENCE_STATUS,
            "design_temperature_evidence_status": DESIGN_TEMPERATURE_EVIDENCE_STATUS,
        }


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def build_heating_system_assignment(
    *, wbl_path: Path = DEFAULT_WBL
) -> tuple[list[dict[str, object]], HeatingSystemSummary]:
    output: list[dict[str, object]] = []
    totals = {value: 0 for value in set(HEATING_SYSTEM_CLASS.values())}

    for row in _read_csv(wbl_path):
        if row["projection_id"] != FULL_PROJECTION:
            continue
        if row["evidence_status"] != "OBS":
            raise ValueError(f"full-joint WBL input must remain OBS: {row!r}")
        count = int(row["dwelling_count"])
        if count <= 0:
            raise ValueError(f"full-joint WBL row must have positive count: {row!r}")
        heating_code = row["heating_mode_code"]
        if heating_code not in HEATING_SYSTEM_CLASS:
            raise ValueError(f"unexpected WBL011 heating-mode code: {heating_code!r}")
        system_class = HEATING_SYSTEM_CLASS[heating_code]
        totals[system_class] += count
        output.append(
            {
                "cell_id": row["cell_id"],
                "dwelling_count": count,
                "heating_mode_code": heating_code,
                "heating_mode_name_hu": row["heating_mode_name_hu"],
                "heating_fuel_code": row["heating_fuel_code"],
                "heating_fuel_name_hu": row["heating_fuel_name_hu"],
                "heating_system_class": system_class,
                "heating_system_evidence_status": HEATING_SYSTEM_EVIDENCE_STATUS,
                "heat_emitter_status": EMITTER_EVIDENCE_STATUS,
                "design_temperature_status": DESIGN_TEMPERATURE_EVIDENCE_STATUS,
                "emitter_resolution": (
                    "CURRENT_EMITTER_UNRESOLVED; FUTES_TOH identifies heating topology, "
                    "not radiator/surface/convector/stove type at this grain"
                ),
                "assignment_id": ASSIGNMENT_ID,
                "source_id": SOURCE_ID,
            }
        )

    if len(output) != EXPECTED_WBL_ROWS:
        raise ValueError(
            f"WBL row-count drift: expected={EXPECTED_WBL_ROWS} actual={len(output)}"
        )
    occupied = sum(int(row["dwelling_count"]) for row in output)
    if occupied != EXPECTED_OCCUPIED_DWELLINGS:
        raise ValueError(
            f"occupied total drift: expected={EXPECTED_OCCUPIED_DWELLINGS} actual={occupied}"
        )
    if sum(totals.values()) != occupied:
        raise ValueError("heating-system classes do not partition occupied stock")

    summary = HeatingSystemSummary(
        row_count=len(output),
        occupied_dwellings=occupied,
        central_heating_dwellings=totals["CENTRAL_HEATING"],
        district_heating_dwellings=totals["DISTRICT_HEATING"],
        room_by_room_or_no_heat_dwellings=totals["ROOM_BY_ROOM_OR_NO_HEAT"],
    )
    return output, summary


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--wbl", type=Path, default=DEFAULT_WBL)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    _rows, summary = build_heating_system_assignment(wbl_path=args.wbl)
    if args.json:
        print(json.dumps(summary.as_dict(), ensure_ascii=False, sort_keys=True))
    else:
        for key, value in summary.as_dict().items():
            print(f"{key}={value}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
