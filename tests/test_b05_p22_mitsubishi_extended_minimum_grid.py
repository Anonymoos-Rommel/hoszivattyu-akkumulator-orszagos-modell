import csv
import unittest
from pathlib import Path

from modules.B05.minimum_point_surface import (
    MISSING_CORNER,
    MinimumPoint,
    MinimumPointSurface,
    p22_boundary,
)

ROOT=Path(__file__).resolve().parents[1]
GRID=ROOT/"data"/"processed"/"b05_p22_mitsubishi_minimum_point_grid.csv"
BINS=ROOT/"data"/"processed"/"b05_p22_mitsubishi_w35_cycling_bins.csv"
P21=ROOT/"data"/"processed"/"b05_p21_mitsubishi_modulation_floor_surface.csv"
REG=ROOT/"registry"/"b05_p22_mitsubishi_extended_minimum_grid.csv"
QUESTIONS=ROOT/"registry"/"open_questions.csv"
VARIABLES=ROOT/"registry"/"heat_pump_variables.csv"
READINESS=ROOT/"registry"/"heat_pump_readiness.csv"
SOURCES=ROOT/"registry"/"heat_pump_sources.csv"
PACK=ROOT/"docs"/"source_packs"/"B05_P22_MITSUBISHI_EXTENDED_MINIMUM_POINT_GRID.md"

def rows(path):
    with path.open(encoding="utf-8",newline="") as h:
        return list(csv.DictReader(h))

def surface():
    return MinimumPointSurface(
        "PUZ-WM50VHA(-BS)",
        [
            MinimumPoint(
                float(r["outdoor_temperature_C"]),
                float(r["supply_temperature_C"]),
                float(r["min_modulation_kW"]),
                float(r["min_point_COP"]),
                r["source_id"],
            )
            for r in rows(GRID)
        ],
    )

class B05P22MitsubishiExtendedMinimumGridTests(unittest.TestCase):
    def test_grid_has_40_exact_source_native_points(self):
        grid=rows(GRID)
        self.assertEqual(len(grid),40)
        self.assertTrue(all(r["evidence_status"]=="OBS" for r in grid))
        self.assertTrue(all(r["source_id"]=="SRC-B05-MITSUBISHI-DATABOOK-WM50-MIN-GRID-2020" for r in grid))

    def test_p21_four_corners_are_reproduced_exactly(self):
        p21={(float(r["outdoor_temperature_C"]),float(r["supply_temperature_C"])):float(r["min_modulation_kW"]) for r in rows(P21)}
        p22={(float(r["outdoor_temperature_C"]),float(r["supply_temperature_C"])):float(r["min_modulation_kW"]) for r in rows(GRID)}
        for key,value in p21.items():
            self.assertIn(key,p22)
            self.assertEqual(p22[key],value)

    def test_surface_has_27_complete_cells(self):
        self.assertEqual(surface().qualified_cell_count(),27)

    def test_core_w55_interpolation_is_bounded(self):
        result=surface().evaluate(-8.5,52.5)
        self.assertEqual(result.status,"DER")
        self.assertEqual(result.interpolation,"bilinear_bounded")
        self.assertAlmostEqual(result.minimum_capacity_kw,1.975,places=12)
        self.assertGreater(result.minimum_cop,0)
        self.assertGreater(result.minimum_input_kw,0)

    def test_cold_shoulder_w45_covers_lower_p9_stress(self):
        result=surface().evaluate(-13.0,42.5)
        self.assertEqual(result.status,"DER")
        self.assertAlmostEqual(result.minimum_capacity_kw,2.23,places=12)

    def test_extreme_shoulder_w35_w40_is_bounded(self):
        result=surface().evaluate(-18.0,37.5)
        self.assertEqual(result.status,"DER")
        self.assertAlmostEqual(result.minimum_capacity_kw,2.10,places=12)

    def test_blank_cold_high_supply_cell_remains_q(self):
        result=surface().evaluate(-13.0,52.5)
        self.assertEqual(result.status,MISSING_CORNER)
        self.assertIsNone(result.minimum_capacity_kw)
        self.assertIsNone(result.minimum_cop)

    def test_p9_stress_w35_w45_full_but_w55_partial(self):
        for outdoor in (-13.331944,-9.644444):
            for supply in (35.0,45.0):
                self.assertEqual(surface().evaluate(outdoor,supply).status,"DER")
        self.assertEqual(surface().evaluate(-9.644444,55.0).status,"DER")
        self.assertEqual(surface().evaluate(-13.331944,55.0).status,MISSING_CORNER)

    def test_four_exact_w35_cdh_bins_are_nondefault_and_colocated(self):
        bins=rows(BINS)
        self.assertEqual(len(bins),4)
        self.assertEqual({float(r["outdoor_temperature_C"]) for r in bins},{-7.0,2.0,7.0,12.0})
        self.assertTrue(all(float(r["Cdh_Tj"])!=0.9 for r in bins))
        self.assertTrue(all(r["runtime_scope"]=="EXACT_TJ_W35_CYCLING_READY" for r in bins))

    def test_registry_narrows_to_three_real_residuals(self):
        reg={r["claim"]:r for r in rows(REG)}
        self.assertEqual(reg["MITSUBISHI_WM50_DATABOOK_MINIMUM_POINT_GRID"]["status"],"QUALIFIED_SOURCE_NATIVE_GRID")
        self.assertEqual(reg["MITSUBISHI_WM50_COMPLETE_BOUNDED_CELLS"]["status"],"QUALIFIED_PIECEWISE_SURFACE")
        self.assertEqual(reg["P9_STRESS_W35_MODULATION_FLOOR_COVERAGE"]["status"],"RESOLVED_FULL_ENVELOPE")
        self.assertEqual(reg["P9_STRESS_W45_MODULATION_FLOOR_COVERAGE"]["status"],"RESOLVED_FULL_ENVELOPE")
        self.assertEqual(reg["P9_STRESS_W55_MODULATION_FLOOR_COVERAGE"]["status"],"PARTIAL_FROM_MINUS10")
        self.assertEqual(reg["MITSUBISHI_COLD_HIGH_SUPPLY_DOMAIN_CLASSIFICATION_REQUIRED"]["status"],"OPEN")
        self.assertEqual(reg["CDH_HOURLY_TEMPERATURE_MAPPING_REQUIRED"]["status"],"OPEN")
        self.assertEqual(reg["SECOND_MANUFACTURER_MODULATION_FLOOR_SURFACE_REQUIRED"]["status"],"OPEN")
        self.assertEqual(reg["Q-B05-004"]["status"],"OPEN_NARROWED_TO_COLD_HIGH_SUPPLY_CDH_MAPPING_AND_SECOND_SURFACE")

    def test_live_question_preserves_lineage(self):
        q={r["question_id"]:r for r in rows(QUESTIONS)}["Q-B05-004"]
        self.assertEqual(q["status"],"OPEN")
        for marker in (
            "B05-P15","B05-P16","B05-P17","B05-P18","B05-P19","B05-P20","B05-P21","B05-P22",
            "OPEN_NARROWED_TO_OUTSIDE_BOUNDED_MODULATION_FLOOR_COVERAGE",
            "OPEN_NARROWED_TO_COLD_HIGH_SUPPLY_CDH_MAPPING_AND_SECOND_SURFACE",
        ):
            self.assertIn(marker,q["notes"])

    def test_live_variables_sources_and_readiness_remain_fail_closed(self):
        variables={r["variable_id"]:r for r in rows(VARIABLES)}
        self.assertEqual(variables["VAR-B05-MINIMUM-POINT-COP-SURFACE"]["status"],"DER")
        self.assertEqual(variables["VAR-B05-COP-CYCLING-BIN"]["status"],"Q")
        readiness={r["component_id"]:r for r in rows(READINESS)}
        self.assertEqual(readiness["PART_LOAD_MODULATION"]["readiness_percent"],"45")
        sources={r["source_id"]:r for r in rows(SOURCES)}
        self.assertIn("SRC-B05-MITSUBISHI-DATABOOK-WM50-MIN-GRID-2020",sources)
        self.assertIn("SRC-B05-MITSUBISHI-ERP-WM50-CDH-2026",sources)

    def test_document_and_contract_keep_blank_cells_and_cdh_mapping_open(self):
        text=PACK.read_text(encoding="utf-8")
        self.assertIn("40 exact OBS points",text)
        self.assertIn("27 complete bounded cells",text)
        self.assertIn("B05 remains **64%**",text)
        self.assertIn("BLANK_SOURCE_CELL_REMAINS_Q",p22_boundary())
        self.assertIn("NO_CDH_INTERPOLATION_IN_THIS_CONTRACT",p22_boundary())

if __name__=="__main__":
    unittest.main()
