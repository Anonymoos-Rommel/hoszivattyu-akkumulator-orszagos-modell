import csv
import unittest
from pathlib import Path

from tests.b05_readiness_assertions import assert_part_load_readiness_unassessed

from modules.B05.transient_report_lineage import (
    ProductTransientReport,
    CrossBrandPlatformEvidence,
    FanCoilHeatingTransient,
    REPORT_LINEAGE_BOUND,
    TRANSIENT_CONTENT_QUALIFIED,
    STRONG_PLATFORM_LINK_NOT_PRODUCT_IDENTITY,
    QUALIFIED_FCU_EMITTER_OBS,
    POLICY_DEFAULT_ONLY,
    Q,
    classify_tau_eq_default,
    p44_boundaries,
)

ROOT = Path(__file__).resolve().parents[1]
REG = ROOT / "registry" / "b05_p44_transient_report_lineage.csv"
DATA = ROOT / "data" / "processed" / "b05_p44_transient_report_inventory.csv"
QUESTIONS = ROOT / "registry" / "open_questions.csv"
VARIABLES = ROOT / "registry" / "heat_pump_variables.csv"
READINESS = ROOT / "registry" / "heat_pump_readiness.csv"
SOURCES = ROOT / "registry" / "heat_pump_sources.csv"
PACK = ROOT / "docs" / "source_packs" / "B05_P44_TRANSIENT_REPORT_LINEAGE.md"

def rows(path):
    with path.open(encoding="utf-8", newline="") as h:
        return list(csv.DictReader(h))

class B05P44TransientReportLineageTests(unittest.TestCase):
    def test_exact_dimplex_report_identity_is_lineage_not_tau(self):
        r = ProductTransientReport(
            report_id="328782-TL2-1",
            exact_product_identity=True,
            recognised_lab=True,
            en14825_test_basis=True,
        )
        self.assertEqual(r.classify(), REPORT_LINEAGE_BOUND)

    def test_exact_report_with_direct_tau_can_pass_content_gate(self):
        r = ProductTransientReport(
            report_id="EXACT-REPORT",
            exact_product_identity=True,
            recognised_lab=True,
            en14825_test_basis=True,
            tau_eq_reported=True,
        )
        self.assertEqual(r.classify(), TRANSIENT_CONTENT_QUALIFIED)

    def test_cross_brand_link_does_not_create_product_identity(self):
        r = CrossBrandPlatformEvidence(True, True, True, False)
        self.assertEqual(r.classify(), STRONG_PLATFORM_LINK_NOT_PRODUCT_IDENTITY)

    def test_fcu_room_system_heating_response_fails_emitter_gate(self):
        r = FanCoilHeatingTransient(
            source_id="SRC-B05-ASHP-RF-FCU-HEATING-TRANSIENT-2026",
            exact_fcu_identity=False,
            heating_mode=True,
            explicit_input_step=True,
            emitter_heat_output_response=False,
            response_time_s=7920.0,
        )
        self.assertEqual(r.classify(), Q)

    def test_exact_fcu_heating_output_response_can_pass(self):
        r = FanCoilHeatingTransient(
            source_id="SRC-EXAMPLE-FCU-LAB",
            exact_fcu_identity=True,
            heating_mode=True,
            explicit_input_step=True,
            emitter_heat_output_response=True,
            response_time_s=180.0,
        )
        self.assertEqual(r.classify(), QUALIFIED_FCU_EMITTER_OBS)

    def test_default_values_are_policy_only(self):
        self.assertEqual(classify_tau_eq_default(30.0, "EN15316"), POLICY_DEFAULT_ONLY)
        self.assertEqual(classify_tau_eq_default(140.0, "UK_SAP_HEM"), POLICY_DEFAULT_ONLY)

    def test_registry_refines_without_false_closure(self):
        reg = {r["claim"]: r for r in rows(REG)}
        self.assertEqual(reg["DIMPLEX_LA2030CP_VDE_REPORT_LINEAGE"]["status"], "EXACT_REPORT_IDENTIFIED")
        self.assertEqual(reg["PUBLIC_EN14825_DECLARATION_TAU_EQ_EXPOSURE"]["status"], "NOT_EXPOSED_ON_PUBLIC_FORM")
        self.assertEqual(reg["BOSCH_DIMPLEX_PLATFORM_EVIDENCE"]["status"], "STRONG_BOUNDED_CROSS_BRAND_LINEAGE")
        self.assertEqual(reg["FANCOIL_OBS_EMITTER_RESPONSE_EVIDENCE_REQUIRED"]["status"],
                         "OPEN_NARROWED_TO_EXACT_FCU_HEATING_OUTPUT_STEP_RESPONSE_RECORD_REQUIRED")

    def test_global_q_and_readiness_stay_bounded(self):
        q = {r["question_id"]: r for r in rows(QUESTIONS)}["Q-B05-004"]
        self.assertEqual(q["status"], "OPEN")
        self.assertIn("B05-P44", q["notes"])
        self.assertIn("328782-TL2-1", q["notes"])
        variables = {r["variable_id"]: r for r in rows(VARIABLES)}
        self.assertEqual(variables["VAR-B05-ONOFF-TRANSIENT-TAU-EQ"]["status"], "Q")
        self.assertEqual(variables["VAR-B05-FANCOIL-OBS-EMITTER-RESPONSE-TIME"]["status"], "Q")
        readiness = {r["component_id"]: r for r in rows(READINESS)}
        assert_part_load_readiness_unassessed(self, readiness["PART_LOAD_MODULATION"])

    def test_sources_inventory_and_boundaries(self):
        s = {r["source_id"]: r for r in rows(SOURCES)}
        for sid in (
            "SRC-B05-DIMPLEX-VDE-CERT-40060852-2025",
            "SRC-B05-HPKEYMARK-ANNEXA-V2-2026",
            "SRC-B05-UK-PCDB-HP-TEST-REQUIREMENTS-2026",
            "SRC-B05-UK-PCDB-EN14825-DECLARATION-V2-2017",
            "SRC-B05-UCERT-EN15316-TAUEQ-DEFAULT-2023",
            "SRC-B05-BOSCH-CS5001AW22-VDE-CERT-2026",
            "SRC-B05-BOSCH-CS5001AW22-DOC-2026",
            "SRC-B05-ASHP-RF-FCU-HEATING-TRANSIENT-2026",
            "SRC-B05-FCU-DYNAMIC-ENTRANSY-DUAN-2021",
            "SRC-B05-FCU-2R1C-DYNAMIC-DUAN-2023",
        ):
            self.assertIn(sid, s)
        self.assertEqual(len(rows(DATA)), 10)
        self.assertIn("EN14825_REPORT_EXISTS_IS_NOT_TAU_EQ_CONTENT", p44_boundaries())
        self.assertIn("CROSS_BRAND_PLATFORM_EVIDENCE_IS_NOT_PRODUCT_IDENTITY", p44_boundaries())
        text = PACK.read_text(encoding="utf-8")
        self.assertIn("328782-TL2-1", text)
        self.assertIn("PART_LOAD_MODULATION = **45%**", text)
        self.assertIn("heat-source -> terminal -> room", text)
        self.assertIn("2R1C", text)

if __name__ == "__main__":
    unittest.main()
