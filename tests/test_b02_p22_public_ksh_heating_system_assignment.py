from __future__ import annotations

import csv
import unittest
from pathlib import Path

from modules.B02.heating_system_assignment import (
    ASSIGNMENT_ID,
    DESIGN_TEMPERATURE_EVIDENCE_STATUS,
    EMITTER_EVIDENCE_STATUS,
    HEATING_SYSTEM_CLASS,
    HEATING_SYSTEM_EVIDENCE_STATUS,
    build_heating_system_assignment,
)

ROOT = Path(__file__).resolve().parents[1]


class B02P22PublicKshHeatingSystemAssignmentTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rows, cls.summary = build_heating_system_assignment()

    def test_exact_wbl_universe_is_preserved(self):
        self.assertEqual(116_452, self.summary.row_count)
        self.assertEqual(4_008_541, self.summary.occupied_dwellings)
        self.assertEqual(618_724, self.summary.district_heating_dwellings)
        self.assertEqual(
            self.summary.occupied_dwellings,
            self.summary.central_heating_dwellings
            + self.summary.district_heating_dwellings
            + self.summary.room_by_room_or_no_heat_dwellings,
        )

    def test_source_native_partition_is_minimal_and_complete(self):
        self.assertEqual(
            {
                "HEAT111": "CENTRAL_HEATING",
                "HEAT112": "CENTRAL_HEATING",
                "HEAT12": "DISTRICT_HEATING",
                "NHEAT": "ROOM_BY_ROOM_OR_NO_HEAT",
            },
            HEATING_SYSTEM_CLASS,
        )
        self.assertEqual(set(HEATING_SYSTEM_CLASS), {row["heating_mode_code"] for row in self.rows})

    def test_heating_system_is_der_but_emitter_and_temperature_remain_q(self):
        self.assertEqual("DER", HEATING_SYSTEM_EVIDENCE_STATUS)
        self.assertEqual("Q", EMITTER_EVIDENCE_STATUS)
        self.assertEqual("Q", DESIGN_TEMPERATURE_EVIDENCE_STATUS)
        for row in self.rows:
            self.assertEqual("DER", row["heating_system_evidence_status"])
            self.assertEqual("Q", row["heat_emitter_status"])
            self.assertEqual("Q", row["design_temperature_status"])
            self.assertEqual(ASSIGNMENT_ID, row["assignment_id"])

    def test_no_emitter_is_inferred_from_heating_mode_or_fuel(self):
        forbidden = ("RADIATOR", "FLOOR_HEATING", "WALL_HEATING", "CONVECTOR", "STOVE")
        for row in self.rows:
            self.assertTrue(row["emitter_resolution"].startswith("CURRENT_EMITTER_UNRESOLVED"))
            rendered = f"{row['heating_system_class']} {row['emitter_resolution']}"
            for token in forbidden:
                self.assertNotIn(token, rendered)

    def test_registry_freezes_system_only_authority(self):
        path = ROOT / "registry" / "b02_heating_system_assignment.csv"
        with path.open(encoding="utf-8", newline="") as handle:
            rows = list(csv.DictReader(handle))
        self.assertEqual(1, len(rows))
        row = rows[0]
        self.assertEqual("QUALIFIED_SYSTEM_ONLY", row["authority_status"])
        self.assertEqual("DER", row["heating_system_status"])
        self.assertEqual("Q", row["heat_emitter_status"])
        self.assertEqual("Q", row["design_temperature_status"])
        self.assertEqual(
            "NO_CURRENT_HEAT_EMITTER_EVIDENCE;NO_CURRENT_DESIGN_TEMPERATURE_EVIDENCE",
            row["current_blockers"],
        )

    def test_source_pack_preserves_non_equivalence_boundaries(self):
        text = (ROOT / "docs" / "source_packs" / "B02_P22_PUBLIC_KSH_HEATING_SYSTEM_ASSIGNMENT.md").read_text(encoding="utf-8")
        self.assertIn(
            "CURRENT HEATING SYSTEM TOPOLOGY != CURRENT HEAT EMITTER != CURRENT DESIGN TEMPERATURE != HYDRAULIC READINESS",
            text,
        )
        self.assertIn("QUALIFIED_SYSTEM_ONLY", text)
        self.assertIn("NO_CURRENT_HEAT_EMITTER_EVIDENCE", text)
        self.assertIn("NO_CURRENT_DESIGN_TEMPERATURE_EVIDENCE", text)
        self.assertIn("SENT_2026-08-22 / AWAITING_RESPONSE", text)


if __name__ == "__main__":
    unittest.main()
