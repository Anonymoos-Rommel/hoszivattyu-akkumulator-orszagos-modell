import csv
import unittest
from pathlib import Path

from modules.B05.cycling_input_colocation import (
    MEASUREMENT_DETERMINED,
    POINT_PAIRED_MINIMUM_CAPACITY_COP_REQUIRED,
    PRODUCT_CDH_MEASUREMENT_STATUS_REQUIRED,
    QUALIFIED,
    assess_cycling_input_colocation,
    derive_cop_from_capacity_input,
    p19_boundary,
)

ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/"data"/"processed"/"b05_p19_cycling_input_coverage.csv"
REG=ROOT/"registry"/"b05_p19_cycling_input_colocation_gate.csv"
QUESTIONS=ROOT/"registry"/"open_questions.csv"
VARIABLES=ROOT/"registry"/"heat_pump_variables.csv"
READINESS=ROOT/"registry"/"heat_pump_readiness.csv"
SOURCES=ROOT/"registry"/"heat_pump_sources.csv"
PACK=ROOT/"docs"/"source_packs"/"B05_P19_CYCLING_INPUT_COLOCATION_GATE.md"

def rows(path):
    with path.open(encoding="utf-8",newline="") as h: return list(csv.DictReader(h))

class B05P19CyclingInputColocationTests(unittest.TestCase):
    def test_range_endpoints_cannot_be_divided_without_pairing_authority(self):
        self.assertIsNone(derive_cop_from_capacity_input(capacity_kw=3.4,input_kw=0.74,point_pairing_explicit=False))
        self.assertAlmostEqual(derive_cop_from_capacity_input(capacity_kw=3.4,input_kw=0.74,point_pairing_explicit=True),3.4/0.74)
    def test_vaillant_and_bosch_require_point_paired_minimum_cop(self):
        result=assess_cycling_input_colocation(exact_modulation_floor=True,point_paired_minimum_capacity_cop=False,cdh_status=MEASUREMENT_DETERMINED)
        self.assertIn(POINT_PAIRED_MINIMUM_CAPACITY_COP_REQUIRED,result.residual_gaps)
        self.assertNotIn(PRODUCT_CDH_MEASUREMENT_STATUS_REQUIRED,result.residual_gaps)
    def test_exact_default_cdh_remains_fail_closed(self):
        result=assess_cycling_input_colocation(exact_modulation_floor=True,point_paired_minimum_capacity_cop=False,cdh_status="AMBIGUOUS_EXACT_DEFAULT_0_9")
        self.assertIn(POINT_PAIRED_MINIMUM_CAPACITY_COP_REQUIRED,result.residual_gaps)
        self.assertIn(PRODUCT_CDH_MEASUREMENT_STATUS_REQUIRED,result.residual_gaps)
    def test_synthetic_fully_colocated_point_can_qualify(self):
        result=assess_cycling_input_colocation(exact_modulation_floor=True,point_paired_minimum_capacity_cop=True,cdh_status=MEASUREMENT_DETERMINED)
        self.assertEqual(result.status,QUALIFIED); self.assertEqual(result.residual_gaps,())
    def test_materialized_coverage_keeps_all_three_products_not_ready(self):
        data=rows(DATA); self.assertEqual(len(data),3)
        self.assertTrue(all(r["runtime_ready"]=="false" for r in data))
        amit=next(r for r in data if r["model_identifier"]=="PAVH-06V1FXC")
        self.assertEqual(amit["point_pair_status"],"NOT_EXPLICITLY_POINT_PAIRED")
        self.assertEqual(amit["cdh_status"],"AMBIGUOUS_EXACT_DEFAULT_0_9")
    def test_registry_narrows_but_does_not_resolve_input_gap(self):
        reg={r["claim"]:r for r in rows(REG)}
        self.assertEqual(reg["MINIMUM_CAPACITY_COP_INPUT_REQUIRED"]["status"],"NARROWED_TO_POINT_PAIRED_MINIMUM_CAPACITY_COP_REQUIRED")
        self.assertEqual(reg["CYCLING_INPUT_COLOCATION_GATE"]["status"],"OPEN")
        self.assertEqual(reg["Q-B05-004"]["status"],"OPEN_NARROWED_TO_MODULATION_SURFACE_AND_POINT_PAIRED_MIN_CAPACITY_COP")
    def test_live_question_preserves_p15_to_p19_lineage(self):
        q={r["question_id"]:r for r in rows(QUESTIONS)}["Q-B05-004"]
        for marker in ("B05-P15","B05-P16","B05-P17","B05-P18","OPEN_NARROWED_TO_MODULATION_SURFACE_AND_MIN_CAPACITY_COP_INPUT","B05-P19","OPEN_NARROWED_TO_MODULATION_SURFACE_AND_POINT_PAIRED_MIN_CAPACITY_COP"):
            self.assertIn(marker,q["notes"])
    def test_live_registry_remains_fail_closed(self):
        v={r["variable_id"]:r for r in rows(VARIABLES)}
        self.assertEqual(v["VAR-B05-COP-AT-CYCLING-CAPACITY"]["status"],"Q")
        self.assertEqual(v["VAR-B05-CYCLING-INPUT-COLOCATION"]["status"],"Q")
        self.assertEqual({r["component_id"]:r for r in rows(READINESS)}["PART_LOAD_MODULATION"]["readiness_percent"],"45")
        s={r["source_id"]:r for r in rows(SOURCES)}
        self.assertEqual(s["SRC-B05-AMITIME-PAVH06-DISTRIBUTOR-RANGE-2026"]["source_tier"],"P3")
        self.assertIn("SRC-B05-HPKEYMARK-AMITIME-PAVH06-2026",s)
    def test_document_and_boundary_preserve_no_shortcuts(self):
        t=PACK.read_text(encoding="utf-8")
        self.assertIn("RANGE CO-PUBLICATION != POINT PAIRING",t)
        self.assertIn("B05 remains **64%**",t)
        self.assertIn("NO_RANGE_ENDPOINT_DIVISION_WITHOUT_PAIRING_AUTHORITY",p19_boundary())
        self.assertIn("NO_CROSS_PRODUCT_ASSEMBLY",p19_boundary())

if __name__=="__main__": unittest.main()
