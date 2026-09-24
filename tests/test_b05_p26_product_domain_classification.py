import csv
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
REG=ROOT/"registry"/"b05_p26_product_domain_classification.csv"
QUESTIONS=ROOT/"registry"/"open_questions.csv"
READINESS=ROOT/"registry"/"heat_pump_readiness.csv"
SOURCES=ROOT/"registry"/"heat_pump_sources.csv"
DIMPLEX_GRID=ROOT/"data"/"processed"/"b05_p23_dimplex_modulation_floor_surface.csv"
MITS_GRID=ROOT/"data"/"processed"/"b05_p22_mitsubishi_minimum_point_grid.csv"
PACK=ROOT/"docs"/"source_packs"/"B05_P26_PRODUCT_DOMAIN_CLASSIFICATION.md"

def rows(path):
    with path.open(encoding="utf-8",newline="") as h:
        return list(csv.DictReader(h))

class B05P26ProductDomainClassificationTests(unittest.TestCase):
    def test_both_domain_classification_blockers_are_resolved(self):
        reg={r["claim"]:r for r in rows(REG)}
        self.assertEqual(
            reg["MITSUBISHI_COLD_HIGH_SUPPLY_DOMAIN_CLASSIFICATION_REQUIRED"]["status"],
            "RESOLVED_SUPPORTED_OPERATION_MINIMUM_POINT_UNPUBLISHED",
        )
        self.assertEqual(
            reg["DIMPLEX_A_MINUS10_MINIMUM_ROW_CLASSIFICATION_REQUIRED"]["status"],
            "RESOLVED_SUPPORTED_OPERATION_MINIMUM_POINT_UNPUBLISHED",
        )

    def test_missing_minimum_point_evidence_remains_open(self):
        reg={r["claim"]:r for r in rows(REG)}
        self.assertEqual(reg["MITSUBISHI_COLD_HIGH_SUPPLY_MINIMUM_POINT_EVIDENCE_REQUIRED"]["status"],"OPEN")
        self.assertEqual(reg["DIMPLEX_A_MINUS10_MINIMUM_POINT_EVIDENCE_REQUIRED"]["status"],"OPEN")

    def test_p9_operation_support_is_resolved_but_not_floor_coverage(self):
        reg={r["claim"]:r for r in rows(REG)}
        self.assertEqual(reg["MITSUBISHI_P9_W55_OPERATION_DOMAIN_SUPPORT"]["status"],"RESOLVED_FULL_ENVELOPE")
        self.assertEqual(reg["DIMPLEX_P9_STRESS_OPERATION_DOMAIN_SUPPORT"]["status"],"RESOLVED_FULL_ENVELOPE")
        self.assertIn("MINIMUM_POINT_EVIDENCE_REQUIRED",reg["MITSUBISHI_P9_W55_OPERATION_DOMAIN_SUPPORT"]["residual_gap"])
        self.assertIn("MINIMUM_POINT_EVIDENCE_REQUIRED",reg["DIMPLEX_P9_STRESS_OPERATION_DOMAIN_SUPPORT"]["residual_gap"])

    def test_no_fake_dimplex_a_minus10_minimum_is_added(self):
        grid=rows(DIMPLEX_GRID)
        self.assertNotIn(-10.0,{float(r["outdoor_temperature_C"]) for r in grid})

    def test_no_fake_mitsubishi_cold_w55_minimum_is_added(self):
        grid=rows(MITS_GRID)
        coords={(float(r["outdoor_temperature_C"]),float(r["supply_temperature_C"])) for r in grid}
        self.assertNotIn((-15.0,55.0),coords)
        self.assertNotIn((-20.0,55.0),coords)

    def test_live_question_is_narrowed_not_closed(self):
        q={r["question_id"]:r for r in rows(QUESTIONS)}["Q-B05-004"]
        self.assertEqual(q["status"],"OPEN")
        self.assertIn("B05-P26",q["notes"])
        self.assertIn("OPEN_NARROWED_TO_MINIMUM_POINT_GAPS_FANCOIL_AND_PRODUCT_TAU_EQ",q["notes"])
        self.assertIn("MITSUBISHI_COLD_HIGH_SUPPLY_MINIMUM_POINT_EVIDENCE_REQUIRED",q["notes"])
        self.assertIn("DIMPLEX_A_MINUS10_MINIMUM_POINT_EVIDENCE_REQUIRED",q["notes"])

    def test_new_operating_envelope_sources_are_registered(self):
        src={r["source_id"]:r for r in rows(SOURCES)}
        self.assertIn("SRC-B05-MITSUBISHI-WM50-OPERATING-ENVELOPE-2020",src)
        self.assertIn("SRC-B05-DIMPLEX-LA2030CP-OPERATING-ENVELOPE-2026",src)
        self.assertIn("-20..+24",src["SRC-B05-MITSUBISHI-WM50-OPERATING-ENVELOPE-2020"]["notes"])
        self.assertIn("-22..+40",src["SRC-B05-DIMPLEX-LA2030CP-OPERATING-ENVELOPE-2026"]["notes"])

    def test_readiness_does_not_inflate(self):
        readiness={r["component_id"]:r for r in rows(READINESS)}
        self.assertEqual(readiness["PART_LOAD_MODULATION"]["readiness_percent"],"45")
        text=PACK.read_text(encoding="utf-8")
        self.assertIn("does not create missing minimum-point",text)
        self.assertIn("B05 remains **64%**",text)

if __name__=="__main__":
    unittest.main()
