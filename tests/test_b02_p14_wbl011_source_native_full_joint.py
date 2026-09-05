import csv
import string
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "registry" / "b02_wbl011_source_native_full_joint.csv"
P9_REGISTRY = ROOT / "registry" / "b02_archetype_admission_gate.csv"
JOINABILITY = ROOT / "data" / "processed" / "b02" / "b02_archetype_joinability_2022.csv"
OPEN_QUESTIONS = ROOT / "registry" / "open_questions.csv"
MODULE_STATUS = ROOT / "registry" / "module_status.csv"
DOC = ROOT / "docs" / "source_packs" / "B02_P14_WBL011_SOURCE_NATIVE_FULL_JOINT.md"

COUNTIES = {
    "HU110", "HU120", "HU211", "HU212", "HU213", "HU221", "HU222",
    "HU223", "HU231", "HU232", "HU233", "HU311", "HU312", "HU313",
    "HU321", "HU322", "HU323", "HU331", "HU332", "HU333",
}
HEX = set(string.hexdigits.lower())


class B02P14WBL011SourceNativeFullJointTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with REGISTRY.open(encoding="utf-8", newline="") as handle:
            cls.rows = list(csv.DictReader(handle))
        cls.county_rows = [row for row in cls.rows if row["scope_id"] != "NATIONAL"]
        cls.national = next(row for row in cls.rows if row["scope_id"] == "NATIONAL")

    def test_exact_twenty_county_surface_and_national_row(self):
        self.assertEqual(len(self.rows), 21)
        self.assertEqual(len(self.county_rows), 20)
        self.assertEqual({row["county_code"] for row in self.county_rows}, COUNTIES)

    def test_every_county_response_is_qualified_but_not_materialized(self):
        for row in self.county_rows:
            self.assertEqual(row["source_dataset_id"], "DATA-B02-KSH-WBL011")
            self.assertEqual(row["source_flow"], "WBL011")
            self.assertEqual(row["source_version"], "V67")
            self.assertEqual(row["evidence_status"], "QUALIFIED")
            self.assertEqual(row["materialization_status"], "SOURCE_VERIFIED_NOT_MATERIALIZED")
            self.assertEqual(int(row["delta"]), 0)

    def test_county_response_hashes_are_exact_sha256_shapes(self):
        for row in self.county_rows:
            for field in ("joint_response_sha256", "total_response_sha256"):
                value = row[field].lower()
                self.assertEqual(len(value), 64)
                self.assertTrue(set(value) <= HEX)

    def test_national_reconciliation_is_exact(self):
        self.assertEqual(sum(int(row["joint_record_count"]) for row in self.county_rows), 116452)
        self.assertEqual(sum(int(row["joint_dwelling_count"]) for row in self.county_rows), 4008541)
        self.assertEqual(
            sum(int(row["independent_total_dwelling_count"]) for row in self.county_rows),
            4008541,
        )
        self.assertEqual(sum(int(row["joint_response_bytes"]) for row in self.county_rows), 27375751)
        self.assertEqual(sum(int(row["total_response_bytes"]) for row in self.county_rows), 4618)

        self.assertEqual(self.national["county_code"], "HU")
        self.assertEqual(int(self.national["joint_record_count"]), 116452)
        self.assertEqual(int(self.national["joint_dwelling_count"]), 4008541)
        self.assertEqual(int(self.national["independent_total_dwelling_count"]), 4008541)
        self.assertEqual(int(self.national["delta"]), 0)
        self.assertEqual(int(self.national["joint_response_bytes"]), 27375751)
        self.assertEqual(int(self.national["total_response_bytes"]), 4618)
        self.assertEqual(self.national["joint_response_sha256"], "")
        self.assertEqual(self.national["total_response_sha256"], "")
        self.assertEqual(self.national["evidence_status"], "QUALIFIED")
        self.assertEqual(self.national["materialization_status"], "SOURCE_VERIFIED_NOT_MATERIALIZED")

    def test_p9_uses_materialization_blocker_not_source_availability_blocker(self):
        with P9_REGISTRY.open(encoding="utf-8", newline="") as handle:
            rows = {row["claim_id"]: row for row in csv.DictReader(handle)}
        for claim_id in ("CURRENT_STOCK_ARCHETYPE_ASSIGNMENT", "TECHNICAL_READINESS_ARCHETYPE"):
            row = rows[claim_id]
            self.assertEqual(row["current_status"], "Q")
            self.assertIn("NO_MATERIALIZED_COMPLETE_WBL_JOINT", row["current_blockers"])
            self.assertNotIn("NO_COMPLETE_WBL_JOINT", row["current_blockers"])

    def test_joinability_preserves_partial_materialization(self):
        with JOINABILITY.open(encoding="utf-8", newline="") as handle:
            rows = {row["join_id"]: row for row in csv.DictReader(handle)}
        core = rows["JOIN-B02-WBL011-CORE"]
        self.assertEqual(core["evidence_status"], "OBS")
        self.assertEqual(core["materialization_status"], "PARTIALLY_MATERIALIZED")
        self.assertIn("116452", core["permitted_link"])
        self.assertIn("4008541", core["permitted_link"])
        self.assertIn("source availability", core["prohibited_inference"])

    def test_document_freezes_source_materialization_boundary(self):
        text = DOC.read_text(encoding="utf-8")
        self.assertIn(
            "SOURCE-NATIVE COMPLETE WBL011 JOINT != REPOSITORY-MATERIALIZED COMPLETE WBL011 JOINT != POPULATED CURRENT-STOCK ARCHETYPE",
            text,
        )
        self.assertIn("**116 452**", text)
        self.assertIn("**4 008 541**", text)
        self.assertIn("**no readiness uplift**", text)
        self.assertIn("OÉNY request: **nem lett elküldve**", text)

    def test_open_questions_and_readiness_remain_fail_closed(self):
        with OPEN_QUESTIONS.open(encoding="utf-8", newline="") as handle:
            questions = {row["question_id"]: row for row in csv.DictReader(handle)}
        for question_id in ("Q-B02-001", "Q-B02-002", "Q-B02-004"):
            self.assertEqual(questions[question_id]["status"], "OPEN")

        with MODULE_STATUS.open(encoding="utf-8", newline="") as handle:
            modules = {row["module_id"]: row for row in csv.DictReader(handle)}
        b02 = modules["B02"]
        self.assertEqual(b02["readiness_percent"], "55")
        self.assertIn("B02-P14", b02["gate_note"])
        self.assertIn("116 452", b02["gate_note"])
        self.assertIn("NO_MATERIALIZED_COMPLETE_WBL_JOINT", b02["gate_note"])


if __name__ == "__main__":
    unittest.main()
