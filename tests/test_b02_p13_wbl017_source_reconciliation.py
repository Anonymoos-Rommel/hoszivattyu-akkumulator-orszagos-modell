import csv
import unittest
from pathlib import Path

from modules.B02.wbl017_codeset_authority import (
    QUALIFIED,
    CodeSetAuthorityInputs,
    GapCauseInputs,
    assess_codeset_authority,
    assess_gap_cause,
)


ROOT = Path(__file__).resolve().parents[1]
HIERARCHY = ROOT / "data" / "processed" / "b02" / "ksh_wbl017_futmodag_hierarchy_2022.csv"
SUMMARY = ROOT / "registry" / "b02_wbl017_source_reconciliation.csv"
AUTHORITY = ROOT / "registry" / "b02_wbl017_codeset_authority.csv"
OPEN_QUESTIONS = ROOT / "registry" / "open_questions.csv"
MODULE_STATUS = ROOT / "registry" / "module_status.csv"
DOC = ROOT / "docs" / "source_packs" / "B02_P13_WBL017_SOURCE_NATIVE_RECONCILIATION.md"


class B02P13WBL017SourceReconciliationTests(unittest.TestCase):
    def _hierarchy(self):
        with HIERARCHY.open(encoding="utf-8", newline="") as handle:
            return {row["code_id"]: row for row in csv.DictReader(handle)}

    def test_exact_source_native_hierarchy_is_materialized(self):
        rows = self._hierarchy()
        self.assertEqual(
            set(rows),
            {
                "TOTAL", "01-12", "01-05", "01", "02", "03", "04-05", "06-12",
                "13-24", "13-17", "13", "14", "15", "16-17", "18-24", "18",
                "19", "20-24", "25",
            },
        )
        self.assertEqual(rows["01-12"]["parent_code"], "TOTAL")
        self.assertEqual(rows["13-24"]["parent_code"], "TOTAL")
        self.assertEqual(rows["25"]["parent_code"], "TOTAL")
        self.assertEqual(rows["18"]["parent_code"], "18-24")

    def test_parent_child_counts_reconcile_exactly(self):
        rows = self._hierarchy()
        count = lambda code: int(rows[code]["national_presence_sum"])
        self.assertEqual(count("01") + count("02") + count("03"), count("01-05"))
        self.assertEqual(count("01-05") + count("06-12"), count("01-12"))
        self.assertEqual(count("13") + count("14") + count("15"), count("13-17"))
        self.assertEqual(count("18") + count("19"), count("18-24"))
        self.assertEqual(count("13-17") + count("18-24"), count("13-24"))

    def test_unreturned_rows_are_not_relabelled_obs_zero(self):
        rows = self._hierarchy()
        for code in ("04-05", "16-17", "20-24"):
            self.assertEqual(rows[code]["evidence_status"], "NO_RETURNED_ROW")
            self.assertEqual(rows[code]["national_presence_sum"], "")

    def test_top_level_population_residual_is_exact_88977(self):
        rows = self._hierarchy()
        classified = sum(int(rows[code]["national_presence_sum"]) for code in ("01-12", "13-24", "25"))
        self.assertEqual(classified, 3919564)
        self.assertEqual(4008541 - classified, 88977)

    def test_top_level_hosziv1_residual_is_exact_6294(self):
        rows = self._hierarchy()
        classified = sum(int(rows[code]["national_hosziv_1"]) for code in ("01-12", "13-24", "25"))
        self.assertEqual(classified, 61559)
        self.assertEqual(67853 - classified, 6294)

    def test_reconciliation_registry_records_both_qualified_mechanisms(self):
        with SUMMARY.open(encoding="utf-8", newline="") as handle:
            rows = {row["claim_id"]: row for row in csv.DictReader(handle)}
        self.assertEqual(set(rows), {"WBL017_OCCUPIED_TOTAL_CLASSIFICATION", "WBL017_HOSZIV1_TOTAL_CLASSIFICATION"})
        self.assertEqual(rows["WBL017_OCCUPIED_TOTAL_CLASSIFICATION"]["residual"], "88977")
        self.assertEqual(rows["WBL017_HOSZIV1_TOTAL_CLASSIFICATION"]["residual"], "6294")
        for row in rows.values():
            self.assertEqual(row["mechanism_status"], "QUALIFIED")
            self.assertEqual(row["evidence_status"], "DER")

    def test_code_set_authority_no_longer_requires_population_total_reconciliation(self):
        decision = assess_codeset_authority(
            CodeSetAuthorityInputs(
                structure_pinned=True,
                selected_codes_exist_in_source=True,
                source_leaf_partition_explicitly_proven=True,
                selected_codes_exhaustive=True,
                selected_codes_disjoint=True,
                leaf_projection_reconciled_to_total=False,
            )
        )
        self.assertEqual(decision.status, QUALIFIED)
        self.assertEqual(decision.blockers, ())

    def test_exact_classification_residual_is_a_qualified_gap_mechanism(self):
        decision = assess_gap_cause(
            GapCauseInputs(
                source_native_cause_identified=True,
                cause_evidence_status="DER",
                cause_reconciles_exact_gap=True,
            )
        )
        self.assertEqual(decision.status, QUALIFIED)

    def test_p11_authority_registry_is_promoted_by_new_evidence(self):
        with AUTHORITY.open(encoding="utf-8", newline="") as handle:
            rows = {row["claim_id"]: row for row in csv.DictReader(handle)}
        for row in rows.values():
            self.assertEqual(row["authority_status"], "QUALIFIED")
            self.assertEqual(row["blockers"], "")

    def test_open_questions_and_readiness_do_not_overclaim(self):
        with OPEN_QUESTIONS.open(encoding="utf-8", newline="") as handle:
            questions = {row["question_id"]: row for row in csv.DictReader(handle)}
        for qid in ("Q-B02-001", "Q-B02-002", "Q-B02-004"):
            self.assertEqual(questions[qid]["status"], "OPEN")
        with MODULE_STATUS.open(encoding="utf-8", newline="") as handle:
            modules = {row["module_id"]: row for row in csv.DictReader(handle)}
        self.assertEqual(modules["B02"]["readiness_percent"], "55")
        self.assertIn("B02-P13", modules["B02"]["gate_note"])

    def test_document_records_rejected_nheat_hypothesis_and_boundaries(self):
        text = DOC.read_text(encoding="utf-8")
        self.assertIn("1 173 639", text)
        self.assertIn("88 977 = NHEAT", text)
        self.assertIn("COMPLETE NON-TOTAL CODESET != COMPLETE POPULATION CLASSIFICATION", text)
        self.assertIn("B02 readiness: **55%**", text)


if __name__ == "__main__":
    unittest.main()
