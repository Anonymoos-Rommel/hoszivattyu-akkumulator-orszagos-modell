import csv
import unittest
from pathlib import Path

from modules.B02.non_ekr_window_performance_calibration import (
    InvertWindowArchetype,
    INVERT_EXTRACT_RESIDUAL,
    OBS_BRIDGE_RESIDUAL,
    EKR_OVERLAP_RESIDUAL,
    PRIMARY_NEXT_RESIDUAL,
    SUPERSEDED_SUB_BLOCKER,
    can_promote_invert_to_population_calibration,
    p106_state,
    semantic_boundaries,
    summarize_by_renovation_generation,
)

ROOT = Path(__file__).resolve().parents[1]

def rows(path, key):
    with path.open(encoding="utf-8", newline="") as h:
        return {r[key]: r for r in csv.DictReader(h)}

class P106Tests(unittest.TestCase):
    def test_effective_u_and_weighting(self):
        data = [
            InvertWindowArchetype("HUN",2025,"A gen2","gen2",10.0,10.0,100.0,1.0),
            InvertWindowArchetype("HUN",2025,"B gen2","gen2",20.0,30.0,50.0,2.0),
            InvertWindowArchetype("HUN",2025,"C gen3","gen3",10.0,8.0,25.0,1.0),
        ]
        s = {x.generation:x for x in summarize_by_renovation_generation(data)}
        self.assertAlmostEqual(s["gen2"].dwelling_weight,200.0)
        self.assertAlmostEqual(s["gen2"].weighted_mean_effective_u_w_m2k,1.25)
        self.assertAlmostEqual(s["gen2"].model_share_at_or_below_1_10,0.5)
        self.assertAlmostEqual(s["gen3"].weighted_mean_effective_u_w_m2k,0.8)

    def test_fail_closed_country_and_year(self):
        with self.assertRaises(ValueError):
            summarize_by_renovation_generation([
                InvertWindowArchetype("AUT",2025,"x","gen2",10,10,1,1)
            ])
        with self.assertRaises(ValueError):
            summarize_by_renovation_generation([
                InvertWindowArchetype("HUN",2030,"x","gen2",10,10,1,1)
            ])

    def test_population_promotion_gate(self):
        ok, blockers = can_promote_invert_to_population_calibration(
            hun_extract_complete_for_declared_scope=False,
            renovation_generation_semantics_explicit=True,
            observed_replacement_state_bridge=False,
            ekr_overlap_explicit_or_bounded=False,
        )
        self.assertFalse(ok)
        self.assertIn(INVERT_EXTRACT_RESIDUAL, blockers)
        self.assertIn(OBS_BRIDGE_RESIDUAL, blockers)
        self.assertIn(EKR_OVERLAP_RESIDUAL, blockers)
        ok2, blockers2 = can_promote_invert_to_population_calibration(
            hun_extract_complete_for_declared_scope=True,
            renovation_generation_semantics_explicit=True,
            observed_replacement_state_bridge=True,
            ekr_overlap_explicit_or_bounded=True,
        )
        self.assertTrue(ok2)
        self.assertEqual(blockers2, ())

    def test_state_preserves_numeric_bounds(self):
        s=p106_state()
        self.assertEqual(s["superseded_sub_blocker"],SUPERSEDED_SUB_BLOCKER)
        self.assertEqual(s["primary_residual"],PRIMARY_NEXT_RESIDUAL)
        self.assertTrue(s["invert_hun_public_dataset_identified"])
        self.assertFalse(s["invert_numeric_hun_extract_materialized_in_repo"])
        self.assertFalse(s["p106_numeric_national_action_tightening"])
        self.assertAlmostEqual(s["p102_structural_calibrated_retrofit_floor_lower_share"],0.8278610299446981)
        self.assertAlmostEqual(s["hp_only_share_upper"],0.17213897005530188)

    def test_registry_and_sources(self):
        reg=rows(ROOT/"registry"/"b02_p106_non_ekr_window_performance_calibration.csv","item_id")
        self.assertEqual(reg["B02-P106-U07"]["status"],"SUPERSEDED_BY_CALIBRATION_CONTRACT")
        sources=rows(ROOT/"registry"/"sources.csv","source_id")
        for sid in (
            "SRC-B02-TUWIEN-INVERT-EU27-STOCK-2026",
            "SRC-B02-INVERT-METHODOLOGY-2026",
            "SRC-B02-INVERT-FLEX-RENOVATION-GENERATION-2023",
        ):
            self.assertIn(sid,sources)

    def test_boundaries(self):
        b=semantic_boundaries()
        self.assertIn("MODEL_EFFECTIVE_WINDOW_U_IS_NOT_OBSERVED_REPLACED_WINDOW_UW",b)
        self.assertIn("RENOVATION_GENERATION_IS_NOT_WINDOW_REPLACEMENT_EVENT",b)

if __name__=="__main__":
    unittest.main()
