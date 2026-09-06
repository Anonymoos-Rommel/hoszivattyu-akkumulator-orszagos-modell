import csv
import unittest
from pathlib import Path

from modules.B02.calibrated_linkage_admission import (
    CalibratedLinkageModelInputs,
    assess_calibrated_linkage_model,
)


ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "registry" / "b02_calibrated_linkage_admission.csv"
P9 = ROOT / "registry" / "b02_archetype_admission_gate.csv"
DOC = ROOT / "docs" / "source_packs" / "B02_P27_CALIBRATED_EMITTER_LINKAGE_FEASIBILITY.md"

EXPECTED_BLOCKERS = (
    "NO_JOSEPH_APPROVAL",
    "NO_REPRESENTATIVENESS_DIAGNOSTICS",
    "NO_VALIDATION_METRICS",
    "NO_MARGINAL_RECONCILIATION",
    "NO_UNCERTAINTY_METHOD",
    "UNCONTROLLED_INDEPENDENCE_ASSUMPTION",
)


class B02P27CalibratedEmitterLinkageFeasibilityTests(unittest.TestCase):
    @staticmethod
    def _candidate() -> dict[str, str]:
        with REGISTRY.open(encoding="utf-8", newline="") as handle:
            rows = {row["claim_id"]: row for row in csv.DictReader(handle)}
        return rows["CALIBRATED_GAS_CONVECTOR_EMITTER_LINKAGE"]

    def test_candidate_is_registered_but_fail_closed(self):
        row = self._candidate()
        self.assertEqual(
            row["current_model_id"],
            "B02-P27-TARKI-REKK-GAS-CONVECTOR-WBL-LINKAGE-CANDIDATE",
        )
        self.assertEqual(row["linkage_target"], "HEAT_EMITTER")
        self.assertEqual(row["approval_status"], "NOT_APPROVED")
        self.assertEqual(row["approval_authority"], "")
        self.assertEqual(row["target_grain_wbl_compatible"], "yes")
        self.assertEqual(row["output_evidence_status"], "ASS")
        self.assertEqual(row["current_status"], "Q")
        self.assertEqual(tuple(row["blockers"].split(";")), EXPECTED_BLOCKERS)

    def test_existing_p12_gate_reproduces_exact_candidate_blockers(self):
        row = self._candidate()
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
        self.assertEqual(decision.status, "Q")
        self.assertEqual(decision.blockers, EXPECTED_BLOCKERS)

    def test_no_uniform_4061_broadcast_is_admitted(self):
        text = DOC.read_text(encoding="utf-8")
        self.assertIn("NUMERIC SURVEY CONTROL != WBL CELL ASSIGNMENT", text)
        self.assertIn("every gas WBL cell * 0.4061 -> gas-convector assignment", text)
        self.assertIn("NO EMITTER WBL ROW IS MATERIALIZED", text)
        self.assertIn("FULL-SAMPLE 3.4% MARGIN OF ERROR != N=657 CONDITIONAL SUBGROUP UNCERTAINTY", text)

    def test_p27_does_not_uplift_technical_readiness(self):
        with P9.open(encoding="utf-8", newline="") as handle:
            rows = {row["claim_id"]: row for row in csv.DictReader(handle)}
        technical = rows["TECHNICAL_READINESS_ARCHETYPE"]
        self.assertEqual(technical["current_status"], "Q")
        self.assertEqual(
            technical["current_blockers"],
            "NO_CURRENT_HEAT_EMITTER_EVIDENCE;NO_CURRENT_DESIGN_TEMPERATURE_EVIDENCE",
        )


if __name__ == "__main__":
    unittest.main()
