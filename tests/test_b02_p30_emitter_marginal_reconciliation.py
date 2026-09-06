import unittest
from pathlib import Path

from modules.B02.emitter_marginal_reconciliation import (
    HISTORICAL_MULTI_PRIOR_SCENARIOS,
    PRIMARY_HEATING_GAS_CONVECTOR_SHARE,
    build_calibrated_emitter_linkage,
    reconcile_gas_convector_margin,
)


ROOT = Path(__file__).resolve().parents[1]
WBL = ROOT / "data" / "processed" / "b02" / "ksh_wbl_joint_cells_2022.csv"


class B02P30EmitterMarginalReconciliationTests(unittest.TestCase):
    def test_strict_room_gas_domain_is_proven_infeasible(self):
        result = reconcile_gas_convector_margin(WBL)
        self.assertEqual(result.occupied_dwellings, 4_008_541)
        self.assertEqual(result.wbl_gas_heating_dwellings, 2_496_034)
        self.assertEqual(result.wbl_room_gas_dwellings, 693_075)
        self.assertEqual(result.blocker, "ROOM_GAS_DOMAIN_TOO_SMALL")
        self.assertFalse(result.marginal_reconciled)
        self.assertGreater(result.room_gas_probability, 1.0)

    def test_calibrated_structural_scenarios_reconcile_primary_margin_exactly(self):
        rows, summary = build_calibrated_emitter_linkage(WBL)
        self.assertEqual(summary.row_count, 116_452)
        self.assertEqual(summary.occupied_dwellings, 4_008_541)
        self.assertEqual(summary.gas_heating_dwellings, 2_496_034)
        self.assertEqual(summary.target_primary_convector_share, PRIMARY_HEATING_GAS_CONVECTOR_SHARE)
        self.assertEqual(
            {scenario.scenario_id for scenario in summary.scenarios},
            set(HISTORICAL_MULTI_PRIOR_SCENARIOS),
        )
        self.assertLessEqual(summary.maximum_absolute_marginal_residual, 1e-5)
        for scenario in summary.scenarios:
            self.assertAlmostEqual(
                scenario.calibrated_expected_dwellings,
                scenario.target_expected_dwellings,
                places=5,
            )
            self.assertGreaterEqual(scenario.minimum_probability, 0.0)
            self.assertLessEqual(scenario.maximum_probability, 1.0)
        print(
            "P30_CALIBRATED "
            f"target_share={summary.target_primary_convector_share:.12f} "
            f"target_dwellings={summary.scenarios[0].target_expected_dwellings:.12f} "
            f"max_residual={summary.maximum_absolute_marginal_residual:.12g} "
            + " ".join(
                f"{scenario.scenario_id}:shift={scenario.logit_shift:.12f},"
                f"pmax={scenario.maximum_probability:.12f}"
                for scenario in summary.scenarios
            )
        )
        self.assertEqual(len(rows), 116_452)

    def test_non_gas_cells_have_zero_convector_probability_in_every_scenario(self):
        rows, _ = build_calibrated_emitter_linkage(WBL)
        for row in rows:
            if not row["gas_present"]:
                for scenario_id in HISTORICAL_MULTI_PRIOR_SCENARIOS:
                    self.assertEqual(row[f"probability__{scenario_id}"], 0.0)

    def test_no_emitter_surface_is_materialized_or_promoted(self):
        self.assertFalse(
            (ROOT / "data" / "processed" / "b02" / "b02_gas_convector_emitter_assignment_2022.csv").exists()
        )


if __name__ == "__main__":
    unittest.main()
