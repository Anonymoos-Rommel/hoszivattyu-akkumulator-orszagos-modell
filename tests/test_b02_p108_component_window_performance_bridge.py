import csv
import unittest
from pathlib import Path

from modules.B02.component_window_performance_bridge import (
    AFFECTED_OPENING_REFERENCE_DEFICIT,
    AFFECTED_OPENING_REFERENCE_SATISFIED,
    COVERAGE_RESIDUAL,
    FINAL_CALC_PATH,
    PRIMARY_NEXT_RESIDUAL,
    PRODUCT_DOP_PATH,
    RESOLVED_BLOCKER,
    WHOLE_DWELLING_WINDOW_REFERENCE_SATISFIED,
    KehopWindowPerformanceCandidate,
    assess_kehop_window_performance,
    p108_state,
    semantic_boundaries,
)
from modules.B06.realized_completion_gate import (
    OBS,
    RealizedCompletionEvidence,
)


ROOT = Path(__file__).resolve().parents[1]
ROUTES = ROOT / "data" / "processed" / "b02" / "p108_component_window_performance_routes.csv"
REG = ROOT / "registry" / "b02_p108_component_window_performance_bridge.csv"
SOURCES = ROOT / "registry" / "sources.csv"
QUESTIONS = ROOT / "registry" / "open_questions.csv"
MODULES = ROOT / "registry" / "module_status.csv"
READINESS = ROOT / "registry" / "retrofit_readiness.csv"
DOC = ROOT / "docs" / "source_packs" / "B02_P108_COMPONENT_WINDOW_PERFORMANCE_BRIDGE.md"


def rows(path, key=None):
    with path.open(encoding="utf-8", newline="") as handle:
        data = list(csv.DictReader(handle))
    if key is None:
        return data
    return {row[key]: row for row in data}


def completion(*, realized_scope=("WINDOW_REPLACEMENT", "WALL_INSULATION")):
    return RealizedCompletionEvidence(
        record_id="REC-1",
        intervention_id="INT-1",
        project_id="PRJ-1",
        site_link_id="SITE-1",
        completion_evidence_status=OBS,
        physical_completion_date="2026-05-01",
        final_het_date="2026-05-10",
        contract_scope_ids=("WINDOW_REPLACEMENT", "WALL_INSULATION"),
        realized_scope_ids=realized_scope,
        final_invoice_refs=("INV-1",),
        performance_confirmation_refs=("PERF-1",),
        final_het_refs=("HET-1",),
        final_energy_calculation_refs=("CALC-1",),
        verifier_id="VER-1",
        final_het_record_link="REC-1",
        final_het_site_link="SITE-1",
        physical_completion_declared=True,
        reproducible_repository_binding=True,
    )


class B02P108ComponentWindowPerformanceBridgeTests(unittest.TestCase):
    def test_final_calculation_path_qualifies_same_record_window_bridge(self):
        result = assess_kehop_window_performance(
            KehopWindowPerformanceCandidate(
                completion=completion(),
                window_scope_ids=("WINDOW_REPLACEMENT",),
                final_calc_replaced_window_u_values_w_m2k=(1.0, 1.1),
                final_calc_values_explicitly_linked_to_window_scope=True,
                full_dwelling_window_coverage=True,
            )
        )
        self.assertEqual(result.status, "QUALIFIED_COMPONENT_SPECIFIC_WINDOW_RECORD")
        self.assertEqual(result.performance_path, FINAL_CALC_PATH)
        self.assertEqual(
            result.affected_opening_state,
            AFFECTED_OPENING_REFERENCE_SATISFIED,
        )
        self.assertEqual(
            result.dwelling_window_state,
            WHOLE_DWELLING_WINDOW_REFERENCE_SATISFIED,
        )
        self.assertEqual(result.blockers, ())

    def test_installed_product_dop_path_qualifies_when_invoice_scope_linked(self):
        result = assess_kehop_window_performance(
            KehopWindowPerformanceCandidate(
                completion=completion(),
                window_scope_ids=("WINDOW_REPLACEMENT",),
                installed_product_refs=("DOP-A", "DOP-B"),
                installed_product_u_values_w_m2k=(1.05, 1.2),
                installed_product_refs_linked_to_final_invoice_and_window_scope=True,
            )
        )
        self.assertEqual(result.status, "QUALIFIED_COMPONENT_SPECIFIC_WINDOW_RECORD")
        self.assertEqual(result.performance_path, PRODUCT_DOP_PATH)
        self.assertEqual(
            result.affected_opening_state,
            AFFECTED_OPENING_REFERENCE_DEFICIT,
        )
        self.assertEqual(result.blockers, ())

    def test_final_het_or_unlinked_values_do_not_mint_component_bridge(self):
        result = assess_kehop_window_performance(
            KehopWindowPerformanceCandidate(
                completion=completion(),
                window_scope_ids=("WINDOW_REPLACEMENT",),
                final_calc_replaced_window_u_values_w_m2k=(1.0,),
                final_calc_values_explicitly_linked_to_window_scope=False,
                full_dwelling_window_coverage=True,
            )
        )
        self.assertEqual(result.status, "Q_COMPONENT_SPECIFIC_WINDOW_RECORD")
        self.assertIn(
            "FINAL_CALC_U_VALUES_NOT_LINKED_TO_REPLACED_WINDOW_SCOPE",
            result.blockers,
        )

    def test_catalogue_product_is_not_installed_product(self):
        result = assess_kehop_window_performance(
            KehopWindowPerformanceCandidate(
                completion=completion(),
                window_scope_ids=("WINDOW_REPLACEMENT",),
                installed_product_refs=("DOP-A",),
                installed_product_u_values_w_m2k=(1.0,),
                installed_product_refs_linked_to_final_invoice_and_window_scope=False,
                full_dwelling_window_coverage=True,
            )
        )
        self.assertEqual(result.status, "Q_COMPONENT_SPECIFIC_WINDOW_RECORD")
        self.assertIn(
            "INSTALLED_PRODUCT_NOT_LINKED_TO_FINAL_INVOICE_AND_WINDOW_SCOPE",
            result.blockers,
        )

    def test_realized_scope_must_contain_window_replacement(self):
        result = assess_kehop_window_performance(
            KehopWindowPerformanceCandidate(
                completion=completion(realized_scope=("WALL_INSULATION",)),
                window_scope_ids=("WINDOW_REPLACEMENT",),
                final_calc_replaced_window_u_values_w_m2k=(1.0,),
                final_calc_values_explicitly_linked_to_window_scope=True,
                full_dwelling_window_coverage=True,
            )
        )
        self.assertEqual(result.status, "Q_COMPONENT_SPECIFIC_WINDOW_RECORD")
        self.assertIn("WINDOW_SCOPE_NOT_PRESENT_IN_REALIZED_SCOPE", result.blockers)

    def test_replaced_opening_satisfaction_still_requires_whole_dwelling_coverage(self):
        result = assess_kehop_window_performance(
            KehopWindowPerformanceCandidate(
                completion=completion(),
                window_scope_ids=("WINDOW_REPLACEMENT",),
                final_calc_replaced_window_u_values_w_m2k=(1.0,),
                final_calc_values_explicitly_linked_to_window_scope=True,
            )
        )
        self.assertEqual(result.status, "Q_COMPONENT_SPECIFIC_WINDOW_RECORD")
        self.assertIn(COVERAGE_RESIDUAL, result.blockers)

    def test_state_resolves_record_bridge_without_national_tightening(self):
        state = p108_state()
        self.assertEqual(state["resolved_blocker"], RESOLVED_BLOCKER)
        self.assertEqual(state["primary_residual"], PRIMARY_NEXT_RESIDUAL)
        self.assertFalse(state["kehop_completed_window_technical_cohort_identified"])
        self.assertFalse(state["kehop_ekr_overlap_identified"])
        self.assertFalse(state["p108_numeric_national_action_tightening"])
        self.assertAlmostEqual(
            state["p102_structural_calibrated_retrofit_floor_lower_share"],
            0.8278610299446981,
        )
        self.assertAlmostEqual(state["hp_only_share_upper"], 0.17213897005530188)

    def test_registry_sources_and_routes_are_frozen(self):
        routes = rows(ROUTES, "route_id")
        self.assertEqual(
            routes["B02-P108-R01"]["status"],
            "QUALIFIED_RECORD_LEVEL_COMPONENT_BRIDGE",
        )
        self.assertEqual(
            routes["B02-P108-R02"]["status"],
            "QUALIFIED_ALTERNATIVE_RECORD_LEVEL_COMPONENT_BRIDGE",
        )

        reg = rows(REG, "item_id")
        self.assertEqual(
            reg["B02-P108-U05"]["status"],
            "RESOLVED_RECORD_LEVEL",
        )
        self.assertEqual(
            reg["B02-P108-U06"]["residual_gap"],
            PRIMARY_NEXT_RESIDUAL,
        )

        sources = rows(SOURCES, "source_id")
        self.assertIn("SRC-B02-KTI-TERMEKINFO-2026", sources)
        self.assertIn(
            "P108 component-specific bridge authority",
            sources["SRC-B06-HU-KEHOP-417-COMPLETION-2025"]["notes"],
        )

        q = rows(QUESTIONS, "question_id")["Q-B02-004"]
        self.assertEqual(q["status"], "OPEN")
        self.assertIn("B02-P108", q["notes"])
        self.assertIn(PRIMARY_NEXT_RESIDUAL, q["notes"])

        module = rows(MODULES, "module_id")["B02"]
        self.assertEqual(module["readiness_percent"], "55")
        self.assertIn("B02-P108", module["gate_note"])

        peak = rows(READINESS, "component_id")["PEAK_LOAD_EFFECT"]
        self.assertEqual(peak["readiness_percent"], "50")
        self.assertIn("B02-P108", peak["notes"])

    def test_semantic_boundaries_and_document_are_frozen(self):
        for boundary in (
            "PROGRAMME_WINDOW_ELIGIBILITY_IS_NOT_REALIZED_WINDOW_REPLACEMENT",
            "FINAL_HET_ONLY_IS_NOT_REALIZED_WINDOW_SCOPE",
            "PRODUCT_CATALOGUE_ENTRY_IS_NOT_INSTALLED_PRODUCT",
            "SAME_PROJECT_DOCUMENT_SET_IS_NOT_AUTOMATIC_COMPONENT_LINK",
            "REPLACED_OPENING_COMPLIANCE_IS_NOT_WHOLE_DWELLING_WINDOW_COMPLIANCE",
            "KEHOP_COMPLETED_PROJECT_IS_NOT_NON_EKR_PROJECT",
            "RECORD_LEVEL_BRIDGE_IS_NOT_NATIONAL_POPULATION_SURFACE",
        ):
            self.assertIn(boundary, semantic_boundaries())

        text = DOC.read_text(encoding="utf-8")
        for phrase in (
            "COMPONENT_SPECIFIC_WINDOW_REPLACEMENT_PERFORMANCE_BRIDGE_REQUIRED",
            "KEHOP_COMPLETED_WINDOW_PROJECT_TECHNICAL_COHORT_REQUIRED",
            "KEHOP COMPLETED PROJECT != NON-EKR PROJECT",
            "82.7861029945%",
            "17.2138970055%",
        ):
            self.assertIn(phrase, text)


if __name__ == "__main__":
    unittest.main()
