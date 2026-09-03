import csv
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
AUTHORITIES = ROOT / "registry/dso_service_area_crosswalk_authorities.csv"
SOURCES = ROOT / "registry/dso_service_area_membership_sources.csv"
TRANCHE = ROOT / "registry/dso_service_area_membership_crosswalk_tranche.csv"
CANONICAL = ROOT / "registry/dso_service_area_membership_crosswalk.csv"
DOC = ROOT / "docs/source_packs/P22_B10_EON_CURRENT_M1_AUTHORITY_RESOLUTION.md"


class B10P22EonCurrentM1ResolutionTests(unittest.TestCase):
    def rows(self, path):
        with path.open(encoding="utf-8", newline="") as handle:
            return list(csv.DictReader(handle))

    def test_three_mekh_approval_decisions_are_registered(self):
        rows = {row["source_id"]: row for row in self.rows(AUTHORITIES)}
        expected = {
            "SRC-B10-ELMU-USZ-APPROVAL-H1728-2025": "APPROVED_2025-06-13_INDEFINITE",
            "SRC-B10-EON-DDASZ-USZ-APPROVAL-H442-2025": "APPROVED_2025-02-13_INDEFINITE",
            "SRC-B10-EON-EDASZ-USZ-APPROVAL-H440-2025": "APPROVED_2025-02-13_INDEFINITE",
        }
        for source_id, status in expected.items():
            self.assertIn(source_id, rows)
            self.assertEqual(status, rows[source_id]["currentness_status"])
            self.assertEqual("OFFICIAL_MEKH_BUSINESS_RULE_APPROVAL_DECISION", rows[source_id]["source_kind"])

    def test_2026_compliance_reports_are_corroboration_not_current_selector(self):
        rows = {row["source_id"]: row for row in self.rows(AUTHORITIES)}
        for source_id in (
            "SRC-B10-ELMU-COMPLIANCE-REPORT-2025-PUB-2026",
            "SRC-B10-EON-DDASZ-COMPLIANCE-REPORT-2025-PUB-2026",
            "SRC-B10-EON-EDASZ-COMPLIANCE-REPORT-2025-PUB-2026",
        ):
            self.assertIn(source_id, rows)
            self.assertEqual("PUBLISHED_2026", rows[source_id]["currentness_status"])
            self.assertIn("ONLY", rows[source_id]["authorizes"])

    def test_eon_live_landing_is_navigation_only(self):
        rows = {row["source_id"]: row for row in self.rows(AUTHORITIES)}
        landing = rows["SRC-B10-EON-RULES-LANDING-2026"]
        self.assertEqual("CURRENT_PAGE_LIVE", landing["currentness_status"])
        self.assertEqual("RULES_NAVIGATION_ONLY_NOT_EXACT_ATTACHMENT_BINDING", landing["authorizes"])

    def test_eon_trio_have_narrowed_q_not_current_promotion(self):
        rows = {row["operator_id"]: row for row in self.rows(SOURCES)}
        for operator in ("ELMU", "EON_DDASZ", "EON_EDASZ"):
            self.assertEqual("Q_CURRENT_LANDING_TO_EXACT_M1_BINDING_REQUIRED", rows[operator]["currentness_status"])
            self.assertEqual("NOT_EXTRACTED", rows[operator]["extraction_status"])

    def test_no_eon_settlement_rows_are_promoted(self):
        operators = {row["operator_id"] for row in self.rows(TRANCHE)}
        self.assertNotIn("ELMU", operators)
        self.assertNotIn("EON_DDASZ", operators)
        self.assertNotIn("EON_EDASZ", operators)
        self.assertEqual({"MVM_DEMASZ", "MVM_EMASZ", "OPUS_TITASZ"}, operators)

    def test_national_crosswalk_remains_header_only(self):
        self.assertEqual(1, len(CANONICAL.read_text(encoding="utf-8").splitlines()))

    def test_document_states_exact_remaining_gate(self):
        text = DOC.read_text(encoding="utf-8")
        self.assertIn("OFFICIAL HOSTING != REGULATORY APPROVAL != CURRENT LIVE ATTACHMENT BINDING", text)
        self.assertIn("Q_CURRENT_LANDING_TO_EXACT_M1_BINDING_REQUIRED", text)
        self.assertIn("readiness remains **15**", text)


if __name__ == "__main__":
    unittest.main()
