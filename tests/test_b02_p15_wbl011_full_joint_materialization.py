import csv
import hashlib
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "processed" / "b02"
REGISTRY = ROOT / "registry" / "b02_wbl011_full_joint_materialization.csv"
DOC = ROOT / "docs" / "source_packs" / "B02_P15_WBL011_FULL_JOINT_MATERIALIZATION.md"

class B02P15FullJointMaterializationTests(unittest.TestCase):
    def test_materialization_registry_matches_committed_artifact(self):
        with REGISTRY.open(encoding="utf-8", newline="") as handle:
            rows = list(csv.DictReader(handle))
        self.assertEqual(1, len(rows))
        row = rows[0]
        self.assertEqual("MATERIALIZED", row["materialization_status"])
        self.assertEqual("116452", row["record_count"])
        self.assertEqual("4008541", row["population_count"])
        self.assertEqual("20", row["p14_record_count_match_count"])
        self.assertEqual("20", row["p14_response_bytes_match_count"])
        self.assertGreater(int(row["p14_raw_hash_differ_count"]), 0)
        self.assertEqual(row["combined_output_sha256"], hashlib.sha256((DATA / "ksh_wbl_joint_cells_2022.csv").read_bytes()).hexdigest())

    def test_materialization_remains_valid_after_p21_model_admission(self):
        with (ROOT / "registry" / "b02_archetype_admission_gate.csv").open(encoding="utf-8", newline="") as handle:
            rows = {r["claim_id"]: r for r in csv.DictReader(handle)}
        stock = rows["CURRENT_STOCK_ARCHETYPE_ASSIGNMENT"]
        self.assertNotIn("NO_MATERIALIZED_COMPLETE_WBL_JOINT", stock["current_blockers"])
        self.assertEqual("", stock["current_blockers"])
        self.assertEqual("QUALIFIED", stock["current_status"])

    def test_source_pack_freezes_materialization_boundary(self):
        text = DOC.read_text(encoding="utf-8")
        self.assertIn("**116 452**", text)
        self.assertIn("**4 008 541**", text)
        self.assertIn("RAW RESPONSE SHA-256 = RETRIEVAL-INSTANCE LINEAGE != IMMUTABLE DATASET FINGERPRINT", text)
        self.assertIn("**no readiness uplift**", text)
        self.assertIn("OÉNY request: **nem lett elküldve**", text)

if __name__ == "__main__":
    unittest.main()
