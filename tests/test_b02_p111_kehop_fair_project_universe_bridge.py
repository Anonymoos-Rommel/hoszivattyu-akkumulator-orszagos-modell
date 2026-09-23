import csv
import unittest
from pathlib import Path

from modules.B02.kehop_fair_project_universe_bridge import (
    PRIMARY_NEXT_RESIDUAL,
    SUPERSEDED_BLOCKER,
    FairProjectUniverseCandidate,
    assess_fair_project_universe,
    p111_state,
    semantic_boundaries,
)

ROOT = Path(__file__).resolve().parents[1]
SURFACE = ROOT / "data" / "processed" / "b02" / "p111_fair_project_universe_surface.csv"
CONTRACT = ROOT / "data" / "processed" / "b02" / "p111_fair_project_universe_contract.csv"
REG = ROOT / "registry" / "b02_p111_fair_project_universe_bridge.csv"
SOURCES = ROOT / "registry" / "sources.csv"
QUESTIONS = ROOT / "registry" / "open_questions.csv"
MODULES = ROOT / "registry" / "module_status.csv"
READINESS = ROOT / "registry" / "retrofit_readiness.csv"
DOC = ROOT / "docs" / "source_packs" / "B02_P111_FAIR_PROJECT_UNIVERSE_BRIDGE.md"


def rows(path, key=None):
    with path.open(encoding="utf-8", newline="") as h:
        data = list(csv.DictReader(h))
    return {r[key]: r for r in data} if key else data


class P111Tests(unittest.TestCase):
    def test_complete_source_generated_project_universe_admitted(self):
        d = assess_fair_project_universe(
            FairProjectUniverseCandidate(
                declared_programmes=(
                    "KEHOP_PLUSZ_4_1_7_24",
                    "KEHOP_PLUSZ_4_1_8_24",
                ),
                extract_refresh_date="2026-09-23",
                project_ids=("P-001", "P-002", "P-003"),
                source_generated_csv=True,
                enumeration_complete_for_declared_scope=True,
                source_scope_description=(
                    "FAIR supported-project CSV for declared programmes and cutoff"
                ),
            )
        )
        self.assertTrue(d.admitted)
        self.assertEqual(d.blockers, ())
        self.assertIn("PROJECT_UNIVERSE_DOES_NOT_CLASSIFY_1103", d.warnings)
        self.assertIn(
            "PROJECT_UNIVERSE_DOES_NOT_SUPPLY_TECHNICAL_U_DISTRIBUTION",
            d.warnings,
        )

    def test_duplicate_or_incomplete_universe_rejected(self):
        d = assess_fair_project_universe(
            FairProjectUniverseCandidate(
                declared_programmes=("KEHOP_PLUSZ_4_1_7_24",),
                extract_refresh_date="2026-09-23",
                project_ids=("P-001", "P-001"),
                source_generated_csv=True,
                enumeration_complete_for_declared_scope=False,
                source_scope_description="partial",
            )
        )
        self.assertFalse(d.admitted)
        self.assertIn("UNIQUE_PROJECT_IDS_REQUIRED", d.blockers)
        self.assertIn(
            "COMPLETE_ENUMERATION_FOR_DECLARED_SCOPE_REQUIRED",
            d.blockers,
        )

    def test_state_narrows_to_indicator_join_without_numeric_tightening(self):
        s = p111_state()
        self.assertEqual(s["superseded_blocker"], SUPERSEDED_BLOCKER)
        self.assertEqual(s["primary_residual"], PRIMARY_NEXT_RESIDUAL)
        self.assertTrue(s["machine_readable_project_universe_route_proven"])
        self.assertTrue(s["authenticated_csv_export_proven"])
        self.assertIsNone(s["szechenyi_terv_plusz_export_row_limit"])
        self.assertFalse(s["physical_completion_indicator_in_search_export_proven"])
        self.assertFalse(s["exact_1103_selector_in_search_export_proven"])
        self.assertFalse(s["p111_numeric_national_action_tightening"])
        self.assertAlmostEqual(s["hp_only_share_upper"], 0.17213897005530188)

    def test_surfaces_contract_registry_and_sources(self):
        surface = rows(SURFACE, "surface_id")
        self.assertEqual(
            surface["B02-P111-S01"]["status"],
            "QUALIFIED_MACHINE_READABLE_PROJECT_UNIVERSE_ROUTE",
        )
        self.assertEqual(
            surface["B02-P111-S02"]["status"],
            "NOT_PROVEN_IN_SEARCH_EXPORT",
        )
        self.assertEqual(
            surface["B02-P111-S04"]["status"],
            "QUALIFIED_PROGRAMME_SCALE_CONTROL_ONLY",
        )

        contract = rows(CONTRACT, "field_id")
        self.assertEqual(
            contract["B02-P111-C03"]["status"],
            "REQUIRED_FOR_PROJECT_UNIVERSE",
        )
        self.assertEqual(
            contract["B02-P111-C07"]["status"],
            "REQUIRED_TO_CLOSE_1103_COHORT",
        )

        reg = rows(REG, "item_id")
        self.assertEqual(
            reg["B02-P111-U01"]["status"],
            "QUALIFIED_MACHINE_READABLE_PROJECT_UNIVERSE_ROUTE",
        )
        self.assertEqual(
            reg["B02-P111-U05"]["residual_gap"],
            PRIMARY_NEXT_RESIDUAL,
        )

        sources = rows(SOURCES, "source_id")
        self.assertIn("SRC-B02-FAIR-SUPPORTED-PROJECT-SEARCH-HELP-2026", sources)
        self.assertIn("SRC-B02-HU-60-2014-FAIR-REGULATION", sources)
        self.assertIn("SRC-B02-MFB-OFP-PROGRAMME-SCALE-2026", sources)

        q = rows(QUESTIONS, "question_id")["Q-B02-004"]
        self.assertIn("B02-P111", q["notes"])
        self.assertIn(PRIMARY_NEXT_RESIDUAL, q["notes"])

        module = rows(MODULES, "module_id")["B02"]
        self.assertEqual(module["readiness_percent"], "55")
        self.assertIn("B02-P111", module["gate_note"])

        peak = rows(READINESS, "component_id")["PEAK_LOAD_EFFECT"]
        self.assertEqual(peak["readiness_percent"], "50")
        self.assertIn("B02-P111", peak["notes"])

    def test_boundaries_and_doc(self):
        for b in (
            "FAIR_PROJECT_CSV_IS_NOT_COMPLETION_INDICATOR_EXPORT",
            "PROJECT_METADATA_IS_NOT_MEASURE_CATEGORY_1103",
            "LOGIN_GATED_SEARCH_EXPORT_IS_NOT_INTERNAL_INDICATOR_EXPORT",
            "NEARLY_10000_EXPECTED_HOMES_IS_NOT_COMPLETED_PROJECT_COUNT",
            "PROJECT_UNIVERSE_ROUTE_IS_NOT_TECHNICAL_U_DISTRIBUTION",
        ):
            self.assertIn(b, semantic_boundaries())

        text = DOC.read_text(encoding="utf-8")
        for phrase in (
            "FAIR_IH_KEHOP_1103_COMPLETION_INDICATOR_JOIN_OR_SOURCE_AGGREGATE_REQUIRED",
            "no result-row limit",
            "daily",
            "82.7861029945%",
            "17.2138970055%",
        ):
            self.assertIn(phrase, text)


if __name__ == "__main__":
    unittest.main()
