import csv
import unittest
from pathlib import Path

from modules.B05.mitsubishi_szu_acquisition_package import (
    AcquisitionResponse,
    AcquisitionTarget,
    REPORT_ID_BOUND,
    QUALIFIED_TRANSIENT_RECORD,
    READY_UNSENT,
    Q,
    required_request_fields,
    p48_boundaries,
)

ROOT = Path(__file__).resolve().parents[1]
REG = ROOT / "registry" / "b05_p48_mitsubishi_szu_acquisition_package.csv"
DATA = ROOT / "data" / "processed" / "b05_p48_mitsubishi_szu_acquisition_targets.csv"
QUESTIONS = ROOT / "registry" / "open_questions.csv"
VARIABLES = ROOT / "registry" / "heat_pump_variables.csv"
READINESS = ROOT / "registry" / "heat_pump_readiness.csv"
SOURCES = ROOT / "registry" / "heat_pump_sources.csv"
PACK = ROOT / "docs" / "source_packs" / "B05_P48_MITSUBISHI_SZU_ACQUISITION_PACKAGE.md"

def rows(path):
    with path.open(encoding="utf-8", newline="") as h:
        return list(csv.DictReader(h))

class B05P48MitsubishiSzuAcquisitionPackageTests(unittest.TestCase):
    def test_report_identity_without_transient_content_is_only_bound(self):
        r = AcquisitionResponse(
            True, "PUZ-WM50VHA", True, "SZU-REPORT-X", "2020-06-01", "SZU Brno"
        )
        self.assertEqual(r.classify(), REPORT_ID_BOUND)

    def test_direct_tau_can_qualify(self):
        r = AcquisitionResponse(
            True, "PUZ-WM50VHA", True, "SZU-REPORT-X", "2020-06-01", "SZU Brno",
            tau_eq_reported=True,
        )
        self.assertEqual(r.classify(), QUALIFIED_TRANSIENT_RECORD)

    def test_trace_needs_derivation_method(self):
        r = AcquisitionResponse(
            True, "PUZ-WM50VHA", True, "SZU-REPORT-X", "2020-06-01", "SZU Brno",
            seconds_scale_trace=True,
            explicit_derivation_method=False,
        )
        self.assertEqual(r.classify(), REPORT_ID_BOUND)
        r2 = AcquisitionResponse(
            True, "PUZ-WM50VHA", True, "SZU-REPORT-X", "2020-06-01", "SZU Brno",
            seconds_scale_trace=True,
            explicit_derivation_method=True,
        )
        self.assertEqual(r2.classify(), QUALIFIED_TRANSIENT_RECORD)

    def test_missing_direct_test_binding_fails_closed(self):
        r = AcquisitionResponse(
            True, "PUZ-WM50VHA", False, "SZU-REPORT-X", "2020-06-01", "SZU Brno",
            tau_eq_reported=True,
        )
        self.assertEqual(r.classify(), Q)

    def test_official_route_is_ready_but_unsent(self):
        t = AcquisitionTarget("SZU", "strakova@szutest.cz", True)
        self.assertEqual(t.state(), READY_UNSENT)

    def test_request_fields_cover_lineage_and_transient_content(self):
        fields = required_request_fields()
        for field in (
            "tested_subtype_or_model",
            "direct_test_specimen_binding",
            "report_or_protocol_id",
            "tau_eq_presence",
            "seconds_scale_trace_presence",
        ):
            self.assertIn(field, fields)

    def test_registry_and_global_state(self):
        reg = {r["claim"]: r for r in rows(REG)}
        self.assertEqual(reg["MITSUBISHI_SZU_ACQUISITION_PACKAGE"]["status"], "READY_UNSENT")
        q = {r["question_id"]: r for r in rows(QUESTIONS)}["Q-B05-004"]
        self.assertEqual(q["status"], "OPEN")
        self.assertIn("B05-P48", q["notes"])
        tau = {r["variable_id"]: r for r in rows(VARIABLES)}["VAR-B05-ONOFF-TRANSIENT-TAU-EQ"]
        self.assertEqual(tau["status"], "Q")
        self.assertIn("P48 adds an exact unsent acquisition contract", tau["notes"])

    def test_targets_sources_readiness_and_no_send(self):
        targets = rows(DATA)
        self.assertEqual(len(targets), 4)
        self.assertTrue(all(r["dispatch_state"] == "READY_UNSENT" for r in targets))
        sources = {r["source_id"]: r for r in rows(SOURCES)}
        for sid in (
            "SRC-B05-SZU-CERTIFICATION-PROCESS-CONTACT-2024",
            "SRC-B05-MITSUBISHI-ECODAN-TECHNICAL-CONTACT-2026",
            "SRC-B05-MITSUBISHI-CONTACT-US-2026",
            "SRC-B05-KEYMARK-DOCUMENTS-ANNEXL-2026",
        ):
            self.assertIn(sid, sources)
        readiness = {r["component_id"]: r for r in rows(READINESS)}
        self.assertEqual(readiness["PART_LOAD_MODULATION"]["readiness_percent"], "45")
        text = PACK.read_text(encoding="utf-8")
        self.assertIn("ACQUISITION_PACKAGE_READY_UNSENT", text)
        self.assertIn("NO_EXTERNAL_SEND_WITHOUT_HUMAN_AUTHORIZATION", p48_boundaries())

if __name__ == "__main__":
    unittest.main()
