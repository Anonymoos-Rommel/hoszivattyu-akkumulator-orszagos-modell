import csv
import unittest
from pathlib import Path

from tests.b05_readiness_assertions import assert_part_load_readiness_unassessed

from modules.B05.mitsubishi_a15_w50_domain_gate import (
    PersistentBlankEvidence,
    CoordinateAuthority,
    PERSISTENT_SOURCE_BLANK,
    EXACT_2D_SUPPORTED,
    EXACT_2D_OUTSIDE,
    Q,
    compose_one_dimensional_limits,
    p46_boundaries,
)

ROOT = Path(__file__).resolve().parents[1]
REG = ROOT / "registry" / "b05_p46_mitsubishi_a15_w50_domain_boundary.csv"
DATA = ROOT / "data" / "processed" / "b05_p46_mitsubishi_a15_w50_evidence.csv"
QUESTIONS = ROOT / "registry" / "open_questions.csv"
READINESS = ROOT / "registry" / "heat_pump_readiness.csv"
SOURCES = ROOT / "registry" / "heat_pump_sources.csv"
PACK = ROOT / "docs" / "source_packs" / "B05_P46_MITSUBISHI_A15_W50_DOMAIN_BOUNDARY.md"

def rows(path):
    with path.open(encoding="utf-8", newline="") as h:
        return list(csv.DictReader(h))

class B05P46MitsubishiA15W50Tests(unittest.TestCase):
    def test_three_revision_blank_is_availability_not_domain_status(self):
        e = PersistentBlankEvidence(
            revision_count=3,
            all_levels_blank=True,
            same_ambient_lower_supply_populated=True,
            warmer_ambient_same_supply_populated=True,
        )
        self.assertEqual(e.classify(), PERSISTENT_SOURCE_BLANK)

    def test_one_dimensional_specs_do_not_create_2d_authority(self):
        self.assertEqual(
            compose_one_dimensional_limits(60.0, -20.0, -15.0, 50.0),
            Q,
        )

    def test_exact_source_native_2d_supported_can_close(self):
        e = CoordinateAuthority(True, -15, 50, True, "SUPPORTED")
        self.assertEqual(e.classify(), EXACT_2D_SUPPORTED)

    def test_exact_source_native_2d_outside_can_close(self):
        e = CoordinateAuthority(True, -15, 50, True, "OUTSIDE")
        self.assertEqual(e.classify(), EXACT_2D_OUTSIDE)

    def test_neighbour_or_unspecified_cannot_close(self):
        self.assertEqual(
            CoordinateAuthority(True, -15, 45, True, "SUPPORTED").classify(),
            Q,
        )
        self.assertEqual(
            CoordinateAuthority(True, -15, 50, False, "SUPPORTED").classify(),
            Q,
        )
        self.assertEqual(
            CoordinateAuthority(True, -15, 50, True, "UNSPECIFIED").classify(),
            Q,
        )

    def test_registry_narrows_but_keeps_coordinate_open(self):
        reg = {r["claim"]: r for r in rows(REG)}
        self.assertEqual(
            reg["MITSUBISHI_A_MINUS15_W50_MULTI_REVISION_TABLE_STATE"]["status"],
            "PERSISTENT_BLANK_ACROSS_V53_V59_V60",
        )
        self.assertEqual(
            reg["MITSUBISHI_A_MINUS15_W50_MINIMUM_CLASSIFICATION_REQUIRED"]["status"],
            "OPEN_NARROWED_TO_EXACT_SOURCE_NATIVE_2D_RECORD",
        )
        self.assertIn(
            "EXACT_SOURCE_NATIVE_A_MINUS15_W50_2D_OPERATING_OR_PERFORMANCE_RECORD_REQUIRED",
            reg["MITSUBISHI_A_MINUS15_W50_MINIMUM_CLASSIFICATION_REQUIRED"]["residual_gap"],
        )

    def test_global_q_and_readiness_remain_open(self):
        q = {r["question_id"]: r for r in rows(QUESTIONS)}["Q-B05-004"]
        self.assertEqual(q["status"], "OPEN")
        self.assertIn("B05-P46", q["notes"])
        self.assertIn("General max outlet temperature 60 C", q["notes"])
        self.assertIn("synthetic two-dimensional A-15/W50 authority", q["notes"])
        readiness = {r["component_id"]: r for r in rows(READINESS)}
        assert_part_load_readiness_unassessed(self, readiness["PART_LOAD_MODULATION"])

    def test_sources_and_inventory(self):
        s = {r["source_id"]: r for r in rows(SOURCES)}
        for sid in (
            "SRC-B05-MITSUBISHI-DATABOOK-WM50-V59-LIBRARY-2026",
            "SRC-B05-MITSUBISHI-DATABOOK-WM50-V59-TABLE-2026",
            "SRC-B05-MITSUBISHI-SE-WM50-A15-2026",
            "SRC-B05-MITSUBISHI-FR-WM50-A15-2026",
        ):
            self.assertIn(sid, s)
        self.assertEqual(len(rows(DATA)), 8)
        text = PACK.read_text(encoding="utf-8")
        self.assertIn("PERSISTENT_BLANK = PHYSICAL_IMPOSSIBILITY", text)
        self.assertIn("PART_LOAD_MODULATION = **45%**", text)
        self.assertIn("MAX_OUTLET_PLUS_AMBIENT_RANGE_IS_NOT_2D_AUTHORITY", p46_boundaries())

if __name__ == "__main__":
    unittest.main()
