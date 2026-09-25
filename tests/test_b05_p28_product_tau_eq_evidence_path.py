import csv
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
QUESTIONS = ROOT / "registry" / "open_questions.csv"
REG = ROOT / "registry" / "b05_p28_product_tau_eq_evidence_path.csv"
VARIABLES = ROOT / "registry" / "heat_pump_variables.csv"
READINESS = ROOT / "registry" / "heat_pump_readiness.csv"
HP_SOURCES = ROOT / "registry" / "heat_pump_sources.csv"
SOURCES = ROOT / "registry" / "sources.csv"
PACK = ROOT / "docs" / "source_packs" / "B05_P28_PRODUCT_TAU_EQ_EVIDENCE_PATH.md"
README = ROOT / "modules" / "B05" / "README.md"

def rows(path):
    with path.open(encoding="utf-8", newline="") as h:
        return list(csv.DictReader(h))

class B05P28ProductTauEqEvidencePathTests(unittest.TestCase):
    def test_q_b05_004_remains_open_and_records_p28_narrowing(self):
        q = {r["question_id"]: r for r in rows(QUESTIONS)}["Q-B05-004"]
        self.assertEqual(q["status"], "OPEN")
        self.assertIn("B05-P28", q["notes"])
        self.assertIn("PRODUCT_OR_LAB_TRANSIENT_TEST_RECORD_REQUIRED", q["notes"])

    def test_product_tau_eq_remains_q(self):
        variables = {r["variable_id"]: r for r in rows(VARIABLES)}
        tau = variables["VAR-B05-ONOFF-TRANSIENT-TAU-EQ"]
        self.assertEqual(tau["status"], "Q")
        self.assertEqual(tau["updated_at"], "2026-09-25")
        self.assertIn("SRC-B05-UK-PCDB-MITSUBISHI-WM50-2026", tau["source_ids"])
        self.assertIn("SRC-B05-UK-PCDB-DIMPLEX-LA2030CP-2026", tau["source_ids"])
        self.assertIn("PRODUCT_OR_LAB_TRANSIENT_TEST_RECORD_REQUIRED", tau["notes"])

    def test_public_pcdb_absence_is_not_promoted_to_internal_absence(self):
        reg = {r["claim"]: r for r in rows(REG)}
        self.assertEqual(
            reg["MITSUBISHI_WM50_PUBLIC_PCDB_TAU_EQ_EXPOSURE"]["status"],
            "NOT_EXPOSED_ON_PUBLIC_RECORD",
        )
        self.assertEqual(
            reg["DIMPLEX_LA2030CP_PUBLIC_PCDB_TAU_EQ_EXPOSURE"]["status"],
            "NOT_EXPOSED_ON_PUBLIC_RECORD",
        )
        self.assertIn("CLAIM_INTERNAL_DATA_ABSENCE", reg["MITSUBISHI_WM50_PUBLIC_PCDB_TAU_EQ_EXPOSURE"]["forbidden_use"])

    def test_false_substitutes_are_forbidden(self):
        reg = {r["claim"]: r for r in rows(REG)}
        self.assertEqual(reg["CDH_TO_PRODUCT_TAU_EQ_INFERENCE"]["status"], "FORBIDDEN")
        self.assertEqual(reg["HEM_DEFAULT_140S_AS_PRODUCT_OBS"]["status"], "FORBIDDEN")
        pack = PACK.read_text(encoding="utf-8")
        for marker in (
            "Cdh -> tau_eq without explicit authority",
            "controller anti-cycling timer -> tau_eq",
            "HEM 140 s default -> product OBS",
        ):
            self.assertIn(marker, pack)

    def test_new_sources_are_registered_in_both_registries(self):
        hp = {r["source_id"]: r for r in rows(HP_SOURCES)}
        generic = {r["source_id"]: r for r in rows(SOURCES)}
        for sid in (
            "SRC-B05-UK-PCDB-MITSUBISHI-WM50-2026",
            "SRC-B05-UK-PCDB-DIMPLEX-LA2030CP-2026",
        ):
            self.assertIn(sid, hp)
            self.assertIn(sid, generic)
            self.assertEqual(hp[sid]["retrieved_at"], "2026-09-25")

    def test_readiness_stays_bounded(self):
        readiness = {r["component_id"]: r for r in rows(READINESS)}
        self.assertEqual(readiness["PART_LOAD_MODULATION"]["readiness_percent"], "45")
        self.assertIn("P28", readiness["PART_LOAD_MODULATION"]["notes"])
        pack = PACK.read_text(encoding="utf-8")
        self.assertIn("B05 = **64%**", pack)
        self.assertIn("No readiness uplift", pack)
        readme = README.read_text(encoding="utf-8")
        self.assertIn("B05-P28 audits the product-specific", readme)

if __name__ == "__main__":
    unittest.main()
