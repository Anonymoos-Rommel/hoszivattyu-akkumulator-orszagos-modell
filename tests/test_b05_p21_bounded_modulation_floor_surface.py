import csv
import unittest
from pathlib import Path

from modules.B05.engine import PerformanceMap, PerformancePoint
from modules.B05.modulation_floor_surface import (
    OUTSIDE_SURFACE,
    ModulationFloorPoint,
    ModulationFloorSurface,
    p21_boundary,
)

ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/"data"/"processed"/"b05_p21_mitsubishi_modulation_floor_surface.csv"
REG=ROOT/"registry"/"b05_p21_modulation_floor_surface.csv"
QUESTIONS=ROOT/"registry"/"open_questions.csv"
VARIABLES=ROOT/"registry"/"heat_pump_variables.csv"
READINESS=ROOT/"registry"/"heat_pump_readiness.csv"
SOURCES=ROOT/"registry"/"heat_pump_sources.csv"
PACK=ROOT/"docs"/"source_packs"/"B05_P21_BOUNDED_MODULATION_FLOOR_SURFACE.md"

def rows(path):
    with path.open(encoding="utf-8",newline="") as handle:
        return list(csv.DictReader(handle))

def surface():
    return ModulationFloorSurface(
        "PUZ-WM50VHA",
        [
            ModulationFloorPoint(float(r["outdoor_temperature_C"]),float(r["supply_temperature_C"]),float(r["min_modulation_kW"]),r["source_id"])
            for r in rows(DATA)
        ],
    )

class B05P21BoundedModulationFloorSurfaceTests(unittest.TestCase):
    def test_four_source_native_corners_are_exact(self):
        data=rows(DATA)
        self.assertEqual(len(data),4)
        expected={(2.0,35.0):2.5,(2.0,45.0):2.5,(7.0,35.0):1.8,(7.0,45.0):1.3}
        actual={(float(r["outdoor_temperature_C"]),float(r["supply_temperature_C"])):float(r["min_modulation_kW"]) for r in data}
        self.assertEqual(actual,expected)
        self.assertTrue(all(r["evidence_status"]=="OBS" for r in data))

    def test_bounded_surface_uses_coordinate_weighted_bilinear_der(self):
        result=surface().evaluate(3.0,40.0)
        self.assertEqual(result.status,"DER")
        self.assertEqual(result.interpolation,"bilinear_bounded")
        self.assertAlmostEqual(result.minimum_capacity_kw,2.31,places=12)
        self.assertNotAlmostEqual(result.minimum_capacity_kw,(2.5+2.5+1.8+1.3)/4,places=6)

    def test_exact_corner_remains_obs_and_outside_is_q(self):
        exact=surface().evaluate(7.0,45.0)
        self.assertEqual(exact.status,"OBS")
        self.assertAlmostEqual(exact.minimum_capacity_kw,1.3)
        outside=surface().evaluate(1.9,40.0)
        self.assertEqual(outside.status,OUTSIDE_SURFACE)
        self.assertIsNone(outside.minimum_capacity_kw)
        self.assertEqual(surface().evaluate(3.0,45.1).status,OUTSIDE_SURFACE)

    def test_engine_bilinear_minimum_is_not_unweighted_corner_average(self):
        points=[
            PerformancePoint(2,35,5,1,5,2.5,evidence_status="OBS",source_id="A"),
            PerformancePoint(7,35,5,1,5,1.8,evidence_status="OBS",source_id="B"),
            PerformancePoint(2,45,5,1,5,2.5,evidence_status="OBS",source_id="C"),
            PerformancePoint(7,45,5,1,5,1.3,evidence_status="OBS",source_id="D"),
        ]
        result=PerformanceMap("TEST","air_to_water",points).evaluate(3,40)
        self.assertEqual(result.status,"DER")
        self.assertAlmostEqual(result.point.min_modulation_kw,2.31,places=12)
        self.assertEqual(result.point.interpolation,"bilinear_bounded")

    def test_engine_cold_boundary_floor_uses_coordinate_weight(self):
        points=[
            PerformancePoint(-15,35,4,1,4,3.0,evidence_status="OBS",source_id="A"),
            PerformancePoint(-7,35,5,1,5,1.0,evidence_status="OBS",source_id="B"),
            PerformancePoint(-7,45,4,1,4,1.2,evidence_status="OBS",source_id="C"),
        ]
        result=PerformanceMap("TEST","air_to_water",points).evaluate(-13,35)
        self.assertEqual(result.status,"DER")
        self.assertEqual(result.point.interpolation,"bounded_axis_linear")
        self.assertAlmostEqual(result.point.min_modulation_kw,2.5,places=12)

    def test_registry_resolves_prior_surface_blocker_bounded_only(self):
        reg={r["claim"]:r for r in rows(REG)}
        self.assertEqual(
            reg["MODULATION_FLOOR_SURFACE_OR_INTERPOLATION_CONTRACT_REQUIRED"]["status"],
            "RESOLVED_FOR_BOUNDED_MITSUBISHI_A2_A7_W35_W45_RECTANGLE",
        )
        self.assertEqual(
            reg["MODULATION_FLOOR_COVERAGE_OUTSIDE_MITSUBISHI_A2_A7_W35_W45_REQUIRED"]["status"],
            "OPEN",
        )
        self.assertEqual(
            reg["Q-B05-004"]["status"],
            "OPEN_NARROWED_TO_OUTSIDE_BOUNDED_MODULATION_FLOOR_COVERAGE",
        )

    def test_live_question_preserves_lineage_and_remains_open(self):
        q={r["question_id"]:r for r in rows(QUESTIONS)}["Q-B05-004"]
        self.assertEqual(q["status"],"OPEN")
        for marker in (
            "B05-P15","B05-P16","B05-P17","B05-P18","B05-P19","B05-P20","B05-P21",
            "OPEN_NARROWED_TO_MODULATION_FLOOR_SURFACE_ONLY",
            "OPEN_NARROWED_TO_OUTSIDE_BOUNDED_MODULATION_FLOOR_COVERAGE",
        ):
            self.assertIn(marker,q["notes"])

    def test_live_variable_sources_and_readiness_are_bounded(self):
        variables={r["variable_id"]:r for r in rows(VARIABLES)}
        self.assertEqual(variables["VAR-B05-MODULATION-FLOOR-SURFACE"]["status"],"DER")
        readiness={r["component_id"]:r for r in rows(READINESS)}
        self.assertEqual(readiness["PART_LOAD_MODULATION"]["readiness_percent"],"45")
        sources={r["source_id"]:r for r in rows(SOURCES)}
        self.assertIn("SRC-B05-MITSUBISHI-ECODAN-PLAN-MINFLOOR-2021",sources)
        self.assertIn("SRC-B05-MITSUBISHI-SE-WM50-A7W45-2026",sources)

    def test_document_and_boundaries_forbid_global_promotion(self):
        text=PACK.read_text(encoding="utf-8")
        self.assertIn("ONE BOUNDED RECTANGLE != GLOBAL PRODUCT SURFACE",text)
        self.assertIn("B05 remains **64%**",text)
        self.assertIn("NO_MODULATION_FLOOR_EXTRAPOLATION",p21_boundary())
        self.assertIn("COORDINATE_WEIGHTED_NOT_UNWEIGHTED_AVERAGE",p21_boundary())

if __name__=="__main__":
    unittest.main()
