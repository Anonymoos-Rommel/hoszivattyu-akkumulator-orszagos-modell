import csv
import unittest
from pathlib import Path

from modules.B05.cycling_degradation_method import (
    MINIMUM_CAPACITY_COP_INPUT_REQUIRED,
    QUALIFIED,
    evaluate_below_minimum_modulation,
    p18_boundary,
    water_side_cycling_cop,
)

ROOT=Path(__file__).resolve().parents[1]
GAP=ROOT/"data"/"processed"/"b05_p18_cycling_input_gap.csv"
REG=ROOT/"registry"/"b05_p18_cycling_numeric_method.csv"
QUESTIONS=ROOT/"registry"/"open_questions.csv"
VARIABLES=ROOT/"registry"/"heat_pump_variables.csv"
READINESS=ROOT/"registry"/"heat_pump_readiness.csv"
FORMULAS=ROOT/"registry"/"heat_pump_formulas.csv"
PACK=ROOT/"docs"/"source_packs"/"B05_P18_EN14825_CYCLING_NUMERIC_METHOD.md"

def rows(path):
    with path.open(encoding="utf-8",newline="") as h: return list(csv.DictReader(h))

class B05P18CyclingNumericMethodTests(unittest.TestCase):
    def test_water_side_formula_matches_published_example(self):
        cr=0.7375
        value=water_side_cycling_cop(3.0,cr,0.9)
        self.assertAlmostEqual(value,2.8968903436988547,places=12)
    def test_capacity_ratio_one_returns_declared_cop(self):
        self.assertAlmostEqual(water_side_cycling_cop(4.2,1.0,0.95),4.2)
    def test_product_cop_capacity_must_match_cycling_capacity(self):
        vaillant=evaluate_below_minimum_modulation(required_capacity_kw=1.5,cycling_capacity_kw=3.0,cdh=0.95,cop_declared=6.33,cop_capacity_kw=3.21)
        self.assertIsNone(vaillant.cop_bin); self.assertEqual(vaillant.residual_gap,MINIMUM_CAPACITY_COP_INPUT_REQUIRED)
        bosch=evaluate_below_minimum_modulation(required_capacity_kw=1.0,cycling_capacity_kw=1.8,cdh=0.99,cop_declared=3.21,cop_capacity_kw=4.31)
        self.assertIsNone(bosch.cop_bin); self.assertEqual(bosch.residual_gap,MINIMUM_CAPACITY_COP_INPUT_REQUIRED)
    def test_qualified_evaluation_requires_capacity_matched_cop(self):
        result=evaluate_below_minimum_modulation(required_capacity_kw=1.5,cycling_capacity_kw=3.0,cdh=0.95,cop_declared=5.0,cop_capacity_kw=3.0)
        self.assertEqual(result.status,QUALIFIED); self.assertAlmostEqual(result.capacity_ratio,0.5); self.assertIsNotNone(result.cop_bin)
        self.assertLess(result.cop_bin,5.0)
    def test_gap_table_records_both_current_products_as_q(self):
        gap=rows(GAP); self.assertEqual(len(gap),2)
        self.assertTrue(all(r["cop_capacity_matches_cycling_capacity"]=="false" for r in gap))
        self.assertTrue(all(r["residual_gap"]==MINIMUM_CAPACITY_COP_INPUT_REQUIRED for r in gap))
    def test_registry_resolves_method_authority_only(self):
        reg={r["claim"]:r for r in rows(REG)}
        self.assertEqual(reg["CYCLING_DEGRADATION_NUMERIC_METHOD_AUTHORITY_REQUIRED"]["status"],"RESOLVED_EN14825_WATER_SIDE_FORMULA")
        self.assertEqual(reg["MINIMUM_CAPACITY_COP_INPUT_REQUIRED"]["status"],"OPEN")
        self.assertEqual(reg["Q-B05-004"]["status"],"OPEN_NARROWED_TO_MODULATION_SURFACE_AND_MIN_CAPACITY_COP_INPUT")
    def test_live_question_preserves_lineage(self):
        q={r["question_id"]:r for r in rows(QUESTIONS)}["Q-B05-004"]
        for marker in ("B05-P15","B05-P16","B05-P17","B05-P18","OPEN_NARROWED_TO_MODULATION_SURFACE_AND_MIN_CAPACITY_COP_INPUT"):
            self.assertIn(marker,q["notes"])
    def test_live_variable_formula_and_readiness_are_fail_closed(self):
        v={r["variable_id"]:r for r in rows(VARIABLES)}
        self.assertEqual(v["VAR-B05-COP-AT-CYCLING-CAPACITY"]["status"],"Q")
        self.assertEqual(v["VAR-B05-COP-CYCLING-BIN"]["status"],"Q")
        f={r["formula_id"]:r for r in rows(FORMULAS)}
        self.assertIn("FORM-B05-EN14825-WATER-CYCLING-COP",f)
        self.assertEqual({r["component_id"]:r for r in rows(READINESS)}["PART_LOAD_MODULATION"]["readiness_percent"],"45")
    def test_document_and_boundary_forbid_shortcuts(self):
        t=PACK.read_text(encoding="utf-8")
        self.assertIn("NOMINAL COP != COP AT MINIMUM CAPACITY",t)
        self.assertIn("B05 remains **64%**",t)
        self.assertIn("NO_DIRECT_COP_TIMES_CDH",p18_boundary())
        self.assertIn("COPD_CAPACITY_MUST_EQUAL_CYCLING_CAPACITY",p18_boundary())

if __name__=="__main__": unittest.main()
