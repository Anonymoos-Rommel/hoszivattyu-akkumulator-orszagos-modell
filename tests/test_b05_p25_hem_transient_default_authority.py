import csv
import unittest
from pathlib import Path

from modules.B05.hourly_onoff_parameter_policy import (
    DHW_STORAGE,
    FAN_COIL,
    HEM_DEFAULT_SCENARIO,
    HEM_FANCOIL_DIVERGENCE,
    RADIATOR_OR_UFH_WET,
    WARM_AIR,
    evaluate_hourly_onoff_with_policy,
    p25_boundary,
    resolve_emitter_response_time,
    resolve_tau_eq,
)

ROOT=Path(__file__).resolve().parents[1]
REG=ROOT/"registry"/"b05_p25_hem_transient_default_authority.csv"
QUESTIONS=ROOT/"registry"/"open_questions.csv"
VARIABLES=ROOT/"registry"/"heat_pump_variables.csv"
READINESS=ROOT/"registry"/"heat_pump_readiness.csv"
SOURCES=ROOT/"registry"/"heat_pump_sources.csv"
PACK=ROOT/"docs"/"source_packs"/"B05_P25_HEM_TRANSIENT_DEFAULT_AUTHORITY.md"

def rows(path):
    with path.open(encoding="utf-8",newline="") as h:
        return list(csv.DictReader(h))

class B05P25HemTransientDefaultAuthorityTests(unittest.TestCase):
    def test_hem_default_tau_eq_requires_explicit_policy(self):
        q=resolve_tau_eq(policy=None)
        self.assertIsNone(q.value_s)
        self.assertEqual(q.evidence_status,"Q")
        default=resolve_tau_eq(policy=HEM_DEFAULT_SCENARIO)
        self.assertEqual(default.value_s,140.0)
        self.assertEqual(default.evidence_status,"POL")

    def test_product_specific_tau_eq_is_not_replaced_by_default(self):
        explicit=resolve_tau_eq(
            policy=HEM_DEFAULT_SCENARIO,
            product_specific_tau_eq_s=87.5,
        )
        self.assertEqual(explicit.value_s,87.5)
        self.assertEqual(explicit.status,"QUALIFIED_EXPLICIT_PRODUCT_INPUT")

    def test_bounded_emitter_classes_resolve_from_current_doc_code_agreement(self):
        expected={
            RADIATOR_OR_UFH_WET:1370.0,
            WARM_AIR:120.0,
            DHW_STORAGE:1560.0,
        }
        for emitter,value in expected.items():
            result=resolve_emitter_response_time(emitter)
            self.assertEqual(result.status,"QUALIFIED_CURRENT_DOC_CODE_AGREEMENT")
            self.assertEqual(result.value_s,value)
            self.assertEqual(result.evidence_status,"POL")

    def test_fan_coil_current_doc_code_divergence_fails_closed(self):
        result=resolve_emitter_response_time(FAN_COIL)
        self.assertEqual(result.status,HEM_FANCOIL_DIVERGENCE)
        self.assertIsNone(result.value_s)
        self.assertIn("1370",result.reason)
        self.assertIn("360",result.reason)

    def test_default_radiator_scenario_executes_p24_formula(self):
        result=evaluate_hourly_onoff_with_policy(
            minimum_continuous_compressor_power_kw=0.5,
            load_ratio=0.2,
            minimum_continuous_load_ratio=0.4,
            emitter_class=RADIATOR_OR_UFH_WET,
            policy=HEM_DEFAULT_SCENARIO,
        )
        self.assertEqual(result.tau_eq_s,140.0)
        self.assertEqual(result.emitter_response_time_s,1370.0)
        self.assertEqual(result.evidence_status,"POL")
        self.assertAlmostEqual(result.onoff_inertia_power_kw,0.5*140*0.2*0.8/1370,places=12)

    def test_fan_coil_policy_remains_q_even_with_default_tau(self):
        result=evaluate_hourly_onoff_with_policy(
            minimum_continuous_compressor_power_kw=0.5,
            load_ratio=0.2,
            minimum_continuous_load_ratio=0.4,
            emitter_class=FAN_COIL,
            policy=HEM_DEFAULT_SCENARIO,
        )
        self.assertEqual(result.status,HEM_FANCOIL_DIVERGENCE)
        self.assertIsNone(result.onoff_inertia_power_kw)

    def test_registry_resolves_p24_parameter_authority_bounded_only(self):
        reg={r["claim"]:r for r in rows(REG)}
        self.assertEqual(
            reg["HOURLY_ONOFF_TRANSIENT_PARAMETER_AUTHORITY_REQUIRED"]["status"],
            "RESOLVED_FOR_EXPLICIT_HEM_DEFAULT_POLICY_WITH_BOUNDED_EMITTER_CLASSES",
        )
        self.assertEqual(reg["HEM_FANCOIL_EMITTER_TIME_DOC_CODE_DIVERGENCE_REQUIRED"]["status"],"OPEN")
        self.assertEqual(reg["PRODUCT_SPECIFIC_TAU_EQ_EVIDENCE_REQUIRED_FOR_OBS_RUNTIME"]["status"],"OPEN")
        self.assertEqual(reg["Q-B05-004"]["status"],"OPEN_NARROWED_TO_DOMAIN_GAPS_FANCOIL_AND_PRODUCT_TAU_EQ")

    def test_generic_product_variables_remain_q_and_policy_variables_are_separate(self):
        variables={r["variable_id"]:r for r in rows(VARIABLES)}
        self.assertEqual(variables["VAR-B05-ONOFF-TRANSIENT-TAU-EQ"]["status"],"Q")
        self.assertEqual(variables["VAR-B05-EMITTER-RESPONSE-TIME"]["status"],"Q")
        self.assertEqual(variables["VAR-B05-HOURLY-ONOFF-INERTIA-POWER"]["status"],"Q")
        self.assertEqual(variables["VAR-B05-HEM-DEFAULT-TAU-EQ"]["status"],"POL")
        self.assertEqual(variables["VAR-B05-HEM-DEFAULT-EMITTER-RESPONSE-TIME"]["status"],"POL")
        self.assertEqual(variables["VAR-B05-HEM-DEFAULT-ONOFF-INERTIA-POWER"]["status"],"DER")

    def test_live_question_lineage_and_readiness_remain_fail_closed(self):
        q={r["question_id"]:r for r in rows(QUESTIONS)}["Q-B05-004"]
        self.assertEqual(q["status"],"OPEN")
        for marker in (
            "B05-P24","B05-P25",
            "OPEN_NARROWED_TO_DOMAIN_GAPS_AND_HOURLY_ONOFF_PARAMETERS",
            "OPEN_NARROWED_TO_DOMAIN_GAPS_FANCOIL_AND_PRODUCT_TAU_EQ",
        ):
            self.assertIn(marker,q["notes"])
        readiness={r["component_id"]:r for r in rows(READINESS)}
        self.assertEqual(readiness["PART_LOAD_MODULATION"]["readiness_percent"],"45")

    def test_sources_and_document_preserve_default_vs_observation_boundary(self):
        sources={r["source_id"]:r for r in rows(SOURCES)}
        self.assertIn("SRC-B05-UK-HEM-RUST-ONOFF-CONSTANTS-2026",sources)
        self.assertIn("SRC-B05-UK-SAP-CALCM01-ONOFF-DEFAULTS-2017",sources)
        text=PACK.read_text(encoding="utf-8")
        self.assertIn("DEFAULT METHOD PARAMETER != PRODUCT OBSERVATION",text)
        self.assertIn("B05 remains **64%**",text)
        self.assertIn("HEM_DEFAULT_TAU_EQ_IS_POL_NOT_PRODUCT_OBS",p25_boundary())
        self.assertIn("FANCOIL_DOC_CODE_DIVERGENCE_FAILS_CLOSED",p25_boundary())

if __name__=="__main__":
    unittest.main()
