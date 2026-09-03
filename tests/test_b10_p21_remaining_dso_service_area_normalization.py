import csv
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
TRANCHE = ROOT / "registry/dso_service_area_membership_crosswalk_tranche.csv"
AUTHORITIES = ROOT / "registry/dso_service_area_crosswalk_authorities.csv"
SOURCES = ROOT / "registry/dso_service_area_membership_sources.csv"
CANONICAL = ROOT / "registry/dso_service_area_membership_crosswalk.csv"
DOC = ROOT / "docs/source_packs/P21_B10_REMAINING_DSO_SERVICE_AREA_NORMALIZATION.md"


class B10P21RemainingDsoServiceAreaNormalizationTests(unittest.TestCase):
    def read_rows(self, path):
        with path.open(encoding="utf-8", newline="") as handle:
            return list(csv.DictReader(handle))

    def test_mvm_emasz_current_authority_is_registered(self):
        rows = {row["source_id"]: row for row in self.read_rows(AUTHORITIES)}
        src = rows["SRC-B10-MVM-EMASZ-M1-2026"]
        self.assertEqual("CURRENT_ON_2026_BUSINESS_RULE_PACKAGE", src["currentness_status"])
        self.assertIn("WHOLE_AND_NAMED_SUBSETTLEMENT", src["authorizes"])

    def test_exact_five_emasz_whole_settlement_rows_are_materialized(self):
        rows = [row for row in self.read_rows(TRANCHE) if row["operator_id"] == "MVM_EMASZ"]
        self.assertEqual(5, len(rows))
        self.assertEqual(
            {
                ("24554", "Abasár"),
                ("23241", "Adács"),
                ("09362", "Aggtelek"),
                ("06345", "Aldebrő"),
                ("05847", "Harsány"),
            },
            {(row["ksh_settlement_code"], row["settlement_name"]) for row in rows},
        )
        self.assertTrue(all(row["coverage_scope"] == "WHOLE_SETTLEMENT" for row in rows))
        self.assertTrue(all(row["evidence_status"] == "OBS" for row in rows))
        self.assertTrue(all(row["status"] == "WHOLE_SETTLEMENT_MEMBERSHIP_PROVEN" for row in rows))
        self.assertTrue(all(len(row["ksh_settlement_code"]) == 5 for row in rows))

    def test_emasz_named_subsettlements_are_not_promoted(self):
        names = {row["settlement_name"] for row in self.read_rows(TRANCHE) if row["operator_id"] == "MVM_EMASZ"}
        self.assertNotIn("Abaújdevecser", names)
        self.assertNotIn("Baglyasalja", names)
        self.assertNotIn("Bükkszentlászló", names)

    def test_eon_trio_remain_currentness_q_but_blocker_may_be_refined(self):
        rows = {row["operator_id"]: row for row in self.read_rows(SOURCES)}
        allowed_q = {
            "Q_CURRENT_VERSION_PIN_REQUIRED",
            "Q_CURRENT_LANDING_TO_EXACT_M1_BINDING_REQUIRED",
            "Q_EXACT_M1_ATTACHMENT_IDENTITY_REQUIRED",
        }
        for operator in ("ELMU", "EON_DDASZ", "EON_EDASZ"):
            self.assertIn(rows[operator]["currentness_status"], allowed_q)
            self.assertEqual("NOT_EXTRACTED", rows[operator]["extraction_status"])

    def test_tranche_now_has_three_operators_but_not_national_six(self):
        operators = {row["operator_id"] for row in self.read_rows(TRANCHE)}
        self.assertEqual({"MVM_DEMASZ", "OPUS_TITASZ", "MVM_EMASZ"}, operators)
        self.assertNotIn("ELMU", operators)
        self.assertNotIn("EON_DDASZ", operators)
        self.assertNotIn("EON_EDASZ", operators)

    def test_national_canonical_crosswalk_stays_header_only(self):
        lines = CANONICAL.read_text(encoding="utf-8").splitlines()
        self.assertEqual(1, len(lines))

    def test_document_preserves_currentness_and_completeness_boundaries(self):
        text = DOC.read_text(encoding="utf-8")
        self.assertIn("OFFICIAL HOSTING != CURRENTNESS PROOF", text)
        self.assertIn("Q_CURRENT_VERSION_PIN_REQUIRED", text)
        self.assertIn("readiness remains **15**", text)


if __name__ == "__main__":
    unittest.main()