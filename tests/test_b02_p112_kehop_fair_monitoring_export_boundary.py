import csv
import unittest
from pathlib import Path

from modules.B02.kehop_fair_monitoring_export_boundary import (
    PARAMETERIZATION_RESIDUAL,
    PRIMARY_NEXT_RESIDUAL,
    SUPERSEDED_BLOCKER,
    ProjectMonitoringExportCandidate,
    assess_project_monitoring_export,
    p112_state,
    semantic_boundaries,
)

ROOT = Path(__file__).resolve().parents[1]
SURFACE = ROOT / "data" / "processed" / "b02" / "p112_fair_monitoring_export_surface.csv"
CONTRACT = ROOT / "data" / "processed" / "b02" / "p112_fair_monitoring_export_contract.csv"
REG = ROOT / "registry" / "b02_p112_fair_monitoring_export_boundary.csv"
SOURCES = ROOT / "registry" / "sources.csv"
QUESTIONS = ROOT / "registry" / "open_questions.csv"
MODULES = ROOT / "registry" / "module_status.csv"
READINESS = ROOT / "registry" / "retrofit_readiness.csv"
DOC = ROOT / "docs" / "source_packs" / "B02_P112_FAIR_MONITORING_EXPORT_BOUNDARY.md"


def rows(path, key=None):
    with path.open(encoding="utf-8", newline="") as h:
        data = list(csv.DictReader(h))
    return {r[key]: r for r in data} if key else data


class P112Tests(unittest.TestCase):
    def test_project_level_source_export_admitted(self):
        d = assess_project_monitoring_export(
            ProjectMonitoringExportCandidate(
                project_id="KEHOP_PLUSZ-4.1.7-24-000001",
                programme_code="KEHOP_PLUSZ_4_1_7_24",
                monitoring_name="Energiahatékonysági intézkedés kategória",
                monitoring_type="SZAKMAI_MUTATO",
                fact_value="1103",
                report_type="ZARO_SZAKMAI_BESZAMOLO",
                source_generated_export=True,
                export_bound_to_project_context=True,
            )
        )
        self.assertTrue(d.admitted)
        self.assertEqual(d.blockers, ())
        self.assertIn(
            "SINGLE_PROJECT_EXPORT_DOES_NOT_PROVE_COMPLETE_PROGRAMME_COHORT",
            d.warnings,
        )
        self.assertIn(
            "GENERIC_EXPORT_DOES_NOT_BY_ITSELF_PROVE_1103_PARAMETERIZATION",
            d.warnings,
        )

    def test_unbound_or_non_source_export_rejected(self):
        d = assess_project_monitoring_export(
            ProjectMonitoringExportCandidate(
                project_id="P-1",
                programme_code="KEHOP_PLUSZ_4_1_8_24",
                monitoring_name="x",
                monitoring_type="x",
                fact_value="1103",
                report_type="ZARO_SZAKMAI_BESZAMOLO",
                source_generated_export=False,
                export_bound_to_project_context=False,
            )
        )
        self.assertFalse(d.admitted)
        self.assertIn("FAIR_SOURCE_GENERATED_EXPORT_REQUIRED", d.blockers)
        self.assertIn("PROJECT_CONTEXT_BINDING_REQUIRED", d.blockers)

    def test_state_narrows_to_cross_project_bulk_acquisition(self):
        s = p112_state()
        self.assertEqual(s["superseded_blocker"], SUPERSEDED_BLOCKER)
        self.assertEqual(s["primary_residual"], PRIMARY_NEXT_RESIDUAL)
        self.assertEqual(s["parameterization_residual"], PARAMETERIZATION_RESIDUAL)
        self.assertTrue(s["project_level_monitoring_list_export_proven"])
        self.assertTrue(s["fact_date_and_fact_value_export_proven"])
        self.assertTrue(s["closing_report_type_supported"])
        self.assertFalse(s["exact_kehop_1103_parameterization_readback_observed"])
        self.assertFalse(s["cross_project_complete_417_418_export_proven"])
        self.assertFalse(s["p112_numeric_national_action_tightening"])
        self.assertAlmostEqual(s["hp_only_share_upper"], 0.17213897005530188)

    def test_surfaces_contract_registry_and_sources(self):
        surface = rows(SURFACE, "surface_id")
        self.assertEqual(
            surface["B02-P112-S01"]["status"],
            "QUALIFIED_PROJECT_LEVEL_EXPORT_ROUTE",
        )
        self.assertEqual(
            surface["B02-P112-S03"]["status"],
            "NOT_EXTERNALLY_OBSERVED",
        )
        self.assertEqual(
            surface["B02-P112-S04"]["status"],
            "PRIMARY_NEXT_ACQUISITION",
        )

        contract = rows(CONTRACT, "field_id")
        self.assertEqual(
            contract["B02-P112-C03"]["status"],
            "REQUIRED_FOR_PROJECT_EXPORT",
        )
        self.assertEqual(
            contract["B02-P112-C09"]["status"],
            "REQUIRED_FOR_COMPLETE_COHORT",
        )

        reg = rows(REG, "item_id")
        self.assertEqual(
            reg["B02-P112-U01"]["status"],
            "QUALIFIED_PROJECT_LEVEL_EXPORT_ROUTE",
        )
        self.assertEqual(
            reg["B02-P112-U05"]["residual_gap"],
            PRIMARY_NEXT_RESIDUAL,
        )

        sources = rows(SOURCES, "source_id")
        self.assertIn("SRC-B02-FAIR-MONITORING-REPORT-EXPORT-HELP-2026", sources)
        self.assertIn("SRC-B06-HU-KEHOP-417-COMPLETION-2025", sources)
        self.assertIn("SRC-B02-HU-KEHOP-418-COMPLETION-INDICATORS-2025", sources)

        q = rows(QUESTIONS, "question_id")["Q-B02-004"]
        self.assertIn("B02-P112", q["notes"])
        self.assertIn(PRIMARY_NEXT_RESIDUAL, q["notes"])

        module = rows(MODULES, "module_id")["B02"]
        self.assertEqual(module["readiness_percent"], "55")
        self.assertIn("B02-P112", module["gate_note"])

        peak = rows(READINESS, "component_id")["PEAK_LOAD_EFFECT"]
        self.assertEqual(peak["readiness_percent"], "50")
        self.assertIn("B02-P112", peak["notes"])

    def test_boundaries_and_doc(self):
        for b in (
            "PROJECT_LEVEL_MONITORING_EXPORT_IS_NOT_CROSS_PROJECT_COMPLETE_COHORT",
            "GENERIC_MONITORING_EXPORT_CAPABILITY_IS_NOT_OBSERVED_KEHOP_1103_EXPORT",
            "PROFESSIONAL_METRIC_SCHEMA_IS_NOT_PUBLIC_FIELD_AVAILABILITY",
            "FACT_VALUE_EXPORT_IS_NOT_TECHNICAL_U_DISTRIBUTION",
            "1103_COMPLETION_FACT_IS_NOT_EKR_HEM_CLASSIFICATION",
        ):
            self.assertIn(b, semantic_boundaries())

        text = DOC.read_text(encoding="utf-8")
        for phrase in (
            "CSV",
            "Excel",
            "Záró szakmai beszámoló",
            "FAIR_IH_CROSS_PROJECT_KEHOP_1103_MONITORING_EXPORT_OR_SOURCE_AGGREGATE_REQUIRED",
            "82.7861029945%",
            "17.2138970055%",
        ):
            self.assertIn(phrase, text)


if __name__ == "__main__":
    unittest.main()
