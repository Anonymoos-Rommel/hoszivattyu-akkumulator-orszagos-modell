import csv
import unittest
from pathlib import Path

from modules.B05.barrier_aware_modulation_floor_surface import (
    MISSING_CORNER,
    SOURCE_GAP_BARRIER,
    BarrierAwareFloorSurface,
    FloorPoint,
    p23_boundary,
)

ROOT=Path(__file__).resolve().parents[1]
GRID=ROOT/"data"/"processed"/"b05_p23_dimplex_modulation_floor_surface.csv"
BINS=ROOT/"data"/"processed"/"b05_p23_dimplex_w35_cycling_bins.csv"
REG=ROOT/"registry"/"b05_p23_dimplex_second_floor_surface.csv"
QUESTIONS=ROOT/"registry"/"open_questions.csv"
VARIABLES=ROOT/"registry"/"heat_pump_variables.csv"
READINESS=ROOT/"registry"/"heat_pump_readiness.csv"
SOURCES=ROOT/"registry"/"heat_pump_sources.csv"
PACK=ROOT/"docs"/"source_packs"/"B05_P23_DIMPLEX_SECOND_MODULATION_FLOOR_SURFACE.md"

def rows(path):
    with path.open(encoding="utf-8",newline="") as h:
        return list(csv.DictReader(h))

def surface():
    return BarrierAwareFloorSurface(
        "LA 2030CP",
        [
            FloorPoint(
                float(r["outdoor_temperature_C"]),
                float(r["supply_temperature_C"]),
                float(r["min_modulation_kW"]),
                r["source_id"],
            )
            for r in rows(GRID)
        ],
        blocked_outdoor_nodes=(-10.0,),
    )

class B05P23DimplexSecondFloorSurfaceTests(unittest.TestCase):
    def test_grid_has_15_exact_source_native_points(self):
        grid=rows(GRID)
        self.assertEqual(len(grid),15)
        self.assertTrue(all(r["evidence_status"]=="OBS" for r in grid))
        self.assertEqual({float(r["supply_temperature_C"]) for r in grid},{35.0,45.0,55.0})

    def test_surface_has_six_complete_nonbarrier_cells(self):
        self.assertEqual(surface().qualified_cell_count(),6)

    def test_cold_cell_interpolates_without_crossing_barrier(self):
        result=surface().evaluate(-20.0,40.0)
        self.assertEqual(result.status,"DER")
        self.assertAlmostEqual(result.minimum_capacity_kw,8.32857142857143,places=12)

    def test_warm_cell_interpolates_without_crossing_barrier(self):
        result=surface().evaluate(0.0,50.0)
        self.assertEqual(result.status,"DER")
        self.assertAlmostEqual(result.minimum_capacity_kw,6.616666666666667,places=12)

    def test_a_minus10_is_explicit_barrier(self):
        exact_gap=surface().evaluate(-10.0,35.0)
        self.assertEqual(exact_gap.status,SOURCE_GAP_BARRIER)
        self.assertIsNone(exact_gap.minimum_capacity_kw)
        self.assertEqual(surface().evaluate(-12.0,40.0).status,MISSING_CORNER)
        self.assertEqual(surface().evaluate(-9.0,40.0).status,MISSING_CORNER)

    def test_p9_stress_endpoints_do_not_cross_gap(self):
        self.assertEqual(surface().evaluate(-13.331944,35.0).status,MISSING_CORNER)
        self.assertEqual(surface().evaluate(-9.644444,45.0).status,MISSING_CORNER)

    def test_three_exact_dimplex_cycling_bins_are_ready(self):
        bins=rows(BINS)
        ready=[r for r in bins if r["runtime_scope"]=="EXACT_TJ_W35_CYCLING_READY"]
        self.assertEqual(len(ready),3)
        self.assertEqual({float(r["outdoor_temperature_C"]) for r in ready},{-7.0,2.0,7.0})
        self.assertTrue(all(float(r["Cdh_Tj"])!=0.9 for r in ready))
        cdh_only=next(r for r in bins if float(r["outdoor_temperature_C"])==12.0)
        self.assertEqual(cdh_only["runtime_scope"],"CDH_ONLY_NO_MINIMUM_POINT")
        self.assertEqual(cdh_only["min_modulation_kW"],"")

    def test_registry_resolves_second_surface_only(self):
        reg={r["claim"]:r for r in rows(REG)}
        self.assertEqual(reg["SECOND_MANUFACTURER_MODULATION_FLOOR_SURFACE_REQUIRED"]["status"],"RESOLVED_FOR_DIMPLEX_LA2030CP_PIECEWISE_SURFACE")
        self.assertEqual(reg["DIMPLEX_A_MINUS10_MINIMUM_ROW_CLASSIFICATION_REQUIRED"]["status"],"OPEN")
        self.assertEqual(reg["MITSUBISHI_COLD_HIGH_SUPPLY_DOMAIN_CLASSIFICATION_REQUIRED"]["status"],"OPEN")
        self.assertEqual(reg["CDH_HOURLY_TEMPERATURE_MAPPING_REQUIRED"]["status"],"OPEN")
        self.assertEqual(reg["Q-B05-004"]["status"],"OPEN_NARROWED_TO_DOMAIN_GAPS_AND_CDH_MAPPING")

    def test_live_question_preserves_lineage(self):
        q={r["question_id"]:r for r in rows(QUESTIONS)}["Q-B05-004"]
        self.assertEqual(q["status"],"OPEN")
        for marker in (
            "B05-P15","B05-P16","B05-P17","B05-P18","B05-P19","B05-P20","B05-P21","B05-P22","B05-P23",
            "OPEN_NARROWED_TO_COLD_HIGH_SUPPLY_CDH_MAPPING_AND_SECOND_SURFACE",
            "OPEN_NARROWED_TO_DOMAIN_GAPS_AND_CDH_MAPPING",
        ):
            self.assertIn(marker,q["notes"])

    def test_live_sources_and_readiness_remain_fail_closed(self):
        variables={r["variable_id"]:r for r in rows(VARIABLES)}
        self.assertEqual(variables["VAR-B05-MODULATION-FLOOR-SURFACE"]["status"],"DER")
        self.assertEqual(variables["VAR-B05-COP-CYCLING-BIN"]["status"],"Q")
        readiness={r["component_id"]:r for r in rows(READINESS)}
        self.assertEqual(readiness["PART_LOAD_MODULATION"]["readiness_percent"],"45")
        sources={r["source_id"]:r for r in rows(SOURCES)}
        self.assertIn("SRC-B05-DIMPLEX-LA2030CP-MIN-SURFACE-2026",sources)
        self.assertIn("SRC-B05-HPKEYMARK-DIMPLEX-LA2030CP-2026",sources)

    def test_document_and_contract_forbid_gap_bridging(self):
        text=PACK.read_text(encoding="utf-8")
        self.assertIn("15-point / 6-cell",text)
        self.assertIn("B05 remains **64%**",text)
        self.assertIn("KNOWN_SOURCE_GAP_IS_INTERPOLATION_BARRIER",p23_boundary())
        self.assertIn("NO_INTERPOLATION_ACROSS_A_MINUS10",p23_boundary())

if __name__=="__main__":
    unittest.main()
