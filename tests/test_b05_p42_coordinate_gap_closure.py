import csv
import unittest
from pathlib import Path

from modules.B05.barrier_aware_modulation_floor_surface import (
    BarrierAwareFloorSurface,
    FloorPoint,
)
from modules.B05.coordinate_gap_closure import (
    DIMPLEX_A_MINUS10_MINIMUM_POINTS,
    DIMPLEX_CURRENT_CELL_COUNT,
    DIMPLEX_CURRENT_POINT_COUNT,
    DIMPLEX_CURRENT_REVISION,
    MITSUBISHI_A_MINUS15_W50_CLASSIFICATION,
    p42_boundary,
    validate_dimplex_a_minus10_points,
)

ROOT=Path(__file__).resolve().parents[1]
P42=ROOT/"data"/"processed"/"b05_p42_coordinate_gap_closure.csv"
REG=ROOT/"registry"/"b05_p42_coordinate_gap_closure.csv"
QUESTIONS=ROOT/"registry"/"open_questions.csv"
READINESS=ROOT/"registry"/"heat_pump_readiness.csv"
SOURCES=ROOT/"registry"/"heat_pump_sources.csv"
PACK=ROOT/"docs"/"source_packs"/"B05_P42_COORDINATE_GAP_CLOSURE.md"

def rows(path):
    with path.open(encoding="utf-8",newline="") as h:
        return list(csv.DictReader(h))

class B05P42CoordinateGapClosureTests(unittest.TestCase):
    def test_current_dimplex_grid_is_complete_and_revision_coherent(self):
        self.assertEqual(DIMPLEX_CURRENT_REVISION,"SYSTEM_C_VERSION_03_2026")
        data=[r for r in rows(P42) if r["model_identifier"]=="LA 2030CP"]
        self.assertEqual(len(data),DIMPLEX_CURRENT_POINT_COUNT)
        self.assertEqual(len(data),30)
        self.assertTrue(all(r["evidence_status"]=="OBS" for r in data))
        self.assertEqual({float(r["supply_temperature_C"]) for r in data},{35.0,45.0,55.0})
        self.assertEqual(
            {float(r["outdoor_temperature_C"]) for r in data},
            {-22.0,-15.0,-10.0,-7.0,2.0,7.0,12.0,20.0,30.0,40.0},
        )
        a7w35=next(r for r in data if r["outdoor_temperature_C"]=="7" and r["supply_temperature_C"]=="35")
        self.assertEqual((a7w35["min_capacity_kW"],a7w35["min_COP"]),("7.72","5.49"))

    def test_exact_dimplex_a_minus10_row(self):
        validate_dimplex_a_minus10_points()
        data=[r for r in rows(P42) if r["model_identifier"]=="LA 2030CP" and r["outdoor_temperature_C"]=="-10"]
        self.assertEqual(len(data),3)
        got={float(r["supply_temperature_C"]):(float(r["min_capacity_kW"]),float(r["min_input_kW"]),float(r["min_COP"])) for r in data}
        expected={k:(v["minimum_capacity_kw"],v["minimum_input_kw"],v["minimum_cop"]) for k,v in DIMPLEX_A_MINUS10_MINIMUM_POINTS.items()}
        self.assertEqual(got,expected)

    def test_current_surface_has_eighteen_cells_and_full_p9_coverage(self):
        data=[r for r in rows(P42) if r["model_identifier"]=="LA 2030CP"]
        points=[
            FloorPoint(
                float(r["outdoor_temperature_C"]),
                float(r["supply_temperature_C"]),
                float(r["min_capacity_kW"]),
                r["source_id"],
            )
            for r in data
        ]
        surface=BarrierAwareFloorSurface("LA 2030CP",points)
        self.assertEqual(surface.qualified_cell_count(),DIMPLEX_CURRENT_CELL_COUNT)
        self.assertEqual(DIMPLEX_CURRENT_CELL_COUNT,18)
        for outdoor in (-13.331944,-9.644444):
            for supply in (35.0,45.0,55.0):
                result=surface.evaluate(outdoor,supply)
                self.assertEqual(result.status,"DER")
                self.assertIsNotNone(result.minimum_capacity_kw)

    def test_mitsubishi_persistent_blank_remains_q(self):
        self.assertEqual(
            MITSUBISHI_A_MINUS15_W50_CLASSIFICATION,
            "Q_PERSISTENT_ALL_LEVELS_BLANK_EXACT_THRESHOLD_NOT_PUBLISHED",
        )
        m=[r for r in rows(P42) if r["model_identifier"]=="PUZ-WM50VHA(-BS)"]
        self.assertEqual(len(m),1)
        self.assertEqual(m[0]["classification"],MITSUBISHI_A_MINUS15_W50_CLASSIFICATION)
        self.assertEqual(m[0]["evidence_status"],"Q")
        self.assertEqual(m[0]["min_capacity_kW"],"")

    def test_registry_question_and_readiness_narrow_without_false_closure(self):
        reg={r["claim"]:r for r in rows(REG)}
        self.assertEqual(reg["DIMPLEX_A_MINUS10_MINIMUM_ROW_CLASSIFICATION_REQUIRED"]["status"],"RESOLVED_BY_CURRENT_REVISION_FULL_SURFACE")
        self.assertEqual(reg["DIMPLEX_P23_CURRENT_USE_SURFACE"]["status"],"SUPERSEDED_BY_CURRENT_DETAILED_REVISION")
        self.assertEqual(reg["MITSUBISHI_A_MINUS15_W50_MINIMUM_CLASSIFICATION_REQUIRED"]["status"],"OPEN_BOUNDED_PERSISTENT_ALL_LEVELS_BLANK")
        q={r["question_id"]:r for r in rows(QUESTIONS)}["Q-B05-004"]
        self.assertEqual(q["status"],"OPEN")
        self.assertIn("B05-P42",q["notes"])
        readiness={r["component_id"]:r for r in rows(READINESS)}
        self.assertEqual(readiness["PART_LOAD_MODULATION"]["readiness_percent"],"45")

    def test_sources_boundaries_and_document(self):
        sources={r["source_id"]:r for r in rows(SOURCES)}
        self.assertIn("SRC-B05-DIMPLEX-LA2030CP-DETAILED-MIN-SURFACE-2026",sources)
        self.assertIn("SRC-B05-MITSUBISHI-DATABOOK-WM50-GAP-RECHECK-2026",sources)
        bounds=p42_boundary()
        self.assertIn("NO_CROSS_VERSION_MIXING_WITH_P23",bounds)
        self.assertIn("NO_GRAPH_DIGITIZATION",bounds)
        self.assertIn("MITSUBISHI_PERSISTENT_BLANK_IS_NOT_PHYSICAL_IMPOSSIBILITY",bounds)
        text=PACK.read_text(encoding="utf-8")
        self.assertIn("30 exact OBS points",text)
        self.assertIn("18 complete adjacent rectangular cells",text)
        self.assertIn("B05 remains **64%**",text)

if __name__=="__main__":
    unittest.main()
