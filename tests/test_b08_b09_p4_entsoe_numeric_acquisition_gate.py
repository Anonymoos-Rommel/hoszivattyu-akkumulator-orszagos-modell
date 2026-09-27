import csv
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "registry" / "b08_b09_p4_entsoe_numeric_acquisition_gate.csv"
QUESTIONS = ROOT / "registry" / "open_questions.csv"
AUDIT = ROOT / "registry" / "project_blocker_evidence_audit.csv"
PACK = ROOT / "docs" / "source_packs" / "B08_B09_P4_ENTSOE_NUMERIC_ACQUISITION_GATE.md"
B08 = ROOT / "modules" / "B08" / "observed_load_contract.py"
B09 = ROOT / "modules" / "B09" / "observed_generation_contract.py"


def read_rows(path):
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


class B08B09P4EntsoeNumericAcquisitionGateTests(unittest.TestCase):
    def test_both_real_panels_are_access_blocked_not_synthetically_filled(self):
        rows = {row["record_id"]: row for row in read_rows(REGISTRY)}
        for key in ("B08B09-P4-R01", "B08B09-P4-R02"):
            row = rows[key]
            self.assertEqual("ACCESS_BLOCKED_PENDING_AUTHENTICATED_EXPORT_OR_API_TOKEN", row["access_state"])
            self.assertEqual("LOGIN_REQUIRED", row["public_ui_bulk_export"])
            self.assertEqual("ENABLED_TOKEN_REQUIRED", row["web_api_access"])
            self.assertEqual("EXTERNAL_ONLY", row["raw_storage_policy"])
            self.assertEqual("UNRESOLVED", row["reuse_status"])

    def test_canonical_period_is_hungarian_2025_calendar_year_not_utc_midnight_year(self):
        rows = {row["record_id"]: row for row in read_rows(REGISTRY)}
        for key in ("B08B09-P4-R01", "B08B09-P4-R02"):
            self.assertEqual(
                "2024-12-31T23:00Z -> 2025-12-31T23:00Z",
                rows[key]["target_period_utc"],
            )
            self.assertIn("Europe/Budapest", rows[key]["target_period_local"])

    def test_token_is_never_part_of_canonical_repo_state(self):
        text = PACK.read_text(encoding="utf-8")
        self.assertIn("ENTSOE_SECURITY_TOKEN", text)
        self.assertIn("must never be placed", text)
        self.assertNotIn("securityToken=", text)

    def test_existing_parsers_are_the_execution_path(self):
        b08 = B08.read_text(encoding="utf-8")
        b09 = B09.read_text(encoding="utf-8")
        self.assertIn("def parse_entsoe_actual_total_load", b08)
        self.assertIn("documentType", b08)
        self.assertIn("A65", b08)
        self.assertIn("def parse_entsoe_actual_generation_per_type", b09)
        self.assertIn("A75", b09)
        self.assertIn("A08", b09)

    def test_open_questions_are_narrowed_to_exact_access_blocker(self):
        questions = {row["question_id"]: row for row in read_rows(QUESTIONS)}
        for qid in ("Q-B08-001", "Q-B09-001"):
            self.assertEqual("OPEN", questions[qid]["status"])
            self.assertIn("ENTSOE_REGISTERED_EXPORT_OR_API_TOKEN_REQUIRED", questions[qid]["notes"])

    def test_project_blocker_audit_remains_e3_model_blocker(self):
        audit = {row["blocker_id"]: row for row in read_rows(AUDIT)}
        for qid in ("Q-B08-001", "Q-B09-001"):
            row = audit[qid]
            self.assertEqual("E3", row["evidence_tier"])
            self.assertEqual("MODEL_BLOCKER", row["blocker_class"])
            self.assertEqual("yes", row["model_blocker"])
            self.assertIn("ENTSOE_REGISTERED_EXPORT_OR_API_TOKEN_REQUIRED", row["canonical_base_rule"])

    def test_no_readiness_uplift_is_claimed(self):
        text = PACK.read_text(encoding="utf-8")
        self.assertIn("No readiness percentage is increased", text)


if __name__ == "__main__":
    unittest.main()
