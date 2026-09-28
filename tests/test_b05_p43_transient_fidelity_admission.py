import csv
import unittest
from pathlib import Path

from modules.B05.transient_fidelity_admission import (
    FanCoilTransientRecord, HeatPumpTauEqRecord,
    QUALIFIED_FANCOIL_OBS, QUALIFIED_PRODUCT_TAU_EQ_OBS, Q, p43_boundaries,
)

ROOT = Path(__file__).resolve().parents[1]
REG = ROOT / "registry" / "b05_p43_transient_fidelity_admission.csv"
DATA = ROOT / "data" / "processed" / "b05_p43_transient_evidence_inventory.csv"
QUESTIONS = ROOT / "registry" / "open_questions.csv"
VARIABLES = ROOT / "registry" / "heat_pump_variables.csv"
READINESS = ROOT / "registry" / "heat_pump_readiness.csv"
SOURCES = ROOT / "registry" / "heat_pump_sources.csv"
PACK = ROOT / "docs" / "source_packs" / "B05_P43_TRANSIENT_FIDELITY_ADMISSION.md"

def rows(path):
    with path.open(encoding="utf-8", newline="") as h:
        return list(csv.DictReader(h))

class B05P43TransientFidelityAdmissionTests(unittest.TestCase):
    def test_reviewed_fancoil_system_response_fails_emitter_gate(self):
        r = FanCoilTransientRecord(3000.0,"SRC-B05-FANCOIL-DYNAMIC-ARGHAND-2018",
            False,False,True,False,True,True)
        self.assertEqual(r.classify(), Q)

    def test_exact_heating_emitter_output_record_can_pass(self):
        r = FanCoilTransientRecord(360.0,"SRC-EXAMPLE-LAB",True,True,True,True,True)
        self.assertEqual(r.classify(), QUALIFIED_FANCOIL_OBS)

    def test_lab_identity_without_transient_result_fails_tau_gate(self):
        r = HeatPumpTauEqRecord(None,"SRC-B05-HPKEYMARK-DIMPLEX-LA2030CP-2026",
            True,True,False)
        self.assertEqual(r.classify(), Q)

    def test_exact_product_direct_lab_report_can_pass_tau_gate(self):
        r = HeatPumpTauEqRecord(42.0,"SRC-EXAMPLE-EXACT-PRODUCT-LAB",
            True,True,True,source_reports_tau_eq=True)
        self.assertEqual(r.classify(), QUALIFIED_PRODUCT_TAU_EQ_OBS)

    def test_trace_derived_tau_requires_complete_record(self):
        incomplete = HeatPumpTauEqRecord(42.0,"SRC-EXAMPLE-TRACE",True,True,True,
            seconds_scale_cadence=True,thermal_output_trace=True,
            electrical_input_trace=False,steady_state_reference=True,
            explicit_derivation_method=True)
        self.assertEqual(incomplete.classify(), Q)
        complete = HeatPumpTauEqRecord(42.0,"SRC-EXAMPLE-TRACE",True,True,True,
            seconds_scale_cadence=True,thermal_output_trace=True,
            electrical_input_trace=True,steady_state_reference=True,
            explicit_derivation_method=True)
        self.assertEqual(complete.classify(), QUALIFIED_PRODUCT_TAU_EQ_OBS)

    def test_registry_narrows_without_false_closure(self):
        reg={r["claim"]:r for r in rows(REG)}
        self.assertEqual(reg["FANCOIL_OBS_EMITTER_RESPONSE_EVIDENCE_REQUIRED"]["status"],
            "OPEN_NARROWED_TO_EMITTER_OUTPUT_STEP_RESPONSE_RECORD_REQUIRED")
        self.assertEqual(reg["PRODUCT_OR_LAB_TRANSIENT_TEST_RECORD_REQUIRED"]["status"],
            "OPEN_NARROWED_TO_EXACT_PRODUCT_SECONDS_SCALE_TRANSIENT_RECORD_FROM_MANUFACTURER_OR_NAMED_TEST_LAB")
        self.assertEqual(reg["GENERIC_AWHP_TRANSIENT_TIME_CONSTANT_TRANSFER"]["status"],"FORBIDDEN")

    def test_canonical_lab_targets_are_explicit(self):
        reg={r["claim"]:r for r in rows(REG)}
        self.assertEqual(reg["DIMPLEX_LA2030CP_TRANSIENT_ACQUISITION_TARGET"]["status"],"NAMED_TEST_LAB_BOUND")
        self.assertEqual(reg["MITSUBISHI_WM50_TRANSIENT_ACQUISITION_TARGET"]["status"],"NAMED_TEST_LAB_BOUND")
        text=PACK.read_text(encoding="utf-8")
        self.assertIn("VDE Prüf- und Zertifizierungsinstitut GmbH",text)
        self.assertIn("SZU Brno",text)

    def test_global_state_remains_fail_closed(self):
        q={r["question_id"]:r for r in rows(QUESTIONS)}["Q-B05-004"]
        self.assertEqual(q["status"],"OPEN")
        self.assertIn("B05-P43",q["notes"])
        vars_={r["variable_id"]:r for r in rows(VARIABLES)}
        self.assertEqual(vars_["VAR-B05-FANCOIL-OBS-EMITTER-RESPONSE-TIME"]["status"],"Q")
        self.assertEqual(vars_["VAR-B05-ONOFF-TRANSIENT-TAU-EQ"]["status"],"Q")
        readiness={r["component_id"]:r for r in rows(READINESS)}
        self.assertGreaterEqual(int(readiness["PART_LOAD_MODULATION"]["readiness_percent"]),45)

    def test_sources_data_and_boundaries_registered(self):
        s={r["source_id"]:r for r in rows(SOURCES)}
        self.assertIn("SRC-B05-FANCOIL-DYNAMIC-ARGHAND-2018",s)
        self.assertIn("SRC-B05-AWHP-ONOFF-XU-2021",s)
        self.assertEqual(len(rows(DATA)),4)
        self.assertIn("ROOM_PLUS_FCU_RESPONSE_IS_NOT_EMITTER_ONLY_RESPONSE",p43_boundaries())
        self.assertIn("GENERIC_LITERATURE_TAU_IS_NOT_PRODUCT_TAU_EQ",p43_boundaries())

if __name__ == "__main__":
    unittest.main()
