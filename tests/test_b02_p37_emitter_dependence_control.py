import csv
import unittest
from pathlib import Path

from modules.B02.calibrated_linkage_admission import (
    CalibratedLinkageModelInputs,
    assess_calibrated_linkage_model,
)
from modules.B02.emitter_dependence_control import (
    EmitterDependenceControlInputs,
    assess_emitter_dependence_control,
)


ROOT = Path(__file__).resolve().parents[1]
ADMISSION = ROOT / "registry" / "b02_calibrated_linkage_admission.csv"
EVIDENCE = ROOT / "registry" / "b02_p37_emitter_dependence_control.csv"
ARCHETYPE_GATE = ROOT / "registry" / "b02_archetype_admission_gate.csv"
DOC = ROOT / "docs" / "source_packs" / "B02_P37_EMITTER_DEPENDENCE_CONTROL.md"

EXPECTED_ADMISSION_BLOCKERS = (
    "NO_JOSEPH_APPROVAL",
    "NO_VALIDATION_METRICS",
)


class B02P37EmitterDependenceControlTests(unittest.TestCase):
    @staticmethod
    def _evidence_rows() -> dict[str, dict[str, str]]:
        with EVIDENCE.open(encoding="utf-8", newline="") as handle:
            return {row["finding_id"]: row for row in csv.DictReader(handle)}

    @staticmethod
    def _admission_row() -> dict[str, str]:
        with ADMISSION.open(encoding="utf-8", newline="") as handle:
            rows = {row["claim_id"]: row for row in csv.DictReader(handle)}
        return rows["CALIBRATED_GAS_CONVECTOR_EMITTER_LINKAGE_P37"]

    def test_exact_reference_only_policy_is_preserved(self):
        rows = self._evidence_rows()
        self.assertEqual(len(rows), 5)
        for row in rows.values():
            self.assertEqual(row["repo_binary_policy"], "REFERENCE_ONLY_NO_BINARY")
            self.assertTrue(row["external_url"].startswith("https://"))
            self.assertTrue(row["exact_locator"].strip())

    def test_same_household_record_contains_building_type_and_primary_gas_convector(self):
        rows = self._evidence_rows()
        q11 = rows["B02-P37-F02"]
        q19 = rows["B02-P37-F03"]
        self.assertEqual(q11["control_role"], "SAME_RECORD_BUILDING_TYPE_VARIABLE")
        self.assertEqual(q19["control_role"], "SAME_RECORD_PRIMARY_EMITTER_VARIABLE")
        self.assertEqual(q11["same_record_joint"], "YES")
        self.assertEqual(q19["same_record_joint"], "YES")
        self.assertIn("Q11", q11["exact_locator"])
        self.assertIn("Q19", q19["exact_locator"])
        self.assertIn("gázkonvektor", q19["source_native_fact"])

    def test_survey_has_building_type_weight_control(self):
        row = self._evidence_rows()["B02-P37-F01"]
        self.assertEqual(row["weighted_by_building_type"], "YES")
        self.assertIn("1013", row["source_native_fact"])
        self.assertIn("region", row["source_native_fact"])
        self.assertIn("building type", row["source_native_fact"])

    def test_current_observed_joint_is_published_without_fabricating_cells(self):
        row = self._evidence_rows()["B02-P37-F04"]
        self.assertEqual(row["observed_joint_published"], "YES")
        self.assertEqual(row["exact_numeric_joint_cells_public"], "NO")
        self.assertEqual(
            row["control_effect"],
            "REPLACES_INDEPENDENT_MARGIN_ASSUMPTION_WITH_OBSERVED_JOINT_AUTHORITY",
        )
        self.assertEqual(row["blockers"], "NO_EXACT_NUMERIC_JOINT_CELLS_PUBLIC")
        self.assertIn("Figure 6", row["exact_locator"])

    def test_full_detailed_database_is_an_existing_exact_joint_recovery_route(self):
        row = self._evidence_rows()["B02-P37-F05"]
        self.assertEqual(row["control_role"], "EXACT_JOINT_RECOVERY_ROUTE")
        self.assertEqual(row["same_record_joint"], "YES")
        self.assertIn("complete detailed survey database", row["source_native_fact"])
        self.assertEqual(row["blockers"], "NO_PUBLIC_RAW_MICRODATA_DOWNLOAD")

    def test_dependence_control_closes_without_claiming_numeric_joint_execution(self):
        decision = assess_emitter_dependence_control(
            EmitterDependenceControlInputs(
                control_id="B02-P37-TARKI-REKK-SAME-RECORD-JOINT",
                survey_source_id="SRC-B02-TARKI-REKK-HOUSEHOLD-ENERGY-SURVEY-2022",
                joint_publication_source_id="SRC-B02-FEANTSA-CSOKNYAI-HEAT-TRANSITION-2024",
                reference_period="2022",
                building_type_variable="Q11",
                emitter_variable="Q19",
                target_emitter_code="4 = gázkonvektor",
                same_household_record=True,
                weighted_by_building_type=True,
                observed_joint_published=True,
                silent_cross_product_forbidden=True,
                historical_prior_override_forbidden=True,
                exact_numeric_joint_cells_available=False,
            )
        )
        self.assertTrue(decision.independence_assumption_controlled)
        self.assertEqual(decision.control_status, "CONTROLLED")
        self.assertEqual(decision.control_blockers, ())
        self.assertEqual(decision.numeric_execution_status, "NOT_EXECUTABLE")
        self.assertEqual(decision.numeric_execution_blockers, ("NO_EXACT_NUMERIC_JOINT_CELLS",))

    def test_silent_cross_product_or_historical_override_fails_control(self):
        common = dict(
            control_id="B02-P37-TARKI-REKK-SAME-RECORD-JOINT",
            survey_source_id="SRC-B02-TARKI-REKK-HOUSEHOLD-ENERGY-SURVEY-2022",
            joint_publication_source_id="SRC-B02-FEANTSA-CSOKNYAI-HEAT-TRANSITION-2024",
            reference_period="2022",
            building_type_variable="Q11",
            emitter_variable="Q19",
            target_emitter_code="4 = gázkonvektor",
            same_household_record=True,
            weighted_by_building_type=True,
            observed_joint_published=True,
            exact_numeric_joint_cells_available=False,
        )
        cross_product = assess_emitter_dependence_control(
            EmitterDependenceControlInputs(
                **common,
                silent_cross_product_forbidden=False,
                historical_prior_override_forbidden=True,
            )
        )
        prior_override = assess_emitter_dependence_control(
            EmitterDependenceControlInputs(
                **common,
                silent_cross_product_forbidden=True,
                historical_prior_override_forbidden=False,
            )
        )
        self.assertIn("SILENT_CROSS_PRODUCT_NOT_FORBIDDEN", cross_product.control_blockers)
        self.assertIn(
            "HISTORICAL_PRIOR_CAN_OVERRIDE_CURRENT_JOINT",
            prior_override.control_blockers,
        )
        self.assertFalse(cross_product.independence_assumption_controlled)
        self.assertFalse(prior_override.independence_assumption_controlled)

    def test_p37_successor_closes_only_uncontrolled_independence_blocker(self):
        row = self._admission_row()
        self.assertEqual(row["approval_status"], "NOT_APPROVED")
        self.assertEqual(row["validation_metrics"], "no")
        self.assertEqual(row["marginal_reconciliation"], "yes")
        self.assertEqual(row["uncertainty_method"], "yes")
        self.assertEqual(row["uncertainty_propagation"], "yes")
        self.assertEqual(row["independence_assumption_controlled"], "yes")
        self.assertEqual(row["output_evidence_status"], "ASS")
        self.assertEqual(row["current_status"], "Q")
        self.assertEqual(tuple(row["blockers"].split(";")), EXPECTED_ADMISSION_BLOCKERS)

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
        self.assertEqual(decision.blockers, EXPECTED_ADMISSION_BLOCKERS)
        self.assertNotIn("UNCONTROLLED_INDEPENDENCE_ASSUMPTION", decision.blockers)

    def test_technical_readiness_remains_unchanged(self):
        with ARCHETYPE_GATE.open(encoding="utf-8", newline="") as handle:
            rows = {row["claim_id"]: row for row in csv.DictReader(handle)}
        row = rows["TECHNICAL_READINESS_ARCHETYPE"]
        self.assertEqual(row["current_status"], "Q")
        self.assertEqual(
            row["current_blockers"],
            "NO_CURRENT_HEAT_EMITTER_EVIDENCE;NO_CURRENT_DESIGN_TEMPERATURE_EVIDENCE",
        )

    def test_source_pack_locks_fail_closed_boundaries(self):
        text = DOC.read_text(encoding="utf-8")
        required = (
            "SAME-RECORD Q11 × Q19 JOINT = DEPENDENCE AUTHORITY",
            "CURRENT OBSERVED BUILDING-TYPE × PRIMARY-HEAT-GENERATOR JOINT != INDEPENDENT-MARGINAL ASSUMPTION",
            "INDEPENDENCE CONTROL != EXACT NUMERIC JOINT CELLS",
            "HISTORICAL STRUCTURAL PRIOR != CURRENT DEPENDENCE AUTHORITY",
            "UNCONTROLLED_INDEPENDENCE_ASSUMPTION = CLOSED",
            "NO_JOSEPH_APPROVAL",
            "NO_VALIDATION_METRICS",
            "B02 readiness remains `55%`",
            "REFERENCED SOURCE DOCUMENT BYTES MUST NOT ENTER THE PUBLIC REPOSITORY",
        )
        for marker in required:
            self.assertIn(marker, text)

    def test_no_emitter_surface_or_external_binary_is_materialized(self):
        self.assertFalse(
            (ROOT / "data" / "processed" / "b02" / "b02_gas_convector_emitter_assignment_2022.csv").exists()
        )
        for path in ROOT.rglob("*"):
            if path.is_file() and "B02_P37" in path.name:
                self.assertIn(path.suffix, {".md"})


if __name__ == "__main__":
    unittest.main()
