import csv
import unittest
from pathlib import Path

from modules.B02.ekr1103_public_admin_cohort_gate import (
    Ekr1103CohortCandidate,
    HISTORICAL_ACCEPTED_PROJECTS,
    HISTORICAL_BUILDING_STRUCTURE_SAVING_GJ,
    HISTORICAL_ENTITLEMENTS,
    HISTORICAL_MEASURE_CATEGORIES,
    OVERALL_WINDOW_RESIDUAL,
    P105_STATUS,
    POST_EXTRACT_RESIDUAL,
    PRIMARY_NEXT_RESIDUAL,
    SUPERSEDED_SUB_BLOCKER,
    admin_aggregation_capability,
    admit_ekr1103_cohort,
    p105_state,
    public_hem_discovery_surface,
    semantic_boundaries,
)


ROOT = Path(__file__).resolve().parents[1]
FIELD_MATRIX = ROOT / "data" / "processed" / "b02" / "p105_hem_public_admin_field_matrix.csv"
HISTORICAL = ROOT / "data" / "processed" / "b02" / "p105_historical_admin_aggregation_evidence.csv"
ROUTES = ROOT / "data" / "processed" / "b02" / "p105_ekr1103_acquisition_routes.csv"
REG = ROOT / "registry" / "b02_p105_ekr1103_technical_cohort.csv"
SOURCES = ROOT / "registry" / "sources.csv"
QUESTIONS = ROOT / "registry" / "open_questions.csv"
MODULES = ROOT / "registry" / "module_status.csv"
READINESS = ROOT / "registry" / "retrofit_readiness.csv"
DOC = ROOT / "docs" / "source_packs" / "B02_P105_EKR1103_TECHNICAL_COHORT.md"


def rows(path, key=None):
    with path.open(encoding="utf-8", newline="") as handle:
        data = list(csv.DictReader(handle))
    if key is None:
        return data
    return {row[key]: row for row in data}


class B02P105Ekr1103TechnicalCohortTests(unittest.TestCase):
    def test_public_hem_surface_is_identifier_bound_not_1103_enumeration(self):
        x = public_hem_discovery_surface()
        self.assertTrue(x.known_identifier_required)
        self.assertTrue(x.public_saving_type_label_available)
        self.assertFalse(x.public_saving_type_is_proven_measure_code)
        self.assertTrue(x.public_global_hem_count_available)
        self.assertFalse(x.public_measure_code_filter_proven)
        self.assertFalse(x.public_bulk_enumeration_proven)
        self.assertFalse(x.public_technical_u_available)
        self.assertEqual(x.residual, PRIMARY_NEXT_RESIDUAL)

        matrix = rows(FIELD_MATRIX, "field_id")
        self.assertEqual(
            matrix["B02-P105-F04"]["status"],
            "SEMANTICALLY_INSUFFICIENT_FOR_1103_DISCOVERY",
        )
        self.assertEqual(
            matrix["B02-P105-F06"]["status"],
            "QUALIFIED_GLOBAL_AGGREGATE_ONLY",
        )

    def test_admin_schema_and_historical_monitoring_prove_aggregation_capability_only(self):
        x = admin_aggregation_capability()
        self.assertTrue(x.administrative_measure_type_available)
        self.assertTrue(x.administrative_technical_context_available)
        self.assertEqual(x.historical_measure_category_count, 39)
        self.assertTrue(x.historical_code_level_aggregation_proven)
        self.assertFalse(x.current_1103_extract_available)
        self.assertEqual(x.residual, PRIMARY_NEXT_RESIDUAL)

        historical = rows(HISTORICAL, "evidence_id")
        self.assertAlmostEqual(
            float(historical["B02-P105-H01"]["value"]),
            HISTORICAL_ACCEPTED_PROJECTS,
        )
        self.assertAlmostEqual(
            float(historical["B02-P105-H02"]["value"]),
            HISTORICAL_ENTITLEMENTS,
        )
        self.assertAlmostEqual(
            float(historical["B02-P105-H03"]["value"]),
            HISTORICAL_MEASURE_CATEGORIES,
        )
        self.assertAlmostEqual(
            float(historical["B02-P105-H04"]["value"]),
            HISTORICAL_BUILDING_STRUCTURE_SAVING_GJ,
        )
        for row in historical.values():
            self.assertIn(
                "MEKH_EKR_1103_ADMIN_EXTRACT_OR_PUBLISHED_AGGREGATE_REQUIRED",
                row["residual"],
            )

    def test_current_public_routes_do_not_mint_1103_count(self):
        routes = rows(ROUTES, "route_id")
        self.assertEqual(
            routes["B02-P105-A01"]["status"],
            "IDENTIFIER_BOUND_ONLY",
        )
        self.assertEqual(
            routes["B02-P105-A02"]["status"],
            "GLOBAL_ONLY_NOT_1103",
        )
        self.assertEqual(
            routes["B02-P105-A03"]["status"],
            "MARKET_PRODUCT_AGGREGATE_NOT_MEASURE_CODE",
        )
        self.assertEqual(
            routes["B02-P105-A04"]["status"],
            "TECHNICALLY_CAPABLE_ADMIN_ROUTE",
        )
        self.assertEqual(
            routes["B02-P105-A05"]["status"],
            "SUBMISSION_AUTOMATION_ONLY_NOT_EXTRACTION_AUTHORITY",
        )

    def test_future_1103_cohort_admission_is_fail_closed(self):
        rejected = admit_ekr1103_cohort(
            Ekr1103CohortCandidate(
                reference_period_current=False,
                exact_measure_code_1103=True,
                cohort_enumeration_complete_for_declared_scope=False,
                source_population_scope_declared=False,
                technical_u_coverage_declared=False,
                full_window_coverage_field_declared=False,
            )
        )
        self.assertFalse(rejected.admitted)
        self.assertIn("CURRENT_REFERENCE_PERIOD_REQUIRED", rejected.blockers)
        self.assertIn(
            "COMPLETE_1103_ENUMERATION_FOR_DECLARED_SCOPE_REQUIRED",
            rejected.blockers,
        )
        self.assertIn("SOURCE_POPULATION_SCOPE_REQUIRED", rejected.blockers)

        admitted = admit_ekr1103_cohort(
            Ekr1103CohortCandidate(
                reference_period_current=True,
                exact_measure_code_1103=True,
                cohort_enumeration_complete_for_declared_scope=True,
                source_population_scope_declared=True,
                technical_u_coverage_declared=False,
                full_window_coverage_field_declared=False,
            )
        )
        self.assertTrue(admitted.admitted)
        self.assertEqual(
            admitted.status,
            "QUALIFIED_CURRENT_1103_COHORT_FOR_POPULATION_BINDING",
        )
        self.assertIn(
            "TECHNICAL_U_COVERAGE_REMAINS_REQUIRED_FOR_COMPLIANCE_DISTRIBUTION",
            admitted.warnings,
        )
        self.assertIn(
            "FULL_WINDOW_COVERAGE_REMAINS_REQUIRED_FOR_WHOLE_DWELLING_PROMOTION",
            admitted.warnings,
        )

        wrong_code = admit_ekr1103_cohort(
            Ekr1103CohortCandidate(
                reference_period_current=True,
                exact_measure_code_1103=False,
                cohort_enumeration_complete_for_declared_scope=True,
                source_population_scope_declared=True,
                technical_u_coverage_declared=True,
                full_window_coverage_field_declared=True,
            )
        )
        self.assertFalse(wrong_code.admitted)
        self.assertIn("EXACT_MEASURE_CODE_1103_REQUIRED", wrong_code.blockers)

    def test_p105_narrows_access_blocker_without_numeric_tightening(self):
        state = p105_state()
        self.assertEqual(state["status"], P105_STATUS)
        self.assertEqual(state["superseded_sub_blocker"], SUPERSEDED_SUB_BLOCKER)
        self.assertEqual(state["primary_residual"], PRIMARY_NEXT_RESIDUAL)
        self.assertEqual(state["overall_window_residual"], OVERALL_WINDOW_RESIDUAL)
        self.assertEqual(state["post_extract_residual"], POST_EXTRACT_RESIDUAL)
        self.assertFalse(state["current_public_1103_count_identified"])
        self.assertFalse(
            state["current_public_1103_technical_u_distribution_identified"]
        )
        self.assertFalse(state["p105_numeric_national_action_tightening"])
        self.assertAlmostEqual(
            state["p102_structural_calibrated_retrofit_floor_lower_share"],
            0.8278610299446981,
        )
        self.assertEqual(state["hp_only_share_lower"], 0.0)
        self.assertAlmostEqual(
            state["hp_only_share_upper"],
            0.17213897005530188,
        )

    def test_registry_sources_and_project_status_are_exact(self):
        reg = rows(REG, "item_id")
        self.assertEqual(
            reg["B02-P105-U09"]["status"],
            "NARROWED_TO_EXACT_ACCESS_ROUTE",
        )
        self.assertEqual(
            reg["B02-P105-U09"]["residual_gap"],
            PRIMARY_NEXT_RESIDUAL,
        )
        self.assertAlmostEqual(
            float(reg["B02-P105-U10"]["lower_bound"]),
            0.8278610299446981,
        )

        sources = rows(SOURCES, "source_id")
        for source_id in (
            "SRC-B02-MEKH-HEM-MODULE-HANDBOOK",
            "SRC-B02-MEKH-17-2020-HEM-DATA-CONTENT",
            "SRC-B02-HUPX-EKR-MONITORING-2022Q3",
            "SRC-B02-CEEGEX-EKR-MARKET-2026",
            "SRC-B02-MEKH-EKR-USER-GUIDE-2025",
        ):
            self.assertIn(source_id, sources)

        self.assertIn(
            "P105 public-discovery boundary",
            sources["SRC-B02-MEKH-HEM-MODULE-HANDBOOK"]["notes"],
        )
        self.assertIn(
            "P105 historical administrative aggregation proof",
            sources["SRC-B02-HUPX-EKR-MONITORING-2022Q3"]["notes"],
        )

        q = rows(QUESTIONS, "question_id")["Q-B02-004"]
        self.assertEqual(q["status"], "OPEN")
        self.assertIn("B02-P105", q["notes"])
        self.assertIn(PRIMARY_NEXT_RESIDUAL, q["notes"])

        module = rows(MODULES, "module_id")["B02"]
        self.assertEqual(module["readiness_percent"], "55")
        self.assertIn("B02-P105", module["gate_note"])

        peak = rows(READINESS, "component_id")["PEAK_LOAD_EFFECT"]
        self.assertEqual(peak["readiness_percent"], "50")
        self.assertIn("B02-P105", peak["notes"])

    def test_semantic_boundaries_and_document_are_frozen(self):
        for boundary in (
            "PUBLIC_SAVING_TYPE_IS_NOT_PROVEN_MEASURE_CODE",
            "KNOWN_HEM_ID_LOOKUP_IS_NOT_COHORT_ENUMERATION",
            "GLOBAL_HEM_COUNT_IS_NOT_EKR_1103_COUNT",
            "CEEGEX_MARKET_PRODUCT_IS_NOT_MEASURE_CODE_1103",
            "HISTORICAL_CODE_AGGREGATION_IS_NOT_CURRENT_1103_AGGREGATE",
            "ADMIN_SCHEMA_CAPABILITY_IS_NOT_PUBLIC_DATA_AVAILABILITY",
            "EKR_1103_COHORT_IS_NOT_ALL_REPLACED_WINDOW_STOCK",
        ):
            self.assertIn(boundary, semantic_boundaries())

        text = DOC.read_text(encoding="utf-8")
        for phrase in (
            "39",
            "541",
            "597",
            "MEKH_EKR_1103_ADMIN_EXTRACT_OR_PUBLISHED_AGGREGATE_REQUIRED",
            "EKR_1103_COHORT_POPULATION_BINDING_REQUIRED",
            "82.7861029945%",
            "17.2138970055%",
            "**B02 remains 55%**",
        ):
            self.assertIn(phrase, text)


if __name__ == "__main__":
    unittest.main()
