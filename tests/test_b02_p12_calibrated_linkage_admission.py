import csv
import unittest
from pathlib import Path

from modules.B02.archetype_admission_gate import (
    CONTRACTED,
    Q,
    QUALIFIED,
    StockArchetypeInputs,
    assess_stock_archetype,
)
from modules.B02.calibrated_linkage_admission import (
    APPROVED,
    JOSEPH,
    CalibratedLinkageModelInputs,
    assess_calibrated_linkage_model,
)


ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "registry" / "b02_calibrated_linkage_admission.csv"
OPEN_QUESTIONS = ROOT / "registry" / "open_questions.csv"
MODULE_STATUS = ROOT / "registry" / "module_status.csv"
DOC = ROOT / "docs" / "source_packs" / "B02_P12_CALIBRATED_LINKAGE_ADMISSION.md"


def complete_model(**overrides):
    values = dict(
        model_id="MODEL-B02-LINKAGE-001",
        approval_status=APPROVED,
        approval_authority=JOSEPH,
        calibration_source_ids=("SRC-B02-CALIBRATION-001",),
        calibration_reference_period_defined=True,
        target_grain_wbl_compatible=True,
        representativeness_diagnostics_present=True,
        validation_metrics_present=True,
        marginal_reconciliation_present=True,
        uncertainty_method_defined=True,
        uncertainty_propagation_required=True,
        independence_assumption_controlled=True,
        output_evidence_status="MODELLED",
    )
    values.update(overrides)
    return CalibratedLinkageModelInputs(**values)


class B02P12CalibratedLinkageAdmissionTests(unittest.TestCase):
    def test_complete_explicit_model_can_qualify(self):
        decision = assess_calibrated_linkage_model(complete_model())
        self.assertEqual(decision.status, QUALIFIED)
        self.assertEqual(decision.blockers, ())

    def test_model_without_joseph_approval_fails_closed(self):
        decision = assess_calibrated_linkage_model(
            complete_model(approval_status="PROPOSED", approval_authority="RESEARCH")
        )
        self.assertEqual(decision.status, Q)
        self.assertIn("NO_JOSEPH_APPROVAL", decision.blockers)

    def test_observed_output_status_is_forbidden_for_model_output(self):
        decision = assess_calibrated_linkage_model(
            complete_model(output_evidence_status="OBS")
        )
        self.assertEqual(decision.status, Q)
        self.assertEqual(decision.blockers, ("MODEL_OUTPUT_EVIDENCE_INVALID",))

    def test_uncertainty_and_representativeness_are_mandatory(self):
        decision = assess_calibrated_linkage_model(
            complete_model(
                representativeness_diagnostics_present=False,
                uncertainty_method_defined=False,
                uncertainty_propagation_required=False,
            )
        )
        self.assertEqual(decision.status, Q)
        self.assertEqual(
            decision.blockers,
            (
                "NO_REPRESENTATIVENESS_DIAGNOSTICS",
                "NO_UNCERTAINTY_METHOD",
                "NO_UNCERTAINTY_PROPAGATION",
            ),
        )

    def test_model_status_tokens_do_not_self_authorize_p9(self):
        candidate = StockArchetypeInputs(
            schema_status=CONTRACTED,
            wbl_joint_complete=True,
            building_type_link_status="APPROVED_CALIBRATED_MODEL",
            primary_energy_link_status="MODELLED_LINKED",
        )
        decision = assess_stock_archetype(candidate)
        self.assertEqual(decision.status, Q)
        self.assertEqual(
            decision.blockers,
            (
                "CALIBRATED_BUILDING_TYPE_MODEL_NOT_ADMITTED",
                "CALIBRATED_PRIMARY_ENERGY_MODEL_NOT_ADMITTED",
            ),
        )

    def test_p9_accepts_model_tokens_only_after_separate_qualification(self):
        candidate = StockArchetypeInputs(
            schema_status=CONTRACTED,
            wbl_joint_complete=True,
            building_type_link_status="APPROVED_CALIBRATED_MODEL",
            primary_energy_link_status="MODELLED_LINKED",
            building_type_model_admission_status=QUALIFIED,
            primary_energy_model_admission_status=QUALIFIED,
        )
        decision = assess_stock_archetype(candidate)
        self.assertEqual(decision.status, QUALIFIED)
        self.assertEqual(decision.blockers, ())

    def test_current_registry_contains_no_approved_model(self):
        with REGISTRY.open(encoding="utf-8", newline="") as handle:
            rows = {row["claim_id"]: row for row in csv.DictReader(handle)}
        self.assertEqual(
            set(rows),
            {
                "CALIBRATED_BUILDING_TYPE_LINKAGE",
                "CALIBRATED_PRIMARY_ENERGY_LINKAGE",
            },
        )
        for row in rows.values():
            self.assertEqual(row["current_status"], "Q")
            self.assertEqual(row["approval_status"], "NOT_APPROVED")
            self.assertEqual(row["current_model_id"], "")

    def test_open_questions_and_readiness_remain_fail_closed(self):
        with OPEN_QUESTIONS.open(encoding="utf-8", newline="") as handle:
            rows = {row["question_id"]: row for row in csv.DictReader(handle)}
        for question_id in ("Q-B02-001", "Q-B02-002", "Q-B02-004"):
            self.assertEqual(rows[question_id]["status"], "OPEN")

        with MODULE_STATUS.open(encoding="utf-8", newline="") as handle:
            modules = {row["module_id"]: row for row in csv.DictReader(handle)}
        self.assertEqual(modules["B02"]["readiness_percent"], "55")

    def test_document_freezes_model_non_equivalence_boundaries(self):
        text = DOC.read_text(encoding="utf-8")
        self.assertIn("OBSERVED MARGINS != JOINT DISTRIBUTION != CALIBRATED LINKAGE MODEL", text)
        self.assertIn("MODEL STATUS TOKEN != MODEL APPROVAL", text)
        self.assertIn("CALIBRATION CONTROL != EVIDENCE PROMOTION", text)
        self.assertIn("MODEL OUTPUT != OBS", text)
        self.assertIn("B02 readiness: változatlanul **55%**", text)


if __name__ == "__main__":
    unittest.main()
