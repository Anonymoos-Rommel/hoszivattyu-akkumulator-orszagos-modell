import csv
import unittest
from pathlib import Path

from modules.B02.calibrated_linkage_admission import (
    CalibratedLinkageModelInputs,
    assess_calibrated_linkage_model,
)
from modules.B02.emitter_linkage_uncertainty import (
    ESTIMATOR,
    METHOD_ID,
    PRIMARY_VARIANCE,
    PROPAGATION,
    assess_uncertainty_execution,
)

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "registry" / "b02_calibrated_linkage_admission.csv"
DOC = ROOT / "docs" / "source_packs" / "B02_P29_EMITTER_LINKAGE_UNCERTAINTY_METHOD.md"

EXPECTED_BLOCKERS = (
    "NO_JOSEPH_APPROVAL",
    "NO_VALIDATION_METRICS",
    "NO_MARGINAL_RECONCILIATION",
    "UNCONTROLLED_INDEPENDENCE_ASSUMPTION",
)


class B02P29EmitterUncertaintyMethodTests(unittest.TestCase):
    @staticmethod
    def _candidate() -> dict[str, str]:
        with REGISTRY.open(encoding="utf-8", newline="") as handle:
            rows = {row["claim_id"]: row for row in csv.DictReader(handle)}
        return rows["CALIBRATED_GAS_CONVECTOR_EMITTER_LINKAGE_P29"]

    def test_method_is_predeclared_and_design_aware(self):
        self.assertEqual(METHOD_ID, "B02-P29-DESIGN-AWARE-GAS-CONVECTOR-UNCERTAINTY")
        self.assertEqual(ESTIMATOR, "HAJEK_WEIGHTED_PROPORTION")
        self.assertIn("DESIGN_BASED", PRIMARY_VARIANCE)
        self.assertIn("MONTE_CARLO", PROPAGATION)

    def test_missing_design_inputs_do_not_fall_back_to_srs(self):
        decision = assess_uncertainty_execution(
            final_case_weights_available=True,
            design_variables_available=False,
            replicate_weights_available=False,
        )
        self.assertTrue(decision.method_defined)
        self.assertFalse(decision.executable)
        self.assertEqual(decision.blockers, ("NO_DESIGN_VARIANCE_INPUT",))

    def test_design_or_replicate_route_can_execute(self):
        for design, replicate in ((True, False), (False, True), (True, True)):
            decision = assess_uncertainty_execution(
                final_case_weights_available=True,
                design_variables_available=design,
                replicate_weights_available=replicate,
            )
            self.assertTrue(decision.executable)
            self.assertEqual(decision.blockers, ())

    def test_p29_successor_closes_only_uncertainty_method_blocker(self):
        row = self._candidate()
        self.assertEqual(row["uncertainty_method"], "yes")
        self.assertEqual(row["uncertainty_propagation"], "yes")
        self.assertEqual(row["current_status"], "Q")
        self.assertEqual(tuple(row["blockers"].split(";")), EXPECTED_BLOCKERS)

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

    def test_document_forbids_false_precision(self):
        text = DOC.read_text(encoding="utf-8")
        self.assertIn("FULL-SAMPLE 3.4% MOE != N=657 GAS-HEATING SUBGROUP UNCERTAINTY", text)
        self.assertIn("WEIGHTED SURVEY != SIMPLE RANDOM SAMPLE", text)
        self.assertIn("NO INTERVAL != ZERO UNCERTAINTY", text)


if __name__ == "__main__":
    unittest.main()
