import csv
import unittest
from pathlib import Path

from modules.B05.transient_report_recoverability import (
    ReportReference,
    PublicSearchResult,
    PublicCertificationExport,
    EXACT_REPORT_REFERENCE_ONLY,
    PUBLIC_SURFACE_ONLY,
    QUALIFIED_PRODUCT_TRANSIENT_CONTENT,
    p45_boundaries,
)

ROOT = Path(__file__).resolve().parents[1]
REG = ROOT / "registry" / "b05_p45_dimplex_vde_report_recoverability.csv"
DATA = ROOT / "data" / "processed" / "b05_p45_dimplex_vde_report_recoverability.csv"
QUESTIONS = ROOT / "registry" / "open_questions.csv"
VARIABLES = ROOT / "registry" / "heat_pump_variables.csv"
READINESS = ROOT / "registry" / "heat_pump_readiness.csv"
SOURCES = ROOT / "registry" / "heat_pump_sources.csv"
PACK = ROOT / "docs" / "source_packs" / "B05_P45_DIMPLEX_VDE_REPORT_RECOVERABILITY.md"

def rows(path):
    with path.open(encoding="utf-8", newline="") as h:
        return list(csv.DictReader(h))

class B05P45DimplexVdeRecoverabilityTests(unittest.TestCase):
    def test_exact_report_reference_is_not_content(self):
        r = ReportReference(
            report_id="328782-TL2-1",
            exact_product=True,
            official_source=True,
            contains_numeric_transient_content=False,
        )
        self.assertEqual(r.classify(), EXACT_REPORT_REFERENCE_ONLY)

    def test_public_search_miss_stays_surface_only(self):
        r = PublicSearchResult(
            exact_id_queried=True,
            official_domains_queried=True,
            report_copy_recovered=False,
            source_native_transient_excerpt_recovered=False,
        )
        self.assertEqual(r.classify(), PUBLIC_SURFACE_ONLY)

    def test_exact_recovered_transient_content_can_pass(self):
        r = PublicSearchResult(True, True, False, True)
        self.assertEqual(r.classify(), QUALIFIED_PRODUCT_TRANSIENT_CONTENT)

    def test_cdh_does_not_admit_tau(self):
        r = PublicCertificationExport(
            exact_product=True,
            cdh_exposed=True,
            tau_eq_exposed=False,
            seconds_scale_trace_exposed=False,
        )
        self.assertFalse(r.admits_tau_eq())
        self.assertFalse(r.admits_trace_derivation())

    def test_registry_uses_bounded_nonrecovery_language(self):
        reg = {r["claim"]: r for r in rows(REG)}
        self.assertEqual(
            reg["EXACT_REPORT_PUBLIC_RECOVERY"]["status"],
            "NOT_RECOVERED_FROM_INDEXED_PUBLIC_SURFACES_AS_OF_2026_09_27",
        )
        self.assertIn(
            "CLAIM_REPORT_NONPUBLIC",
            reg["EXACT_REPORT_PUBLIC_RECOVERY"]["forbidden_use"],
        )
        self.assertEqual(
            reg["DIMPLEX_PRODUCT_TAU_EQ_EVIDENCE"]["status"],
            "OPEN_NARROWED_TO_EXACT_REPORT_CONTENT_OR_TRANSIENT_EXCERPT",
        )

    def test_global_question_and_readiness_do_not_close(self):
        q = {r["question_id"]: r for r in rows(QUESTIONS)}["Q-B05-004"]
        self.assertEqual(q["status"], "OPEN")
        self.assertIn("B05-P45", q["notes"])
        self.assertIn("PUBLIC_INDEX_SEARCH_MISS", q["notes"])
        tau = {r["variable_id"]: r for r in rows(VARIABLES)}[
            "VAR-B05-ONOFF-TRANSIENT-TAU-EQ"
        ]
        self.assertEqual(tau["status"], "Q")
        self.assertEqual(tau["updated_at"], "2026-09-27")
        readiness = {r["component_id"]: r for r in rows(READINESS)}
        self.assertEqual(readiness["PART_LOAD_MODULATION"]["readiness_percent"], "45")

    def test_sources_and_inventory(self):
        s = {r["source_id"]: r for r in rows(SOURCES)}
        self.assertIn("SRC-B05-HPKEYMARK-LA2030CP-PUBLIC-EXPORT-2026", s)
        self.assertIn("SRC-B05-VDE-PUBLIC-CERTIFICATE-SEARCH-2026", s)
        self.assertEqual(len(rows(DATA)), 5)
        text = PACK.read_text(encoding="utf-8")
        self.assertIn("328782-TL2-1", text)
        self.assertIn("PART_LOAD_MODULATION = **45%**", text)
        self.assertIn(
            "PUBLIC_INDEX_SEARCH_MISS_IS_NOT_REPORT_NONEXISTENCE",
            p45_boundaries(),
        )

if __name__ == "__main__":
    unittest.main()
