import csv
import unittest
from pathlib import Path

from modules.B02.calibrated_linkage_admission import (
    CalibratedLinkageModelInputs,
    assess_calibrated_linkage_model,
)
from modules.B02.emitter_marginal_reconciliation import (
    HISTORICAL_MULTI_PRIOR_SCENARIOS,
    PRIMARY_HEATING_GAS_CONVECTOR_SHARE,
    build_calibrated_emitter_linkage,
    reconcile_gas_convector_margin,
)


ROOT = Path(__file__).resolve().parents[1]
WBL = ROOT / "data" / "processed" / "b02" / "ksh_wbl_joint_cells_2022.csv"
ADMISSION = ROOT / "registry" / "b02_calibrated_linkage_admission.csv"
CONTROLS = ROOT / "registry" / "b02_current_heating_device_controls.csv"
PRIORS = ROOT / "registry" / "b02_emitter_structural_prior_controls.csv"
ARCHETYPE_GATE = ROOT / "registry" / "b02_archetype_admission_gate.csv"
DOC = ROOT / "docs" / "source_packs" / "B02_P30_EMITTER_MARGINAL_RECONCILIATION.md"

EXPECTED_BLOCKERS = (
    "NO_JOSEPH_APPROVAL",
    "NO_VALIDATION_METRICS",
    "UNCONTROLLED_INDEPENDENCE_ASSUMPTION",
)


class B02P30EmitterMarginalReconciliationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.model_rows, cls.summary = build_calibrated_emitter_linkage(WBL)

    @staticmethod
    def _admission_row() -> dict[str, str]:
        with ADMISSION.open(encoding="utf-8", newline="") as handle:
            rows = {row["claim_id"]: row for row in csv.DictReader(handle)}
        return rows["CALIBRATED_GAS_CONVECTOR_EMITTER_LINKAGE_P30"]

    def test_strict_room_gas_domain_is_proven_infeasible(self):
        result = reconcile_gas_convector_margin(WBL)
        self.assertEqual(result.occupied_dwellings, 4_008_541)
        self.assertEqual(result.wbl_gas_heating_dwellings, 2_496_034)
        self.assertEqual(result.wbl_room_gas_dwellings, 693_075)
        self.assertEqual(result.blocker, "ROOM_GAS_DOMAIN_TOO_SMALL")
        self.assertFalse(result.marginal_reconciled)
        self.assertGreater(result.room_gas_probability, 1.0)

    def test_calibrated_structural_scenarios_reconcile_primary_margin_exactly(self):
        summary = self.summary
        self.assertEqual(summary.row_count, 116_452)
        self.assertEqual(summary.occupied_dwellings, 4_008_541)
        self.assertEqual(summary.gas_heating_dwellings, 2_496_034)
        self.assertEqual(summary.target_primary_convector_share, PRIMARY_HEATING_GAS_CONVECTOR_SHARE)
        self.assertEqual(
            {scenario.scenario_id for scenario in summary.scenarios},
            set(HISTORICAL_MULTI_PRIOR_SCENARIOS),
        )
        self.assertLessEqual(summary.maximum_absolute_marginal_residual, 1e-5)
        for scenario in summary.scenarios:
            self.assertAlmostEqual(
                scenario.calibrated_expected_dwellings,
                scenario.target_expected_dwellings,
                places=5,
            )
            self.assertGreaterEqual(scenario.minimum_probability, 0.0)
            self.assertLessEqual(scenario.maximum_probability, 1.0)
        print(
            "P30_CALIBRATED "
            f"target_share={summary.target_primary_convector_share:.12f} "
            f"target_dwellings={summary.scenarios[0].target_expected_dwellings:.12f} "
            f"max_residual={summary.maximum_absolute_marginal_residual:.12g} "
            + " ".join(
                f"{scenario.scenario_id}:shift={scenario.logit_shift:.12f},"
                f"pmax={scenario.maximum_probability:.12f}"
                for scenario in summary.scenarios
            )
        )
        self.assertEqual(len(self.model_rows), 116_452)

    def test_non_gas_cells_have_zero_convector_probability_in_every_scenario(self):
        for row in self.model_rows:
            if not row["gas_present"]:
                for scenario_id in HISTORICAL_MULTI_PRIOR_SCENARIOS:
                    self.assertEqual(row[f"probability__{scenario_id}"], 0.0)

    def test_p30_successor_closes_only_marginal_reconciliation(self):
        row = self._admission_row()
        self.assertEqual(row["marginal_reconciliation"], "yes")
        self.assertEqual(row["validation_metrics"], "no")
        self.assertEqual(row["independence_assumption_controlled"], "no")
        self.assertEqual(row["approval_status"], "NOT_APPROVED")
        self.assertEqual(row["output_evidence_status"], "ASS")
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

    def test_primary_control_is_distinct_from_conditional_4061_control(self):
        with CONTROLS.open(encoding="utf-8", newline="") as handle:
            rows = {row["control_id"]: row for row in csv.DictReader(handle)}
        conditional = rows["B02-P25-C03"]
        primary = rows["B02-P30-C01"]
        self.assertEqual(conditional["value_percent"], "40.61")
        self.assertEqual(conditional["survey_universe"], "GAS_HEATING_HOUSEHOLDS")
        self.assertEqual(primary["value_percent"], "23.3")
        self.assertEqual(primary["survey_universe"], "FULL_SAMPLE_PRIMARY_HEATING_SYSTEM")
        self.assertEqual(primary["admission_effect"], "CALIBRATION_MARGIN_ONLY")

    def test_historical_priors_are_never_current_stock_authority(self):
        with PRIORS.open(encoding="utf-8", newline="") as handle:
            rows = list(csv.DictReader(handle))
        self.assertEqual(len(rows), 4)
        self.assertEqual({row["canonical_use"] for row in rows}, {"ASS_STRUCTURAL_PRIOR_ONLY"})
        self.assertEqual({row["current_stock_authority"] for row in rows}, {"NO"})
        panel = next(row for row in rows if row["prior_id"] == "B02-P30-PRIOR-MULTI-PANEL")
        self.assertEqual(panel["gas_convector_share_percent"], "0.0")
        self.assertIn("explicit derived zero", panel["notes"])

    def test_technical_readiness_is_not_uplifted(self):
        with ARCHETYPE_GATE.open(encoding="utf-8", newline="") as handle:
            rows = {row["claim_id"]: row for row in csv.DictReader(handle)}
        technical = rows["TECHNICAL_READINESS_ARCHETYPE"]
        self.assertEqual(technical["current_status"], "Q")
        self.assertEqual(
            technical["current_blockers"],
            "NO_CURRENT_HEAT_EMITTER_EVIDENCE;NO_CURRENT_DESIGN_TEMPERATURE_EVIDENCE",
        )

    def test_document_preserves_hard_boundaries(self):
        text = DOC.read_text(encoding="utf-8")
        for phrase in (
            "40.61% CONDITIONAL GAS-DEVICE SHARE != 23.3% PRIMARY-HEATING STOCK SHARE",
            "HEATING MODE != EMITTER",
            "HISTORICAL STRUCTURAL PRIOR != CURRENT STOCK OBSERVATION",
            "EXACT MARGINAL RECONCILIATION != VALIDATION",
            "EXACT MARGINAL RECONCILIATION != INDEPENDENCE CONTROL",
            "CALIBRATED ASS SURFACE != TECHNICAL READINESS AUTHORITY",
        ):
            self.assertIn(phrase, text)

    def test_no_emitter_surface_is_materialized_or_promoted(self):
        self.assertFalse(
            (ROOT / "data" / "processed" / "b02" / "b02_gas_convector_emitter_assignment_2022.csv").exists()
        )


if __name__ == "__main__":
    unittest.main()
