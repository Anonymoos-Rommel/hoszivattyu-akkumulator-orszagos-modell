import csv
import unittest
from pathlib import Path

from modules.B02.kehop_1103_completion_cohort import (
    EKR_OVERLAP_RESIDUAL,
    PRIMARY_NEXT_RESIDUAL,
    SUPERSEDED_BLOCKER,
    TECHNICAL_JOIN_RESIDUAL,
    WINDOW_MEASURE_CATEGORY,
    CompletionIndicatorDecision,
    Kehop1103ExtractCandidate,
    KehopCompletionIndicatorRecord,
    assess_completion_indicator_record,
    assess_kehop_1103_extract,
    classify_ekr_overlap,
    p109_state,
    semantic_boundaries,
)

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = ROOT / "data" / "processed" / "b02" / "p109_kehop_completion_indicator_schema.csv"
ROUTES = ROOT / "data" / "processed" / "b02" / "p109_kehop_window_cohort_routes.csv"
REG = ROOT / "registry" / "b02_p109_kehop_1103_completion_cohort.csv"
SOURCES = ROOT / "registry" / "sources.csv"
QUESTIONS = ROOT / "registry" / "open_questions.csv"
MODULES = ROOT / "registry" / "module_status.csv"
READINESS = ROOT / "registry" / "retrofit_readiness.csv"
DOC = ROOT / "docs" / "source_packs" / "B02_P109_KEHOP_1103_COMPLETION_COHORT.md"

def rows(path, key=None):
    with path.open(encoding="utf-8", newline="") as h:
        data = list(csv.DictReader(h))
    return {r[key]: r for r in data} if key else data

def rec(project_id="P1", programme="KEHOP_PLUSZ_4_1_7_24", cats=("1103",), hem_id=""):
    return KehopCompletionIndicatorRecord(
        project_id=project_id,
        programme_code=programme,
        physical_completion_date="2026-08-31",
        measure_category_codes=cats,
        final_het_ref="HET-1",
        final_energy_calculation_ref="CALC-1",
        hem_id=hem_id,
    )

class P109Tests(unittest.TestCase):
    def test_1103_record_admission(self):
        d=assess_completion_indicator_record(rec())
        self.assertTrue(d.admitted_to_1103_cohort)
        self.assertEqual(d.blockers,())
        self.assertEqual(WINDOW_MEASURE_CATEGORY,"1103")

    def test_wrong_measure_or_programme_rejected(self):
        d=assess_completion_indicator_record(rec(cats=("1101",)))
        self.assertFalse(d.admitted_to_1103_cohort)
        self.assertIn("MEKH_MEASURE_CATEGORY_1103_REQUIRED",d.blockers)
        d2=assess_completion_indicator_record(rec(programme="OTHER"))
        self.assertFalse(d2.admitted_to_1103_cohort)
        self.assertIn("SUPPORTED_KEHOP_PROGRAMME_REQUIRED",d2.blockers)

    def test_complete_declared_extract_required(self):
        good=assess_kehop_1103_extract(Kehop1103ExtractCandidate(
            records=(rec("P1"),rec("P2","KEHOP_PLUSZ_4_1_8_24")),
            declared_programmes=("KEHOP_PLUSZ_4_1_7_24","KEHOP_PLUSZ_4_1_8_24"),
            reference_cutoff_date="2026-09-23",
            enumeration_complete_for_declared_scope=True,
            source_scope_description="all physically completed projects through cutoff",
        ))
        self.assertTrue(good.admitted)
        self.assertEqual(good.unique_project_count,2)

        bad=assess_kehop_1103_extract(Kehop1103ExtractCandidate(
            records=(rec("P1"),),
            declared_programmes=("KEHOP_PLUSZ_4_1_7_24",),
            reference_cutoff_date="2026-09-23",
            enumeration_complete_for_declared_scope=False,
            source_scope_description="sample",
        ))
        self.assertFalse(bad.admitted)
        self.assertIn("COMPLETE_ENUMERATION_FOR_DECLARED_SCOPE_REQUIRED",bad.blockers)

    def test_duplicates_rejected(self):
        d=assess_kehop_1103_extract(Kehop1103ExtractCandidate(
            records=(rec("P1"),rec("P1")),
            declared_programmes=("KEHOP_PLUSZ_4_1_7_24",),
            reference_cutoff_date="2026-09-23",
            enumeration_complete_for_declared_scope=True,
            source_scope_description="complete",
        ))
        self.assertFalse(d.admitted)
        self.assertIn("DUPLICATE_PROJECT_IDS_IN_EXTRACT",d.blockers)

    def test_measure_category_does_not_mint_hem(self):
        self.assertEqual(classify_ekr_overlap(rec()),"EKR_HEM_OVERLAP_UNCLASSIFIED")
        self.assertEqual(classify_ekr_overlap(rec(hem_id="HEM-1")),"EXPLICIT_HEM_ID_BOUND")

    def test_state_and_registries(self):
        s=p109_state()
        self.assertEqual(s["superseded_blocker"],SUPERSEDED_BLOCKER)
        self.assertEqual(s["primary_residual"],PRIMARY_NEXT_RESIDUAL)
        self.assertEqual(s["technical_join_residual"],TECHNICAL_JOIN_RESIDUAL)
        self.assertEqual(s["ekr_overlap_residual"],EKR_OVERLAP_RESIDUAL)
        self.assertTrue(s["completion_indicator_1103_admin_field_proven"])
        self.assertFalse(s["public_1103_completion_extract_identified"])
        self.assertFalse(s["p109_numeric_national_action_tightening"])
        self.assertAlmostEqual(s["hp_only_share_upper"],0.17213897005530188)

        schema=rows(SCHEMA,"field_id")
        self.assertEqual(schema["B02-P109-F04"]["status"],"QUALIFIED_ADMIN_FIELD")
        self.assertEqual(schema["B02-P109-F05"]["status"],"QUALIFIED_EXACT_CODE")

        routes=rows(ROUTES,"route_id")
        self.assertEqual(routes["B02-P109-R01"]["status"],"QUALIFIED_ADMIN_COHORT_ROUTE")

        reg=rows(REG,"item_id")
        self.assertEqual(reg["B02-P109-U05"]["status"],"SUPERSEDED_BY_EXACT_ADMIN_EXTRACT_AND_JOIN")

        sources=rows(SOURCES,"source_id")
        self.assertIn("SRC-B02-HU-KEHOP-418-COMPLETION-INDICATORS-2025",sources)

        q=rows(QUESTIONS,"question_id")["Q-B02-004"]
        self.assertIn("B02-P109",q["notes"])
        self.assertIn(PRIMARY_NEXT_RESIDUAL,q["notes"])

        module=rows(MODULES,"module_id")["B02"]
        self.assertEqual(module["readiness_percent"],"55")
        self.assertIn("B02-P109",module["gate_note"])

        peak=rows(READINESS,"component_id")["PEAK_LOAD_EFFECT"]
        self.assertEqual(peak["readiness_percent"],"50")
        self.assertIn("B02-P109",peak["notes"])

    def test_boundaries_and_doc(self):
        for b in (
            "COMPLETION_INDICATOR_1103_IS_NOT_TECHNICAL_U_DISTRIBUTION",
            "RCO18_HOUSEHOLD_COUNT_IS_NOT_WINDOW_1103_COHORT",
            "MEKH_CATEGORY_1103_IS_NOT_REGISTERED_HEM_1103",
            "ADMINISTRATIVELY_ENUMERABLE_IS_NOT_PUBLICLY_AVAILABLE",
            "CONVENIENCE_SAMPLE_IS_NOT_COMPLETE_DECLARED_SCOPE_COHORT",
        ):
            self.assertIn(b,semantic_boundaries())
        text=DOC.read_text(encoding="utf-8")
        for phrase in (
            "MFB_KEHOP_COMPLETION_INDICATOR_1103_EXTRACT_REQUIRED",
            "KEHOP_1103_FINAL_TECHNICAL_DOCUMENT_JOIN_REQUIRED",
            "MEKH CATEGORY 1103 != REGISTERED HEM 1103",
            "82.7861029945%",
            "17.2138970055%",
        ):
            self.assertIn(phrase,text)

if __name__=="__main__":
    unittest.main()
