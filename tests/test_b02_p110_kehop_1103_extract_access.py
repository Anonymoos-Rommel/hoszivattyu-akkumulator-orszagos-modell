import csv
import unittest
from pathlib import Path

from modules.B02.kehop_1103_extract_access import (
    PRIMARY_NEXT_RESIDUAL,
    PREFERRED_RECORD_RESIDUAL,
    SUPERSEDED_BLOCKER,
    Kehop1103AggregateCandidate,
    assess_kehop_1103_aggregate,
    p110_state,
    semantic_boundaries,
)

ROOT=Path(__file__).resolve().parents[1]
SURFACE=ROOT/"data"/"processed"/"b02"/"p110_kehop_1103_access_surface.csv"
CONTRACT=ROOT/"data"/"processed"/"b02"/"p110_kehop_1103_extract_contract.csv"
REG=ROOT/"registry"/"b02_p110_kehop_1103_extract_access.csv"
SOURCES=ROOT/"registry"/"sources.csv"
QUESTIONS=ROOT/"registry"/"open_questions.csv"
MODULES=ROOT/"registry"/"module_status.csv"
READINESS=ROOT/"registry"/"retrofit_readiness.csv"
DOC=ROOT/"docs"/"source_packs"/"B02_P110_KEHOP_1103_EXTRACT_ACCESS.md"

def rows(path,key=None):
    with path.open(encoding="utf-8",newline="") as h:
        data=list(csv.DictReader(h))
    return {r[key]:r for r in data} if key else data

class P110Tests(unittest.TestCase):
    def test_complete_aggregate_admitted(self):
        d=assess_kehop_1103_aggregate(Kehop1103AggregateCandidate(
            declared_programmes=("KEHOP_PLUSZ_4_1_7_24","KEHOP_PLUSZ_4_1_8_24"),
            cutoff_date="2026-09-23",
            completed_project_count_all_measures=1000,
            completed_project_count_1103=400,
            enumeration_complete_for_declared_scope=True,
            source_scope_description="all physically completed projects through cutoff",
        ))
        self.assertTrue(d.admitted)
        self.assertEqual(d.blockers,())
        self.assertIn("AGGREGATE_1103_COUNT_DOES_NOT_SUPPLY_TECHNICAL_U_DISTRIBUTION",d.warnings)
        self.assertIn("AGGREGATE_1103_COUNT_DOES_NOT_CLASSIFY_EKR_OVERLAP",d.warnings)

    def test_incomplete_or_incoherent_aggregate_rejected(self):
        d=assess_kehop_1103_aggregate(Kehop1103AggregateCandidate(
            declared_programmes=("KEHOP_PLUSZ_4_1_7_24",),
            cutoff_date="2026-09-23",
            completed_project_count_all_measures=10,
            completed_project_count_1103=11,
            enumeration_complete_for_declared_scope=False,
            source_scope_description="sample",
        ))
        self.assertFalse(d.admitted)
        self.assertIn("1103_COUNT_CANNOT_EXCEED_ALL_COMPLETED_PROJECTS",d.blockers)
        self.assertIn("COMPLETE_ENUMERATION_FOR_DECLARED_SCOPE_REQUIRED",d.blockers)

    def test_state_narrows_access_boundary_without_numeric_tightening(self):
        s=p110_state()
        self.assertEqual(s["superseded_blocker"],SUPERSEDED_BLOCKER)
        self.assertEqual(s["primary_residual"],PRIMARY_NEXT_RESIDUAL)
        self.assertEqual(s["preferred_record_residual"],PREFERRED_RECORD_RESIDUAL)
        self.assertTrue(s["admin_indicator_monitoring_and_aggregation_proven"])
        self.assertTrue(s["fair_information_content_governance_proven"])
        self.assertFalse(s["current_public_project_level_1103_export_identified"])
        self.assertFalse(s["p110_numeric_national_action_tightening"])
        self.assertAlmostEqual(s["hp_only_share_upper"],0.17213897005530188)

    def test_surfaces_contract_and_registry(self):
        surface=rows(SURFACE,"surface_id")
        self.assertEqual(surface["B02-P110-S01"]["status"],"QUALIFIED_EXACT_ADMIN_SURFACE")
        self.assertEqual(surface["B02-P110-S02"]["status"],"STATUS_ONLY")
        self.assertEqual(surface["B02-P110-S06"]["status"],"QUALIFIED_PREFERRED_ROUTE")

        contract=rows(CONTRACT,"field_id")
        self.assertEqual(contract["B02-P110-C04"]["rule"],"must contain exact 1103")
        self.assertEqual(contract["B02-P110-C06"]["status"],"REQUIRED")

        reg=rows(REG,"item_id")
        self.assertEqual(reg["B02-P110-U05"]["status"],"SUPERSEDED_BY_FAIR_IH_ACCESS_BOUNDARY")
        self.assertEqual(reg["B02-P110-U02"]["residual_gap"],PRIMARY_NEXT_RESIDUAL)

        sources=rows(SOURCES,"source_id")
        self.assertIn("SRC-B02-KTM-KEHOP-FAIR-GOVERNANCE-2025",sources)
        self.assertIn("SRC-B02-KTM-KEHOP-FAIR-GOVERNANCE-2024",sources)

        q=rows(QUESTIONS,"question_id")["Q-B02-004"]
        self.assertIn("B02-P110",q["notes"])
        self.assertIn(PRIMARY_NEXT_RESIDUAL,q["notes"])

        module=rows(MODULES,"module_id")["B02"]
        self.assertEqual(module["readiness_percent"],"55")
        self.assertIn("B02-P110",module["gate_note"])

        peak=rows(READINESS,"component_id")["PEAK_LOAD_EFFECT"]
        self.assertEqual(peak["readiness_percent"],"50")
        self.assertIn("B02-P110",peak["notes"])

    def test_boundaries_and_doc(self):
        for b in (
            "PUBLIC_PROJECT_SEARCH_IS_NOT_COMPLETION_INDICATOR_EXPORT",
            "PROGRAMME_INDICATORS_ARE_NOT_COMPONENT_ACTION_COHORT",
            "ADMIN_DATA_EXISTS_IS_NOT_PUBLIC_DATA_AVAILABLE",
            "1103_AGGREGATE_IS_NOT_TECHNICAL_U_DISTRIBUTION",
            "1103_COUNT_IS_NOT_NON_EKR_1103_COUNT",
        ):
            self.assertIn(b,semantic_boundaries())

        text=DOC.read_text(encoding="utf-8")
        for phrase in (
            "FAIR_IH_KEHOP_1103_COMPLETION_EXPORT_OR_AGGREGATE_REQUIRED",
            "FAIR_IH_KEHOP_1103_COMPLETION_RECORD_EXTRACT_REQUIRED",
            "82.7861029945%",
            "17.2138970055%",
        ):
            self.assertIn(phrase,text)

if __name__=="__main__":
    unittest.main()
