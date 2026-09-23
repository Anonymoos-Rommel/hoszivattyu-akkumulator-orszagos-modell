import csv
import unittest
from pathlib import Path

from modules.B02.kehop_programmonitoring_1103_aggregate_boundary import (
    PRIMARY_NEXT_RESIDUAL,
    SUPERSEDED_BLOCKER,
    ProgramMonitoringAggregateCandidate,
    assess_program_monitoring_aggregate,
    p113_state,
    semantic_boundaries,
)

ROOT = Path(__file__).resolve().parents[1]
SURFACE = ROOT / "data" / "processed" / "b02" / "p113_programmonitoring_1103_surface.csv"
CONTRACT = ROOT / "data" / "processed" / "b02" / "p113_programmonitoring_1103_contract.csv"
REG = ROOT / "registry" / "b02_p113_programmonitoring_1103_boundary.csv"
SOURCES = ROOT / "registry" / "sources.csv"
QUESTIONS = ROOT / "registry" / "open_questions.csv"
MODULES = ROOT / "registry" / "module_status.csv"
READINESS = ROOT / "registry" / "retrofit_readiness.csv"
DOC = ROOT / "docs" / "source_packs" / "B02_P113_PROGRAMMONITORING_1103_BOUNDARY.md"


def rows(path, key=None):
    with path.open(encoding="utf-8", newline="") as h:
        data = list(csv.DictReader(h))
    return {r[key]: r for r in data} if key else data


class P113Tests(unittest.TestCase):
    def test_complete_exact_1103_programme_aggregate_admitted(self):
        d = assess_program_monitoring_aggregate(
            ProgramMonitoringAggregateCandidate(
                declared_programmes=(
                    "KEHOP_PLUSZ_4_1_7_24",
                    "KEHOP_PLUSZ_4_1_8_24",
                ),
                cutoff_date="2026-09-23",
                metric_name="Energiahatékonysági intézkedés kategória",
                measure_category_code="1103",
                completed_project_count_all_measures=1000,
                completed_project_count_1103=400,
                source_generated=True,
                complete_for_declared_scope=True,
                aggregation_basis_description=(
                    "all completed projects in declared programme/cutoff scope"
                ),
            )
        )
        self.assertTrue(d.admitted)
        self.assertEqual(d.blockers, ())
        self.assertIn(
            "1103_PROGRAMME_AGGREGATE_DOES_NOT_SUPPLY_TECHNICAL_U_DISTRIBUTION",
            d.warnings,
        )

    def test_wrong_metric_or_incomplete_scope_rejected(self):
        d = assess_program_monitoring_aggregate(
            ProgramMonitoringAggregateCandidate(
                declared_programmes=("KEHOP_PLUSZ_4_1_7_24",),
                cutoff_date="2026-09-23",
                metric_name="RCO18",
                measure_category_code="1103",
                completed_project_count_all_measures=10,
                completed_project_count_1103=4,
                source_generated=True,
                complete_for_declared_scope=False,
                aggregation_basis_description="partial",
            )
        )
        self.assertFalse(d.admitted)
        self.assertIn("EXACT_KEHOP_MEASURE_CATEGORY_METRIC_REQUIRED", d.blockers)
        self.assertIn("COMPLETE_DECLARED_SCOPE_REQUIRED", d.blockers)

    def test_state_narrows_to_1103_inclusion_or_institutional_readback(self):
        s = p113_state()
        self.assertEqual(s["superseded_blocker"], SUPERSEDED_BLOCKER)
        self.assertEqual(s["primary_residual"], PRIMARY_NEXT_RESIDUAL)
        self.assertTrue(
            s["programmonitoring_cross_project_aggregation_semantics_proven"]
        )
        self.assertTrue(s["source_generated_aggregate_product_class_qualified"])
        self.assertFalse(s["kehop_1103_in_programmonitoring_inclusion_proven"])
        self.assertFalse(s["current_institutional_1103_aggregate_observed"])
        self.assertFalse(s["p113_numeric_national_action_tightening"])
        self.assertAlmostEqual(s["hp_only_share_upper"], 0.17213897005530188)

    def test_surfaces_contract_registry_and_sources(self):
        surface = rows(SURFACE, "surface_id")
        self.assertEqual(
            surface["B02-P113-S01"]["status"],
            "QUALIFIED_CROSS_PROJECT_AGGREGATION_LAYER",
        )
        self.assertEqual(
            surface["B02-P113-S03"]["status"],
            "NOT_PROVEN_FOR_1103",
        )
        self.assertEqual(
            surface["B02-P113-S04"]["status"],
            "PRIMARY_NEXT_ACQUISITION",
        )

        contract = rows(CONTRACT, "field_id")
        self.assertEqual(
            contract["B02-P113-C03"]["status"],
            "REQUIRED_FOR_1103_AGGREGATE",
        )
        self.assertEqual(
            contract["B02-P113-C08"]["status"],
            "REQUIRED_FOR_COMPLETE_AGGREGATE",
        )

        reg = rows(REG, "item_id")
        self.assertEqual(
            reg["B02-P113-U01"]["status"],
            "QUALIFIED_CROSS_PROJECT_AGGREGATION_LAYER",
        )
        self.assertEqual(
            reg["B02-P113-U05"]["residual_gap"],
            PRIMARY_NEXT_RESIDUAL,
        )

        sources = rows(SOURCES, "source_id")
        self.assertIn("SRC-B02-FAIR-PROGRAMMONITORING-GLOSSARY-2026", sources)
        self.assertIn("SRC-B02-FAIR-MONITORING-REPORT-EXPORT-HELP-2026", sources)

        q = rows(QUESTIONS, "question_id")["Q-B02-004"]
        self.assertIn("B02-P113", q["notes"])
        self.assertIn(PRIMARY_NEXT_RESIDUAL, q["notes"])

        module = rows(MODULES, "module_id")["B02"]
        self.assertEqual(module["readiness_percent"], "55")
        self.assertIn("B02-P113", module["gate_note"])

        peak = rows(READINESS, "component_id")["PEAK_LOAD_EFFECT"]
        self.assertEqual(peak["readiness_percent"], "50")
        self.assertIn("B02-P113", peak["notes"])

    def test_boundaries_and_doc(self):
        for b in (
            "PROGRAMMONITORING_AGGREGATES_PROJECT_RESULTS_IS_NOT_ALL_FIELDS_AGGREGATED",
            "PROGRAMMONITORING_LAYER_EXISTS_IS_NOT_1103_INCLUDED",
            "SOURCE_GENERATED_AGGREGATE_CLASS_EXISTS_IS_NOT_CURRENT_1103_AGGREGATE_OBSERVED",
            "PROGRAMME_AGGREGATE_IS_NOT_TECHNICAL_U_DISTRIBUTION",
            "PROGRAMME_1103_COUNT_IS_NOT_NON_EKR_1103_COUNT",
        ):
            self.assertIn(b, semantic_boundaries())

        text = DOC.read_text(encoding="utf-8")
        for phrase in (
            "Programmonitoring",
            "aggregates the results of projects",
            "KEHOP_417_418_PROGRAMMONITORING_1103_INCLUSION_OR_INSTITUTIONAL_EXPORT_READBACK_REQUIRED",
            "82.7861029945%",
            "17.2138970055%",
        ):
            self.assertIn(phrase, text)


if __name__ == "__main__":
    unittest.main()
