import csv
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
QUESTIONS = ROOT / "registry" / "open_questions.csv"
REG = ROOT / "registry" / "b05_p27_question_layer_semantic_split.csv"
READINESS = ROOT / "registry" / "heat_pump_readiness.csv"
HP_SOURCES = ROOT / "registry" / "heat_pump_sources.csv"
PACK = ROOT / "docs" / "source_packs" / "B05_P27_QUESTION_LAYER_SEMANTIC_SPLIT.md"
README = ROOT / "modules" / "B05" / "README.md"

def rows(path):
    with path.open(encoding="utf-8", newline="") as h:
        return list(csv.DictReader(h))

class B05P27QuestionLayerSemanticSplitTests(unittest.TestCase):
    def test_q_b05_004_remains_open_umbrella_with_resolved_product_subclaim(self):
        q = {r["question_id"]: r for r in rows(QUESTIONS)}
        self.assertEqual(q["Q-B05-004"]["status"], "OPEN")
        self.assertIn("PRODUCT_LEVEL_EVIDENCE", q["Q-B05-004"]["notes"])
        self.assertIn("RESOLVED_BOUNDED_PRODUCT_EVIDENCE", q["Q-B05-004"]["notes"])
        self.assertNotIn("Q-B05-007", q)
        self.assertNotIn("Q-B05-008", q)

    def test_coordinate_coverage_is_a_separate_open_subclaim(self):
        reg = {r["claim"]: r for r in rows(REG)}
        c = reg["Q-B05-004_COORDINATE_COVERAGE"]
        self.assertEqual(c["status"], "OPEN_PRODUCT_COORDINATE_COVERAGE")
        self.assertIn("MITSUBISHI_A_MINUS15_W50_MINIMUM_CLASSIFICATION_REQUIRED", c["residual_gap"])
        self.assertIn("DIMPLEX_A_MINUS10_MINIMUM_ROW_CLASSIFICATION_REQUIRED", c["residual_gap"])

    def test_obs_hourly_transient_fidelity_is_a_separate_open_subclaim(self):
        reg = {r["claim"]: r for r in rows(REG)}
        c = reg["Q-B05-004_OBS_HOURLY_TRANSIENT_FIDELITY"]
        self.assertEqual(c["status"], "OPEN_OBS_HOURLY_TRANSIENT_FIDELITY")
        self.assertIn("HEM_FANCOIL_EMITTER_TIME_DOC_CODE_DIVERGENCE_REQUIRED", c["residual_gap"])
        self.assertIn("PRODUCT_SPECIFIC_TAU_EQ_EVIDENCE_REQUIRED_FOR_OBS_RUNTIME", c["residual_gap"])

    def test_product_level_subclaim_is_resolved_bounded(self):
        reg = {r["claim"]: r for r in rows(REG)}
        self.assertEqual(
            reg["Q-B05-004_PRODUCT_LEVEL_EVIDENCE"]["status"],
            "RESOLVED_BOUNDED_PRODUCT_EVIDENCE",
        )
        self.assertEqual(
            reg["PRODUCT_LEVEL_EVIDENCE_MITSUBISHI_WM50"]["status"],
            "QUALIFIED_BOUNDED",
        )
        self.assertEqual(
            reg["PRODUCT_LEVEL_EVIDENCE_DIMPLEX_LA2030CP"]["status"],
            "QUALIFIED_BOUNDED",
        )

    def test_current_fan_coil_divergence_and_readiness_are_preserved(self):
        reg = {r["claim"]: r for r in rows(REG)}
        fan = reg["HEM_FANCOIL_EMITTER_TIME_DOC_CODE_DIVERGENCE_REQUIRED"]
        self.assertEqual(fan["status"], "CONFIRMED_CURRENT_DIVERGENCE_Q")
        self.assertEqual((fan["lower_bound"], fan["upper_bound"], fan["unit"]), ("360", "1370", "s"))
        readiness = {r["component_id"]: r for r in rows(READINESS)}
        self.assertEqual(readiness["PART_LOAD_MODULATION"]["readiness_percent"], "45")
        self.assertIn("P27", readiness["PART_LOAD_MODULATION"]["notes"])

    def test_fresh_hem_sources_pack_and_readme_are_pinned(self):
        sources = {r["source_id"]: r for r in rows(HP_SOURCES)}
        for sid in (
            "SRC-B05-UK-HEM-TP12-HOURLY-ONOFF-2026",
            "SRC-B05-UK-HEM-RUST-ONOFF-CONSTANTS-2026",
        ):
            self.assertEqual(sources[sid]["retrieved_at"], "2026-09-25")
            self.assertIn("P27 fresh audit", sources[sid]["notes"])
        pack = PACK.read_text(encoding="utf-8")
        self.assertIn("Q-B05-004 remains OPEN", pack)
        self.assertIn("B05 = **64%**", pack)
        readme = README.read_text(encoding="utf-8")
        self.assertIn("B05-P27 repairs the internal semantics", readme)
        self.assertIn("PRODUCT_LEVEL_EVIDENCE", readme)

if __name__ == "__main__":
    unittest.main()
