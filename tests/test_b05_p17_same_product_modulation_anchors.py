import csv
import unittest
from pathlib import Path
from modules.B05.modulation_anchor_contract import ANCHOR_NOT_QUALIFIED,SURFACE_CONTRACT_REQUIRED,ModulationAnchor,classify_at_exact_anchor,p17_boundary,resolve_exact_anchor
from modules.B05.part_load_runtime_contract import CONTINUOUS,CYCLING

ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/"data"/"processed"/"b05_p17_same_product_modulation_anchors.csv"
REG=ROOT/"registry"/"b05_p17_same_product_modulation_anchors.csv"
VARIABLES=ROOT/"registry"/"heat_pump_variables.csv"
READINESS=ROOT/"registry"/"heat_pump_readiness.csv"
QUESTIONS=ROOT/"registry"/"open_questions.csv"
SOURCES=ROOT/"registry"/"heat_pump_sources.csv"
PACK=ROOT/"docs"/"source_packs"/"B05_P17_SAME_PRODUCT_MODULATION_ANCHORS.md"

def rows(path):
    with path.open(encoding="utf-8",newline="") as h: return list(csv.DictReader(h))
def anchors():
    return [ModulationAnchor(r["model_identifier"],float(r["outdoor_temperature_C"]),float(r["supply_temperature_C"]),float(r["min_modulation_kW"]),float(r["max_modulation_kW"]),r["modulation_source_id"]) for r in rows(DATA)]

class B05P17SameProductModulationAnchorTests(unittest.TestCase):
    def test_two_exact_same_product_anchors_are_materialized(self):
        m=rows(DATA); self.assertEqual(len(m),2); b={r["model_identifier"]:r for r in m}
        self.assertEqual(float(b["VWL 85/6 A 230V S3"]["min_modulation_kW"]),3.0)
        self.assertEqual(float(b["VWL 85/6 A 230V S3"]["Cdh_Tj"]),0.95)
        self.assertEqual(float(b["CS5800iAW 4 ORE-S"]["min_modulation_kW"]),1.8)
        self.assertEqual(float(b["CS5800iAW 4 ORE-S"]["Cdh_Tj"]),0.99)
        self.assertTrue(all(r["join_status"]=="EXACT_MODEL_EXACT_A_W_ANCHOR" for r in m))
    def test_exact_anchor_resolution_does_not_interpolate(self):
        exact=resolve_exact_anchor(anchors(),model_identifier="VWL 85/6 A 230V S3",outdoor_temperature_c=7.0,supply_temperature_c=35.0)
        self.assertEqual(exact.status,"EXACT_MODULATION_ANCHOR"); self.assertEqual(exact.anchor.min_modulation_kw,3.0)
        near=resolve_exact_anchor(anchors(),model_identifier="VWL 85/6 A 230V S3",outdoor_temperature_c=6.0,supply_temperature_c=35.0)
        self.assertEqual(near.status,ANCHOR_NOT_QUALIFIED); self.assertEqual(near.residual_gap,SURFACE_CONTRACT_REQUIRED)
    def test_exact_product_identity_is_required(self):
        self.assertEqual(resolve_exact_anchor(anchors(),model_identifier="VWL 65/6 A 230V S3",outdoor_temperature_c=7.0,supply_temperature_c=35.0).status,ANCHOR_NOT_QUALIFIED)
        self.assertEqual(resolve_exact_anchor(anchors(),model_identifier="CS5800iAW 4 ORE-S (60°C)",outdoor_temperature_c=2.0,supply_temperature_c=35.0).status,ANCHOR_NOT_QUALIFIED)
    def test_exact_anchor_can_drive_p16_state_gate_only_at_anchor(self):
        _,cycling=classify_at_exact_anchor(anchors(),model_identifier="CS5800iAW 4 ORE-S",outdoor_temperature_c=2.0,supply_temperature_c=35.0,required_capacity_kw=1.0,available_capacity_kw=4.3)
        self.assertEqual(cycling.state,CYCLING); self.assertFalse(cycling.direct_numeric_cdh_application_allowed)
        _,continuous=classify_at_exact_anchor(anchors(),model_identifier="CS5800iAW 4 ORE-S",outdoor_temperature_c=2.0,supply_temperature_c=35.0,required_capacity_kw=2.0,available_capacity_kw=4.3)
        self.assertEqual(continuous.state,CONTINUOUS)
        missing,state=classify_at_exact_anchor(anchors(),model_identifier="CS5800iAW 4 ORE-S",outdoor_temperature_c=3.0,supply_temperature_c=35.0,required_capacity_kw=1.0,available_capacity_kw=4.3)
        self.assertEqual(missing.status,ANCHOR_NOT_QUALIFIED); self.assertIsNone(state)
    def test_live_question_preserves_lineage_and_narrows(self):
        q={r["question_id"]:r for r in rows(QUESTIONS)}["Q-B05-004"]
        for marker in ("B05-P15","OPEN_NARROWED_TO_RUNTIME_APPLICATION_AND_MODULATION_COVERAGE","B05-P16","OPEN_NARROWED_TO_MIN_MOD_COVERAGE_AND_NUMERIC_CYCLING_METHOD","B05-P17","OPEN_NARROWED_TO_MODULATION_SURFACE_AND_NUMERIC_CYCLING_METHOD"): self.assertIn(marker,q["notes"])
    def test_registry_resolves_anchor_gap_only(self):
        reg={r["claim"]:r for r in rows(REG)}
        self.assertEqual(reg["MULTI_PRODUCT_MIN_MODULATION_COVERAGE_REQUIRED"]["status"],"RESOLVED_FOR_TWO_SAME_PRODUCT_ANCHORS")
        self.assertEqual(reg["MODULATION_FLOOR_SURFACE_OR_INTERPOLATION_CONTRACT_REQUIRED"]["status"],"OPEN")
        self.assertEqual(reg["CYCLING_DEGRADATION_NUMERIC_METHOD_AUTHORITY_REQUIRED"]["status"],"OPEN")
    def test_live_variable_and_readiness_are_bounded(self):
        v={r["variable_id"]:r for r in rows(VARIABLES)}; self.assertEqual(v["VAR-B05-MIN-MODULATION"]["status"],"OBS")
        self.assertEqual({r["component_id"]:r for r in rows(READINESS)}["PART_LOAD_MODULATION"]["readiness_percent"],"45")
        s={r["source_id"]:r for r in rows(SOURCES)}; self.assertIn("SRC-B05-VAILLANT-PLUS-VWL85-MINMAX-2026",s); self.assertIn("SRC-B05-BOSCH-CS5800I-MODULATION-2024",s)
    def test_document_and_contract_keep_residuals_open(self):
        t=PACK.read_text(encoding="utf-8"); self.assertIn("ONE MODULATION ANCHOR != MODULATION SURFACE",t); self.assertIn("CYCLING STATE != NUMERIC CYCLING ENERGY CORRECTION",t); self.assertIn("B05 remains **64%**",t)
        self.assertIn("NO_MIN_MODULATION_INTERPOLATION",p17_boundary()); self.assertIn("NO_MIN_MODULATION_EXTRAPOLATION",p17_boundary())

if __name__=="__main__": unittest.main()
