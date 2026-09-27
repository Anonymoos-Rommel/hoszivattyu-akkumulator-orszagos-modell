import csv
import unittest
from pathlib import Path

from modules.B05.mitsubishi_szu_sampling_report_boundary import (
    CertificateScope,
    SamplingArchitecture,
    RegistrationComparison,
    ExactTransientRecord,
    CERTIFICATE_SCOPE_ONLY,
    SAMPLED_CERTIFICATION_SCOPE,
    CROSS_REGISTRATION_IDENTITY,
    EXACT_TEST_BINDING,
    QUALIFIED_TRANSIENT_RECORD,
    Q,
    p47_boundaries,
)

ROOT = Path(__file__).resolve().parents[1]
REG = ROOT / "registry" / "b05_p47_mitsubishi_szu_sampling_report_boundary.csv"
DATA = ROOT / "data" / "processed" / "b05_p47_mitsubishi_szu_sampling_inventory.csv"
QUESTIONS = ROOT / "registry" / "open_questions.csv"
VARIABLES = ROOT / "registry" / "heat_pump_variables.csv"
READINESS = ROOT / "registry" / "heat_pump_readiness.csv"
SOURCES = ROOT / "registry" / "heat_pump_sources.csv"
PACK = ROOT / "docs" / "source_packs" / "B05_P47_MITSUBISHI_SZU_SAMPLING_REPORT_BOUNDARY.md"

def rows(path):
    with path.open(encoding="utf-8", newline="") as h:
        return list(csv.DictReader(h))

class B05P47MitsubishiSzuSamplingBoundaryTests(unittest.TestCase):
    def test_certificate_registration_alone_is_not_report_identity(self):
        c = CertificateScope("037-0032-20", True, True)
        self.assertEqual(c.classify(), CERTIFICATE_SCOPE_ONLY)

    def test_exact_report_and_sample_binding_can_reach_exact_test_binding(self):
        c = CertificateScope(
            "037-0032-20", True, True, report_id="SZU-X", tested_sample_id="SERIAL-X"
        )
        self.assertEqual(c.classify(), EXACT_TEST_BINDING)

    def test_sampled_scheme_scope_is_explicit(self):
        self.assertEqual(
            SamplingArchitecture(5, 1).classify(),
            SAMPLED_CERTIFICATION_SCOPE,
        )

    def test_same_outdoor_unit_across_registrations_is_not_unique_test_identity(self):
        c = RegistrationComparison("037-0030-20", "037-0032-20", True)
        self.assertEqual(c.classify(), CROSS_REGISTRATION_IDENTITY)

    def test_exact_tau_or_derivable_trace_requires_test_binding(self):
        direct = ExactTransientRecord(True, True, True, True, False, False)
        self.assertEqual(direct.classify(), QUALIFIED_TRANSIENT_RECORD)
        trace = ExactTransientRecord(True, True, True, False, True, True)
        self.assertEqual(trace.classify(), QUALIFIED_TRANSIENT_RECORD)
        missing_binding = ExactTransientRecord(True, False, True, True, False, False)
        self.assertEqual(missing_binding.classify(), Q)

    def test_registry_narrows_mitsubishi_transient_route(self):
        reg = {r["claim"]: r for r in rows(REG)}
        self.assertEqual(
            reg["MITSUBISHI_037_0032_20_CERTIFICATE_SCOPE"]["status"],
            "EXACT_CERTIFICATE_SCOPE_BOUND",
        )
        self.assertEqual(
            reg["MITSUBISHI_PRODUCT_TAU_EQ_EVIDENCE"]["status"],
            "OPEN_NARROWED_TO_TESTED_SPECIMEN_BINDING_PLUS_EXACT_TRANSIENT_RECORD",
        )
        self.assertIn(
            "EXACT_PUZ_WM50_TESTED_SPECIMEN_BINDING",
            reg["MITSUBISHI_PRODUCT_TAU_EQ_EVIDENCE"]["residual_gap"],
        )

    def test_global_question_and_tau_stay_open(self):
        q = {r["question_id"]: r for r in rows(QUESTIONS)}["Q-B05-004"]
        self.assertEqual(q["status"], "OPEN")
        self.assertIn("B05-P47", q["notes"])
        self.assertIn("REGISTRATION_ID != UNIQUE_TESTED_SPECIMEN", q["notes"])
        tau = {r["variable_id"]: r for r in rows(VARIABLES)}[
            "VAR-B05-ONOFF-TRANSIENT-TAU-EQ"
        ]
        self.assertEqual(tau["status"], "Q")
        self.assertIn("P47 repairs", tau["notes"])

    def test_sources_inventory_and_readiness(self):
        s = {r["source_id"]: r for r in rows(SOURCES)}
        for sid in (
            "SRC-B05-SZU-MITSUBISHI-WM50-CERT-2020",
            "SRC-B05-HPKEYMARK-SAMPLING-ANNEXA-2017",
            "SRC-B05-HPKEYMARK-SCHEME-V15-2024",
            "SRC-B05-HPKEYMARK-MITSUBISHI-WM50-170D-2026",
            "SRC-B05-MITSUBISHI-WM50-PRODUCT-SHEET-2025",
            "SRC-B05-MCS-WM50-DIRECTORY-CAPTURE-2022",
        ):
            self.assertIn(sid, s)
        self.assertEqual(len(rows(DATA)), 7)
        readiness = {r["component_id"]: r for r in rows(READINESS)}
        self.assertEqual(readiness["PART_LOAD_MODULATION"]["readiness_percent"], "45")
        text = PACK.read_text(encoding="utf-8")
        self.assertIn("PART_LOAD_MODULATION = **45%**", text)
        self.assertIn("CERTIFIED_SUBTYPE_IS_NOT_PROVEN_DIRECTLY_TESTED_SUBTYPE", p47_boundaries())
        reg = {r["claim"]: r for r in rows(REG)}
        self.assertEqual(reg["MCS_SUFFIX_037_0032_20_01_02_SEMANTICS"]["status"], "MODEL_LEVEL_CERTIFICATION_IDS_NOT_TEST_REPORT_IDS")

if __name__ == "__main__":
    unittest.main()
