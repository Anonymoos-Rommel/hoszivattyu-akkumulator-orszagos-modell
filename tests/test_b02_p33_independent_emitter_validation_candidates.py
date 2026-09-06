import csv
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CANDIDATES = ROOT / "registry" / "b02_p33_independent_emitter_validation_candidates.csv"
LINKAGE = ROOT / "registry" / "b02_calibrated_linkage_admission.csv"
DOC = ROOT / "docs" / "source_packs" / "B02_P33_INDEPENDENT_EMITTER_VALIDATION_CANDIDATES.md"


class B02P33IndependentEmitterValidationCandidateTests(unittest.TestCase):
    def _candidate_rows(self) -> dict[str, dict[str, str]]:
        with CANDIDATES.open(encoding="utf-8", newline="") as handle:
            return {row["candidate_id"]: row for row in csv.DictReader(handle)}

    def test_exact_three_candidates_and_reference_only_policy(self):
        rows = self._candidate_rows()
        self.assertEqual(set(rows), {"B02-P33-C01", "B02-P33-C02", "B02-P33-C03"})
        for row in rows.values():
            self.assertEqual(row["repo_binary_policy"], "REFERENCE_ONLY_NO_BINARY")
            self.assertTrue(row["external_url"].startswith("https://"))
            self.assertTrue(row["exact_locator"])

    def test_hkef_proves_explicit_taxonomy_only(self):
        row = self._candidate_rows()["B02-P33-C01"]
        self.assertEqual(row["evidence_role"], "SOURCE_NATIVE_TAXONOMY")
        self.assertIn("FUTMOD=4", row["exact_locator"])
        self.assertIn("EGYEDI=1", row["exact_locator"])
        self.assertEqual(row["validation_admissible"], "NO")
        self.assertEqual(row["current_stock_authority"], "NO")

    def test_stadat_derivation_remains_fail_closed(self):
        row = self._candidate_rows()["B02-P33-C02"]
        self.assertEqual(row["validation_admissible"], "NO")
        self.assertEqual(row["current_status"], "Q")
        self.assertEqual(row["blockers"], "QUESTIONNAIRE_TO_PUBLICATION_DERIVATION_UNPROVEN")
        self.assertIn("11.7%", row["source_native_fact"])
        self.assertNotIn("gas-convector prevalence", row["source_native_fact"].lower())

    def test_nees_is_historical_holdout_not_current_authority(self):
        row = self._candidate_rows()["B02-P33-C03"]
        self.assertEqual(row["evidence_role"], "INDEPENDENT_HISTORICAL_STRUCTURAL_HOLDOUT")
        self.assertEqual(row["independent_from_p30_calibration"], "YES")
        self.assertEqual(row["current_stock_authority"], "NO")
        self.assertEqual(row["validation_admissible"], "NO")
        self.assertIn("HISTORICAL_NOT_CURRENT", row["blockers"])
        self.assertIn("20842", row["source_native_fact"])

    def test_p30_admission_remains_unclosed(self):
        with LINKAGE.open(encoding="utf-8", newline="") as handle:
            rows = {row["claim_id"]: row for row in csv.DictReader(handle)}
        row = rows["CALIBRATED_GAS_CONVECTOR_EMITTER_LINKAGE_P30"]
        self.assertEqual(row["approval_status"], "NOT_APPROVED")
        self.assertEqual(row["validation_metrics"], "no")
        self.assertEqual(row["independence_assumption_controlled"], "no")
        self.assertEqual(row["current_status"], "Q")
        self.assertEqual(
            row["blockers"],
            "NO_JOSEPH_APPROVAL;NO_VALIDATION_METRICS;UNCONTROLLED_INDEPENDENCE_ASSUMPTION",
        )

    def test_source_pack_preserves_fail_closed_boundaries(self):
        text = DOC.read_text(encoding="utf-8")
        required = (
            "VALIDATION CANDIDATE != VALIDATION METRIC",
            "SOURCE-NATIVE LABEL SIMILARITY != PROVEN PUBLICATION DERIVATION",
            "HISTORICAL FIELD SURVEY != CURRENT STOCK AUTHORITY",
            "STADAT \"Egyedi helyiségfűtés gázzal\" -> GAS_CONVECTOR = DERIVATION_UNPROVEN",
            "B02 readiness remains `55%`",
        )
        for marker in required:
            self.assertIn(marker, text)


if __name__ == "__main__":
    unittest.main()
