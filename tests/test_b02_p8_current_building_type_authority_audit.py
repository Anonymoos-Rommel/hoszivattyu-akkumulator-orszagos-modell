import csv
import unittest
from pathlib import Path

from modules.B02.building_type_authority_gate import (
    BuildingTypeAuthorityCandidate,
    Q,
    QUALIFIED,
    assess_building_type_authority,
)


ROOT = Path(__file__).resolve().parents[1]
AUDIT = ROOT / "registry" / "b02_current_building_type_authority_audit.csv"
OPEN_QUESTIONS = ROOT / "registry" / "open_questions.csv"
MODULE_STATUS = ROOT / "registry" / "module_status.csv"
DOC = ROOT / "docs" / "source_packs" / "B02_P8_CURRENT_BUILDING_TYPE_AUTHORITY_AUDIT.md"

MANIFESTS = (
    ROOT / "evidence" / "history" / "SRC-B02-KSH-CENSUS-QUESTIONNAIRE-2022" / "manifest.csv",
    ROOT / "evidence" / "history" / "SRC-B02-KSH-CENSUS-STATIC-TABLES-2022" / "manifest.csv",
    ROOT / "evidence" / "history" / "SRC-B02-KSH-REAL-ESTATE-METHODOLOGY-2026" / "manifest.csv",
)


class B02P8CurrentBuildingTypeAuthorityAuditTests(unittest.TestCase):
    def test_all_audited_current_sources_fail_closed(self):
        with AUDIT.open(encoding="utf-8", newline="") as handle:
            rows = list(csv.DictReader(handle))
        self.assertEqual(len(rows), 3)
        self.assertEqual({row["gate_status"] for row in rows}, {"Q"})
        self.assertEqual({row["q_b02_002_effect"] for row in rows}, {"OPEN"})
        self.assertEqual({row["publishes_occupied_stock_distribution"] for row in rows}, {"no"})
        self.assertEqual({row["wbl_compatible_join_key"] for row in rows}, {"no"})

    def test_transaction_source_is_not_stock_authority(self):
        candidate = BuildingTypeAuthorityCandidate(
            source_id="SRC-B02-KSH-REAL-ESTATE-METHODOLOGY-2026",
            reference_year=2024,
            source_universe="USED_HOUSING_TRANSACTIONS",
            source_grain="TRANSACTION_RECORDS_WITH_RECORDED_FLOOR_AREA",
            building_type_taxonomy="FAMILY_HOUSE_VS_MULTI_DWELLING_COMPATIBLE",
            evidence_status="OBS",
            publishes_stock_distribution=False,
            wbl_compatible_join_key=False,
        )
        decision = assess_building_type_authority(candidate)
        self.assertEqual(decision.status, Q)
        self.assertIn("NOT_OCCUPIED_DWELLING_STOCK", decision.reasons)
        self.assertIn("NO_STOCK_DISTRIBUTION", decision.reasons)
        self.assertIn("NO_WBL_COMPATIBLE_JOIN_KEY", decision.reasons)

    def test_gate_can_accept_only_a_complete_current_stock_authority(self):
        candidate = BuildingTypeAuthorityCandidate(
            source_id="FIXTURE-CURRENT-STOCK-AUTHORITY",
            reference_year=2022,
            source_universe="OCCUPIED_DWELLING_STOCK",
            source_grain="COUNTY_X_SETTLEMENT_TYPE",
            building_type_taxonomy="FAMILY_HOUSE_VS_MULTI_DWELLING_COMPATIBLE",
            evidence_status="OBS",
            publishes_stock_distribution=True,
            wbl_compatible_join_key=True,
        )
        decision = assess_building_type_authority(candidate)
        self.assertEqual(decision.status, QUALIFIED)
        self.assertEqual(decision.reasons, ())

    def test_q_b02_002_remains_open(self):
        with OPEN_QUESTIONS.open(encoding="utf-8", newline="") as handle:
            rows = {row["question_id"]: row for row in csv.DictReader(handle)}
        self.assertEqual(rows["Q-B02-002"]["status"], "OPEN")

    def test_b02_readiness_does_not_increase(self):
        with MODULE_STATUS.open(encoding="utf-8", newline="") as handle:
            rows = {row["module_id"]: row for row in csv.DictReader(handle)}
        self.assertEqual(rows["B02"]["readiness_percent"], "55")
        self.assertIn("B02-P8", rows["B02"]["gate_note"])
        self.assertIn("no readiness uplift", rows["B02"]["gate_note"].lower())

    def test_source_manifests_are_reuse_cleared_but_snapshot_pending(self):
        for path in MANIFESTS:
            with path.open(encoding="utf-8", newline="") as handle:
                rows = list(csv.DictReader(handle))
            self.assertEqual(len(rows), 1)
            row = rows[0]
            self.assertEqual(row["reuse_status"], "REPOSITORY_COPY_CLEARED_ATTRIBUTION_REQUIRED")
            self.assertEqual(row["sha256"], "")
            self.assertTrue(row["snapshot_status"].startswith("PENDING_"))

    def test_document_freezes_non_inference_boundaries(self):
        text = DOC.read_text(encoding="utf-8")
        self.assertIn(
            "CENSUS-ASSISTED TRANSACTION CLASSIFICATION != OCCUPIED-STOCK DISTRIBUTION != WBL JOINT AUTHORITY",
            text,
        )
        self.assertIn("Q-B02-002` remains **OPEN**", text)
        self.assertIn("No readiness uplift", text)


if __name__ == "__main__":
    unittest.main()
