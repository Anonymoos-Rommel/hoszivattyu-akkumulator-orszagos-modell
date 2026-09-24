import csv
import unittest
from pathlib import Path

from modules.B05.cycling_input_colocation import MEASUREMENT_DETERMINED, QUALIFIED, assess_cycling_input_colocation
from modules.B05.qualified_cycling_point import (
    QUALIFIED_POINT,
    QualifiedCyclingPoint,
    evaluate_exact_cycling_point,
    p20_boundary,
)

ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/"data"/"processed"/"b05_p20_qualified_cycling_ready_point.csv"
REG=ROOT/"registry"/"b05_p20_qualified_cycling_ready_point.csv"
QUESTIONS=ROOT/"registry"/"open_questions.csv"
VARIABLES=ROOT/"registry"/"heat_pump_variables.csv"
READINESS=ROOT/"registry"/"heat_pump_readiness.csv"
SOURCES=ROOT/"registry"/"heat_pump_sources.csv"
PACK=ROOT/"docs"/"source_packs"/"B05_P20_QUALIFIED_CYCLING_READY_POINT.md"

def rows(path):
    with path.open(encoding="utf-8",newline="") as h:
        return list(csv.DictReader(h))

def point():
    return QualifiedCyclingPoint(
        manufacturer_model_identifier="PUZ-WM50VHA",
        certified_model_identifier="PUZ-WM50VHA(-BS)",
        outdoor_temperature_c=7.0,
        supply_temperature_c=35.0,
        minimum_capacity_kw=1.80,
        minimum_input_kw=0.33,
        declared_minimum_cop=5.46,
        cdh=0.950,
        cdh_status=MEASUREMENT_DETERMINED,
        identity_correlated=True,
        point_pairing_explicit=True,
    )

class B05P20QualifiedCyclingReadyPointTests(unittest.TestCase):
    def test_materialized_point_is_exact_and_runtime_ready(self):
        data=rows(DATA)
        self.assertEqual(len(data),1)
        row=data[0]
        self.assertEqual(row["manufacturer_model_identifier"],"PUZ-WM50VHA")
        self.assertEqual(row["certified_model_identifier"],"PUZ-WM50VHA(-BS)")
        self.assertEqual(float(row["min_capacity_kW"]),1.80)
        self.assertEqual(float(row["min_input_kW"]),0.33)
        self.assertEqual(float(row["declared_min_COP"]),5.46)
        self.assertEqual(float(row["cdh_Tj"]),0.950)
        self.assertEqual(row["runtime_ready"],"true")

    def test_minimum_point_cop_is_rounding_consistent(self):
        p=point()
        p.validate()
        self.assertAlmostEqual(p.minimum_capacity_kw/p.minimum_input_kw,5.4545454545,places=9)
        self.assertLess(abs(p.minimum_capacity_kw/p.minimum_input_kw-p.declared_minimum_cop),0.05)

    def test_p19_colocation_gate_now_qualifies_for_exact_point(self):
        result=assess_cycling_input_colocation(
            exact_modulation_floor=True,
            point_paired_minimum_capacity_cop=True,
            cdh_status=MEASUREMENT_DETERMINED,
        )
        self.assertEqual(result.status,QUALIFIED)
        self.assertEqual(result.residual_gaps,())

    def test_exact_point_can_execute_p18_cycling_method(self):
        result=evaluate_exact_cycling_point(point(),required_capacity_kw=0.90)
        self.assertEqual(result.status,QUALIFIED_POINT)
        self.assertAlmostEqual(result.capacity_ratio,0.5)
        self.assertAlmostEqual(result.cop_bin,5.20,places=10)
        self.assertAlmostEqual(result.electrical_input_kw,0.90/5.20,places=10)

    def test_exact_point_rejects_non_cycling_load(self):
        with self.assertRaises(ValueError):
            evaluate_exact_cycling_point(point(),required_capacity_kw=1.80)
        with self.assertRaises(ValueError):
            evaluate_exact_cycling_point(point(),required_capacity_kw=2.00)

    def test_registry_closes_point_pair_and_colocation_only(self):
        reg={r["claim"]:r for r in rows(REG)}
        self.assertEqual(reg["POINT_PAIRED_MINIMUM_CAPACITY_COP_REQUIRED"]["status"],"RESOLVED_FOR_QUALIFIED_MITSUBISHI_A7_W35_POINT")
        self.assertEqual(reg["CYCLING_INPUT_COLOCATION_GATE"]["status"],"RESOLVED_FOR_ONE_EXACT_CURRENT_PRODUCT_POINT")
        self.assertEqual(reg["MODULATION_FLOOR_SURFACE_OR_INTERPOLATION_CONTRACT_REQUIRED"]["status"],"OPEN")
        self.assertEqual(reg["Q-B05-004"]["status"],"OPEN_NARROWED_TO_MODULATION_FLOOR_SURFACE_ONLY")

    def test_live_question_preserves_p15_to_p20_lineage(self):
        q={r["question_id"]:r for r in rows(QUESTIONS)}["Q-B05-004"]
        for marker in (
            "B05-P15","B05-P16","B05-P17","B05-P18","B05-P19",
            "OPEN_NARROWED_TO_MODULATION_SURFACE_AND_POINT_PAIRED_MIN_CAPACITY_COP",
            "B05-P20","OPEN_NARROWED_TO_MODULATION_FLOOR_SURFACE_ONLY",
        ):
            self.assertIn(marker,q["notes"])

    def test_generic_variables_remain_fail_closed_outside_exact_point(self):
        v={r["variable_id"]:r for r in rows(VARIABLES)}
        self.assertEqual(v["VAR-B05-COP-AT-CYCLING-CAPACITY"]["status"],"Q")
        self.assertEqual(v["VAR-B05-COP-CYCLING-BIN"]["status"],"Q")
        self.assertEqual(v["VAR-B05-CYCLING-INPUT-COLOCATION"]["status"],"Q")
        self.assertEqual({r["component_id"]:r for r in rows(READINESS)}["PART_LOAD_MODULATION"]["readiness_percent"],"45")

    def test_sources_and_document_are_bounded(self):
        s={r["source_id"]:r for r in rows(SOURCES)}
        for source_id in (
            "SRC-B05-MITSUBISHI-PUZ-WM-MINNOMMAX-2024",
            "SRC-B05-MITSUBISHI-PUZ-WM50-OPTIONAL-BS-ID-2026",
            "SRC-B05-HPKEYMARK-MITSUBISHI-WM50-2026",
        ):
            self.assertIn(source_id,s)
        text=PACK.read_text(encoding="utf-8")
        self.assertIn("ONE_QUALIFIED_POINT_IS_NOT_A_SURFACE",p20_boundary())
        self.assertIn("B05 remains **64%**",text)
        self.assertIn("OPEN_NARROWED_TO_MODULATION_FLOOR_SURFACE_ONLY",text)

if __name__=="__main__":
    unittest.main()
