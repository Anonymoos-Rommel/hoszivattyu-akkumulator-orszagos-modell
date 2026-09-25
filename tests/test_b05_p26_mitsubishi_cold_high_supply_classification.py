import csv
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/"data"/"processed"/"b05_p26_mitsubishi_cold_high_supply_classification.csv"
REG=ROOT/"registry"/"b05_p26_mitsubishi_cold_high_supply_classification.csv"
QUESTIONS=ROOT/"registry"/"open_questions.csv"
READINESS=ROOT/"registry"/"heat_pump_readiness.csv"
SOURCES=ROOT/"registry"/"heat_pump_sources.csv"
PACK=ROOT/"docs"/"source_packs"/"B05_P26_MITSUBISHI_COLD_HIGH_SUPPLY_CLASSIFICATION.md"

def rows(path):
    with path.open(encoding="utf-8",newline="") as h:
        return list(csv.DictReader(h))

class B05P26MitsubishiColdHighSupplyClassificationTests(unittest.TestCase):
    def test_five_p22_blank_cells_are_explicitly_classified(self):
        data=rows(DATA)
        self.assertEqual(len(data),5)
        outside=[r for r in data if r["p26_domain_classification"]=="OUTSIDE_OPERATING_ENVELOPE"]
        q=[r for r in data if r["p26_domain_classification"]=="Q_THRESHOLD_NOT_EXACT"]
        self.assertEqual(len(outside),4)
        self.assertEqual(len(q),1)
        self.assertEqual((q[0]["outdoor_temperature_C"],q[0]["supply_temperature_C"]),("-15","50"))

    def test_registry_narrows_mitsubishi_gap_to_one_cell(self):
        reg={r["claim"]:r for r in rows(REG)}
        self.assertEqual(
            reg["MITSUBISHI_COLD_HIGH_SUPPLY_DOMAIN_CLASSIFICATION_REQUIRED"]["status"],
            "PARTIAL_RESOLVED_NARROWED_TO_A_MINUS15_W50",
        )
        self.assertEqual(
            reg["MITSUBISHI_A_MINUS15_W50_MINIMUM_CLASSIFICATION_REQUIRED"]["status"],
            "OPEN",
        )
        self.assertEqual(
            reg["P9_STRESS_W55_MITSUBISHI_APPLICABILITY"]["status"],
            "PARTIAL_PRODUCT_NOT_APPLICABLE_BELOW_A_MINUS10",
        )

    def test_dimplex_a_minus10_is_not_falsely_promoted(self):
        reg={r["claim"]:r for r in rows(REG)}
        d=reg["DIMPLEX_A_MINUS10_MINIMUM_ROW_CLASSIFICATION_REQUIRED"]
        self.assertEqual(d["status"],"OPEN")
        self.assertIn("max capacity/COP",d["notes"])

    def test_live_question_preserves_p25_and_adds_p26_state(self):
        q={r["question_id"]:r for r in rows(QUESTIONS)}["Q-B05-004"]
        self.assertEqual(q["status"],"OPEN")
        for marker in (
            "B05-P25",
            "OPEN_NARROWED_TO_DOMAIN_GAPS_FANCOIL_AND_PRODUCT_TAU_EQ",
            "B05-P26",
            "PARTIAL_RESOLVED_NARROWED_TO_A_MINUS15_W50",
            "OPEN_NARROWED_TO_SINGLE_MITSUBISHI_CELL_PLUS_DIMPLEX_FANCOIL_TAU_EQ",
        ):
            self.assertIn(marker,q["notes"])

    def test_source_and_readiness_remain_bounded(self):
        sources={r["source_id"]:r for r in rows(SOURCES)}
        self.assertIn("SRC-B05-MITSUBISHI-WM50-OUTLET-ENVELOPE-2025",sources)
        readiness={r["component_id"]:r for r in rows(READINESS)}
        self.assertEqual(readiness["PART_LOAD_MODULATION"]["readiness_percent"],"45")

    def test_document_forbids_graph_digitization_and_keeps_b05_64(self):
        text=PACK.read_text(encoding="utf-8")
        self.assertIn("does **not** digitize",text)
        self.assertIn("B05 remains **64%**",text)
        self.assertIn("A-15/W50 remains Q",text)

if __name__=="__main__":
    unittest.main()
