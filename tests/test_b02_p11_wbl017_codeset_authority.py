import csv
import unittest
from pathlib import Path

from modules.B02.wbl017_codeset_authority import (
    Q,
    QUALIFIED,
    CodeSetAuthorityInputs,
    GapCauseInputs,
    assess_codeset_authority,
    assess_gap_cause,
)


ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "registry" / "b02_wbl017_codeset_authority.csv"
OPEN_QUESTIONS = ROOT / "registry" / "open_questions.csv"
MODULE_STATUS = ROOT / "registry" / "module_status.csv"
DOC = ROOT / "docs" / "source_packs" / "B02_P11_WBL017_CODESET_AUTHORITY.md"
EXTRACTOR = ROOT / "tools" / "extract_b02_ksh_wbl_joint_cells.py"


CURRENT_CODESET = CodeSetAuthorityInputs(
    structure_pinned=True,
    selected_codes_exist_in_source=True,
    source_leaf_partition_explicitly_proven=False,
    selected_codes_exhaustive=False,
    selected_codes_disjoint=False,
    leaf_projection_reconciled_to_total=False,
)

CURRENT_CAUSE = GapCauseInputs(
    source_native_cause_identified=False,
    cause_evidence_status="Q",
    cause_reconciles_exact_gap=False,
)


class B02P11WBL017CodeSetAuthorityTests(unittest.TestCase):
    def test_unproven_codeset_fails_closed(self):
        decision = assess_codeset_authority(CURRENT_CODESET)
        self.assertEqual(decision.status, Q)
        self.assertEqual(
            set(decision.blockers),
            {
                "SOURCE_LEAF_PARTITION_NOT_PROVEN",
                "SELECTED_CODESET_NOT_EXHAUSTIVE",
                "SELECTED_CODESET_NOT_DISJOINT",
            },
        )

    def test_source_code_existence_is_not_exhaustiveness(self):
        decision = assess_codeset_authority(
            CodeSetAuthorityInputs(
                structure_pinned=True,
                selected_codes_exist_in_source=True,
                source_leaf_partition_explicitly_proven=False,
                selected_codes_exhaustive=False,
                selected_codes_disjoint=True,
                leaf_projection_reconciled_to_total=True,
            )
        )
        self.assertEqual(decision.status, Q)
        self.assertIn("SOURCE_LEAF_PARTITION_NOT_PROVEN", decision.blockers)
        self.assertIn("SELECTED_CODESET_NOT_EXHAUSTIVE", decision.blockers)

    def test_proven_non_total_codeset_can_qualify_with_population_residual(self):
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

    def test_unresolved_gap_cause_fails_closed(self):
        decision = assess_gap_cause(CURRENT_CAUSE)
        self.assertEqual(decision.status, Q)
        self.assertEqual(
            decision.blockers,
            (
                "SOURCE_NATIVE_CAUSE_UNRESOLVED",
                "CAUSE_EVIDENCE_NOT_OBS_OR_DER",
                "CAUSE_DOES_NOT_RECONCILE_EXACT_GAP",
            ),
        )

    def test_source_native_exact_gap_cause_can_qualify(self):
        decision = assess_gap_cause(
            GapCauseInputs(
                source_native_cause_identified=True,
                cause_evidence_status="DER",
                cause_reconciles_exact_gap=True,
            )
        )
        self.assertEqual(decision.status, QUALIFIED)
        self.assertEqual(decision.blockers, ())

    def test_p13_registry_supersedes_current_p11_q_state(self):
        with REGISTRY.open(encoding="utf-8", newline="") as handle:
            rows = {row["claim_id"]: row for row in csv.DictReader(handle)}
        self.assertEqual(
            set(rows),
            {
                "WBL017_FUTMODAG_V3_CODESET_AUTHORITY",
                "WBL017_POPULATION_GAP_CAUSE",
                "WBL017_HOSZIV1_GAP_CAUSE",
            },
        )
        for row in rows.values():
            self.assertEqual(row["authority_status"], "QUALIFIED")
            self.assertEqual(row["cause_evidence_status"], "DER")
        self.assertEqual(
            rows["WBL017_POPULATION_GAP_CAUSE"]["count_or_existence_evidence_status"],
            "DER",
        )

    def test_extractor_contains_bounded_13_code_selection(self):
        text = EXTRACTOR.read_text(encoding="utf-8")
        for code in (
            '"01"', '"02"', '"03"', '"04-05"', '"06-12"', '"13"',
            '"14"', '"15"', '"16-17"', '"18"', '"19"', '"20-24"', '"25"',
        ):
            self.assertIn(code, text)
        self.assertIn("missing = set(selected) - available[dimension]", text)

    def test_open_questions_remain_open(self):
        with OPEN_QUESTIONS.open(encoding="utf-8", newline="") as handle:
            rows = {row["question_id"]: row for row in csv.DictReader(handle)}
        for question_id in ("Q-B02-001", "Q-B02-002", "Q-B02-004"):
            self.assertEqual(rows[question_id]["status"], "OPEN")

    def test_b02_readiness_remains_55_and_mentions_p11(self):
        with MODULE_STATUS.open(encoding="utf-8", newline="") as handle:
            rows = {row["module_id"]: row for row in csv.DictReader(handle)}
        self.assertEqual(rows["B02"]["readiness_percent"], "55")
        self.assertIn("B02-P11", rows["B02"]["gate_note"])

    def test_document_freezes_non_equivalence_boundaries(self):
        text = DOC.read_text(encoding="utf-8")
        self.assertIn("SOURCE CODE EXISTS != SELECTED CODESET IS EXHAUSTIVE", text)
        self.assertIn("PINNED STRUCTURE != PROVEN SOURCE-NATIVE LEAF PARTITION", text)
        self.assertIn("COUNT GAP OBSERVED != GAP MECHANISM PROVEN", text)
        self.assertIn("88 977", text)
        self.assertIn("6 294", text)
        self.assertIn("B02 readiness változatlanul **55%**", text)


if __name__ == "__main__":
    unittest.main()
