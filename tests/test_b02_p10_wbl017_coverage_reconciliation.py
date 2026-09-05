import csv
import unittest
from pathlib import Path

from modules.B02.wbl017_coverage_reconciliation import (
    Q,
    RECONCILED,
    CoverageInputs,
    assess_coverage,
)


ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "registry" / "b02_wbl017_coverage_reconciliation.csv"
COVERAGE = ROOT / "data" / "processed" / "b02" / "ksh_wbl_joint_cell_coverage_2022.csv"
P1H_DOC = ROOT / "docs" / "source_packs" / "P1H_B02_KSH_WBL_JOINT_CELLS.md"
DOC = ROOT / "docs" / "source_packs" / "B02_P10_WBL017_COVERAGE_RECONCILIATION.md"
OPEN_QUESTIONS = ROOT / "registry" / "open_questions.csv"
MODULE_STATUS = ROOT / "registry" / "module_status.csv"


class B02P10WBL017CoverageReconciliationTests(unittest.TestCase):
    def test_current_wbl017_population_gap_fails_closed(self):
        decision = assess_coverage(
            CoverageInputs(
                reference_count=4_008_541,
                projection_count=3_919_564,
                reference_evidence="DER",
                projection_evidence="DER",
            )
        )
        self.assertEqual(decision.status, Q)
        self.assertEqual(decision.difference_count, 88_977)
        self.assertEqual(decision.blockers, ("INCOMPLETE_POPULATION_COVERAGE",))

    def test_current_hosziv1_gap_fails_closed(self):
        decision = assess_coverage(
            CoverageInputs(
                reference_count=67_853,
                projection_count=61_559,
                reference_evidence="OBS",
                projection_evidence="DER",
            )
        )
        self.assertEqual(decision.status, Q)
        self.assertEqual(decision.difference_count, 6_294)
        self.assertEqual(decision.blockers, ("INCOMPLETE_POPULATION_COVERAGE",))

    def test_equal_real_counts_only_reconcile_counts(self):
        decision = assess_coverage(
            CoverageInputs(
                reference_count=100,
                projection_count=100,
                reference_evidence="OBS",
                projection_evidence="DER",
            )
        )
        self.assertEqual(decision.status, RECONCILED)
        self.assertEqual(decision.difference_count, 0)
        self.assertEqual(decision.blockers, ())

    def test_projection_above_reference_fails_closed(self):
        decision = assess_coverage(
            CoverageInputs(
                reference_count=99,
                projection_count=100,
                reference_evidence="OBS",
                projection_evidence="OBS",
            )
        )
        self.assertEqual(decision.status, Q)
        self.assertEqual(decision.difference_count, -1)
        self.assertEqual(decision.blockers, ("PROJECTION_EXCEEDS_REFERENCE",))

    def test_non_real_evidence_cannot_reconcile(self):
        decision = assess_coverage(
            CoverageInputs(
                reference_count=100,
                projection_count=100,
                reference_evidence="ASS",
                projection_evidence="DER",
            )
        )
        self.assertEqual(decision.status, Q)
        self.assertEqual(decision.blockers, ("REFERENCE_EVIDENCE_NOT_REAL",))

    def test_invalid_counts_are_rejected(self):
        for reference, projection in ((-1, 0), (1, -1), (True, 1), (1, 1.0)):
            with self.subTest(reference=reference, projection=projection):
                with self.assertRaises(ValueError):
                    assess_coverage(
                        CoverageInputs(
                            reference_count=reference,
                            projection_count=projection,
                            reference_evidence="OBS",
                            projection_evidence="DER",
                        )
                    )

    def test_machine_registry_preserves_exact_gaps_and_q_status(self):
        with REGISTRY.open(encoding="utf-8", newline="") as handle:
            rows = {row["claim_id"]: row for row in csv.DictReader(handle)}

        population = rows["WBL017_OCCUPIED_POPULATION_COVERAGE"]
        self.assertEqual(population["reference_count"], "4008541")
        self.assertEqual(population["projection_count"], "3919564")
        self.assertEqual(population["difference_count"], "88977")
        self.assertEqual(population["current_status"], "Q")

        hp = rows["WBL017_HOSZIV1_COVERAGE"]
        self.assertEqual(hp["reference_count"], "67853")
        self.assertEqual(hp["projection_count"], "61559")
        self.assertEqual(hp["difference_count"], "6294")
        self.assertEqual(hp["current_status"], "Q")

    def test_existing_coverage_inventory_reconciles_population_inputs(self):
        with COVERAGE.open(encoding="utf-8", newline="") as handle:
            rows = {row["projection_id"]: row for row in csv.DictReader(handle)}
        self.assertEqual(
            rows["WBL011_ENVELOPE"]["returned_numeric_dwelling_sum"],
            "4008541",
        )
        self.assertEqual(
            rows["WBL011_HEATING_FUEL"]["returned_numeric_dwelling_sum"],
            "4008541",
        )
        self.assertEqual(
            rows["WBL017_HEAT_PUMP_BASELINE"]["returned_numeric_dwelling_sum"],
            "3919564",
        )

    def test_p1h_preserves_separate_hosziv_controls(self):
        text = P1H_DOC.read_text(encoding="utf-8")
        self.assertIn("`HOSZIV=1`: 61 559 lakás", text)
        self.assertIn("67 853", text)
        self.assertIn("88 977", text)
        self.assertIn("nem kerül nullának", text)

    def test_open_questions_remain_open(self):
        with OPEN_QUESTIONS.open(encoding="utf-8", newline="") as handle:
            rows = {row["question_id"]: row for row in csv.DictReader(handle)}
        for question_id in ("Q-B02-001", "Q-B02-002", "Q-B02-004"):
            self.assertEqual(rows[question_id]["status"], "OPEN")

    def test_b02_readiness_remains_55(self):
        with MODULE_STATUS.open(encoding="utf-8", newline="") as handle:
            rows = {row["module_id"]: row for row in csv.DictReader(handle)}
        self.assertEqual(rows["B02"]["readiness_percent"], "55")
        self.assertIn("B02-P10", rows["B02"]["gate_note"])

    def test_document_freezes_non_equivalence_boundaries(self):
        text = DOC.read_text(encoding="utf-8")
        self.assertIn(
            "RETURNED WBL017 LEAF PROJECTION != COMPLETE OCCUPIED-DWELLING UNIVERSE",
            text,
        )
        self.assertIn("MISSING / UNRETURNED != ZERO != HOSZIV=0 != EXCLUDED", text)
        self.assertIn("COUNT RECONCILIATION != CELL-LEVEL JOINT AUTHORITY != TECHNICAL ELIGIBILITY", text)
        self.assertIn("B02 readiness változatlanul **55%**", text)


if __name__ == "__main__":
    unittest.main()
