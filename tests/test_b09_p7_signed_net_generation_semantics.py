import csv
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "registry" / "b09_p7_signed_net_generation_semantics.csv"
AUDIT = ROOT / "registry" / "project_blocker_evidence_audit.csv"
QUESTIONS = ROOT / "registry" / "open_questions.csv"
SOURCES = ROOT / "registry" / "sources.csv"
PACK = ROOT / "docs" / "source_packs" / "B09_P7_SIGNED_NET_GENERATION_RECOVERY_SEMANTICS.md"


def rows(path):
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


class B09P7SignedNetGenerationSemanticsTests(unittest.TestCase):
    def test_directional_contract_is_explicit(self):
        r = {row["record_id"]: row for row in rows(REGISTRY)}
        self.assertEqual("EXECUTABLE", r["B09-P7-R01"]["status"])
        self.assertIn("injection=max(v,0)", r["B09-P7-R01"]["runtime_effect"])
        self.assertIn("NO_NEGATIVE_TO_ZERO_OR_ABS", r["B09-P7-R01"]["fail_closed_guard"])

    def test_numeric_a75_precedence_and_exact_key_match_are_locked(self):
        r = {row["record_id"]: row for row in rows(REGISTRY)}
        self.assertIn("RECOVERY_CANNOT_OVERWRITE_NUMERIC_A75", r["B09-P7-R03"]["fail_closed_guard"])
        self.assertIn("recovery key set must equal A75 missing key set", r["B09-P7-R04"]["runtime_effect"])

    def test_q_b09_001_is_now_e2_model_continue(self):
        audit = {row["blocker_id"]: row for row in rows(AUDIT)}
        x = audit["Q-B09-001"]
        self.assertEqual("E2", x["evidence_tier"])
        self.assertEqual("VALIDATION_BLOCKER", x["blocker_class"])
        self.assertEqual("no", x["model_blocker"])
        self.assertEqual("MODEL_CONTINUE", x["canonical_use"])
        self.assertIn("NO_OVERWRITE_NO_CLAMP", x["canonical_base_rule"])

    def test_open_question_records_executable_resolution(self):
        q = {row["question_id"]: row for row in rows(QUESTIONS)}
        notes = q["Q-B09-001"]["notes"]
        self.assertIn("SIGNED_NET_GENERATION_RECOVERY_SEMANTICS_REQUIRED is resolved executable", notes)
        self.assertIn("E2 / VALIDATION_BLOCKER / MODEL_CONTINUE", notes)

    def test_required_authority_sources_are_registered(self):
        source_ids = {row["source_id"] for row in rows(SOURCES)}
        self.assertIn("SRC-B09-MAVIR-FUEL-NET-OPERATIONAL-2026", source_ids)
        self.assertIn("SRC-B09-EU-543-2013-TOTAL-LOAD-BALANCE", source_ids)

    def test_source_pack_forbids_double_count_and_relabelling(self):
        text = PACK.read_text(encoding="utf-8")
        self.assertIn("residual_demand = B08_net_grid_load - net_generation", text)
        self.assertIn("not** separately added to B08 load", text)
        self.assertIn("negative -> abs(value)", text)
        self.assertIn("RECOVERY_KEYS == A75_MISSING_KEYS", text)


if __name__ == "__main__":
    unittest.main()
