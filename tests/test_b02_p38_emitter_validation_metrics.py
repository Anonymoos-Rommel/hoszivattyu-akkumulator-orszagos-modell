import csv
import unittest
from pathlib import Path

from modules.B02.calibrated_linkage_admission import (
    CalibratedLinkageModelInputs,
    assess_calibrated_linkage_model,
)
from modules.B02.emitter_validation_metrics import (
    CLEAR_PASS,
    CONSISTENT_WITH_REPORTED_BOUND,
    DIAGNOSTIC_ONLY,
    FAIL,
    build_independent_emitter_validation,
)


ROOT = Path(__file__).resolve().parents[1]
WBL = ROOT / "data" / "processed" / "b02" / "ksh_wbl_joint_cells_2022.csv"
REGISTRY = ROOT / "registry" / "b02_p38_emitter_validation_metrics.csv"
ADMISSION = ROOT / "registry" / "b02_calibrated_linkage_admission.csv"
ARCHETYPE_GATE = ROOT / "registry" / "b02_archetype_admission_gate.csv"
DOC = ROOT / "docs" / "source_packs" / "B02_P38_INDEPENDENT_EMITTER_VALIDATION_METRICS.md"


class B02P38EmitterValidationMetricsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.summary = build_independent_emitter_validation(WBL)

    @staticmethod
    def _metric_rows():
        with REGISTRY.open(encoding="utf-8", newline="") as handle:
            return {row["metric_id"]: row for row in csv.DictReader(handle)}

    @staticmethod
    def _admission_row():
        with ADMISSION.open(encoding="utf-8", newline="") as handle:
            rows = {row["claim_id"]: row for row in csv.DictReader(handle)}
        return rows["CALIBRATED_GAS_CONVECTOR_EMITTER_LINKAGE_P38"]

    def test_exact_wbl_denominators_and_budapest_outputs(self):
        summary = self.summary
        self.assertEqual(summary.national_occupied_dwellings, 4_008_541)
        self.assertEqual(summary.budapest_occupied_dwellings, 800_338)
        metrics = {metric.scenario_id: metric for metric in summary.scenario_metrics}
        self.assertAlmostEqual(metrics["MULTI_PANEL_LOWER_BOUND"].model_share, 0.099937732, places=8)
        self.assertAlmostEqual(metrics["MULTI_SMALL_4_9"].model_share, 0.228165175, places=8)
        self.assertAlmostEqual(metrics["MULTI_LARGE_OTHER_10_PLUS"].model_share, 0.262239407, places=8)

    def test_independent_holdout_is_discriminatory_and_rejects_exactly_one_scenario(self):
        metrics = {metric.scenario_id: metric for metric in self.summary.scenario_metrics}
        self.assertEqual(metrics["MULTI_PANEL_LOWER_BOUND"].decision, CLEAR_PASS)
        self.assertEqual(metrics["MULTI_SMALL_4_9"].decision, CONSISTENT_WITH_REPORTED_BOUND)
        self.assertEqual(metrics["MULTI_LARGE_OTHER_10_PLUS"].decision, FAIL)
        self.assertEqual(
            self.summary.retained_scenarios,
            ("MULTI_PANEL_LOWER_BOUND", "MULTI_SMALL_4_9"),
        )
        self.assertEqual(self.summary.rejected_scenarios, ("MULTI_LARGE_OTHER_10_PLUS",))
        self.assertTrue(self.summary.validation_metrics_present)

    def test_reported_precision_is_not_replaced_by_posthoc_tolerance(self):
        for metric in self.summary.scenario_metrics:
            self.assertAlmostEqual(metric.reported_broad_share, 0.23)
            self.assertAlmostEqual(metric.lower_rounding_edge, 0.225)
            self.assertAlmostEqual(metric.upper_rounding_edge, 0.235)
        text = DOC.read_text(encoding="utf-8")
        self.assertIn("No threshold was selected after looking at the scenario results.", text)
        self.assertIn("This is **not** a confidence interval", text)

    def test_national_industry_estimate_is_diagnostic_only(self):
        metric = self.summary.national_diagnostic
        self.assertAlmostEqual(metric.model_expected_dwellings, 933_990.053, places=3)
        self.assertEqual(metric.external_approx_properties, 800_000.0)
        self.assertAlmostEqual(metric.absolute_difference, 133_990.053, places=3)
        self.assertAlmostEqual(metric.relative_difference_to_external, 0.16748756625, places=8)
        self.assertEqual(metric.decision, DIAGNOSTIC_ONLY)

    def test_registry_preserves_source_semantics_and_reference_only_policy(self):
        rows = self._metric_rows()
        self.assertEqual(len(rows), 5)
        for row in rows.values():
            self.assertEqual(row["repo_binary_policy"], "REFERENCE_ONLY_NO_BINARY")
            self.assertTrue(row["external_url"].startswith("https://"))
            self.assertTrue(row["exact_locator"].strip())
        self.assertEqual(rows["B02-P38-M01"]["metric_type"], "LOGICAL_BROAD_CATEGORY_UPPER_BOUND")
        self.assertEqual(rows["B02-P38-M03"]["decision"], "FAIL")
        self.assertIn("convector or stove", rows["B02-P38-M01"]["exact_locator"])
        self.assertEqual(rows["B02-P38-M04"]["binding"], "NO")
        self.assertEqual(rows["B02-P38-M04"]["decision"], "DIAGNOSTIC_ONLY")

    def test_cares_is_independent_structural_holdout_without_digitized_chart_values(self):
        row = self._metric_rows()["B02-P38-M05"]
        self.assertEqual(row["metric_type"], "INDEPENDENT_STRUCTURAL_HOLDOUT")
        self.assertEqual(row["decision"], "STRUCTURAL_HOLDOUT_ONLY")
        self.assertEqual(row["binding"], "NO")
        self.assertEqual(row["model_value"], "")
        self.assertIn("2009 owner households", row["exact_locator"])
        self.assertIn("No stacked-bar segment is digitized or fabricated", row["notes"])

    def test_p38_successor_closes_validation_metrics_blocker_only(self):
        row = self._admission_row()
        self.assertEqual(row["approval_status"], "NOT_APPROVED")
        self.assertEqual(row["validation_metrics"], "yes")
        self.assertEqual(row["marginal_reconciliation"], "yes")
        self.assertEqual(row["uncertainty_method"], "yes")
        self.assertEqual(row["uncertainty_propagation"], "yes")
        self.assertEqual(row["independence_assumption_controlled"], "yes")
        self.assertEqual(row["output_evidence_status"], "ASS")
        self.assertEqual(row["current_status"], "Q")
        self.assertEqual(row["blockers"], "NO_JOSEPH_APPROVAL")

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
        self.assertEqual(decision.blockers, ("NO_JOSEPH_APPROVAL",))

    def test_validation_sources_are_outside_calibration_lineage(self):
        row = self._admission_row()
        calibration_sources = set(row["calibration_sources"].split(";"))
        self.assertNotIn("SRC-B02-DAIKIN-HU-HEATING-STOCK-2022", calibration_sources)
        self.assertNotIn("SRC-B02-BUDAPEST-CARES-HOUSEHOLD-SURVEY-2023", calibration_sources)
        text = DOC.read_text(encoding="utf-8")
        self.assertIn("CALIBRATION TARGET != VALIDATION METRIC", text)
        self.assertIn("INDEPENDENT HOLDOUT != REUSED CALIBRATION MARGIN", text)

    def test_technical_readiness_and_b02_readiness_do_not_uplift(self):
        with ARCHETYPE_GATE.open(encoding="utf-8", newline="") as handle:
            rows = {row["claim_id"]: row for row in csv.DictReader(handle)}
        technical = rows["TECHNICAL_READINESS_ARCHETYPE"]
        self.assertEqual(technical["current_status"], "Q")
        self.assertEqual(
            technical["current_blockers"],
            "NO_CURRENT_HEAT_EMITTER_EVIDENCE;NO_CURRENT_DESIGN_TEMPERATURE_EVIDENCE",
        )
        text = DOC.read_text(encoding="utf-8")
        self.assertIn("B02 readiness remains `55%`", text)
        self.assertIn("VALIDATED MODEL CANDIDATE != CURRENT EMITTER OBSERVATION", text)


if __name__ == "__main__":
    unittest.main()
