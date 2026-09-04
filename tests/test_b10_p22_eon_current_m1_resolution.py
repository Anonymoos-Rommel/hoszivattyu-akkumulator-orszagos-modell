import csv
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
AUTHORITIES = ROOT / "registry/dso_service_area_crosswalk_authorities.csv"
SOURCES = ROOT / "registry/dso_service_area_membership_sources.csv"
TRANCHE = ROOT / "registry/dso_service_area_membership_crosswalk_tranche.csv"
CANONICAL = ROOT / "registry/dso_service_area_membership_crosswalk.csv"
DOC = ROOT / "docs/source_packs/P22_B10_EON_CURRENT_M1_AUTHORITY_RESOLUTION.md"

P35_KSH_SOURCE = "SRC-B10-KSH-HNT-2025-SETTLEMENT-IDS"


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
            self.assertIn("WITH_ATTACHMENTS", rows[source_id]["authorizes"])

    def test_current_eon_landing_authority_is_proven_for_all_three(self):
        rows = {row["source_id"]: row for row in self.rows(AUTHORITIES)}
        hmke = rows["SRC-B10-EON-HMKE-CURRENT-EUSZ-LANDING-2026"]
        self.assertEqual("CURRENT_2026_DOCUMENT", hmke["currentness_status"])
        self.assertEqual("CURRENT_EUSZ_LANDING_FOR_ELMU_DDASZ_EDASZ", hmke["authorizes"])
        landing = rows["SRC-B10-EON-RULES-LANDING-2026"]
        self.assertEqual("CURRENT_PAGE_LIVE", landing["currentness_status"])

    def test_exact_m1_identity_is_derived_from_approved_package_revision_lineage(self):
        rows = {row["source_id"]: row for row in self.rows(AUTHORITIES)}
        for source_id in (
            "SRC-B10-ELMU-M1-CANDIDATE-2025",
            "SRC-B10-EON-DDASZ-M1-CANDIDATE-2025",
            "SRC-B10-EON-EDASZ-M1-CANDIDATE-2025",
        ):
            self.assertEqual("CURRENT_2026_DER_APPROVED_PACKAGE_REVISION_LINEAGE", rows[source_id]["currentness_status"])
            self.assertEqual("OFFICIAL_APPROVED_PACKAGE_M1_ATTACHMENT", rows[source_id]["source_kind"])
            self.assertEqual("WHOLE_SETTLEMENT_DSO_MEMBERSHIP_DER_ONLY", rows[source_id]["authorizes"])

    def test_eon_trio_are_no_longer_currentness_q(self):
        rows = {row["operator_id"]: row for row in self.rows(SOURCES)}
        for operator in ("ELMU", "EON_DDASZ", "EON_EDASZ"):
            self.assertEqual("CURRENT_2026_DER_APPROVED_PACKAGE_REVISION_LINEAGE", rows[operator]["currentness_status"])
            self.assertEqual("PARTIAL_TRANCHE_MATERIALIZED", rows[operator]["extraction_status"])

    def test_exact_nine_eon_rows_are_materialized_as_der(self):
        rows = [row for row in self.rows(TRANCHE) if row["operator_id"] in {"ELMU", "EON_DDASZ", "EON_EDASZ"}]
        self.assertEqual(9, len(rows))
        expected = {
            ("18573", "Acsa", "ELMU"),
            ("23199", "Alsónémedi", "ELMU"),
            ("33561", "Apaj", "ELMU"),
            ("12548", "Abaliget", "EON_DDASZ"),
            ("06080", "Ádánd", "EON_DDASZ"),
            ("08925", "Adony", "EON_DDASZ"),
            ("17376", "Aba", "EON_EDASZ"),
            ("11882", "Abda", "EON_EDASZ"),
            ("04428", "Ács", "EON_EDASZ"),
        }
        self.assertEqual(expected, {(row["ksh_settlement_code"], row["settlement_name"], row["operator_id"]) for row in rows})
        self.assertTrue(all(row["evidence_status"] == "DER" for row in rows))
        self.assertTrue(all(row["status"] == "WHOLE_SETTLEMENT_MEMBERSHIP_PROVEN" for row in rows))
        self.assertTrue(all(row["coverage_scope"] == "WHOLE_SETTLEMENT" for row in rows))

    def test_p22_snapshot_has_all_six_operators_and_survives_later_evolving_tranches(self):
        rows = self.rows(TRANCHE)
        operators = {row["operator_id"] for row in rows}
        self.assertEqual({"ELMU", "EON_DDASZ", "EON_EDASZ", "MVM_DEMASZ", "MVM_EMASZ", "OPUS_TITASZ"}, operators)

        p22_snapshot = [
            row for row in rows
            if P35_KSH_SOURCE not in row["source_ids"].split(";")
        ]
        self.assertEqual(34, len(p22_snapshot))
        self.assertGreaterEqual(len(rows), len(p22_snapshot))

    def test_national_crosswalk_remains_header_only(self):
        self.assertEqual(1, len(CANONICAL.read_text(encoding="utf-8").splitlines()))

    def test_document_preserves_der_and_completeness_boundaries(self):
        text = DOC.read_text(encoding="utf-8")
        self.assertIn("CURRENT_2026_DER_APPROVED_PACKAGE_REVISION_LINEAGE", text)
        self.assertIn("DER != OBS", text)
        self.assertIn("six operators", text)
        self.assertIn("registry/dso_service_area_membership_crosswalk.csv", text)
        self.assertIn("remains header-only", text)
        self.assertIn("readiness remains **15**", text)


if __name__ == "__main__":
    unittest.main()
