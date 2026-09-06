import csv
import unittest
from pathlib import Path

from modules.B02.calibrated_linkage_admission import (
    CalibratedLinkageModelInputs,
    assess_calibrated_linkage_model,
)


ROOT = Path(__file__).resolve().parents[1]
ADMISSION = ROOT / "registry" / "b02_calibrated_linkage_admission.csv"
ARCHETYPE_GATE = ROOT / "registry" / "b02_archetype_admission_gate.csv"
DOC = ROOT / "docs" / "source_packs" / "B02_P39_P38_JOSEPH_APPROVAL.md"


class B02P39P38JosephApprovalTests(unittest.TestCase):
    @staticmethod
    def _rows():
        with ADMISSION.open(encoding="utf-8", newline="") as handle:
            return {row["claim_id"]: row for row in csv.DictReader(handle)}

    def test_p38_historical_preapproval_state_is_preserved(self):
        row = self._rows()["CALIBRATED_GAS_CONVECTOR_EMITTER_LINKAGE_P38"]
        self.assertEqual(row["approval_status"], "NOT_APPROVED")
        self.assertEqual(row["approval_authority"], "")
        self.assertEqual(row["current_status"], "Q")
        self.assertEqual(row["blockers"], "NO_JOSEPH_APPROVAL")

    def test_p39_records_explicit_joseph_approval_of_exact_p38_model(self):
        rows = self._rows()
        p38 = rows["CALIBRATED_GAS_CONVECTOR_EMITTER_LINKAGE_P38"]
        p39 = rows["CALIBRATED_GAS_CONVECTOR_EMITTER_LINKAGE_P39"]
        self.assertEqual(p39["current_model_id"], p38["current_model_id"])
        self.assertEqual(p39["approval_status"], "APPROVED")
        self.assertEqual(p39["approval_authority"], "JOSEPH")
        self.assertEqual(p39["calibration_sources"], p38["calibration_sources"])
        for field in (
            "reference_period_defined",
            "target_grain_wbl_compatible",
            "representativeness_diagnostics",
            "validation_metrics",
            "marginal_reconciliation",
            "uncertainty_method",
            "uncertainty_propagation",
            "independence_assumption_controlled",
        ):
            self.assertEqual(p39[field], "yes")
        self.assertEqual(p39["output_evidence_status"], "ASS")
        self.assertEqual(p39["current_status"], "QUALIFIED")
        self.assertEqual(p39["blockers"], "")

    def test_existing_admission_contract_reproduces_qualified_state(self):
        row = self._rows()["CALIBRATED_GAS_CONVECTOR_EMITTER_LINKAGE_P39"]
        decision = assess_calibrated_linkage_model(
            CalibratedLinkageModelInputs(
                model_id=row["current_model_id"],
                approval_status=row["approval_status"],
                approval_authority=row["approval_authority"],
                calibration_source_ids=tuple(row["calibration_sources"].split(";")),
                calibration_reference_period_defined=row["reference_period_defined"] == "yes",
                target_grain_wbl_compatible=row["target_grain_wbl_compatible"] == "yes",
                representativeness_diagnostics_present=row["representativeness_diagnostics"] == "yes",
                validation_metrics_present=row["validation_metrics"] == "yes",
                marginal_reconciliation_present=row["marginal_reconciliation"] == "yes",
                uncertainty_method_defined=row["uncertainty_method"] == "yes",
                uncertainty_propagation_required=row["uncertainty_propagation"] == "yes",
                independence_assumption_controlled=row["independence_assumption_controlled"] == "yes",
                output_evidence_status=row["output_evidence_status"],
            )
        )
        self.assertEqual(decision.status, "QUALIFIED")
        self.assertEqual(decision.blockers, ())

    def test_technical_readiness_is_not_uplifted_by_model_approval(self):
        with ARCHETYPE_GATE.open(encoding="utf-8", newline="") as handle:
            rows = {row["claim_id"]: row for row in csv.DictReader(handle)}
        technical = rows["TECHNICAL_READINESS_ARCHETYPE"]
        self.assertEqual(technical["current_status"], "Q")
        self.assertEqual(
            technical["current_blockers"],
            "NO_CURRENT_HEAT_EMITTER_EVIDENCE;NO_CURRENT_DESIGN_TEMPERATURE_EVIDENCE",
        )

    def test_source_pack_freezes_approval_and_non_observation_boundaries(self):
        text = DOC.read_text(encoding="utf-8")
        self.assertIn("2026-09-06 19:27 Europe/Budapest", text)
        self.assertIn("jóváhagyom a P38-at", text)
        self.assertIn("APPROVED / JOSEPH / QUALIFIED", text)
        self.assertIn("MODEL APPROVAL != CURRENT EMITTER OBSERVATION", text)
        self.assertIn("NO_CURRENT_HEAT_EMITTER_EVIDENCE", text)
        self.assertIn("NO_CURRENT_DESIGN_TEMPERATURE_EVIDENCE", text)
        self.assertIn("B02 technical readiness remains `55%`", text)


if __name__ == "__main__":
    unittest.main()
