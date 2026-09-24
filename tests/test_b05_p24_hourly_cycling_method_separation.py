import csv
import unittest
from pathlib import Path

from modules.B05.hourly_cycling_method import (
    HOURLY_ONOFF_TRANSIENT_PARAMETER_AUTHORITY_REQUIRED,
    NO_EXACT_CDH_BIN,
    QUALIFIED_HOURLY_ONOFF_METHOD,
    exact_cdh_bin_lookup,
    onoff_inertia_power_kw,
    p24_boundary,
)

ROOT=Path(__file__).resolve().parents[1]
REG=ROOT/"registry"/"b05_p24_hourly_cycling_method_separation.csv"
QUESTIONS=ROOT/"registry"/"open_questions.csv"
VARIABLES=ROOT/"registry"/"heat_pump_variables.csv"
FORMULAS=ROOT/"registry"/"heat_pump_formulas.csv"
READINESS=ROOT/"registry"/"heat_pump_readiness.csv"
SOURCES=ROOT/"registry"/"heat_pump_sources.csv"
PACK=ROOT/"docs"/"source_packs"/"B05_P24_HOURLY_CYCLING_METHOD_SEPARATION.md"

def rows(path):
    with path.open(encoding="utf-8",newline="") as h:
        return list(csv.DictReader(h))

class B05P24HourlyCyclingMethodSeparationTests(unittest.TestCase):
    def test_exact_cdh_bins_are_available_but_intermediate_temperature_is_not(self):
        bins={-7.0:0.99,2.0:0.98,7.0:0.95,12.0:0.93}
        exact=exact_cdh_bin_lookup(2.0,bins)
        self.assertEqual(exact.status,"OBS / EXACT_CDH_BIN")
        self.assertEqual(exact.cdh,0.98)
        mid=exact_cdh_bin_lookup(4.0,bins)
        self.assertEqual(mid.status,NO_EXACT_CDH_BIN)
        self.assertIsNone(mid.cdh)

    def test_hourly_path_requires_transient_parameters_below_floor(self):
        result=onoff_inertia_power_kw(
            minimum_continuous_compressor_power_kw=0.5,
            load_ratio=0.2,
            minimum_continuous_load_ratio=0.4,
            tau_eq_s=None,
            emitter_response_time_s=None,
        )
        self.assertEqual(result.residual_gap,HOURLY_ONOFF_TRANSIENT_PARAMETER_AUTHORITY_REQUIRED)
        self.assertIsNone(result.onoff_inertia_power_kw)

    def test_hourly_onoff_formula_is_executable_when_inputs_are_explicit(self):
        result=onoff_inertia_power_kw(
            minimum_continuous_compressor_power_kw=0.5,
            load_ratio=0.2,
            minimum_continuous_load_ratio=0.4,
            tau_eq_s=140.0,
            emitter_response_time_s=900.0,
        )
        self.assertEqual(result.status,QUALIFIED_HOURLY_ONOFF_METHOD)
        self.assertAlmostEqual(result.onoff_inertia_power_kw,0.5*140*0.2*0.8/900,places=12)

    def test_no_penalty_when_not_below_minimum_continuous_load(self):
        result=onoff_inertia_power_kw(
            minimum_continuous_compressor_power_kw=0.5,
            load_ratio=0.4,
            minimum_continuous_load_ratio=0.4,
            tau_eq_s=None,
            emitter_response_time_s=None,
        )
        self.assertEqual(result.status,"CONTINUOUS / NO_ONOFF_INERTIA_TERM")
        self.assertEqual(result.onoff_inertia_power_kw,0.0)
        self.assertIsNone(result.residual_gap)

    def test_registry_resolves_cdh_mapping_by_method_separation(self):
        reg={r["claim"]:r for r in rows(REG)}
        self.assertEqual(reg["CDH_HOURLY_TEMPERATURE_MAPPING_REQUIRED"]["status"],"RESOLVED_BY_METHOD_SEPARATION_NO_CDH_INTERPOLATION")
        self.assertEqual(reg["HEM_HOURLY_ONOFF_METHOD"]["status"],"QUALIFIED_METHOD_CONTRACT")
        self.assertEqual(reg["HOURLY_ONOFF_TRANSIENT_PARAMETER_AUTHORITY_REQUIRED"]["status"],"OPEN")
        self.assertEqual(reg["Q-B05-004"]["status"],"OPEN_NARROWED_TO_DOMAIN_GAPS_AND_HOURLY_ONOFF_PARAMETERS")

    def test_live_question_preserves_lineage_and_new_residual(self):
        q={r["question_id"]:r for r in rows(QUESTIONS)}["Q-B05-004"]
        self.assertEqual(q["status"],"OPEN")
        for marker in (
            "B05-P15","B05-P16","B05-P17","B05-P18","B05-P19","B05-P20","B05-P21","B05-P22","B05-P23","B05-P24",
            "OPEN_NARROWED_TO_DOMAIN_GAPS_AND_CDH_MAPPING",
            "OPEN_NARROWED_TO_DOMAIN_GAPS_AND_HOURLY_ONOFF_PARAMETERS",
            "RESOLVED_BY_METHOD_SEPARATION_NO_CDH_INTERPOLATION",
        ):
            self.assertIn(marker,q["notes"])

    def test_live_variables_and_formula_keep_runtime_fail_closed(self):
        variables={r["variable_id"]:r for r in rows(VARIABLES)}
        self.assertEqual(variables["VAR-B05-ONOFF-TRANSIENT-TAU-EQ"]["status"],"Q")
        self.assertEqual(variables["VAR-B05-EMITTER-RESPONSE-TIME"]["status"],"Q")
        self.assertEqual(variables["VAR-B05-HOURLY-ONOFF-INERTIA-POWER"]["status"],"Q")
        formulas={r["formula_id"]:r for r in rows(FORMULAS)}
        formula=formulas["FORM-B05-HEM-ONOFF-INERTIA-POWER"]
        self.assertNotIn("CDH",formula["input_variable_ids"].upper())
        self.assertIn("VAR-B05-ONOFF-TRANSIENT-TAU-EQ",formula["input_variable_ids"])

    def test_sources_readiness_and_document_are_bounded(self):
        sources={r["source_id"]:r for r in rows(SOURCES)}
        self.assertIn("SRC-B05-UK-HEM-TP12-HOURLY-ONOFF-2026",sources)
        readiness={r["component_id"]:r for r in rows(READINESS)}
        self.assertEqual(readiness["PART_LOAD_MODULATION"]["readiness_percent"],"45")
        text=PACK.read_text(encoding="utf-8")
        self.assertIn("Cdh is not an input to this hourly equation",text)
        self.assertIn("B05 remains **64%**",text)
        self.assertIn("NO_CDH_TEMPERATURE_INTERPOLATION_FOR_GENERIC_HOURLY_RUNTIME",p24_boundary())
        self.assertIn("TAU_EQ_AND_EMITTER_RESPONSE_TIME_REQUIRE_AUTHORITY",p24_boundary())

if __name__=="__main__":
    unittest.main()
