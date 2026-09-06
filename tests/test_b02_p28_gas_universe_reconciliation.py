import csv
import unittest
from pathlib import Path

from modules.B02.calibrated_linkage_admission import (
    CalibratedLinkageModelInputs,
    assess_calibrated_linkage_model,
)


ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "registry" / "b02_calibrated_linkage_admission.csv"
CONTROLS = ROOT / "registry" / "b02_tarki_rekk_gas_universe_controls.csv"
DOC = ROOT / "docs" / "source_packs" / "B02_P28_GAS_UNIVERSE_REPRESENTATIVENESS_RECONCILIATION.md"

EXPECTED_BLOCKERS = (
    "NO_JOSEPH_APPROVAL",
    "NO_VALIDATION_METRICS",
    "NO_MARGINAL_RECONCILIATION",
    "NO_UNCERTAINTY_METHOD",
    "UNCONTROLLED_INDEPENDENCE_ASSUMPTION",
)


class B02P28GasUniverseReconciliationTests(unittest.TestCase):
    @staticmethod
    def _candidate() -> dict[str, str]:
        with REGISTRY.open(encoding="utf-8", newline="") as handle:
            rows = {row["claim_id"]: row for row in csv.DictReader(handle)}
        return rows["CALIBRATED_GAS_CONVECTOR_EMITTER_LINKAGE_P28"]

    def test_successor_candidate_closes_representativeness_only(self):
        row = self._candidate()
        self.assertEqual(row["current_model_id"], "B02-P28-TARKI-REKK-GAS-CONVECTOR-WBL-LINKAGE-CANDIDATE")
        self.assertEqual(row["representativeness_diagnostics"], "yes")
        self.assertEqual(row["marginal_reconciliation"], "no")
        self.assertEqual(row["validation_metrics"], "no")
        self.assertEqual(row["uncertainty_method"], "no")
        self.assertEqual(row["independence_assumption_controlled"], "no")
        self.assertEqual(row["current_status"], "Q")
        self.assertEqual(tuple(row["blockers"].split(";")), EXPECTED_BLOCKERS)

    def test_existing_p12_gate_reproduces_reduced_blocker_set(self):
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

    def test_published_controls_are_pinned_without_emitter_overclaim(self):
        with CONTROLS.open(encoding="utf-8", newline="") as handle:
            rows = list(csv.DictReader(handle))
        by_id = {row["control_id"]: row for row in rows}
        self.assertEqual(by_id["P28-PRIMARY-GAS"]["weighted_share_pct"], "54.89")
        self.assertEqual(by_id["P28-SECONDARY-GAS"]["weighted_share_pct"], "6.98")
        self.assertEqual(by_id["P28-NO-GAS"]["weighted_share_pct"], "38.13")
        self.assertAlmostEqual(54.89 + 6.98 + 38.13, 100.0, places=9)
        self.assertTrue(all(row["evidence_status"] == "OBS" for row in rows))
        self.assertTrue(all("EMITTER" not in row["canonical_use"] for row in rows))

    def test_document_preserves_hard_boundaries(self):
        text = DOC.read_text(encoding="utf-8")
        self.assertIn("SURVEY REPRESENTATIVENESS DIAGNOSTIC != EMITTER CONDITIONAL DISTRIBUTION", text)
        self.assertIn("GAS-HEATING MARGINS != GAS-CONVECTOR MARGINS", text)
        self.assertIn("SOURCE-NATIVE GAS-UNIVERSE CONTROL != LOSSLESS WBL CROSSWALK", text)
        self.assertIn("REPRESENTATIVENESS PROVEN != LINKAGE VALIDATED", text)


if __name__ == "__main__":
    unittest.main()
